# S3 Completion Checklist

S3 status: not complete.

This checklist must be updated as S3 work lands. Until every required row is
complete, S4 must not start except for documentation-only planning.

## Required for S3

| Requirement | Status | Evidence |
| --- | --- | --- |
| S3 contract exists | Complete | `docs/S3_VISIBILITY_PRODUCTION_WORKLOAD_CONTRACT.md` |
| Workload classes are defined | Pending | stable LOD0, normal movement, rapid turns, underground, mining while moving, fast travel/teleport |
| Target-machine budget profile exists | Pending | CPU/GPU/frame-time/render/physics/I/O/memory budgets |
| Visibility/frustum audit exists | Pending | `tools/s3_visibility_workload.py` |
| Godot frustum behavior is measured separately from terrain demand | Pending | S3 workload report |
| Forward-biased prefetch policy is implemented or rejected | Pending | policy section and workload evidence |
| Fast travel / teleport policy is decided | Pending | supported, rejected, or loading-screen semantics |
| Repeated mining while moving is measured | Pending | S3 workload report |
| Edit latency and edit-journal growth are measured in workload loop | Pending | S3 workload report |
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

Next valid action: implement the S3 workload harness and target-machine budget
profile, then run the first baseline measurement.
