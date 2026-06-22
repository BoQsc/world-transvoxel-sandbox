# World Transvoxel Sandbox

Visual, gameplay, and scale validation for the qualified World Transvoxel
1.0.0 MIT-backed addon. This repository is deliberately a sandbox before it
becomes a game.

The vendored addon is the exact Windows x86-64 release from
`world-transvoxel` commit `f4d9aca`. Its mixed 0BSD/MIT scope and release
manifest are retained at the repository root.

## Run

Python 3.11 or newer is required for generation. Godot 4.6.3 or 4.7 is the
qualified engine matrix.

```console
python tools/validate_sandbox.py
python tools/generate_world.py --force
python tools/test_sandbox.py
```

Then open `project.godot`, or run:

```console
Godot --path .
```

## Controls

- right mouse: capture/release mouse;
- mouse: look;
- `WASD`: move;
- `Q` / `E`: descend/ascend;
- Shift: fast movement;
- mouse wheel: adjust movement speed;
- left mouse: carve terrain;
- Shift + left mouse: fill terrain;
- Ctrl + left mouse: paint an ore material;
- `F1`: normal/material/LOD shader view;
- `F2`: chunk-boundary overlay;
- `F3`: physics collision debug;
- `F4`: metrics/help overlay.

## Current validation scope

The initial generated world is 128 x 64 x 128 cells with 256 LOD0 pages and
32 LOD1 pages. It contains deterministic hills, cliffs, caves, material
strata, and ore veins. The shader reads the addon's categorical material ID
from `UV2.x` and provides normal, material-debug, and LOD-debug views.

This does not yet prove a 2K map, GPU compute, water, lava, planetary terrain,
or structural stability. Those gates are finite and recorded in
[`docs/ROADMAP.md`](docs/ROADMAP.md).

## License

Sandbox-owned code is 0BSD. The vendored World Transvoxel addon is mixed
0BSD/MIT because it includes Eric Lengyel's official MIT Transvoxel backend.
See `WORLD_TRANSVOXEL_LICENSE_SCOPE.md`, `LICENSES/MIT-Transvoxel.txt`, and
`addons/world_transvoxel/LICENSE_SCOPE.md`.
