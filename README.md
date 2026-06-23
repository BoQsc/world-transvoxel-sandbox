# World Transvoxel Sandbox

Visual, gameplay, and scale validation for the qualified World Transvoxel
1.0.2 MIT-backed addon. This repository is deliberately a sandbox before it
becomes a game.

World Transvoxel 1.0.0 is rejected and withdrawn. This sandbox exposed its
incorrect Godot render/collision winding, incomplete convex mixed-LOD corner
deformation, and inadequate one-chunk acceptance tests. Version 1.0.1 is also
superseded because moving-viewer LOD changes could remove old chunks before
their replacements were applied. Version 1.0.2 is the current baseline; it is
not a claim that the sandbox is a finished terrain product or game.

The vendored addon is the exact Windows x86-64 release from
`world-transvoxel` commit `50f3a6d`. Its mixed 0BSD/MIT scope and release
manifest are retained at the repository root.

Dynamic mixed-LOD streaming is not yet visually seamless. It remains covered
by topology, render/collision continuity, and motion stress tests, but visible
LOD replacement popping is an open visual-quality blocker. The normal human
playtest therefore uses a fixed, complete LOD0 map and must not be presented
as proof that dynamic LOD appearance is finished.

## Run

Python 3.11 or newer is required for generation. Godot 4.6.3 or 4.7 is the
qualified engine matrix.

```console
python tools/validate_sandbox.py
python tools/generate_world.py --force
python tools/test_sandbox.py
python tools/capture_visuals.py
```

Then open `project.godot`, or run:

```console
Godot --path .
```

Autonomous tests and visual captures disable player input before the scene
enters the tree. Mouse capture and movement controls are enabled only for the
normal human playtest scene. Autonomous graphical tools that launch the main
scene must pass `-- --disable-player-input`.

## Controls

- right mouse: capture/release mouse;
- mouse: look;
- `WASD`: move;
- `Q` / `E`: descend/ascend;
- Shift: fast movement;
- mouse wheel: adjust movement speed;
- movement is constrained to the finite map; F5 resets the camera;
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
strata, and ore veins. `+Y` is up. Black beyond the terrain is outside the
finite closed map, and orange terrain patches are ore. The optional orange
wire box toggled by F2 is the map boundary.

The interactive reference scene is deliberately conservative: it is capped at
60 FPS and loads the complete small finite map once at LOD0 from a fixed
center anchor. Camera movement therefore causes no chunk or LOD replacement
in the human playtest view. Collision remains available across the complete
map so digging and inspection rays do not silently miss visible terrain.
Dynamic mixed-LOD streaming remains tested, but it is not the default
playtest view until LOD popping is addressed as a separate visual-quality
milestone.

On the current four-core / GTX 1060 Max-Q reference machine, a 12-second
settled sample of the fixed full-map scene with autonomous input disabled
averaged 21.1% of one CPU core (about 5.3% total machine CPU), 282.9 MiB RSS,
and 8.2 W GPU board power. A prior uncapped comparison averaged about 39.6%
total machine CPU, 56.8% device GPU utilization, and 32.5 W. Windows GPU
utilization counters are noisy, but the CPU and board-power difference
confirms that uncapped ~300 FPS rendering was the main unexplained load.

Correctness is checked automatically before human playtesting: every loaded
triangle is finite, nondegenerate, and outward-facing for Godot; render and
collision probes must agree; click-to-carve must change authoritative density
and remesh; mixed-LOD audits must include both LODs; every full-world triangle
edge must form a closed two-use manifold; and coincident cross-chunk normals
must agree. An idle audit also proves settled terrain creates no additional
viewer updates, sample jobs, mesh jobs, mesh completions, or publications,
that camera movement does not alter the fixed reference anchor, and that the
dynamic test mode honors the eight-unit streaming threshold.
Continuous motion checks 480 viewer positions, direct render coverage, and
2,400 collision probes while confirming staged replacement resources return
to zero after motion settles.
Eight deterministic captures cover surface, material, LOD, top, unshadowed
top, top LOD, and surface/material views of the closed boundary. Human review
is for appearance and game feel, not for proving Transvoxel topology.

This does not yet prove a 2K map, GPU compute, water, lava, planetary terrain,
or structural stability. Those gates are finite and recorded in
[`docs/ROADMAP.md`](docs/ROADMAP.md).

## License

Sandbox-owned code is 0BSD. The vendored World Transvoxel addon is mixed
0BSD/MIT because it includes Eric Lengyel's official MIT Transvoxel backend.
See `WORLD_TRANSVOXEL_LICENSE_SCOPE.md`, `LICENSES/MIT-Transvoxel.txt`, and
`addons/world_transvoxel/LICENSE_SCOPE.md`.
