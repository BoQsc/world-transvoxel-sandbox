# S4 Bottleneck Selection

S4 bottleneck-selection gate: complete as part of S4.

This document records the first S4 gate after S3 exit. It selects the measured
terrain bottleneck that S4 may investigate. It does not authorize compute
implementation.

Command:

```console
python tools/s4_bottleneck_selection.py
```

Expected marker:

```text
WT_SANDBOX_S4_BOTTLENECK_SELECTION_PASS selected=interactive_edit_settle_latency
```

## Selected bottleneck: interactive edit-settle latency

S4 selects interactive edit-settle latency as the first M6 decision target.

Evidence:

- S3 visibility workload: `max_edit_ms=867` while running the representative L4
  workload on both supported Godot engines.
- S3 restore-to-base audit: `carve_ms=671`, `restore_ms=501`, and exact sampled
  density/material repair.
- S3 process sampling: average process CPU reached `54.068%` and peak sampling
  reached `206.0%` during the S3 workload.

This is selected because it is terrain-specific, user-facing, and compute
relevant enough to justify attribution. It is not proof that compute shaders
will help.

## Non-selected pressures

- Graphical frame interval reached `169.634 ms`, but S3 does not attribute that
  time to terrain generation, meshing, upload, renderer, capture, or driver
  work. It is not a valid compute target until attribution exists.
- Headless frame interval reached `66.296 ms`, which stays below the S3 frame
  budget.
- Initial settle reached `6838 ms`, but S4 M6 is prioritizing repeated
  user-facing edit behavior before one-time loading.

## Next valid S4 action at selection time

The next action from this gate was to create a CPU/native edit phase baseline.
That action is now complete in `docs/S4_CPU_EDIT_PHASE_BASELINE.md`. The
baseline split edit-settle latency across:

- pre-edit sample capture;
- density/material edit application;
- journal/storage update;
- meshing;
- render resource application;
- collision readiness.

The baseline did not show a compute-relevant phase above the S4 investigation
floor, so `docs/S4_M6_DECISION.md` closes S4 with CPU/native retained and
compute rejected for now.

## Still not authorized

- broad GPU rewrite;
- compute prototype before CPU/native edit phase baseline;
- removing deterministic CPU/headless fallback;
- water/lava, planets, structural stability, game repository, or 0BSD backend
  replacement.
