# Current Project Status

This file is the short-form tracker. It exists to prevent the project from
turning into an endless stream of small unrelated decisions.

## Active operating rule

Follow `docs/TERRAIN_ACCEPTANCE_STANDARD.md`.

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
- generation seconds: 150.745;
- scale-ladder elapsed seconds: 150.998;
- stable world payload bytes: 191,113,103;
- source samples: 18,442,941;
- volumetric columns: 37,026;
- warnings: none reported by the scale-ladder tool;
- world hash:
  `1d1e27ad6ca9521229e2a4c14693150cd64e214d63cae6d628b3ee6f06da6ad4`;
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
- Godot 4.6.3: startup 222 ms, settle 3,331 ms, edit 514 ms;
- Godot 4.7: startup 119 ms, settle 3,107 ms, edit 513 ms;
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
- latest generation seconds: 33.125;
- stable world payload bytes: 47,778,959;
- world hash:
  `fb10bfa47bc7530a78a41791c155599e3d4e9a7a1a070aea4dcf6acd2a01084b`;
- proven: Python generation, native bake tool, storage validation;
- not proven: Godot startup, movement/render/collision coverage, visual
  artifact acceptance, edit latency, or 512/1024/2048 scale support.

## Current active task

S2.5 - L2 runtime acceptance path.

Scope:

- use the generated L2 artifact path, not the accepted L0 playtest world;
- prove or reject Godot startup at L2 across the supported engine matrix;
- measure staged movement render/collision coverage at L2;
- measure one density edit/remesh at L2;
- keep dynamic visual acceptance separate from headless runtime acceptance.

Exit:

- `python tools/scale_runtime.py --level L2` produces a report or a documented
  failure;
- the report clearly says what is and is not proven at runtime;
- no GDScript performance logic is added.

## Next finite steps

1. Add L2 runtime acceptance support without changing the L0 default.
2. Run L2 headless startup/movement/collision/edit coverage.
3. Add L2 visual capture only if runtime acceptance succeeds.

## Deferred by rule

- compute shaders;
- water and lava;
- planetary terrain;
- structural collapse;
- timed regeneration;
- small-game repository;
- independent 0BSD backend replacement.
