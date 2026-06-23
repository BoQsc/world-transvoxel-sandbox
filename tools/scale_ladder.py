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
SUPPORTED_LEVELS = tuple(SCALE_PROFILES)
GENERATION_TIMEOUT_SECONDS = {
    "L0": 300,
    "L1": 300,
    "L2": 900,
    "L3": 3600,
    "L4": 7200,
}
PAYLOAD_BUDGET_PER_PAGE = 48 * 1024
DISK_SAFETY_RESERVE_BYTES = 512 * 1024 * 1024
DISK_WARNING_HEADROOM_BYTES = 256 * 1024 * 1024
DENSE_SOURCE_LIMIT_BYTES = 512 * 1024 * 1024
LARGEST_PROVEN_DENSE_LEVEL = "L3"
LARGEST_PROVEN_DENSE_SOURCE_BYTES = (
    math.prod(SCALE_PROFILES[LARGEST_PROVEN_DENSE_LEVEL].dimensions) * 6
)
DENSE_MEMORY_OVERHEAD_NUMERATOR = 5
DENSE_MEMORY_OVERHEAD_DENOMINATOR = 4
MEMORY_SAFETY_RESERVE_BYTES = 512 * 1024 * 1024


def resource_estimate(level: str) -> tuple[dict, list[str], list[str]]:
    profile = SCALE_PROFILES[level]
    samples = math.prod(profile.dimensions)
    source_bytes = samples * 6
    lod0_pages = math.prod(profile.lod0_chunks)
    lod1_pages = math.prod(value // 2 for value in profile.lod0_chunks)
    pages = lod0_pages + lod1_pages
    payload_bytes = pages * PAYLOAD_BUDGET_PER_PAGE
    disk_free = shutil.disk_usage(ROOT).free
    required = source_bytes + payload_bytes + DISK_SAFETY_RESERVE_BYTES
    generator_working_set = math.ceil(
        source_bytes
        * DENSE_MEMORY_OVERHEAD_NUMERATOR
        / DENSE_MEMORY_OVERHEAD_DENOMINATOR
    )
    bake_working_set = source_bytes * 2 + payload_bytes
    dense_peak_memory = max(generator_working_set, bake_working_set)
    required_memory = dense_peak_memory + MEMORY_SAFETY_RESERVE_BYTES
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
    blockers: list[str] = []
    if profile.generation_mode != "dense":
        blockers.append("profile requires bounded generation")
    if source_bytes > DENSE_SOURCE_LIMIT_BYTES:
        blockers.append(
            f"estimated source bytes {source_bytes} exceed the dense-source "
            f"limit {DENSE_SOURCE_LIMIT_BYTES}"
        )
    if disk_free < required:
        blockers.append(
            f"disk free bytes {disk_free} are below required bytes {required}"
        )
    if memory_available is not None and memory_available < required_memory:
        blockers.append(
            f"available memory bytes {memory_available} are below required "
            f"bytes {required_memory}"
        )
    report = {
        "disk_free_before_bytes": disk_free,
        "estimated_source_bytes": source_bytes,
        "estimated_payload_bytes": payload_bytes,
        "disk_safety_reserve_bytes": DISK_SAFETY_RESERVE_BYTES,
        "required_free_bytes": required,
        "memory_available_before_bytes": memory_available,
        "estimated_generator_working_set_bytes": generator_working_set,
        "estimated_bake_working_set_bytes": bake_working_set,
        "estimated_dense_peak_memory_bytes": dense_peak_memory,
        "dense_bake_memory_basis": (
            "raw source bytes plus decoded source arrays plus retained baked pages"
        ),
        "memory_safety_reserve_bytes": MEMORY_SAFETY_RESERVE_BYTES,
        "required_available_memory_bytes": required_memory,
        "dense_source_limit_bytes": DENSE_SOURCE_LIMIT_BYTES,
        "dense_source_limit_basis": (
            f"{LARGEST_PROVEN_DENSE_LEVEL} proven source "
            f"{LARGEST_PROVEN_DENSE_SOURCE_BYTES} bytes plus headroom"
        ),
        "largest_proven_dense_source_bytes": LARGEST_PROVEN_DENSE_SOURCE_BYTES,
        "generation_mode": profile.generation_mode,
        "expected_pages": pages,
        "blockers": blockers,
        "dense_generation_feasible": not blockers,
    }
    return report, warnings, blockers


def resource_preflight(level: str) -> tuple[dict, list[str]]:
    report, warnings, blockers = resource_estimate(level)
    if blockers:
        raise RuntimeError(
            f"scale ladder resource preflight rejected {level}: "
            + "; ".join(blockers)
        )
    return report, warnings


def write_feasibility_report(level: str, preset: str) -> Path:
    estimate, warnings, blockers = resource_estimate(level)
    decision = "reject_dense_generation" if blockers else "allow_dense_generation"
    report = {
        "schema": "world-transvoxel-sandbox.scale-feasibility.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "preset": preset,
        "decision": decision,
        "resource_estimate": estimate,
        "warnings": warnings,
        "proven": [
            "source, payload, page, disk, and dense-memory estimates calculated",
            "whole-volume generation decision recorded before source allocation",
        ],
        "not_proven": [
            "bounded source generation",
            "generated world storage validation",
            "Godot runtime or visual acceptance",
        ],
    }
    level_root = ARTIFACT_ROOT / level
    level_root.mkdir(parents=True, exist_ok=True)
    report_path = level_root / "feasibility_report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        "WT_SANDBOX_SCALE_FEASIBILITY_PASS "
        f"level={level} decision={decision} "
        f"source_bytes={estimate['estimated_source_bytes']} "
        f"payload_bytes={estimate['estimated_payload_bytes']} "
        f"report={report_path.relative_to(ROOT).as_posix()}"
    )
    return report_path


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
    parser.add_argument(
        "--estimate-only",
        action="store_true",
        help="Write a resource decision without allocating source or world data.",
    )
    arguments = parser.parse_args()

    if arguments.estimate_only:
        write_feasibility_report(arguments.level, arguments.preset)
        return
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
