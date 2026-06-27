#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_FILES = (
    "docs/S1_S2_COMPLETION_CHECKLIST.md",
    "docs/S1_DYNAMIC_LOD_POLICY.md",
    "docs/S1_LOD0_WORKLOAD_BASELINE.md",
    "docs/S1_LOD0_GALLERY_AUDIT.md",
    "docs/S2_SCALE_LADDER_EXIT_REVIEW.md",
    "docs/TERRAIN_ACCEPTANCE_STANDARD.md",
    "docs/TERRAIN_RUNTIME_BUDGETS.md",
    "tools/s1_lod0_workload_audit.py",
    "tools/s1_lod0_gallery_audit.py",
    "tools/s2_exit_review.py",
    "tests/terrain_s1_default_policy_audit.gd",
    "tests/terrain_s1_lod0_persistence_audit.gd",
)

REQUIRED_PHRASES = {
    "docs/S1_S2_COMPLETION_CHECKLIST.md": (
        "S1 technical exit: complete by S1.11",
        "S2 automated exit: complete by `WT_SANDBOX_S2_EXIT_REVIEW_PASS`",
        "Go to S3 contract: yes",
        "dynamic seamless mixed-LOD gameplay",
        "not skipped S1/S2 work",
    ),
    "docs/CURRENT_STATUS.md": (
        "S2 automated scale-ladder exit evidence is complete",
        "S1.11 added an accepted fixed-center LOD0 gallery",
        "S2 now has an explicit exit review",
    ),
    "docs/ROADMAP.md": (
        "Technical exit: complete by S1.11",
        "Exit: complete for automated 2K scale-ladder evidence",
        "S3 may start after S2 exit",
    ),
}

EXPECTED_S2 = {
    "L1": {
        "pages": 1152,
        "payload_bytes": 47_778_959,
        "visual_images": 7,
        "world_hash": "4e052784ce8743a6ac72f34a8fef23699875e7fad7ed61ff8e12da1bf5ac5ff0",
    },
    "L2": {
        "pages": 4608,
        "payload_bytes": 191_113_103,
        "visual_images": 7,
        "world_hash": "167c8a4aa98611bf324c373558d170509b67358dfaff7fd535fb486c51d5cd4a",
    },
    "L3": {
        "pages": 18432,
        "payload_bytes": 764_449_679,
        "visual_images": 7,
        "world_hash": "e6f74c2b9bcf60263229e4a15ed0133d82fe2973816a1139fcd908cc821e9567",
    },
    "L4": {
        "pages": 73728,
        "payload_bytes": 3_057_795_983,
        "visual_images": 7,
        "world_hash": "0f908b1e36c8c602ca884070c40d360e6a661274135791f13dafab1f48384368",
    },
}


def run_command(command: list[str]) -> str:
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
        errors="replace",
        timeout=120,
    )
    combined = result.stdout + result.stderr
    print(combined, end="" if combined.endswith("\n") else "\n")
    if result.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(command)}")
    return combined


def read_json(relative: str) -> dict:
    path = ROOT / relative
    if not path.is_file():
        raise RuntimeError(f"missing report: {relative}")
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def check_required_files_and_text() -> None:
    for relative in REQUIRED_FILES:
        require((ROOT / relative).is_file(), f"missing checklist file: {relative}")
    for relative, phrases in REQUIRED_PHRASES.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        collapsed = " ".join(text.split())
        for phrase in phrases:
            require(
                phrase in text or phrase in collapsed,
                f"{relative} is missing phrase: {phrase}",
            )


def check_s1_report() -> None:
    report = read_json("artifacts/s1_lod0_gallery/gallery_report.json")
    require(
        report.get("schema") == "world-transvoxel-sandbox.s1-lod0-gallery.v1",
        "S1 gallery report schema drifted",
    )
    require(report.get("status") == "accepted_lod0_gallery_pass",
            "S1 gallery report status is not pass")
    require(len(report.get("images", [])) == 9, "S1 gallery image count drifted")
    require(len(report.get("persistence", [])) == 2,
            "S1 persistence engine count drifted")
    for persistence in report["persistence"]:
        marker = persistence.get("marker", {})
        require(marker.get("restart") == "exact", "S1 restart persistence drifted")
        require(marker.get("mesh") == "stable", "S1 restart mesh stability drifted")
    classes = report.get("artifact_classification", {})
    require(
        classes.get("dynamic_lod_popping", "").startswith("out_of_scope"),
        "S1 dynamic LOD boundary classification drifted",
    )


def check_s2_report() -> None:
    report = read_json("artifacts/s2_exit_review/s2_exit_review_report.json")
    require(
        report.get("schema") == "world-transvoxel-sandbox.s2-exit-review.v1",
        "S2 exit report schema drifted",
    )
    require(report.get("status") == "s2_scale_ladder_exit_review_pass",
            "S2 exit report status is not pass")
    levels = {level["level"]: level for level in report.get("levels", [])}
    require(set(levels) == set(EXPECTED_S2), "S2 level set drifted")
    for name, expected in EXPECTED_S2.items():
        actual = levels[name]
        for key, value in expected.items():
            require(actual.get(key) == value, f"S2 {name} {key} drifted")
        require(actual.get("runtime_engines") == 2,
                f"S2 {name} runtime engine count drifted")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate the S1/S2 completion checklist evidence."
    )
    parser.add_argument(
        "--refresh-fast",
        action="store_true",
        help="Rerun fast validation and S2 exit review before checking reports.",
    )
    arguments = parser.parse_args()
    check_required_files_and_text()
    if arguments.refresh_fast:
        validation = run_command([sys.executable, "tools/validate_sandbox.py"])
        require("WT_SANDBOX_VALIDATION_PASS" in validation, "sandbox validation marker missing")
        s2 = run_command([sys.executable, "tools/s2_exit_review.py"])
        require("WT_SANDBOX_S2_EXIT_REVIEW_PASS" in s2, "S2 exit marker missing")
    check_s1_report()
    check_s2_report()
    print(
        "WT_SANDBOX_S1_S2_COMPLETION_CHECKLIST_PASS "
        "s1=complete s2=complete decision=ready_for_s3_contract"
    )


if __name__ == "__main__":
    main()
