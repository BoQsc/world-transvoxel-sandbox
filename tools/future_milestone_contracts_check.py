#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED = {
    "docs/S3_VISIBILITY_PRODUCTION_WORKLOAD_CONTRACT.md": (
        "S3 starts only after S1/S2",
        "visibility/frustum behavior",
        "WT_SANDBOX_S3_VISIBILITY_WORKLOAD_PASS",
        "WT_SANDBOX_S3_EXIT_REVIEW_PASS",
        "GPU compute acceleration",
        "Out of scope",
    ),
    "docs/S3_COMPLETION_CHECKLIST.md": (
        "S3 status: not complete",
        "Workload classes are defined",
        "Fast travel / teleport policy",
        "Current decision: do not proceed to S4",
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
        "official MIT-backed World Transvoxel backend first",
        "WT_SANDBOX_S5_SMALL_GAME_DECISION_PASS",
        "0BSD backend replacement",
    ),
    "docs/S5_COMPLETION_CHECKLIST.md": (
        "S5 status: not started",
        "Official MIT-backed backend is used first",
        "Current decision: do not start S5",
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
