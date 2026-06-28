# Sandbox Validation Roadmap

This roadmap ends in a decision about using World Transvoxel in a small game.
It does not begin 0BSD replacement or compute work prematurely.
The governing quality gate is `docs/TERRAIN_ACCEPTANCE_STANDARD.md`: larger
artifact-free terrain and standards come before optional feature systems.
Runtime budget acceptance is tracked in `docs/TERRAIN_RUNTIME_BUDGETS.md`.
The short-form tracker is `docs/CURRENT_STATUS.md`.

Milestone order is strict. Do not start later-milestone implementation while the
current milestone is incomplete. If a task is required for the current
milestone, move it into that milestone before doing it.

## S0 - Visible integration

Status: revalidated against World Transvoxel 1.0.11-dev.

- vendored and locked World Transvoxel 1.0.11-dev sandbox build; 1.0.0 is withdrawn,
  1.0.1 is superseded for premature moving-viewer chunk retirement, and 1.0.3
  is superseded for one-frame bulk retirement during dynamic mixed-LOD motion;
  1.0.5 adds a bounded native render fade-out for retiring chunks after
  replacement application, and 1.0.6 adds a bounded native render fade-in for
  newly introduced chunks; 1.0.9 exposes the native `wt_fade_opacity` shader
  parameter; 1.0.10-dev adds native batched authoritative sample queries for
  exact restore capture; and 1.0.11-dev makes `wt_fade_opacity`
  instance-parameter writes opt-in/default-off because Godot retains
  per-instance shader parameter slots while keeping native engine transparency
  fade and same-key render nodes stable; the reference sandbox terrain material
  remains opaque;
- deterministic 128 x 64 x 128 surface baseline plus volumetric caves,
  chamber, winding tunnel, XYZ rock geology, and ore vein;
- material and LOD shader views;
- chunk, collision, queue, latency, and resource visualization;
- fly camera and distinct carve/construct/paint controls;
- bounded pre-carve authoritative sample capture and exact LIFO carve
  restoration at the original brush coordinates;
- terrain recovery contract with `manual_exact_restore` as the default and
  automatic regeneration, smoothing, collapse, and fluid equilibrium disabled;
- 60 FPS cap and fixed-center complete-map LOD0 playtest mode with full
  collision availability for stable human inspection;
- idle-work regression proving settled terrain and sub-threshold camera
  movement do not produce new streaming or meshing work;
- headless startup, streaming, edit, and shutdown smoke test;
- complete loaded-world winding, collision, density-sign, edit, and finite-map
  boundary audit;
- exact full-world mixed-LOD manifold and cross-chunk normal-continuity audit;
- automated carve, exact restoration, material-bearing construction,
  non-heightfield underground, and deterministic visual captures;
- continuous-motion render/collision coverage and bounded staged-retirement
  regression across the complete supported Godot/build matrix.

Exit: a human can see, navigate, inspect, and modify real terrain.

## S1 - Visual acceptance

Status: S1 technical exit evidence is complete. Reference-scene stability
defaults, a one-chunk render-apply budget, single-view plus multi-view temporal
gross-pop and region-bounds gates, native batched exact-restore capture, the
S1.10 dynamic mixed-LOD default-policy decision, and the S1.11 accepted LOD0
gallery/restart-persistence audit are in place. The accepted default playtest
path is fixed-center LOD0. Dynamic mixed LOD is rejected/demoted as default and
remains diagnostic-only until a later explicit milestone supplies stronger
technical evidence or native mitigation. Human review remains final qualitative
confirmation.

- dynamic mixed-LOD appearance remains an explicit visual acceptance gate after
  the 1.0.9 native fade-in/fade-out and budget-1 temporal evidence;
- S1.1 dynamic evidence classifies the current blocker as
  `lod_transition_visual_swap_without_geomorph`: fixed-camera demand-anchor
  movement observed 39 render-set replacement frames, maximum staged
  retirements 36, maximum render-set delta 61, no render/collision probe loss,
  and no render/collision queue backlog;
- S1.2 native retirement smoothing in World Transvoxel 1.0.4 reduced maximum
  one-frame render-set delta from 61 to 8, but replacement frames increased to
  79 and staged retirements to 92; this is an improvement, not visual
  acceptance;
- S1.3 native fade-out transition smoothing in World Transvoxel 1.0.5 proved
  the fade path was active, but still left the temporal surface gate too narrow
  and did not prove technical visual acceptance, final human qualitative
  confirmation, or geomorphing;
- S1.4 adds surface-mode dynamic transition captures because LOD-debug captures
  are diagnostic only; the surface stills show no hard hole or obvious large
  terrain swap, but temporal technical acceptance and final human qualitative
  confirmation remain open;
- S1.5 native fade-in/fade-out transition smoothing in World Transvoxel 1.0.6
  records six deterministic anchors and 540 temporal surface frames; it passes
  the automated gross-pop gate with maximum visible changed ratio 0.004353
  against limit 0.005 and maximum mean RGB delta 0.000872 against limit 0.002;
  this still does not prove technical visual acceptance, final human qualitative
  confirmation, all camera angles, or geomorphing;
- S1.6 locks `render_apply_budget = 1` for the reference dynamic mixed-LOD
  policy and adds a three-view temporal harness. With World Transvoxel 1.0.9,
  single-view temporal evidence passes with maximum visible changed ratio
  0.002314, maximum mean RGB delta 0.000471, 1,301 changed visible pixels, and
  changed bounding-box visible ratio 0.034371; multi-view evidence passes with
  maximum visible changed ratio 0.004534, maximum mean RGB delta 0.000845,
  2,381 changed visible pixels, and changed bounding-box visible ratio 0.150831.
  This still does not prove technical visual acceptance, final human qualitative
  confirmation, all camera angles, all movement speeds, or geomorphing;
- S1.7 applies containment, not completion: normal sandbox/playtest paths use
  fixed-center LOD0 reference mode, while dynamic mixed LOD remains
  diagnostic/experimental until technical acceptance or a native mitigation
  closes the visual-quality gap; final human review confirms appearance/game
  feel but does not replace technical evidence;
- S1.8 reclassifies the conservative LOD0 workload audit as S1 evidence because
  mining latency and interaction feel affect S1 visual/playtest acceptance;
  `docs/S1_LOD0_WORKLOAD_BASELINE.md` and
  `python tools/s1_lod0_workload_audit.py` pass on Godot 4.6.3 and 4.7;
- S1.9 replaces the GDScript exact-restore capture loop with a native batched
  authoritative sample query. The workload audit now gates carve submission,
  total carve settle, and restore settle under 2,000 ms; the accepted run
  measured max carve submit 139 ms and max total carve settle 417 ms across the
  supported Godot matrix;
- S1.10 resolves the dynamic mixed-LOD default-policy question for S1:
  dynamic mixed LOD is not accepted as default gameplay, remains explicit
  diagnostic-only, and is guarded by `docs/S1_DYNAMIC_LOD_POLICY.md`,
  `tests/terrain_s1_default_policy_audit.gd`, and
  `python tools/test_sandbox.py`;
- S1.11 adds the accepted fixed-center LOD0 gallery and restart-persistence
  audit. `docs/S1_LOD0_GALLERY_AUDIT.md`,
  `tools/s1_lod0_gallery_audit.py`, and
  `tests/terrain_s1_lod0_persistence_audit.gd` pass with
  `WT_SANDBOX_S1_LOD0_GALLERY_AUDIT_PASS`; the audit captures nine nonblank
  1280 x 720 gallery images, requires closed-boundary render/collision ray
  agreement, rejects Godot errors, and proves an edit journal survives
  stop/start with exact edited density and stable mesh identity on Godot 4.6.3
  and 4.7;
- classify every visible artifact as topology/collision, generation,
  material/shading, LOD transition, streaming/lifetime, harness
  misunderstanding, or documented limitation;
- do not accept holes, missing backsides, upside-down terrain, diagonal ridges,
  or unexplained popping as normal behavior;
- inspect surfaces, caves, and interaction feel using the conservative LOD0
  reference scene;
- inspect mixed-LOD appearance separately using the existing audit/debug views;
- do not promote native fade-only mixed LOD to default gameplay unless a later
  milestone replaces the S1.10 diagnostic-only policy with stronger evidence;
- add real texture-array/triplanar assets after the procedural palette is
  accepted;
- record representative screenshots and identified defects;
- confirm editing appearance and persistence after restart.

Technical exit: complete by S1.11. No automated hard visual blocker remains in
the accepted fixed-center LOD0 test gallery, mining latency is under the S1.9
native-batch gate, and dynamic mixed LOD is explicitly rejected/demoted as
default gameplay. Final human qualitative confirmation remains the last external
confirmation.

## S2 - Chunked generation and scale ladder

Status: complete for automated S2 exit by
`WT_SANDBOX_S2_EXIT_REVIEW_PASS`. L0 remains the default accepted human playtest
world. L1, L2, L3, and L4 have generation, headless runtime, and automated
static visual evidence. None of the larger mixed-LOD levels are yet technically
or dynamically visually accepted; final human qualitative confirmation also
remains open.

- follow the terrain acceptance standard scale ladder: 128, 256, 512, 1024,
  and 2048 horizontal cells;
- keep scale-ladder orchestration in Python/native-facing tooling, not
  performance-sensitive GDScript;
- require every accepted runtime level to declare a budget profile before it is
  used for visual capture, larger-scale work, or gameplay reference work;
- L1 generated artifact evidence: 1,152 pages, 47,778,959 stable payload
  bytes, latest generation 29.442 seconds, source revision 10003, world hash
  `4e052784ce8743a6ac72f34a8fef23699875e7fad7ed61ff8e12da1bf5ac5ff0`;
- L1 headless runtime evidence: Godot 4.6.3 and 4.7 startup, five staged
  positions, 25 render/collision probes, minimum 97 render/collision chunks,
  one density edit/remesh, and clean shutdown;
- L1 visual evidence: seven Godot 4.7 captures covering overview, material,
  LOD, top, underground tunnel, closed boundary, and boundary materials; the
  finite boundary shell and LOD color partition are classified as expected
  debug/finite-map views, not open terrain holes;
- L2 generated artifact evidence: 4,608 pages, 191,113,103 stable payload
  bytes, 135.595 generation seconds, 18,442,941 source samples, 36,259
  volumetric columns, no scale-ladder warnings, world hash
  `167c8a4aa98611bf324c373558d170509b67358dfaff7fd535fb486c51d5cd4a`;
- L2 headless runtime evidence: Godot 4.6.3 and 4.7 startup, five staged
  positions, 25 render/collision probes, minimum 176 render/collision chunks,
  one density edit/remesh, clean shutdown, and explicit active chunk capacity
  1,024;
- L2 runtime classification: the default 512 active/change capacity rejected
  L2 staged movement because the active set is about 294 chunks and large
  staged moves can exceed the delta budget; this is a budget boundary, not a
  visual acceptance result, and it is now locked in
  `docs/TERRAIN_RUNTIME_BUDGETS.md`;
- L2 visual evidence: seven Godot 4.7 captures covering overview, material,
  LOD, top, underground tunnel, closed boundary, and boundary materials; the
  first L2 tunnel framing was rejected and fixed by moving the camera onto the
  generated tunnel centerline;
- L2 static visual classification: overview is upright/nonblank, top view has
  no old side-band symptom but remains low-detail with the flat procedural
  palette, boundary shell is expected, and LOD color partitioning is expected
  in debug view;
- L2 still not proven: final human qualitative confirmation, dynamic seamless
  LOD appearance, fast travel or disjoint teleport movement, or larger-scale
  runtime/visual support;
- L3 generated artifact evidence: 18,432 pages, 764,449,679 stable payload
  bytes, 504.486 generation seconds, 73,060,029 source samples, 141,327
  volumetric columns, world hash
  `e6f74c2b9bcf60263229e4a15ed0133d82fe2973816a1139fcd908cc821e9567`;
- source revision 10003 reserves three solid samples between finite-map
  boundaries and procedural caves, chambers, and tunnels at every generated
  scale;
- L3 accepted runtime budget: staged movement, radius 3, maximum LOD 1,
  active chunk capacity 1,024, inherited cache budgets; derived from a 616
  full replacement bound rather than copied from world width;
- L3 headless runtime evidence: Godot 4.6.3 and 4.7 startup, seven staged
  positions, 35 render/collision probes, minimum 201 render/collision chunks,
  one active-window edit/remesh, and clean shutdown;
- L3 visual evidence: seven Godot 4.7 captures covering overview, material,
  LOD, top, underground tunnel, closed boundary, and boundary materials;
- L3 boundary defect and fix: static inspection found an opening in the finite
  wall; shadow and LOD0 isolation ruled out shading and transition causes,
  collision rays located a cave immediately behind a one-sample wall, and the
  three-sample source guard closed it. A permanent outside-in ray now requires
  the first collision at x=0.500 in the affected region;
- L3 not yet proven: final human qualitative confirmation, dynamic seamless LOD
  appearance, or fast travel/disjoint teleport movement;
- L4 bounded generation evidence: 290,821,821 samples, 1,744,930,926 source
  bytes, 73,728 pages, 3,057,795,983 stable payload bytes, 2,651.646
  generation seconds, 562,862 volumetric columns, no scale-ladder warnings,
  and world hash
  `0f908b1e36c8c602ca884070c40d360e6a661274135791f13dafab1f48384368`;
- L4 preflight memory contract: streamed Python source estimate 68,160,000
  bytes, bounded native bake estimate 77,840,384 bytes, required available
  memory with reserve 614,711,296 bytes, and no resource blockers on the
  accepted run;
- L4 accepted runtime budget: staged movement, radius 3, maximum LOD 1, active
  chunk capacity 1,024, inherited cache budgets;
- L4 headless runtime evidence: Godot 4.6.3 and 4.7 startup, seven staged
  positions, 35 render/collision probes, minimum 195 render/collision chunks,
  one active-window edit/remesh, and clean shutdown;
- L4 visual evidence: seven Godot 4.7 captures covering overview, material,
  LOD, top, underground tunnel, closed boundary, and boundary materials; the
  permanent outside-in ray requires the first collision at x=0.500;
- S2.14 L4 shader-instance budget fix: 1.0.11-dev makes `wt_fade_opacity`
  instance-parameter writes opt-in/default-off so accepted large-scale defaults
  allocate no per-instance shader parameter slots, keeps native engine
  transparency fade active, and preserves active render-node identity during
  same-key LOD remeshes while fading the previous mesh through a temporary
  retiring copy; the rerun L4 visual gate passes with seven images and no Godot
  `Too many instances using shader instance variables` errors;
- S2 exit review: `docs/S2_SCALE_LADDER_EXIT_REVIEW.md` and
  `tools/s2_exit_review.py` validate L1-L4 generation, runtime, static visual,
  declared budget, L3/L4 boundary-marker, and bounded L4 preflight evidence;
- L4 not yet proven: final human qualitative confirmation, dynamic seamless LOD
  appearance, fast travel/disjoint teleport movement, target-hardware gameplay
  workload, or scale support beyond 2048;
- set the supported vertical range and target hardware profile before claiming
  game-readiness beyond this reference machine.

Exit: complete for automated 2K scale-ladder evidence. The accepted S2 claim is
bounded generation, staged runtime, edit/remesh, and static visual capture
through L4. Final human qualitative confirmation, dynamic seamless LOD movement,
and gameplay workload acceptance remain outside S2.

S1/S2 go/no-go: `docs/S1_S2_COMPLETION_CHECKLIST.md` and
`tools/s1_s2_completion_checklist.py` report
`WT_SANDBOX_S1_S2_COMPLETION_CHECKLIST_PASS`. S3 may start after S2 exit;
this does not complete S3 systems.

## S3 - Visibility and production workload

Status: complete. Scope is governed by
`docs/S3_VISIBILITY_PRODUCTION_WORKLOAD_CONTRACT.md` and
`docs/S3_COMPLETION_CHECKLIST.md`. GPU compute, water/lava, planets, structural
collapse, a game repository, and 0BSD backend replacement remain out of scope
unless the S3 contract explicitly moves them in.

- first headless L4 visibility/frustum workload baseline: complete by
  `WT_SANDBOX_S3_VISIBILITY_WORKLOAD_AUDIT_PASS`;
- forward-biased prefetch: accepted by `docs/S3_FORWARD_PREFETCH_POLICY.md`
  with a secondary movement-direction viewer while retaining the primary
  all-direction safety ring;
- test fast travel, rapid turns, underground movement, and repeated mining;
- measure restoration capture latency and edit-journal growth; replace the
  correctness-first point-command snapshot with a compressed native delta path
  if it misses the production interaction or storage budgets;
- keep explicit restore-to-base audited before any timed regeneration, surface
  relaxation, or stability/collapse module;
- keep graphical visual/GPU artifact acceptance audited as part of S3 exit review;
- establish idle CPU, active CPU, render, physics, I/O, and memory budgets;
- close with `docs/S3_EXIT_REVIEW.md` and `WT_SANDBOX_S3_EXIT_REVIEW_PASS`.

Exit: the representative small-game workload meets its budgets without
visible holes or uncontrolled resource growth.

## S4 - M6 decision

Status: complete by `WT_SANDBOX_S4_M6_DECISION_PASS`. Scope was governed by
`docs/S4_M6_DECISION_CONTRACT.md` plus `docs/S4_COMPLETION_CHECKLIST.md`.

S4 selected interactive edit-settle latency by
`WT_SANDBOX_S4_BOTTLENECK_SELECTION_PASS`, attributed it with
`WT_SANDBOX_S4_CPU_EDIT_PHASE_BASELINE_AUDIT_PASS`, then closed with
CPU/native retained and compute rejected for now.

- select only a measured bottleneck;
- attribute the selected edit-settle latency across CPU/native phases;
- compare complete CPU and compute paths, including transfer/readback;
- keep deterministic CPU/headless fallback;
- enable compute only when end-to-end behavior improves.

Exit: targeted compute acceleration ships, or M6 closes with CPU retained.

## S5 - Small-game decision

Status: complete by `WT_SANDBOX_S5_SMALL_GAME_DECISION_PASS`. Scope was governed by
`docs/S5_SMALL_GAME_DECISION_CONTRACT.md` plus
`docs/S5_COMPLETION_CHECKLIST.md`. The repository/package boundary is locked by
`docs/REPOSITORY_BOUNDARY_CONTRACT.md`: `world-transvoxel-sandbox` validates
`world-transvoxel`, and a future game repository validates
`world-transvoxel-terrain`.

S5 defines the smallest game vertical slice, keeps the official MIT-backed
backend first, defers optional systems, and exits with
`revise_terrain_architecture_first`: create/design `world-transvoxel-terrain`
before creating the separate game repository.

Exit: complete. Decision is revise terrain architecture first; game repository
is deferred until `world-transvoxel-terrain` exists.

## Post-S5 - world-transvoxel-terrain addon architecture

Status: architecture gate complete; separate addon repository A4 phase 4
reference runtime/cold-idle validation complete.
Scope is governed by `docs/WORLD_TRANSVOXEL_TERRAIN_ARCHITECTURE_CONTRACT.md`
and checked by `tools/world_transvoxel_terrain_contract_check.py`.

This is the next valid workstream after S5. It defines the reusable
`world-transvoxel-terrain` addon boundary before any separate game repository is
created.

- use the official MIT-backed `world-transvoxel` backend first;
- package proven sandbox terrain patterns into addon APIs, resources, presets,
  materials, debug tools, save/load hooks, and edit/recovery conventions;
- keep performance-sensitive generation, meshing, storage, streaming, and
  recovery work out of GDScript hot paths;
- avoid giant source files by separating public API, runtime implementation,
  storage, editor/debug, and tests;
- keep compute rejected for now by S4 unless a later measured bottleneck contract
  reopens it;
- keep water/lava, planets, structural stability, vegetation, building blocks,
  inventory/economy systems, advanced mining effects, timed regeneration,
  independent 0BSD backend replacement, and the game repository deferred.

Exit: complete for the sandbox-side post-S5 handoff. The
`world-transvoxel-terrain` repository exists with A0 skeleton commit `244db4c`
and A1 public API/source-layout contract commit `f076597`, plus A2
addon-local smoke harness commit `8609c99`, plus A3 `world-transvoxel` bridge
commit `ef03d55`, plus A4 phase 1 resource semantics commit `2774664`, plus A4
phase 2 bridge/storage fixture commit `4b8855c`, plus A4 phase 3 terrain-world
lifecycle commit `b28c623`, plus A4 phase 4 reference runtime/cold-idle
validation commit `9007b83`. The next valid action is A4 phase 5 A4 exit review
in `world-transvoxel-terrain`, not a game repository.
