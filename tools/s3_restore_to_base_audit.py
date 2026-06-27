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
ARTIFACT_ROOT = ROOT / "artifacts" / "s3_restore_to_base"
SCRIPT = "res://tests/terrain_s3_restore_to_base_audit.gd"
PASS_MARKER = "WT_SANDBOX_S3_RESTORE_TO_BASE_PASS"
TIMEOUT_SECONDS = 360


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


def run_engine(version: str, engine: Path) -> dict:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [str(engine), "--headless", "--path", str(ROOT), "--script", SCRIPT],
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
    fields = parse_marker(combined)
    if result.returncode != 0 or not fields or fail_if_godot_error(combined):
        raise RuntimeError(f"S3 restore_to_base audit failed on {version}")
    return {"engine": version, "executable": str(engine), "marker": fields}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the S3 restore_to_base audit.")
    parser.add_argument("--godot", type=Path, action="append", default=[])
    parser.add_argument("--force-generation", action="store_true")
    arguments = parser.parse_args()
    ensure_l4_world(arguments.force_generation)
    engines = discover_engines(arguments.godot)
    results = [run_engine(version, engine) for version, engine in engines]
    report = {
        "schema": "world-transvoxel-sandbox.s3-restore-to-base.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "restore_to_base_pass",
        "script": SCRIPT,
        "engines": results,
        "proven": [
            "restore_to_base is explicit, not automatic regeneration",
            "edited sphere grid points restore density and material to deterministic base",
            "default recovery policy still leaves timed regeneration disabled",
        ],
    }
    report_path = ARTIFACT_ROOT / "restore_to_base_report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "WT_SANDBOX_S3_RESTORE_TO_BASE_AUDIT_PASS "
        f"engines={len(engines)} report={report_path.relative_to(ROOT).as_posix()}"
    )


if __name__ == "__main__":
    main()
