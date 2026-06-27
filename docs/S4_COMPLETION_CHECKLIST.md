# S4 Completion Checklist

S4 status: complete.

S4 selected a measured S3 bottleneck, attributed the CPU/native edit path, and
closed with CPU/native retained. No compute prototype is authorized by S4.

## Required for S4

| Requirement | Status | Evidence |
| --- | --- | --- |
| S4 contract exists | Complete | `docs/S4_M6_DECISION_CONTRACT.md` |
| S3 bottleneck selected | Complete | `tools/s4_bottleneck_selection.py`; `docs/S4_BOTTLENECK_SELECTION.md`; `WT_SANDBOX_S4_BOTTLENECK_SELECTION_PASS`; selected `interactive_edit_settle_latency` |
| CPU/native baseline measured | Complete | `tools/s4_cpu_edit_phase_baseline.py`; `docs/S4_CPU_EDIT_PHASE_BASELINE.md`; `WT_SANDBOX_S4_CPU_EDIT_PHASE_BASELINE_AUDIT_PASS`; max total 1205 ms |
| Compute prototype scoped to one bottleneck | Rejected for now | `docs/S4_M6_DECISION.md`; no compute-relevant phase reached 250 ms |
| Transfer/readback/synchronization measured | Not applicable | no S4 compute prototype authorized |
| Output parity or tolerance proven | Not applicable | no S4 compute output path shipped |
| CPU/headless fallback remains deterministic | Complete | CPU/native path retained; S3/S4 headless gates pass on two Godot engines |
| Compute ship/reject decision recorded | Complete | `tools/s4_m6_decision.py`; `docs/S4_M6_DECISION.md`; `WT_SANDBOX_S4_M6_DECISION_PASS` |

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

Current decision: S4 is complete. CPU/native is retained and compute is rejected
for now.

Next valid action: start S5 decision work. Do not start a game repository until
S5 defines and accepts the smallest vertical slice.
