# S3 Target-Machine Budget Profile

This profile defines the first S3 production-workload baseline. It is a
headless local target-machine profile, not final S3 exit acceptance.

## Profile

| Field | Value |
| --- | --- |
| profile id | `S3-L4-headless-baseline` |
| world scale | L4 / 2048 horizontal cells |
| workload runner | `tools/s3_visibility_workload.py` |
| Godot script | `tests/terrain_s3_visibility_workload.gd` |
| report | `artifacts/s3_visibility_workload/workload_report.json` |
| engines | Godot 4.6.3 and Godot 4.7 when available |
| radius chunks | 3 |
| maximum LOD | 1 |
| active chunk capacity | 1024 |
| render apply budget | 1 |
| forward prefetch policy | `docs/S3_FORWARD_PREFETCH_POLICY.md` |
| prefetch distance | 64 world cells |
| prefetch radius | 1 chunk |
| fast travel policy | loading-screen required |

## Workload classes

The S3 baseline defines and measures these workload classes:

- stable loaded-window inspection, with S1 retained as the fixed LOD0 reference;
- normal movement with forward prefetch;
- rapid turns with frustum estimate separated from terrain demand;
- underground traversal;
- repeated mining while moving.

Fast travel / teleport is not accepted as seamless movement in this profile.
The policy is loading-screen required until a later S3 task proves progressive
catch-up or another explicit fast-travel design.

## Hard headless budgets

| Budget | Limit |
| --- | --- |
| startup | <= 15,000 ms |
| initial settle | <= 20,000 ms |
| per-phase settle | <= 20,000 ms |
| max frame interval observed by script | <= 250 ms |
| active chunk records | <= 1,024 |
| queued render/collision at settle | 0 |
| pending retirements at settle | 0 |
| fading render resources at settle | 0 |
| max mining edit latency | <= 15,000 ms |
| edit-journal growth | <= 2 MiB |
| process RSS | <= 768 MiB |

## Recorded but not final

CPU percent and RSS are recorded by the Python runner when `psutil` is
available. RSS has a hard local cap in this profile. CPU percent remains
host-dependent and is recorded for trend comparison instead of final acceptance.

GPU frame time and visual artifact acceptance are not measured by the headless
baseline. A visual/GPU S3 pass is still required before S3 exit.

## Current claim boundary

Passing this profile proves the S3 visibility/frustum production workload
baseline with the accepted forward-biased prefetch policy. It does not prove S3
exit, compute acceleration, fluids, planets, structural stability, the future
game repository, or `world-transvoxel-terrain`. Explicit `restore_to_base` is
covered by `tools/s3_restore_to_base_audit.py`, not by this visibility baseline.
