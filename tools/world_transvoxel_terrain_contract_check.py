#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED = {
    "docs/WORLD_TRANSVOXEL_TERRAIN_ARCHITECTURE_CONTRACT.md": (
        "Status: complete post-S5 architecture gate",
        "WT_SANDBOX_WORLD_TRANSVOXEL_TERRAIN_CONTRACT_PASS",
        "`world-transvoxel-terrain` is the reusable Godot terrain addon",
        "commit `2219a0f`",
        "official MIT-backed World Transvoxel backend is used first",
        "Optional independent 0BSD backend work remains deferred",
        "load a 2048 x 2048 x 64 terrain profile",
        "support carve, construct, fill, paint, and restore-to-base",
        "preserve edits through save/restart",
        "Compute shaders remain rejected for now by S4",
        "GDScript is not the place for",
        "avoid the old single-large-source-file failure mode",
        "event-based state changes instead of hidden continuous background work",
        "settled terrain must be cold",
        "water and lava",
        "separate game repository",
        "After this gate passes, the next valid action is a separate validation game",
    ),
    "docs/REPOSITORY_BOUNDARY_CONTRACT.md": (
        "world-transvoxel-sandbox validates world-transvoxel",
        "future game repository validates world-transvoxel-terrain",
        "Do not use world-transvoxel-sandbox to test world-transvoxel-terrain",
    ),
    "docs/S5_SMALL_GAME_DECISION.md": (
        "Decision: revise terrain architecture first",
        "The next architecture step is to create or design `world-transvoxel-terrain`",
        "Do not create the game repository yet",
    ),
    "docs/S5_VERTICAL_SLICE_REQUIREMENTS.md": (
        "load a 2048 x 2048 x 64 terrain profile",
        "install `world-transvoxel-terrain`",
        "Do not create the future game repository until `world-transvoxel-terrain`",
    ),
}


def has_phrase(text: str, phrase: str) -> bool:
    return phrase in text or phrase in " ".join(text.split())


def main() -> None:
    errors: list[str] = []
    for relative, phrases in REQUIRED.items():
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"missing terrain architecture contract input: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in phrases:
            if not has_phrase(text, phrase):
                errors.append(f"{relative} missing phrase: {phrase}")

    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        raise SystemExit(1)

    print(
        "WT_SANDBOX_WORLD_TRANSVOXEL_TERRAIN_CONTRACT_PASS "
        "next=separate_validation_game_repository_when_user_approves "
        "game_repository=approved_when_user_asks"
    )


if __name__ == "__main__":
    main()
