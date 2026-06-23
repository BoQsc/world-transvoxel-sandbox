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
- Godot 4.6.3: startup 301 ms, settle 3,704 ms, edit 512 ms;
- Godot 4.7: startup 110 ms, settle 2,752 ms, edit 529 ms;
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

S2.3 - L1 visual capture and artifact classification.

Scope:

- keep L0 128 as the default accepted playtest world;
- capture representative L1 visuals and classify artifacts;
- inspect surface, material, LOD, boundary, and at least one underground view;
- keep the report explicit that dynamic seamless LOD is still not proven;
- do not change accepted playtest semantics just to make a larger map appear;
- do not hide visual artifacts behind feature work.

Exit:

- L1 visual captures exist under artifacts and have nonblank viewport range;
- all visible artifacts found during L1 inspection are classified;
- no GDScript performance logic is added for this step.

## Next finite steps

1. Add L1 visual capture/reporting.
2. Classify any artifact before moving to 512.
3. Move to L2 512 only after L1 has generation, runtime, and visual evidence.

## Deferred by rule

- compute shaders;
- water and lava;
- planetary terrain;
- structural collapse;
- timed regeneration;
- small-game repository;
- independent 0BSD backend replacement.
