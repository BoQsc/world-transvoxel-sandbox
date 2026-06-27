# S3 Exit Review

S3 status: complete after `tools/s3_exit_review.py` reports
`WT_SANDBOX_S3_EXIT_REVIEW_PASS`.

S3 exits only for the sandbox visibility and production-workload scope defined
by `docs/S3_VISIBILITY_PRODUCTION_WORKLOAD_CONTRACT.md`. This does not start or
complete S4/S5 work.

## Required evidence

| Gate | Evidence |
| --- | --- |
| Visibility/frustum workload | `tools/s3_visibility_workload.py`; `WT_SANDBOX_S3_VISIBILITY_WORKLOAD_AUDIT_PASS` |
| Forward prefetch policy | `docs/S3_FORWARD_PREFETCH_POLICY.md`; secondary viewer `603`, distance `64`, radius `1` |
| Fast travel policy | loading-screen required; seamless disjoint teleport not accepted |
| Restore-to-base | `tools/s3_restore_to_base_audit.py`; `WT_SANDBOX_S3_RESTORE_TO_BASE_AUDIT_PASS` |
| Visual/GPU artifact gate | `tools/s3_visual_gpu_audit.py`; `WT_SANDBOX_S3_VISUAL_GPU_AUDIT_PASS` |
| Exit review | `tools/s3_exit_review.py`; `WT_SANDBOX_S3_EXIT_REVIEW_PASS` |

## Exit decision

S3 passes because:

- the L4 visibility/frustum workload passes declared headless budgets on the
  Godot 4.6.3 and 4.7 engine matrix;
- rapid camera turns change frustum visibility without changing terrain demand;
- forward-biased prefetch is bounded and keeps the primary viewer as the
  all-direction safety ring;
- repeated mining while moving remains under edit-latency and journal-growth
  budgets;
- explicit `restore_to_base` restores audited edited samples to deterministic
  generated density/material;
- graphical capture acceptance passes representative stable, movement,
  rapid-turn, underground, pre-edit, and post-edit views without queued/fading
  resources at capture points.

## Claim boundary

S3 proves the sandbox terrain can survive the declared L4 representative
visibility, movement, edit, restore, and graphical capture workload. It does
not prove:

- GPU compute acceleration;
- water, lava, planets, or structural stability;
- future game repository readiness;
- 0BSD backend replacement;
- final human aesthetic acceptance or final texture/art production.

Next valid action after S3 is S4 decision work: choose one measured bottleneck
for targeted acceleration, or close S4 with the CPU/native path if no compute
rewrite is justified. Broad GPU implementation must not start from S3 exit
alone.
