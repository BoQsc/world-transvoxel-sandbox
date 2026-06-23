# Sandbox Validation Roadmap

This roadmap ends in a decision about using World Transvoxel in a small game.
It does not begin 0BSD replacement or compute work prematurely.
The governing quality gate is `docs/TERRAIN_ACCEPTANCE_STANDARD.md`: larger
artifact-free terrain and standards come before optional feature systems.
Runtime budget acceptance is tracked in `docs/TERRAIN_RUNTIME_BUDGETS.md`.
The short-form tracker is `docs/CURRENT_STATUS.md`.

## S0 - Visible integration

Status: revalidated against World Transvoxel 1.0.2.

- vendored and locked World Transvoxel 1.0.2 release; 1.0.0 is withdrawn and
  1.0.1 is superseded for premature moving-viewer chunk retirement;
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

Status: reference-scene stability defaults are in place; human
appearance/playtest review remains.

- dynamic mixed-LOD replacement popping remains an explicit visual blocker;
- classify every visible artifact as topology/collision, generation,
  material/shading, LOD transition, streaming/lifetime, harness
  misunderstanding, or documented limitation;
- do not accept holes, missing backsides, upside-down terrain, diagonal ridges,
  or unexplained popping as normal behavior;
- inspect surfaces, caves, and interaction feel using the conservative LOD0
  reference scene;
- inspect mixed-LOD appearance separately using the existing audit/debug views;
- decide whether visible LOD popping requires geomorphing, cross-fading,
  stronger hysteresis, larger prefetch rings, or a different default policy;
- add real texture-array/triplanar assets after the procedural palette is
  accepted;
- record representative screenshots and identified defects;
- confirm editing appearance and persistence after restart.

Exit: no visible correctness blocker remains in the test gallery.

## S2 - Chunked generation and scale ladder

Status: active; L0 remains the default accepted playtest world. L1 256 has
generation, headless runtime, and automated visual evidence. L2 512 has
generation, headless runtime, and automated static visual evidence, but is not
yet human or dynamically visually accepted. L3 1024 has generation and
headless runtime evidence, but no visual acceptance.

- follow the terrain acceptance standard scale ladder: 128, 256, 512, 1024,
  and 2048 horizontal cells;
- keep scale-ladder orchestration in Python/native-facing tooling, not
  performance-sensitive GDScript;
- require every accepted runtime level to declare a budget profile before it is
  used for visual capture, larger-scale work, or gameplay reference work;
- L1 generated artifact evidence: 1,152 pages, 47,778,959 stable payload
  bytes, latest generation 33.125 seconds, world hash
  `fb10bfa47bc7530a78a41791c155599e3d4e9a7a1a070aea4dcf6acd2a01084b`;
- L1 headless runtime evidence: Godot 4.6.3 and 4.7 startup, five staged
  positions, 25 render/collision probes, minimum 97 render/collision chunks,
  one density edit/remesh, and clean shutdown;
- L1 visual evidence: seven Godot 4.7 captures covering overview, material,
  LOD, top, underground tunnel, closed boundary, and boundary materials; the
  finite boundary shell and LOD color partition are classified as expected
  debug/finite-map views, not open terrain holes;
- L2 generated artifact evidence: 4,608 pages, 191,113,103 stable payload
  bytes, 150.745 generation seconds, 18,442,941 source samples, 37,026
  volumetric columns, no scale-ladder warnings, world hash
  `1d1e27ad6ca9521229e2a4c14693150cd64e214d63cae6d628b3ee6f06da6ad4`;
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
- L2 still not proven: human visual acceptance, dynamic seamless LOD
  appearance, fast travel or disjoint teleport movement, or larger-scale
  runtime/visual support;
- L3 generated artifact evidence: 18,432 pages, 764,449,679 stable payload
  bytes, 642.484 generation seconds, 73,060,029 source samples, 143,831
  volumetric columns, world hash
  `6c2ae9110f18fbc480a35308850ed97f981b155c7767e130a9b552de9f05e09d`;
- L3 resource warning: preflight had only 139,122,578 bytes above the
  conservative source/payload estimate plus 512 MiB safety reserve; generation
  completed, but the warning remains part of the evidence;
- L3 accepted runtime budget: staged movement, radius 3, maximum LOD 1,
  active chunk capacity 1,024, inherited cache budgets; derived from a 616
  full replacement bound rather than copied from world width;
- L3 headless runtime evidence: Godot 4.6.3 and 4.7 startup, seven staged
  positions, 35 render/collision probes, minimum 201 render/collision chunks,
  one active-window edit/remesh, and clean shutdown;
- L3 not yet proven: visual acceptance, dynamic seamless LOD appearance, fast
  travel or disjoint teleport movement, or L4 2048 support;
- replace whole-volume source generation with bounded chunked/sparse baking;
- run 256, 512, 1024, and 2048 horizontal-cell worlds;
- record page count, disk size, bake duration, peak memory, startup latency,
  idle CPU/GPU/memory, movement latency, frame time, edit latency, visual
  captures, known defects, and shutdown;
- set the supported vertical range and target hardware profile.

Exit: the 2K claim is accepted with evidence or rejected with a measured
limit and redesign requirement.

## S3 - Visibility and production workload

Status: pending.

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
