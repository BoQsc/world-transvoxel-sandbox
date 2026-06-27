# S4 Completion Checklist

S4 status: not started.

S4 may not start implementation until S3 identifies a measured bottleneck.

## Required for S4

| Requirement | Status | Evidence |
| --- | --- | --- |
| S4 contract exists | Complete | `docs/S4_M6_DECISION_CONTRACT.md` |
| S3 bottleneck selected | Pending | S3 workload report reference |
| CPU/native baseline measured | Pending | baseline report |
| Compute prototype scoped to one bottleneck | Pending | implementation/report |
| Transfer/readback/synchronization measured | Pending | comparison report |
| Output parity or tolerance proven | Pending | comparison report |
| CPU/headless fallback remains deterministic | Pending | fallback report |
| Compute ship/reject decision recorded | Pending | `WT_SANDBOX_S4_M6_DECISION_PASS` |

## Explicitly out of scope for S4

| Item | Status |
| --- | --- |
| Broad GPU rewrite | Out of scope |
| Compute without measured S3 bottleneck | Out of scope |
| Water/lava/fluid simulation | Out of scope unless separately contracted |
| Planets / alternate gravity worlds | Out of scope |
| Structural collapse/stability simulation | Out of scope |
| Small-game repository | Out of scope until S5 |
| 0BSD backend replacement | Out of scope |

## Go/no-go

Current decision: do not start S4 implementation.

Next valid action after S3: choose one measured bottleneck or close S4 with CPU
retained.
