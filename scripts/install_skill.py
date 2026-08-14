#!/usr/bin/env python3
"""Install or update the standalone Snowe skill with an exact staged replacement."""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import sys
from pathlib import Path
from typing import Any


PRODUCT_NAME = "snowe-ui-skill"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = REPOSITORY_ROOT / "skill" / PRODUCT_NAME
DEFAULT_DESTINATION = Path.home() / ".agents" / "skills" / PRODUCT_NAME
COPY_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".DS_Store")


def _path_exists(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def _retry_writeable(function: Any, path: str, _error: Any) -> None:
    current_mode = os.stat(path, follow_symlinks=False).st_mode
    os.chmod(path, current_mode | stat.S_IWUSR, follow_symlinks=False)
    function(path)


def _remove_path(path: Path) -> None:
    if not _path_exists(path):
        return
    if path.is_symlink() or path.is_file():
        try:
            path.unlink()
        except PermissionError:
            path.chmod(path.stat().st_mode | stat.S_IWUSR)
            path.unlink()
        return
    shutil.rmtree(path, onerror=_retry_writeable)


def _rename(source: Path, destination: Path) -> None:
    source.rename(destination)


def _validated_paths(source: str | Path, destination: str | Path) -> tuple[Path, Path]:
    source_path = Path(source).expanduser().resolve(strict=True)
    destination_path = Path(destination).expanduser().resolve(strict=False)
    if not source_path.is_dir() or not (source_path / "SKILL.md").is_file():
        raise ValueError(f"Skill source must be a directory containing SKILL.md: {source_path}")
    if destination_path.name != PRODUCT_NAME:
        raise ValueError(f"Destination must end with {PRODUCT_NAME!r}: {destination_path}")
    if (
        source_path == destination_path
        or destination_path.is_relative_to(source_path)
        or source_path.is_relative_to(destination_path)
    ):
        raise ValueError("Source and destination must not contain or replace one another.")
    return source_path, destination_path


def install_skill(
    source: str | Path = DEFAULT_SOURCE,
    destination: str | Path = DEFAULT_DESTINATION,
) -> dict[str, str]:
    """Install an exact copy and restore the previous destination on activation failure."""

    source_path, destination_path = _validated_paths(source, destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    staging = destination_path.parent / f".{PRODUCT_NAME}.installing"
    previous = destination_path.parent / f".{PRODUCT_NAME}.previous"

    # Recover the only destructive window of an interrupted prior run before
    # preparing a new staged copy.
    if _path_exists(previous):
        if _path_exists(destination_path):
            _remove_path(previous)
        else:
            _rename(previous, destination_path)
    _remove_path(staging)

    try:
        shutil.copytree(source_path, staging, symlinks=True, ignore=COPY_IGNORE)
    except BaseException:
        _remove_path(staging)
        raise
    if not (staging / "SKILL.md").is_file():
        _remove_path(staging)
        raise RuntimeError("Staged install is missing SKILL.md; destination was not changed.")

    operation = "updated" if _path_exists(destination_path) else "installed"
    moved_previous = False
    try:
        if _path_exists(destination_path):
            _rename(destination_path, previous)
            moved_previous = True
        _rename(staging, destination_path)
    except BaseException:
        if _path_exists(destination_path):
            _remove_path(destination_path)
        if moved_previous and _path_exists(previous):
            _rename(previous, destination_path)
        _remove_path(staging)
        raise

    if moved_previous:
        _remove_path(previous)
    return {
        "operation": operation,
        "source": str(source_path),
        "destination": str(destination_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install or update Snowe as an exact standalone Codex skill copy."
    )
    parser.add_argument(
        "--destination",
        type=Path,
        default=DEFAULT_DESTINATION,
        help=f"Final skill directory (default: {DEFAULT_DESTINATION})",
    )
    args = parser.parse_args()
    try:
        result = install_skill(destination=args.destination)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Install failed: {error}", file=sys.stderr)
        return 1
    print(f"Snowe {result['operation']}: {result['destination']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
