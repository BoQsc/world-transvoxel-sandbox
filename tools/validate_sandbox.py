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
        "scripts/terrain_recovery_policy.gd",
        "scripts/terrain_recovery_policy.gd.uid",
        "scripts/terrain_sculpt_controller.gd",
        "scripts/fly_camera.gd",
        "scripts/terrain_visualizer.gd",
        "scripts/terrain_overlay.gd",
        "shaders/terrain_material.gdshader",
        "materials/terrain_material.tres",
        "config/terrain_config.tres",
        "tools/generate_world.py",
        "tools/scale_ladder.py",
        "tools/scale_runtime.py",
        "tools/scale_visual.py",
        "tools/capture_visuals.py",
        "tools/test_sandbox.py",
        "tests/sandbox_smoke.gd",
        "tests/terrain_geometry_audit.gd",
        "tests/terrain_idle_audit.gd",
        "tests/terrain_interaction_audit.gd",
        "tests/terrain_l1_runtime_audit.gd",
        "tests/terrain_l1_runtime_audit.gd.uid",
        "tests/terrain_l2_runtime_audit.gd",
        "tests/terrain_l2_runtime_audit.gd.uid",
        "tests/terrain_l1_visual_capture.gd",
        "tests/terrain_l1_visual_capture.gd.uid",
        "tests/terrain_volumetric_audit.gd",
        "tests/terrain_motion_audit.gd",
        "tests/terrain_seam_audit.gd",
        "tests/terrain_visual_capture.gd",
        "docs/CURRENT_STATUS.md",
        "docs/ROADMAP.md",
        "docs/TERRAIN_ACCEPTANCE_STANDARD.md",
        "docs/TERRAIN_RECOVERY_CONTRACT.md",
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

    contract = ROOT / "docs" / "TERRAIN_RECOVERY_CONTRACT.md"
    if contract.is_file():
        text = contract.read_text(encoding="utf-8")
        for phrase in (
            "manual_exact_restore",
            "restore_to_base",
            "timed_regeneration",
            "surface_relaxation",
            "structural_stability",
            "fluid_equilibrium",
            "settled terrain must stay cold",
        ):
            if phrase not in text:
                errors.append(f"recovery contract is missing phrase: {phrase}")

    standard = ROOT / "docs" / "TERRAIN_ACCEPTANCE_STANDARD.md"
    if standard.is_file():
        text = standard.read_text(encoding="utf-8")
        for phrase in (
            "standards-first",
            "Large-terrain ladder",
            "Dynamic LOD popping remains a blocker",
            "Settled terrain must stay cold",
            "no tracked PowerShell workflow scripts",
            "GDScript is glue",
            "Compute shaders are deferred",
            "Decision tracking",
        ):
            if phrase not in text:
                errors.append(f"terrain standard is missing phrase: {phrase}")

    status = ROOT / "docs" / "CURRENT_STATUS.md"
    if status.is_file():
        text = status.read_text(encoding="utf-8")
        for phrase in (
            "S2 - chunked generation and scale ladder",
            "S2.1 - Python scale-ladder generation proof is complete",
            "S2.2 - L1 runtime acceptance path is complete",
            "S2.3 - L1 visual capture and artifact classification is complete",
            "S2.4 - L2 512 generation preflight is complete",
            "S2.5 - L2 runtime acceptance path",
            "S2.6 - L2 visual capture and artifact classification",
            "GDScript is glue",
            "Deferred by rule",
        ):
            if phrase not in text:
                errors.append(f"current status is missing phrase: {phrase}")

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
