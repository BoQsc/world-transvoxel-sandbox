# S3a Conservative LOD0 Workload Budgets

This document defines the current S3a.1 budget baseline for the accepted
playtest mode. It covers the conservative fixed-center LOD0 reference scene
only. It does not accept dynamic mixed LOD, fast travel, GPU compute, fluids,
planets, or game-scale feature systems.

## Baseline profile

| Field | Accepted value |
| --- | --- |
| World | `world/world.wtworld`, 128 x 64 x 128 cells |
| Movement class | fixed-center LOD0 reference |
| `radius_chunks` | 4 |
| `maximum_lod` | 0 |
| `streaming_follows_viewer` | false |
| `streaming_update_distance` | 8 |
| `active_chunk_capacity` | 512 |
| `render_apply_budget` | 1 |
| `collision_apply_budget` | 3 |
| Exact restore capture request batch | 15 |
| Frame cap | 60 FPS |
| Autonomous input | disabled before scene entry |

## Hard audit gates

Run:

```console
python tools/workload_audit.py
```

The audit must print `WT_SANDBOX_S3A_WORKLOAD_AUDIT_PASS` and each Godot run
must print `WT_SANDBOX_S3A_WORKLOAD_PASS`.

| Area | Budget |
| --- | --- |
| Startup | world reaches running state within 10,000 ms |
| Initial settle | LOD0 resources settle within 10,000 ms |
| Full-map active set | at least 256 active and fully ready LOD0 chunk records |
| Render/collision coverage | at least 160 nonempty rendered chunks and 160 collision chunks |
| Capacity | active chunk records never exceed 512 |
| Settled idle | 120 idle frames produce no viewer updates, sample jobs, mesh jobs, mesh completions, published events, queued render/collision work, or pending retirements |
| Frame stall guard | idle and fixed-anchor movement frames stay under 250 ms in the audit harness |
| Rapid movement | fixed-anchor movement across surface and underground positions does not trigger streaming |
| Movement coverage | every movement probe has both render and collision coverage |
| Repeated edits | 3 carve + exact-restore cycles commit exactly 6 edits with no edit rejections |
| Edit latency | carve submission, total carve settle, and restore settle each stay under 10,000 ms |
| Edit journal | 3 carve + restore cycles grow `world.wtedit` by no more than 1 MiB |
| Post-edit idle | 120 idle frames after edits produce no hidden runtime work |

The 10,000 ms edit-latency gate is a correctness/regression ceiling for this
first deterministic workload audit. It is not the final gameplay interaction
target. The accepted run below uses a conservative 15-request capture batch and
still shows that exact pre-carve restoration capture is too slow for
production-feel mining. It must be replaced or reduced in S3a before gameplay
readiness is claimed.

## Accepted S3a.1 run

Command:

```console
python tools/workload_audit.py
```

Result on June 26, 2026:

| Engine | Startup ms | Settle ms | Render/collision | Active records | Idle frames | Max move frame ms | Max carve submit ms | Max carve total ms | Max restore ms | Journal growth |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Godot 4.6.3 | 113 | 4,840 | 173 / 173 | 256 | 240 | 33.226 | 8,370 | 8,717 | 300 | 62,844 bytes |
| Godot 4.7 | 99 | 4,780 | 173 / 173 | 256 | 240 | 31.666 | 9,577 | 9,924 | 333 | 62,844 bytes |

Process sampling was available through `psutil`: maximum RSS was 220,217,344
bytes on Godot 4.6.3 and 220,110,848 bytes on Godot 4.7. Average process CPU
over the full headless audit was about 69.3% and 66.4% of one core
respectively; startup and edit work are included in those averages.

## Recorded host observations

`tools/workload_audit.py` records process CPU and RSS samples when `psutil` is
available. These values are useful for regression comparison on the same host,
but they are not portable hard gates because CPU scheduling, drivers, renderer
mode, and background load vary by machine.

GPU power and real rendered-frame cost are not available from the portable
headless audit. A later S3a graphical workload gate must measure the accepted
scene in the renderer used for playtesting before claiming target-hardware
gameplay readiness.

## Boundary

Passing S3a.1 proves that the conservative LOD0 baseline is deterministic,
bounded, cold while idle, and supports controlled movement plus repeated
carve/restore edits under the listed audit budgets. It does not prove dynamic
mixed-LOD visual acceptance, fast travel, graphical GPU budget, production-feel
mining latency, or final human qualitative confirmation.
