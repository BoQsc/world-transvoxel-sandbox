# S4 M6 Compute Decision Contract

S4 starts only after S3 exits or S3 explicitly produces a measured bottleneck
that justifies targeted compute work.

S4 is not "move terrain to GPU." S4 is a decision milestone: either targeted
compute acceleration ships with proof, or the CPU/native path is retained.

## In scope

- Select one measured bottleneck from S3 evidence.
- Measure the CPU/native phase baseline for that bottleneck.
- Build the smallest compute path only if the CPU/native baseline identifies a
  compute-relevant phase above the investigation floor.
- Compare complete CPU/native and compute paths end to end only when a compute
  prototype is authorized.
- Include dispatch, synchronization, transfer, readback, memory, and fallback
  costs.
- Prove deterministic CPU/headless fallback remains available.
- Prove output compatibility or document any accepted numerical tolerance.
- Decide whether compute ships or is rejected for now.

## Out of scope

- Broad GPU rewrite.
- Compute work without an S3 bottleneck.
- Fluids, planets, structural collapse, game repository, or 0BSD replacement.
- Removing CPU/native behavior or headless determinism.

## Required S4 gates

| Gate | Required marker or artifact |
| --- | --- |
| S4 completion checklist | `docs/S4_COMPLETION_CHECKLIST.md` |
| selected bottleneck report | `tools/s4_bottleneck_selection.py`; `WT_SANDBOX_S4_BOTTLENECK_SELECTION_PASS` |
| CPU baseline | `tools/s4_cpu_edit_phase_baseline.py`; `WT_SANDBOX_S4_CPU_EDIT_PHASE_BASELINE_AUDIT_PASS` |
| compute comparison | complete end-to-end report, or rejected by `WT_SANDBOX_S4_M6_DECISION_PASS` before implementation |
| fallback proof | deterministic CPU/headless fallback |
| decision marker | `WT_SANDBOX_S4_M6_DECISION_PASS` |

The selected bottleneck report is a decision gate only. It does not authorize a
compute prototype until the CPU/native baseline attributes the selected latency
to a phase that compute can improve end to end.

## Exit condition

S4 exits with exactly one of these decisions:

- targeted compute acceleration ships because it improves end-to-end behavior;
- compute is rejected and CPU/native remains the accepted path;
- S4 is blocked because the selected bottleneck or parity proof is insufficient.
