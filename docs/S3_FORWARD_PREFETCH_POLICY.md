# S3 Forward-Biased Prefetch Policy

S3 accepts forward-biased prefetch as a bounded secondary-viewer policy.

## Accepted policy

The primary viewer remains at the real player/camera position with the normal
all-direction safety ring.

Forward prefetch is submitted as a secondary viewer ahead of the latest movement
direction:

| Field | Value |
| --- | --- |
| secondary viewer id | `603` |
| prefetch distance | `64` world cells |
| prefetch radius | `1` chunk |
| maximum LOD | `1` |
| active chunk capacity | `1024` |

This biases loading toward likely near-future movement without removing the
all-direction safety ring around the real viewer.

## Rotation policy

Rapid camera turns must not directly change terrain demand. The prefetch target
is updated by movement submissions, not by look-only camera rotation. The S3
workload keeps `viewer_updates_delta=0` and `planned_demands_delta=0` during the
rapid-turn phase to preserve the separation between Godot frustum visibility and
terrain demand generation.

## Claim boundary

This policy is accepted only for the S3 L4 headless workload baseline. It does
not prove final visual quality, GPU frame time, seamless fast travel, or S3 exit.

Fast travel remains loading-screen required until a separate S3 task proves a
bounded catch-up policy.
