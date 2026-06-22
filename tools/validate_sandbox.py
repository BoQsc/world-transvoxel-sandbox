#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "WORLD_TRANSVOXEL_RELEASE_MANIFEST.json"
LOCK_PATH = ROOT / "VENDOR_LOCK.json"
SOURCE_LIMITS = {".gd": 250, ".gdshader": 400, ".py": 600}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return [line.replace("\\", "/") for line in result.stdout.splitlines()]


def main() -> int:
    errors: list[str] = []
    required = (
        "LICENSE",
        "README.md",
        "VENDOR_LOCK.json",
        "WORLD_TRANSVOXEL_LICENSE_SCOPE.md",
        "WORLD_TRANSVOXEL_RELEASE_MANIFEST.json",
        "LICENSES/MIT-Transvoxel.txt",
        "project.godot",
        "scenes/terrain_lab.tscn",
        "scripts/terrain_lab.gd",
        "scripts/fly_camera.gd",
        "scripts/terrain_visualizer.gd",
        "scripts/terrain_overlay.gd",
        "shaders/terrain_material.gdshader",
        "materials/terrain_material.tres",
        "config/terrain_config.tres",
        "tools/generate_world.py",
        "tools/test_sandbox.py",
        "tests/sandbox_smoke.gd",
        "docs/ROADMAP.md",
        "addons/world_transvoxel/bin/world_transvoxel.windows.template_debug.x86_64.dll",
        "addons/world_transvoxel/bin/world_transvoxel.windows.template_release.x86_64.dll",
    )
    for relative in required:
        if not (ROOT / relative).is_file():
            errors.append(f"missing required file: {relative}")

    if MANIFEST_PATH.is_file() and LOCK_PATH.is_file():
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
        expected_manifest_hash = lock["world_transvoxel"]["manifest_sha256"]
        if sha256(MANIFEST_PATH) != expected_manifest_hash:
            errors.append("vendored release manifest hash mismatch")
        records = manifest.get("files", [])
        listed_addon_paths = {
            record["path"]
            for record in records
            if record["path"].startswith("addons/world_transvoxel/")
        }
        addon_root = ROOT / "addons" / "world_transvoxel"
        actual_addon_paths = {
            path.relative_to(ROOT).as_posix()
            for path in addon_root.rglob("*")
            if path.is_file()
        }
        if actual_addon_paths != listed_addon_paths:
            missing = sorted(listed_addon_paths - actual_addon_paths)
            unlisted = sorted(actual_addon_paths - listed_addon_paths)
            errors.append(
                "vendored addon payload differs from manifest: "
                f"missing={missing[:10]}, unlisted={unlisted[:10]}"
            )
        for record in records:
            relative = record["path"]
            if not relative.startswith("addons/world_transvoxel/"):
                continue
            path = ROOT / relative
            if (
                not path.is_file()
                or path.stat().st_size != record["bytes"]
                or sha256(path) != record["sha256"]
            ):
                errors.append(f"vendored addon file mismatch: {relative}")

    files = tracked_files()
    for relative in files:
        path = ROOT / relative
        if not path.is_file() or relative.startswith("addons/world_transvoxel/"):
            continue
        suffix = path.suffix.lower()
        if suffix in SOURCE_LIMITS:
            count = sum(
                1 for _ in path.open(encoding="utf-8", errors="replace")
            )
            if count > SOURCE_LIMITS[suffix]:
                errors.append(
                    f"source limit exceeded: {relative} "
                    f"({count} > {SOURCE_LIMITS[suffix]})"
                )
        if relative.lower().endswith(".ps1"):
            errors.append(f"platform-specific shell script is tracked: {relative}")

    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        print(f"Sandbox validation failed with {len(errors)} error(s).")
        return 1
    print(
        "WT_SANDBOX_VALIDATION_PASS "
        f"vendored_files={len(json.loads(MANIFEST_PATH.read_text())['files'])} "
        f"project_files={len(files)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
