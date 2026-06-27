# S1/S2 Completion Checklist

This checklist answers one question: can the project logically move to S3, or
did S1/S2 skip required terrain validation?

Verdict: S1 and S2 are complete for their defined technical scope. The project
may proceed to an S3 contract for visibility/frustum behavior and production
workload. This verdict does not mean the terrain is game-complete.

## Scope boundary

S1 and S2 are sandbox validation milestones:

- S1: accepted LOD0 playtest behavior, visual correctness gates, edit feel,
  restart persistence, and dynamic mixed-LOD default-policy decision.
- S2: chunked generation and scale-ladder evidence through L4 / 2048.

S1/S2 do not require GPU compute, water/lava, planets, structural collapse,
fast travel, target-hardware gameplay workload, real art-direction textures, a
game repository, or 0BSD backend replacement.

## S1 checklist

| Requirement | Status | Evidence |
| --- | --- | --- |
| Accepted default playtest mode is defined | Complete | `docs/S1_DYNAMIC_LOD_POLICY.md`; fixed-center LOD0, `radius_chunks = 4`, `maximum_lod = 0`, `streaming_follows_viewer = false` |
| Normal scene keeps dynamic mixed LOD out of default gameplay | Complete | `tests/terrain_s1_default_policy_audit.gd`; `WT_SANDBOX_S1_DEFAULT_POLICY_PASS` |
| Dynamic mixed LOD is not falsely promoted | Complete | S1.10 policy keeps it diagnostic-only; unresolved seamlessness remains visible |
| Conservative LOD0 workload budget exists | Complete | `docs/S1_LOD0_WORKLOAD_BASELINE.md` |
| LOD0 workload gate passes | Complete | `tools/s1_lod0_workload_audit.py`; `WT_SANDBOX_S1_LOD0_WORKLOAD_AUDIT_PASS` |
| Mining/edit latency is gated | Complete | S1.9 native batched exact-restore path; 2,000 ms gate |
| Exact restore uses native batched capture path | Complete | `scripts/terrain_sculpt_capture.gd`; native `request_authoritative_samples` path |
| Accepted LOD0 visual gallery exists | Complete | `tools/s1_lod0_gallery_audit.py`; nine 1280 x 720 captures |
| Gallery rejects blank/flat/wrong-size images | Complete | `tools/s1_lod0_gallery_audit.py`; image metrics in `artifacts/s1_lod0_gallery/gallery_report.json` |
| Boundary render/collision agreement is checked | Complete | `WT_SANDBOX_BOUNDARY_PROBE` required by S1.11 |
| Restart persistence is checked | Complete | `tests/terrain_s1_lod0_persistence_audit.gd`; `WT_SANDBOX_S1_LOD0_PERSISTENCE_PASS` |
| Autonomous tests disable player input | Complete | S1 audits set `input_enabled` false before scene entry |
| Human review is separated from technical gates | Complete | `docs/TERRAIN_ACCEPTANCE_STANDARD.md`; final qualitative confirmation remains external |

S1 technical exit: complete by S1.11.

## S2 checklist

| Requirement | Status | Evidence |
| --- | --- | --- |
| Scale ladder levels are defined | Complete | `docs/TERRAIN_ACCEPTANCE_STANDARD.md`; L1 256, L2 512, L3 1024, L4 2048 |
| Runtime budgets are declared before acceptance | Complete | `docs/TERRAIN_RUNTIME_BUDGETS.md`; `WT_SANDBOX_RUNTIME_BUDGETS_PASS` |
| L1 generation/runtime/visual evidence exists | Complete | `artifacts/scale_ladder/L1/*_report.json`; S2 exit review validates it |
| L2 generation/runtime/visual evidence exists | Complete | `artifacts/scale_ladder/L2/*_report.json`; S2 exit review validates it |
| L2 active-capacity problem is classified | Complete | `docs/TERRAIN_RUNTIME_BUDGETS.md`; L2 requires active capacity 1024 |
| L3 generation/runtime/visual evidence exists | Complete | `artifacts/scale_ladder/L3/*_report.json`; S2 exit review validates it |
| L3 finite-boundary defect was fixed and guarded | Complete | `WT_SANDBOX_L3_BOUNDARY_PASS`; three-sample finite shell |
| L4 bounded generation preflight exists | Complete | `artifacts/scale_ladder/L4/scale_ladder_report.json`; bounded mode and memory reserve |
| L4 runtime and static visual evidence exists | Complete | `WT_SANDBOX_L4_RUNTIME_PASS`; `WT_SANDBOX_L4_VISUAL_CAPTURE_PASS` |
| L4 shader instance-variable budget blocker is resolved | Complete | 1.0.11-dev default-off shader fade parameters; `WT_SANDBOX_SCALE_VISUAL_PASS level=L4` |
| S2 has a single exit review | Complete | `tools/s2_exit_review.py`; `WT_SANDBOX_S2_EXIT_REVIEW_PASS` |

S2 automated exit: complete by `WT_SANDBOX_S2_EXIT_REVIEW_PASS`.

## Intentionally not complete in S1/S2

These are not skipped S1/S2 work. They are later milestones or external
confirmation:

- final human qualitative confirmation;
- dynamic seamless mixed-LOD gameplay;
- fast travel or disjoint teleport support;
- target-hardware gameplay workload;
- GPU compute acceleration;
- water/lava/fluid simulation;
- planets or alternate gravity worlds;
- structural collapse/stability simulation;
- real texture-array/triplanar art direction;
- small-game repository;
- 0BSD backend replacement.

## Go/no-go decision

Go to S3 contract: yes.

S3 must begin by defining its own scope and gates for visibility/frustum
behavior and production workload. It must not quietly absorb GPU compute,
fluids, planets, structural collapse, or game-repository work.
