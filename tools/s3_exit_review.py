#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "artifacts" / "s3_exit_review"
VISIBILITY_REPORT = ROOT / "artifacts" / "s3_visibility_workload" / "workload_report.json"
RESTORE_REPORT = ROOT / "artifacts" / "s3_restore_to_base" / "restore_to_base_report.json"
VISUAL_REPORT = ROOT / "artifacts" / "s3_visual_gpu" / "visual_gpu_report.json"
S3_CHECKLIST = ROOT / "docs" / "S3_COMPLETION_CHECKLIST.md"
S3_CONTRACT = ROOT / "docs" / "S3_VISIBILITY_PRODUCTION_WORKLOAD_CONTRACT.md"


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"missing S3 evidence report: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def marker_int(marker: dict[str, Any], name: str) -> int:
    try:
        return int(marker[name])
    except (KeyError, TypeError, ValueError) as error:
        raise RuntimeError(f"invalid marker integer {name}: {marker}") from error


def marker_float(marker: dict[str, Any], name: str) -> float:
    try:
        return float(marker[name])
    except (KeyError, TypeError, ValueError) as error:
        raise RuntimeError(f"invalid marker float {name}: {marker}") from error


def check_no_godot_errors(paths: list[Path]) -> list[str]:
    checked: list[str] = []
    for path in paths:
        require(path.is_file(), f"missing S3 log: {path.relative_to(ROOT)}")
        text = path.read_text(encoding="utf-8", errors="replace")
        require("SCRIPT ERROR" not in text, f"Godot script error in {path.relative_to(ROOT)}")
        require(not text.startswith("ERROR:"), f"Godot error in {path.relative_to(ROOT)}")
        require("\nERROR:" not in text, f"Godot error in {path.relative_to(ROOT)}")
        checked.append(path.relative_to(ROOT).as_posix())
    return checked


def validate_visibility(report: dict[str, Any]) -> dict[str, Any]:
    require(report.get("schema") == "world-transvoxel-sandbox.s3-visibility-workload.v1", "visibility schema drifted")
    require(report.get("status") == "visibility_workload_baseline_pass", "visibility status drifted")
    require(report.get("fast_travel_policy") == "loading_screen_required", "fast travel policy drifted")
    budget = report["target_budget_profile"]
    require(budget["profile_id"] == "S3-L4-headless-baseline", "S3 profile id drifted")
    require(budget["horizontal_cells"] == 2048, "S3 horizontal scale drifted")
    require(budget["active_chunk_capacity"] == 1024, "S3 active capacity drifted")
    require(budget["render_apply_budget"] == 1, "S3 render apply budget drifted")
    engines = report.get("engines", [])
    require(len(engines) == 2, "S3 visibility must pass on two Godot engines")
    max_edit_ms = 0
    max_frame_ms = 0.0
    min_render = 999999
    min_collision = 999999
    max_active = 0
    for engine in engines:
        marker = engine["marker"]
        require(marker_int(marker, "classes") == 5, "S3 workload class count drifted")
        require(marker_int(marker, "normal_positions") == 4, "normal movement count drifted")
        require(marker_int(marker, "underground_positions") == 3, "underground movement count drifted")
        require(marker_int(marker, "rapid_turns") == 6, "rapid-turn count drifted")
        require(marker_int(marker, "viewer_updates_delta") == 0, "rapid turns changed viewer demand")
        require(marker_int(marker, "planned_demands_delta") == 0, "rapid turns changed terrain demand")
        require(marker_int(marker, "prefetch_updates") > 0, "forward prefetch did not update")
        require(marker.get("prefetch_distance") == "64.0", "prefetch distance drifted")
        require(marker.get("prefetch_radius") == "1", "prefetch radius drifted")
        require(marker.get("fast_travel_policy") == "loading_screen_required", "fast travel marker drifted")
        require(marker_int(marker, "edit_cycles") == 2, "mining edit cycle count drifted")
        require(marker_int(marker, "journal_growth_bytes") <= budget["max_journal_growth_bytes"], "journal growth exceeded S3 budget")
        require(marker_int(marker, "max_edit_ms") <= budget["max_edit_ms"], "edit latency exceeded S3 budget")
        require(marker_float(marker, "max_frame_ms") <= budget["max_frame_ms"], "frame interval exceeded S3 budget")
        require(marker_int(marker, "max_active") <= budget["max_active_chunk_records"], "active chunk cap exceeded")
        min_render = min(min_render, marker_int(marker, "min_render"))
        min_collision = min(min_collision, marker_int(marker, "min_collision"))
        max_active = max(max_active, marker_int(marker, "max_active"))
        max_edit_ms = max(max_edit_ms, marker_int(marker, "max_edit_ms"))
        max_frame_ms = max(max_frame_ms, marker_float(marker, "max_frame_ms"))
    return {
        "engines": len(engines),
        "min_render": min_render,
        "min_collision": min_collision,
        "max_active": max_active,
        "max_edit_ms": max_edit_ms,
        "max_frame_ms": round(max_frame_ms, 3),
        "fast_travel_policy": "loading_screen_required",
    }


def validate_restore(report: dict[str, Any]) -> dict[str, Any]:
    require(report.get("schema") == "world-transvoxel-sandbox.s3-restore-to-base.v1", "restore schema drifted")
    require(report.get("status") == "restore_to_base_pass", "restore status drifted")
    engines = report.get("engines", [])
    require(len(engines) == 2, "restore_to_base must pass on two Godot engines")
    max_restore_ms = 0
    for engine in engines:
        marker = engine["marker"]
        require(marker_int(marker, "points") == 33, "restore sample count drifted")
        require(marker_int(marker, "active_capacity") == 1024, "restore active capacity drifted")
        require(marker_int(marker, "journal_growth_bytes") <= 2 * 1024 * 1024, "restore journal growth exceeded budget")
        require(marker_int(marker, "carve_ms") <= 15000, "restore audit carve exceeded latency budget")
        require(marker_int(marker, "restore_ms") <= 15000, "restore_to_base exceeded latency budget")
        max_restore_ms = max(max_restore_ms, marker_int(marker, "restore_ms"))
    return {"engines": len(engines), "points": 33, "max_restore_ms": max_restore_ms}


def validate_visual(report: dict[str, Any]) -> dict[str, Any]:
    require(report.get("schema") == "world-transvoxel-sandbox.s3-visual-gpu.v1", "visual/GPU schema drifted")
    require(report.get("status") == "visual_gpu_acceptance_pass", "visual/GPU status drifted")
    marker = report["marker"]
    require(marker_int(marker, "images") == 13, "visual image count drifted")
    require(marker_float(marker, "max_frame_ms") <= 250.0, "graphical frame interval exceeded S3 budget")
    require(marker_int(marker, "min_render") >= 160, "graphical render coverage regressed")
    require(marker_int(marker, "min_collision") >= 160, "graphical collision coverage regressed")
    require(marker_int(marker, "max_active") <= 1024, "graphical active chunk cap exceeded")
    require(marker_int(marker, "rapid_turns") == 4, "visual rapid-turn count drifted")
    require(marker_int(marker, "viewer_updates_delta") == 0, "visual rapid turns changed viewer demand")
    require(marker_int(marker, "planned_demands_delta") == 0, "visual rapid turns changed terrain demand")
    images = report.get("images", [])
    require(len(images) == 13, "visual report image metrics missing")
    for image in images:
        require(image.get("size") == "1280x720", f"visual image size drifted: {image}")
        require(int(image.get("bytes", 0)) > 10000, f"visual image is undersized: {image}")
    contact_sheet = ROOT / report["contact_sheet"]
    require(contact_sheet.is_file(), "visual contact sheet is missing")
    return {
        "images": 13,
        "max_frame_ms": marker["max_frame_ms"],
        "min_render": marker["min_render"],
        "min_collision": marker["min_collision"],
        "contact_sheet": report["contact_sheet"],
    }


def validate_docs() -> dict[str, Any]:
    checklist = S3_CHECKLIST.read_text(encoding="utf-8")
    contract = S3_CONTRACT.read_text(encoding="utf-8")
    for phrase in (
        "WT_SANDBOX_S3_VISIBILITY_WORKLOAD_AUDIT_PASS",
        "WT_SANDBOX_S3_RESTORE_TO_BASE_AUDIT_PASS",
        "WT_SANDBOX_S3_VISUAL_GPU_AUDIT_PASS",
        "WT_SANDBOX_S3_EXIT_REVIEW_PASS",
    ):
        require(phrase in checklist + contract, f"S3 docs missing phrase: {phrase}")
    return {
        "checklist": S3_CHECKLIST.relative_to(ROOT).as_posix(),
        "contract": S3_CONTRACT.relative_to(ROOT).as_posix(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate S3 exit evidence.")
    parser.parse_args()
    visibility = validate_visibility(read_json(VISIBILITY_REPORT))
    restore = validate_restore(read_json(RESTORE_REPORT))
    visual = validate_visual(read_json(VISUAL_REPORT))
    docs = validate_docs()
    logs = check_no_godot_errors([
        ROOT / "artifacts" / "s3_visibility_workload" / "godot-4.6.3.stdout.txt",
        ROOT / "artifacts" / "s3_visibility_workload" / "godot-4.7.stdout.txt",
        ROOT / "artifacts" / "s3_restore_to_base" / "godot-4.6.3.stdout.txt",
        ROOT / "artifacts" / "s3_restore_to_base" / "godot-4.7.stdout.txt",
        ROOT / "artifacts" / "s3_visual_gpu" / "capture.log",
    ])
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "world-transvoxel-sandbox.s3-exit-review.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "s3_exit_review_pass",
        "visibility": visibility,
        "restore_to_base": restore,
        "visual_gpu": visual,
        "docs": docs,
        "logs_checked": logs,
        "decision": "S3 complete; next valid milestone is S4 decision, not broad GPU implementation",
        "proven": [
            "S3 L4 visibility/frustum workload passed declared budgets on two Godot engines",
            "rapid camera turns are separated from terrain demand",
            "forward-biased prefetch uses the accepted bounded secondary-viewer policy",
            "fast travel is classified as loading-screen required",
            "restore_to_base repairs audited edited samples to deterministic generated terrain",
            "graphical visual artifact gate passed representative L4 S3 captures",
        ],
        "not_proven": [
            "GPU compute acceleration",
            "water, lava, planets, or structural stability",
            "future game repository readiness",
            "0BSD backend replacement",
            "final human aesthetic acceptance or final texture/art production",
        ],
    }
    report_path = ARTIFACT_ROOT / "s3_exit_review_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"WT_SANDBOX_S3_EXIT_REVIEW_PASS report={report_path.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
