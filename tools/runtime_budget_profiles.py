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
    render_apply_budget: int
    min_render: int
    min_collision: int
    status: str


PROFILES = {
    "L0": RuntimeBudgetProfile(
        "L0", 128, "fixed-center LOD0 reference", 4, 0, 512, 1, 0, 0,
        "accepted baseline",
    ),
    "L1": RuntimeBudgetProfile(
        "L1", 256, "staged movement", 3, 1, 512, 1, 97, 97,
        "accepted runtime",
    ),
    "L2": RuntimeBudgetProfile(
        "L2", 512, "staged movement", 3, 1, 1024, 1, 176, 176,
        "accepted runtime",
    ),
    "L3": RuntimeBudgetProfile(
        "L3", 1024, "staged movement", 3, 1, 1024, 1, 201, 201,
        "accepted runtime",
    ),
    "L4": RuntimeBudgetProfile(
        "L4", 2048, "staged movement", 3, 1, 1024, 1, 210, 195,
        "accepted runtime",
    ),
}


def read_text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def require(text: str, phrase: str, label: str, errors: list[str]) -> None:
    if phrase not in text and phrase not in " ".join(text.split()):
        errors.append(f"{label} missing phrase: {phrase}")


def validate() -> list[str]:
    errors: list[str] = []
    contract = read_text("docs/TERRAIN_RUNTIME_BUDGETS.md")
    workload = read_text("docs/S1_LOD0_WORKLOAD_BASELINE.md")
    status = read_text("docs/CURRENT_STATUS.md")
    runtime_tool = read_text("tools/scale_runtime.py")
    workload_tool = read_text("tools/s1_lod0_workload_audit.py")
    workload_audit = read_text("tests/terrain_s1_lod0_workload_audit.gd")
    l2_audit = read_text("tests/terrain_l2_runtime_audit.gd")
    l3_audit = read_text("tests/terrain_l3_runtime_audit.gd")
    l4_audit = read_text("tests/terrain_l4_runtime_audit.gd")
    config = read_text("config/terrain_config.tres")

    for phrase in (
        "Runtime budgets are part of terrain correctness",
        "Every accepted runtime scale must declare its budget profile",
        "| L2 | 512 | staged movement | 3 | 1 | 1024 | 1 | 176 / 176",
        "Fast travel is not proven by L2 runtime acceptance",
        "| L3 | 1024 | staged movement | 3 | 1 | 1024 | 1 | 201 / 201",
        "| L4 | 2048 | staged movement | 3 | 1 | 1024 | 1 | 210 / 195",
        "docs/S1_LOD0_WORKLOAD_BASELINE.md",
        "A conservative full replacement bound is therefore 616 records",
        "Its only scale-specific",
        "The profile passed Godot 4.6.3 and 4.7",
        "L4 therefore uses the same active chunk capacity as L3",
    ):
        require(contract, phrase, "runtime budget contract", errors)

    for phrase in (
        "S1.8/S1.9 baseline",
        "fixed-center LOD0 reference",
        "Autonomous input | disabled before scene entry",
        "Default mining radius | 2",
        "native batched authoritative sample query",
        "Compatibility fallback batch | 15",
        "2,000 ms edit-latency gate",
        "WT_SANDBOX_S1_LOD0_WORKLOAD_AUDIT_PASS",
        "3 carve + exact-restore cycles",
        "GPU power and real rendered-frame cost are not available",
    ):
        require(workload, phrase, "S1 LOD0 workload baseline", errors)

    for phrase in (
        "docs/TERRAIN_RUNTIME_BUDGETS.md",
        "L2 runtime budget: active chunk capacity 1,024",
        "L4 accepted runtime budget: staged movement",
        "docs/S1_LOD0_WORKLOAD_BASELINE.md",
        "production-feel mining latency",
        "tightened 2,000 ms edit-latency ceiling",
        "World Transvoxel 1.0.10-dev",
        "fast travel or disjoint teleport movement",
    ):
        require(status, phrase, "current status", errors)

    require(config, "active_chunk_capacity = 512", "default config", errors)
    require(config, "render_apply_budget = 1", "default config", errors)
    require(
        l2_audit,
        "const ACTIVE_CHUNK_CAPACITY := 1024",
        "L2 runtime audit",
        errors,
    )
    require(l2_audit, "active_capacity=%d", "L2 runtime audit", errors)
    require(l2_audit, "render_apply_budget=%d", "L2 runtime audit", errors)
    require(
        l3_audit,
        "const ACTIVE_CHUNK_CAPACITY := 1024",
        "L3 runtime audit",
        errors,
    )
    require(l3_audit, "active_capacity=%d", "L3 runtime audit", errors)
    require(l3_audit, "render_apply_budget=%d", "L3 runtime audit", errors)
    require(
        l4_audit,
        "const ACTIVE_CHUNK_CAPACITY := 1024",
        "L4 runtime audit",
        errors,
    )
    require(l4_audit, "active_capacity=%d", "L4 runtime audit", errors)
    require(l4_audit, "render_apply_budget=%d", "L4 runtime audit", errors)
    require(workload_tool, "WT_SANDBOX_S1_LOD0_WORKLOAD_AUDIT_PASS", "S1 workload tool", errors)
    require(workload_audit, "WT_SANDBOX_S1_LOD0_WORKLOAD_PASS", "S1 workload audit", errors)
    require(workload_audit, "set(\"input_enabled\", false)", "S1 workload audit", errors)
    require(workload_audit, "EDIT_CYCLES := 3", "S1 workload audit", errors)
    require(read_text("scripts/terrain_lab.gd"), "var mining_radius := 2.0", "terrain lab", errors)
    require(runtime_tool, '"L2": {', "scale runtime tool", errors)
    require(runtime_tool, '"L3": {', "scale runtime tool", errors)
    require(runtime_tool, '"L4": {', "scale runtime tool", errors)
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
            f"render_apply_budget={profile.render_apply_budget} "
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
    print("WT_SANDBOX_RUNTIME_BUDGETS_PASS profiles=5")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
