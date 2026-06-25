#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

from capture_lod_temporal import (
    MAX_MEAN_RGB_DELTA,
    MAX_VISIBLE_CHANGED_RATIO,
    parse_fields,
    visible_changed_ratio,
)
from scale_visual import discover_engine


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "artifacts" / "dynamic_lod_temporal_multiview"
SCRIPT = "res://tests/terrain_lod_temporal_multiview_capture.gd"
PASS_MARKER = "WT_SANDBOX_LOD_TEMPORAL_MULTIVIEW_CAPTURE_PASS"
FRAME_MARKER = "WT_SANDBOX_LOD_TEMPORAL_MULTIVIEW_FRAME"
CLASSIFICATION = "temporal_multiview_gross_pop_gate_pass_pending_human_review"
FAILURE_CLASSIFICATION = "temporal_multiview_gross_pop_gate_failed_pending_review"
IMAGE_PATTERN = re.compile(
    r"view_(?P<view>\d+)_(?P<view_name>[a-z]+)_anchor_"
    r"(?P<anchor>\d+)_frame_(?P<frame>\d+)\.png"
)
THUMBNAIL_SIZE = (320, 180)
LABEL_HEIGHT = 42
PADDING = 8


def image_key(path: Path) -> tuple[int, str, int, int]:
    match = IMAGE_PATTERN.fullmatch(path.name)
    if match is None:
        raise RuntimeError(f"unexpected temporal multi-view image name: {path.name}")
    return (
        int(match.group("view")),
        match.group("view_name"),
        int(match.group("anchor")),
        int(match.group("frame")),
    )


def group_images(paths: list[Path]) -> dict[tuple[int, str, int], list[Path]]:
    groups: dict[tuple[int, str, int], list[Path]] = {}
    for path in paths:
        view, view_name, anchor, _frame = image_key(path)
        groups.setdefault((view, view_name, anchor), []).append(path)
    for values in groups.values():
        values.sort(key=lambda item: image_key(item)[3])
    return groups


def analyze_groups(groups: dict[tuple[int, str, int], list[Path]]) -> dict[str, object]:
    pairs: list[dict[str, object]] = []
    max_pair: dict[str, object] | None = None
    for (view, view_name, anchor), paths in sorted(groups.items()):
        previous: Image.Image | None = None
        for index, path in enumerate(paths):
            current = Image.open(path)
            if previous is not None:
                mean_delta, changed_ratio = visible_changed_ratio(previous, current)
                pair = {
                    "view": view,
                    "view_name": view_name,
                    "anchor": anchor,
                    "from": paths[index - 1].name,
                    "to": path.name,
                    "mean_rgb_delta": mean_delta,
                    "visible_changed_ratio": changed_ratio,
                }
                pairs.append(pair)
                if max_pair is None or changed_ratio > max_pair["visible_changed_ratio"]:
                    max_pair = pair
            previous = current
    if max_pair is None:
        raise RuntimeError("not enough temporal multi-view images to compare")
    return {
        "frame_pairs": pairs,
        "max_visible_changed_ratio": max_pair["visible_changed_ratio"],
        "max_mean_rgb_delta": max(pair["mean_rgb_delta"] for pair in pairs),
        "maximum_change_pair": max_pair,
    }


def thumbnail(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB").resize(
        THUMBNAIL_SIZE,
        Image.Resampling.LANCZOS,
    )


def amplified_difference(left: Path, right: Path) -> Image.Image:
    diff = ImageChops.difference(
        Image.open(left).convert("RGB"),
        Image.open(right).convert("RGB"),
    )
    return diff.point(lambda value: min(255, value * 8)).resize(
        THUMBNAIL_SIZE,
        Image.Resampling.LANCZOS,
    )


def write_top_change_review(analysis: dict[str, object], limit: int = 8) -> Path:
    pairs = sorted(
        analysis["frame_pairs"],
        key=lambda pair: pair["visible_changed_ratio"],
        reverse=True,
    )[:limit]
    font = ImageFont.load_default()
    thumb_width, thumb_height = THUMBNAIL_SIZE
    canvas = Image.new(
        "RGB",
        (
            3 * thumb_width + 4 * PADDING,
            len(pairs) * (thumb_height + LABEL_HEIGHT) + (len(pairs) + 1) * PADDING,
        ),
        (25, 25, 25),
    )
    draw = ImageDraw.Draw(canvas)
    for row, pair in enumerate(pairs):
        y = PADDING + row * (thumb_height + LABEL_HEIGHT + PADDING)
        labels = [
            pair["from"],
            pair["to"],
            (
                "diff x8 "
                f"ratio={pair['visible_changed_ratio']:.6f} "
                f"mean={pair['mean_rgb_delta']:.6f}"
            ),
        ]
        images = [
            thumbnail(OUTPUT_ROOT / pair["from"]),
            thumbnail(OUTPUT_ROOT / pair["to"]),
            amplified_difference(OUTPUT_ROOT / pair["from"], OUTPUT_ROOT / pair["to"]),
        ]
        for column, (image, label) in enumerate(zip(images, labels)):
            x = PADDING + column * (thumb_width + PADDING)
            draw.text((x, y), label, fill=(235, 235, 235), font=font)
            canvas.paste(image, (x, y + LABEL_HEIGHT))
    output = OUTPUT_ROOT / "temporal_multiview_top_change_pairs_review.png"
    canvas.save(output)
    return output


def write_preview(paths: list[Path]) -> Path:
    frames: list[Image.Image] = []
    for path in sorted(paths, key=image_key)[::12]:
        frame = Image.open(path).convert("P", palette=Image.Palette.ADAPTIVE)
        frames.append(frame.resize((480, 270)))
    output = OUTPUT_ROOT / "temporal_multiview_preview.gif"
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
        description="Capture multi-view temporal mixed-LOD surface evidence."
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
        timeout=900,
    )
    combined = result.stdout + result.stderr
    (OUTPUT_ROOT / "capture.log").write_text(combined, encoding="utf-8")
    print(combined, end="" if combined.endswith("\n") else "\n")
    pass_line = next((line for line in combined.splitlines() if PASS_MARKER in line), "")
    frame_lines = [line for line in combined.splitlines() if FRAME_MARKER in line]
    if result.returncode != 0 or not pass_line or len(frame_lines) < 360:
        raise RuntimeError("temporal multi-view dynamic LOD capture failed")
    pass_fields = parse_fields(pass_line)
    if int(pass_fields.get("max_render_fading", "0")) <= 0:
        raise RuntimeError("temporal multi-view capture missed native fade")
    images = sorted(OUTPUT_ROOT.glob("view_*_anchor_*_frame_*.png"), key=image_key)
    groups = group_images(images)
    analysis = analyze_groups(groups)
    review = write_top_change_review(analysis)
    preview = write_preview(images)
    passed = (
        analysis["max_visible_changed_ratio"] <= MAX_VISIBLE_CHANGED_RATIO
        and analysis["max_mean_rgb_delta"] <= MAX_MEAN_RGB_DELTA
    )
    classification = CLASSIFICATION if passed else FAILURE_CLASSIFICATION
    report = {
        "schema": "world-transvoxel-sandbox.dynamic-lod-temporal-multiview.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "engine": str(engine),
        "status": "classified" if passed else "failed",
        "classification": classification,
        "gross_pop_gate": {
            "max_mean_rgb_delta": MAX_MEAN_RGB_DELTA,
            "max_visible_changed_ratio": MAX_VISIBLE_CHANGED_RATIO,
            "passed": passed,
        },
        "raw_capture_classification": pass_fields["classification"],
        "summary": pass_fields,
        "frames": [parse_fields(line) for line in frame_lines],
        "image_analysis": analysis,
        "image_count": len(images),
        "group_count": len(groups),
        "output": OUTPUT_ROOT.relative_to(ROOT).as_posix(),
        "preview": preview.relative_to(ROOT).as_posix(),
        "review": review.relative_to(ROOT).as_posix(),
        "proven": [
            "surface-mode transition frame sequences were captured from multiple camera views",
            "native render fade was active during the sequences",
            "frame-to-frame visible image deltas were measured per view and anchor",
        ],
        "not_proven": [
            "human visual acceptance",
            "all possible camera angles",
            "all movement speeds",
            "geomorphing",
        ],
    }
    if passed:
        report["proven"].append(
            "automated gross-pop threshold passed for these deterministic views"
        )
    else:
        report["not_proven"].append(
            "automated gross-pop threshold passed for these deterministic views"
        )
    report_path = OUTPUT_ROOT / "dynamic_lod_temporal_multiview_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if not passed:
        raise RuntimeError(
            "multi-view temporal gross-pop gate failed; "
            f"report={report_path.relative_to(ROOT).as_posix()} "
            f"review={review.relative_to(ROOT).as_posix()}"
        )
    maximum = analysis["maximum_change_pair"]
    print(
        "WT_SANDBOX_DYNAMIC_LOD_TEMPORAL_MULTIVIEW_PASS "
        f"frames={len(images)} groups={len(groups)} "
        f"max_render_fading={pass_fields['max_render_fading']} "
        f"max_visible_changed_ratio={analysis['max_visible_changed_ratio']:.6f} "
        f"max_pair={maximum['from']}->{maximum['to']} "
        f"classification={CLASSIFICATION} "
        f"report={report_path.relative_to(ROOT).as_posix()}"
    )


if __name__ == "__main__":
    main()
