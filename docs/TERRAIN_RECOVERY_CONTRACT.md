# Terrain Recovery Contract

This contract defines what "restore equilibrium" means for the sandbox before
we add larger systems such as timed regeneration, cave-ins, water, lava, or GPU
acceleration. It is intentionally narrower than a game design document: it
specifies terrain state semantics and what must remain deterministic.

## Current default

The default policy is `manual_exact_restore`.

- mining is permanent after commit;
- `Ctrl+Z` restores the last committed carve from exact pre-edit density
  samples at the original brush coordinates;
- explicit `restore_to_base` is available for audited/manual use and restores
  affected samples to deterministic generated base density/material;
- construction and material painting are separate operations, not undo;
- construction invalidates older carve snapshots because those snapshots no
  longer describe the current terrain state;
- automatic timed regeneration is disabled;
- automatic surface relaxation/smoothing is disabled;
- automatic structural collapse is disabled;
- water/lava/fluid equilibrium is not part of terrain recovery;
- settled terrain must stay cold: no recovery work, meshing work, or streaming
  work is allowed while nothing changed.

Transvoxel is only the meshing backend for the resolved density/material
field. It does not decide why terrain changes, what should regrow, what should
collapse, or whether a cave should fill with water. Those are separate policy
layers above the scalar field.

## Authoritative terrain model

All future recovery features must fit this layering:

```text
immutable base terrain
  -> semantic edit layers
  -> explicit recovery/stability/fluid events
  -> resolved density/material samples
  -> Transvoxel mesh/collision output
```

The base terrain is deterministic generated content. Edits are explicit
transactions. Recovery must never be an untracked background mutation hidden
inside the mesher.

## Restore targets

"Normal terrain" is ambiguous unless a target is named. Supported or reserved
targets are:

1. `pre_edit_snapshot` - the exact sampled state before a specific edit.
2. `base_terrain` - the original generated terrain at the same coordinates.
3. `checkpoint` - a saved world state chosen by the game.
4. `designer_stamp` - an authored repair/rebuild shape.
5. `settled_physics_state` - a new result after an enabled stability system.

`pre_edit_snapshot` is the default restore target. `base_terrain` is now
implemented as explicit `restore_to_base` and supports "heal mined area back to
generated terrain" without implying time-based regeneration or physics.

## Brush command standard

Mining, construction, painting, and future recovery commands should be stored
as semantic commands before they are lowered into voxel writes. A command
record must be able to describe:

- operation kind: carve, construct, paint, restore, relax, collapse, or fluid;
- shape: sphere, box, capsule, stamp, or future explicit field;
- transform: world-space center, orientation, radius/extent, and resolution;
- density operation: add, subtract, set, min, max, or blend;
- falloff: hard, linear, smoothstep, or authored curve;
- material rule: keep, paint, replace-filtered, or restore-sampled;
- quantization rule: grid resolution and deterministic rounding;
- affected bounds;
- author/tool identifier;
- world revision before and after;
- transaction identifier;
- persistence rule;
- optional recovery policy.

The sandbox currently uses sphere commands and exact point-density restoration
for the affected sphere grid. That is correctness-first, not the final storage
or performance format.

## Optional recovery modules

These systems are allowed only behind explicit toggles and separate tests:

- `restore_to_base`: restore density/material from the deterministic base
  generator inside a bounded region; S3 audits this as an explicit operation,
  not automatic regeneration;
- `timed_regeneration`: schedule bounded restoration over time;
- `surface_relaxation`: smooth or rebuild an edited signed-distance field in a
  bounded dirty region;
- `structural_stability`: compute support at a lower resolution and convert
  unsupported islands into debris, rigid bodies, or deferred collapse events;
- `fluid_equilibrium`: water/lava simulation and rendering driven by explicit
  fluid state, not by implicit terrain healing.

None of these modules may create idle work when disabled. Enabling one must
define its dirty-region bounds, update budget, persistence format, and
determinism requirements before implementation.

## Validation requirements

The sandbox must keep these checks:

- exact carve restoration recovers authoritative density and mesh hash;
- construction paints its material and is not treated as undo;
- no automatic recovery policy is enabled by default;
- settled default terrain performs no background work;
- restore-to-base must prove restored density/material equals the deterministic
  base terrain for the edited region;
- future timed regeneration must prove bounded work per frame and stable idle
  after completion;
- future stability must prove bounded dirty-region recomputation and must not
  run globally every frame.

This contract is part of the acceptance boundary for the small-game decision.
Compute shaders are deferred until the enabled policies and workloads are known.
