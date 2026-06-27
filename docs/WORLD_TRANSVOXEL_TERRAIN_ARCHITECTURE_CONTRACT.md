# World Transvoxel Terrain Architecture Contract

Status: active post-S5 architecture gate.

Validation marker:

```text
WT_SANDBOX_WORLD_TRANSVOXEL_TERRAIN_CONTRACT_PASS
```

This contract defines what `world-transvoxel-terrain` must become before a
separate game repository is created. It is not a game design document, not a GPU
rewrite plan, and not a 0BSD backend replacement milestone.

## Repository role

`world-transvoxel-terrain` is the reusable Godot terrain addon that sits above
`world-transvoxel`.

It packages proven sandbox terrain patterns into stable game-facing APIs,
resources, presets, materials, debug tools, generation policies, save/load hooks,
and edit/recovery conventions.

It must not be a copy of `world-transvoxel-sandbox`. The sandbox is evidence and
reference material only. Stable behavior may be extracted or reimplemented as
addon code when it has a clear package boundary.

The intended consumer path remains:

```text
install world-transvoxel
install world-transvoxel-terrain
add terrain scene/resource
choose config preset
connect player/camera
run
```

## Dependency and license boundary

- `world-transvoxel-terrain` depends on `world-transvoxel`.
- The official MIT-backed World Transvoxel backend is used first.
- Optional independent 0BSD backend work remains deferred until the official
  backend survives the terrain addon and later game validation path.
- `world-transvoxel-sandbox` remains a reference/evidence project and must not
  become a required game dependency.
- The future game repository imports `world-transvoxel` and
  `world-transvoxel-terrain`; it does not fork or copy this sandbox.

## Scope imported from S5

The first useful terrain addon must support the S5 smallest vertical slice:

- load a 2048 x 2048 x 64 terrain profile derived from the S2/S3 L4 evidence;
- expose terrain through installable Godot addon assets;
- connect a player/camera through explicit API calls or exported scene links;
- support surface and underground exploration;
- support carve, construct, fill, paint, and restore-to-base interaction modes;
- preserve edits through save/restart;
- expose debug/status UI for chunk, collision, queue, budget, and edit state;
- keep fast travel as loading-screen semantics unless later evidence changes it.

## Performance and implementation rules

Performance-sensitive terrain work belongs in native code, low-level addon
interfaces, shaders when already justified, binary formats, or Python offline
tooling.

GDScript is allowed for:

- scene scaffolding;
- Godot editor glue;
- input routing;
- debug UI;
- small smoke-test harnesses.

GDScript is not the place for:

- terrain generation hot paths;
- meshing;
- large-map streaming policy;
- persistent storage format processing;
- edit recovery algorithms;
- fluid simulation;
- structural stability;
- compute-heavy validation.

Compute shaders remain rejected for now by S4. The addon must keep a deterministic
CPU/native path as the accepted baseline. Compute can only return under a later
measured bottleneck contract.

## Source organization rules

The terrain addon must avoid the old single-large-source-file failure mode.

Expected organization:

- small, prefixed source files by subsystem;
- separate public API, runtime implementation, storage, editor/debug, and tests;
- explicit package manifests and license files;
- binary formats for large terrain data and edit journals;
- deterministic offline generation tools where generation is not runtime-hot;
- event-based state changes instead of hidden continuous background work;
- stable public APIs plus optional subsystem interfaces, not many redundant APIs.

The public API should be small and boring first. Optional systems must extend it
through explicit contracts instead of widening every base class.

## Required addon concepts

The first architecture pass must define names and ownership for these concepts:

- terrain world/root node;
- terrain profile/resource;
- generation profile;
- streaming policy;
- edit controller;
- edit operation descriptions;
- save/load and journal boundary;
- material/texture policy;
- collision policy;
- debug/status overlay;
- runtime budget profile;
- test harness entry points.

The exact class names may change during implementation, but the concepts may not
silently disappear.

## Terrain behavior standard

The addon must inherit the current sandbox standards:

- `+Y` is up;
- finite maps need an explicit closed-boundary policy;
- underground terrain must be volumetric, not heightfield-only;
- terrain edits operate on authoritative voxel samples, not visual-only meshes;
- restore-to-base is explicit and audited before automatic regeneration;
- settled terrain must be cold unless player action, streaming demand, or an
  explicit enabled system creates work;
- holes, missing backsides, upside-down terrain, diagonal artifacts, unexplained
  popping, and unbounded CPU/GPU use are defects until classified.

## Deferred optional systems

The following remain outside the first terrain-addon architecture unless a later
contract moves them in:

- water and lava;
- planets or alternate gravity worlds;
- structural collapse/stability;
- vegetation;
- building blocks;
- inventory/economy systems;
- advanced mining animations/effects;
- automatic timed regeneration or equilibrium simulation;
- broad GPU compute implementation;
- independent 0BSD backend replacement;
- separate game repository.

## Evidence inherited from the sandbox

This contract depends on:

- `docs/REPOSITORY_BOUNDARY_CONTRACT.md`;
- `docs/S5_SMALL_GAME_DECISION.md`;
- `docs/S5_VERTICAL_SLICE_REQUIREMENTS.md`;
- `docs/S4_M6_DECISION.md`;
- `docs/S3_EXIT_REVIEW.md`;
- `docs/S2_SCALE_LADDER_EXIT_REVIEW.md`;
- `docs/TERRAIN_ACCEPTANCE_STANDARD.md`;
- `docs/TERRAIN_RUNTIME_BUDGETS.md`;
- `docs/TERRAIN_RECOVERY_CONTRACT.md`.

These documents prove enough to design the addon boundary. They do not prove that
the future addon is already implemented or game-ready.

## Exit criteria for this architecture gate

This gate is complete when:

- this contract exists and passes `tools/world_transvoxel_terrain_contract_check.py`;
- `tools/future_milestone_contracts_check.py` includes this contract;
- `docs/CURRENT_STATUS.md`, `docs/ROADMAP.md`, and `README.md` point to this
  contract as the active post-S5 workstream;
- the next action is explicitly limited to `world-transvoxel-terrain` addon
  architecture or skeleton work;
- no separate game repository has been created as part of this gate.

After this gate passes, the next valid action is to create the
`world-transvoxel-terrain` addon architecture/skeleton. The game repository
remains deferred until the terrain addon exists with its own package boundary and
local smoke tests.
