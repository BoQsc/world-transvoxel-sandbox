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

Status: revalidated against World Transvoxel 1.0.10-dev.

- vendored and locked World Transvoxel 1.0.10-dev sandbox build; 1.0.0 is withdrawn,
  1.0.1 is superseded for premature moving-viewer chunk retirement, and 1.0.3
  is superseded for one-frame bulk retirement during dynamic mixed-LOD motion;
  1.0.5 adds a bounded native render fade-out for retiring chunks after
  replacement application, and 1.0.6 adds a bounded native render fade-in for
  newly introduced chunks; 1.0.9 exposes the native `wt_fade_opacity` shader
  parameter, and 1.0.10-dev adds native batched authoritative sample queries
  for exact restore capture; the reference sandbox terrain material remains
  opaque;
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

Status: reference-scene stability defaults, a one-chunk render-apply budget,
single-view plus multi-view temporal gross-pop and region-bounds gates, and the
conservative fixed-center LOD0 sandbox default are in place. S1 is not complete:
technical acceptance of dynamic mixed LOD remains open; human review remains
final qualitative confirmation.

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
  measured max carve submit 135 ms and max total carve settle 415 ms across the
  supported Godot matrix;
- classify every visible artifact as topology/collision, generation,
  material/shading, LOD transition, streaming/lifetime, harness
  misunderstanding, or documented limitation;
- do not accept holes, missing backsides, upside-down terrain, diagonal ridges,
  or unexplained popping as normal behavior;
- inspect surfaces, caves, and interaction feel using the conservative LOD0
  reference scene;
- inspect mixed-LOD appearance separately using the existing audit/debug views;
- decide whether the native fade is acceptable as the default policy or whether
  visible LOD transitions still require geomorphing, stronger hysteresis, larger
  prefetch rings, or a different default policy;
- add real texture-array/triplanar assets after the procedural palette is
  accepted;
- record representative screenshots and identified defects;
- confirm editing appearance and persistence after restart.

Exit: no visible correctness blocker remains in the test gallery.

## S2 - Chunked generation and scale ladder

Status: automated scale-ladder evidence is complete through L4 / 2048. L0
remains the default accepted human playtest world. L1, L2, L3, and L4 have
generation, headless runtime, and automated static visual evidence. None of
the larger mixed-LOD levels are yet technically or dynamically visually
accepted; final human qualitative confirmation also remains open.

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
- L4 not yet proven: final human qualitative confirmation, dynamic seamless LOD
  appearance, fast travel/disjoint teleport movement, target-hardware gameplay
  workload, or scale support beyond 2048;
- set the supported vertical range and target hardware profile before claiming
  game-readiness beyond this reference machine.

Exit: the automated 2K scale-ladder claim is accepted for bounded generation,
staged runtime, edit/remesh, and static visual capture. Final human qualitative
confirmation, dynamic seamless LOD movement, and gameplay workload acceptance
remain outside S2.

## S3 - Visibility and production workload

Status: inactive. S3 must not start until S1 exits or the roadmap is explicitly
redefined. The LOD0 workload audit is S1.8 because it affects S1 interaction
feel and accepted-playtest correctness.

- profile Godot frustum culling separately from terrain demand generation;
- add forward-biased prefetch while retaining an all-direction safety ring;
- test fast travel, rapid turns, underground movement, and repeated mining;
- measure restoration capture latency and edit-journal growth; replace the
  correctness-first point-command snapshot with a compressed native delta path
  if it misses the production interaction or storage budgets;
- implement and audit restore-to-base as the next recovery target before any
  timed regeneration, surface relaxation, or stability/collapse module;
- establish idle CPU, active CPU, render, physics, I/O, and memory budgets.

Exit: the representative small-game workload meets its budgets without
visible holes or uncontrolled resource growth.

## S4 - M6 decision

Status: pending and evidence-gated.

- select only a measured bottleneck;
- compare complete CPU and compute paths, including transfer/readback;
- keep deterministic CPU/headless fallback;
- enable compute only when end-to-end behavior improves.

Exit: targeted compute acceleration ships, or M6 closes with CPU retained.

## S5 - Small-game decision

Status: pending.

Water/lava, mining effects, inventory, structural stability, and planetary
terrain remain separate systems. The independent 0BSD backend qualification
starts only after the official backend survives this vertical slice.

Exit: proceed with a game, revise the terrain architecture, or stop with a
documented reason.
