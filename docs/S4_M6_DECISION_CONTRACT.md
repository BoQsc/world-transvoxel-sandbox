# S4 M6 Compute Decision Contract

S4 starts only after S3 exits or S3 explicitly produces a measured bottleneck
that justifies targeted compute work.

S4 is not "move terrain to GPU." S4 is a decision milestone: either targeted
compute acceleration ships with proof, or the CPU/native path is retained.

## In scope

- Select one measured bottleneck from S3 evidence.
- Build the smallest compute path needed to test that bottleneck.
- Compare complete CPU/native and compute paths end to end.
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
| selected bottleneck report | S3 report reference |
| CPU baseline | measured before compute comparison |
| compute comparison | complete end-to-end report |
| fallback proof | deterministic CPU/headless fallback |
| decision marker | `WT_SANDBOX_S4_M6_DECISION_PASS` |

## Exit condition

S4 exits with exactly one of these decisions:

- targeted compute acceleration ships because it improves end-to-end behavior;
- compute is rejected and CPU/native remains the accepted path;
- S4 is blocked because the selected bottleneck or parity proof is insufficient.
