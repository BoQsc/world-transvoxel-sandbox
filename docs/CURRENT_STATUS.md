# Current Project Status

This file is the short-form tracker. It exists to prevent the project from
turning into an endless stream of small unrelated decisions.

## Active operating rule

Follow `docs/TERRAIN_ACCEPTANCE_STANDARD.md`.
Runtime scale budgets are governed by `docs/TERRAIN_RUNTIME_BUDGETS.md`.

Performance-sensitive terrain work belongs in native code, shaders/compute
when justified, binary formats, or Python offline tooling. GDScript is glue for
Godot scene scaffolding, input routing, debug UI, and headless test harnesses.
It is not where terrain generation, meshing, large-map streaming policy,
storage, recovery, fluids, or stability algorithms should live.

## Current milestone

S2 - chunked generation and scale ladder.

S0 is complete for the 128 baseline. S1 still has a visual blocker: dynamic
mixed-LOD popping is not accepted as seamless. We are not starting GPU compute,
water/lava, planets, structural collapse, a game repository, or 0BSD backend
replacement work before larger terrain behavior is measured.

## Latest evidence

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
- not proven: human visual acceptance, dynamic seamless LOD appearance, fast
  travel/disjoint teleport movement, or L4 2048 support.

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
- not proven: human visual acceptance, dynamic seamless LOD appearance, fast
  travel or disjoint teleport movement, or 1024/2048 scale support.

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
- not proven: human visual acceptance, dynamic seamless LOD appearance, or
  512/1024/2048 scale support.

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

S2.11 - L4 bounded-generation feasibility gate.

Scope:

- calculate the L4 source, payload, memory, disk, and duration estimates before
  allocating a 2,048 world;
- reject the current whole-volume source path if it cannot retain the safety
  reserve or a defensible memory bound;
- define and implement the bounded chunked/sparse source-generation path needed
  to make L4 safe;
- do not claim L4 support from preflight or generation alone.

Exit:

- an explicit L4 feasibility report records estimates and the accept/reject
  decision;
- an unsafe dense run cannot begin accidentally;
- if redesign is required, its bounded-memory contract and first automated
  proof are committed before L4 generation.

## Next finite steps

1. Add an L4 estimate-only profile and conservative resource gate.
2. Measure whether whole-volume source generation is safe on the target host.
3. Implement bounded source generation if the dense path is rejected; only
   then generate L4.

## Deferred by rule

- compute shaders;
- water and lava;
- planetary terrain;
- structural collapse;
- timed regeneration;
- small-game repository;
- independent 0BSD backend replacement.
