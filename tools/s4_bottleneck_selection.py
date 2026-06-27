#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "artifacts" / "s4_bottleneck_selection"
S3_EXIT_REPORT = ROOT / "artifacts" / "s3_exit_review" / "s3_exit_review_report.json"
VISIBILITY_REPORT = ROOT / "artifacts" / "s3_visibility_workload" / "workload_report.json"
RESTORE_REPORT = ROOT / "artifacts" / "s3_restore_to_base" / "restore_to_base_report.json"
VISUAL_REPORT = ROOT / "artifacts" / "s3_visual_gpu" / "visual_gpu_report.json"
S4_CONTRACT = ROOT / "docs" / "S4_M6_DECISION_CONTRACT.md"
S4_CHECKLIST = ROOT / "docs" / "S4_COMPLETION_CHECKLIST.md"
S4_SELECTION_DOC = ROOT / "docs" / "S4_BOTTLENECK_SELECTION.md"

EDIT_INVESTIGATION_FLOOR_MS = 250.0
FRAME_BUDGET_MS = 250.0
EDIT_BUDGET_MS = 15000.0


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"missing S4 input report: {path.relative_to(ROOT)}")
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


def max_visibility_metric(report: dict[str, Any], name: str, as_float: bool = False) -> float:
    values: list[float] = []
    for engine in report.get("engines", []):
        marker = engine["marker"]
        values.append(marker_float(marker, name) if as_float else float(marker_int(marker, name)))
    if not values:
        raise RuntimeError(f"visibility report has no engine values for {name}")
    return max(values)


def max_restore_metric(report: dict[str, Any], name: str) -> int:
    values: list[int] = []
    for engine in report.get("engines", []):
        values.append(marker_int(engine["marker"], name))
    if not values:
        raise RuntimeError(f"restore report has no engine values for {name}")
    return max(values)


def max_process_sampling(report: dict[str, Any], name: str) -> float:
    values: list[float] = []
    for engine in report.get("engines", []):
        sampling = engine.get("process_sampling", {})
        if sampling.get("available") == "true":
            values.append(float(sampling[name]))
    if not values:
        raise RuntimeError(f"visibility report has no process sampling for {name}")
    return max(values)


def validate_inputs(
    s3_exit: dict[str, Any],
    visibility: dict[str, Any],
    restore: dict[str, Any],
    visual: dict[str, Any],
) -> None:
    require(
        s3_exit.get("schema") == "world-transvoxel-sandbox.s3-exit-review.v1",
        "S3 exit review schema drifted",
    )
    require(s3_exit.get("status") == "s3_exit_review_pass", "S3 exit review is not passing")
    require(
        visibility.get("schema") == "world-transvoxel-sandbox.s3-visibility-workload.v1",
        "S3 visibility schema drifted",
    )
    require(
        visibility.get("status") == "visibility_workload_baseline_pass",
        "S3 visibility report is not passing",
    )
    require(
        restore.get("schema") == "world-transvoxel-sandbox.s3-restore-to-base.v1",
        "S3 restore schema drifted",
    )
    require(restore.get("status") == "restore_to_base_pass", "S3 restore report is not passing")
    require(
        visual.get("schema") == "world-transvoxel-sandbox.s3-visual-gpu.v1",
        "S3 visual/GPU schema drifted",
    )
    require(visual.get("status") == "visual_gpu_acceptance_pass", "S3 visual/GPU report is not passing")


def validate_docs() -> None:
    required = {
        S4_CONTRACT: (
            "tools/s4_bottleneck_selection.py",
            "WT_SANDBOX_S4_BOTTLENECK_SELECTION_PASS",
        ),
        S4_CHECKLIST: (
            "S4 status: active decision work, not implementation",
            "S3 bottleneck selected | Complete",
            "WT_SANDBOX_S4_BOTTLENECK_SELECTION_PASS",
        ),
        S4_SELECTION_DOC: (
            "Selected bottleneck: interactive edit-settle latency",
            "WT_SANDBOX_S4_BOTTLENECK_SELECTION_PASS",
            "Next valid S4 action",
        ),
    }
    for path, phrases in required.items():
        if not path.is_file():
            raise RuntimeError(f"missing S4 document: {path.relative_to(ROOT)}")
        text = path.read_text(encoding="utf-8")
        for phrase in phrases:
            require(phrase in text, f"{path.relative_to(ROOT)} missing phrase: {phrase}")


def build_report() -> dict[str, Any]:
    s3_exit = read_json(S3_EXIT_REPORT)
    visibility = read_json(VISIBILITY_REPORT)
    restore = read_json(RESTORE_REPORT)
    visual = read_json(VISUAL_REPORT)
    validate_inputs(s3_exit, visibility, restore, visual)

    max_edit_ms = int(max_visibility_metric(visibility, "max_edit_ms"))
    max_headless_frame_ms = round(max_visibility_metric(visibility, "max_frame_ms", as_float=True), 3)
    max_settle_ms = int(max_visibility_metric(visibility, "settle_ms"))
    max_active = int(max_visibility_metric(visibility, "max_active"))
    max_avg_cpu_percent = round(max_process_sampling(visibility, "avg_cpu_percent"), 3)
    max_peak_cpu_percent = round(max_process_sampling(visibility, "max_cpu_percent"), 3)
    max_rss_bytes = int(max_process_sampling(visibility, "max_rss_bytes"))
    max_restore_carve_ms = max_restore_metric(restore, "carve_ms")
    max_restore_ms = max_restore_metric(restore, "restore_ms")
    max_restore_journal_bytes = max_restore_metric(restore, "journal_growth_bytes")
    max_visual_frame_ms = marker_float(visual["marker"], "max_frame_ms")

    require(
        max_edit_ms >= EDIT_INVESTIGATION_FLOOR_MS,
        "S4 edit bottleneck selection floor is not met",
    )

    candidates = [
        {
            "id": "interactive_edit_settle_latency",
            "source": VISIBILITY_REPORT.relative_to(ROOT).as_posix(),
            "metric": "max_edit_ms",
            "value_ms": max_edit_ms,
            "s3_budget_ms": EDIT_BUDGET_MS,
            "s3_budget_usage": round(max_edit_ms / EDIT_BUDGET_MS, 6),
            "investigation_floor_ms": EDIT_INVESTIGATION_FLOOR_MS,
            "floor_multiple": round(max_edit_ms / EDIT_INVESTIGATION_FLOOR_MS, 3),
            "classification": "selected",
            "reason": (
                "Terrain-specific, user-facing edit/remesh settle latency is "
                "measured in the S3 production workload and remains high enough "
                "to require CPU/native phase attribution before any compute prototype."
            ),
        },
        {
            "id": "restore_to_base_settle_latency",
            "source": RESTORE_REPORT.relative_to(ROOT).as_posix(),
            "metric": "max(carve_ms, restore_ms)",
            "value_ms": max(max_restore_carve_ms, max_restore_ms),
            "carve_ms": max_restore_carve_ms,
            "restore_ms": max_restore_ms,
            "s3_budget_ms": EDIT_BUDGET_MS,
            "classification": "related_not_primary",
            "reason": (
                "Restore-to-base confirms edit/recovery work is terrain-specific, "
                "but the audit is a correctness repair gate, not the primary "
                "interactive production loop."
            ),
        },
        {
            "id": "graphical_frame_interval",
            "source": VISUAL_REPORT.relative_to(ROOT).as_posix(),
            "metric": "max_frame_ms",
            "value_ms": max_visual_frame_ms,
            "s3_budget_ms": FRAME_BUDGET_MS,
            "s3_budget_usage": round(max_visual_frame_ms / FRAME_BUDGET_MS, 6),
            "classification": "not_selected_for_compute_yet",
            "reason": (
                "This is the largest declared-budget pressure, but S3 does not "
                "attribute it to terrain generation, meshing, upload, renderer, "
                "capture, or driver work. It is not a valid compute target yet."
            ),
        },
        {
            "id": "headless_frame_interval",
            "source": VISIBILITY_REPORT.relative_to(ROOT).as_posix(),
            "metric": "max_frame_ms",
            "value_ms": max_headless_frame_ms,
            "s3_budget_ms": FRAME_BUDGET_MS,
            "s3_budget_usage": round(max_headless_frame_ms / FRAME_BUDGET_MS, 6),
            "classification": "not_selected",
            "reason": "Headless frame interval is below the S3 frame budget and below the edit target.",
        },
        {
            "id": "initial_settle_latency",
            "source": VISIBILITY_REPORT.relative_to(ROOT).as_posix(),
            "metric": "settle_ms",
            "value_ms": max_settle_ms,
            "s3_budget_ms": 20000.0,
            "s3_budget_usage": round(max_settle_ms / 20000.0, 6),
            "classification": "not_selected",
            "reason": "One-time loading/settle pressure is less important than interactive edit latency for S4 M6.",
        },
    ]

    return {
        "schema": "world-transvoxel-sandbox.s4-bottleneck-selection.v1",
        "status": "s4_bottleneck_selection_pass",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "selected_bottleneck": {
            "id": "interactive_edit_settle_latency",
            "name": "interactive edit-settle latency",
            "max_edit_ms": max_edit_ms,
            "investigation_floor_ms": EDIT_INVESTIGATION_FLOOR_MS,
            "floor_multiple": round(max_edit_ms / EDIT_INVESTIGATION_FLOOR_MS, 3),
            "source": VISIBILITY_REPORT.relative_to(ROOT).as_posix(),
        },
        "supporting_metrics": {
            "restore_carve_ms": max_restore_carve_ms,
            "restore_ms": max_restore_ms,
            "restore_journal_growth_bytes": max_restore_journal_bytes,
            "headless_frame_ms": max_headless_frame_ms,
            "visual_frame_ms": max_visual_frame_ms,
            "initial_settle_ms": max_settle_ms,
            "max_active_chunk_records": max_active,
            "max_avg_cpu_percent": max_avg_cpu_percent,
            "max_peak_cpu_percent": max_peak_cpu_percent,
            "max_rss_bytes": max_rss_bytes,
        },
        "candidates": candidates,
        "decision": (
            "S4 selects interactive edit-settle latency as the first M6 decision "
            "target. The next valid S4 action is a CPU/native phase baseline, "
            "not compute implementation."
        ),
        "next_required_gate": {
            "id": "cpu_native_edit_phase_baseline",
            "purpose": (
                "Attribute edit-settle time across sample capture, density edit, "
                "journal/storage, meshing, render resource application, and "
                "collision readiness."
            ),
            "compute_blocked_until": (
                "A complete CPU/native phase baseline shows a terrain source, "
                "meshing, or upload phase that a targeted compute path can "
                "improve end to end."
            ),
        },
        "not_authorized": [
            "broad GPU rewrite",
            "compute prototype before CPU/native edit phase baseline",
            "removing deterministic CPU/headless fallback",
            "water/lava, planets, structural stability, game repository, or 0BSD replacement",
        ],
        "input_reports": [
            S3_EXIT_REPORT.relative_to(ROOT).as_posix(),
            VISIBILITY_REPORT.relative_to(ROOT).as_posix(),
            RESTORE_REPORT.relative_to(ROOT).as_posix(),
            VISUAL_REPORT.relative_to(ROOT).as_posix(),
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Select the S4 M6 bottleneck from S3 evidence.")
    parser.parse_args()
    validate_docs()
    report = build_report()
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    report_path = ARTIFACT_ROOT / "bottleneck_selection_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    selected = report["selected_bottleneck"]
    print(
        "WT_SANDBOX_S4_BOTTLENECK_SELECTION_PASS "
        f"selected={selected['id']} "
        f"max_edit_ms={selected['max_edit_ms']} "
        f"report={report_path.relative_to(ROOT).as_posix()}"
    )


if __name__ == "__main__":
    main()
