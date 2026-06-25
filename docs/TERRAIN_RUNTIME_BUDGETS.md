# Terrain Runtime Budgets

Runtime budgets are part of terrain correctness. A scale level is not accepted
just because generation succeeds or because a smaller-level configuration
happens to work.

This document exists because L2 exposed a real budget boundary: 512-wide
terrain can replace most of a roughly 294 chunk active set during staged
movement, and the old 512 active/change capacity can reject that delta.

## Rule

Every accepted runtime scale must declare its budget profile before it is used
for visual capture, larger scale work, or gameplay reference work.

The profile must include:

- horizontal scale level;
- movement class covered by the audit;
- `radius_chunks`;
- `maximum_lod`;
- `active_chunk_capacity`;
- `render_apply_budget`;
- inherited cache budgets or explicit cache overrides;
- minimum observed render/collision coverage;
- what movement is not proven by the profile.

Changing a budget is not a hidden fix. The changed value must be in the audit
marker, the runtime report, and this document.

## Accepted and provisional profiles

| Level | Horizontal cells | Movement class | Radius | Max LOD | Active capacity | Render apply | Min render/collision | Status |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| L0 | 128 | fixed-center LOD0 reference | 4 | 0 | 512 | 1 | full reference world | accepted baseline |
| L1 | 256 | staged movement | 3 | 1 | 512 | 1 | 97 / 97 | accepted runtime |
| L2 | 512 | staged movement | 3 | 1 | 1024 | 1 | 176 / 176 | accepted runtime |
| L3 | 1024 | staged movement | 3 | 1 | 1024 | 1 | 201 / 201 | accepted runtime |
| L4 | 2048 | staged movement | 3 | 1 | 1024 | 1 | 210 / 195 | accepted runtime |

## L2 capacity classification

The failed L2 default-budget audit is classified as a runtime budget boundary,
not a terrain topology proof and not a visual acceptance result.

Facts:

- L2 generation passed with 4,608 pages.
- L2 default active capacity 512 rejected staged movement during runtime.
- The rejected movement involved a large replacement of the active set.
- L2 passed on Godot 4.6.3 and 4.7 with active chunk capacity 1,024.

Therefore L2 is accepted only under the explicit L2 runtime budget. We do not
pretend the old L0/L1 default budget is sufficient.

## Movement classes

`fixed-center LOD0 reference` means the stable inspection scene loads the
accepted area without dynamic mixed-LOD movement.

`staged movement` means the viewer moves between planned positions and waits
for terrain resources to settle at each stage.

`fast travel` means large disjoint camera/player relocation, teleporting,
loading after travel, or rapid flight that can invalidate most of the active
set in one operation. Fast travel is not proven by L2 runtime acceptance.

Fast travel must get a separate policy before it can be called supported. Valid
solutions may include a larger delta budget, progressive catch-up, a streaming
reset path, loading screen semantics, or a dedicated teleport API.

## L3 derivation and acceptance

L3 keeps radius 3 and maximum LOD 1. Horizontal world extent increases page
storage but does not increase the local planner window for those settings.

The L2 visual/runtime evidence observed an active set up to roughly 308 chunks.
A conservative full replacement bound is therefore 616 records. Active chunk
capacity 1,024 leaves 408 records above that bound.

L3 inherits storage, encoded/decoded page, mesh, render, collision, byte, and
apply budgets from `config/terrain_config.tres`. The accepted visual/runtime
default is `render_apply_budget = 1`; this intentionally spreads dynamic
surface replacement over more frames. Its only scale-specific override is
`active_chunk_capacity = 1024`, matching the derived local replacement bound
rather than copying world size.

The profile passed Godot 4.6.3 and 4.7 with seven staged positions, 35
render/collision probes, minimum 201 render/collision chunks, one active-window
edit/remesh, and clean shutdown. It is accepted for staged movement only. It
does not prove fast travel, disjoint teleport movement, visual acceptance, or
L4 support.

## L4 derivation and acceptance

L4 keeps radius 3 and maximum LOD 1. The world storage is much larger, but the
local planner window remains bounded by the same runtime budget knobs.

L4 therefore uses the same active chunk capacity as L3: 1,024 records and the
same accepted render-apply budget: 1 chunk per frame. These are not inherited
silently; they are locked because the L4 audit passed with those explicit
budgets.

The profile passed Godot 4.6.3 and 4.7 with seven staged positions, 35
render/collision probes, minimum render/collision coverage 210 / 195, one
active-window edit/remesh, and clean shutdown. It is accepted for staged
movement only. It
does not prove fast travel, disjoint teleport movement, final human qualitative
confirmation, dynamic seamless LOD appearance, or support beyond L4.
