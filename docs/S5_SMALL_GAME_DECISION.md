# S5 Small-Game Decision

S5 status: complete.

Decision: revise terrain architecture first.

Command:

```console
python tools/s5_small_game_decision.py
```

Expected marker:

```text
WT_SANDBOX_S5_SMALL_GAME_DECISION_PASS decision=revise_terrain_architecture_first
```

## Decision basis

S3 proves the representative L4 production workload, graphical artifact gate,
restore-to-base audit, and S3 exit review.

S4 proves the selected edit-settle bottleneck does not justify compute now.
CPU/native remains the accepted path and compute is rejected for now.

S5 defines the smallest game vertical slice in
`docs/S5_VERTICAL_SLICE_REQUIREMENTS.md`.

## Outcome

Do not create the game repository yet.

The next architecture step is to create or design `world-transvoxel-terrain`,
the reusable terrain addon that packages the proven sandbox patterns into
game-facing APIs, resources, presets, materials, debug tools, save/load hooks,
and terrain interaction conventions.

That post-S5 workstream is governed by
`docs/WORLD_TRANSVOXEL_TERRAIN_ARCHITECTURE_CONTRACT.md` and checked by
`tools/world_transvoxel_terrain_contract_check.py`.

After `world-transvoxel-terrain` exists, a separate game repository may validate
it by importing:

- `world-transvoxel`;
- `world-transvoxel-terrain`.

The game must not fork or copy `world-transvoxel-sandbox`.

## Locked decisions

- official MIT-backed World Transvoxel backend is used first;
- independent 0BSD backend replacement stays deferred until the official backend
  survives the vertical slice;
- compute shaders stay rejected for now by S4;
- water/lava, planets, structural stability, inventory, and advanced mining
  effects remain separate future contracts;
- fast travel remains loading-screen semantics until later evidence changes it.

## S5 exit classification

S5 exits as `revise_terrain_architecture_first`: the terrain reference is good
enough to define the vertical slice, but the game repository is deferred until a
real `world-transvoxel-terrain` addon exists.
