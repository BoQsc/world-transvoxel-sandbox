#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from test_sandbox import discover_engines


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "artifacts" / "scale_ladder"
SUPPORTED_LEVELS = ("L1", "L2", "L3")
SCRIPT_BY_LEVEL = {
    "L1": "res://tests/terrain_l1_runtime_audit.gd",
    "L2": "res://tests/terrain_l2_runtime_audit.gd",
    "L3": "res://tests/terrain_l3_runtime_audit.gd",
}
MARKER_BY_LEVEL = {
    "L1": "WT_SANDBOX_L1_RUNTIME_PASS",
    "L2": "WT_SANDBOX_L2_RUNTIME_PASS",
    "L3": "WT_SANDBOX_L3_RUNTIME_PASS",
}
RUNTIME_TIMEOUT_SECONDS = {
    "L1": 180,
    "L2": 300,
    "L3": 600,
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
}


def ensure_generated(level: str, force: bool) -> None:
    world = ARTIFACT_ROOT / level / "world" / "world.wtworld"
    if world.is_file() and not force:
        return
    command = [
        sys.executable,
        str(ROOT / "tools" / "scale_ladder.py"),
        "--level",
        level,
        "--force",
    ]
    subprocess.run(command, cwd=ROOT, check=True)


def fail_if_godot_error(combined: str) -> bool:
    return (
        "SCRIPT ERROR:" in combined
        or "SCRIPT ERROR" in combined
        or combined.startswith("ERROR:")
        or "\nERROR:" in combined
    )


def parse_marker(marker: str, combined: str) -> dict[str, str]:
    for line in combined.splitlines():
        if marker not in line:
            continue
        fields: dict[str, str] = {}
        for item in line.split()[1:]:
            if "=" in item:
                key, value = item.split("=", 1)
                fields[key] = value
        return fields
    return {}


def run_level(level: str, engines: list[tuple[str, Path]]) -> dict:
    level_root = ARTIFACT_ROOT / level
    marker = MARKER_BY_LEVEL[level]
    results: list[dict] = []
    for version, engine in engines:
        name = f"runtime-godot-{version}"
        result = subprocess.run(
            [
                str(engine),
                "--headless",
                "--path",
                str(ROOT),
                "--script",
                SCRIPT_BY_LEVEL[level],
            ],
            cwd=ROOT,
            check=False,
            text=True,
            capture_output=True,
            errors="replace",
            timeout=RUNTIME_TIMEOUT_SECONDS[level],
        )
        combined = result.stdout + result.stderr
        level_root.mkdir(parents=True, exist_ok=True)
        (level_root / f"{name}.stdout.txt").write_text(
            result.stdout, encoding="utf-8"
        )
        (level_root / f"{name}.stderr.txt").write_text(
            result.stderr, encoding="utf-8"
        )
        print(combined, end="" if combined.endswith("\n") else "\n")
        fields = parse_marker(marker, combined)
        if result.returncode != 0 or not fields or fail_if_godot_error(combined):
            raise RuntimeError(f"scale runtime failed for {level} on {version}")
        results.append({
            "engine": version,
            "executable": str(engine),
            "marker": fields,
        })
    return {
        "schema": "world-transvoxel-sandbox.scale-runtime.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "status": "runtime_headless_pass",
        "runtime_budget": RUNTIME_BUDGET_BY_LEVEL[level],
        "engines": results,
        "proven": [
            "Godot startup on this level",
            "staged movement render/collision coverage on this level",
            "one density edit and remesh on this level",
            "clean shutdown on this level",
        ],
        "not_proven": [
            "visual artifact acceptance on this level",
            "dynamic seamless LOD appearance on this level",
            "larger scale support beyond this runtime level",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run headless runtime audits for generated scale levels."
    )
    parser.add_argument("--level", choices=SUPPORTED_LEVELS, required=True)
    parser.add_argument("--godot", type=Path, action="append", default=[])
    parser.add_argument("--force-generation", action="store_true")
    arguments = parser.parse_args()
    ensure_generated(arguments.level, arguments.force_generation)
    engines = discover_engines(arguments.godot)
    report = run_level(arguments.level, engines)
    report_path = ARTIFACT_ROOT / arguments.level / "runtime_report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "WT_SANDBOX_SCALE_RUNTIME_PASS "
        f"level={arguments.level} engines={len(engines)} "
        f"report={report_path.relative_to(ROOT).as_posix()}"
    )


if __name__ == "__main__":
    main()
