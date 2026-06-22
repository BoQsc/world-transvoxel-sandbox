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
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / ".generated" / "world_source"
DEFAULT_OUTPUT = ROOT / "world"
ORIGIN = (-2, -2, -2)
DIMENSIONS = (133, 69, 133)
LOD0_CHUNKS = (8, 4, 8)
WORLD_EXTENT = tuple(value * 16 for value in LOD0_CHUNKS)
SOURCE_REVISION = 10001


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
    crossing = 3.5 * math.sin((x + z) * 0.029)
    ridge = 4.0 * abs(math.sin((x - z) * 0.021))
    return 34.0 + broad + crossing + ridge


def write_volume(preset: str) -> dict[str, int]:
    SOURCE_ROOT.mkdir(parents=True, exist_ok=True)
    densities = array.array("f")
    materials = array.array("H")
    material_counts = {str(index): 0 for index in range(6)}
    cave_samples = 0
    ore_samples = 0
    boundary_samples = 0

    x_coordinates = [ORIGIN[0] + index for index in range(DIMENSIONS[0])]
    y_coordinates = [ORIGIN[1] + index for index in range(DIMENSIONS[1])]
    z_coordinates = [ORIGIN[2] + index for index in range(DIMENSIONS[2])]
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
                cave_margin = (
                    1 < x < WORLD_EXTENT[0] - 1
                    and 1 < y
                    and 1 < z < WORLD_EXTENT[2] - 1
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
                        if density >= 0.0:
                            cave_samples += 1

                boundary_distance = min(
                    x,
                    WORLD_EXTENT[0] - x,
                    y,
                    z,
                    WORLD_EXTENT[2] - z,
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
                    elif y < 10:
                        material = 5
                    else:
                        material = 3
                    if preset == "terrain" and depth > 7.0:
                        dy = float(y) - vein_y[x_index]
                        dz = float(z) - vein_z[x_index]
                        if dy * dy + dz * dz < 5.0:
                            material = 4
                            ore_samples += 1
                densities.append(density)
                materials.append(material)
                material_counts[str(material)] += 1

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
        "ore_samples": ore_samples,
        "boundary_samples": boundary_samples,
        **{f"material_{key}": value for key, value in material_counts.items()},
    }


def write_keys() -> int:
    keys: list[tuple[int, int, int, int]] = []
    for z in range(LOD0_CHUNKS[2]):
        for y in range(LOD0_CHUNKS[1]):
            for x in range(LOD0_CHUNKS[0]):
                keys.append((x, y, z, 0))
    for z in range(LOD0_CHUNKS[2] // 2):
        for y in range(LOD0_CHUNKS[1] // 2):
            for x in range(LOD0_CHUNKS[0] // 2):
                keys.append((x, y, z, 1))
    (SOURCE_ROOT / "keys.txt").write_text(
        "".join(f"{x} {y} {z} {lod}\n" for x, y, z, lod in keys),
        encoding="utf-8",
    )
    return len(keys)


def generate(output_root: Path, preset: str, force: bool) -> None:
    output_root = output_root.resolve()
    if force:
        remove_generated(SOURCE_ROOT)
        remove_generated(output_root)
    elif output_root.exists():
        raise RuntimeError(f"Output exists; pass --force to replace it: {output_root}")

    started = time.perf_counter()
    volume = write_volume(preset)
    page_count = write_keys()
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
        *(str(value) for value in ORIGIN),
        "--dimensions",
        *(str(value) for value in DIMENSIONS),
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
        "schema": "world-transvoxel-sandbox.generation.v1",
        "preset": preset,
        "origin": ORIGIN,
        "dimensions": DIMENSIONS,
        "lod0_chunks": LOD0_CHUNKS,
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
        f"preset={preset} pages={page_count} "
        f"seconds={report['generation_seconds']} "
        f"world_sha256={world_report['sha256']}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the deterministic World Transvoxel sandbox world."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--preset", choices=("terrain", "flat"), default="terrain")
    parser.add_argument("--force", action="store_true")
    arguments = parser.parse_args()
    generate(arguments.output, arguments.preset, arguments.force)


if __name__ == "__main__":
    main()
