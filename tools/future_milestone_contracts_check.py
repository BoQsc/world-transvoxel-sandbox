#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED = {
    "docs/S3_VISIBILITY_PRODUCTION_WORKLOAD_CONTRACT.md": (
        "S3 starts only after S1/S2",
        "docs/S3_TARGET_MACHINE_BUDGET_PROFILE.md",
        "docs/S3_FORWARD_PREFETCH_POLICY.md",
        "tools/s3_visibility_workload.py",
        "visibility/frustum behavior",
        "WT_SANDBOX_S3_VISIBILITY_WORKLOAD_PASS",
        "WT_SANDBOX_S3_EXIT_REVIEW_PASS",
        "GPU compute acceleration",
        "Out of scope",
    ),
    "docs/S3_COMPLETION_CHECKLIST.md": (
        "S3 status: not complete",
        "Workload classes are defined",
        "WT_SANDBOX_S3_VISIBILITY_WORKLOAD_AUDIT_PASS",
        "Fast travel / teleport policy",
        "Forward-biased prefetch policy is implemented or rejected | Complete",
        "Current decision: do not proceed to S4",
    ),
    "docs/S3_FORWARD_PREFETCH_POLICY.md": (
        "secondary viewer id | `603`",
        "prefetch distance | `64` world cells",
        "prefetch radius | `1` chunk",
        "Rapid camera turns must not directly change terrain demand",
    ),
    "docs/S3_TARGET_MACHINE_BUDGET_PROFILE.md": (
        "S3-L4-headless-baseline",
        "stable loaded-window inspection",
        "normal movement with forward prefetch",
        "prefetch distance | 64 world cells",
        "rapid turns with frustum estimate separated from terrain demand",
        "fast travel policy | loading-screen required",
        "GPU frame time and visual artifact acceptance are not measured",
        "Passing this profile proves the S3 visibility/frustum production workload baseline with the accepted forward-biased prefetch policy",
    ),
    "tools/s3_visibility_workload.py": (
        "WT_SANDBOX_S3_VISIBILITY_WORKLOAD_PASS",
        "world-transvoxel-sandbox.s3-visibility-workload.v1",
        "fast_travel_policy",
        "forward_prefetch_distance",
        "loading_screen_required",
    ),
    "tests/terrain_s3_visibility_workload.gd": (
        "WT_SANDBOX_S3_VISIBILITY_WORKLOAD_PASS",
        "set(\"input_enabled\", false)",
        "frustum_min",
        "planned_demands_delta",
        "prefetch_distance=%.1f",
        "fast_travel_policy=loading_screen_required",
    ),
    "docs/S4_M6_DECISION_CONTRACT.md": (
        "S4 starts only after S3 exits",
        "measured bottleneck",
        "WT_SANDBOX_S4_M6_DECISION_PASS",
        "CPU/headless fallback",
    ),
    "docs/S4_COMPLETION_CHECKLIST.md": (
        "S4 status: not started",
        "S3 bottleneck selected",
        "Current decision: do not start S4 implementation",
    ),
    "docs/S5_SMALL_GAME_DECISION_CONTRACT.md": (
        "S5 starts only after S3 production workload evidence",
        "docs/REPOSITORY_BOUNDARY_CONTRACT.md",
        "future game repository validates world-transvoxel-terrain",
        "official MIT-backed World Transvoxel backend first",
        "WT_SANDBOX_S5_SMALL_GAME_DECISION_PASS",
        "0BSD backend replacement",
    ),
    "docs/S5_COMPLETION_CHECKLIST.md": (
        "S5 status: not started",
        "Repository boundary contract exists",
        "future game repository validates `world-transvoxel-terrain`",
        "Official MIT-backed backend is used first",
        "Current decision: do not start S5",
    ),
    "docs/REPOSITORY_BOUNDARY_CONTRACT.md": (
        "world-transvoxel-sandbox validates world-transvoxel",
        "future game repository validates world-transvoxel-terrain",
        "Do not use world-transvoxel-sandbox to test world-transvoxel-terrain",
        "game projects must not fork or copy the sandbox",
        "Do not replace these roles with vague names",
    ),
}


def has_phrase(text: str, phrase: str) -> bool:
    return phrase in text or phrase in " ".join(text.split())


def main() -> None:
    errors: list[str] = []
    for relative, phrases in REQUIRED.items():
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"missing milestone contract file: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in phrases:
            if not has_phrase(text, phrase):
                errors.append(f"{relative} missing phrase: {phrase}")
        if "status: complete" in text.lower():
            errors.append(f"{relative} is prematurely marked complete")
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        raise SystemExit(1)
    print(
        "WT_SANDBOX_FUTURE_MILESTONE_CONTRACTS_PASS "
        "s3=defined_not_complete s4=defined_not_started s5=defined_not_started"
    )


if __name__ == "__main__":
    main()
