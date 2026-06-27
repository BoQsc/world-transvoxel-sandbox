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
        "tools/s3_restore_to_base_audit.py",
        "WT_SANDBOX_S3_RESTORE_TO_BASE_AUDIT_PASS",
        "tools/s3_visual_gpu_audit.py",
        "WT_SANDBOX_S3_VISUAL_GPU_AUDIT_PASS",
        "tools/s3_exit_review.py",
        "WT_SANDBOX_S3_EXIT_REVIEW_PASS",
        "GPU compute acceleration",
        "Out of scope",
    ),
    "docs/S3_COMPLETION_CHECKLIST.md": (
        "S3 status: complete",
        "Workload classes are defined",
        "WT_SANDBOX_S3_VISIBILITY_WORKLOAD_AUDIT_PASS",
        "WT_SANDBOX_S3_RESTORE_TO_BASE_AUDIT_PASS",
        "WT_SANDBOX_S3_VISUAL_GPU_AUDIT_PASS",
        "WT_SANDBOX_S3_EXIT_REVIEW_PASS",
        "Fast travel / teleport policy",
        "Forward-biased prefetch policy is implemented or rejected | Complete",
        "`restore_to_base` is implemented/audited or explicitly deferred | Complete",
        "Visual/GPU artifact acceptance exists | Complete",
        "S3 exit review exists | Complete",
        "Current decision: S3 is complete; proceed only to S4 decision work",
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
        "Explicit `restore_to_base` is covered by `tools/s3_restore_to_base_audit.py`, not by this visibility baseline",
        "Graphical visual acceptance is covered by `tools/s3_visual_gpu_audit.py`",
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
    "tools/s3_restore_to_base_audit.py": (
        "WT_SANDBOX_S3_RESTORE_TO_BASE_PASS",
        "world-transvoxel-sandbox.s3-restore-to-base.v1",
        "restore_to_base is explicit",
        "WT_SANDBOX_S3_RESTORE_TO_BASE_AUDIT_PASS",
    ),
    "tests/terrain_s3_restore_to_base_audit.gd": (
        "WT_SANDBOX_S3_RESTORE_TO_BASE_PASS",
        "set(\"input_enabled\", false)",
        "BaseSampler.l4_sample",
        "restore_last_carve_to_base",
    ),
    "tools/s3_visual_gpu_audit.py": (
        "WT_SANDBOX_S3_VISUAL_GPU_AUDIT_PASS",
        "world-transvoxel-sandbox.s3-visual-gpu.v1",
        "contact_sheet",
        "hardware vendor GPU timing beyond graphical frame interval",
    ),
    "tests/terrain_s3_visual_gpu_audit.gd": (
        "WT_SANDBOX_S3_VISUAL_GPU_PASS",
        "set(\"input_enabled\", false)",
        "WT_SANDBOX_S3_VISUAL_CAPTURE",
        "render_fading_resources",
        "ProbeUtil.probe_render_and_collision",
    ),
    "tools/s3_exit_review.py": (
        "WT_SANDBOX_S3_EXIT_REVIEW_PASS",
        "world-transvoxel-sandbox.s3-exit-review.v1",
        "visibility_workload_baseline_pass",
        "visual_gpu_acceptance_pass",
        "restore_to_base_pass",
    ),
    "docs/S3_EXIT_REVIEW.md": (
        "S3 status: complete",
        "WT_SANDBOX_S3_EXIT_REVIEW_PASS",
        "GPU compute acceleration",
        "Next valid action after S3 is S4 decision work",
    ),
    "scripts/terrain_base_sampler.gd": (
        "class_name WtSandboxTerrainBaseSampler",
        "terrain_sample",
        "sphere_grid_points",
    ),
    "scripts/terrain_sculpt_controller.gd": (
        "restore_last_carve_to_base",
        "MODE_RESTORE_BASE",
        "BaseSampler.terrain_sample",
        "_base_horizontal_cells",
    ),
    "scripts/terrain_recovery_policy.gd": (
        "\"available_targets\"",
        "TARGET_BASE_TERRAIN",
        "\"enabled_targets\": [TARGET_PRE_EDIT_SNAPSHOT]",
    ),
    "docs/S4_M6_DECISION_CONTRACT.md": (
        "S4 starts only after S3 exits",
        "measured bottleneck",
        "tools/s4_bottleneck_selection.py",
        "WT_SANDBOX_S4_BOTTLENECK_SELECTION_PASS",
        "tools/s4_cpu_edit_phase_baseline.py",
        "WT_SANDBOX_S4_CPU_EDIT_PHASE_BASELINE_AUDIT_PASS",
        "WT_SANDBOX_S4_M6_DECISION_PASS",
        "CPU/headless fallback",
    ),
    "docs/S4_COMPLETION_CHECKLIST.md": (
        "S4 status: complete",
        "S3 bottleneck selected | Complete",
        "WT_SANDBOX_S4_BOTTLENECK_SELECTION_PASS",
        "CPU/native baseline measured | Complete",
        "WT_SANDBOX_S4_CPU_EDIT_PHASE_BASELINE_AUDIT_PASS",
        "Compute ship/reject decision recorded | Complete",
        "WT_SANDBOX_S4_M6_DECISION_PASS",
        "Current decision: S4 is complete",
    ),
    "tools/s4_bottleneck_selection.py": (
        "WT_SANDBOX_S4_BOTTLENECK_SELECTION_PASS",
        "world-transvoxel-sandbox.s4-bottleneck-selection.v1",
        "interactive_edit_settle_latency",
        "CPU/native phase baseline",
    ),
    "docs/S4_BOTTLENECK_SELECTION.md": (
        "S4 bottleneck-selection gate: complete as part of S4",
        "Selected bottleneck: interactive edit-settle latency",
        "WT_SANDBOX_S4_BOTTLENECK_SELECTION_PASS",
        "compute rejected for now",
    ),
    "tools/s4_cpu_edit_phase_baseline.py": (
        "WT_SANDBOX_S4_CPU_EDIT_PHASE_BASELINE_AUDIT_PASS",
        "world-transvoxel-sandbox.s4-cpu-edit-phase-baseline.v1",
        "terrain_s4_cpu_edit_phase_baseline.gd",
        "phase_boundary",
    ),
    "tests/terrain_s4_cpu_edit_phase_baseline.gd": (
        "WT_SANDBOX_S4_CPU_EDIT_PHASE_BASELINE_PASS",
        "set(\"input_enabled\", false)",
        "request_authoritative_samples",
        "max_capture_ms",
        "max_mesh_ms",
    ),
    "docs/S4_CPU_EDIT_PHASE_BASELINE.md": (
        "S4 status: CPU/native baseline complete",
        "WT_SANDBOX_S4_CPU_EDIT_PHASE_BASELINE_AUDIT_PASS",
        "max_total_ms=1205",
        "No compute-relevant phase reaches the 250 ms S4 investigation floor",
    ),
    "tools/s4_m6_decision.py": (
        "WT_SANDBOX_S4_M6_DECISION_PASS",
        "world-transvoxel-sandbox.s4-m6-decision.v1",
        "cpu_native_retained_compute_rejected_for_now",
        "COMPUTE_PHASE_FLOOR_MS = 250",
    ),
    "docs/S4_M6_DECISION.md": (
        "S4 status: complete",
        "Decision: CPU/native retained; compute rejected for now",
        "WT_SANDBOX_S4_M6_DECISION_PASS",
        "No S4 compute prototype is authorized",
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
        "S3 production workload evidence exists | Complete",
        "S4 compute decision exists | Complete",
        "future game repository validates `world-transvoxel-terrain`",
        "Official MIT-backed backend is used first",
        "Current decision: S5 decision work may start",
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
        if relative.startswith("docs/S5") and "status: complete" in text.lower():
            errors.append(f"{relative} is prematurely marked complete")
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        raise SystemExit(1)
    print(
        "WT_SANDBOX_FUTURE_MILESTONE_CONTRACTS_PASS "
        "s3=exit_review_pass s4=complete_cpu_native_retained s5=decision_not_started"
    )


if __name__ == "__main__":
    main()
