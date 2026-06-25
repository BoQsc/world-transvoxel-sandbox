# Terrain Acceptance Standard

This is the standards-first operating rule for the sandbox until the terrain
is large, stable, understandable, and visually acceptable. Details will expand
as we learn more, but new feature work must not outrun this standard.

## Priority order

1. Correct terrain geometry and collision.
2. Artifact-free visual behavior in the accepted playtest mode.
3. Larger terrain scale with measured budgets.
4. Clear standards for edits, recovery, streaming, materials, and persistence.
5. Optional systems behind toggles.
6. GPU acceleration only for measured bottlenecks.

Water, lava, planets, structural collapse, mining effects, inventory, and game
repository work remain secondary until the terrain itself is proven at scale.

## Non-negotiable acceptance rules

- `+Y` is up and orientation must be visible in docs, overlay, and tests.
- Render mesh and collision must agree for loaded terrain.
- Terrain must be closed at finite-map boundaries unless a mode explicitly
  documents open streaming edges.
- Finite boundary guards must reserve a measured solid region before caves,
  chambers, tunnels, or other subtractive generation may begin. Acceptance
  requires an outside-in render/collision probe to hit the intended boundary
  before internal geometry; a correct density sign at one sample is not enough.
- No holes, missing backsides, upside-down terrain, diagonal ridges, or
  untracked visual artifacts may be accepted as normal.
- Human playtesting must use the stable accepted mode, not an experimental mode
  with known popping.
- Dynamic LOD popping remains a blocker until fixed or explicitly demoted by a
  documented standard. The current reference mitigation is native
  fade-in/fade-out with `render_apply_budget = 1`; higher render-apply bursts
  are not accepted as the default visual policy unless they pass the same gates.
- LOD-debug captures are diagnostic only. Dynamic LOD visual acceptance requires
  surface-mode transition evidence, and still-image evidence cannot by itself
  prove temporal seamlessness; video/human review or a stricter automated
  temporal criterion is required before accepting the default policy. The
  current automated gross-pop gate covers six deterministic surface-mode LOD
  anchors in the primary view plus the front/side/diagonal multi-view harness.
  It fails if more than 0.5% of visible pixels change between adjacent temporal
  surface frames or if mean RGB delta exceeds 0.2%; this catches large swaps
  but does not replace human acceptance.
- Settled terrain must stay cold: no hidden streaming, meshing, recovery, or
  regeneration work while nothing changed.
- Runtime budgets are part of acceptance. Each accepted scale must follow
  `docs/TERRAIN_RUNTIME_BUDGETS.md`; larger levels must not silently inherit
  smaller-level capacities.
- Generation preflight must account for both the offline generator and native
  bake lifetime. Raw source, decoded source, retained page payloads, and safety
  reserve count toward the peak; disk-only source size is not a memory bound.
- Unbounded whole-volume generation must be rejected before allocation when it
  exceeds the accepted source or peak-memory limit. Large levels may run only
  through preflight-authorized streamed source generation and bounded native
  bake paths. Estimate-only reports are evidence for a redesign decision, not
  evidence that the scale is supported.
- Autonomous captures and tests must disable player input from scene startup.
- Project scripts must remain cross-platform Python where external scripting is
  needed; no tracked PowerShell workflow scripts.
- GDScript is glue for Godot scene scaffolding, input routing, debug UI, and
  headless test harnesses; performance-sensitive terrain generation, meshing,
  large-map streaming policy, storage, recovery, fluids, and stability belong
  in native code, shaders/compute when justified, binary formats, or Python
  offline tooling.
- Source files should stay small and purpose-prefixed instead of collapsing into
  one large terrain file.

## Large-terrain ladder

The scale ladder is evidence-based. A size is not supported because the code
can theoretically generate it; it is supported only after passing the required
checks.

| Level | Horizontal cells | Purpose |
| --- | ---: | --- |
| L0 | 128 | correctness, visual debugging, edit semantics |
| L1 | 256 | first larger-terrain generation proof |
| L2 | 512 | movement and visibility workload proof |
| L3 | 1024 | large-map storage and latency proof |
| L4 | 2048 | target 2K map claim |

Each level must record:

- generation duration;
- peak generator memory;
- world/page count and disk size;
- runtime budget profile;
- startup latency;
- settled idle CPU/GPU/memory;
- movement latency and frame time;
- render/collision coverage during motion;
- edit latency and persistence behavior;
- representative visual captures;
- known visual defects.

The 2K map claim is rejected until L4 has this evidence.

## Visual artifact standard

Every artifact gets classified before feature work continues:

- topology/collision bug;
- generation bug;
- material/shading bug;
- LOD transition bug;
- streaming/lifetime bug;
- camera/test harness misunderstanding;
- accepted limitation with documented bounds.

Artifacts are not closed by assumption. They close by test, capture, or an
explicit human playtest note tied to the current accepted mode.

## Standard-first feature policy

Optional systems may be designed now, but they must not become default behavior
until they have their own contract and tests.

- Recovery follows `docs/TERRAIN_RECOVERY_CONTRACT.md`.
- Timed regeneration is off until restore-to-base exists and is measured.
- Surface smoothing is off until the desired terrain style is defined.
- Structural collapse is off until support-graph rules are specified.
- Water and lava are separate fluid systems, not implicit terrain recovery.
- Compute shaders are deferred until CPU/native behavior and workloads are
  stable enough to compare end-to-end.

## Decision tracking

`docs/CURRENT_STATUS.md` records the active milestone, current task, exit
criteria, next finite steps, and deferred systems. If a decision does not
change the active milestone, it belongs in that tracker or a backlog note; it
must not interrupt the scale ladder.

## Exit condition

This standard is satisfied when a larger terrain level can be generated,
opened, moved through, inspected, edited, saved, restored, and captured without
unexplained artifacts or uncontrolled background work.
