# Sandbox Validation Roadmap

This roadmap ends in a decision about using World Transvoxel in a small game.
It does not begin 0BSD replacement or compute work prematurely.

## S0 - Visible integration

Status: revalidated against World Transvoxel 1.0.2.

- vendored and locked World Transvoxel 1.0.2 release; 1.0.0 is withdrawn and
  1.0.1 is superseded for premature moving-viewer chunk retirement;
- deterministic 128 x 64 x 128 hills/caves/strata/veins world;
- material and LOD shader views;
- chunk, collision, queue, latency, and resource visualization;
- fly camera and interactive carve/fill/paint controls;
- 60 FPS cap and fixed-center complete-map LOD0 playtest mode with full
  collision availability for stable human inspection;
- idle-work regression proving settled terrain and sub-threshold camera
  movement do not produce new streaming or meshing work;
- headless startup, streaming, edit, and shutdown smoke test;
- complete loaded-world winding, collision, density-sign, edit, and finite-map
  boundary audit;
- exact full-world mixed-LOD manifold and cross-chunk normal-continuity audit;
- automated center-screen carve interaction and deterministic visual captures.
- continuous-motion render/collision coverage and bounded staged-retirement
  regression across the complete supported Godot/build matrix.

Exit: a human can see, navigate, inspect, and modify real terrain.

## S1 - Visual acceptance

Status: reference-scene stability defaults are in place; human
appearance/playtest review remains.

- dynamic mixed-LOD replacement popping remains an explicit visual blocker;
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

Status: pending.

- replace whole-volume source generation with bounded chunked/sparse baking;
- run 256, 512, 1024, and 2048 horizontal-cell worlds;
- record page count, disk size, bake duration, peak memory, startup latency,
  movement latency, frame time, and shutdown;
- set the supported vertical range and target hardware profile.

Exit: the 2K claim is accepted with evidence or rejected with a measured
limit and redesign requirement.

## S3 - Visibility and production workload

Status: pending.

- profile Godot frustum culling separately from terrain demand generation;
- add forward-biased prefetch while retaining an all-direction safety ring;
- test fast travel, rapid turns, underground movement, and repeated mining;
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
