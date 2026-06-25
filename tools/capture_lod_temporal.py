#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

from scale_visual import discover_engine


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "artifacts" / "dynamic_lod_temporal"
SCRIPT = "res://tests/terrain_lod_temporal_capture.gd"
PASS_MARKER = "WT_SANDBOX_LOD_TEMPORAL_CAPTURE_PASS"
FRAME_MARKER = "WT_SANDBOX_LOD_TEMPORAL_FRAME"
MAX_VISIBLE_CHANGED_RATIO = 0.005
MAX_MEAN_RGB_DELTA = 0.002
MAX_VISIBLE_CHANGED_PIXELS = 4096
MAX_CHANGED_BBOX_VISIBLE_RATIO = 0.2
CLASSIFICATION = "temporal_surface_gross_pop_gate_pass_pending_human_review"


def parse_fields(line: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for item in line.split()[1:]:
        if "=" in item:
            key, value = item.split("=", 1)
            fields[key] = value
    return fields


def visible_change_metrics(left: Image.Image, right: Image.Image) -> dict[str, object]:
    left_rgb = left.convert("RGB")
    right_rgb = right.convert("RGB")
    diff = ImageChops.difference(left_rgb, right_rgb)
    mean_delta = sum(ImageStat.Stat(diff).mean) / (3.0 * 255.0)
    diff_gray = diff.convert("L")
    visible = ImageChops.lighter(left_rgb.convert("L"), right_rgb.convert("L")).point(
        lambda value: 255 if value > 8 else 0
    )
    changed = diff_gray.point(lambda value: 255 if value > 8 else 0)
    visible_count = visible.histogram()[255]
    changed_visible = ImageChops.multiply(changed, visible)
    changed_visible_count = changed_visible.histogram()[255]
    bbox = changed_visible.getbbox()
    bbox_pixels = 0
    if bbox is not None:
        bbox_pixels = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
    bbox_record = (
        None
        if bbox is None
        else {
            "x_min": bbox[0],
            "y_min": bbox[1],
            "x_max": bbox[2],
            "y_max": bbox[3],
        }
    )
    if visible_count == 0:
        return {
            "mean_rgb_delta": mean_delta,
            "visible_changed_ratio": 0.0,
            "visible_changed_pixels": 0,
            "changed_bbox_pixels": bbox_pixels,
            "changed_bbox_visible_ratio": 0.0,
            "changed_bbox": bbox_record,
        }
    return {
        "mean_rgb_delta": mean_delta,
        "visible_changed_ratio": changed_visible_count / visible_count,
        "visible_changed_pixels": changed_visible_count,
        "changed_bbox_pixels": bbox_pixels,
        "changed_bbox_visible_ratio": bbox_pixels / visible_count,
        "changed_bbox": bbox_record,
    }


def visible_changed_ratio(left: Image.Image, right: Image.Image) -> tuple[float, float]:
    metrics = visible_change_metrics(left, right)
    return (
        float(metrics["mean_rgb_delta"]),
        float(metrics["visible_changed_ratio"]),
    )


def analyze_images(paths: list[Path]) -> dict[str, object]:
    pairs: list[dict[str, object]] = []
    max_pair: dict[str, object] | None = None
    previous: Image.Image | None = None
    for index, path in enumerate(paths):
        current = Image.open(path)
        if previous is not None:
            metrics = visible_change_metrics(previous, current)
            pair = {
                "from": paths[index - 1].name,
                "to": path.name,
                **metrics,
            }
            pairs.append(pair)
            if (
                max_pair is None or
                pair["visible_changed_ratio"] > max_pair["visible_changed_ratio"]
            ):
                max_pair = pair
        previous = current
    if max_pair is None:
        raise RuntimeError("not enough temporal images to compare")
    return {
        "frame_pairs": pairs,
        "max_visible_changed_ratio": max_pair["visible_changed_ratio"],
        "max_mean_rgb_delta": max(pair["mean_rgb_delta"] for pair in pairs),
        "max_visible_changed_pixels": max(
            pair["visible_changed_pixels"] for pair in pairs
        ),
        "max_changed_bbox_pixels": max(pair["changed_bbox_pixels"] for pair in pairs),
        "max_changed_bbox_visible_ratio": max(
            pair["changed_bbox_visible_ratio"] for pair in pairs
        ),
        "maximum_change_pair": max_pair,
        "maximum_changed_pixels_pair": max(
            pairs,
            key=lambda pair: pair["visible_changed_pixels"],
        ),
        "maximum_changed_bbox_pair": max(
            pairs,
            key=lambda pair: pair["changed_bbox_visible_ratio"],
        ),
    }


def write_preview(paths: list[Path]) -> Path:
    frames: list[Image.Image] = []
    for path in paths[::6]:
        frame = Image.open(path).convert("P", palette=Image.Palette.ADAPTIVE)
        frame = frame.resize((480, 270))
        frames.append(frame)
    output = OUTPUT_ROOT / "temporal_preview.gif"
    frames[0].save(
        output,
        save_all=True,
        append_images=frames[1:],
        duration=50,
        loop=0,
        optimize=True,
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Capture temporal surface-mode dynamic mixed-LOD evidence."
    )
    parser.add_argument("--godot", type=Path)
    arguments = parser.parse_args()
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    engine = discover_engine(arguments.godot)
    result = subprocess.run(
        [
            str(engine),
            "--path",
            str(ROOT),
            "--script",
            SCRIPT,
            "--",
            "--disable-player-input",
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
        errors="replace",
        timeout=600,
    )
    combined = result.stdout + result.stderr
    (OUTPUT_ROOT / "capture.log").write_text(combined, encoding="utf-8")
    print(combined, end="" if combined.endswith("\n") else "\n")
    pass_line = next(
        (line for line in combined.splitlines() if PASS_MARKER in line),
        "",
    )
    frame_lines = [line for line in combined.splitlines() if FRAME_MARKER in line]
    if result.returncode != 0 or not pass_line or len(frame_lines) < 180:
        raise RuntimeError("temporal dynamic LOD capture failed")
    pass_fields = parse_fields(pass_line)
    if int(pass_fields.get("max_render_fading", "0")) <= 0:
        raise RuntimeError("temporal dynamic LOD capture missed native fade")
    images = sorted(OUTPUT_ROOT.glob("anchor_*_frame_*.png"))
    analysis = analyze_images(images)
    if analysis["max_visible_changed_ratio"] > MAX_VISIBLE_CHANGED_RATIO:
        raise RuntimeError("temporal visible changed ratio exceeded gross-pop gate")
    if analysis["max_mean_rgb_delta"] > MAX_MEAN_RGB_DELTA:
        raise RuntimeError("temporal mean RGB delta exceeded gross-pop gate")
    if analysis["max_visible_changed_pixels"] > MAX_VISIBLE_CHANGED_PIXELS:
        raise RuntimeError("temporal changed-pixel count exceeded region gate")
    if analysis["max_changed_bbox_visible_ratio"] > MAX_CHANGED_BBOX_VISIBLE_RATIO:
        raise RuntimeError("temporal changed bounding box exceeded region gate")
    preview = write_preview(images)
    report = {
        "schema": "world-transvoxel-sandbox.dynamic-lod-temporal-evidence.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "engine": str(engine),
        "status": "classified",
        "classification": CLASSIFICATION,
        "gross_pop_gate": {
            "max_mean_rgb_delta": MAX_MEAN_RGB_DELTA,
            "max_visible_changed_ratio": MAX_VISIBLE_CHANGED_RATIO,
            "passed": True,
        },
        "region_bounds_gate": {
            "max_changed_bbox_visible_ratio": MAX_CHANGED_BBOX_VISIBLE_RATIO,
            "max_visible_changed_pixels": MAX_VISIBLE_CHANGED_PIXELS,
            "passed": True,
        },
        "raw_capture_classification": pass_fields["classification"],
        "summary": pass_fields,
        "frames": [parse_fields(line) for line in frame_lines],
        "image_analysis": analysis,
        "image_count": len(images),
        "output": OUTPUT_ROOT.relative_to(ROOT).as_posix(),
        "preview": preview.relative_to(ROOT).as_posix(),
        "proven": [
            "surface-mode transition frame sequence was captured",
            "native render retirement fade was active during the sequence",
            "frame-to-frame visible image deltas were measured",
            "automated gross-pop threshold passed for this deterministic view",
            "automated region-bounds threshold passed for this deterministic view",
        ],
        "not_proven": [
            "human visual acceptance",
            "seamless dynamic LOD appearance",
            "geomorphing",
        ],
    }
    report_path = OUTPUT_ROOT / "dynamic_lod_temporal_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        "WT_SANDBOX_DYNAMIC_LOD_TEMPORAL_PASS "
        f"frames={len(images)} "
        f"max_render_fading={pass_fields['max_render_fading']} "
        f"max_visible_changed_ratio={analysis['max_visible_changed_ratio']:.6f} "
        f"classification={CLASSIFICATION} "
        f"report={report_path.relative_to(ROOT).as_posix()}"
    )


if __name__ == "__main__":
    main()
