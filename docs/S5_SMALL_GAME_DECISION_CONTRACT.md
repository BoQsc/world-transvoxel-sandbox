# S5 Small-Game Decision Contract

S5 starts only after S3 production workload evidence and the S4 compute decision
are recorded.

S5 decides whether the terrain reference is ready to support a small game, needs
architecture revision, or should stop with a documented reason.

## In scope

- Apply `docs/REPOSITORY_BOUNDARY_CONTRACT.md`.
- Define the smallest representative game vertical slice.
- Use the official MIT-backed World Transvoxel backend first.
- Validate gameplay loop requirements against the S3/S4 evidence.
- Decide which optional systems are required for the vertical slice.
- Require separate contracts before adding fluids, structural stability,
  planetary terrain, inventory, or complex mining effects.
- Decide whether to create or defer a separate game repository. If created, the
  future game repository validates world-transvoxel-terrain and imports
  `world-transvoxel` plus `world-transvoxel-terrain`.
- Decide whether the 0BSD backend replacement effort should reopen after the
  official backend survives the vertical slice.

## Out of scope

- Starting a game before the terrain reference has a passing production
  workload.
- Using `world-transvoxel-sandbox` to test `world-transvoxel-terrain`.
- Asking a game project to fork or copy the sandbox as terrain architecture.
- Mixing optional systems into terrain core without contracts.
- Reopening 0BSD backend replacement before the official backend is
  battle-tested in the vertical slice.

## Required S5 gates

| Gate | Required marker or artifact |
| --- | --- |
| repository boundary contract | `docs/REPOSITORY_BOUNDARY_CONTRACT.md` |
| S5 completion checklist | `docs/S5_COMPLETION_CHECKLIST.md` |
| vertical-slice requirements | documented game loop |
| official-backend integration decision | use/revise/stop |
| optional-system contracts | required before implementation |
| repository decision | same repo, new repo, or defer |
| final decision marker | `WT_SANDBOX_S5_SMALL_GAME_DECISION_PASS` |

## Exit condition

S5 exits with exactly one of these decisions:

- proceed with a small game;
- revise terrain architecture first;
- stop with a documented reason.
