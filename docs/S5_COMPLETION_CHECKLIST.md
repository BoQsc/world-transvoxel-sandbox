# S5 Completion Checklist

S5 status: not started.

S5 is a decision milestone, not permission to start a game immediately.

## Required for S5

| Requirement | Status | Evidence |
| --- | --- | --- |
| S5 contract exists | Complete | `docs/S5_SMALL_GAME_DECISION_CONTRACT.md` |
| S3 production workload evidence exists | Pending | S3 exit report |
| S4 compute decision exists | Pending | S4 decision report |
| Smallest game vertical slice is defined | Pending | game-loop requirements |
| Official MIT-backed backend is used first | Pending | integration decision |
| Optional systems have separate contracts | Pending | fluids/stability/planet/etc. contracts if needed |
| Repository decision is recorded | Pending | same repo, new repo, or defer |
| Final proceed/revise/stop decision is recorded | Pending | `WT_SANDBOX_S5_SMALL_GAME_DECISION_PASS` |

## Explicitly out of scope until contracted

| Item | Status |
| --- | --- |
| Water/lava/fluid simulation | Out of scope until separate contract |
| Structural collapse/stability simulation | Out of scope until separate contract |
| Planets / alternate gravity worlds | Out of scope until separate contract |
| Inventory/mining effects/game systems | Out of scope until vertical slice says needed |
| 0BSD backend replacement | Deferred until official backend survives vertical slice |

## Go/no-go

Current decision: do not start S5.

Next valid action after S4: define the vertical slice and decide whether the
official backend reference is ready for game integration.
