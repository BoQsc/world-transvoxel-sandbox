# S5 Completion Checklist

S5 status: not started.

S5 is a decision milestone, not permission to start a game immediately.

## Required for S5

| Requirement | Status | Evidence |
| --- | --- | --- |
| S5 contract exists | Complete | `docs/S5_SMALL_GAME_DECISION_CONTRACT.md` |
| Repository boundary contract exists | Complete | `docs/REPOSITORY_BOUNDARY_CONTRACT.md` |
| S3 production workload evidence exists | Complete | `docs/S3_EXIT_REVIEW.md`; `WT_SANDBOX_S3_EXIT_REVIEW_PASS` |
| S4 compute decision exists | Pending | S4 bottleneck selection exists, but final S4 decision report is still pending |
| Smallest game vertical slice is defined | Pending | game-loop requirements |
| Official MIT-backed backend is used first | Pending | integration decision |
| Optional systems have separate contracts | Pending | fluids/stability/planet/etc. contracts if needed |
| Repository decision is recorded | Pending | same repo, new repo, or defer |
| Game-repo validation boundary is preserved | Pending | future game repository validates `world-transvoxel-terrain` |
| Final proceed/revise/stop decision is recorded | Pending | `WT_SANDBOX_S5_SMALL_GAME_DECISION_PASS` |

## Explicitly out of scope until contracted

| Item | Status |
| --- | --- |
| Water/lava/fluid simulation | Out of scope until separate contract |
| Structural collapse/stability simulation | Out of scope until separate contract |
| Planets / alternate gravity worlds | Out of scope until separate contract |
| Inventory/mining effects/game systems | Out of scope until vertical slice says needed |
| 0BSD backend replacement | Deferred until official backend survives vertical slice |
| Testing `world-transvoxel-terrain` in this sandbox | Out of scope by repository boundary contract |

## Go/no-go

Current decision: do not start S5.

Next valid action after S4: define the vertical slice and decide whether the
official backend reference is ready for game integration.
