#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "artifacts" / "s4_m6_decision"
BOTTLENECK_REPORT = ROOT / "artifacts" / "s4_bottleneck_selection" / "bottleneck_selection_report.json"
BASELINE_REPORT = ROOT / "artifacts" / "s4_cpu_edit_phase_baseline" / "cpu_edit_phase_baseline_report.json"
S4_BASELINE_DOC = ROOT / "docs" / "S4_CPU_EDIT_PHASE_BASELINE.md"
S4_DECISION_DOC = ROOT / "docs" / "S4_M6_DECISION.md"
S4_CHECKLIST = ROOT / "docs" / "S4_COMPLETION_CHECKLIST.md"
COMPUTE_PHASE_FLOOR_MS = 250
TOTAL_LATENCY_REJECT_LIMIT_MS = 2_000


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"missing S4 decision input: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def validate_docs() -> None:
    required = {
        S4_BASELINE_DOC: (
            "WT_SANDBOX_S4_CPU_EDIT_PHASE_BASELINE_AUDIT_PASS",
            "max_total_ms=1205",
        ),
        S4_DECISION_DOC: (
            "Decision: CPU/native retained; compute rejected for now",
            "WT_SANDBOX_S4_M6_DECISION_PASS",
        ),
        S4_CHECKLIST: (
            "S4 status: complete",
            "Compute ship/reject decision recorded | Complete",
            "WT_SANDBOX_S4_M6_DECISION_PASS",
        ),
    }
    for path, phrases in required.items():
        if not path.is_file():
            raise RuntimeError(f"missing S4 decision document: {path.relative_to(ROOT)}")
        text = path.read_text(encoding="utf-8")
        for phrase in phrases:
            require(phrase in text, f"{path.relative_to(ROOT)} missing phrase: {phrase}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Close S4 M6 compute decision from CPU/native evidence.")
    parser.parse_args()
    validate_docs()
    bottleneck = read_json(BOTTLENECK_REPORT)
    baseline = read_json(BASELINE_REPORT)
    require(
        bottleneck.get("schema") == "world-transvoxel-sandbox.s4-bottleneck-selection.v1",
        "S4 bottleneck schema drifted",
    )
    require(bottleneck.get("status") == "s4_bottleneck_selection_pass", "S4 bottleneck is not passing")
    require(
        baseline.get("schema") == "world-transvoxel-sandbox.s4-cpu-edit-phase-baseline.v1",
        "S4 CPU baseline schema drifted",
    )
    require(baseline.get("status") == "cpu_edit_phase_baseline_pass", "S4 CPU baseline is not passing")
    summary = baseline["summary"]
    compute_relevant_ms = max(
        int(summary["max_capture_ms"]),
        int(summary["max_commit_ms"]),
        int(summary["max_mesh_ms"]),
        int(summary["max_render_ms"]),
        int(summary["max_collision_ms"]),
    )
    require(
        compute_relevant_ms < COMPUTE_PHASE_FLOOR_MS,
        "a compute-relevant phase still exceeds the S4 floor; do not reject compute",
    )
    require(
        int(summary["max_total_ms"]) <= TOTAL_LATENCY_REJECT_LIMIT_MS,
        "total edit latency is too high for CPU/native retained decision",
    )
    report = {
        "schema": "world-transvoxel-sandbox.s4-m6-decision.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "s4_m6_decision_pass",
        "decision": "cpu_native_retained_compute_rejected_for_now",
        "selected_bottleneck": bottleneck["selected_bottleneck"],
        "cpu_baseline_summary": summary,
        "compute_relevant_max_ms": compute_relevant_ms,
        "compute_phase_floor_ms": COMPUTE_PHASE_FLOOR_MS,
        "total_latency_reject_limit_ms": TOTAL_LATENCY_REJECT_LIMIT_MS,
        "reason": (
            "The selected edit-settle bottleneck was attributed. No compute-relevant "
            "CPU/native phase reached the investigation floor; the largest remaining "
            "time is the explicit stable-settle hold. A compute prototype is not "
            "authorized for S4."
        ),
        "proven": [
            "S4 selected a measured S3 bottleneck",
            "CPU/native edit phase baseline passed on two Godot engines",
            "deterministic CPU/headless fallback remains the accepted path",
            "M6 compute decision is reject-for-now, not a broad GPU rewrite",
        ],
        "not_proven": [
            "compute shader acceleration",
            "GPU transfer/readback performance",
            "water/lava, planets, stability, game repository, or 0BSD replacement",
        ],
        "input_reports": [
            BOTTLENECK_REPORT.relative_to(ROOT).as_posix(),
            BASELINE_REPORT.relative_to(ROOT).as_posix(),
        ],
    }
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    report_path = ARTIFACT_ROOT / "s4_m6_decision_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "WT_SANDBOX_S4_M6_DECISION_PASS "
        f"decision={report['decision']} "
        f"compute_relevant_max_ms={compute_relevant_ms} "
        f"report={report_path.relative_to(ROOT).as_posix()}"
    )


if __name__ == "__main__":
    main()
