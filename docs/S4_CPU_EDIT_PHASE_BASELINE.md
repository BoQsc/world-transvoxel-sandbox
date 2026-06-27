# S4 CPU/Native Edit Phase Baseline

S4 status: CPU/native baseline complete.

This baseline attributes the selected S4 bottleneck, interactive edit-settle
latency. It does not implement compute and does not prove compute would help.

Command:

```console
python tools/s4_cpu_edit_phase_baseline.py
```

Result:

```text
WT_SANDBOX_S4_CPU_EDIT_PHASE_BASELINE_AUDIT_PASS engines=2 max_total_ms=1205 report=artifacts/s4_cpu_edit_phase_baseline/cpu_edit_phase_baseline_report.json
```

## Measured maximums

| Phase | Maximum |
| --- | ---: |
| pre-edit authoritative sample capture | 149 ms |
| transaction build/submission | 1 ms |
| runtime commit/journal/replacement publication | 27 ms |
| edit replacement mesh completion | 38 ms |
| render queue/resource readiness | 134 ms |
| collision queue/resource readiness | 0 ms |
| final stable no-queue/no-retirement hold | 857 ms |
| total measured edit cycle | 1205 ms |
| graphical/headless frame interval during audit | 194.386 ms |

The audit ran two edit cycles on Godot 4.6.3 and Godot 4.7. Each cycle used 33
pre-edit authoritative samples and produced positive edit replacements, mesh
completions, render applications, and collision applications.

## Interpretation

No compute-relevant phase reaches the 250 ms S4 investigation floor:

- sample capture max: 149 ms;
- commit/journal/replacement publication max: 27 ms;
- mesh completion max: 38 ms;
- render queue/resource readiness max: 134 ms;
- collision readiness max: 0 ms.

The largest remaining time is the explicit final stable-settle hold. That is a
correctness gate requiring a quiet no-queue/no-retirement window, not a meshing
or GPU-compute workload.

## Claim boundary

This proves CPU/native phase attribution for the selected S4 edit-settle
bottleneck on the current S3 L4 workload and supported Godot engines.

It does not prove:

- compute shader acceleration;
- GPU transfer/readback cost;
- water/lava, planets, structural stability, game repository, or 0BSD backend
  replacement.
