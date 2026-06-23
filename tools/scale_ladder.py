#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from generate_world import SCALE_PROFILES
except ModuleNotFoundError:
    from tools.generate_world import SCALE_PROFILES


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "artifacts" / "scale_ladder"
SUPPORTED_LEVELS = ("L0", "L1", "L2", "L3")
GENERATION_TIMEOUT_SECONDS = {
    "L0": 300,
    "L1": 300,
    "L2": 900,
    "L3": 3600,
}
PAYLOAD_BUDGET_PER_PAGE = 48 * 1024
DISK_SAFETY_RESERVE_BYTES = 512 * 1024 * 1024
DISK_WARNING_HEADROOM_BYTES = 256 * 1024 * 1024


def resource_preflight(level: str) -> tuple[dict, list[str]]:
    profile = SCALE_PROFILES[level]
    samples = math.prod(profile.dimensions)
    source_bytes = samples * 6
    lod0_pages = math.prod(profile.lod0_chunks)
    lod1_pages = math.prod(value // 2 for value in profile.lod0_chunks)
    pages = lod0_pages + lod1_pages
    payload_bytes = pages * PAYLOAD_BUDGET_PER_PAGE
    disk_free = shutil.disk_usage(ROOT).free
    required = source_bytes + payload_bytes + DISK_SAFETY_RESERVE_BYTES
    if disk_free < required:
        raise RuntimeError(
            "scale ladder disk preflight failed: "
            f"level={level} free={disk_free} required={required}"
        )
    warnings: list[str] = []
    if disk_free - required < DISK_WARNING_HEADROOM_BYTES:
        warnings.append(
            "disk headroom is below 256 MiB above the conservative "
            "generation estimate"
        )
    memory_available: int | None = None
    try:
        import psutil

        memory_available = int(psutil.virtual_memory().available)
    except ImportError:
        pass
    return {
        "disk_free_before_bytes": disk_free,
        "estimated_source_bytes": source_bytes,
        "estimated_payload_bytes": payload_bytes,
        "disk_safety_reserve_bytes": DISK_SAFETY_RESERVE_BYTES,
        "required_free_bytes": required,
        "memory_available_before_bytes": memory_available,
        "expected_pages": pages,
    }, warnings


def directory_size(path: Path, excluded_names: set[str] | None = None) -> int:
    excluded = excluded_names or set()
    return sum(
        file.stat().st_size
        for file in path.rglob("*")
        if file.is_file() and file.name not in excluded
    )


def run_generation(level: str, preset: str, force: bool) -> dict:
    preflight, warnings = resource_preflight(level)
    output = ARTIFACT_ROOT / level / "world"
    command = [
        sys.executable,
        str(ROOT / "tools" / "generate_world.py"),
        "--output",
        str(output),
        "--scale-level",
        level,
        "--preset",
        preset,
    ]
    if force:
        command.append("--force")
    started = time.perf_counter()
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
        errors="replace",
        timeout=GENERATION_TIMEOUT_SECONDS[level],
    )
    level_root = ARTIFACT_ROOT / level
    level_root.mkdir(parents=True, exist_ok=True)
    (level_root / "generate.stdout.txt").write_text(
        result.stdout, encoding="utf-8"
    )
    (level_root / "generate.stderr.txt").write_text(
        result.stderr, encoding="utf-8"
    )
    print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.stderr:
        print(result.stderr, end="" if result.stderr.endswith("\n") else "\n")
    if result.returncode != 0:
        raise RuntimeError(f"scale ladder generation failed for {level}")
    generation_report = json.loads(
        (output / "sandbox_generation.json").read_text(encoding="utf-8")
    )
    return {
        "schema": "world-transvoxel-sandbox.scale-ladder.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "preset": preset,
        "status": "generated_only",
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "artifact_root": level_root.relative_to(ROOT).as_posix(),
        "world_payload_bytes": directory_size(output, {"sandbox_generation.json"}),
        "world_report_bytes": (output / "sandbox_generation.json").stat().st_size,
        "generation": generation_report,
        "resource_preflight": preflight,
        "disk_free_after_bytes": shutil.disk_usage(ROOT).free,
        "warnings": warnings,
        "proven": [
            "Python generation completed",
            "native bake tool completed",
            "storage validation completed",
        ],
        "not_proven": [
            "Godot startup on this level",
            "movement/render/collision coverage on this level",
            "visual artifact acceptance on this level",
            "edit latency on this level",
            "larger scale support beyond this generated level",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate measured scale-ladder terrain artifacts."
    )
    parser.add_argument("--level", choices=SUPPORTED_LEVELS, required=True)
    parser.add_argument("--preset", choices=("terrain", "flat"), default="terrain")
    parser.add_argument("--force", action="store_true")
    arguments = parser.parse_args()

    report = run_generation(arguments.level, arguments.preset, arguments.force)
    report_path = ARTIFACT_ROOT / arguments.level / "scale_ladder_report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    generation = report["generation"]
    print(
        "WT_SANDBOX_SCALE_LADDER_PASS "
        f"level={arguments.level} "
        f"horizontal={generation['horizontal_cells']} "
        f"pages={generation['world']['pages']} "
        f"payload_bytes={report['world_payload_bytes']} "
        f"report={report_path.relative_to(ROOT).as_posix()}"
    )


if __name__ == "__main__":
    main()
