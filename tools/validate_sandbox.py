#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "WORLD_TRANSVOXEL_RELEASE_MANIFEST.json"
LOCK_PATH = ROOT / "VENDOR_LOCK.json"
SOURCE_LIMITS = {".gd": 250, ".gdshader": 400, ".py": 600}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return [line.replace("\\", "/") for line in result.stdout.splitlines()]


def main() -> int:
    errors: list[str] = []
    required = (
        "LICENSE",
        "README.md",
        "VENDOR_LOCK.json",
        "WORLD_TRANSVOXEL_LICENSE_SCOPE.md",
        "WORLD_TRANSVOXEL_RELEASE_MANIFEST.json",
        "LICENSES/MIT-Transvoxel.txt",
        "project.godot",
        "scenes/terrain_lab.tscn",
        "scripts/terrain_lab.gd",
        "scripts/terrain_recovery_policy.gd",
        "scripts/terrain_recovery_policy.gd.uid",
        "scripts/terrain_sculpt_controller.gd",
        "scripts/fly_camera.gd",
        "scripts/terrain_visualizer.gd",
        "scripts/terrain_overlay.gd",
        "shaders/terrain_material.gdshader",
        "materials/terrain_material.tres",
        "config/terrain_config.tres",
        "tools/generate_world.py",
        "tools/runtime_budget_profiles.py",
        "tools/scale_ladder.py",
        "tools/scale_runtime.py",
        "tools/scale_visual.py",
        "tools/capture_lod_popping.py",
        "tools/capture_visuals.py",
        "tools/test_sandbox.py",
        "tests/sandbox_smoke.gd",
        "tests/terrain_geometry_audit.gd",
        "tests/terrain_idle_audit.gd",
        "tests/terrain_interaction_audit.gd",
        "tests/terrain_l1_runtime_audit.gd",
        "tests/terrain_l1_runtime_audit.gd.uid",
        "tests/terrain_l2_runtime_audit.gd",
        "tests/terrain_l2_runtime_audit.gd.uid",
        "tests/terrain_l3_runtime_audit.gd",
        "tests/terrain_l3_runtime_audit.gd.uid",
        "tests/terrain_l4_runtime_audit.gd",
        "tests/terrain_l4_runtime_audit.gd.uid",
        "tests/terrain_l1_visual_capture.gd",
        "tests/terrain_l1_visual_capture.gd.uid",
        "tests/terrain_l2_visual_capture.gd",
        "tests/terrain_l2_visual_capture.gd.uid",
        "tests/terrain_l3_visual_capture.gd",
        "tests/terrain_l3_visual_capture.gd.uid",
        "tests/terrain_l4_visual_capture.gd",
        "tests/terrain_l4_visual_capture.gd.uid",
        "tests/terrain_lod_pop_capture.gd",
        "tests/terrain_lod_pop_capture.gd.uid",
        "tests/terrain_volumetric_audit.gd",
        "tests/terrain_motion_audit.gd",
        "tests/terrain_seam_audit.gd",
        "tests/terrain_visual_capture.gd",
        "docs/CURRENT_STATUS.md",
        "docs/ROADMAP.md",
        "docs/TERRAIN_ACCEPTANCE_STANDARD.md",
        "docs/TERRAIN_RUNTIME_BUDGETS.md",
        "docs/TERRAIN_RECOVERY_CONTRACT.md",
        "addons/world_transvoxel/bin/world_transvoxel.windows.template_debug.x86_64.dll",
        "addons/world_transvoxel/bin/world_transvoxel.windows.template_release.x86_64.dll",
    )
    for relative in required:
        if not (ROOT / relative).is_file():
            errors.append(f"missing required file: {relative}")

    if MANIFEST_PATH.is_file() and LOCK_PATH.is_file():
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
        expected_manifest_hash = lock["world_transvoxel"]["manifest_sha256"]
        if sha256(MANIFEST_PATH) != expected_manifest_hash:
            errors.append("vendored release manifest hash mismatch")
        records = manifest.get("files", [])
        listed_addon_paths = {
            record["path"]
            for record in records
            if record["path"].startswith("addons/world_transvoxel/")
        }
        addon_root = ROOT / "addons" / "world_transvoxel"
        actual_addon_paths = {
            path.relative_to(ROOT).as_posix()
            for path in addon_root.rglob("*")
            if path.is_file()
        }
        if actual_addon_paths != listed_addon_paths:
            missing = sorted(listed_addon_paths - actual_addon_paths)
            unlisted = sorted(actual_addon_paths - listed_addon_paths)
            errors.append(
                "vendored addon payload differs from manifest: "
                f"missing={missing[:10]}, unlisted={unlisted[:10]}"
            )
        for record in records:
            relative = record["path"]
            if not relative.startswith("addons/world_transvoxel/"):
                continue
            path = ROOT / relative
            if (
                not path.is_file()
                or path.stat().st_size != record["bytes"]
                or sha256(path) != record["sha256"]
            ):
                errors.append(f"vendored addon file mismatch: {relative}")

    contract = ROOT / "docs" / "TERRAIN_RECOVERY_CONTRACT.md"
    if contract.is_file():
        text = contract.read_text(encoding="utf-8")
        for phrase in (
            "manual_exact_restore",
            "restore_to_base",
            "timed_regeneration",
            "surface_relaxation",
            "structural_stability",
            "fluid_equilibrium",
            "settled terrain must stay cold",
        ):
            if phrase not in text:
                errors.append(f"recovery contract is missing phrase: {phrase}")

    standard = ROOT / "docs" / "TERRAIN_ACCEPTANCE_STANDARD.md"
    if standard.is_file():
        text = standard.read_text(encoding="utf-8")
        for phrase in (
            "standards-first",
            "Large-terrain ladder",
            "Dynamic LOD popping remains a blocker",
            "Settled terrain must stay cold",
            "Finite boundary guards",
            "Generation preflight must account",
            "no tracked PowerShell workflow scripts",
            "GDScript is glue",
            "Compute shaders are deferred",
            "Decision tracking",
        ):
            if phrase not in text:
                errors.append(f"terrain standard is missing phrase: {phrase}")

    status = ROOT / "docs" / "CURRENT_STATUS.md"
    if status.is_file():
        text = status.read_text(encoding="utf-8")
        for phrase in (
            "S1 - visual acceptance and dynamic mixed-LOD quality",
            "S2.1 - Python scale-ladder generation proof is complete",
            "S2.2 - L1 runtime acceptance path is complete",
            "S2.3 - L1 visual capture and artifact classification is complete",
            "S2.4 - L2 512 generation preflight is complete",
            "S2.5 - L2 runtime acceptance path",
            "S2.6 - L2 visual capture and artifact classification is complete",
            "S2.7 - L3 1024 generation preflight is complete",
            "S2.8 - L3 runtime budget planning is complete",
            "S2.9 - L3 runtime acceptance is complete",
            "S2.10 - L3 visual capture and artifact classification is complete",
            "S1.2 previously observed 79 replacement frames",
            "S1.3 - native dynamic LOD visual transition smoothing is complete",
            "S2.13 - L4 bounded generation, runtime, and static visual capture are complete",
            "S1.4 - visual acceptance and default dynamic LOD policy decision",
            "lod_transition_native_fade_without_geomorph_pending_visual_acceptance",
            "maximum render-set delta in one observed frame: 8",
            "maximum native fading resources: 30",
            "fade frames observed: 101",
            "improved from 61 to 8",
            "L4 accepted runtime budget: staged movement",
            "docs/TERRAIN_RUNTIME_BUDGETS.md",
            "GDScript is glue",
            "Deferred by rule",
        ):
            if phrase not in text:
                errors.append(f"current status is missing phrase: {phrase}")

    budget_check = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "runtime_budget_profiles.py"), "--check"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    if budget_check.returncode != 0:
        errors.append(
            "runtime budget profile validation failed: "
            + (budget_check.stdout + budget_check.stderr).strip()
        )

    generator = (ROOT / "tools" / "generate_world.py").read_text(encoding="utf-8")
    scale_ladder = (ROOT / "tools" / "scale_ladder.py").read_text(encoding="utf-8")
    scale_runtime = (ROOT / "tools" / "scale_runtime.py").read_text(encoding="utf-8")
    scale_visual = (ROOT / "tools" / "scale_visual.py").read_text(encoding="utf-8")
    for phrase in (
        '"L4": ScaleProfile(',
        '"bounded"',
        "requires scale-ladder resource preflight",
        "--resource-preflight-approved",
        "source_generation_mode",
        "streamed_x_rows",
    ):
        if phrase not in generator:
            errors.append(f"L4 generation guard is missing phrase: {phrase}")
    for phrase in (
        "BOUNDED_BAKE_SOURCE_CACHE_BYTES",
        "estimated_bake_working_set_bytes",
        "generator_memory_basis",
        "bounded_bake_memory_basis",
        "estimated_peak_memory_bytes",
        "required_available_memory_bytes",
        "--estimate-only",
        "allow_bounded_generation",
    ):
        if phrase not in scale_ladder:
            errors.append(f"L4 feasibility gate is missing phrase: {phrase}")
    for phrase in (
        '"L4": "res://tests/terrain_l4_runtime_audit.gd"',
        '"WT_SANDBOX_L4_RUNTIME_PASS"',
        '"L4": 900',
        '"active_chunk_capacity": 1024',
    ):
        if phrase not in scale_runtime:
            errors.append(f"L4 runtime runner is missing phrase: {phrase}")
    for phrase in (
        '"L4": "res://tests/terrain_l4_visual_capture.gd"',
        '"WT_SANDBOX_L4_VISUAL_CAPTURE_PASS"',
        '"WT_SANDBOX_L4_BOUNDARY_PASS"',
        '"L4": 420',
    ):
        if phrase not in scale_visual:
            errors.append(f"L4 visual runner is missing phrase: {phrase}")
    try:
        from scale_ladder import resource_estimate

        estimate, _warnings, blockers = resource_estimate("L4")
        if (
            estimate["estimated_source_bytes"] != 1_744_930_926
            or estimate["expected_pages"] != 73_728
            or estimate["estimated_generator_working_set_bytes"] != 68_160_000
            or estimate["estimated_bake_working_set_bytes"] != 77_840_384
            or estimate["estimated_peak_memory_bytes"] != 77_840_384
            or estimate["required_available_memory_bytes"] != 614_711_296
            or estimate["generation_mode"] != "bounded"
            or any("unsupported generation mode" in blocker for blocker in blockers)
        ):
            errors.append(f"L4 feasibility estimate drifted: {estimate}")
    except (ImportError, KeyError, TypeError, ValueError) as error:
        errors.append(f"L4 feasibility estimate could not be checked: {error}")

    files = tracked_files()
    for relative in files:
        path = ROOT / relative
        if not path.is_file() or relative.startswith("addons/world_transvoxel/"):
            continue
        suffix = path.suffix.lower()
        if suffix in SOURCE_LIMITS:
            count = sum(
                1 for _ in path.open(encoding="utf-8", errors="replace")
            )
            if count > SOURCE_LIMITS[suffix]:
                errors.append(
                    f"source limit exceeded: {relative} "
                    f"({count} > {SOURCE_LIMITS[suffix]})"
                )
        if relative.lower().endswith(".ps1"):
            errors.append(f"platform-specific shell script is tracked: {relative}")

    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        print(f"Sandbox validation failed with {len(errors)} error(s).")
        return 1
    print(
        "WT_SANDBOX_VALIDATION_PASS "
        f"vendored_files={len(json.loads(MANIFEST_PATH.read_text())['files'])} "
        f"project_files={len(files)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
