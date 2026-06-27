#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "artifacts" / "s5_small_game_decision"
S3_EXIT_REPORT = ROOT / "artifacts" / "s3_exit_review" / "s3_exit_review_report.json"
S4_DECISION_REPORT = ROOT / "artifacts" / "s4_m6_decision" / "s4_m6_decision_report.json"
S5_CONTRACT = ROOT / "docs" / "S5_SMALL_GAME_DECISION_CONTRACT.md"
S5_CHECKLIST = ROOT / "docs" / "S5_COMPLETION_CHECKLIST.md"
S5_VERTICAL_SLICE = ROOT / "docs" / "S5_VERTICAL_SLICE_REQUIREMENTS.md"
S5_DECISION = ROOT / "docs" / "S5_SMALL_GAME_DECISION.md"
REPOSITORY_BOUNDARY = ROOT / "docs" / "REPOSITORY_BOUNDARY_CONTRACT.md"


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"missing S5 decision input: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def require_phrases(path: Path, phrases: tuple[str, ...]) -> None:
    if not path.is_file():
        raise RuntimeError(f"missing S5 document: {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    compressed = " ".join(text.split())
    for phrase in phrases:
        require(
            phrase in text or phrase in compressed,
            f"{path.relative_to(ROOT)} missing phrase: {phrase}",
        )


def validate_docs() -> None:
    require_phrases(
        S5_CONTRACT,
        (
            "S5 starts only after S3 production workload evidence",
            "official MIT-backed World Transvoxel backend first",
            "WT_SANDBOX_S5_SMALL_GAME_DECISION_PASS",
        ),
    )
    require_phrases(
        S5_VERTICAL_SLICE,
        (
            "S5 vertical-slice gate: complete",
            "load a 2048 x 2048 x 64 terrain profile",
            "Use the official MIT-backed World Transvoxel backend first",
            "Do not create the future game repository until `world-transvoxel-terrain`",
        ),
    )
    require_phrases(
        S5_DECISION,
        (
            "Decision: revise terrain architecture first",
            "WT_SANDBOX_S5_SMALL_GAME_DECISION_PASS",
            "Do not create the game repository yet",
        ),
    )
    require_phrases(
        S5_CHECKLIST,
        (
            "S5 status: complete",
            "Smallest game vertical slice is defined | Complete",
            "Final proceed/revise/stop decision is recorded | Complete",
        ),
    )
    require_phrases(
        REPOSITORY_BOUNDARY,
        (
            "future game repository validates world-transvoxel-terrain",
            "Do not use world-transvoxel-sandbox to test world-transvoxel-terrain",
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Close S5 small-game decision.")
    parser.parse_args()
    validate_docs()
    s3_exit = read_json(S3_EXIT_REPORT)
    s4_decision = read_json(S4_DECISION_REPORT)
    require(
        s3_exit.get("schema") == "world-transvoxel-sandbox.s3-exit-review.v1",
        "S3 exit schema drifted",
    )
    require(s3_exit.get("status") == "s3_exit_review_pass", "S3 exit is not passing")
    require(
        s4_decision.get("schema") == "world-transvoxel-sandbox.s4-m6-decision.v1",
        "S4 decision schema drifted",
    )
    require(s4_decision.get("status") == "s4_m6_decision_pass", "S4 decision is not passing")
    require(
        s4_decision.get("decision") == "cpu_native_retained_compute_rejected_for_now",
        "S4 compute decision drifted",
    )
    report = {
        "schema": "world-transvoxel-sandbox.s5-small-game-decision.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "s5_small_game_decision_pass",
        "decision": "revise_terrain_architecture_first",
        "repository_decision": "defer_game_repository_until_world_transvoxel_terrain_exists",
        "backend_decision": "official_mit_backend_first",
        "compute_decision": "cpu_native_retained_compute_rejected_for_now",
        "vertical_slice": S5_VERTICAL_SLICE.relative_to(ROOT).as_posix(),
        "next_architecture_step": "design_or_create_world_transvoxel_terrain",
        "proven": [
            "S3 production workload exit evidence exists",
            "S4 compute decision exists and rejects compute for now",
            "smallest game vertical slice is defined",
            "repository boundary keeps game validation separate from sandbox validation",
        ],
        "not_authorized": [
            "creating the game repository before world-transvoxel-terrain exists",
            "using world-transvoxel-sandbox as game terrain architecture",
            "reopening 0BSD backend replacement before official backend vertical slice",
            "water/lava, planets, structural stability, inventory, or advanced mining effects without contracts",
        ],
        "input_reports": [
            S3_EXIT_REPORT.relative_to(ROOT).as_posix(),
            S4_DECISION_REPORT.relative_to(ROOT).as_posix(),
        ],
    }
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    report_path = ARTIFACT_ROOT / "s5_small_game_decision_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "WT_SANDBOX_S5_SMALL_GAME_DECISION_PASS "
        f"decision={report['decision']} "
        f"repository={report['repository_decision']} "
        f"report={report_path.relative_to(ROOT).as_posix()}"
    )


if __name__ == "__main__":
    main()
