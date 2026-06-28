# Current Project Status

This file is the short-form tracker. It exists to prevent the project from
turning into an endless stream of small unrelated decisions.

## Active operating rule

Follow `docs/TERRAIN_ACCEPTANCE_STANDARD.md`.
Runtime scale budgets are governed by `docs/TERRAIN_RUNTIME_BUDGETS.md`.
The conservative LOD0 workload gate is governed by
`docs/S1_LOD0_WORKLOAD_BASELINE.md`.
The accepted LOD0 gallery and restart-persistence gate is governed by
`docs/S1_LOD0_GALLERY_AUDIT.md`.
The S1/S2 go/no-go checkpoint is governed by
`docs/S1_S2_COMPLETION_CHECKLIST.md`.

Milestones are sequential. Do not start later-milestone work while the current
milestone is incomplete. If a task is required for correct S1 completion, move
it into S1 with explicit exit criteria instead of labeling it as S2 or S3.

Performance-sensitive terrain work belongs in native code, shaders/compute
when justified, binary formats, or Python offline tooling. GDScript is glue for
Godot scene scaffolding, input routing, debug UI, and headless test harnesses.
It is not where terrain generation, meshing, large-map streaming policy,
storage, recovery, fluids, or stability algorithms should live.

## Current milestone

S2 automated scale-ladder exit evidence is complete, S3 automated exit evidence
is complete, S4 M6 compute decision evidence is complete, and S5 small-game
decision evidence is complete. The roadmap decision is to revise terrain
architecture first: create/design `world-transvoxel-terrain` before creating a
separate game repository. The active post-S5 workstream is governed by
`docs/WORLD_TRANSVOXEL_TERRAIN_ARCHITECTURE_CONTRACT.md` and checked by
`tools/world_transvoxel_terrain_contract_check.py`. The separate
`world-transvoxel-terrain` repository now exists with A0 skeleton commit
`244db4c`, A1 public API/source-layout contract commit `f076597`, and A2
addon-local smoke harness commit `8609c99`, plus A3 `world-transvoxel` bridge
commit `ef03d55`, plus A4 phase 1 resource semantics commit `2774664`, plus A4
phase 2 bridge/storage fixture commit `4b8855c`, plus A4 phase 3 terrain-world
lifecycle commit `b28c623`, plus A4 phase 4 reference runtime/cold-idle
validation commit `9007b83`, plus A4 phase 5 exit-review commit `a02e8cc`; A4
is complete there. A5 phase 1 debug snapshot contract commit `809ecf6` is also
complete there, plus A5 phase 2 local reference scene scaffold commit
`efd8404`, plus A5 phase 3 backend reference-scene runtime smoke commit
`f0ad840`, plus A5 phase 4 debug overlay category rendering commit `1ff8f37`,
plus A5 exit review commit `cc3f5d2`, plus A6 game repository readiness decision
commit `2219a0f`; A6 is complete there. A separate validation game repository is
approved only when explicitly requested. `world-transvoxel-validation-game` now
exists with G0 install/run validation complete, first-person playable-world
target evidence, G2 first-person flat baseline evidence, G3 flat/mountain
generation evidence, G4 terrain edit interaction evidence, G5
material/performance baseline evidence, and G6 profile-selectable playable-world
evidence through commit `cf12e61`, including 4 by 4 baked page sets, flat and
mountain captures, terrain triangles, terrain collision, scripted player motion,
scripted jump, crosshair, visible player capture, first-person carve/place
affordance, edit commits, replacement metrics, materialized checker terrain, GPU
watt sampling, flat/mountain playable profile selection, and first-person plus
overview captures.
S4 closed with CPU/native
retained and compute rejected for now. Do not start broad GPU compute,
water/lava, planets, structural collapse, production game systems, or 0BSD
backend replacement unless a new explicit contract moves those items into scope.
Do not create the separate validation game repository unless the user explicitly
asks for it.

The repository boundary is locked by
`docs/REPOSITORY_BOUNDARY_CONTRACT.md`: `world-transvoxel-sandbox` validates
`world-transvoxel`; a future game repository validates
`world-transvoxel-terrain`. Do not use this sandbox to test the future terrain
addon, and do not ask games to fork or copy this sandbox as terrain
architecture.

S0 is complete for the 128 baseline. S1 now has a technical default-policy
decision: the accepted playtest path is fixed-center LOD0 reference mode, and
dynamic mixed LOD is rejected/demoted as default gameplay by S1.10. Human review
remains final qualitative confirmation; it does not block technical milestone
progress or replace automated/capture-based correctness. S1.8 reclassified the
fixed-center LOD0 workload audit as S1 evidence because interaction feel and
visible terrain stability belong to S1, and S1.9 moved exact restore capture to
the native batched path. S1.11 added an accepted fixed-center LOD0 gallery plus
restart-persistence audit. S2 now has an explicit exit review for L1 through L4
bounded generation, staged runtime, and static visual reports. We are not
starting GPU compute, water/lava, planets, structural collapse, a game
repository, or 0BSD backend replacement work before the relevant S3/S4 contracts
move those items into scope.

## Unresolved blockers kept visible

- dynamic mixed-LOD technical seamless visual acceptance, all camera angles, all
  movement speeds, and geomorphing/native mitigation remain open as a
  diagnostic/future limitation, not as accepted default gameplay;
- production-feel mining latency has an S1.9 native-batch regression gate. The
  conservative LOD0 workload evidence covers fixed-anchor movement, repeated
  mining/restoration, process CPU/RSS sampling, I/O, memory, and idle coldness;
- accepted fixed-center LOD0 gallery and restart persistence now have an S1.11
  gate. No automated hard gallery blocker is detected; final human qualitative
  confirmation remains external;
- S3 graphical visual/GPU artifact acceptance is now covered by its own audit;
  portable vendor GPU timing and target-hardware game readiness remain later
  concerns;
- full terrain/game readiness still requires `world-transvoxel-terrain` and a
  future game repository; S1.11 closes S1 technical exit evidence, not full
  game readiness;
- compute shaders remain rejected for now by S4; optional systems remain
  deferred until later measured workload evidence justifies them.

## Latest evidence

S3 visibility/frustum workload baseline - first production-workload baseline,
not S3 exit.

Command:

```console
python tools/s3_visibility_workload.py
```

Result:

- budget profile: `docs/S3_TARGET_MACHINE_BUDGET_PROFILE.md`;
- runner: `tools/s3_visibility_workload.py`;
- Godot script: `tests/terrain_s3_visibility_workload.gd`;
- report: `artifacts/s3_visibility_workload/workload_report.json`;
- marker: `WT_SANDBOX_S3_VISIBILITY_WORKLOAD_AUDIT_PASS engines=2`;
- Godot 4.6.3: `startup_ms=213`, `settle_ms=6838`, `min_render=222`,
  `min_collision=222`, `max_active=322`, `max_edit_ms=867`,
  `journal_growth_bytes=1192`, `max_frame_ms=66.296`;
- Godot 4.7: `startup_ms=206`, `settle_ms=6600`, `min_render=222`,
  `min_collision=222`, `max_active=322`, `max_edit_ms=867`,
  `journal_growth_bytes=1192`, `max_frame_ms=50.851`;
- forward prefetch: accepted by `docs/S3_FORWARD_PREFETCH_POLICY.md` with
  secondary viewer `603`, distance `64`, radius `1`, and
  `prefetch_updates=10`;
- rapid-turn frustum separation: `frustum_min=27`, `frustum_max=40`,
  `viewer_updates_delta=0`, `planned_demands_delta=0`;
- fast-travel policy: `loading_screen_required`;
- claim boundary: S3 headless baseline with forward prefetch only.
  Graphical visual/GPU acceptance and S3 exit review are covered separately by
  `tools/s3_visual_gpu_audit.py` and `tools/s3_exit_review.py`.

S3 restore-to-base audit - explicit base-terrain repair, not timed
regeneration.

Command:

```console
python tools/s3_restore_to_base_audit.py
```

Result:

- marker: `WT_SANDBOX_S3_RESTORE_TO_BASE_AUDIT_PASS
  engines=2 report=artifacts/s3_restore_to_base/restore_to_base_report.json`;
- Godot 4.6.3 marker: `points=33`, `carve_ms=599`, `restore_ms=501`,
  `journal_growth_bytes=13428`, `active_capacity=1024`;
- Godot 4.7 marker: `points=33`, `carve_ms=671`, `restore_ms=500`,
  `journal_growth_bytes=13428`, `active_capacity=1024`;
- proven: edited sphere-grid samples restore density/material to deterministic
  base terrain;
- claim boundary: this proves explicit restore-to-base for the audited region.
  It does not enable automatic timed regeneration, smoothing, stability,
  fluid equilibrium, visual/GPU S3 acceptance, or S3 exit.

S3 visual/GPU artifact audit - graphical L4 S3 capture gate.

Command:

```console
python tools/s3_visual_gpu_audit.py
```

Result:

- marker: `WT_SANDBOX_S3_VISUAL_GPU_AUDIT_PASS
  images=13 report=artifacts/s3_visual_gpu/visual_gpu_report.json
  contact_sheet=artifacts/s3_visual_gpu/contact_sheet.png`;
- graphical engine: Godot 4.7, OpenGL 3.3, NVIDIA GTX 1060 Max-Q;
- Godot marker: `images=13`, `max_frame_ms=169.634`, `min_render=172`,
  `min_collision=172`, `max_active=322`, `rapid_turns=4`,
  `viewer_updates_delta=0`, `planned_demands_delta=0`;
- captures: stable overview/material, four normal movement views, four rapid
  turns, underground tunnel, pre-edit, and post-edit;
- capture-time gates: player input disabled before scene entry, nonblank
  1280 x 720 images, zero queued render/collision work, zero pending
  retirements, zero render fading resources at capture points, and
  render/collision probes for surface views;
- contact-sheet inspection in this run: no obvious hard holes, upside-down
  terrain, or chunk disappearance in captured views; the underground view is
  dark but nonblank and structurally visible; procedural visual style remains
  simple;
- claim boundary: this proves the S3 graphical still-capture artifact gate and
  graphical frame-interval budget for the captured workload. It does not prove
  vendor GPU timing beyond Godot graphical frame interval, compute acceleration,
  final human aesthetic acceptance, fluids, planets, stability, or S3 exit.

S3 exit review - visibility and production workload milestone closed.

Command:

```console
python tools/s3_exit_review.py
```

Result:

- marker: `WT_SANDBOX_S3_EXIT_REVIEW_PASS
  report=artifacts/s3_exit_review/s3_exit_review_report.json`;
- review doc: `docs/S3_EXIT_REVIEW.md`;
- validated inputs: S3 visibility/frustum workload, restore-to-base audit,
  visual/GPU artifact audit, S3 checklist, S3 contract, and S3 logs;
- decision: S3 complete; next valid milestone is S4 decision work, not broad
  GPU implementation.

S4 bottleneck selection - first M6 decision gate.

Command:

```console
python tools/s4_bottleneck_selection.py
```

Result:

- marker: `WT_SANDBOX_S4_BOTTLENECK_SELECTION_PASS
  selected=interactive_edit_settle_latency max_edit_ms=867
  report=artifacts/s4_bottleneck_selection/bottleneck_selection_report.json`;
- decision doc: `docs/S4_BOTTLENECK_SELECTION.md`;
- selected bottleneck: interactive edit-settle latency from S3 visibility
  workload evidence;
- supporting pressure: S3 restore-to-base reached `carve_ms=671` and
  `restore_ms=501`; S3 process sampling reached `54.068%` average CPU and
  `206.0%` peak CPU;
- boundary: this does not authorize compute implementation. The next valid S4
  action is a CPU/native edit phase baseline.

S4 CPU/native edit phase baseline - selected bottleneck attributed.

Command:

```console
python tools/s4_cpu_edit_phase_baseline.py
```

Result:

- marker: `WT_SANDBOX_S4_CPU_EDIT_PHASE_BASELINE_AUDIT_PASS
  engines=2 max_total_ms=1205
  report=artifacts/s4_cpu_edit_phase_baseline/cpu_edit_phase_baseline_report.json`;
- decision doc: `docs/S4_CPU_EDIT_PHASE_BASELINE.md`;
- maximums: capture `149 ms`, submit `1 ms`, commit/journal/replacement
  publication `27 ms`, mesh `38 ms`, render readiness `134 ms`, collision
  readiness `0 ms`, final stable-settle hold `857 ms`;
- interpretation: no compute-relevant phase reached the 250 ms S4
  investigation floor.

S4 M6 decision - compute rejected for now.

Command:

```console
python tools/s4_m6_decision.py
```

Result:

- marker: `WT_SANDBOX_S4_M6_DECISION_PASS
  decision=cpu_native_retained_compute_rejected_for_now
  compute_relevant_max_ms=149
  report=artifacts/s4_m6_decision/s4_m6_decision_report.json`;
- decision doc: `docs/S4_M6_DECISION.md`;
- outcome: CPU/native path retained; no S4 compute prototype is authorized;
- S4 handoff: S5 decision work is now complete. Do not start a game repository
  until `world-transvoxel-terrain` exists.

S5 small-game decision - revise terrain architecture first.

Command:

```console
python tools/s5_small_game_decision.py
```

Result:

- marker: `WT_SANDBOX_S5_SMALL_GAME_DECISION_PASS
  decision=revise_terrain_architecture_first
  repository=defer_game_repository_until_world_transvoxel_terrain_exists
  report=artifacts/s5_small_game_decision/s5_small_game_decision_report.json`;
- vertical slice: `docs/S5_VERTICAL_SLICE_REQUIREMENTS.md`;
- decision doc: `docs/S5_SMALL_GAME_DECISION.md`;
- outcome: do not create the game repository yet. The next architecture
  workstream is `world-transvoxel-terrain`, using the official MIT-backed
  backend first.

World Transvoxel Terrain architecture contract - active post-S5 addon gate.

Command:

```console
python tools/world_transvoxel_terrain_contract_check.py
```

Result:

- contract: `docs/WORLD_TRANSVOXEL_TERRAIN_ARCHITECTURE_CONTRACT.md`;
- checker: `tools/world_transvoxel_terrain_contract_check.py`;
- marker: `WT_SANDBOX_WORLD_TRANSVOXEL_TERRAIN_CONTRACT_PASS
  next=create_world_transvoxel_terrain_addon_architecture
  game_repository=deferred`;
- decision: next work is `world-transvoxel-terrain` addon
  architecture/skeleton, not a separate game repository;
- constraints: official MIT-backed backend first; compute remains rejected for
  now; GDScript stays glue/scaffolding; hot terrain work belongs in native code,
  low-level addon paths, binary formats, shaders when justified, or Python
  offline tooling.

World Transvoxel Terrain A0 skeleton repository - created outside this sandbox.

Command:

```console
python tools/validate_terrain_skeleton.py
```

Result:

- repository: `world-transvoxel-terrain`;
- commit: `244db4c Create world-transvoxel-terrain skeleton`;
- marker: `WT_TERRAIN_SKELETON_PASS
  addon=world-transvoxel-terrain implementation=deferred
  game_repository=deferred`;
- contents: canonical charter, 0BSD license scope, Godot addon manifest,
  minimal editor-plugin glue, roadmap, references/tests placeholders, and
  skeleton validator;
- decision: A0 is complete.

World Transvoxel Terrain A1 public API/source-layout contract - completed
outside this sandbox.

Command:

```console
python tools/validate_a1_contract.py
```

Result:

- repository: `world-transvoxel-terrain`;
- commit: `f076597 Complete terrain addon A1 contracts`;
- marker: `WT_TERRAIN_A1_CONTRACT_PASS
  next=a2_addon_local_smoke_harness implementation=contract_only`;
- contents: public API/resource contract, source-layout ownership directories,
  old marching-cubes maintainability audit, reference manifest, and A1
  validator;
- decision: A1 is complete. Next work is A2 addon-local smoke harness in
  `world-transvoxel-terrain`, not a game repository.

World Transvoxel Terrain A2 addon-local smoke harness - completed outside this
sandbox.

Commands:

```console
python tools/validate_a2_smoke.py
python tools/a2_addon_smoke.py
```

Result:

- repository: `world-transvoxel-terrain`;
- commit: `8609c99 Complete terrain addon A2 smoke harness`;
- marker: `WT_TERRAIN_A2_CONTRACT_PASS
  next=a3_world_transvoxel_bridge implementation=smoke_only`;
- Godot marker: `WT_TERRAIN_A2_SMOKE_PASS engines=2
  report=artifacts/a2_addon_smoke/a2_addon_smoke_report.json`;
- engines: Godot 4.6.3 and Godot 4.7;
- contents: dependency-status detection without vendoring `world-transvoxel`,
  placeholder `WtTerrainWorld`, `WtTerrainProfile`, and
  `WtTerrainGenerationProfile`, Godot headless smoke script, Python smoke
  runner, A2 validator, and committed `.gd.uid` metadata;
- decision: A2 is complete. Next work is A3 `world-transvoxel` bridge in
  `world-transvoxel-terrain`, not a game repository.

World Transvoxel Terrain A3 `world-transvoxel` bridge - completed outside this
sandbox.

Commands:

```console
python tools/validate_a3_bridge.py
python tools/a3_bridge_smoke.py
```

Result:

- repository: `world-transvoxel-terrain`;
- commit: `ef03d55 Complete terrain addon A3 bridge`;
- marker: `WT_TERRAIN_A3_CONTRACT_PASS
  next=a4_terrain_profile_edit_storage_recovery implementation=bridge_only`;
- Godot marker: `WT_TERRAIN_A3_BRIDGE_PASS engines=2
  report=artifacts/a3_bridge_smoke/a3_bridge_smoke_report.json`;
- engines: Godot 4.6.3 and Godot 4.7;
- bridge evidence: temporary ignored Godot fixture loads sibling
  `world-transvoxel`, detects `WorldTransvoxelTerrain` and
  `WorldTransvoxelConfig`, reads backend identity
  `transvoxel_mit_official`, license `MIT`, config schema `1`, and addon version
  `1.0.11-dev`;
- decision: A3 is complete. Next work is A4 terrain
  profile/edit/storage/recovery implementation in `world-transvoxel-terrain`,
  not a game repository.

World Transvoxel Terrain A4 phase 1 resource semantics - completed outside this
sandbox.

Commands:

```console
python tools/validate_a4_phase1.py
python tools/a4_phase1_resources_smoke.py
```

Result:

- repository: `world-transvoxel-terrain`;
- commit: `2774664 Add A4 phase 1 terrain resources`;
- marker: `WT_TERRAIN_A4_PHASE1_CONTRACT_PASS
  next=a4_phase2_bridge_edit_submission implementation=resource_semantics_only`;
- Godot marker: `WT_TERRAIN_A4_PHASE1_SMOKE_PASS engines=2
  report=artifacts/a4_phase1_resources/a4_phase1_resources_report.json`;
- engines: Godot 4.6.3 and Godot 4.7;
- contents: `WtTerrainEditOperation`, `WtTerrainEditBatch`,
  `WtTerrainStorageProfile`, `WtTerrainRecoveryPolicy`, A4 phase 1 Godot smoke,
  Python runner, validator, docs, and committed `.gd.uid` metadata;
- claim boundary: this is `resource_semantics_only`; it does not submit edits
  into the backend, generate terrain pages, persist a real edit journal, prove
  collision readiness, or prove game-ready terrain;
- decision: A4 remains active. Next work is A4 phase 2 bridge edit submission
  and storage fixture in `world-transvoxel-terrain`, not a game repository.

World Transvoxel Terrain A4 phase 2 bridge/storage fixture - completed outside
this sandbox.

Commands:

```console
python tools/validate_a4_phase2.py
python tools/a4_phase2_bridge_storage_smoke.py
```

Result:

- repository: `world-transvoxel-terrain`;
- commit: `4b8855c Add A4 phase 2 edit bridge storage fixture`;
- marker: `WT_TERRAIN_A4_PHASE2_CONTRACT_PASS
  next=a4_phase3_public_terrain_world_lifecycle
  implementation=bridge_storage_fixture`;
- Godot marker: `WT_TERRAIN_A4_PHASE2_SMOKE_PASS engines=2
  report=artifacts/a4_phase2_bridge_storage/a4_phase2_bridge_storage_report.json`;
- engines: Godot 4.6.3 and Godot 4.7;
- contents: `WtTerrainEditBridge`, `density_value` on edit operations, A4 phase
  2 backend fixture smoke, Python runner, validator, docs, and committed
  `.gd.uid` metadata;
- evidence: the temporary fixture starts the official backend production
  lifecycle world, converts five terrain operations into eight native backend
  edit commands, commits one transaction, verifies native `world.wtedit`, stops,
  restarts, and verifies journal replay through an authoritative sample query;
- claim boundary: this is `bridge_storage_fixture`; it does not make
  `WtTerrainWorld` own backend lifecycle, does not prove a final game-facing
  terrain scene, does not prove 2048 x 2048 x 64 full terrain scene operation,
  and does not authorize GPU/water/planets/stability/game-repo/0BSD backend
  work;
- decision: A4 remains active. Next work is A4 phase 3 public `WtTerrainWorld`
  lifecycle ownership in `world-transvoxel-terrain`, not a game repository.

World Transvoxel Terrain A4 phase 3 terrain-world lifecycle - completed outside
this sandbox.

Commands:

```console
python tools/validate_a4_phase3.py
python tools/a4_phase3_terrain_world_lifecycle_smoke.py
```

Result:

- repository: `world-transvoxel-terrain`;
- commit: `b28c623 Add A4 phase 3 terrain world lifecycle`;
- marker: `WT_TERRAIN_A4_PHASE3_CONTRACT_PASS
  next=a4_phase4_reference_profile_runtime_cold_idle
  implementation=terrain_world_lifecycle`;
- Godot marker: `WT_TERRAIN_A4_PHASE3_SMOKE_PASS engines=2
  report=artifacts/a4_phase3_terrain_world_lifecycle/a4_phase3_terrain_world_lifecycle_report.json`;
- engines: Godot 4.6.3 and Godot 4.7;
- contents: `WtTerrainWorld.start_backend_world()`, `stop_backend_world()`,
  `submit_edit_batch()`, owned backend terrain/config instantiation,
  `object_root_path` on `WtTerrainStorageProfile`, phase 3 smoke, Python
  runner, validator, docs, and committed `.gd.uid` metadata;
- evidence: public `WtTerrainWorld` starts the official backend production
  lifecycle fixture, submits an edit batch, verifies native `world.wtedit`,
  stops, restarts, and verifies journal replay through the owned backend;
- claim boundary: this is `terrain_world_lifecycle`; it does not prove 2048 x
  2048 x 64 full profile runtime, viewer binding, terrain streaming policy,
  collision readiness through the terrain-world API, debug UI, cold-idle
  budgets, or game-ready terrain;
- decision: A4 remains active. Next work is A4 phase 4 reference-profile
  runtime/cold-idle validation in `world-transvoxel-terrain`, not a game
  repository.

World Transvoxel Terrain A4 phase 4 reference runtime/cold-idle validation -
completed outside this sandbox.

Commands:

```console
python tools/validate_a4_phase4.py
python tools/a4_phase4_reference_runtime_cold_idle_smoke.py
```

Result:

- repository: `world-transvoxel-terrain`;
- commit: `9007b83 Add A4 phase 4 runtime cold idle validation`;
- marker: `WT_TERRAIN_A4_PHASE4_CONTRACT_PASS
  next=a4_phase5_a4_exit_review
  implementation=reference_profile_runtime_cold_idle`;
- Godot marker: `WT_TERRAIN_A4_PHASE4_SMOKE_PASS engines=2
  report=artifacts/a4_phase4_reference_runtime_cold_idle/a4_phase4_reference_runtime_cold_idle_report.json`;
- engines: Godot 4.6.3 and Godot 4.7;
- contents: public `WtTerrainWorld.update_viewer()`, `remove_viewer()`,
  `query_chunk_state()`, runtime metrics, cold-idle summary, focused
  `WtTerrainRuntimeAudit`, phase 4 smoke, Python runner, validator, docs, and
  committed `.gd.uid` metadata;
- evidence: public `WtTerrainWorld` starts the official backend lifecycle
  fixture, verifies the default 2048 x 2048 x 64 `+Y` up finite reference
  profile, streams one viewer, waits for render/collision readiness, queries the
  ready origin chunk, holds selected runtime counters stable while cold idle,
  removes the viewer, and stops cleanly;
- claim boundary: this is `reference_profile_runtime_cold_idle`; it does not
  prove a generated full 2048 x 2048 x 64 world, broad movement, dynamic LOD,
  seams, visual smoothness, debug UI, native terrain generation policy, optional
  systems, or game-ready terrain;
- decision: A4 remains active for one finite closure step. Next work is A4 phase
  5 A4 exit review in `world-transvoxel-terrain`, not a game repository.

World Transvoxel Terrain A4 phase 5 exit review - completed outside this
sandbox.

Commands:

```console
python tools/validate_a4_phase5.py
python tools/a4_phase5_exit_review.py
```

Result:

- repository: `world-transvoxel-terrain`;
- commit: `a02e8cc Close A4 with exit review evidence`;
- marker: `WT_TERRAIN_A4_PHASE5_CONTRACT_PASS
  next=a5_local_reference_scene_debug_ui
  implementation=a4_exit_review`;
- exit marker: `WT_TERRAIN_A4_PHASE5_EXIT_REVIEW_PASS validators=9 smokes=6
  report=artifacts/a4_phase5_exit_review/a4_phase5_exit_review_report.json
  next=a5_local_reference_scene_debug_ui`;
- engines: Godot 4.6.3 and Godot 4.7;
- evidence: one documented run covered the terrain skeleton validator, A1, A2,
  A3, A4 phase 1, A4 phase 2, A4 phase 3, A4 phase 4, and A4 phase 5 contract
  validators, plus the A2, A3, A4 phase 1, A4 phase 2, A4 phase 3, and A4 phase
  4 Godot smoke harnesses;
- decision: A4 is complete at the terrain-addon API/control-plane level. Next
  work is A5 local reference scene and debug UI in `world-transvoxel-terrain`,
  not a game repository.

World Transvoxel Terrain A5 phase 1 debug snapshot contract - completed outside
this sandbox.

Commands:

```console
python tools/validate_a5_phase1.py
python tools/a5_phase1_debug_snapshot_smoke.py
python tools/a4_phase5_exit_review.py
```

Result:

- repository: `world-transvoxel-terrain`;
- commit: `809ecf6 Add A5 phase 1 debug snapshot contract`;
- marker: `WT_TERRAIN_A5_PHASE1_CONTRACT_PASS
  next=a5_phase2_local_reference_scene_scaffold
  implementation=debug_snapshot_contract`;
- Godot marker: `WT_TERRAIN_A5_PHASE1_SMOKE_PASS engines=2
  report=artifacts/a5_phase1_debug_snapshot/a5_phase1_debug_snapshot_report.json`;
- engines: Godot 4.6.3 and Godot 4.7;
- evidence: `WtTerrainDebugSnapshot.capture()` exposes stable world, terrain
  profile, generation profile, storage profile, recovery policy, budget,
  collision, streaming, edit, and material categories without starting hidden
  backend work;
- decision: A5 is active. Next work is A5 phase 2 local reference scene scaffold
  in `world-transvoxel-terrain`, not a game repository.

World Transvoxel Terrain A5 phase 2 local reference scene scaffold - completed
outside this sandbox.

Commands:

```console
python tools/validate_a5_phase2.py
python tools/a5_phase2_reference_scene_scaffold_smoke.py
python tools/a5_phase1_debug_snapshot_smoke.py
python tools/a2_addon_smoke.py
```

Result:

- repository: `world-transvoxel-terrain`;
- commit: `efd8404 Add A5 phase 2 reference scene scaffold`;
- marker: `WT_TERRAIN_A5_PHASE2_CONTRACT_PASS
  next=a5_phase3_backend_reference_scene_runtime_smoke
  implementation=local_reference_scene_scaffold`;
- Godot marker: `WT_TERRAIN_A5_PHASE2_SMOKE_PASS engines=2
  report=artifacts/a5_phase2_reference_scene_scaffold/a5_phase2_reference_scene_scaffold_report.json`;
- engines: Godot 4.6.3 and Godot 4.7;
- evidence: `wt_terrain_reference_scene.tscn` instantiates inside the addon,
  owns a `WtTerrainWorld` child and debug overlay label, assigns default
  terrain/generation/storage/recovery resources, refreshes through
  `WtTerrainDebugSnapshot`, and does not start hidden backend work;
- decision: A5 remains active. Next work is A5 phase 3 backend reference-scene
  runtime smoke in `world-transvoxel-terrain`, not a game repository.

World Transvoxel Terrain A5 phase 3 backend reference-scene runtime smoke -
completed outside this sandbox.

Commands:

```console
python tools/validate_a5_phase3.py
python tools/a5_phase3_reference_scene_runtime_smoke.py
python tools/a5_phase2_reference_scene_scaffold_smoke.py
python tools/a5_phase1_debug_snapshot_smoke.py
python tools/a4_phase4_reference_runtime_cold_idle_smoke.py
```

Result:

- repository: `world-transvoxel-terrain`;
- commit: `f0ad840 Add A5 phase 3 reference scene runtime smoke`;
- marker: `WT_TERRAIN_A5_PHASE3_CONTRACT_PASS
  next=a5_phase4_debug_overlay_category_rendering
  implementation=backend_reference_scene_runtime_smoke`;
- Godot marker: `WT_TERRAIN_A5_PHASE3_SMOKE_PASS engines=2
  report=artifacts/a5_phase3_reference_scene_runtime/a5_phase3_reference_scene_runtime_report.json`;
- engines: Godot 4.6.3 and Godot 4.7;
- evidence: `WtTerrainReferenceScene` starts/stops its owned `WtTerrainWorld`,
  submits scene-level viewer update/removal, refreshes `WtTerrainDebugSnapshot`
  while backend resources are live, reports running backend state, cold-idle,
  render resources, and collision resources in status text, and returns to zero
  render/collision resources after viewer removal;
- decision: A5 remains active. Next work is A5 phase 4 debug overlay category
  rendering in `world-transvoxel-terrain`, not a game repository.

World Transvoxel Terrain A5 phase 4 debug overlay category rendering -
completed outside this sandbox.

Commands:

```console
python tools/validate_a5_phase4.py
python tools/a5_phase4_debug_overlay_categories_smoke.py
python tools/a5_phase3_reference_scene_runtime_smoke.py
python tools/a5_phase2_reference_scene_scaffold_smoke.py
python tools/a5_phase1_debug_snapshot_smoke.py
```

Result:

- repository: `world-transvoxel-terrain`;
- commit: `1ff8f37 Add A5 phase 4 debug overlay category rendering`;
- marker: `WT_TERRAIN_A5_PHASE4_CONTRACT_PASS
  next=a5_phase5_a5_exit_review
  implementation=debug_overlay_category_rendering`;
- Godot marker: `WT_TERRAIN_A5_PHASE4_SMOKE_PASS engines=2
  report=artifacts/a5_phase4_debug_overlay_categories/a5_phase4_debug_overlay_categories_report.json`;
- engines: Godot 4.6.3 and Godot 4.7;
- evidence: `WtTerrainDebugOverlayFormatter` renders world, terrain profile,
  generation profile, storage profile, recovery policy, budget, collision,
  streaming, edit, and material sections; the backend-backed smoke verifies live
  backend state, cold-idle, queue state, render resources, collision resources,
  and material placeholder state in overlay text;
- decision: A5 remains active for exit review. Next work is A5 phase 5 A5 exit
  review in `world-transvoxel-terrain`, not a game repository.

World Transvoxel Terrain A5 phase 5 exit review - completed outside this
sandbox.

Commands:

```console
python tools/a5_phase5_exit_review.py
python tools/validate_a5_phase5.py
python tools/validate_a5_phase4.py
python tools/validate_terrain_skeleton.py
```

Result:

- repository: `world-transvoxel-terrain`;
- commit: `cc3f5d2 Close A5 with exit review evidence`;
- marker: `WT_TERRAIN_A5_PHASE5_CONTRACT_PASS
  next=a6_game_repository_readiness_decision
  implementation=a5_exit_review`;
- exit marker: `WT_TERRAIN_A5_PHASE5_EXIT_REVIEW_PASS validators=7 smokes=4
  report=artifacts/a5_phase5_exit_review/a5_phase5_exit_review_report.json
  next=a6_game_repository_readiness_decision`;
- reviewed validators: terrain skeleton, A4 phase 5, A5 phase 1, A5 phase 2,
  A5 phase 3, A5 phase 4, and A5 phase 5;
- reviewed smokes: A5 phase 1 debug snapshot, A5 phase 2 reference scene
  scaffold, A5 phase 3 reference scene runtime, and A5 phase 4 debug overlay
  categories;
- engines: Godot 4.6.3 and Godot 4.7 for each A5 smoke;
- decision: A5 is complete. Next work is A6 game repository readiness decision
  in `world-transvoxel-terrain`, not a game repository.

World Transvoxel Terrain A6 game repository readiness decision - completed
outside this sandbox.

Commands:

```console
python tools/a6_readiness_decision.py
python tools/validate_a6_readiness_decision.py
```

Result:

- repository: `world-transvoxel-terrain`;
- commit: `2219a0f Record A6 game repository readiness decision`;
- marker: `WT_TERRAIN_A6_CONTRACT_PASS
  decision=approve_validation_game_repository
  implementation=readiness_decision
  next=separate_validation_game_repository_when_user_approves`;
- decision marker: `WT_TERRAIN_A6_READINESS_DECISION_PASS
  decision=approve_validation_game_repository validators=2
  report=artifacts/a6_readiness_decision/a6_readiness_decision_report.json
  next=separate_validation_game_repository_when_user_approves`;
- reviewed evidence: package boundary, local smoke evidence, stable minimal API,
  and the full A5 exit review;
- decision: the separate validation game repository may be created when the user
  explicitly asks. This is not a production-ready terrain claim.

World Transvoxel Validation Game G0 install/run validation scaffold - completed
outside this sandbox.

Commands:

```console
python tools/validate_g0_contract.py
python tools/g0_install_run_smoke.py
```

Result:

- repository: `world-transvoxel-validation-game`;
- commit: `8923f6e Create validation game G0 install run scaffold`;
- marker: `WT_VALIDATION_G0_CONTRACT_PASS
  implementation=install_run_validation_scaffold
  next=human_visible_playtest_confirmation`;
- smoke marker: `WT_VALIDATION_G0_SMOKE_PASS engines=2
  report=artifacts/g0_install_run_smoke/g0_install_run_smoke_report.json`;
- composed sources: `world-transvoxel` commit `a84256e` and
  `world-transvoxel-terrain` commit `2219a0f`;
- engines: Godot 4.6.3 and Godot 4.7;
- decision: G0 install/run validation is complete. Next validation-game work is
  G1 human-visible playtest confirmation.

World Transvoxel Validation Game G1 visible playtest guard - completed outside
this sandbox; human rerun confirmation remains pending.

Commands:

```console
python tools/root_project_safe_import.py
python tools/validate_g1_contract.py
python tools/g1_visible_playtest_smoke.py
python tools/g1_visual_capture.py --windowed
```

Result:

- repository: `world-transvoxel-validation-game`;
- commit: `cf12e61 Add profile selectable playable world gate`;
- marker: `WT_VALIDATION_G1_CONTRACT_PASS
  implementation=human_visible_playtest_guard
  next=human_rerun_confirmation`;
- smoke marker: `WT_VALIDATION_G1_SMOKE_PASS engines=2
  report=artifacts/g1_visible_playtest/g1_visible_playtest_report.json`;
- root safe-import marker: `WT_VALIDATION_ROOT_PROJECT_SAFE_IMPORT_PASS
  engines=2
  report=artifacts/root_project_safe_import/root_project_safe_import_report.json`;
- playable-world marker: `WT_VALIDATION_PLAYABLE_WORLD_TARGET_PASS
  next=g6_profile_selectable_playable_world`;
- G2 marker: `WT_VALIDATION_G2_CONTRACT_PASS
  implementation=first_person_flat_baseline
  next=g3_terrain_generation_modes`;
- G2 smoke marker: `WT_VALIDATION_G2_SMOKE_PASS engines=2
  report=artifacts/g2_first_person_baseline/g2_first_person_baseline_report.json`;
- G3 marker: `WT_VALIDATION_G3_CONTRACT_PASS
  implementation=flat_and_mountain_baked_generation_modes
  next=g4_terrain_edit_interaction`;
- G3 smoke marker: `WT_VALIDATION_G3_SMOKE_PASS profiles=2 engines=2
  report=artifacts/g3_generation_modes/g3_generation_modes_report.json`;
- G4 marker: `WT_VALIDATION_G4_CONTRACT_PASS
  implementation=first_person_edit_interaction
  next=g5_material_performance_baseline`;
- G4 smoke marker: `WT_VALIDATION_G4_SMOKE_PASS engines=2
  report=artifacts/g4_edit_interaction/g4_edit_interaction_report.json`;
- G5 marker: `WT_VALIDATION_G5_CONTRACT_PASS
  implementation=materialized_performance_baseline
  next=g6_profile_selectable_playable_world`;
- G5 smoke marker: `WT_VALIDATION_G5_SMOKE_PASS engines=2
  power_samples=45 avg_gpu_power_watts=24.41
  report=artifacts/g5_material_performance/g5_material_performance_report.json`;
- G6 marker: `WT_VALIDATION_G6_CONTRACT_PASS
  implementation=profile_selectable_playable_world
  next=human_visual_verification`;
- G6 smoke marker: `WT_VALIDATION_G6_SMOKE_PASS profiles=2 engines=2
  report=artifacts/g6_profile_selectable_playable_world/g6_profile_selectable_playable_world_report.json`;
- visual capture marker: `WT_VALIDATION_G1_VISUAL_CAPTURE_RUN_PASS engines=2
  report=artifacts/g1_visual_capture/g1_visual_capture_report.json`;
- terrain geometry: `terrain_triangles=512` on Godot 4.6.3 and Godot 4.7;
- player: `player_motion=2.800` and `player_cyan_samples=432` on Godot 4.6.3
  and Godot 4.7;
- G2 player probes: `walk_motion=2.800` and `jump_height=1.080` on Godot 4.6.3
  and Godot 4.7;
- generation: `profile_id=flat_baseline`, `source_mode=FLAT`, `seed=1`;
- G3 generation: `flat_large` and `mountain_large`, 16 baked pages each,
  `flat_triangles=4096`, `mountain_triangles=5436`, `mountain_span=7.862`;
- G4 edits: left mouse carves, right mouse constructs/places; automated carve
  and place commit through the same interactor with human input disabled;
  replacement count `2`, carve/place commit frames <= 1, settle frames <= 3 on
  Godot 4.6.3 and Godot 4.7;
- G5 material/performance: backend terrain meshes receive the validation checker
  material, visual captures contain colored terrain, and the windowed smoke
  measured `avg_gpu_power_watts=24.41`;
- G6 profile selection: `flat_large` and `mountain_large` run through the same
  playable scene, submit 16 viewer positions, keep 8 render/collision resources,
  apply materials, perform automated carve/construct, and save first-person plus
  overview captures;
- view: first-person camera/crosshair for human play; overview camera mode only
  for automated capture;
- engines: Godot 4.6.3 and Godot 4.7;
- decision: the gray-rectangle-only playtest was not acceptable. The validation
  scene now targets the terrain chunk, shows status text and orientation markers,
  fails if no terrain `MeshInstance3D` exists, verifies terrain collision plus
  scripted player movement with human input disabled, and saves a visual capture
  containing the player. The repository-root project is notice-only;
  addon-enabled playtest projects are generated under `artifacts/.../project`.
  G2 first-person flat baseline, G3 terrain generation modes, G4 terrain edit
  interaction, G5 material/performance baseline, and G6 profile-selectable
  playable world are programmatically complete; human visual verification is
  next.

Future milestone contract guard - S3/S4/S5 scopes are defined before
implementation.

Command:

```console
python tools/future_milestone_contracts_check.py
```

Result:

- S3 contract: `docs/S3_VISIBILITY_PRODUCTION_WORKLOAD_CONTRACT.md`;
- S3 checklist: `docs/S3_COMPLETION_CHECKLIST.md`;
- S4 contract: `docs/S4_M6_DECISION_CONTRACT.md`;
- S4 checklist: `docs/S4_COMPLETION_CHECKLIST.md`;
- S5 contract: `docs/S5_SMALL_GAME_DECISION_CONTRACT.md`;
- S5 checklist: `docs/S5_COMPLETION_CHECKLIST.md`;
- repository boundary contract: `docs/REPOSITORY_BOUNDARY_CONTRACT.md`;
- terrain addon architecture contract:
  `docs/WORLD_TRANSVOXEL_TERRAIN_ARCHITECTURE_CONTRACT.md`;
- marker: `WT_SANDBOX_FUTURE_MILESTONE_CONTRACTS_PASS
  s3=exit_review_pass s4=complete_cpu_native_retained
  s5=complete_revise_terrain_architecture_first
  terrain_contract=active_post_s5`;
- decision: roadmap decision is complete; next work belongs to the
  `world-transvoxel-terrain` addon architecture, not a game repository.

S1/S2 completion checklist - no required S1/S2 gate is missing.

Command:

```console
python tools/s1_s2_completion_checklist.py --refresh-fast
```

Result:

- checklist: `docs/S1_S2_COMPLETION_CHECKLIST.md`;
- validator: `tools/s1_s2_completion_checklist.py`;
- marker: `WT_SANDBOX_S1_S2_COMPLETION_CHECKLIST_PASS s1=complete s2=complete
  decision=ready_for_s3_contract`;
- refreshed gates: `WT_SANDBOX_VALIDATION_PASS`,
  `WT_SANDBOX_RUNTIME_BUDGETS_PASS`, and `WT_SANDBOX_S2_EXIT_REVIEW_PASS`;
- decision: S1 and S2 are complete for their defined technical scope; proceed
  only to an S3 contract, not directly to GPU compute, fluids, planets, 0BSD
  backend replacement, or game repository work.

S2 exit review - L1 through L4 scale-ladder evidence is complete.

Command:

```console
python tools/s2_exit_review.py
```

Result:

- contract: `docs/S2_SCALE_LADDER_EXIT_REVIEW.md`;
- review tool: `tools/s2_exit_review.py`;
- marker: `WT_SANDBOX_S2_EXIT_REVIEW_PASS levels=4
  report=artifacts/s2_exit_review/s2_exit_review_report.json`;
- validated reports: L1-L4 generation, L1-L4 runtime, and L1-L4 static visual
  reports under `artifacts/scale_ladder`;
- validated budget gate: `WT_SANDBOX_RUNTIME_BUDGETS_PASS profiles=5`;
- validated L4 shader-budget cleanup: rerun
  `WT_SANDBOX_SCALE_VISUAL_PASS level=L4 images=7`;
- accepted S2 claim: bounded L1-L4 generation, storage validation, staged
  runtime movement, one active-window edit/remesh per runtime audit, clean
  shutdown, declared active chunk capacities, nonblank static visual captures,
  and L3/L4 finite-boundary regression markers;
- still outside S2: final human qualitative confirmation, dynamic seamless LOD
  gameplay, fast travel/disjoint teleport support, target-hardware gameplay
  workload, scale beyond L4 / 2048, and optional systems.

S1.11 - accepted fixed-center LOD0 gallery and restart-persistence audit are
complete.

Command:

```console
python tools/s1_lod0_gallery_audit.py
```

Result:

- contract: `docs/S1_LOD0_GALLERY_AUDIT.md`;
- visual runner: `tools/s1_lod0_gallery_audit.py`;
- persistence audit: `tests/terrain_s1_lod0_persistence_audit.gd`;
- marker: `WT_SANDBOX_S1_LOD0_GALLERY_AUDIT_PASS images=9 engines=2
  report=artifacts/s1_lod0_gallery/gallery_report.json`;
- persistence marker on Godot 4.6.3 and 4.7:
  `WT_SANDBOX_S1_LOD0_PERSISTENCE_PASS density_delta=8.000
  journal_bytes=612 restart=exact mesh=stable`;
- accepted-gallery gates: player input disabled, nine 1280 x 720 nonblank
  images, closed-boundary render/collision ray agreement, no Godot `ERROR:` or
  `SCRIPT ERROR`, and exact edited density/mesh restoration after stop/start;
- S1 technical exit coverage: accepted LOD0 gallery has no automated hard
  blocker, S1.9 keeps mining latency under the native-batch gate, and S1.10
  keeps dynamic mixed LOD diagnostic-only instead of default gameplay;
- still outside this claim: final human qualitative confirmation, real
  triplanar/texture-array art direction, dynamic mixed-LOD seamless gameplay,
  water/lava, planets, GPU compute, or full game readiness.

S1.10 - dynamic mixed-LOD default-policy decision and fixed LOD0 default gate
are complete.

Commands:

```console
python tools/validate_sandbox.py
python tools/test_sandbox.py
python tools/s1_lod0_workload_audit.py
python tools/capture_visuals.py
```

Decision:

- policy document: `docs/S1_DYNAMIC_LOD_POLICY.md`;
- runtime audit: `tests/terrain_s1_default_policy_audit.gd`;
- matrix runner: `tools/test_sandbox.py`;
- marker: `WT_SANDBOX_S1_DEFAULT_POLICY_PASS`;
- validation marker: `WT_SANDBOX_VALIDATION_PASS vendored_files=147
  project_files=240`;
- matrix marker: `WT_SANDBOX_MATRIX_PASS engines=2 configurations=2 tests=8
  cases=32`;
- workload marker: `WT_SANDBOX_S1_LOD0_WORKLOAD_AUDIT_PASS engines=2
  report=artifacts/s1_lod0_workload/workload_report.json`;
- visual marker: `WT_SANDBOX_VISUAL_EVIDENCE_PASS images=9`;
- accepted default: `radius_chunks = 4`, `maximum_lod = 0`,
  `streaming_follows_viewer = false`, fixed streaming position `(64, 32, 64)`,
  `render_apply_budget = 1`, and 60 FPS;
- verified behavior: the accepted scene starts fixed LOD0, settles the full
  LOD0 reference active set, renders only LOD0 chunks, and viewer movement does
  not change the fixed streaming anchor or submit new viewer demand;
- dynamic mixed LOD remains available only through explicit diagnostic scripts
  or test modes. Existing S1.6 evidence proves bounded deterministic
  transitions under the current automated gates; it does not prove seamless
  default gameplay, all camera angles, all movement speeds, or geomorphing.

S1.9 - native batched exact-restore capture and conservative LOD0 workload gate
are complete.

Command:

```console
python tools/s1_lod0_workload_audit.py
```

Result:

- budget document: `docs/S1_LOD0_WORKLOAD_BASELINE.md`;
- audit: `tests/terrain_s1_lod0_workload_audit.gd`;
- runner: `tools/s1_lod0_workload_audit.py`;
- marker: `WT_SANDBOX_S1_LOD0_WORKLOAD_AUDIT_PASS engines=2
  report=artifacts/s1_lod0_workload/workload_report.json`;
- Godot 4.6.3: startup 153 ms, settle 4,963 ms, render/collision 173 / 173,
  active records 256, 240 idle frames, max movement frame 33.176 ms,
  3 carve + exact-restore cycles, 6 edit commits, max carve submit 137 ms,
  max carve total 400 ms, max restore 267 ms, edit-journal growth 18,852
  bytes, max RSS 221,093,888 bytes, average process CPU 31.162%;
- Godot 4.7: startup 121 ms, settle 4,857 ms, render/collision 173 / 173,
  active records 256, 240 idle frames, max movement frame 32.778 ms,
  3 carve + exact-restore cycles, 6 edit commits, max carve submit 139 ms,
  max carve total 417 ms, max restore 283 ms, edit-journal growth 18,852
  bytes, max RSS 217,853,952 bytes, average process CPU 32.472%;
- completed evidence: conservative fixed-center LOD0 active set is bounded and cold while
  idle; fixed-anchor surface/underground movement does not trigger streaming;
  repeated carve/exact-restore commits and journal growth are bounded under the
  tightened 2,000 ms edit-latency ceiling;
- implemented S1 improvement: World Transvoxel 1.0.10-dev adds a native batched
  authoritative sample query. The sandbox moved exact pre-carve restoration
  capture out of the GDScript hot path; the 15-request single-sample loop remains
  only as a compatibility fallback. Dynamic mixed-LOD gameplay readiness remains
  an S1 blocker.

S1.6 - dynamic LOD visual-burst budget plus multi-view gross-pop and
region-bounds gates are complete.

Commands:

```console
python tools/capture_lod_popping.py
python tools/capture_lod_surface.py
python tools/capture_lod_temporal.py
python tools/capture_lod_temporal_multiview.py
python tools/review_lod_temporal.py
```

Result:

- vendored addon: World Transvoxel 1.0.11-dev from upstream commit
  `a84256e9a1d6877d994be6a7fd221285f00e4c99`;
- `render_apply_budget = 1` is now the locked reference runtime/visual policy
  for dynamic mixed-LOD captures; budget 2 passed the single-view temporal gate
  but still failed the multi-view gate, and budget 1 passed both without
  loosening thresholds;
- the sandbox terrain material remains opaque. World Transvoxel 1.0.9 exposed
  native `wt_fade_opacity`, but consuming it as transparent alpha in this
  terrain material created worse patch/sorting artifacts and is not the
  accepted surface-mode policy;
- diagnostic mode: fixed camera, LOD-color debug view, autonomous input
  disabled, and native terrain demand anchor moved independently of camera
  motion;
- anchors: 6;
- replacement frames observed: 140;
- saved diagnostic captures: 12 under `artifacts/dynamic_lod`;
- report: `artifacts/dynamic_lod/dynamic_lod_report.json`;
- maximum staged retirements: 92;
- maximum render-set delta in one observed frame: 7;
- maximum native fading resources: 59;
- fade frames observed: 295;
- maximum queued render/collision backlog: 0 / 0;
- center render/collision probe stayed present during replacements;
- classification:
  `lod_transition_native_fade_without_geomorph_pending_visual_acceptance`;
- comparison against S1.1 baseline: improved from 61 to 7 maximum one-frame
  render-set delta; S1.2 previously observed 79 replacement frames with the
  same render-set delta, S1.3 proved native fade-out activity, S1.5 proved
  native fade-in/fade-out activity, and S1.6 locks a one-chunk render-apply
  budget plus multi-view temporal measurement;
- proven: retirement smoothing and native render fade-in/fade-out are active,
  bounded, keep queues/probes stable, and stay under the automated gross-pop
  and region-bounds thresholds in the deterministic single-view and multi-view
  captures;
- not proven: seamless dynamic LOD appearance, final human qualitative
  confirmation, all camera angles, all movement speeds, or geomorphing.

Surface-mode still evidence:

- replacement frames observed: 140;
- saved surface captures: 12 under `artifacts/dynamic_lod_surface`;
- report: `artifacts/dynamic_lod_surface/dynamic_lod_surface_report.json`;
- maximum render-set delta in one observed frame: 7;
- maximum native fading resources: 59;
- fade frames observed: 294;
- classification: `surface_transition_pending_visual_acceptance`;
- AI pre-review of the generated still-image contact sheet found stable terrain
  massing across the baseline and transition captures, with no hard hole,
  missing backside, upside-down terrain, diagonal ridge, or full chunk
  disappearance visible in the inspected surface stills;
- not proven: temporal seamlessness. Still images do not replace video/capture
  review, direct technical inspection, or stricter automated temporal criteria
  for accepting the default dynamic LOD policy.

Single-view temporal surface evidence:

- frames captured: 540 under `artifacts/dynamic_lod_temporal`;
- preview: `artifacts/dynamic_lod_temporal/temporal_preview.gif`;
- top-change review sheet:
  `artifacts/dynamic_lod_temporal/temporal_top_change_pairs_review.png`;
- per-anchor transition review sheet:
  `artifacts/dynamic_lod_temporal/temporal_anchor_transition_review.png`;
- report: `artifacts/dynamic_lod_temporal/dynamic_lod_temporal_report.json`;
- maximum render-set delta: 8;
- maximum native fading resources: 59;
- fade frames observed: 164;
- maximum visible changed ratio between adjacent frames: 0.002314;
- maximum mean RGB delta between adjacent frames: 0.000471;
- maximum visible changed pixels between adjacent frames: 1,301;
- maximum changed bounding-box visible ratio between adjacent frames: 0.034371;
- maximum-change pair: `anchor_00_frame_049.png` to
  `anchor_00_frame_050.png`;
- gross-pop gate: passed across six anchors against visible-ratio limit 0.005
  and mean-RGB limit 0.002;
- region-bounds gate: passed across six anchors against changed-pixel limit
  4,096 and changed bounding-box visible-ratio limit 0.20;
- classification:
  `temporal_surface_gross_pop_gate_pass_pending_human_review`;
- proven: these deterministic surface transitions do not produce a large
  measured frame-to-frame image swap under the automated gross-pop and
  region-bounds gates;
- AI visual pre-review of the generated review sheets found localized
  silhouette/edge changes only, with no hard hole, missing backside,
  upside-down terrain, or full chunk disappearance visible in the worst
  measured pairs;
- not proven: final human qualitative confirmation, all camera angles, all
  movement speeds, or geomorphing.

Multi-view temporal surface evidence:

- views: front, side, and diagonal;
- frames captured: 1,080 under `artifacts/dynamic_lod_temporal_multiview`;
- preview:
  `artifacts/dynamic_lod_temporal_multiview/temporal_multiview_preview.gif`;
- top-change review sheet:
  `artifacts/dynamic_lod_temporal_multiview/temporal_multiview_top_change_pairs_review.png`;
- report:
  `artifacts/dynamic_lod_temporal_multiview/dynamic_lod_temporal_multiview_report.json`;
- maximum render-set delta: 8;
- maximum native fading resources: 59;
- fade frames observed: 490;
- maximum visible changed ratio between adjacent frames: 0.004534;
- maximum mean RGB delta between adjacent frames: 0.000845;
- maximum visible changed pixels between adjacent frames: 2,381;
- maximum changed bounding-box visible ratio between adjacent frames: 0.150831;
- maximum-change pair:
  `view_02_diagonal_anchor_02_frame_041.png` to
  `view_02_diagonal_anchor_02_frame_042.png`;
- gross-pop gate: passed across three views and six anchors against
  visible-ratio limit 0.005 and mean-RGB limit 0.002;
- region-bounds gate: passed across three views and six anchors against
  changed-pixel limit 4,096 and changed bounding-box visible-ratio limit 0.20;
- classification:
  `temporal_multiview_gross_pop_gate_pass_pending_human_review`;
- AI visual pre-review of the generated multi-view top-change sheet found
  localized silhouette/edge changes only, with no hard hole, missing backside,
  upside-down terrain, or full chunk disappearance visible in the worst measured
  pairs;
- not proven: final human qualitative confirmation, all camera angles, all
  movement speeds, or geomorphing.

S1.7 - conservative default dynamic LOD containment is complete.

Commands:

```console
python tools/validate_sandbox.py
python tools/test_sandbox.py
```

Result:

- normal sandbox/playtest defaults are fixed-center LOD0 reference mode:
  `radius_chunks = 4`, `maximum_lod = 0`, and
  `streaming_follows_viewer = false`;
- `config/terrain_config.tres` keeps `render_apply_budget = 1`;
- `scenes/terrain_lab.tscn` already used the conservative scene values, and
  `scripts/terrain_lab.gd` now uses the same conservative fallback defaults for
  newly instantiated labs;
- overlay policy text now reports `fixed LOD0 reference` for the accepted normal
  playtest mode and marks mixed LOD as diagnostic when enabled;
- dynamic mixed LOD captures and scale-ladder audits remain explicit opt-in
  diagnostics/tests by setting `maximum_lod = 1`;
- not proven: dynamic mixed LOD is still not a seamless default play mode. S1.7
  was containment, and S1.10 later made the default-policy decision to keep that
  path diagnostic-only instead of treating fade-only transitions as accepted
  gameplay.

Post-vendor 1.0.11-dev verification passed:

```console
python tools/validate_sandbox.py
python -m py_compile tools/capture_lod_temporal.py tools/capture_lod_temporal_multiview.py tools/review_lod_temporal.py tools/test_sandbox.py tools/validate_sandbox.py tools/runtime_budget_profiles.py
python tools/test_sandbox.py
python tools/capture_visuals.py
python tools/scale_runtime.py --level L4
python tools/scale_visual.py --level L4
python tools/s1_lod0_workload_audit.py
```

Result:

- repository validation: `WT_SANDBOX_VALIDATION_PASS vendored_files=147
  project_files=240`;
- sandbox matrix: `WT_SANDBOX_MATRIX_PASS engines=2 configurations=2 tests=8
  cases=32`;
- visual capture: `WT_SANDBOX_VISUAL_EVIDENCE_PASS images=9`;
- L4 runtime: `WT_SANDBOX_SCALE_RUNTIME_PASS level=L4 engines=2`, with
  active chunk capacity 1,024, `render_apply_budget=1`, minimum render 210,
  minimum collision 195, and max pending retirements 0;
- L4 visual shader-budget gate:
  `WT_SANDBOX_SCALE_VISUAL_PASS level=L4 images=7`, with no Godot
  `Too many instances using shader instance variables` errors;
- S1 LOD0 workload regression:
  `WT_SANDBOX_S1_LOD0_WORKLOAD_AUDIT_PASS engines=2`.

S2.14 - L4 shader-instance budget and same-key render-node stability fix is
complete.

Result:

- source fix: World Transvoxel 1.0.11-dev makes `wt_fade_opacity`
  instance-parameter writes opt-in/default-off because Godot retains
  per-instance shader parameter slots; accepted large-scale defaults allocate no
  per-instance shader fade parameter slots, while native engine transparency fade
  remains active;
- source fix: same-key LOD remeshes preserve the active `MeshInstance3D` and
  fade the previous mesh through a temporary retiring copy, so downstream node
  identity does not churn when only mesh generation changes;
- blocker resolved: the previous L4 visual run produced Godot
  `Too many instances using shader instance variables` errors; this is no longer
  accepted as a future issue and must remain a hard validation failure if it
  returns. The rerun L4 visual gate now passes with accepted defaults because no
  per-instance shader fade parameter slots are allocated by default.

S2.13 - L4 bounded generation, runtime, and static visual capture are complete.

Commands:

```console
python tools/scale_ladder.py --level L4 --force
python tools/scale_runtime.py --level L4
python tools/scale_visual.py --level L4
```

Result:

- dimensions: 2,053 x 69 x 2,053 samples;
- source samples: 290,821,821;
- source bytes: 1,744,930,926;
- expected pages: 73,728;
- stable payload bytes: 3,057,795,983;
- generation seconds: 2,651.646;
- volumetric columns: 562,862;
- world hash:
  `0f908b1e36c8c602ca884070c40d360e6a661274135791f13dafab1f48384368`;
- bounded memory contract: streamed Python source estimate 68,160,000 bytes,
  bounded native bake estimate 77,840,384 bytes, and required available memory
  with reserve 614,711,296 bytes;
- direct L4 source/generation remains guarded: it requires scale-ladder
  resource preflight and `--resource-preflight-approved`;
- L4 accepted runtime budget: staged movement, radius 3, maximum LOD 1, active
  chunk capacity 1,024, render-apply budget 1, inherited cache budgets;
- runtime evidence: Godot 4.6.3 and 4.7, seven staged positions, 35
  render/collision probes, latest minimum render/collision coverage 210 / 195,
  one active-window edit/remesh, clean shutdown, and max pending retirements 0;
- visual evidence: seven Godot 4.7 captures under
  `artifacts/scale_ladder/L4/visual`, all nonblank, covering overview,
  material, LOD, top, underground tunnel, closed boundary, and boundary
  materials;
- permanent boundary regression: an outside-in collision ray at y=12, z=1024
  must hit the finite wall at x=0.500 before any internal geometry;
- proven: L4 bounded generation, storage validation, Godot startup, staged
  movement render/collision coverage, one edit/remesh, clean shutdown, and
  static visual capture;
- not proven: final human qualitative confirmation, dynamic seamless LOD
  appearance, fast travel/disjoint teleport movement, target-hardware gameplay
  workload, water/lava, planets, structural collapse, or scale beyond L4.

S2.10 - L3 visual capture and artifact classification is complete for
automated static visual and targeted boundary evidence.

Command:

```console
python tools/scale_visual.py --level L3
```

Result:

- engine: Godot 4.7 graphical mode;
- accepted runtime budget: staged movement, radius 3, maximum LOD 1, active
  chunk capacity 1,024;
- captures: 7 images under `artifacts/scale_ladder/L3/visual`;
- capture ranges: overview/material/LOD 0.706, top 0.090, tunnel 0.617,
  boundary/material boundary 0.471;
- defect found and rejected: the first boundary capture contained an opening
  where rays passed the expected x=0.5 shell and hit geometry at x=3.9 to 9.0;
- diagnosis: disabling shadows and forcing LOD0 did not remove the opening,
  while authoritative samples proved x=0 empty and x=1 solid; the generator
  had allowed a cave to begin at x=2 behind a one-sample wall;
- fix: source revision 10003 reserves three solid samples between finite-map
  boundaries and procedural caves, chambers, and tunnels; L0 through L3 were
  regenerated and their runtime/visual evidence was rerun;
- permanent regression: an outside-in collision ray at y=12, z=546 must hit
  the finite wall at x=0.500 before any internal geometry;
- proven: nonblank representative L3 static captures, closed targeted boundary
  collision, staged runtime coverage on the corrected artifact, and no
  regression in the full L0 test matrix;
- not proven: final human qualitative confirmation, dynamic seamless LOD
  appearance, fast travel/disjoint teleport movement, or L4 2048 support.

S2.9 - L3 runtime acceptance is complete for headless runtime evidence.

Command:

```console
python tools/scale_runtime.py --level L3
```

Result:

- engines: Godot 4.6.3 and 4.7;
- accepted L3 runtime budget: staged movement, radius 3, maximum LOD 1,
  active chunk capacity 1,024, inherited cache budgets;
- positions: 7 staged positions across the 1,024 world;
- probes: 35 render/collision probes per engine;
- minimum rendered chunks: 201;
- minimum collision chunks: 201;
- Godot 4.6.3: startup 140 ms, settle 2,833 ms, edit 563 ms;
- Godot 4.7: startup 129 ms, settle 2,634 ms, edit 563 ms;
- edit density delta: 6.0;
- maximum pending retirements: 0;
- fixed during this step: the first audit edited the distant map center after
  the viewer reached the final stage, so the durable edit committed but no
  active chunk required remeshing; the audit now edits inside the final active
  window and proves remeshing;
- proven: derived L3 runtime budget, Godot startup, staged movement
  render/collision coverage, one active-window edit/remesh, clean shutdown;
- not proven: visual artifact acceptance, dynamic seamless LOD appearance,
  fast travel or disjoint teleport movement, or L4 2048 support.

S2.8 - L3 runtime budget planning is complete.

Result:

- local demand is derived from radius 3 and maximum LOD 1, not total world
  width;
- L2 observed active set bound: approximately 308 chunks;
- conservative full replacement bound: 616 records;
- selected active chunk capacity: 1,024, leaving 408 records above that bound;
- inherited storage/page/mesh/render/collision cache budgets remain explicit
  in `config/terrain_config.tres`;
- the budget was provisional until S2.9 runtime acceptance passed.

S2.7 - L3 1024 generation preflight is complete for generation-only evidence.

Command:

```console
python tools/scale_ladder.py --level L3 --force
```

Result:

- horizontal cells: 1,024;
- vertical cells: 64;
- dimensions: 1,029 x 69 x 1,029 samples;
- LOD0 chunks: 64 x 4 x 64;
- pages: 18,432;
- generation seconds: 504.486;
- scale-ladder elapsed seconds: 512.271;
- stable world payload bytes: 764,449,679;
- source samples: 73,060,029;
- volumetric columns: 141,327;
- source revision: 10003 with a three-sample finite solid-shell guard;
- resource preflight: 6,340,239,360 free bytes, 1,881,200,750 required
  bytes including a 512 MiB safety reserve, and 2,673,745,920 available
  memory bytes;
- warnings: none reported by the regenerated scale-ladder artifact;
- world hash:
  `e6f74c2b9bcf60263229e4a15ed0133d82fe2973816a1139fcd908cc821e9567`;
- proven: Python generation, native bake tool, storage validation;
- not proven: Godot startup, movement/render/collision coverage, visual
  artifact acceptance, edit latency, or L4 2048 scale support.

S2.6 - L2 visual capture and artifact classification is complete for
automated static visual evidence.

Command:

```console
python tools/scale_visual.py --level L2
```

Result:

- engine: Godot 4.7 graphical mode;
- runtime budget: L2 staged movement profile with active chunk capacity 1,024;
- captures: 7 images under `artifacts/scale_ladder/L2/visual`;
- capture ranges: overview/material 0.626, LOD 0.639, top 0.077, tunnel
  0.773, boundary/material boundary 0.434;
- fixed during this step: the first L2 tunnel capture placed the camera too
  close to the tunnel wall and produced a large clipped wall plane, so the
  tunnel camera now follows the generated L2 tunnel centerline;
- classified: overview surface is upright and nonblank;
- classified: top view has no old side-band symptom, but remains low-detail
  because the current procedural terrain material is flat;
- classified: finite boundary shell is expected in boundary captures;
- classified: LOD color partitioning is expected in LOD debug captures;
- classified: underground tunnel is visible after centerline reframing;
- proven: representative L2 static visual captures were produced and every
  capture had nonblank viewport range;
- not proven: final human qualitative confirmation, dynamic seamless LOD
  appearance, fast travel or disjoint teleport movement, or 1024/2048 scale
  support.

S2.5 - L2 runtime acceptance path is complete for headless runtime evidence.

Command:

```console
python tools/scale_runtime.py --level L2
```

Result:

- engines: Godot 4.6.3 and 4.7;
- L2 runtime budget: active chunk capacity 1,024;
- positions: 5 staged positions;
- probes: 25 render/collision probes per engine;
- minimum rendered chunks: 176;
- minimum collision chunks: 176;
- Godot 4.6.3: startup 119 ms, settle 2,914 ms, edit 562 ms;
- Godot 4.7: startup 108 ms, settle 2,500 ms, edit 561 ms;
- edit density delta: 6.0;
- maximum pending retirements: 0;
- classified during this step: the original L2 audit failed with the default
  512 active/change capacity because L2 movement can replace most of a 294
  chunk active set and exceed the delta budget; L2 runtime acceptance therefore
  uses an explicit 1,024 active chunk capacity;
- locked during this step: runtime budgets are now first-class acceptance data
  in `docs/TERRAIN_RUNTIME_BUDGETS.md` and are checked by
  `python tools/runtime_budget_profiles.py --check`;
- proven: Godot startup, staged movement render/collision coverage, one
  density edit/remesh, clean shutdown;
- not proven: visual artifact acceptance, dynamic seamless LOD appearance,
  fast travel or disjoint teleport movement, or 1024/2048 scale support.

S2.4 - L2 512 generation preflight is complete for generation-only evidence.

Command:

```console
python tools/scale_ladder.py --level L2 --force
```

Result:

- horizontal cells: 512;
- vertical cells: 64;
- dimensions: 517 x 69 x 517 samples;
- LOD0 chunks: 32 x 4 x 32;
- pages: 4,608;
- generation seconds: 135.595;
- scale-ladder elapsed seconds: 138.322;
- stable world payload bytes: 191,113,103;
- source samples: 18,442,941;
- volumetric columns: 36,259;
- source revision: 10003 with a three-sample finite solid-shell guard;
- warnings: none reported by the scale-ladder tool;
- world hash:
  `167c8a4aa98611bf324c373558d170509b67358dfaff7fd535fb486c51d5cd4a`;
- proven: Python generation, native bake tool, storage validation;
- not proven: Godot startup, movement/render/collision coverage, visual
  artifact acceptance, edit latency, dynamic seamless LOD appearance, or
  1024/2048 scale support.

S2.3 - L1 visual capture and artifact classification is complete for automated
visual evidence.

Command:

```console
python tools/scale_visual.py --level L1
```

Result:

- engine: Godot 4.7 graphical mode;
- captures: 7 images under `artifacts/scale_ladder/L1/visual`;
- capture ranges: overview/material/LOD 0.701, top 0.088, tunnel 0.749,
  boundary/material boundary 0.443;
- fixed during this step: L1 graphical capture originally exceeded the GL
  compatibility shader instance-variable limit, so LOD debug coloring now uses
  per-LOD material copies instead of per-instance shader parameters;
- fixed during this step: L1 overlay/bounds reporting still assumed a 128 map,
  so debug UI now reads active world bounds;
- classified: finite boundary shell is expected in boundary captures;
- classified: LOD color partitioning is expected in LOD debug captures;
- not proven: final human qualitative confirmation, dynamic seamless LOD
  appearance, or 512/1024/2048 scale support.

S2.2 - L1 runtime acceptance path is complete for headless runtime evidence.

Command:

```console
python tools/scale_runtime.py --level L1
```

Result:

- engines: Godot 4.6.3 and 4.7;
- positions: 5 staged positions;
- probes: 25 render/collision probes per engine;
- minimum rendered chunks: 97;
- minimum collision chunks: 97;
- Godot 4.6.3: startup 127 ms, settle 2,989 ms, edit 497 ms;
- Godot 4.7: startup 115 ms, settle 2,776 ms, edit 496 ms;
- edit density delta: 6.0;
- proven: Godot startup, staged movement render/collision coverage, one
  density edit/remesh, clean shutdown;
- not proven: visual artifact acceptance, dynamic seamless LOD appearance, or
  512/1024/2048 scale support.

S2.1 - Python scale-ladder generation proof is complete for L1.

Command:

```console
python tools/scale_ladder.py --level L1 --force
```

Result:

- horizontal cells: 256;
- vertical cells: 64;
- pages: 1,152;
- latest generation seconds: 29.442;
- stable world payload bytes: 47,778,959;
- source revision: 10003 with a three-sample finite solid-shell guard;
- world hash:
  `4e052784ce8743a6ac72f34a8fef23699875e7fad7ed61ff8e12da1bf5ac5ff0`;
- proven: Python generation, native bake tool, storage validation;
- not proven: Godot startup, movement/render/collision coverage, visual
  artifact acceptance, edit latency, or 512/1024/2048 scale support.

## Current active task

Post-S5 active task - keep sandbox tracking aligned after
`world-transvoxel-terrain` A6 game repository readiness decision.

Scope:

- keep `world-transvoxel-sandbox` as the reference/evidence project for
  `world-transvoxel`;
- keep `world-transvoxel-terrain` as the reusable terrain addon above
  `world-transvoxel`;
- keep `world-transvoxel-validation-game` as the separate validation repository;
- use the official MIT-backed backend first;
- keep GDScript limited to scaffolding, input, debug UI, and test harness glue;
- keep hot terrain work in native code, low-level addon paths, binary formats,
  shaders when justified, or Python offline tooling;
- avoid giant source files by requiring separate public API, runtime
  implementation, storage, editor/debug, and test ownership;
- keep compute, fluids, planets, stability, production game systems, and 0BSD
  backend replacement deferred until separately contracted.

Exit:

- this handoff is satisfied when the sandbox status records the
  `world-transvoxel-terrain` A0/A1/A2/A3/A4 phase 1/A4 phase 2/A4 phase 3/A4
  phase 4/A4 phase 5/A5 phase 1/A5 phase 2/A5 phase 3/A5 phase 4/A5 phase 5
  and A6 commits plus validation-game G0 through G6 evidence and points further
  work to the approved next boundary.

## Next finite steps

1. Human visually verifies `world-transvoxel-validation-game` G6 generated
   flat and mountain playable profiles.
2. Record visual, orientation, artifact, popping, or performance failures as
   addon follow-up work, not hidden validation-game workarounds.
3. Keep production game systems, GPU compute, fluids, planets, and 0BSD backend
   replacement out of scope until separately contracted.

## Deferred by rule

- compute shaders;
- water and lava;
- planetary terrain;
- structural collapse;
- timed regeneration;
- small-game repository;
- independent 0BSD backend replacement.
