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


def has_phrase(text: str, phrase: str) -> bool:
    return phrase in text or phrase in " ".join(text.split())


def main() -> int:
    errors: list[str] = []
    required = (
        "LICENSE",
        "README.md",
        "VENDOR_LOCK.json",
        "WORLD_TRANSVOXEL_LICENSE_SCOPE.md",
        "WORLD_TRANSVOXEL_RELEASE_MANIFEST.json",
        "LICENSES/MIT-Transvoxel.txt",
        "artifacts/.gdignore",
        "project.godot",
        "scenes/terrain_lab.tscn",
        "scripts/terrain_lab.gd",
        "scripts/terrain_recovery_policy.gd",
        "scripts/terrain_recovery_policy.gd.uid",
        "scripts/terrain_sculpt_capture.gd",
        "scripts/terrain_sculpt_capture.gd.uid",
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
        "tools/s1_lod0_workload_audit.py",
        "tools/s1_lod0_gallery_audit.py",
        "tools/s1_s2_completion_checklist.py",
        "tools/s2_exit_review.py",
        "tools/capture_lod_popping.py",
        "tools/capture_lod_surface.py",
        "tools/capture_lod_temporal.py",
        "tools/capture_lod_temporal_multiview.py",
        "tools/review_lod_temporal.py",
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
        "tests/terrain_probe_util.gd",
        "tests/terrain_probe_util.gd.uid",
        "tests/terrain_s1_default_policy_audit.gd",
        "tests/terrain_s1_default_policy_audit.gd.uid",
        "tests/terrain_s1_lod0_workload_audit.gd",
        "tests/terrain_s1_lod0_workload_audit.gd.uid",
        "tests/terrain_s1_lod0_persistence_audit.gd",
        "tests/terrain_s1_lod0_persistence_audit.gd.uid",
        "tests/terrain_lod_pop_capture.gd",
        "tests/terrain_lod_pop_capture.gd.uid",
        "tests/terrain_lod_surface_capture.gd",
        "tests/terrain_lod_surface_capture.gd.uid",
        "tests/terrain_lod_temporal_capture.gd",
        "tests/terrain_lod_temporal_capture.gd.uid",
        "tests/terrain_lod_temporal_multiview_capture.gd",
        "tests/terrain_lod_temporal_multiview_capture.gd.uid",
        "tests/terrain_volumetric_audit.gd",
        "tests/terrain_motion_audit.gd",
        "tests/terrain_seam_audit.gd",
        "tests/terrain_visual_capture.gd",
        "docs/CURRENT_STATUS.md",
        "docs/ROADMAP.md",
        "docs/TERRAIN_ACCEPTANCE_STANDARD.md",
        "docs/TERRAIN_RUNTIME_BUDGETS.md",
        "docs/TERRAIN_RECOVERY_CONTRACT.md",
        "docs/S1_LOD0_WORKLOAD_BASELINE.md",
        "docs/S1_LOD0_GALLERY_AUDIT.md",
        "docs/S1_S2_COMPLETION_CHECKLIST.md",
        "docs/S2_SCALE_LADDER_EXIT_REVIEW.md",
        "docs/S1_DYNAMIC_LOD_POLICY.md",
        "docs/WORLD_TRANSVOXEL_TERRAIN_ARCHITECTURE_CONTRACT.md",
        "tools/world_transvoxel_terrain_contract_check.py",
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
            if not has_phrase(text, phrase):
                errors.append(f"recovery contract is missing phrase: {phrase}")

    readme = ROOT / "README.md"
    if readme.is_file():
        text = readme.read_text(encoding="utf-8")
        for phrase in (
            "S1.10 explicitly rejects/demotes dynamic mixed LOD",
            "diagnostic-only until stronger evidence",
            "Human review is final qualitative confirmation",
            "WT_SANDBOX_S1_LOD0_GALLERY_AUDIT_PASS",
            "WT_SANDBOX_S2_EXIT_REVIEW_PASS",
            "WT_SANDBOX_S1_S2_COMPLETION_CHECKLIST_PASS",
        ):
            if not has_phrase(text, phrase):
                errors.append(f"readme is missing phrase: {phrase}")

    standard = ROOT / "docs" / "TERRAIN_ACCEPTANCE_STANDARD.md"
    if standard.is_file():
        text = standard.read_text(encoding="utf-8")
        for phrase in (
            "standards-first",
            "Large-terrain ladder",
            "Dynamic LOD popping is demoted by the S1.10 documented standard",
            "Normal sandbox/playtest defaults are conservative",
            "docs/S1_DYNAMIC_LOD_POLICY.md",
            "LOD-debug captures are diagnostic only",
            "current automated gross-pop and region-bounds gates",
            "front/side/diagonal multi-view harness",
            "render_apply_budget = 1",
            "Human review is final qualitative confirmation",
            "does not block technical",
            "cannot replace automated gates",
            "stronger evidence or a native mitigation",
            "final qualitative confirmation does not replace technical correctness",
            "docs/S1_LOD0_WORKLOAD_BASELINE.md",
            "docs/S1_LOD0_GALLERY_AUDIT.md",
            "WT_SANDBOX_S1_LOD0_GALLERY_AUDIT_PASS",
            "Do not jump milestones",
            "Settled terrain must stay cold",
            "Finite boundary guards",
            "Generation preflight must account",
            "no tracked PowerShell workflow scripts",
            "GDScript is glue",
            "Compute shaders are deferred",
            "Decision tracking",
            "Containment is not completion",
            "S1 default-policy gate is part of acceptance",
        ):
            if not has_phrase(text, phrase):
                errors.append(f"terrain standard is missing phrase: {phrase}")

    roadmap = ROOT / "docs" / "ROADMAP.md"
    if roadmap.is_file():
        text = roadmap.read_text(encoding="utf-8")
        for phrase in (
            "S1.10 dynamic mixed-LOD default-policy",
            "Dynamic mixed LOD is rejected/demoted as default",
            "tests/terrain_s1_default_policy_audit.gd",
            "S1.11 adds the accepted fixed-center LOD0 gallery",
            "WT_SANDBOX_S1_LOD0_GALLERY_AUDIT_PASS",
            "Technical exit: complete by S1.11",
            "Human review remains",
            "final human qualitative confirmation",
            "S3 may start after S2 exit",
        ):
            if not has_phrase(text, phrase):
                errors.append(f"roadmap is missing phrase: {phrase}")

    budgets = ROOT / "docs" / "TERRAIN_RUNTIME_BUDGETS.md"
    if budgets.is_file():
        text = budgets.read_text(encoding="utf-8")
        for phrase in (
            "docs/S1_LOD0_WORKLOAD_BASELINE.md",
            "final human qualitative confirmation",
            "dynamic seamless LOD appearance",
        ):
            if not has_phrase(text, phrase):
                errors.append(f"runtime budgets are missing phrase: {phrase}")

    workload = ROOT / "docs" / "S1_LOD0_WORKLOAD_BASELINE.md"
    if workload.is_file():
        text = workload.read_text(encoding="utf-8")
        for phrase in (
            "S1.8/S1.9 baseline",
            "fixed-center LOD0 reference",
            "Default mining radius | 2",
            "native batched authoritative sample query",
            "Compatibility fallback batch | 15",
            "2,000 ms edit-latency gate",
            "WT_SANDBOX_S1_LOD0_WORKLOAD_AUDIT_PASS",
            "3 carve + exact-restore cycles",
            "GPU power and real rendered-frame cost are not available",
        ):
            if not has_phrase(text, phrase):
                errors.append(f"S1 workload baseline is missing phrase: {phrase}")

    dynamic_policy = ROOT / "docs" / "S1_DYNAMIC_LOD_POLICY.md"
    if dynamic_policy.is_file():
        text = dynamic_policy.read_text(encoding="utf-8")
        for phrase in (
            "S1.10 rejects dynamic mixed LOD as the default accepted playtest policy",
            "fixed-center LOD0 reference mode",
            "`maximum_lod` | `0`",
            "`streaming_follows_viewer` | `false`",
            "diagnostic mode",
            "does not prove all camera angles",
            "user-visible popping/glitching concern",
            "not as normal terrain behavior",
            "tests/terrain_s1_default_policy_audit.gd",
            "autonomous input disabled",
            "all rendered chunks are LOD0",
            "Human review remains final qualitative confirmation",
        ):
            if not has_phrase(text, phrase):
                errors.append(f"S1 dynamic LOD policy is missing phrase: {phrase}")

    gallery = ROOT / "docs" / "S1_LOD0_GALLERY_AUDIT.md"
    if gallery.is_file():
        text = gallery.read_text(encoding="utf-8")
        for phrase in (
            "S1.11 Accepted LOD0 Gallery and Persistence Audit",
            "fixed-center LOD0 reference",
            "WT_SANDBOX_S1_LOD0_GALLERY_AUDIT_PASS",
            "tests/terrain_s1_lod0_persistence_audit.gd",
            "WT_SANDBOX_S1_LOD0_PERSISTENCE_PASS",
            "closed-boundary render/collision ray probe",
            "S1 technical exit criteria are now covered by explicit gates",
            "dynamic mixed LOD remains diagnostic-only by S1.10",
        ):
            if not has_phrase(text, phrase):
                errors.append(f"S1 LOD0 gallery audit doc is missing phrase: {phrase}")

    completion = ROOT / "docs" / "S1_S2_COMPLETION_CHECKLIST.md"
    if completion.is_file():
        text = completion.read_text(encoding="utf-8")
        for phrase in (
            "S1 technical exit: complete by S1.11",
            "S2 automated exit: complete by `WT_SANDBOX_S2_EXIT_REVIEW_PASS`",
            "Go to S3 contract: yes",
            "not skipped S1/S2 work",
        ):
            if not has_phrase(text, phrase):
                errors.append(f"S1/S2 checklist is missing phrase: {phrase}")

    status = ROOT / "docs" / "CURRENT_STATUS.md"
    if status.is_file():
        text = status.read_text(encoding="utf-8")
        for phrase in (
            "S2 automated scale-ladder exit evidence is complete",
            "WT_SANDBOX_S2_EXIT_REVIEW_PASS",
            "WT_SANDBOX_S1_S2_COMPLETION_CHECKLIST_PASS",
            "S1 now has a technical default-policy decision",
            "Unresolved blockers kept visible",
            "docs/S1_LOD0_WORKLOAD_BASELINE.md",
            "docs/S1_LOD0_GALLERY_AUDIT.md",
            "docs/WORLD_TRANSVOXEL_TERRAIN_ARCHITECTURE_CONTRACT.md",
            "tools/world_transvoxel_terrain_contract_check.py",
            "Do not start later-milestone work",
            "dynamic mixed LOD is rejected/demoted as default gameplay by S1.10",
            "Human review remains final",
            "does not block technical milestone progress",
            "replace automated/capture-based correctness",
            "final human qualitative confirmation",
            "Too many instances using shader instance variables",
            "S1.11 - accepted fixed-center LOD0 gallery and restart-persistence audit",
            "WT_SANDBOX_S1_LOD0_GALLERY_AUDIT_PASS",
            "WT_SANDBOX_S1_LOD0_PERSISTENCE_PASS",
            "No automated hard gallery blocker is detected",
            "S1.10 - dynamic mixed-LOD default-policy decision",
            "WT_SANDBOX_S1_DEFAULT_POLICY_PASS",
            "tests/terrain_s1_default_policy_audit.gd",
            "S1.9 - native batched exact-restore capture",
            "production-feel mining latency",
            "tools/s1_lod0_workload_audit.py",
            "normal sandbox/playtest defaults are fixed-center LOD0 reference mode",
            "dynamic mixed LOD remains available only through explicit diagnostic scripts",
            "temporal_surface_gross_pop_gate_pass_pending_human_review",
            "L4 accepted runtime budget: staged movement",
            "docs/TERRAIN_RUNTIME_BUDGETS.md",
            "Deferred by rule",
        ):
            if not has_phrase(text, phrase):
                errors.append(f"current status is missing phrase: {phrase}")

    workload_tool = ROOT / "tools" / "s1_lod0_workload_audit.py"
    if workload_tool.is_file():
        text = workload_tool.read_text(encoding="utf-8")
        for phrase in (
            "WT_SANDBOX_S1_LOD0_WORKLOAD_AUDIT_PASS",
            "terrain_s1_lod0_workload_audit.gd",
            "--disable-player-input",
            "process_sampling",
        ):
            if not has_phrase(text, phrase):
                errors.append(f"S1 workload tool is missing phrase: {phrase}")

    workload_audit = ROOT / "tests" / "terrain_s1_lod0_workload_audit.gd"
    if workload_audit.is_file():
        text = workload_audit.read_text(encoding="utf-8")
        for phrase in (
            "WT_SANDBOX_S1_LOD0_WORKLOAD_PASS",
            "set(\"input_enabled\", false)",
            "MAX_JOURNAL_GROWTH_BYTES",
            "EDIT_CYCLES := 3",
            "ProbeUtil.probe_render_and_collision",
        ):
            if not has_phrase(text, phrase):
                errors.append(f"S1 workload audit is missing phrase: {phrase}")

    gallery_tool = ROOT / "tools" / "s1_lod0_gallery_audit.py"
    if gallery_tool.is_file():
        text = gallery_tool.read_text(encoding="utf-8")
        for phrase in (
            "WT_SANDBOX_S1_LOD0_GALLERY_AUDIT_PASS",
            "terrain_s1_lod0_persistence_audit.gd",
            "WT_SANDBOX_S1_LOD0_PERSISTENCE_PASS",
            "WT_SANDBOX_BOUNDARY_PROBE",
            "ERROR/SCRIPT ERROR output is a hard failure",
            "dynamic mixed-LOD seamless gameplay",
        ):
            if not has_phrase(text, phrase):
                errors.append(f"S1 gallery tool is missing phrase: {phrase}")

    persistence_audit = ROOT / "tests" / "terrain_s1_lod0_persistence_audit.gd"
    if persistence_audit.is_file():
        text = persistence_audit.read_text(encoding="utf-8")
        for phrase in (
            "WT_SANDBOX_S1_LOD0_PERSISTENCE_PASS",
            "set(\"input_enabled\", false)",
            "begin_edit_transaction",
            "restart=exact",
            "mesh=stable",
            "world.wtedit",
        ):
            if not has_phrase(text, phrase):
                errors.append(f"S1 persistence audit is missing phrase: {phrase}")

    default_policy_audit = ROOT / "tests" / "terrain_s1_default_policy_audit.gd"
    if default_policy_audit.is_file():
        text = default_policy_audit.read_text(encoding="utf-8")
        for phrase in (
            "WT_SANDBOX_S1_DEFAULT_POLICY_PASS",
            "set(\"input_enabled\", false)",
            "radius_chunks != 4",
            "maximum_lod != 0",
            "streaming_follows_viewer",
            "fixed_streaming_position",
            "render_apply_budget",
            "_all_render_chunks_are_lod0",
            "viewer movement changed the accepted fixed-anchor demand",
        ):
            if not has_phrase(text, phrase):
                errors.append(f"S1 default policy audit is missing phrase: {phrase}")

    sculpt_capture = ROOT / "scripts" / "terrain_sculpt_capture.gd"
    if sculpt_capture.is_file():
        text = sculpt_capture.read_text(encoding="utf-8")
        for phrase in (
            "request_authoritative_samples",
            "const MAX_CAPTURE_REQUESTS := 15",
            "_capture_density_samples_batch",
        ):
            if not has_phrase(text, phrase):
                errors.append(f"terrain sculpt capture is missing phrase: {phrase}")

    lab = ROOT / "scripts" / "terrain_lab.gd"
    if lab.is_file():
        text = lab.read_text(encoding="utf-8")
        for phrase in (
            "var radius_chunks := 4",
            "var maximum_lod := 0",
            "var streaming_follows_viewer := false",
            "var mining_radius := 2.0",
        ):
            if not has_phrase(text, phrase):
                errors.append(f"terrain lab default is missing phrase: {phrase}")

    scene = ROOT / "scenes" / "terrain_lab.tscn"
    if scene.is_file():
        text = scene.read_text(encoding="utf-8")
        for phrase in (
            "radius_chunks = 4",
            "maximum_lod = 0",
            "streaming_follows_viewer = false",
        ):
            if not has_phrase(text, phrase):
                errors.append(f"terrain lab scene default is missing phrase: {phrase}")

    overlay = ROOT / "scripts" / "terrain_overlay.gd"
    if overlay.is_file():
        text = overlay.read_text(encoding="utf-8")
        for phrase in (
            "World Transvoxel 1.0.11-dev Visual Sandbox",
            "fixed LOD0 reference",
            "fixed mixed-LOD diagnostic",
        ):
            if not has_phrase(text, phrase):
                errors.append(f"terrain overlay is missing phrase: {phrase}")

    test_runner = ROOT / "tools" / "test_sandbox.py"
    if test_runner.is_file():
        text = test_runner.read_text(encoding="utf-8")
        for phrase in (
            "terrain_s1_default_policy_audit.gd",
            "WT_SANDBOX_S1_DEFAULT_POLICY_PASS",
        ):
            if not has_phrase(text, phrase):
                errors.append(f"sandbox test runner is missing phrase: {phrase}")

    for name, command in (
        ("runtime budget profile", [sys.executable, str(ROOT / "tools" / "runtime_budget_profiles.py"), "--check"]),
        ("future milestone contract", [sys.executable, str(ROOT / "tools" / "future_milestone_contracts_check.py")]),
    ):
        result = subprocess.run(command, cwd=ROOT, check=False, text=True, capture_output=True)
        if result.returncode != 0:
            errors.append(f"{name} validation failed: " + (result.stdout + result.stderr).strip())

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
