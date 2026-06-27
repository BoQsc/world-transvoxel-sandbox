#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageStat

from scale_visual import discover_engine
from s3_visibility_workload import ensure_l4_world


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "artifacts" / "s3_visual_gpu"
SCRIPT = "res://tests/terrain_s3_visual_gpu_audit.gd"
PASS_MARKER = "WT_SANDBOX_S3_VISUAL_GPU_PASS"
AUDIT_MARKER = "WT_SANDBOX_S3_VISUAL_GPU_AUDIT_PASS"
CAPTURE_MARKER = "WT_SANDBOX_S3_VISUAL_CAPTURE"
TIMEOUT_SECONDS = 480
EXPECTED_IMAGES = (
    "stable_overview.png",
    "stable_material.png",
    "normal_00.png",
    "normal_01.png",
    "normal_02.png",
    "normal_03.png",
    "rapid_turn_00.png",
    "rapid_turn_01.png",
    "rapid_turn_02.png",
    "rapid_turn_03.png",
    "underground_tunnel.png",
    "pre_edit.png",
    "post_edit.png",
)


def parse_fields(line: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for item in line.split()[1:]:
        if "=" in item:
            key, value = item.split("=", 1)
            fields[key] = value
    return fields


def has_godot_error(combined: str) -> bool:
    return (
        "SCRIPT ERROR:" in combined
        or "SCRIPT ERROR" in combined
        or combined.startswith("ERROR:")
        or "\nERROR:" in combined
    )


def reset_artifacts() -> None:
    resolved = ARTIFACT_ROOT.resolve()
    resolved.relative_to(ROOT.resolve())
    if resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True)


def run_capture(engine: Path) -> tuple[dict[str, str], list[dict[str, str]]]:
    reset_artifacts()
    result = subprocess.run(
        [str(engine), "--path", str(ROOT), "--script", SCRIPT, "--", "--disable-player-input"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
        errors="replace",
        timeout=TIMEOUT_SECONDS,
    )
    combined = result.stdout + result.stderr
    (ARTIFACT_ROOT / "capture.log").write_text(combined, encoding="utf-8")
    print(combined, end="" if combined.endswith("\n") else "\n")
    pass_line = next((line for line in combined.splitlines() if PASS_MARKER in line), "")
    captures = [
        parse_fields(line)
        for line in combined.splitlines()
        if CAPTURE_MARKER in line
    ]
    if result.returncode != 0 or not pass_line or has_godot_error(combined):
        raise RuntimeError("S3 visual/GPU capture failed")
    missing = [
        name
        for name in EXPECTED_IMAGES
        if not (ARTIFACT_ROOT / name).is_file()
        or (ARTIFACT_ROOT / name).stat().st_size < 10_000
    ]
    if missing or len(captures) != len(EXPECTED_IMAGES):
        raise RuntimeError(f"S3 visual/GPU capture set is incomplete: {missing}")
    return parse_fields(pass_line), captures


def image_metrics(path: Path) -> dict[str, object]:
    with Image.open(path) as source:
        rgb = source.convert("RGB")
        width, height = rgb.size
        stat = ImageStat.Stat(rgb)
        extrema = rgb.getextrema()
    luminance_range = max(high for _low, high in extrema) - min(low for low, _high in extrema)
    stddev = sum(stat.stddev) / (3.0 * 255.0)
    if (width, height) != (1280, 720):
        raise RuntimeError(f"Unexpected S3 visual image size: {path}")
    if luminance_range < 13:
        raise RuntimeError(f"S3 visual image has low range: {path}")
    if stddev < 0.01:
        raise RuntimeError(f"S3 visual image is too flat: {path}")
    return {
        "image": path.name,
        "bytes": path.stat().st_size,
        "size": f"{width}x{height}",
        "rgb_range_0_255": int(luminance_range),
        "rgb_stddev_0_1": round(stddev, 6),
    }


def contact_sheet() -> Path:
    thumbnails: list[tuple[str, Image.Image]] = []
    for name in EXPECTED_IMAGES:
        with Image.open(ARTIFACT_ROOT / name) as source:
            thumb = source.convert("RGB")
            thumb.thumbnail((320, 180))
            thumbnails.append((name, thumb.copy()))
    width = 4 * 340
    height = 4 * 230
    sheet = Image.new("RGB", (width, height), (18, 18, 18))
    draw = ImageDraw.Draw(sheet)
    for index, (name, image) in enumerate(thumbnails):
        x = (index % 4) * 340 + 10
        y = (index // 4) * 230 + 10
        sheet.paste(image, (x, y + 24))
        draw.text((x, y), name, fill=(235, 235, 235))
    output = ARTIFACT_ROOT / "contact_sheet.png"
    sheet.save(output)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Run S3 graphical visual/GPU audit.")
    parser.add_argument("--godot", type=Path)
    parser.add_argument("--force-generation", action="store_true")
    arguments = parser.parse_args()
    ensure_l4_world(arguments.force_generation)
    engine = discover_engine(arguments.godot)
    marker, captures = run_capture(engine)
    images = [image_metrics(ARTIFACT_ROOT / name) for name in EXPECTED_IMAGES]
    sheet = contact_sheet()
    report = {
        "schema": "world-transvoxel-sandbox.s3-visual-gpu.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "visual_gpu_acceptance_pass",
        "engine": str(engine),
        "script": SCRIPT,
        "marker": marker,
        "captures": captures,
        "images": images,
        "contact_sheet": sheet.relative_to(ROOT).as_posix(),
        "proven": [
            "L4 S3 graphical scene captures representative stable, movement, turn, underground, and edit views",
            "player input is disabled before scene entry",
            "capture-time render/collision coverage is present and render queues/fades are settled",
            "rapid graphical turns do not create terrain demand",
            "captured images are nonblank 1280x720 frames with measurable visual range",
        ],
        "not_proven": [
            "hardware vendor GPU timing beyond graphical frame interval",
            "GPU compute acceleration",
            "final human qualitative acceptance",
            "water, lava, planets, structural stability, or game repository readiness",
        ],
    }
    report_path = ARTIFACT_ROOT / "visual_gpu_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"{AUDIT_MARKER} images={len(images)} "
        f"report={report_path.relative_to(ROOT).as_posix()} "
        f"contact_sheet={sheet.relative_to(ROOT).as_posix()}"
    )


if __name__ == "__main__":
    main()
