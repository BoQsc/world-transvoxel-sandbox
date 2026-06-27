#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from test_sandbox import discover_engines


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "artifacts" / "s4_cpu_edit_phase_baseline"
SCRIPT = "res://tests/terrain_s4_cpu_edit_phase_baseline.gd"
PASS_MARKER = "WT_SANDBOX_S4_CPU_EDIT_PHASE_BASELINE_PASS"
CYCLE_MARKER = "WT_SANDBOX_S4_CPU_EDIT_PHASE_CYCLE"
TIMEOUT_SECONDS = 420
MAX_TOTAL_MS = 15_000
MAX_PHASE_MS = 15_000
MAX_SUBMIT_MS = 1_000
MAX_FRAME_MS = 250.0
MAX_JOURNAL_GROWTH_BYTES = 2 * 1024 * 1024


def ensure_l4_world(force_generation: bool) -> None:
    world = ROOT / "artifacts" / "scale_ladder" / "L4" / "world" / "world.wtworld"
    if world.is_file() and not force_generation:
        return
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "scale_ladder.py"),
            "--level",
            "L4",
            "--force",
            "--resource-preflight-approved",
        ],
        cwd=ROOT,
        check=True,
    )


def fail_if_godot_error(combined: str) -> bool:
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


def parse_markers(combined: str) -> tuple[dict[str, str], list[dict[str, str]]]:
    pass_fields: dict[str, str] = {}
    cycles: list[dict[str, str]] = []
    for line in combined.splitlines():
        if PASS_MARKER in line:
            pass_fields = parse_fields(line)
        elif CYCLE_MARKER in line:
            cycles.append(parse_fields(line))
    return pass_fields, cycles


def as_int(fields: dict[str, str], key: str) -> int:
    try:
        return int(fields[key])
    except (KeyError, ValueError) as error:
        raise RuntimeError(f"invalid integer field {key}: {fields}") from error


def as_float(fields: dict[str, str], key: str) -> float:
    try:
        return float(fields[key])
    except (KeyError, ValueError) as error:
        raise RuntimeError(f"invalid float field {key}: {fields}") from error


def validate_fields(version: str, fields: dict[str, str], cycles: list[dict[str, str]]) -> None:
    if as_int(fields, "cycles") != 2 or len(cycles) != 2:
        raise RuntimeError(f"S4 CPU baseline cycle count drifted on {version}")
    if as_int(fields, "samples") != 33:
        raise RuntimeError(f"S4 CPU baseline sample count drifted on {version}: {fields}")
    if as_int(fields, "max_total_ms") > MAX_TOTAL_MS:
        raise RuntimeError(f"S4 CPU baseline total latency exceeded budget on {version}: {fields}")
    if as_int(fields, "max_submit_ms") > MAX_SUBMIT_MS:
        raise RuntimeError(f"S4 CPU baseline submit latency exceeded budget on {version}: {fields}")
    if as_float(fields, "max_frame_ms") > MAX_FRAME_MS:
        raise RuntimeError(f"S4 CPU baseline frame interval exceeded budget on {version}: {fields}")
    if as_int(fields, "journal_growth_bytes") > MAX_JOURNAL_GROWTH_BYTES:
        raise RuntimeError(f"S4 CPU baseline journal growth exceeded budget on {version}: {fields}")
    if as_int(fields, "max_active") > as_int(fields, "active_capacity"):
        raise RuntimeError(f"S4 CPU baseline active capacity exceeded on {version}: {fields}")
    for phase in ("capture", "commit", "mesh", "render", "collision", "settle"):
        if as_int(fields, f"max_{phase}_ms") > MAX_PHASE_MS:
            raise RuntimeError(f"S4 CPU baseline {phase} exceeded budget on {version}: {fields}")
    for cycle in cycles:
        for key in ("replacements", "mesh_delta", "render_delta", "collision_delta"):
            if as_int(cycle, key) <= 0:
                raise RuntimeError(f"S4 CPU baseline missing {key} on {version}: {cycle}")


def run_engine(version: str, engine: Path) -> dict[str, Any]:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            str(engine),
            "--headless",
            "--path",
            str(ROOT),
            "--script",
            SCRIPT,
            "--",
            "--disable-player-input",
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
        errors="replace",
        timeout=TIMEOUT_SECONDS,
    )
    (ARTIFACT_ROOT / f"godot-{version}.stdout.txt").write_text(
        result.stdout, encoding="utf-8"
    )
    (ARTIFACT_ROOT / f"godot-{version}.stderr.txt").write_text(
        result.stderr, encoding="utf-8"
    )
    combined = result.stdout + result.stderr
    print(combined, end="" if combined.endswith("\n") else "\n")
    fields, cycles = parse_markers(combined)
    if result.returncode != 0 or not fields or fail_if_godot_error(combined):
        raise RuntimeError(f"S4 CPU/native edit phase baseline failed on {version}")
    validate_fields(version, fields, cycles)
    return {
        "engine": version,
        "executable": str(engine),
        "marker": fields,
        "cycles": cycles,
    }


def max_marker_int(results: list[dict[str, Any]], key: str) -> int:
    return max(as_int(result["marker"], key) for result in results)


def max_marker_float(results: list[dict[str, Any]], key: str) -> float:
    return max(as_float(result["marker"], key) for result in results)


def max_cycle_int(results: list[dict[str, Any]], key: str) -> int:
    return max(as_int(cycle, key) for result in results for cycle in result["cycles"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the S4 CPU/native edit phase baseline.")
    parser.add_argument("--godot", type=Path, action="append", default=[])
    parser.add_argument("--force-generation", action="store_true")
    arguments = parser.parse_args()
    ensure_l4_world(arguments.force_generation)
    engines = discover_engines(arguments.godot)
    results = [run_engine(version, engine) for version, engine in engines]
    report = {
        "schema": "world-transvoxel-sandbox.s4-cpu-edit-phase-baseline.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "cpu_edit_phase_baseline_pass",
        "script": SCRIPT,
        "engines": results,
        "summary": {
            "engines": len(results),
            "cycles_per_engine": 2,
            "samples_per_cycle": 33,
            "max_capture_ms": max_marker_int(results, "max_capture_ms"),
            "max_submit_ms": max_marker_int(results, "max_submit_ms"),
            "max_commit_ms": max_marker_int(results, "max_commit_ms"),
            "max_mesh_ms": max_marker_int(results, "max_mesh_ms"),
            "max_render_ms": max_marker_int(results, "max_render_ms"),
            "max_collision_ms": max_marker_int(results, "max_collision_ms"),
            "max_settle_ms": max_marker_int(results, "max_settle_ms"),
            "max_total_ms": max_marker_int(results, "max_total_ms"),
            "max_frame_ms": round(max_marker_float(results, "max_frame_ms"), 3),
            "max_cycle_replacements": max_cycle_int(results, "replacements"),
            "max_cycle_mesh_delta": max_cycle_int(results, "mesh_delta"),
        },
        "phase_boundary": [
            "capture_ms measures native authoritative sample batch request latency",
            "submit_ms measures transaction build and asynchronous edit submission",
            "commit_ms measures runtime edit acceptance, journal append, replacement planning, and commit publication",
            "mesh_ms measures edit replacement mesh completion after commit observation",
            "render_ms measures render queue/resource readiness after mesh completion",
            "collision_ms measures collision queue/resource readiness after render readiness",
            "settle_ms measures final stable no-queue/no-retirement hold window",
        ],
        "decision": (
            "CPU/native edit phase baseline exists. Compute remains blocked until "
            "this report is reviewed against a targeted end-to-end improvement case."
        ),
        "not_proven": [
            "compute shader acceleration",
            "GPU transfer/readback cost",
            "final S4 M6 ship/reject decision",
            "water/lava, planets, stability, game repository, or 0BSD replacement",
        ],
    }
    report_path = ARTIFACT_ROOT / "cpu_edit_phase_baseline_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "WT_SANDBOX_S4_CPU_EDIT_PHASE_BASELINE_AUDIT_PASS "
        f"engines={len(results)} "
        f"max_total_ms={report['summary']['max_total_ms']} "
        f"report={report_path.relative_to(ROOT).as_posix()}"
    )


if __name__ == "__main__":
    main()
