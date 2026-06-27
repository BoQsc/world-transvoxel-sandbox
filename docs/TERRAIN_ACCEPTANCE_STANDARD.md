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
- Human review is final qualitative confirmation. It does not block technical
  milestone progress, and it cannot replace automated gates, deterministic
  captures, measured runtime evidence, native audits, or direct technical
  inspection.
- Dynamic LOD popping is demoted by the S1.10 documented standard, not accepted
  as normal gameplay behavior. The current reference mitigation is native
  fade-in/fade-out with `render_apply_budget = 1`, but fade-only mixed LOD is
  diagnostic-only until stronger evidence or a native mitigation closes the
  visual-quality gap. Higher render-apply bursts are not accepted as the
  default visual policy unless they pass the same or stronger gates.
- Normal sandbox/playtest defaults are conservative: fixed-center LOD0 reference
  mode with `radius_chunks = 4`, `maximum_lod = 0`, and
  `streaming_follows_viewer = false`. Dynamic mixed LOD remains
  diagnostic-only unless a later explicit milestone replaces
  `docs/S1_DYNAMIC_LOD_POLICY.md`. Human review remains final qualitative
  confirmation.
- LOD-debug captures are diagnostic only. Dynamic LOD visual acceptance requires
  surface-mode transition evidence, and still-image evidence cannot by itself
  prove temporal seamlessness; video/capture review, direct technical
  inspection, or a stricter automated temporal criterion is required before
  accepting the default policy. The current automated gross-pop and region-bounds
  gates cover six deterministic surface-mode LOD anchors in the primary view plus the front/side/diagonal multi-view harness.
  The gross-pop gate fails if more than 0.5% of visible
  pixels change between adjacent temporal surface frames or if mean RGB delta
  exceeds 0.2%. The region-bounds gate fails if more than 4,096 visible pixels
  change in one adjacent-frame pair or if the changed bounding box exceeds 20%
  of the visible terrain area. These gates catch large swaps and broad-region
  pops but do not replace final qualitative confirmation, and final qualitative
  confirmation does not replace technical correctness.
- Settled terrain must stay cold: no hidden streaming, meshing, recovery, or
  regeneration work while nothing changed.
- Runtime budgets are part of acceptance. Each accepted scale must follow
  `docs/TERRAIN_RUNTIME_BUDGETS.md`; the conservative LOD0 workload baseline
  must follow `docs/S1_LOD0_WORKLOAD_BASELINE.md`; larger levels must not silently
  inherit smaller-level capacities.
- The accepted LOD0 gallery and restart-persistence gate is part of S1
  technical exit. It must follow `docs/S1_LOD0_GALLERY_AUDIT.md` and print
  `WT_SANDBOX_S1_LOD0_GALLERY_AUDIT_PASS` before S1 is considered technically
  complete.
- The S1 default-policy gate is part of acceptance. The normal scene, script
  fallback defaults, overlay labels, and test matrix must keep dynamic mixed LOD
  out of the accepted playtest path unless the policy is explicitly replaced.
- Do not jump milestones. If work becomes necessary for the current milestone,
  reclassify it into the current milestone with exit criteria before doing it;
  otherwise defer it until the current milestone exits.
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
- Containment is not completion. A conservative default, diagnostic-only mode,
  or documented workaround must not be described as closing a milestone unless
  the original exit criteria are actually proven. `docs/CURRENT_STATUS.md` must
  keep unresolved blockers visible at the top and must distinguish usable
  baseline evidence from full implementation readiness.

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

The 2K map claim is rejected until L4 has this evidence. S2 scale-ladder exit
also requires `docs/S2_SCALE_LADDER_EXIT_REVIEW.md` and
`WT_SANDBOX_S2_EXIT_REVIEW_PASS`.

## Visual artifact standard

Every artifact gets classified before feature work continues:

- topology/collision bug;
- generation bug;
- material/shading bug;
- LOD transition bug;
- streaming/lifetime bug;
- camera/test harness misunderstanding;
- accepted limitation with documented bounds.

Artifacts are not closed by assumption. They close by test, capture, measured
evidence, or direct technical inspection. Human playtest notes confirm
appearance/game feel for the current accepted mode; they do not prove topology
or replace technical evidence.

## Standard-first feature policy

Optional systems may be designed now, but they must not become default behavior
until they have their own contract and tests.

- Recovery follows `docs/TERRAIN_RECOVERY_CONTRACT.md`.
- Timed regeneration remains off. Explicit restore-to-base exists and is
  measured, but time-based recovery needs a separate contract and tests.
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
