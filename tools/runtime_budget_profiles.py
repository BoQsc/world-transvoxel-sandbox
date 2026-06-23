#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class RuntimeBudgetProfile:
    level: str
    horizontal_cells: int
    movement_class: str
    radius_chunks: int
    maximum_lod: int
    active_chunk_capacity: int
    min_render: int
    min_collision: int
    status: str


PROFILES = {
    "L0": RuntimeBudgetProfile(
        "L0", 128, "fixed-center LOD0 reference", 4, 0, 512, 0, 0,
        "accepted baseline",
    ),
    "L1": RuntimeBudgetProfile(
        "L1", 256, "staged movement", 3, 1, 512, 97, 97,
        "accepted runtime",
    ),
    "L2": RuntimeBudgetProfile(
        "L2", 512, "staged movement", 3, 1, 1024, 176, 176,
        "accepted runtime",
    ),
    "L3": RuntimeBudgetProfile(
        "L3", 1024, "staged movement", 3, 1, 1024, 201, 201,
        "accepted runtime",
    ),
}


def read_text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def require(text: str, phrase: str, label: str, errors: list[str]) -> None:
    if phrase not in text:
        errors.append(f"{label} missing phrase: {phrase}")


def validate() -> list[str]:
    errors: list[str] = []
    contract = read_text("docs/TERRAIN_RUNTIME_BUDGETS.md")
    status = read_text("docs/CURRENT_STATUS.md")
    runtime_tool = read_text("tools/scale_runtime.py")
    l2_audit = read_text("tests/terrain_l2_runtime_audit.gd")
    l3_audit = read_text("tests/terrain_l3_runtime_audit.gd")
    config = read_text("config/terrain_config.tres")

    for phrase in (
        "Runtime budgets are part of terrain correctness",
        "Every accepted runtime scale must declare its budget profile",
        "| L2 | 512 | staged movement | 3 | 1 | 1024 | 176 / 176",
        "Fast travel is not proven by L2 runtime acceptance",
        "| L3 | 1024 | staged movement | 3 | 1 | 1024 | 201 / 201",
        "A conservative full replacement bound is therefore 616 records",
        "Its only scale-specific",
        "The profile passed Godot 4.6.3 and 4.7",
    ):
        require(contract, phrase, "runtime budget contract", errors)

    for phrase in (
        "docs/TERRAIN_RUNTIME_BUDGETS.md",
        "L2 runtime budget: active chunk capacity 1,024",
        "fast travel or disjoint teleport movement",
    ):
        require(status, phrase, "current status", errors)

    require(config, "active_chunk_capacity = 512", "default config", errors)
    require(
        l2_audit,
        "const ACTIVE_CHUNK_CAPACITY := 1024",
        "L2 runtime audit",
        errors,
    )
    require(l2_audit, "active_capacity=%d", "L2 runtime audit", errors)
    require(
        l3_audit,
        "const ACTIVE_CHUNK_CAPACITY := 1024",
        "L3 runtime audit",
        errors,
    )
    require(l3_audit, "active_capacity=%d", "L3 runtime audit", errors)
    require(runtime_tool, '"L2": {', "scale runtime tool", errors)
    require(runtime_tool, '"L3": {', "scale runtime tool", errors)
    require(runtime_tool, '"active_chunk_capacity": 1024', "scale runtime tool", errors)
    return errors


def print_profiles() -> None:
    for profile in PROFILES.values():
        print(
            "WT_SANDBOX_RUNTIME_BUDGET "
            f"level={profile.level} "
            f"horizontal={profile.horizontal_cells} "
            f"movement={profile.movement_class!r} "
            f"radius={profile.radius_chunks} "
            f"max_lod={profile.maximum_lod} "
            f"active_capacity={profile.active_chunk_capacity} "
            f"min_render={profile.min_render} "
            f"min_collision={profile.min_collision} "
            f"status={profile.status!r}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report and validate terrain runtime budget profiles."
    )
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    if not arguments.check:
        print_profiles()
        return 0
    errors = validate()
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        print(f"Runtime budget validation failed with {len(errors)} error(s).")
        return 1
    print("WT_SANDBOX_RUNTIME_BUDGETS_PASS profiles=4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
