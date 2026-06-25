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

S1 - visual acceptance and dynamic mixed-LOD quality.

S0 is complete for the 128 baseline. S2 automated scale-ladder evidence is
complete through L4 / 2048 for bounded generation, staged runtime,
edit/remesh, and static visual capture. S1 still has a visual gate: dynamic
mixed-LOD now passes the automated six-anchor single-view and three-view
surface temporal gross-pop and region-bounds gates, but it is not accepted as a
default seamless
play mode until human visual review accepts the result or the standard is
explicitly changed. We are not starting GPU compute, water/lava, planets,
structural collapse, a game repository, or 0BSD backend replacement work before
the visual-quality blocker is resolved or explicitly demoted by standard.

## Latest evidence

S1.6 - dynamic LOD visual-burst budget plus multi-view gross-pop and
region-bounds gates are complete.

Commands:

```console
python tools/capture_lod_popping.py
python tools/capture_lod_surface.py
python tools/capture_lod_temporal.py
python tools/capture_lod_temporal_multiview.py
python tools/review_lod_temporal.py
```

Result:

- vendored addon: World Transvoxel 1.0.9 from upstream commit
  `c0ef66b77a40c2c0891e8b063109eb111cd47457`;
- `render_apply_budget = 1` is now the locked reference runtime/visual policy
  for dynamic mixed-LOD captures; budget 2 passed the single-view temporal gate
  but still failed the multi-view gate, and budget 1 passed both without
  loosening thresholds;
- the sandbox terrain material remains opaque. World Transvoxel 1.0.9 exposes
  native `wt_fade_opacity`, but consuming it as transparent alpha in this
  terrain material created worse patch/sorting artifacts and is not the
  accepted surface-mode policy;
- diagnostic mode: fixed camera, LOD-color debug view, autonomous input
  disabled, and native terrain demand anchor moved independently of camera
  motion;
- anchors: 6;
- replacement frames observed: 140;
- saved diagnostic captures: 12 under `artifacts/dynamic_lod`;
- report: `artifacts/dynamic_lod/dynamic_lod_report.json`;
- maximum staged retirements: 92;
- maximum render-set delta in one observed frame: 7;
- maximum native fading resources: 59;
- fade frames observed: 295;
- maximum queued render/collision backlog: 0 / 0;
- center render/collision probe stayed present during replacements;
- classification:
  `lod_transition_native_fade_without_geomorph_pending_visual_acceptance`;
- comparison against S1.1 baseline: improved from 61 to 7 maximum one-frame
  render-set delta; S1.2 previously observed 79 replacement frames with the
  same render-set delta, S1.3 proved native fade-out activity, S1.5 proved
  native fade-in/fade-out activity, and S1.6 locks a one-chunk render-apply
  budget plus multi-view temporal measurement;
- proven: retirement smoothing and native render fade-in/fade-out are active,
  bounded, keep queues/probes stable, and stay under the automated gross-pop
  and region-bounds thresholds in the deterministic single-view and multi-view
  captures;
- not proven: seamless dynamic LOD appearance, human visual acceptance, all
  camera angles, all movement speeds, or geomorphing.

Surface-mode still evidence:

- replacement frames observed: 140;
- saved surface captures: 12 under `artifacts/dynamic_lod_surface`;
- report: `artifacts/dynamic_lod_surface/dynamic_lod_surface_report.json`;
- maximum render-set delta in one observed frame: 7;
- maximum native fading resources: 59;
- fade frames observed: 294;
- classification: `surface_transition_pending_visual_acceptance`;
- AI pre-review of the generated still-image contact sheet found stable terrain
  massing across the baseline and transition captures, with no hard hole,
  missing backside, upside-down terrain, diagonal ridge, or full chunk
  disappearance visible in the inspected surface stills;
- not proven: temporal seamlessness. Still images do not replace video/human
  review for accepting the default dynamic LOD policy.

Single-view temporal surface evidence:

- frames captured: 540 under `artifacts/dynamic_lod_temporal`;
- preview: `artifacts/dynamic_lod_temporal/temporal_preview.gif`;
- top-change review sheet:
  `artifacts/dynamic_lod_temporal/temporal_top_change_pairs_review.png`;
- per-anchor transition review sheet:
  `artifacts/dynamic_lod_temporal/temporal_anchor_transition_review.png`;
- report: `artifacts/dynamic_lod_temporal/dynamic_lod_temporal_report.json`;
- maximum render-set delta: 8;
- maximum native fading resources: 59;
- fade frames observed: 164;
- maximum visible changed ratio between adjacent frames: 0.002314;
- maximum mean RGB delta between adjacent frames: 0.000471;
- maximum visible changed pixels between adjacent frames: 1,301;
- maximum changed bounding-box visible ratio between adjacent frames: 0.034371;
- maximum-change pair: `anchor_00_frame_049.png` to
  `anchor_00_frame_050.png`;
- gross-pop gate: passed across six anchors against visible-ratio limit 0.005
  and mean-RGB limit 0.002;
- region-bounds gate: passed across six anchors against changed-pixel limit
  4,096 and changed bounding-box visible-ratio limit 0.20;
- classification:
  `temporal_surface_gross_pop_gate_pass_pending_human_review`;
- proven: these deterministic surface transitions do not produce a large
  measured frame-to-frame image swap under the automated gross-pop and
  region-bounds gates;
- AI visual pre-review of the generated review sheets found localized
  silhouette/edge changes only, with no hard hole, missing backside,
  upside-down terrain, or full chunk disappearance visible in the worst
  measured pairs;
- not proven: human visual acceptance, all camera angles, all movement speeds,
  or geomorphing.

Multi-view temporal surface evidence:

- views: front, side, and diagonal;
- frames captured: 1,080 under `artifacts/dynamic_lod_temporal_multiview`;
- preview:
  `artifacts/dynamic_lod_temporal_multiview/temporal_multiview_preview.gif`;
- top-change review sheet:
  `artifacts/dynamic_lod_temporal_multiview/temporal_multiview_top_change_pairs_review.png`;
- report:
  `artifacts/dynamic_lod_temporal_multiview/dynamic_lod_temporal_multiview_report.json`;
- maximum render-set delta: 8;
- maximum native fading resources: 59;
- fade frames observed: 490;
- maximum visible changed ratio between adjacent frames: 0.004534;
- maximum mean RGB delta between adjacent frames: 0.000845;
- maximum visible changed pixels between adjacent frames: 2,381;
- maximum changed bounding-box visible ratio between adjacent frames: 0.150831;
- maximum-change pair:
  `view_02_diagonal_anchor_02_frame_041.png` to
  `view_02_diagonal_anchor_02_frame_042.png`;
- gross-pop gate: passed across three views and six anchors against
  visible-ratio limit 0.005 and mean-RGB limit 0.002;
- region-bounds gate: passed across three views and six anchors against
  changed-pixel limit 4,096 and changed bounding-box visible-ratio limit 0.20;
- classification:
  `temporal_multiview_gross_pop_gate_pass_pending_human_review`;
- AI visual pre-review of the generated multi-view top-change sheet found
  localized silhouette/edge changes only, with no hard hole, missing backside,
  upside-down terrain, or full chunk disappearance visible in the worst measured
  pairs;
- not proven: human visual acceptance, all camera angles, all movement speeds,
  or geomorphing.

Post-vendor 1.0.9 verification passed:

```console
python tools/validate_sandbox.py
python -m py_compile tools/capture_lod_temporal.py tools/capture_lod_temporal_multiview.py tools/review_lod_temporal.py tools/test_sandbox.py tools/validate_sandbox.py tools/runtime_budget_profiles.py
python tools/test_sandbox.py
python tools/capture_visuals.py
python tools/scale_runtime.py --level L4
```

Result:

- repository validation: `WT_SANDBOX_VALIDATION_PASS vendored_files=147
  project_files=228`;
- sandbox matrix: `WT_SANDBOX_MATRIX_PASS engines=2 configurations=2 tests=7
  cases=28`;
- visual capture: `WT_SANDBOX_VISUAL_EVIDENCE_PASS images=9`;
- L4 runtime: `WT_SANDBOX_SCALE_RUNTIME_PASS level=L4 engines=2`, with
  active chunk capacity 1,024, `render_apply_budget=1`, minimum render 210,
  minimum collision 195, and max pending retirements 0.

S2.13 - L4 bounded generation, runtime, and static visual capture are complete.

Commands:

```console
python tools/scale_ladder.py --level L4 --force
python tools/scale_runtime.py --level L4
python tools/scale_visual.py --level L4
```

Result:

- dimensions: 2,053 x 69 x 2,053 samples;
- source samples: 290,821,821;
- source bytes: 1,744,930,926;
- expected pages: 73,728;
- stable payload bytes: 3,057,795,983;
- generation seconds: 2,651.646;
- volumetric columns: 562,862;
- world hash:
  `0f908b1e36c8c602ca884070c40d360e6a661274135791f13dafab1f48384368`;
- bounded memory contract: streamed Python source estimate 68,160,000 bytes,
  bounded native bake estimate 77,840,384 bytes, and required available memory
  with reserve 614,711,296 bytes;
- direct L4 source/generation remains guarded: it requires scale-ladder
  resource preflight and `--resource-preflight-approved`;
- L4 accepted runtime budget: staged movement, radius 3, maximum LOD 1, active
  chunk capacity 1,024, render-apply budget 1, inherited cache budgets;
- runtime evidence: Godot 4.6.3 and 4.7, seven staged positions, 35
  render/collision probes, latest minimum render/collision coverage 210 / 195,
  one active-window edit/remesh, clean shutdown, and max pending retirements 0;
- visual evidence: seven Godot 4.7 captures under
  `artifacts/scale_ladder/L4/visual`, all nonblank, covering overview,
  material, LOD, top, underground tunnel, closed boundary, and boundary
  materials;
- permanent boundary regression: an outside-in collision ray at y=12, z=1024
  must hit the finite wall at x=0.500 before any internal geometry;
- proven: L4 bounded generation, storage validation, Godot startup, staged
  movement render/collision coverage, one edit/remesh, clean shutdown, and
  static visual capture;
- not proven: human visual acceptance, dynamic seamless LOD appearance, fast
  travel/disjoint teleport movement, target-hardware gameplay workload,
  water/lava, planets, structural collapse, or scale beyond L4.

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

S1.7 - default dynamic LOD policy or native mitigation decision.

Scope:

- treat S1.6 as stronger automated evidence, not default seamless acceptance:
  the one-chunk budget, gross-pop gate, and region-bounds gate pass, but human
  visual acceptance and geomorphing remain not proven;
- choose the bounded next policy before broad gameplay work resumes:
  documented conservative LOD0/fixed-center default for normal playtest/game
  paths, or a native mixed-LOD mitigation such as geomorphing, stronger
  hysteresis, or larger prefetch rings;
- keep the single-view and multi-view capture harnesses as regression metrics
  and preserve the S1.1/S1.2/S1.3/S1.5/S1.6 comparison;
- keep GDScript limited to diagnostic capture/scaffolding.

Exit:

- the accepted default playtest/game policy is documented in
  `docs/TERRAIN_ACCEPTANCE_STANDARD.md` and reflected by the sandbox defaults,
  or the next native mixed-LOD mitigation is implemented and rerun through the
  S1.6 single-view and multi-view gates;
- no compute, water/lava, planets, structural stability, or game-repository work
  starts before this boundary is closed.

## Next finite steps

1. Choose and apply the conservative default policy unless mixed LOD is visually
   accepted: normal playtest/game paths use LOD0/fixed-center, while dynamic
   mixed LOD remains diagnostic/experimental.
2. If conservative default is rejected, implement one native mitigation
   candidate before any feature expansion: geomorphing, stronger hysteresis, or
   larger prefetch rings.
3. Rerun the single-view and multi-view temporal gates after any default-policy
   or mitigation change.

## Deferred by rule

- compute shaders;
- water and lava;
- planetary terrain;
- structural collapse;
- timed regeneration;
- small-game repository;
- independent 0BSD backend replacement.
