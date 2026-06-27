# S3 Completion Checklist

S3 status: complete.

This checklist records the completed S3 gate set. S4 implementation must not
start until S4 decision work selects a measured bottleneck or closes the compute
path with a CPU/native fallback decision.

## Required for S3

| Requirement | Status | Evidence |
| --- | --- | --- |
| S3 contract exists | Complete | `docs/S3_VISIBILITY_PRODUCTION_WORKLOAD_CONTRACT.md` |
| Workload classes are defined | Complete | stable loaded-window inspection, normal movement with forward prefetch, rapid turns, underground, mining while moving, fast travel/teleport policy; S1 remains the fixed LOD0 reference |
| Target-machine budget profile exists | Complete | `docs/S3_TARGET_MACHINE_BUDGET_PROFILE.md` |
| Visibility/frustum audit exists | Complete | `tools/s3_visibility_workload.py`; `WT_SANDBOX_S3_VISIBILITY_WORKLOAD_AUDIT_PASS` |
| Godot frustum behavior is measured separately from terrain demand | Complete | S3 baseline: `frustum_min=27`, `frustum_max=40`, `viewer_updates_delta=0`, `planned_demands_delta=0` |
| Forward-biased prefetch policy is implemented or rejected | Complete | `docs/S3_FORWARD_PREFETCH_POLICY.md`; secondary viewer, distance 64, radius 1 |
| Fast travel / teleport policy is decided | Complete | loading-screen required; seamless disjoint teleport is not accepted by this profile |
| Repeated mining while moving is measured | Complete | S3 baseline: two moving edits per engine |
| Edit latency and edit-journal growth are measured in workload loop | Complete | S3 baseline: max edit 867 ms, journal growth 1,192 bytes |
| `restore_to_base` is implemented/audited or explicitly deferred | Complete | `tools/s3_restore_to_base_audit.py`; `WT_SANDBOX_S3_RESTORE_TO_BASE_AUDIT_PASS`; edited sphere samples restore to deterministic base density/material |
| Visual/GPU artifact acceptance exists | Complete | `tools/s3_visual_gpu_audit.py`; `WT_SANDBOX_S3_VISUAL_GPU_AUDIT_PASS`; 13 graphical captures, max frame interval 169.634 ms, no queued/fading resources at capture points |
| S3 exit review exists | Complete | `tools/s3_exit_review.py`; `docs/S3_EXIT_REVIEW.md`; `WT_SANDBOX_S3_EXIT_REVIEW_PASS` |

## Explicitly out of scope for S3

| Item | Status |
| --- | --- |
| GPU compute acceleration | Out of scope until S4 |
| Water/lava/fluid simulation | Out of scope |
| Planets / alternate gravity worlds | Out of scope |
| Structural collapse/stability simulation | Out of scope |
| Small-game repository | Out of scope until S5 |
| 0BSD backend replacement | Out of scope until after official backend vertical slice |
| Final texture/art production | Out of scope unless a material contract is added |

## Go/no-go

Current decision: S3 is complete; proceed only to S4 decision work.

First baseline complete: `python tools/s3_visibility_workload.py` reports
`WT_SANDBOX_S3_VISIBILITY_WORKLOAD_AUDIT_PASS` with
`artifacts/s3_visibility_workload/workload_report.json`.

Restore-to-base audit complete: `python tools/s3_restore_to_base_audit.py`
reports `WT_SANDBOX_S3_RESTORE_TO_BASE_AUDIT_PASS` with
`artifacts/s3_restore_to_base/restore_to_base_report.json`.

Visual/GPU audit complete: `python tools/s3_visual_gpu_audit.py` reports
`WT_SANDBOX_S3_VISUAL_GPU_AUDIT_PASS` with
`artifacts/s3_visual_gpu/visual_gpu_report.json` and
`artifacts/s3_visual_gpu/contact_sheet.png`.

S3 exit review complete: `python tools/s3_exit_review.py` reports
`WT_SANDBOX_S3_EXIT_REVIEW_PASS` with
`artifacts/s3_exit_review/s3_exit_review_report.json`.

Next valid action: start S4 decision work. Do not begin broad GPU
implementation without a selected S3-measured bottleneck.
