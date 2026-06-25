#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "artifacts" / "dynamic_lod_temporal"
REPORT_PATH = OUTPUT_ROOT / "dynamic_lod_temporal_report.json"
TOP_CHANGE_REVIEW = OUTPUT_ROOT / "temporal_top_change_pairs_review.png"
ANCHOR_REVIEW = OUTPUT_ROOT / "temporal_anchor_transition_review.png"
THUMBNAIL_SIZE = (320, 180)
LABEL_HEIGHT = 42
PADDING = 8


def draw_label(
    canvas: Image.Image,
    position: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
) -> None:
    draw = ImageDraw.Draw(canvas)
    draw.text(position, text, fill=(235, 235, 235), font=font)


def thumbnail(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB").resize(
        THUMBNAIL_SIZE,
        Image.Resampling.LANCZOS,
    )


def amplified_difference(left: Path, right: Path) -> Image.Image:
    left_image = Image.open(left).convert("RGB")
    right_image = Image.open(right).convert("RGB")
    diff = ImageChops.difference(left_image, right_image)
    return diff.point(lambda value: min(255, value * 8)).resize(
        THUMBNAIL_SIZE,
        Image.Resampling.LANCZOS,
    )


def write_top_change_review(report: dict[str, object], limit: int) -> Path:
    pairs = sorted(
        report["image_analysis"]["frame_pairs"],
        key=lambda pair: pair["visible_changed_ratio"],
        reverse=True,
    )[:limit]
    font = ImageFont.load_default()
    thumb_width, thumb_height = THUMBNAIL_SIZE
    columns = 3
    rows = len(pairs)
    canvas = Image.new(
        "RGB",
        (
            columns * thumb_width + (columns + 1) * PADDING,
            rows * (thumb_height + LABEL_HEIGHT) + (rows + 1) * PADDING,
        ),
        (25, 25, 25),
    )
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
            amplified_difference(
                OUTPUT_ROOT / pair["from"],
                OUTPUT_ROOT / pair["to"],
            ),
        ]
        for column, (image, label) in enumerate(zip(images, labels)):
            x = PADDING + column * (thumb_width + PADDING)
            draw_label(canvas, (x, y), label, font)
            canvas.paste(image, (x, y + LABEL_HEIGHT))
    canvas.save(TOP_CHANGE_REVIEW)
    return TOP_CHANGE_REVIEW


def write_anchor_review(report: dict[str, object]) -> Path:
    frames_by_anchor: dict[int, list[dict[str, str]]] = {}
    for frame in report["frames"]:
        frames_by_anchor.setdefault(int(frame["anchor"]), []).append(frame)
    samples_by_anchor: list[tuple[int, list[int]]] = []
    for anchor, frames in sorted(frames_by_anchor.items()):
        chosen = max(
            frames,
            key=lambda frame: (
                int(frame["render_fading"]),
                abs(int(frame["render"]) - int(frames[0]["render"])),
            ),
        )
        center = int(chosen["frame"])
        samples = [
            max(0, center - 6),
            max(0, center - 3),
            center,
            min(89, center + 3),
            min(89, center + 6),
        ]
        samples_by_anchor.append((anchor, list(dict.fromkeys(samples))))

    font = ImageFont.load_default()
    thumb_width, thumb_height = THUMBNAIL_SIZE
    columns = max(len(samples) for _, samples in samples_by_anchor)
    rows = len(samples_by_anchor)
    canvas = Image.new(
        "RGB",
        (
            columns * thumb_width + (columns + 1) * PADDING,
            rows * (thumb_height + LABEL_HEIGHT) + (rows + 1) * PADDING,
        ),
        (25, 25, 25),
    )
    for row, (anchor, samples) in enumerate(samples_by_anchor):
        y = PADDING + row * (thumb_height + LABEL_HEIGHT + PADDING)
        for column, frame in enumerate(samples):
            image_path = OUTPUT_ROOT / f"anchor_{anchor:02d}_frame_{frame:03d}.png"
            x = PADDING + column * (thumb_width + PADDING)
            draw_label(canvas, (x, y), f"anchor {anchor} frame {frame}", font)
            canvas.paste(thumbnail(image_path), (x, y + LABEL_HEIGHT))
    canvas.save(ANCHOR_REVIEW)
    return ANCHOR_REVIEW


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build temporal LOD visual-review contact sheets."
    )
    parser.add_argument("--top-pairs", type=int, default=8)
    arguments = parser.parse_args()
    if not REPORT_PATH.is_file():
        raise RuntimeError(f"missing temporal report: {REPORT_PATH}")
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    top_change = write_top_change_review(report, max(1, arguments.top_pairs))
    anchor = write_anchor_review(report)
    maximum = report["image_analysis"]["maximum_change_pair"]
    print(
        "WT_SANDBOX_LOD_TEMPORAL_REVIEW_PASS "
        f"top_change={top_change.relative_to(ROOT).as_posix()} "
        f"anchor_review={anchor.relative_to(ROOT).as_posix()} "
        f"max_pair={maximum['from']}->{maximum['to']} "
        f"max_visible_changed_ratio={maximum['visible_changed_ratio']:.6f}"
    )


if __name__ == "__main__":
    main()
