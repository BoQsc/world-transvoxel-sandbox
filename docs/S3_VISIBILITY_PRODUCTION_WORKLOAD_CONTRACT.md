# S3 Visibility and Production Workload Contract

S3 starts only after S1/S2 report
`WT_SANDBOX_S1_S2_COMPLETION_CHECKLIST_PASS`.

S3 exists to answer whether the terrain reference can survive representative
visibility/frustum behavior and a small-game camera/workload loop without
uncontrolled rendering, streaming, editing, or memory behavior.

## In scope

- Separate Godot renderer/frustum visibility from terrain demand generation.
- Measure graphical frame-time, CPU, memory, rendered chunk count, collision
  coverage, queued work, and retiring/fading resources.
- Define and test camera workload classes:
  - stable loaded-window inspection, with S1 retained as the fixed LOD0
    reference;
  - normal flight/walking;
  - rapid turns;
  - underground traversal;
  - repeated mining while moving;
  - fast travel / disjoint teleport policy.
- Define forward-biased prefetch without losing an all-direction safety ring.
  The accepted S3 policy is `docs/S3_FORWARD_PREFETCH_POLICY.md`.
- Define whether fast travel is supported, rejected, or requires loading-screen
  semantics.
- Measure edit latency, restoration latency, and edit-journal growth under a
  production-like loop.
- Implement and audit `restore_to_base` before timed regeneration, smoothing,
  structural collapse, or fluid equilibrium.
- Establish target-machine budgets for idle CPU, active CPU, GPU frame time,
  render count, physics/collision cost, I/O, and memory.

The first target-machine budget profile is
`docs/S3_TARGET_MACHINE_BUDGET_PROFILE.md`. Its headless baseline runner is
`tools/s3_visibility_workload.py`; it is baseline evidence, not S3 exit.
Explicit base-terrain repair is audited separately by
`tools/s3_restore_to_base_audit.py`.

## Out of scope

S3 does not implement or complete:

- GPU compute acceleration;
- water/lava/fluid simulation;
- planets or alternate gravity worlds;
- structural collapse/stability simulation;
- small-game repository;
- 0BSD backend replacement;
- final art direction or texture production.

Those may become later contracts only after S3 workload data justifies them.

## Required S3 gates

S3 cannot exit until these exist and pass:

| Gate | Required marker or artifact |
| --- | --- |
| S3 completion checklist | `docs/S3_COMPLETION_CHECKLIST.md` |
| target-machine budget profile | `docs/S3_TARGET_MACHINE_BUDGET_PROFILE.md` |
| forward prefetch policy | `docs/S3_FORWARD_PREFETCH_POLICY.md` |
| workload runner | `tools/s3_visibility_workload.py` |
| workload report | `artifacts/s3_visibility_workload/workload_report.json` |
| visibility/frustum audit | `WT_SANDBOX_S3_VISIBILITY_WORKLOAD_PASS` |
| fast-travel policy | explicit supported/rejected/loading-screen decision |
| restore-to-base audit | `WT_SANDBOX_S3_RESTORE_TO_BASE_AUDIT_PASS` |
| visual/GPU artifact acceptance | explicit visual/GPU S3 pass |
| S3 exit review | `WT_SANDBOX_S3_EXIT_REVIEW_PASS` |

## Exit condition

S3 exits only when the representative production workload meets its declared
budgets without visible holes, uncontrolled background work, unbounded memory
growth, or unclassified camera/streaming behavior.

If this cannot pass, S3 exits as blocked with exact reasons and next design
options. It must not silently move to S4.
