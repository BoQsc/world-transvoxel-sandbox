#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "artifacts" / "s2_exit_review"
SCALE_ROOT = ROOT / "artifacts" / "scale_ladder"
LEVELS = ("L1", "L2", "L3", "L4")
EXPECTED = {
    "L1": {
        "horizontal_cells": 256,
        "pages": 1152,
        "payload_bytes": 47_778_959,
        "world_hash": "4e052784ce8743a6ac72f34a8fef23699875e7fad7ed61ff8e12da1bf5ac5ff0",
        "active_capacity": 512,
        "positions": 5,
        "probes": 25,
        "min_render": 97,
        "min_collision": 97,
    },
    "L2": {
        "horizontal_cells": 512,
        "pages": 4608,
        "payload_bytes": 191_113_103,
        "world_hash": "167c8a4aa98611bf324c373558d170509b67358dfaff7fd535fb486c51d5cd4a",
        "active_capacity": 1024,
        "positions": 5,
        "probes": 25,
        "min_render": 176,
        "min_collision": 176,
    },
    "L3": {
        "horizontal_cells": 1024,
        "pages": 18432,
        "payload_bytes": 764_449_679,
        "world_hash": "e6f74c2b9bcf60263229e4a15ed0133d82fe2973816a1139fcd908cc821e9567",
        "active_capacity": 1024,
        "positions": 7,
        "probes": 35,
        "min_render": 201,
        "min_collision": 201,
    },
    "L4": {
        "horizontal_cells": 2048,
        "pages": 73728,
        "payload_bytes": 3_057_795_983,
        "world_hash": "0f908b1e36c8c602ca884070c40d360e6a661274135791f13dafab1f48384368",
        "active_capacity": 1024,
        "positions": 7,
        "probes": 35,
        "min_render": 210,
        "min_collision": 195,
    },
}


def read_json(path: Path) -> dict:
    if not path.is_file():
        raise RuntimeError(f"missing required S2 report: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def check_runtime_budget_profiles() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "runtime_budget_profiles.py"), "--check"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
        errors="replace",
        timeout=60,
    )
    combined = result.stdout + result.stderr
    print(combined, end="" if combined.endswith("\n") else "\n")
    if result.returncode != 0 or "WT_SANDBOX_RUNTIME_BUDGETS_PASS" not in combined:
        raise RuntimeError("runtime budget profile check failed")


def marker_int(marker: dict, name: str) -> int:
    try:
        return int(marker[name])
    except (KeyError, TypeError, ValueError) as error:
        raise RuntimeError(f"invalid runtime marker field {name}: {marker}") from error


def validate_level(level: str) -> dict[str, object]:
    expected = EXPECTED[level]
    root = SCALE_ROOT / level
    generation = read_json(root / "scale_ladder_report.json")
    runtime = read_json(root / "runtime_report.json")
    visual = read_json(root / "visual_report.json")

    require(generation.get("schema") == "world-transvoxel-sandbox.scale-ladder.v1",
            f"{level} generation schema drifted")
    require(generation.get("status") == "generated_only",
            f"{level} generation status drifted")
    require(generation.get("warnings") == [], f"{level} generation has warnings")
    gen = generation["generation"]
    world = gen["world"]
    require(gen["source_revision"] == 10003, f"{level} source revision drifted")
    require(gen["finite_shell_solid_samples"] == 3,
            f"{level} finite boundary guard drifted")
    require(gen["horizontal_cells"] == expected["horizontal_cells"],
            f"{level} horizontal cell count drifted")
    require(world["pages"] == expected["pages"], f"{level} page count drifted")
    require(world["sha256"] == expected["world_hash"], f"{level} world hash drifted")
    require(generation["world_payload_bytes"] == expected["payload_bytes"],
            f"{level} payload size drifted")
    if level == "L4":
        preflight = generation["resource_preflight"]
        require(preflight["generation_mode"] == "bounded",
                "L4 generation mode must stay bounded")
        require(preflight["blockers"] == [], "L4 resource preflight has blockers")
        require(preflight["required_available_memory_bytes"] == 614_711_296,
                "L4 memory reserve contract drifted")

    require(runtime.get("schema") == "world-transvoxel-sandbox.scale-runtime.v1",
            f"{level} runtime schema drifted")
    require(runtime.get("status") == "runtime_headless_pass",
            f"{level} runtime status drifted")
    budget = runtime["runtime_budget"]
    require(budget["movement_class"] == "staged movement",
            f"{level} runtime movement class drifted")
    require(budget["radius_chunks"] == 3, f"{level} runtime radius drifted")
    require(budget["maximum_lod"] == 1, f"{level} runtime max LOD drifted")
    require(budget["active_chunk_capacity"] == expected["active_capacity"],
            f"{level} active chunk capacity drifted")
    require(len(runtime["engines"]) == 2, f"{level} runtime engine count drifted")
    for engine in runtime["engines"]:
        marker = engine["marker"]
        require(marker_int(marker, "positions") == expected["positions"],
                f"{level} runtime position count drifted")
        require(marker_int(marker, "probes") == expected["probes"],
                f"{level} runtime probe count drifted")
        require(marker_int(marker, "min_render") >= expected["min_render"],
                f"{level} runtime render coverage regressed")
        require(marker_int(marker, "min_collision") >= expected["min_collision"],
                f"{level} runtime collision coverage regressed")
        require(marker_int(marker, "max_retiring") == 0,
                f"{level} runtime left retiring chunks pending")

    require(visual.get("schema") == "world-transvoxel-sandbox.scale-visual.v1",
            f"{level} visual schema drifted")
    require(visual.get("status") == "visual_capture_pass",
            f"{level} visual status drifted")
    require(len(visual.get("images", [])) == 7, f"{level} visual image count drifted")
    log = root / "visual" / "capture.log"
    log_text = log.read_text(encoding="utf-8", errors="replace")
    require("SCRIPT ERROR" not in log_text and "\nERROR:" not in log_text,
            f"{level} visual log contains Godot errors")
    if level in {"L3", "L4"}:
        require(f"WT_SANDBOX_{level}_BOUNDARY_PASS" in log_text,
                f"{level} boundary pass marker is missing")

    return {
        "level": level,
        "pages": world["pages"],
        "payload_bytes": generation["world_payload_bytes"],
        "world_hash": world["sha256"],
        "runtime_budget": budget,
        "runtime_engines": len(runtime["engines"]),
        "visual_images": len(visual["images"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate the S2 L1-L4 scale-ladder exit evidence."
    )
    parser.parse_args()
    check_runtime_budget_profiles()
    levels = [validate_level(level) for level in LEVELS]
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "world-transvoxel-sandbox.s2-exit-review.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "s2_scale_ladder_exit_review_pass",
        "levels": levels,
        "proven": [
            "L1-L4 generation reports match locked hashes and page counts",
            "L1-L4 staged runtime reports pass with declared budgets",
            "L1-L4 static visual reports pass with seven images each",
            "L3 and L4 finite-boundary regression markers are present",
            "L4 generation remains bounded by explicit resource preflight",
        ],
        "not_proven": [
            "final human qualitative confirmation",
            "dynamic seamless LOD gameplay",
            "fast travel or disjoint teleport support",
            "target-hardware gameplay workload",
            "scale support beyond L4 / 2048",
        ],
    }
    report_path = ARTIFACT_ROOT / "s2_exit_review_report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "WT_SANDBOX_S2_EXIT_REVIEW_PASS "
        f"levels={len(LEVELS)} report={report_path.relative_to(ROOT).as_posix()}"
    )


if __name__ == "__main__":
    main()
