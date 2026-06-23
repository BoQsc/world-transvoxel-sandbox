#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "artifacts" / "tests"
ENGINE_VERSIONS = ("4.6.3", "4.7")
TEST_CASES = (
    ("smoke", "res://tests/sandbox_smoke.gd", "WT_SANDBOX_SMOKE_PASS"),
    ("idle", "res://tests/terrain_idle_audit.gd", "WT_SANDBOX_IDLE_PASS"),
    (
        "geometry",
        "res://tests/terrain_geometry_audit.gd",
        "WT_SANDBOX_GEOMETRY_PASS",
    ),
    (
        "interaction",
        "res://tests/terrain_interaction_audit.gd",
        "WT_SANDBOX_INTERACTION_PASS",
    ),
    (
        "motion",
        "res://tests/terrain_motion_audit.gd",
        "WT_SANDBOX_MOTION_PASS",
    ),
    ("seams", "res://tests/terrain_seam_audit.gd", "WT_SANDBOX_SEAM_PASS"),
)
DEBUG_DLL = (
    ROOT
    / "addons"
    / "world_transvoxel"
    / "bin"
    / "world_transvoxel.windows.template_debug.x86_64.dll"
)
RELEASE_DLL = (
    ROOT
    / "addons"
    / "world_transvoxel"
    / "bin"
    / "world_transvoxel.windows.template_release.x86_64.dll"
)


def discover_engines(explicit: list[Path]) -> list[tuple[str, Path]]:
    if explicit:
        return [(path.stem, path.resolve()) for path in explicit]
    sibling = ROOT.parent / "world-transvoxel" / ".tools" / "godot"
    discovered: list[tuple[str, Path]] = []
    for version in ENGINE_VERSIONS:
        folder = sibling / version
        candidates = sorted(folder.glob("Godot*_win64.exe"))
        if candidates:
            discovered.append((version, candidates[0].resolve()))
    if discovered:
        return discovered
    environment = os.environ.get("GODOT")
    if environment:
        return [("environment", Path(environment).resolve())]
    executable = shutil.which("godot")
    if executable:
        return [("path", Path(executable).resolve())]
    raise RuntimeError(
        "No Godot executable found. Pass --godot or set the GODOT environment variable."
    )


def run_case(engine: Path, name: str, script: str, marker: str) -> None:
    journal = ROOT / "world" / "world.wtedit"
    if journal.exists():
        journal.unlink()
    result = subprocess.run(
        [
            str(engine),
            "--headless",
            "--path",
            str(ROOT),
            "--script",
            script,
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
        errors="replace",
        timeout=120,
    )
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    (ARTIFACT_ROOT / f"{name}.stdout.txt").write_text(
        result.stdout, encoding="utf-8"
    )
    (ARTIFACT_ROOT / f"{name}.stderr.txt").write_text(
        result.stderr, encoding="utf-8"
    )
    combined = result.stdout + result.stderr
    print(combined, end="" if combined.endswith("\n") else "\n")
    if result.returncode != 0 or marker not in combined:
        raise RuntimeError(f"Sandbox Godot case failed: {name}")


def import_project(engine: Path, name: str) -> None:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    attempts: list[str] = []
    result: subprocess.CompletedProcess[str] | None = None
    extension_cache = ROOT / ".godot" / "extension_list.cfg"
    for _attempt in range(2):
        result = subprocess.run(
            [str(engine), "--headless", "--path", str(ROOT), "--import"],
            cwd=ROOT,
            check=False,
            text=True,
            capture_output=True,
            errors="replace",
            timeout=120,
        )
        combined = result.stdout + result.stderr
        attempts.append(combined)
        cache_valid = (
            extension_cache.is_file()
            and "res://addons/world_transvoxel/world_transvoxel.gdextension"
            in extension_cache.read_text(encoding="utf-8")
        )
        if result.returncode == 0 and cache_valid and "SCRIPT ERROR:" not in combined:
            break
        if "SCRIPT ERROR:" in combined or not cache_valid:
            break
    combined = "\n".join(attempts)
    (ARTIFACT_ROOT / f"{name}.import.txt").write_text(
        combined, encoding="utf-8"
    )
    print(combined, end="" if combined.endswith("\n") else "\n")
    if (
        result is None
        or
        result.returncode != 0
        or not extension_cache.is_file()
        or "res://addons/world_transvoxel/world_transvoxel.gdextension"
        not in extension_cache.read_text(encoding="utf-8")
        or "SCRIPT ERROR:" in combined
    ):
        raise RuntimeError(f"Sandbox Godot import failed: {name}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the World Transvoxel sandbox Godot matrix."
    )
    parser.add_argument("--godot", type=Path, action="append", default=[])
    arguments = parser.parse_args()
    engines = discover_engines(arguments.godot)
    if not (ROOT / "world" / "world.wtworld").is_file():
        raise RuntimeError("Generate the sandbox world before testing.")
    if not DEBUG_DLL.is_file() or not RELEASE_DLL.is_file():
        raise RuntimeError("Vendored runtime binaries are incomplete.")

    for version, engine in engines:
        import_project(engine, f"godot-{version}")
    for version, engine in engines:
        for case_name, script, marker in TEST_CASES:
            run_case(
                engine,
                f"godot-{version}-debug-{case_name}",
                script,
                marker,
            )

    backup = ARTIFACT_ROOT / f"{DEBUG_DLL.name}.backup"
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DEBUG_DLL, backup)
    try:
        shutil.copy2(RELEASE_DLL, DEBUG_DLL)
        for version, engine in engines:
            for case_name, script, marker in TEST_CASES:
                run_case(
                    engine,
                    f"godot-{version}-release-{case_name}",
                    script,
                    marker,
                )
    finally:
        shutil.copy2(backup, DEBUG_DLL)
        backup.unlink(missing_ok=True)
    print(
        "WT_SANDBOX_MATRIX_PASS "
        f"engines={len(engines)} configurations=2 "
        f"tests={len(TEST_CASES)} cases={len(engines) * 2 * len(TEST_CASES)}"
    )


if __name__ == "__main__":
    main()
