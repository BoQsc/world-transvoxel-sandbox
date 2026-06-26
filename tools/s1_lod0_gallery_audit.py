#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image

from test_sandbox import discover_engines


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "artifacts" / "s1_lod0_gallery"
VISUAL_ROOT = ROOT / "artifacts" / "visual"
CAPTURE_TOOL = ROOT / "tools" / "capture_visuals.py"
PERSISTENCE_SCRIPT = "res://tests/terrain_s1_lod0_persistence_audit.gd"
PERSISTENCE_MARKER = "WT_SANDBOX_S1_LOD0_PERSISTENCE_PASS"
EXPECTED_IMAGES = (
    "overview_surface.png",
    "overview_material.png",
    "overview_lod.png",
    "top_surface.png",
    "top_unshadowed.png",
    "top_lod.png",
    "underground_tunnel.png",
    "closed_boundary.png",
    "closed_boundary_material.png",
)


def has_godot_error(combined: str) -> bool:
    return (
        "SCRIPT ERROR:" in combined
        or "SCRIPT ERROR" in combined
        or combined.startswith("ERROR:")
        or "\nERROR:" in combined
    )


def parse_fields(line: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for item in line.split()[1:]:
        if "=" in item:
            key, value = item.split("=", 1)
            fields[key] = value
    return fields


def choose_visual_engine(engines: list[tuple[str, Path]]) -> tuple[str, Path]:
    for version, engine in engines:
        if version == "4.7":
            return version, engine
    return engines[-1]


def run_visual_capture(engine: Path) -> str:
    result = subprocess.run(
        [sys.executable, str(CAPTURE_TOOL), "--godot", str(engine)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
        errors="replace",
        timeout=240,
    )
    combined = result.stdout + result.stderr
    print(combined, end="" if combined.endswith("\n") else "\n")
    if (
        result.returncode != 0
        or "WT_SANDBOX_VISUAL_EVIDENCE_PASS" not in combined
        or "WT_SANDBOX_BOUNDARY_PROBE" not in combined
        or has_godot_error(combined)
    ):
        raise RuntimeError("S1 LOD0 visual capture failed")
    return combined


def image_metrics(image_path: Path) -> dict[str, object]:
    if not image_path.is_file() or image_path.stat().st_size < 10_000:
        raise RuntimeError(f"Missing or undersized S1 gallery image: {image_path}")
    with Image.open(image_path) as image:
        rgb = image.convert("RGB")
        width, height = rgb.size
        pixels = np.asarray(rgb, dtype=np.float32) / 255.0
    luminance = pixels.mean(axis=2)
    metrics: dict[str, object] = {
        "image": image_path.name,
        "bytes": image_path.stat().st_size,
        "size": f"{width}x{height}",
        "luminance_min": round(float(luminance.min()), 6),
        "luminance_max": round(float(luminance.max()), 6),
        "luminance_range": round(float(luminance.max() - luminance.min()), 6),
        "luminance_stddev": round(float(luminance.std()), 6),
    }
    if width != 1280 or height != 720:
        raise RuntimeError(f"Unexpected S1 gallery image dimensions: {image_path}")
    if float(metrics["luminance_range"]) < 0.05:
        raise RuntimeError(f"S1 gallery image lacks visual range: {image_path}")
    if float(metrics["luminance_stddev"]) < 0.01:
        raise RuntimeError(f"S1 gallery image is too visually flat: {image_path}")
    return metrics


def parse_visual_captures(combined: str) -> list[dict[str, str]]:
    captures: list[dict[str, str]] = []
    for line in combined.splitlines():
        if "WT_SANDBOX_CAPTURE" in line:
            captures.append(parse_fields(line))
    if len(captures) != len(EXPECTED_IMAGES):
        raise RuntimeError(f"Expected {len(EXPECTED_IMAGES)} captures, got {len(captures)}")
    return captures


def run_persistence(version: str, engine: Path) -> dict[str, object]:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            str(engine),
            "--headless",
            "--path",
            str(ROOT),
            "--script",
            PERSISTENCE_SCRIPT,
            "--",
            "--disable-player-input",
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
        errors="replace",
        timeout=180,
    )
    stdout_path = ARTIFACT_ROOT / f"persistence-godot-{version}.stdout.txt"
    stderr_path = ARTIFACT_ROOT / f"persistence-godot-{version}.stderr.txt"
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    combined = result.stdout + result.stderr
    print(combined, end="" if combined.endswith("\n") else "\n")
    marker_line = next(
        (line for line in combined.splitlines() if PERSISTENCE_MARKER in line),
        "",
    )
    if result.returncode != 0 or not marker_line or has_godot_error(combined):
        raise RuntimeError(f"S1 LOD0 persistence audit failed on Godot {version}")
    return {
        "engine": version,
        "executable": str(engine),
        "marker": parse_fields(marker_line),
        "stdout": stdout_path.relative_to(ROOT).as_posix(),
        "stderr": stderr_path.relative_to(ROOT).as_posix(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit the accepted S1 fixed-center LOD0 visual gallery."
    )
    parser.add_argument("--godot", type=Path, action="append", default=[])
    arguments = parser.parse_args()
    if not (ROOT / "world" / "world.wtworld").is_file():
        raise RuntimeError("Generate the baseline world before the S1 gallery audit.")
    engines = discover_engines(arguments.godot)
    visual_version, visual_engine = choose_visual_engine(engines)
    visual_log = run_visual_capture(visual_engine)
    image_reports = [image_metrics(VISUAL_ROOT / name) for name in EXPECTED_IMAGES]
    persistence = [run_persistence(version, engine) for version, engine in engines]
    report = {
        "schema": "world-transvoxel-sandbox.s1-lod0-gallery.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "accepted_lod0_gallery_pass",
        "visual_engine": {
            "engine": visual_version,
            "executable": str(visual_engine),
        },
        "visual_output": VISUAL_ROOT.relative_to(ROOT).as_posix(),
        "captures": parse_visual_captures(visual_log),
        "images": image_reports,
        "persistence": persistence,
        "hard_gates": [
            "accepted fixed-center LOD0 scene captured with player input disabled",
            "nine representative images exist, are 1280x720, and are nonblank",
            "closed-boundary render and collision rays agree during capture",
            "edit journal survives stop/start and restores exact edited density/mesh",
            "Godot ERROR/SCRIPT ERROR output is a hard failure",
        ],
        "artifact_classification": {
            "blank_or_missing_viewport": "not_detected",
            "upside_down_terrain": "not_detected_by_top_and_overview_capture_orientation",
            "missing_backsides_or_boundary_holes": "not_detected_by_closed_boundary_ray_probe",
            "render_collision_runtime_gap": "not_detected_by_boundary_ray_probe",
            "diagonal_ridge": "not_detected_as_a_hard_gallery_blocker; procedural terrain detail remains visually simple",
            "lod_debug_partition": "expected only in overview_lod/top_lod debug captures",
            "dynamic_lod_popping": "out_of_scope_for_accepted_default; dynamic mixed LOD is diagnostic-only by S1.10",
            "human_visual_acceptance": "pending_final_qualitative_confirmation",
        },
        "proven": [
            "the accepted fixed-center LOD0 gallery is reproducibly captured",
            "the accepted gallery has no automated hard visual blocker",
            "boundary render and collision agree in the gallery view",
            "an edit persists across restart with stable edited mesh identity",
        ],
        "not_proven": [
            "final human qualitative confirmation",
            "real triplanar/texture-array art direction",
            "dynamic mixed-LOD seamless gameplay",
            "water, lava, planets, compute shaders, or game readiness",
        ],
    }
    report_path = ARTIFACT_ROOT / "gallery_report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "WT_SANDBOX_S1_LOD0_GALLERY_AUDIT_PASS "
        f"images={len(EXPECTED_IMAGES)} engines={len(engines)} "
        f"report={report_path.relative_to(ROOT).as_posix()}"
    )


if __name__ == "__main__":
    main()
