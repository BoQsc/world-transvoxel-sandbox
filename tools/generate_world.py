#!/usr/bin/env python3

from __future__ import annotations

import argparse
import array
import hashlib
import json
import math
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / ".generated" / "world_source"
DEFAULT_OUTPUT = ROOT / "world"
SOURCE_REVISION = 10002


@dataclass(frozen=True)
class ScaleProfile:
    level: str
    horizontal_cells: int
    vertical_cells: int
    lod0_chunks: tuple[int, int, int]
    purpose: str

    @property
    def origin(self) -> tuple[int, int, int]:
        return (-2, -2, -2)

    @property
    def dimensions(self) -> tuple[int, int, int]:
        return (
            self.lod0_chunks[0] * 16 + 5,
            self.lod0_chunks[1] * 16 + 5,
            self.lod0_chunks[2] * 16 + 5,
        )

    @property
    def world_extent(self) -> tuple[int, int, int]:
        return tuple(value * 16 for value in self.lod0_chunks)

    @property
    def feature_scale(self) -> float:
        return float(self.horizontal_cells) / 128.0


SCALE_PROFILES = {
    "L0": ScaleProfile(
        "L0", 128, 64, (8, 4, 8), "current correctness and visual baseline"
    ),
    "L1": ScaleProfile(
        "L1", 256, 64, (16, 4, 16), "first larger-terrain generation proof"
    ),
    "L2": ScaleProfile(
        "L2", 512, 64, (32, 4, 32), "512 generation preflight"
    ),
    "L3": ScaleProfile(
        "L3", 1024, 64, (64, 4, 64), "1024 generation preflight"
    ),
}
DEFAULT_SCALE_LEVEL = "L0"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def remove_generated(path: Path) -> None:
    resolved = path.resolve()
    try:
        resolved.relative_to(ROOT)
    except ValueError as error:
        raise RuntimeError(f"Refusing to remove path outside sandbox: {resolved}") from error
    if resolved in {ROOT, ROOT / "addons"}:
        raise RuntimeError(f"Refusing to remove protected path: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)


def terrain_height(x: int, z: int, preset: str) -> float:
    if preset == "flat":
        return 32.0
    broad = 7.0 * math.sin(x * 0.047) + 5.0 * math.cos(z * 0.053)
    local = 2.0 * math.sin(x * 0.091 + 0.7 * math.cos(z * 0.037))
    mound = 3.0 * math.sin(x * 0.023) * math.cos(z * 0.031)
    return 34.0 + broad + local + mound


def chamber_void_density(x: int, y: int, z: int, profile: ScaleProfile) -> float:
    scale = profile.feature_scale
    dx = (float(x) - 40.0 * scale) / 9.0
    dy = (float(y) - 18.0) / 6.0
    dz = (float(z) - 40.0 * scale) / 9.0
    return (1.0 - math.sqrt(dx * dx + dy * dy + dz * dz)) * 7.0


def tunnel_void_density(x: int, y: int, z: int, profile: ScaleProfile) -> float:
    scale = profile.feature_scale
    if x < 16 * scale or x > profile.world_extent[0] - 16 * scale:
        return -math.inf
    center_y = 15.0 + 2.5 * math.sin(float(x) * 0.083)
    center_z = 88.0 * scale + 9.0 * math.sin(float(x) * 0.047)
    dy = float(y) - center_y
    dz = float(z) - center_z
    return (4.2 - math.sqrt(dy * dy + dz * dz)) * 1.8


def underground_material(x: int, y: int, z: int) -> int:
    rock_field = (
        math.sin(float(x) * 0.071 + float(y) * 0.043)
        + math.cos(float(z) * 0.067 - float(y) * 0.051)
        + 0.65 * math.sin(float(x + y + z) * 0.039)
    )
    return 5 if rock_field > 0.55 else 3


def count_volumetric_columns(
    densities: array.array[float], dimensions: tuple[int, int, int]
) -> int:
    count = 0
    width, height, depth = dimensions
    for z_index in range(2, depth - 2):
        for x_index in range(2, width - 2):
            transitions = 0
            previous_solid = densities[z_index * width * height + 2 * width + x_index] < 0.0
            for y_index in range(3, height - 2):
                index = y_index * width + z_index * width * height + x_index
                solid = densities[index] < 0.0
                if solid != previous_solid:
                    transitions += 1
                    previous_solid = solid
            if transitions >= 3:
                count += 1
    return count


def write_volume(preset: str, profile: ScaleProfile) -> dict[str, int]:
    SOURCE_ROOT.mkdir(parents=True, exist_ok=True)
    densities = array.array("f")
    materials = array.array("H")
    material_counts = {str(index): 0 for index in range(6)}
    cave_samples = 0
    chamber_samples = 0
    tunnel_samples = 0
    ore_samples = 0
    boundary_samples = 0

    world_extent = profile.world_extent
    dimensions = profile.dimensions
    x_coordinates = [profile.origin[0] + index for index in range(dimensions[0])]
    y_coordinates = [profile.origin[1] + index for index in range(dimensions[1])]
    z_coordinates = [profile.origin[2] + index for index in range(dimensions[2])]
    sin_x = [math.sin(value * 0.112) for value in x_coordinates]
    sin_y = [math.sin(value * 0.137) for value in y_coordinates]
    cos_z = [math.cos(value * 0.104) for value in z_coordinates]
    vein_y = [18.0 + 5.0 * math.sin(value * 0.078) for value in x_coordinates]
    vein_z = [64.0 + 20.0 * math.sin(value * 0.043) for value in x_coordinates]

    for z_index, z in enumerate(z_coordinates):
        heights = [terrain_height(x, z, preset) for x in x_coordinates]
        cross_noise = [
            0.55 * math.sin((x + z) * 0.071) for x in x_coordinates
        ]
        for y_index, y in enumerate(y_coordinates):
            for x_index, x in enumerate(x_coordinates):
                height = heights[x_index]
                density = float(y) - height
                base_density = density
                cave_margin = (
                    1 < x < world_extent[0] - 1
                    and 1 < y
                    and 1 < z < world_extent[2] - 1
                )
                if preset == "terrain" and cave_margin and y < height - 6.0:
                    cave = (
                        sin_x[x_index]
                        + sin_y[y_index]
                        + cos_z[z_index]
                        + cross_noise[x_index]
                    )
                    if cave > 2.28:
                        density = max(density, (cave - 2.28) * 9.0)
                if preset == "terrain" and cave_margin:
                    chamber_density = chamber_void_density(x, y, z, profile)
                    if chamber_density > density:
                        density = chamber_density
                        chamber_samples += 1
                    tunnel_density = tunnel_void_density(x, y, z, profile)
                    if tunnel_density > density:
                        density = tunnel_density
                        tunnel_samples += 1
                if base_density < 0.0 <= density:
                    cave_samples += 1

                boundary_distance = min(
                    x,
                    world_extent[0] - x,
                    y,
                    z,
                    world_extent[2] - z,
                )
                # Keep the finite shell halfway between integer samples. An
                # exact zero at distance one creates collapsed/isovalue-tied
                # boundary triangles and fragmented material patches.
                boundary_density = 0.5 - float(boundary_distance)
                if boundary_density >= density:
                    density = boundary_density
                    boundary_samples += 1

                material = 0
                if density < 0.0:
                    depth = height - float(y)
                    if depth < 2.2:
                        material = 1
                    elif depth < 8.0:
                        material = 2
                    else:
                        material = (
                            underground_material(x, y, z)
                            if preset == "terrain"
                            else (5 if y < 10 else 3)
                        )
                    if preset == "terrain" and depth > 7.0:
                        dy = float(y) - vein_y[x_index]
                        dz = float(z) - vein_z[x_index]
                        if dy * dy + dz * dz < 5.0:
                            material = 4
                            ore_samples += 1
                densities.append(density)
                materials.append(material)
                material_counts[str(material)] += 1

    volumetric_columns = count_volumetric_columns(densities, dimensions)
    if preset == "terrain" and volumetric_columns == 0:
        raise RuntimeError("Terrain generation produced no non-heightfield columns.")
    if densities.itemsize != 4 or materials.itemsize != 2:
        raise RuntimeError("Host array widths do not match the bake format.")
    if sys.byteorder != "little":
        densities.byteswap()
        materials.byteswap()
    density_path = SOURCE_ROOT / "density.f32"
    material_path = SOURCE_ROOT / "materials.u16"
    with density_path.open("wb") as output:
        densities.tofile(output)
    with material_path.open("wb") as output:
        materials.tofile(output)
    return {
        "samples": len(densities),
        "cave_samples": cave_samples,
        "chamber_samples": chamber_samples,
        "tunnel_samples": tunnel_samples,
        "volumetric_columns": volumetric_columns,
        "ore_samples": ore_samples,
        "boundary_samples": boundary_samples,
        **{f"material_{key}": value for key, value in material_counts.items()},
    }


def write_keys(profile: ScaleProfile) -> int:
    keys: list[tuple[int, int, int, int]] = []
    lod0_chunks = profile.lod0_chunks
    for z in range(lod0_chunks[2]):
        for y in range(lod0_chunks[1]):
            for x in range(lod0_chunks[0]):
                keys.append((x, y, z, 0))
    for z in range(lod0_chunks[2] // 2):
        for y in range(lod0_chunks[1] // 2):
            for x in range(lod0_chunks[0] // 2):
                keys.append((x, y, z, 1))
    (SOURCE_ROOT / "keys.txt").write_text(
        "".join(f"{x} {y} {z} {lod}\n" for x, y, z, lod in keys),
        encoding="utf-8",
    )
    return len(keys)


def generate(output_root: Path, preset: str, force: bool, scale_level: str) -> None:
    profile = SCALE_PROFILES[scale_level]
    output_root = output_root.resolve()
    if force:
        remove_generated(SOURCE_ROOT)
        remove_generated(output_root)
    elif output_root.exists():
        raise RuntimeError(f"Output exists; pass --force to replace it: {output_root}")

    started = time.perf_counter()
    volume = write_volume(preset, profile)
    page_count = write_keys(profile)
    bake_script = ROOT / "addons" / "world_transvoxel" / "tools" / "wt_bake.py"
    command = [
        sys.executable,
        str(bake_script),
        str(SOURCE_ROOT / "density.f32"),
        str(SOURCE_ROOT / "keys.txt"),
        str(output_root),
        "--materials",
        str(SOURCE_ROOT / "materials.u16"),
        "--origin",
        *(str(value) for value in profile.origin),
        "--dimensions",
        *(str(value) for value in profile.dimensions),
        "--spacing",
        "1",
        "--source-revision",
        str(SOURCE_REVISION),
        "--configuration",
        "template_release",
    ]
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(result.stdout + result.stderr)
    bake_report = json.loads(result.stdout.strip().splitlines()[-1])
    if bake_report.get("pages") != page_count:
        raise RuntimeError(f"Unexpected bake report: {bake_report}")

    validation = subprocess.run(
        [
            sys.executable,
            str(ROOT / "addons" / "world_transvoxel" / "tools" / "wt_storage.py"),
            "validate",
            str(output_root / "world.wtworld"),
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    world_report = json.loads(validation.stdout)
    report = {
        "schema": "world-transvoxel-sandbox.generation.v2",
        "scale_level": profile.level,
        "horizontal_cells": profile.horizontal_cells,
        "vertical_cells": profile.vertical_cells,
        "scale_purpose": profile.purpose,
        "preset": preset,
        "origin": profile.origin,
        "dimensions": profile.dimensions,
        "lod0_chunks": profile.lod0_chunks,
        "source_revision": SOURCE_REVISION,
        "source_density_sha256": sha256(SOURCE_ROOT / "density.f32"),
        "source_material_sha256": sha256(SOURCE_ROOT / "materials.u16"),
        "generation_seconds": round(time.perf_counter() - started, 3),
        "volume": volume,
        "world": world_report,
    }
    (output_root / "sandbox_generation.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "WT_SANDBOX_GENERATION_PASS "
        f"level={profile.level} preset={preset} pages={page_count} "
        f"seconds={report['generation_seconds']} "
        f"world_sha256={world_report['sha256']}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the deterministic World Transvoxel sandbox world."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--preset", choices=("terrain", "flat"), default="terrain")
    parser.add_argument(
        "--scale-level",
        choices=tuple(SCALE_PROFILES),
        default=DEFAULT_SCALE_LEVEL,
    )
    parser.add_argument("--force", action="store_true")
    arguments = parser.parse_args()
    generate(arguments.output, arguments.preset, arguments.force, arguments.scale_level)


if __name__ == "__main__":
    main()
