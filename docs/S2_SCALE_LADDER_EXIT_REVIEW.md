# S2 Scale-Ladder Exit Review

S2 covers bounded generation, declared runtime budgets, and automated static
visual evidence for L1 through L4 / 2048 horizontal cells.

This is not a gameplay-readiness or dynamic-LOD seamlessness claim. L0 remains
the accepted human playtest world from S1.

## Exit gate

```console
python tools/s2_exit_review.py
```

The gate must print:

```text
WT_SANDBOX_S2_EXIT_REVIEW_PASS
```

The review validates existing reports under `artifacts/scale_ladder`:

- `scale_ladder_report.json` for L1, L2, L3, and L4;
- `runtime_report.json` for L1, L2, L3, and L4;
- `visual_report.json` for L1, L2, L3, and L4;
- runtime budget profiles from `docs/TERRAIN_RUNTIME_BUDGETS.md`;
- finite-boundary regression markers for L3 and L4;
- bounded L4 resource preflight.

## Locked S2 claim

S2 is accepted for:

- L1 through L4 generation;
- storage validation;
- staged runtime movement;
- one active-window edit/remesh per runtime audit;
- clean shutdown;
- declared active chunk capacities;
- nonblank static visual captures;
- finite-boundary targeted regression markers on L3 and L4.

## Still outside S2

The following remain outside this milestone:

- final human qualitative confirmation;
- dynamic seamless LOD gameplay;
- fast travel or disjoint teleport support;
- target-hardware gameplay workload;
- scale support beyond L4 / 2048;
- water/lava, planets, structural collapse, GPU compute, or game readiness.

## Accepted run

The accepted review writes:

```text
artifacts/s2_exit_review/s2_exit_review_report.json
```

and records `status = s2_scale_ladder_exit_review_pass`.
