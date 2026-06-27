# Repository Boundary Contract

This contract locks the repository/package roles so the project does not drift
back into mixed-purpose terrain experiments.

## Accepted names and roles

`world-transvoxel` is the base native Godot addon. It owns the Transvoxel
meshing/backend boundary, official MIT backend isolation, future optional 0BSD
backend qualification, low-level terrain APIs, and native systems that must be
shared by terrain users.

`world-transvoxel-sandbox` is the reference/evidence sandbox for
`world-transvoxel`. It proves base addon behavior, scale, streaming, edits,
visual captures, performance budgets, and reference terrain patterns.

`world-transvoxel-terrain` is the future reusable game-terrain addon. It
packages proven terrain patterns from the sandbox into game-ready APIs,
resources, presets, materials, debug tools, generation policies, save/load
hooks, and terrain interaction conventions.

A future game repository is the consumer/integration project. It imports
`world-transvoxel` and `world-transvoxel-terrain`, keeps terrain-specific game
code minimal, and validates the terrain addon in real gameplay.

## Validation boundary

world-transvoxel-sandbox validates world-transvoxel.

future game repository validates world-transvoxel-terrain.

Do not use world-transvoxel-sandbox to test world-transvoxel-terrain.

`world-transvoxel-terrain` may have its own local unit/smoke tests, but its real
acceptance proof belongs in the future game repository, not in this sandbox.

## Dependency boundary

```text
future game repository
  depends on world-transvoxel-terrain
  depends on world-transvoxel

world-transvoxel-terrain
  depends on world-transvoxel

world-transvoxel-sandbox
  depends on world-transvoxel

world-transvoxel
  standalone base addon
```

## Extraction rule

The sandbox may prove reference behavior and terrain patterns. Stable, reusable
terrain systems may later be extracted into `world-transvoxel-terrain`.

game projects must not fork or copy the sandbox as their terrain architecture.

The intended game experience is:

```text
install world-transvoxel
install world-transvoxel-terrain
add terrain scene/resource
choose config preset
connect player/camera
run
```

## Naming guard

Do not replace these roles with vague names such as `transvoxel-addon` or
`world-transvoxel-core` without explicitly revising this contract.

## Milestone consequence

S3 and S4 remain sandbox milestones for proving `world-transvoxel` behavior and
performance boundaries. S5 may decide whether to create the future game
repository, but the game repository is separate from this sandbox and is the
place where `world-transvoxel-terrain` gets real gameplay confirmation.
