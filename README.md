# World Transvoxel Sandbox

Visual, gameplay, and scale validation for the qualified World Transvoxel
1.0.9 MIT-backed addon. This repository is deliberately a sandbox before it
becomes a game.

World Transvoxel 1.0.0 is rejected and withdrawn. This sandbox exposed its
incorrect Godot render/collision winding, incomplete convex mixed-LOD corner
deformation, and inadequate one-chunk acceptance tests. Version 1.0.1 is also
superseded because moving-viewer LOD changes could remove old chunks before
their replacements were applied. Version 1.0.3 is superseded because dynamic
mixed-LOD movement could retire a large ready replacement set in one frame.
Version 1.0.5 adds a bounded native render fade-out for retiring chunks after
replacement application. Version 1.0.6 also fades newly introduced render
chunks through a bounded native window. Version 1.0.9 is the current sandbox
baseline and exposes the native `wt_fade_opacity` shader parameter, but this
reference terrain material remains opaque because transparent alpha blending
created worse patch/sorting artifacts in surface mode.

The vendored addon is the exact Windows x86-64 release from
`world-transvoxel` commit `c0ef66b77a40c2c0891e8b063109eb111cd47457`. Its
mixed 0BSD/MIT scope and release manifest are retained at the repository root.

Dynamic mixed-LOD streaming now passes the automated six-anchor surface
temporal gross-pop gate in both the primary view and the three-camera
multi-view harness. The reference dynamic LOD policy is native fade-in/fade-out
plus `render_apply_budget = 1` to avoid large visual bursts. Human visual
acceptance is still open, so the normal human playtest uses a fixed, complete
LOD0 map and must not be presented as proof that dynamic LOD appearance is
finished.

The project is standards-first. Larger terrain without artifacts, holes,
upside-down behavior, uncontrolled background work, or unexplained visual
popping comes before GPU acceleration, water/lava, planets, structural
collapse, or a small-game repository. The current acceptance standard is
recorded in
[`docs/TERRAIN_ACCEPTANCE_STANDARD.md`](docs/TERRAIN_ACCEPTANCE_STANDARD.md).
The current active milestone and next finite task are tracked in
[`docs/CURRENT_STATUS.md`](docs/CURRENT_STATUS.md).

Automated L4 / 2048 terrain evidence now exists for bounded generation,
staged runtime, edit/remesh, and static visual capture. Human visual acceptance,
dynamic seamless LOD movement, fast travel, and game-scale feature systems are
still separate unfinished gates.

## Run

Python 3.11 or newer is required for generation. Godot 4.6.3 or 4.7 is the
qualified engine matrix.

```console
python tools/validate_sandbox.py
python tools/generate_world.py --force
python tools/test_sandbox.py
python tools/capture_visuals.py
```

Scale-ladder artifacts are generated separately from the accepted L0 playtest
world:

```console
python tools/scale_ladder.py --level L1 --force
python tools/scale_runtime.py --level L1
python tools/scale_visual.py --level L1
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
- Shift + left mouse: construct solid terrain with rock material 3;
- Ctrl + left mouse: paint an ore material;
- `Ctrl+Z`: exactly restore the last committed carve at its original brush
  position; construction invalidates older carve snapshots;
- `F1`: normal/material/LOD shader view;
- `F2`: chunk-boundary overlay;
- `F3`: physics collision debug;
- `F4`: metrics/help overlay.

## Current validation scope

The initial generated world is 128 x 64 x 128 cells with 256 LOD0 pages and
32 LOD1 pages. A deterministic height function establishes only the outside
surface baseline. The baked world remains a dense 3D scalar volume: procedural
caves, a guaranteed underground chamber, a winding tunnel, XYZ-selected rock
geology, and a 3D ore vein alter its interior. The generation audit rejects a
terrain preset unless it contains solid-to-void-to-solid-to-air columns, which
a height field cannot represent. `+Y` is up. Black beyond the terrain is
outside the finite closed map, and orange terrain patches are ore. The optional
orange wire box toggled by F2 is the map boundary.

Carving and construction are intentionally different operations. Carving
changes density without erasing the existing material. Before committing a
carve, the sandbox captures every affected authoritative grid sample in bounded
batches. `Ctrl+Z` restores those exact float32 values with point-sized density
commands, so it does not raycast a new brush position or rely on numerically
inexact `+strength/-strength` cancellation. Shift+LMB instead constructs new
solid density and explicitly paints rock material 3; it is not undo. The carve
restoration stack is session-local; both carvings and committed restorations
still persist through the addon's edit journal.

Terrain recovery is governed by
[`docs/TERRAIN_RECOVERY_CONTRACT.md`](docs/TERRAIN_RECOVERY_CONTRACT.md).
The current default is `manual_exact_restore`: no automatic timed
regeneration, smoothing, structural collapse, or water/lava equilibrium runs
unless an explicit future module enables it. The idle audit verifies this
default remains zero-idle-work.

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
and remesh; restoration must recover the exact density and original mesh hash;
construction must assign rock material 3; an authoritative column audit must
prove solid-void-solid-air volume and XYZ geology; mixed-LOD audits must include
both LODs; every full-world triangle edge must form a closed two-use manifold;
and coincident cross-chunk normals must agree. An idle audit also proves settled
terrain creates no additional viewer updates, sample jobs, mesh jobs, mesh
completions, or publications,
that camera movement does not alter the fixed reference anchor, and that the
dynamic test mode honors the eight-unit streaming threshold.
Continuous motion checks 480 viewer positions, direct render coverage, and
2,400 collision probes while confirming staged replacement resources return
to zero after motion settles.
Nine deterministic captures cover surface, material, LOD, top, unshadowed
top, top LOD, a lit underground tunnel inspection, and surface/material views
of the closed boundary. Capture contrast is measured outside the overlay, so a
blank terrain viewport cannot pass from UI contrast alone. Human review is for
appearance and game feel, not for proving Transvoxel topology.

This does not yet prove a 2K map, GPU compute, water, lava, planetary terrain,
or structural stability. Those gates are finite and recorded in
[`docs/ROADMAP.md`](docs/ROADMAP.md).

## License

Sandbox-owned code is 0BSD. The vendored World Transvoxel addon is mixed
0BSD/MIT because it includes Eric Lengyel's official MIT Transvoxel backend.
See `WORLD_TRANSVOXEL_LICENSE_SCOPE.md`, `LICENSES/MIT-Transvoxel.txt`, and
`addons/world_transvoxel/LICENSE_SCOPE.md`.
