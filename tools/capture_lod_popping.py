#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from scale_visual import discover_engine


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "artifacts" / "dynamic_lod"
SCRIPT = "res://tests/terrain_lod_pop_capture.gd"
PASS_MARKER = "WT_SANDBOX_LOD_POP_EVIDENCE_PASS"
FRAME_MARKER = "WT_SANDBOX_LOD_POP_FRAME"


def parse_fields(line: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for item in line.split()[1:]:
        if "=" in item:
            key, value = item.split("=", 1)
            fields[key] = value
    return fields


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Capture dynamic mixed-LOD replacement evidence."
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
        timeout=300,
    )
    combined = result.stdout + result.stderr
    (OUTPUT_ROOT / "capture.log").write_text(combined, encoding="utf-8")
    print(combined, end="" if combined.endswith("\n") else "\n")
    pass_line = next(
        (line for line in combined.splitlines() if PASS_MARKER in line),
        "",
    )
    frame_lines = [
        line for line in combined.splitlines() if FRAME_MARKER in line
    ]
    if result.returncode != 0 or not pass_line or not frame_lines:
        raise RuntimeError("dynamic LOD evidence capture failed")
    pass_fields = parse_fields(pass_line)
    frame_fields = [parse_fields(line) for line in frame_lines]
    replacement_frames = int(pass_fields["replacement_frames"])
    if replacement_frames <= 0:
        raise RuntimeError("dynamic LOD capture did not observe replacements")
    images = sorted(
        path.name
        for path in OUTPUT_ROOT.glob("*.png")
        if path.stat().st_size > 10_000
    )
    if len(images) < 2:
        raise RuntimeError("dynamic LOD capture produced too few images")
    report = {
        "schema": "world-transvoxel-sandbox.dynamic-lod-evidence.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "engine": str(engine),
        "status": "classified",
        "classification": pass_fields["classification"],
        "summary": pass_fields,
        "frames": frame_fields,
        "images": images,
        "output": OUTPUT_ROOT.relative_to(ROOT).as_posix(),
        "proven": [
            "fixed-camera dynamic demand updates produce render-set replacement frames",
            "render and collision stay present at the center probe during replacements",
            "the observed artifact is an LOD transition visual swap, not a hard hole",
        ],
        "not_proven": [
            "human visual acceptance",
            "geomorphing or cross-fading",
            "fast travel or disjoint teleport policy",
        ],
    }
    (OUTPUT_ROOT / "dynamic_lod_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "WT_SANDBOX_DYNAMIC_LOD_CAPTURE_PASS "
        f"replacement_frames={replacement_frames} "
        f"captures={pass_fields['captures']} "
        f"classification={pass_fields['classification']} "
        f"report={(OUTPUT_ROOT / 'dynamic_lod_report.json').relative_to(ROOT).as_posix()}"
    )


if __name__ == "__main__":
    main()
