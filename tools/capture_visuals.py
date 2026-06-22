#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "artifacts" / "visual"
EXPECTED_IMAGES = (
    "overview_surface.png",
    "overview_material.png",
    "overview_lod.png",
    "top_surface.png",
    "top_unshadowed.png",
    "top_lod.png",
    "closed_boundary.png",
    "closed_boundary_material.png",
)


def discover_engine(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.resolve()
    sibling = ROOT.parent / "world-transvoxel" / ".tools" / "godot" / "4.7"
    candidates = sorted(sibling.glob("Godot*_win64.exe"))
    if candidates:
        return candidates[0].resolve()
    environment = os.environ.get("GODOT")
    if environment:
        return Path(environment).resolve()
    executable = shutil.which("godot")
    if executable:
        return Path(executable).resolve()
    raise RuntimeError("No Godot executable found; pass --godot.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Capture deterministic World Transvoxel visual evidence."
    )
    parser.add_argument("--godot", type=Path)
    arguments = parser.parse_args()
    engine = discover_engine(arguments.godot)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            str(engine),
            "--path",
            str(ROOT),
            "--script",
            "res://tests/terrain_visual_capture.gd",
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
        errors="replace",
        timeout=180,
    )
    combined = result.stdout + result.stderr
    (OUTPUT_ROOT / "capture.log").write_text(combined, encoding="utf-8")
    print(combined, end="" if combined.endswith("\n") else "\n")
    missing = [
        name
        for name in EXPECTED_IMAGES
        if not (OUTPUT_ROOT / name).is_file()
        or (OUTPUT_ROOT / name).stat().st_size < 10_000
    ]
    if (
        result.returncode != 0
        or "WT_SANDBOX_VISUAL_CAPTURE_PASS" not in combined
        or missing
    ):
        raise RuntimeError(
            f"Visual capture failed; missing or undersized images: {missing}"
        )
    print(
        "WT_SANDBOX_VISUAL_EVIDENCE_PASS "
        f"images={len(EXPECTED_IMAGES)} output={OUTPUT_ROOT}"
    )


if __name__ == "__main__":
    main()
