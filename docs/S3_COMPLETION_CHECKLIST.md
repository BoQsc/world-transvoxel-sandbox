# S3 Completion Checklist

S3 status: not complete.

This checklist must be updated as S3 work lands. Until every required row is
complete, S4 must not start except for documentation-only planning.

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
| Edit latency and edit-journal growth are measured in workload loop | Complete | S3 baseline: max edit 903 ms, journal growth 1,192 bytes |
| `restore_to_base` is implemented/audited or explicitly deferred | Pending | pass marker or deferral decision |
| S3 exit review exists | Pending | `WT_SANDBOX_S3_EXIT_REVIEW_PASS` |

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

Current decision: do not proceed to S4.

First baseline complete: `python tools/s3_visibility_workload.py` reports
`WT_SANDBOX_S3_VISIBILITY_WORKLOAD_AUDIT_PASS` with
`artifacts/s3_visibility_workload/workload_report.json`.

Next valid action: implement/audit `restore_to_base` or explicitly defer it,
then rerun the S3 workload baseline against that decision.
