# S1.11 Accepted LOD0 Gallery and Persistence Audit

This document defines the S1 accepted fixed-center LOD0 gallery gate. It covers
the normal playtest path only:

| Field | Value |
| --- | --- |
| Scene | `scenes/terrain_lab.tscn` |
| Movement class | fixed-center LOD0 reference |
| `radius_chunks` | `4` |
| `maximum_lod` | `0` |
| `streaming_follows_viewer` | `false` |
| Visual runner | `tools/s1_lod0_gallery_audit.py` |
| Persistence script | `tests/terrain_s1_lod0_persistence_audit.gd` |
| Pass marker | `WT_SANDBOX_S1_LOD0_GALLERY_AUDIT_PASS` |

## Hard gates

The audit must:

- launch autonomous captures with player input disabled from scene startup;
- capture nine representative fixed-center LOD0 images under `artifacts/visual`;
- reject missing, undersized, blank, wrong-size, or visually flat captures;
- require Godot 4.7 graphical capture to finish without `ERROR:` or
  `SCRIPT ERROR`;
- require the closed-boundary render/collision ray probe from
  `tests/terrain_visual_capture.gd`;
- run restart persistence on the discovered Godot engines;
- require `WT_SANDBOX_S1_LOD0_PERSISTENCE_PASS` on each persistence run;
- prove the edit journal survives stop/start and restores the edited density and
  rendered mesh identity exactly after restart.

## Accepted S1.11 run

```console
python tools/s1_lod0_gallery_audit.py
```

Accepted marker:

```text
WT_SANDBOX_S1_LOD0_GALLERY_AUDIT_PASS images=9 engines=2 report=artifacts/s1_lod0_gallery/gallery_report.json
```

Persistence markers:

```text
WT_SANDBOX_S1_LOD0_PERSISTENCE_PASS density_delta=8.000 journal_bytes=612 restart=exact mesh=stable
```

The report classifies the accepted-gallery artifact state:

- blank or missing viewport: not detected;
- missing backsides or boundary holes: not detected by the closed-boundary
  render/collision ray probe;
- render/collision runtime gap: not detected by the boundary probe;
- upside-down terrain: not detected by top and overview capture orientation;
- LOD debug partitioning: expected only in `overview_lod` and `top_lod`;
- dynamic LOD popping: out of scope for accepted default play, because dynamic
  mixed LOD remains diagnostic-only by S1.10;
- final human qualitative confirmation: still pending.

## What this closes

S1.11 closes the automated technical evidence gap for the accepted fixed-center
LOD0 gallery and restart persistence. Together with S1.9 mining latency and
S1.10 dynamic-LOD default demotion, the S1 technical exit criteria are now
covered by explicit gates.

## What this does not prove

This audit does not prove final human qualitative approval, real texture-array
or triplanar art direction, dynamic mixed-LOD seamless gameplay, GPU compute,
water/lava, planets, structural collapse, or full game readiness.
