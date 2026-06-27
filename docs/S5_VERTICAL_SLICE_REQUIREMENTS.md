# S5 Vertical Slice Requirements

S5 vertical-slice gate: complete.

This document defines the smallest representative game loop that future work
may use to validate `world-transvoxel-terrain`. It is a requirements contract,
not a game implementation.

## Target slice

The smallest game vertical slice is a local single-player terrain traversal and
editing loop:

- install `world-transvoxel`;
- install `world-transvoxel-terrain`;
- create one terrain scene/resource through addon APIs, not by copying the
  sandbox;
- load a 2048 x 2048 x 64 terrain profile derived from the S3 L4 evidence;
- spawn a controllable player/camera;
- explore surface and underground paths;
- perform carve, construct/fill, paint, and explicit restore-to-base operations;
- persist edits and verify restart recovery;
- expose lightweight terrain debug/status UI;
- keep fast travel as loading-screen semantics unless later evidence changes it.

## Backend and implementation requirements

- Use the official MIT-backed World Transvoxel backend first.
- Keep deterministic CPU/headless fallback available.
- Keep compute rejected for now by S4 unless later measured evidence reopens it.
- Keep performance-sensitive work in native code, shaders when justified,
  binary formats, or offline Python tooling.
- Use GDScript only for scaffolding, editor/game UI, input routing, and test
  harnesses.

## Optional systems

The slice does not require these systems:

- water or lava;
- planetary terrain or alternate gravity;
- structural collapse/stability;
- inventory or item economy;
- advanced mining effects/animations;
- independent 0BSD backend replacement.

Each optional system must get a separate contract before implementation.

## Repository boundary

The future game repository must import `world-transvoxel` and
`world-transvoxel-terrain`. It must not fork, copy, or validate
`world-transvoxel-sandbox` as terrain architecture.

`world-transvoxel-sandbox` remains the evidence sandbox for `world-transvoxel`.
`world-transvoxel-terrain` is the missing reusable terrain addon that must be
designed before a game repository can validate terrain in gameplay.

## Acceptance before game repo

Do not create the future game repository until `world-transvoxel-terrain` has a
minimal addon shape that can satisfy this vertical slice without asking the
game to copy sandbox internals.
