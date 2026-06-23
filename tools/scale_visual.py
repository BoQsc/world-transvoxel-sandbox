#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "artifacts" / "scale_ladder"
SUPPORTED_LEVELS = ("L1", "L2", "L3", "L4")
SCRIPT_BY_LEVEL = {
    "L1": "res://tests/terrain_l1_visual_capture.gd",
    "L2": "res://tests/terrain_l2_visual_capture.gd",
    "L3": "res://tests/terrain_l3_visual_capture.gd",
    "L4": "res://tests/terrain_l4_visual_capture.gd",
}
CAPTURE_MARKER_BY_LEVEL = {
    "L1": "WT_SANDBOX_L1_CAPTURE",
    "L2": "WT_SANDBOX_L2_CAPTURE",
    "L3": "WT_SANDBOX_L3_CAPTURE",
    "L4": "WT_SANDBOX_L4_CAPTURE",
}
PASS_MARKER_BY_LEVEL = {
    "L1": "WT_SANDBOX_L1_VISUAL_CAPTURE_PASS",
    "L2": "WT_SANDBOX_L2_VISUAL_CAPTURE_PASS",
    "L3": "WT_SANDBOX_L3_VISUAL_CAPTURE_PASS",
    "L4": "WT_SANDBOX_L4_VISUAL_CAPTURE_PASS",
}
REQUIRED_MARKERS_BY_LEVEL = {
    "L1": (),
    "L2": (),
    "L3": ("WT_SANDBOX_L3_BOUNDARY_PASS",),
    "L4": ("WT_SANDBOX_L4_BOUNDARY_PASS",),
}
VISUAL_TIMEOUT_SECONDS = {
    "L1": 180,
    "L2": 180,
    "L3": 300,
    "L4": 420,
}
RUNTIME_BUDGET_BY_LEVEL = {
    "L1": {
        "movement_class": "staged movement",
        "radius_chunks": 3,
        "maximum_lod": 1,
        "active_chunk_capacity": 512,
    },
    "L2": {
        "movement_class": "staged movement",
        "radius_chunks": 3,
        "maximum_lod": 1,
        "active_chunk_capacity": 1024,
    },
    "L3": {
        "movement_class": "staged movement",
        "radius_chunks": 3,
        "maximum_lod": 1,
        "active_chunk_capacity": 1024,
        "cache_policy": "inherit config/terrain_config.tres",
    },
    "L4": {
        "movement_class": "staged movement",
        "radius_chunks": 3,
        "maximum_lod": 1,
        "active_chunk_capacity": 1024,
        "cache_policy": "inherit config/terrain_config.tres",
    },
}
EXPECTED_IMAGES = (
    "overview_surface.png",
    "overview_material.png",
    "overview_lod.png",
    "top_unshadowed.png",
    "underground_tunnel.png",
    "closed_boundary.png",
    "closed_boundary_material.png",
)


def discover_engine(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.resolve()
    sibling = ROOT.parent / "world-transvoxel" / ".tools" / "godot" / "4.7"
    candidates = sorted(sibling.glob("Godot*_win64.exe"))
    if candidates:
        return candidates[0].resolve()
    environment = os.environ.get("GODOT")
    if environment:
        return Path(environment).resolve()
    executable = shutil.which("godot")
    if executable:
        return Path(executable).resolve()
    raise RuntimeError("No Godot executable found; pass --godot.")


def ensure_generated(level: str) -> None:
    if (ARTIFACT_ROOT / level / "world" / "world.wtworld").is_file():
        return
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "scale_ladder.py"),
            "--level",
            level,
            "--force",
        ],
        cwd=ROOT,
        check=True,
    )


def parse_captures(combined: str, marker: str) -> list[dict[str, str]]:
    captures: list[dict[str, str]] = []
    for line in combined.splitlines():
        if marker not in line:
            continue
        fields: dict[str, str] = {}
        for item in line.split()[1:]:
            if "=" in item:
                key, value = item.split("=", 1)
                fields[key] = value
        captures.append(fields)
    return captures


def has_godot_error(combined: str) -> bool:
    return (
        "SCRIPT ERROR:" in combined
        or "SCRIPT ERROR" in combined
        or combined.startswith("ERROR:")
        or "\nERROR:" in combined
    )


def run_visual(level: str, engine: Path) -> dict:
    visual_root = ARTIFACT_ROOT / level / "visual"
    visual_root.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            str(engine),
            "--path",
            str(ROOT),
            "--script",
            SCRIPT_BY_LEVEL[level],
            "--",
            "--disable-player-input",
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
        errors="replace",
        timeout=VISUAL_TIMEOUT_SECONDS[level],
    )
    combined = result.stdout + result.stderr
    (visual_root / "capture.log").write_text(combined, encoding="utf-8")
    print(combined, end="" if combined.endswith("\n") else "\n")
    captures = parse_captures(combined, CAPTURE_MARKER_BY_LEVEL[level])
    missing = [
        name
        for name in EXPECTED_IMAGES
        if not (visual_root / name).is_file()
        or (visual_root / name).stat().st_size < 10_000
    ]
    if (
        result.returncode != 0
        or PASS_MARKER_BY_LEVEL[level] not in combined
        or any(marker not in combined for marker in REQUIRED_MARKERS_BY_LEVEL[level])
        or has_godot_error(combined)
        or missing
        or len(captures) != len(EXPECTED_IMAGES)
    ):
        raise RuntimeError(
            f"scale visual failed for {level}; missing/undersized={missing}"
        )
    return {
        "schema": "world-transvoxel-sandbox.scale-visual.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "engine": str(engine),
        "status": "visual_capture_pass",
        "runtime_budget": RUNTIME_BUDGET_BY_LEVEL[level],
        "images": captures,
        "output": visual_root.relative_to(ROOT).as_posix(),
        "artifact_classification": {
            "blank_or_missing_viewport": "not_detected",
            "finite_boundary_shell": (
                "targeted collision ray and static captures passed"
                if level in {"L3", "L4"}
                else "expected in closed_boundary captures"
            ),
            "debug_bounds": "world-bound aware",
            "lod_debug_partition": "expected in overview_lod captures",
            "underground_tunnel": "static centerline-framed capture",
            "top_view_detail": "limited by flat procedural palette",
            "shader_instance_variable_limit": "not_detected after per-LOD materials",
            "render_collision_runtime_gap": "not_tested_here; covered by scale_runtime",
            "dynamic_lod_popping": "not_proven_by_static_captures",
            "human_visual_acceptance": "pending",
        },
        "proven": [
            "representative visual captures were produced",
            "capture viewport range was nonblank for every image",
        ],
        "not_proven": [
            "human visual acceptance",
            "dynamic seamless LOD appearance",
            "larger scale support beyond this visual level",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Capture representative visual evidence for scale levels."
    )
    parser.add_argument("--level", choices=SUPPORTED_LEVELS, required=True)
    parser.add_argument("--godot", type=Path)
    arguments = parser.parse_args()
    ensure_generated(arguments.level)
    report = run_visual(arguments.level, discover_engine(arguments.godot))
    report_path = ARTIFACT_ROOT / arguments.level / "visual_report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "WT_SANDBOX_SCALE_VISUAL_PASS "
        f"level={arguments.level} images={len(EXPECTED_IMAGES)} "
        f"report={report_path.relative_to(ROOT).as_posix()}"
    )


if __name__ == "__main__":
    main()
