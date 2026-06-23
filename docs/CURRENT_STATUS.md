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

S2.2 - L1 runtime acceptance path.

Scope:

- keep L0 128 as the default accepted playtest world;
- load the generated L1 artifact through Godot without pretending it is the
  accepted human playtest mode;
- measure startup, movement, render/collision coverage, and edit latency;
- capture representative L1 visuals and classify artifacts;
- do not change accepted playtest semantics just to make a larger map appear;
- do not hide visual artifacts behind feature work.

Exit:

- an L1 runtime report clearly says what is proven and what is still not
  proven;
- all visible artifacts found during L1 inspection are classified;
- no GDScript performance logic is added for this step.

## Next finite steps

1. Add a larger-world startup/motion/capture path for L1.
2. Classify any artifact before moving to 512.
3. Move to L2 512 only after L1 has generation plus runtime evidence.

## Deferred by rule

- compute shaders;
- water and lava;
- planetary terrain;
- structural collapse;
- timed regeneration;
- small-game repository;
- independent 0BSD backend replacement.
