# S4 Completion Checklist

S4 status: active decision work, not implementation.

S4 may not start implementation until the selected S3 bottleneck has a
CPU/native phase baseline.

## Required for S4

| Requirement | Status | Evidence |
| --- | --- | --- |
| S4 contract exists | Complete | `docs/S4_M6_DECISION_CONTRACT.md` |
| S3 bottleneck selected | Complete | `tools/s4_bottleneck_selection.py`; `docs/S4_BOTTLENECK_SELECTION.md`; `WT_SANDBOX_S4_BOTTLENECK_SELECTION_PASS`; selected `interactive_edit_settle_latency` |
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

Current decision: S4 selected interactive edit-settle latency for CPU/native
phase attribution. Do not start S4 implementation until that baseline exists.

Next valid action: create the CPU/native edit phase baseline or close S4 with
CPU retained if attribution cannot justify a targeted compute path.
