# S1.8/S1.9 Conservative LOD0 Workload Baseline

This document defines the S1.8/S1.9 baseline for the accepted playtest mode. It
is part of S1 because interaction feel and visible terrain stability are S1
concerns. It covers the conservative fixed-center LOD0 reference scene only. It
does not move the project to S2 or S3, and it does not accept dynamic mixed LOD,
fast travel, GPU compute, fluids, planets, or game-scale feature systems.

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
| Default mining radius | 2 |
| Exact restore capture path | native batched authoritative sample query |
| Compatibility fallback batch | 15 single-sample requests |
| Frame cap | 60 FPS |
| Autonomous input | disabled before scene entry |

## Hard audit gates

Run:

```console
python tools/s1_lod0_workload_audit.py
```

The audit must print `WT_SANDBOX_S1_LOD0_WORKLOAD_AUDIT_PASS` and each Godot
run must print `WT_SANDBOX_S1_LOD0_WORKLOAD_PASS`.

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
| Edit latency | carve submission, total carve settle, and restore settle each stay under 2,000 ms |
| Edit journal | 3 carve + restore cycles grow `world.wtedit` by no more than 1 MiB |
| Post-edit idle | 120 idle frames after edits produce no hidden runtime work |

The 2,000 ms edit-latency gate is a conservative S1 regression ceiling for the
native batched path. The accepted run below uses the default mining radius 2.0.
The former GDScript single-sample loop is retained only as a compatibility
fallback and is not the accepted hot path.

## Accepted S1.9 run

Command:

```console
python tools/s1_lod0_workload_audit.py
```

Result on June 26, 2026 after the native batched query change:

| Engine | Startup ms | Settle ms | Render/collision | Active records | Idle frames | Max move frame ms | Max carve submit ms | Max carve total ms | Max restore ms | Journal growth |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Godot 4.6.3 | 101 | 4,797 | 173 / 173 | 256 | 240 | 33.226 | 135 | 415 | 285 | 18,852 bytes |
| Godot 4.7 | 102 | 4,788 | 173 / 173 | 256 | 240 | 33.208 | 125 | 405 | 283 | 18,852 bytes |

Process sampling was available through `psutil`: maximum RSS was 217,731,072
bytes on Godot 4.6.3 and 223,084,544 bytes on Godot 4.7. Average process CPU
over the full headless audit was about 30.0% and 30.3% of one core
respectively; startup and edit work are included in those averages.

## Recorded host observations

`tools/s1_lod0_workload_audit.py` records process CPU and RSS samples when
`psutil` is available. These values are useful for regression comparison on the
same host, but they are not portable hard gates because CPU scheduling, drivers,
renderer mode, and background load vary by machine.

GPU power and real rendered-frame cost are not available from the portable
headless audit. If graphical workload evidence is necessary for S1 exit, it
must be added to S1 explicitly rather than starting S3.

## Boundary

Passing S1.9 shows that the conservative LOD0 baseline is deterministic,
bounded, cold while idle, and supports controlled movement plus repeated
carve/restore edits under the tightened native-batch audit budgets. Remaining
S1 work is to resolve the dynamic mixed-LOD default policy and capture final
qualitative confirmation.
