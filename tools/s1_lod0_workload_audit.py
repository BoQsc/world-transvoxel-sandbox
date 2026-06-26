#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from test_sandbox import discover_engines

try:
    import psutil
except ImportError:  # pragma: no cover - optional host sampler
    psutil = None


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "artifacts" / "s1_lod0_workload"
SCRIPT = "res://tests/terrain_s1_lod0_workload_audit.gd"
PASS_MARKER = "WT_SANDBOX_S1_LOD0_WORKLOAD_PASS"
TIMEOUT_SECONDS = 240


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


def make_sampler(process: subprocess.Popen[str]) -> object | None:
    if psutil is None:
        return None
    process_sampler = psutil.Process(process.pid)
    process_sampler.cpu_percent(None)
    return process_sampler


def summarize_samples(
    samples: list[dict[str, float | int]]
) -> dict[str, float | int | str]:
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
                raise RuntimeError(f"S1 LOD0 workload audit timed out on {version}")
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
        raise RuntimeError(f"S1 LOD0 workload audit failed on {version}")
    return {
        "engine": version,
        "executable": str(engine),
        "marker": fields,
        "process_sampling": summarize_samples(samples),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the S1 conservative LOD0 workload audit."
    )
    parser.add_argument("--godot", type=Path, action="append", default=[])
    arguments = parser.parse_args()
    if not (ROOT / "world" / "world.wtworld").is_file():
        raise RuntimeError("Generate the baseline world before workload audit.")
    engines = discover_engines(arguments.godot)
    results = [run_engine(version, engine) for version, engine in engines]
    report = {
        "schema": "world-transvoxel-sandbox.s1-lod0-workload.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "conservative_lod0_workload_pass",
        "script": SCRIPT,
        "engines": results,
        "hard_gates": [
            "fixed-center LOD0 reference mode",
            "player input disabled before scene entry",
            "full LOD0 render/collision chunk coverage",
            "settled idle produces no runtime work",
            "fixed-anchor movement does not trigger streaming",
            "repeated carve and exact restore meet latency/journal budgets",
        ],
        "recorded_not_portable_gates": [
            "process CPU/RSS samples depend on host and are recorded in report",
            "GPU power is not available in portable headless audit",
        ],
    }
    report_path = ARTIFACT_ROOT / "workload_report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "WT_SANDBOX_S1_LOD0_WORKLOAD_AUDIT_PASS "
        f"engines={len(engines)} report={report_path.relative_to(ROOT).as_posix()}"
    )


if __name__ == "__main__":
    main()
