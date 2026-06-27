#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from test_sandbox import discover_engines

try:
    import psutil
except ImportError:  # pragma: no cover - optional host sampler
    psutil = None


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "artifacts" / "s3_visibility_workload"
SCRIPT = "res://tests/terrain_s3_visibility_workload.gd"
PASS_MARKER = "WT_SANDBOX_S3_VISIBILITY_WORKLOAD_PASS"
TIMEOUT_SECONDS = 900
TARGET_BUDGET = {
    "profile_id": "S3-L4-headless-baseline",
    "terrain_level": "L4",
    "horizontal_cells": 2048,
    "radius_chunks": 3,
    "maximum_lod": 1,
    "active_chunk_capacity": 1024,
    "render_apply_budget": 1,
    "startup_ms_max": 15000,
    "initial_settle_ms_max": 20000,
    "phase_settle_ms_max": 20000,
    "max_frame_ms": 250.0,
    "max_active_chunk_records": 1024,
    "max_edit_ms": 15000,
    "max_journal_growth_bytes": 2 * 1024 * 1024,
    "max_rss_bytes": 768 * 1024 * 1024,
    "gpu_frame_time": "not measured by headless baseline; required before S3 exit",
}


def fail_if_godot_error(combined: str) -> bool:
    return (
        "SCRIPT ERROR:" in combined
        or "SCRIPT ERROR" in combined
        or combined.startswith("ERROR:")
        or "\nERROR:" in combined
    )


def parse_marker(combined: str) -> dict[str, str]:
    for line in combined.splitlines():
        if PASS_MARKER not in line:
            continue
        fields: dict[str, str] = {}
        for item in line.split()[1:]:
            if "=" in item:
                key, value = item.split("=", 1)
                fields[key] = value
        return fields
    return {}


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


def make_sampler(process: subprocess.Popen[str]) -> object | None:
    if psutil is None:
        return None
    sampler = psutil.Process(process.pid)
    sampler.cpu_percent(None)
    return sampler


def summarize_samples(samples: list[dict[str, float | int]]) -> dict[str, float | int | str]:
    if psutil is None:
        return {"available": "false"}
    if not samples:
        return {"available": "true", "samples": 0}
    cpu_values = [float(sample["cpu_percent"]) for sample in samples]
    rss_values = [int(sample["rss_bytes"]) for sample in samples]
    return {
        "available": "true",
        "samples": len(samples),
        "avg_cpu_percent": round(sum(cpu_values) / len(cpu_values), 3),
        "max_cpu_percent": round(max(cpu_values), 3),
        "max_rss_bytes": max(rss_values),
    }


def run_engine(version: str, engine: Path) -> dict:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    stdout_path = ARTIFACT_ROOT / f"godot-{version}.stdout.txt"
    stderr_path = ARTIFACT_ROOT / f"godot-{version}.stderr.txt"
    command = [
        str(engine),
        "--headless",
        "--path",
        str(ROOT),
        "--script",
        SCRIPT,
        "--",
        "--disable-player-input",
    ]
    with stdout_path.open("w", encoding="utf-8") as stdout_file, \
            stderr_path.open("w", encoding="utf-8") as stderr_file:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            text=True,
            stdout=stdout_file,
            stderr=stderr_file,
        )
        started = time.monotonic()
        process_sampler = make_sampler(process)
        samples: list[dict[str, float | int]] = []
        while process.poll() is None:
            if time.monotonic() - started > TIMEOUT_SECONDS:
                process.kill()
                raise RuntimeError(f"S3 visibility workload timed out on {version}")
            if process_sampler is not None:
                try:
                    info = process_sampler.memory_info()
                    samples.append({
                        "cpu_percent": process_sampler.cpu_percent(None),
                        "rss_bytes": int(info.rss),
                    })
                except psutil.Error:
                    process_sampler = None
            time.sleep(0.25)
        return_code = process.wait()
    combined = (
        stdout_path.read_text(encoding="utf-8", errors="replace")
        + stderr_path.read_text(encoding="utf-8", errors="replace")
    )
    print(combined, end="" if combined.endswith("\n") else "\n")
    fields = parse_marker(combined)
    if return_code != 0 or not fields or fail_if_godot_error(combined):
        raise RuntimeError(f"S3 visibility workload failed on {version}")
    sampling = summarize_samples(samples)
    if int(sampling.get("max_rss_bytes", 0)) > TARGET_BUDGET["max_rss_bytes"]:
        raise RuntimeError(f"S3 RSS budget exceeded on {version}: {sampling}")
    return {
        "engine": version,
        "executable": str(engine),
        "marker": fields,
        "process_sampling": sampling,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the S3 visibility/frustum production workload baseline."
    )
    parser.add_argument("--godot", type=Path, action="append", default=[])
    parser.add_argument("--force-generation", action="store_true")
    arguments = parser.parse_args()
    ensure_l4_world(arguments.force_generation)
    engines = discover_engines(arguments.godot)
    results = [run_engine(version, engine) for version, engine in engines]
    report = {
        "schema": "world-transvoxel-sandbox.s3-visibility-workload.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "visibility_workload_baseline_pass",
        "script": SCRIPT,
        "target_budget_profile": TARGET_BUDGET,
        "workload_classes": [
            "stable loaded-window inspection; S1 remains the fixed LOD0 reference",
            "normal movement",
            "rapid turns with frustum estimate separated from terrain demand",
            "underground traversal",
            "repeated mining while moving",
        ],
        "fast_travel_policy": "loading_screen_required",
        "engines": results,
        "proven": [
            "player input disabled before scene entry",
            "L4 streaming workload can settle under declared headless budgets",
            "camera rapid turns change frustum estimate without terrain demand",
            "underground movement has render/collision probes",
            "repeated mining while moving records edit latency and journal growth",
        ],
        "not_proven": [
            "S3 exit acceptance",
            "GPU frame-time or visual artifact acceptance",
            "forward-biased prefetch",
            "restore_to_base",
            "seamless fast travel without loading-screen semantics",
        ],
    }
    report_path = ARTIFACT_ROOT / "workload_report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "WT_SANDBOX_S3_VISIBILITY_WORKLOAD_AUDIT_PASS "
        f"engines={len(engines)} report={report_path.relative_to(ROOT).as_posix()}"
    )


if __name__ == "__main__":
    main()
