# S1.10 Dynamic Mixed-LOD Default Policy

Decision date: June 26, 2026.

S1.10 rejects dynamic mixed LOD as the default accepted playtest policy for the
current sandbox. It remains available only as an explicit diagnostic mode. The
accepted S1 playtest path is fixed-center LOD0 reference mode:

| Setting | Accepted value |
| --- | --- |
| `radius_chunks` | `4` |
| `maximum_lod` | `0` |
| `streaming_follows_viewer` | `false` |
| `fixed_streaming_position` | `(64, 32, 64)` |
| `render_apply_budget` | `1` |
| `run/max_fps` | `60` |

## Why dynamic mixed LOD is not the default

The S1.6 evidence proves that native fade-in/fade-out and a one-chunk render
apply budget keep deterministic dynamic transitions bounded under the current
automated gross-pop and region-bounds gates. That is useful diagnostic evidence,
but it does not prove all camera angles, all movement speeds, perceptual
seamlessness, or geomorph-quality transitions.

The user-visible popping/glitching concern is therefore treated as a real S1
visual-quality blocker for dynamic mixed LOD, not as normal terrain behavior.
The stable accepted mode must not require players or reviewers to tolerate that
experimental path.

## Allowed diagnostic use

Diagnostic scripts and scale/runtime audits may explicitly set `maximum_lod = 1`
or `streaming_follows_viewer = true` when the test name, output marker, or
documentation makes clear that mixed LOD is being inspected. These paths must
not be described as proving default seamless dynamic LOD.

The overlay must continue to label mixed-LOD modes as diagnostic. The normal
scene, fallback script defaults, and accepted playtest documentation must keep
the fixed LOD0 reference values above.

## Reopening the default decision

Dynamic mixed LOD may be reconsidered as a default only after a new S1 or later
milestone explicitly replaces this policy with stronger evidence. At minimum,
that evidence must cover:

- surface-mode temporal transition captures, not only LOD debug stills;
- multiple camera angles and representative movement speeds;
- render and collision coverage during movement;
- bounded queue, retirement, and frame-time behavior;
- no hard holes, missing backsides, upside-down terrain, broad swaps, or
  unexplained popping;
- a documented native mitigation if fade-only transitions are still visibly
  insufficient.

Human review remains final qualitative confirmation, but it does not replace
the technical gates above.

## Enforcement

`tests/terrain_s1_default_policy_audit.gd` is the runtime gate for the accepted
default path. It instantiates the normal scene with autonomous input disabled,
verifies the fixed LOD0 defaults, waits for the full LOD0 reference world to
settle, confirms all rendered chunks are LOD0, moves the viewer, and verifies
that the fixed streaming anchor and viewer demand do not change.

`tools/validate_sandbox.py` also checks the policy document, scene defaults,
script fallback defaults, overlay diagnostic labels, and test matrix entry.
