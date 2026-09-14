#!/usr/bin/env python3
"""Install or update the standalone Snowe skill with an exact staged replacement."""

from __future__ import annotations

import argparse
import hashlib
from contextlib import contextmanager
import json
import os
import re
import shutil
import stat
import sys
import uuid
from pathlib import Path
from typing import Any


PRODUCT_NAME = "snowe-ui-skill"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = REPOSITORY_ROOT / "skill" / PRODUCT_NAME
DEFAULT_DESTINATION = Path.home() / ".agents" / "skills" / PRODUCT_NAME
COPY_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".DS_Store")
INSTALLER_STATE_VERSION = "1"
FRONTMATTER_LINE_LIMIT = 128


def _path_exists(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def _retry_writeable(function: Any, path: str, _error: Any) -> None:
    current_mode = os.stat(path, follow_symlinks=False).st_mode
    os.chmod(path, current_mode | stat.S_IWUSR, follow_symlinks=False)
    function(path)


def _remove_path(path: Path) -> None:
    if not _path_exists(path):
        return
    # Junctions are directory reparse points but are not always reported as
    # symlinks by pathlib on Windows.  Remove the link itself; never recurse
    # through an activated path that failed post-swap validation.
    if _is_reparse_path(path):
        if path.is_dir() and not path.is_symlink():
            path.rmdir()
        else:
            path.unlink()
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


def _marker_path(path: Path) -> Path:
    """Return the sidecar that proves a transient path belongs to this run."""
    return path.with_name(f"{path.name}.owner")


def _lexical_path(path: Path) -> str:
    """Canonicalize a path without following a final symlink."""
    return os.path.normcase(os.path.abspath(os.fspath(path)))


def _stat_identity(information: os.stat_result) -> dict[str, int] | None:
    """Return the stable filesystem identity available from an lstat/fstat."""
    try:
        device = int(information.st_dev)
        inode = int(information.st_ino)
    except (AttributeError, TypeError, ValueError):
        return None
    # Some filesystems report a zero file index.  Treat that as unknown rather
    # than claiming that two unrelated objects are the same transient slot.
    if inode == 0:
        return None
    return {"st_dev": device, "st_ino": inode}


def _filesystem_identity(path: Path) -> dict[str, int] | None:
    try:
        return _stat_identity(os.lstat(path))
    except (FileNotFoundError, OSError):
        return None


def _same_identity(actual: object, expected: object) -> bool:
    return isinstance(actual, dict) and isinstance(expected, dict) and actual == expected


def _is_reparse_path(path: Path) -> bool:
    """Detect symlinks and Windows junction/reparse points without following them."""
    try:
        information = os.lstat(path)
    except FileNotFoundError:
        return False
    attributes = getattr(information, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return stat.S_ISLNK(information.st_mode) or bool(attributes & reparse_flag)


def _reject_reparse_chain(path: Path, label: str) -> None:
    """Reject any existing redirect in a destructive target's lexical chain."""
    current = Path(os.path.abspath(os.fspath(path)))
    while True:
        if _is_reparse_path(current):
            raise ValueError(f"{label} must not contain a symlink, junction, or reparse point: {current}")
        parent = current.parent
        if parent == current:
            return
        current = parent


def _windows_long_path_name(path: Path, label: str) -> Path:
    """Expand Windows short names without resolving a reparse target."""
    import ctypes
    from ctypes import wintypes

    get_long_path_name = ctypes.WinDLL("kernel32", use_last_error=True).GetLongPathNameW
    get_long_path_name.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
    get_long_path_name.restype = wintypes.DWORD
    requested = os.fspath(path)
    size = int(get_long_path_name(requested, None, 0))
    if size == 0:
        error = ctypes.get_last_error()
        raise ValueError(f"{label} aliases cannot be inspected safely: {path} (Windows error {error})")
    for _ in range(2):
        buffer = ctypes.create_unicode_buffer(size)
        written = int(get_long_path_name(requested, buffer, size))
        if written == 0:
            error = ctypes.get_last_error()
            raise ValueError(f"{label} aliases cannot be inspected safely: {path} (Windows error {error})")
        if written < size:
            return Path(buffer.value)
        size = written
    raise ValueError(f"{label} aliases changed while they were being inspected: {path}")


def _normalize_lexical_aliases(path: Path, label: str) -> Path:
    """Normalize lexical aliases while preserving every reparse component."""
    absolute = Path(os.path.abspath(os.fspath(path)))
    if os.name != "nt":
        return absolute

    existing = absolute
    suffix: list[str] = []
    while True:
        try:
            os.lstat(existing)
            break
        except FileNotFoundError:
            parent = existing.parent
            if parent == existing:
                raise ValueError(f"{label} has no inspectable existing ancestor: {path}")
            suffix.append(existing.name)
            existing = parent
        except OSError as error:
            raise ValueError(f"{label} aliases cannot be inspected safely: {existing}") from error

    normalized = _windows_long_path_name(existing, label)
    return normalized.joinpath(*reversed(suffix))


def _validate_source_tree(source: Path) -> None:
    """Require the installable product to be a self-contained regular tree.

    ``copytree(..., symlinks=True)`` would otherwise preserve a repository
    symlink or Windows junction and could make the installed skill depend on
    files outside the product boundary.  Walk with ``lstat`` semantics and do
    not enter redirects or special filesystem objects.
    """
    pending = [source]
    while pending:
        directory = pending.pop()
        for child in directory.iterdir():
            if _is_reparse_path(child):
                raise ValueError(
                    f"Skill source must be self-contained; symlinks, junctions, and reparse points are not allowed: {child}"
                )
            information = os.lstat(child)
            if stat.S_ISDIR(information.st_mode):
                pending.append(child)
            elif not stat.S_ISREG(information.st_mode):
                raise ValueError(f"Skill source contains an unsupported filesystem object: {child}")


def _has_product_identity(skill_file: Path) -> bool:
    """Recognize the product from its bounded, unquoted frontmatter name."""
    if _is_reparse_path(skill_file) or not skill_file.is_file():
        return False
    try:
        with skill_file.open("r", encoding="utf-8", newline="") as handle:
            if handle.readline().rstrip("\r\n") != "---":
                return False
            name: str | None = None
            for _ in range(FRONTMATTER_LINE_LIMIT):
                line = handle.readline()
                if not line or len(line) > 65536:
                    return False
                value = line.rstrip("\r\n")
                if value == "---":
                    return name == PRODUCT_NAME
                if not value or value.startswith("#"):
                    continue
                match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_-]*)[ \t]*:[ \t]*(.*)", value)
                if match is None:
                    return False
                key, field_value = match.groups()
                if key == "name":
                    if name is not None:
                        return False
                    name = field_value.strip()
    except (OSError, UnicodeError):
        return False
    return False


def _is_recognized_install_tree(path: Path) -> bool:
    """Return whether a path is safe to treat as an existing Snowe install."""
    try:
        if _is_reparse_path(path) or not path.is_dir() or path.is_symlink():
            return False
        skill_file = path / "SKILL.md"
        if not _has_product_identity(skill_file):
            return False
        _validate_source_tree(path)
    except (OSError, ValueError):
        return False
    return True


@contextmanager
def _installation_lock(parent: Path):
    """Serialize swaps; the OS releases this lock after interruption or crash."""
    lock_path = parent / f".{PRODUCT_NAME}.install.lock"
    if _is_reparse_path(lock_path):
        raise ValueError(f"Installer lock must not be a symlink, junction, or reparse point: {lock_path}")
    flags = os.O_CREAT | os.O_RDWR
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    existing_identity = None
    try:
        existing_information = os.lstat(lock_path)
    except FileNotFoundError:
        existing_information = None
    if existing_information is not None:
        if _is_reparse_path(lock_path):
            raise ValueError(f"Installer lock must not be a symlink, junction, or reparse point: {lock_path}")
        if not stat.S_ISREG(existing_information.st_mode):
            raise ValueError(f"Installer lock must be a regular file: {lock_path}")
        if int(getattr(existing_information, "st_nlink", 1)) > 1:
            raise ValueError(f"Installer lock must not be a shared hardlink: {lock_path}")
        existing_identity = _stat_identity(existing_information)
    descriptor = os.open(lock_path, flags, 0o600)
    handle = os.fdopen(descriptor, "r+b", buffering=0)
    locked = False
    try:
        opened_information = os.fstat(handle.fileno())
        if _is_reparse_path(lock_path):
            raise ValueError(f"Installer lock must not be a symlink, junction, or reparse point: {lock_path}")
        if not stat.S_ISREG(opened_information.st_mode):
            raise ValueError(f"Installer lock must be a regular file: {lock_path}")
        if int(getattr(opened_information, "st_nlink", 1)) > 1:
            raise ValueError(f"Installer lock must not be a shared hardlink: {lock_path}")
        if existing_identity is not None and not _same_identity(
            _stat_identity(opened_information), existing_identity
        ):
            raise ValueError(f"Installer lock changed identity before it could be opened safely: {lock_path}")
        if os.name == "nt":
            import msvcrt

            if os.fstat(handle.fileno()).st_size == 0:
                handle.write(b"\0")
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as error:
                raise RuntimeError(f"Another Snowe installation is active for {parent}") from error
        else:
            import fcntl

            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as error:
                raise RuntimeError(f"Another Snowe installation is active for {parent}") from error
        locked = True
        yield
    finally:
        if locked:
            if os.name == "nt":
                import msvcrt

                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def _owner_record(
    path: Path,
    destination: Path,
    role: str,
    token: str,
    identity: dict[str, int] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": INSTALLER_STATE_VERSION,
        "product": PRODUCT_NAME,
        "role": role,
        "path": _lexical_path(path),
        "destination": _lexical_path(destination),
        "token": token,
        "identity": identity,
    }


def _write_owner_marker(path: Path, destination: Path, role: str, token: str) -> None:
    """Claim a transient path without overwriting an existing marker."""
    marker = _marker_path(path)
    record = _owner_record(path, destination, role, token)
    with marker.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(record, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def _read_owner_record(marker: Path) -> dict[str, Any] | None:
    if _is_reparse_path(marker) or not marker.is_file():
        return None
    try:
        record = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return record if isinstance(record, dict) else None


def _owner_metadata_matches(
    record: dict[str, Any] | None,
    path: Path,
    destination: Path,
    role: str,
    token: str,
) -> bool:
    if record is None:
        return False
    expected = {
        "schema_version": INSTALLER_STATE_VERSION,
        "product": PRODUCT_NAME,
        "role": role,
        "path": _lexical_path(path),
        "destination": _lexical_path(destination),
    }
    return (
        all(record.get(key) == value for key, value in expected.items())
        and record.get("token") == token
    )


def _bind_owner_slot(
    path: Path,
    destination: Path,
    role: str,
    token: str,
    expected_identity: dict[str, int] | None = None,
) -> dict[str, int]:
    """Bind a marker to the inode created for this run before copy/swap work."""
    marker = _marker_path(path)
    record = _read_owner_record(marker)
    if not _owner_metadata_matches(record, path, destination, role, token):
        raise ValueError(f"Installer ownership marker changed before binding: {marker}")
    try:
        marker_information = os.lstat(marker)
    except OSError as error:
        raise ValueError(f"Installer ownership marker cannot be inspected safely: {marker}") from error
    if not stat.S_ISREG(marker_information.st_mode) or int(getattr(marker_information, "st_nlink", 1)) != 1:
        raise ValueError(f"Installer ownership marker must be a private regular file: {marker}")
    identity = _filesystem_identity(path)
    if identity is None:
        raise ValueError(f"Installer transient path has no stable filesystem identity: {path}")
    if expected_identity is not None and not _same_identity(identity, expected_identity):
        raise ValueError(f"Installer transient path changed identity before binding: {path}")
    bound = dict(record)
    bound["identity"] = identity
    try:
        with marker.open("r+", encoding="utf-8", newline="\n") as handle:
            handle.seek(0)
            json.dump(bound, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.truncate()
    except OSError as error:
        raise ValueError(f"Installer ownership marker could not be bound safely: {marker}") from error
    return identity


def _owns_path(path: Path, destination: Path, role: str, token: str) -> bool:
    """Verify marker metadata and the bound filesystem identity."""
    record = _read_owner_record(_marker_path(path))
    return _owner_metadata_matches(record, path, destination, role, token) and _same_identity(
        _filesystem_identity(path), record.get("identity") if record else None
    )


def _owned_identity(path: Path, destination: Path, role: str, token: str) -> dict[str, int] | None:
    record = _read_owner_record(_marker_path(path))
    if not _owner_metadata_matches(record, path, destination, role, token):
        return None
    identity = record.get("identity") if record else None
    return dict(identity) if isinstance(identity, dict) else None


def _remove_owned_slot(path: Path, destination: Path, role: str, token: str) -> None:
    """Clean an owned transient, quarantining a replacement instead of deleting it."""
    marker = _marker_path(path)
    record = _read_owner_record(marker)
    if not _owner_metadata_matches(record, path, destination, role, token):
        return
    if not _path_exists(path):
        _remove_path(marker)
        return
    if not _same_identity(_filesystem_identity(path), record.get("identity")):
        quarantined = _quarantine_unowned(path)
        if quarantined is not None:
            _remove_path(marker)
        return
    _remove_path(path)
    _remove_path(marker)


def _remove_owned_object(
    path: Path,
    owner_path: Path,
    destination: Path,
    role: str,
    token: str,
) -> None:
    """Remove a renamed owned object only when its marker identity still matches."""
    marker = _marker_path(owner_path)
    record = _read_owner_record(marker)
    if not _owner_metadata_matches(record, owner_path, destination, role, token):
        return
    if not _path_exists(path):
        return
    if not _same_identity(_filesystem_identity(path), record.get("identity")):
        quarantined = _quarantine_unowned(path)
        if quarantined is not None:
            _remove_path(marker)
        return
    _remove_path(path)


def _quarantine_owned_slot(path: Path, destination: Path, role: str, token: str) -> Path | None:
    """Preserve an owned slot when it no longer proves safe to activate/delete."""
    marker = _marker_path(path)
    record = _read_owner_record(marker)
    if not _owner_metadata_matches(record, path, destination, role, token):
        return _quarantine_unowned(path)
    if not _path_exists(path):
        _remove_path(marker)
        return None
    quarantined = _quarantine_unowned(path)
    if quarantined is not None:
        _remove_path(marker)
    return quarantined


def _restore_owned_previous(
    previous: Path,
    destination: Path,
    token: str,
) -> None:
    """Revalidate and restore the exact previous object, never a replacement."""
    marker = _marker_path(previous)
    previous_identity = _owned_identity(previous, destination, "previous", token)
    def previous_is_safe() -> bool:
        return (
            previous_identity is not None
            and _same_identity(_filesystem_identity(previous), previous_identity)
            and _owns_path(previous, destination, "previous", token)
            and _is_recognized_install_tree(previous)
        )

    if not previous_is_safe():
        _quarantine_owned_slot(previous, destination, "previous", token)
        raise RuntimeError("Previous install changed identity before rollback; it was quarantined.")

    # A path that appeared after the staged object was removed is foreign to
    # this rollback. Preserve it by quarantine rather than replacing it.
    if _path_exists(destination):
        quarantined = _quarantine_unowned(destination)
        if quarantined is None or _path_exists(destination):
            raise RuntimeError("Destination became occupied before rollback; previous install was not activated.")
    _reject_reparse_chain(destination, "Destination")
    # Repeat both checks immediately before the rename; the earlier full-tree
    # walk is only a preflight and cannot prove a path was not replaced while
    # the destination was being cleared.
    if not previous_is_safe():
        _quarantine_owned_slot(previous, destination, "previous", token)
        raise RuntimeError("Previous install changed identity during rollback; it was quarantined.")
    _rename(previous, destination)
    if (
        not _same_identity(_filesystem_identity(destination), previous_identity)
        or not _is_recognized_install_tree(destination)
    ):
        quarantined = _quarantine_unowned(destination)
        if quarantined is not None:
            _remove_path(marker)
        raise RuntimeError("Previous install changed during rollback; it was quarantined.")


def _new_slot(parent: Path, prefix: str) -> Path:
    """Choose an unoccupied per-run fallback slot without touching fixed names."""
    for _ in range(100):
        candidate = parent / f".{PRODUCT_NAME}.{prefix}-{uuid.uuid4().hex}"
        if not _path_exists(candidate) and not _path_exists(_marker_path(candidate)):
            return candidate
    raise RuntimeError(f"Could not allocate a transient {prefix} path in {parent}")


def _quarantine_unowned(path: Path) -> Path | None:
    """Move an unowned fixed path aside, preserving its bytes/link target.

    Quarantine is intentionally a rename, never recursive deletion. If the
    filesystem cannot move the path, the caller uses a unique transient slot
    and leaves the unowned path untouched.
    """
    if not _path_exists(path):
        return None
    parent = path.parent
    for _ in range(100):
        candidate = parent / f"{path.name}.unowned-{uuid.uuid4().hex}"
        if _path_exists(candidate):
            continue
        try:
            _rename(path, candidate)
        except OSError:
            return None
        return candidate
    return None


def _recover_previous(
    previous: Path,
    destination: Path,
) -> tuple[bool, Path | None]:
    """Preserve an interrupted previous tree and return a rollback candidate."""
    if not _path_exists(previous) and not _path_exists(_marker_path(previous)):
        return False, None

    # A legacy/interrupted tree with a real SKILL.md is recognizable as a
    # possible prior install, but a persistent marker is forgeable and is not
    # current-run ownership. Preserve both tree and marker by quarantine. A
    # fresh exact install can then restore service without deleting either.
    # Validate the complete tree before it can become a rollback candidate;
    # checking only SKILL.md would allow an unsafe child redirect to survive
    # the recovery boundary.
    legacy_install_shape = _is_recognized_install_tree(previous)

    # A fixed path with no verifiable ownership must not be deleted. Move it
    # aside when possible so the installer can continue using a per-run slot.
    recovered = _quarantine_unowned(previous)
    _quarantine_unowned(_marker_path(previous))
    return legacy_install_shape, recovered if legacy_install_shape else None


def _restore_recovered_previous(recovered: Path | None, destination: Path) -> None:
    """Restore a recognized interrupted install when activation cannot complete."""
    if recovered is None or not _path_exists(recovered) or _path_exists(destination):
        return
    if not _is_recognized_install_tree(recovered):
        return
    _reject_reparse_chain(destination, "Destination")
    _rename(recovered, destination)


def _validate_activated_tree(destination: Path) -> None:
    """Recheck the final object after path-based activation before reporting success."""
    _reject_reparse_chain(destination, "Destination")
    if not destination.is_dir() or destination.is_symlink():
        raise RuntimeError("Activated destination is not a regular directory.")
    _validate_source_tree(destination)
    if not _has_product_identity(destination / "SKILL.md"):
        raise RuntimeError("Activated destination is missing valid Snowe SKILL.md frontmatter.")


def _claim_slot(
    fixed: Path,
    destination: Path,
    role: str,
    token: str,
) -> Path:
    """Claim a fixed transient name or fall back without deleting foreign state."""
    marker = _marker_path(fixed)
    if _path_exists(fixed) or _path_exists(marker):
        _quarantine_unowned(fixed)
        _quarantine_unowned(marker)

    if _path_exists(fixed) or _path_exists(marker):
        slot = _new_slot(fixed.parent, role)
    else:
        slot = fixed
    _write_owner_marker(slot, destination, role, token)
    return slot


def _validated_paths(source: str | Path, destination: str | Path) -> tuple[Path, Path]:
    # Preserve the caller's lexical source path until the complete reparse
    # chain has been checked. Resolving first would erase a source-root
    # junction/symlink and could make an external tree look self-contained.
    source_lexical = Path(os.path.abspath(os.fspath(Path(source).expanduser())))
    _reject_reparse_chain(source_lexical, "Skill source")
    source_path = _normalize_lexical_aliases(source_lexical, "Skill source")
    _reject_reparse_chain(source_lexical, "Skill source")
    _reject_reparse_chain(source_path, "Skill source")
    destination_lexical = Path(os.path.abspath(os.fspath(Path(destination).expanduser())))
    if not source_path.is_dir() or not _has_product_identity(source_path / "SKILL.md"):
        raise ValueError(
            f"Skill source must be a directory containing a valid Snowe SKILL.md: {source_path}"
        )
    _validate_source_tree(source_path)
    _reject_reparse_chain(destination_lexical, "Destination")
    # Expand Windows 8.3 spellings without resolving junction/symlink targets,
    # then recheck both spellings to close a redirect inserted during lookup.
    destination_path = _normalize_lexical_aliases(destination_lexical, "Destination")
    _reject_reparse_chain(destination_lexical, "Destination")
    _reject_reparse_chain(destination_path, "Destination")
    if os.path.normcase(destination_path.name) != os.path.normcase(PRODUCT_NAME):
        raise ValueError(f"Destination must end with {PRODUCT_NAME!r}: {destination_lexical}")
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
    _reject_reparse_chain(destination_path, "Destination")
    with _installation_lock(destination_path.parent):
        _reject_reparse_chain(destination_path, "Destination")
        return _install_skill_locked(source_path, destination_path)


def _install_skill_locked(source_path: Path, destination_path: Path) -> dict[str, str]:
    """Perform one serialized swap after lexical path validation."""
    fixed_staging = destination_path.parent / f".{PRODUCT_NAME}.installing"
    fixed_previous = destination_path.parent / f".{PRODUCT_NAME}.previous"
    token = uuid.uuid4().hex

    staging = _claim_slot(fixed_staging, destination_path, "staging", token)
    try:
        # Bind the marker to a directory created by this run before copytree
        # can leave partial bytes behind.  Cleanup can then distinguish that
        # object from a path replaced by another writer.
        staging.mkdir()
        _bind_owner_slot(
            staging,
            destination_path,
            "staging",
            token,
            expected_identity=_filesystem_identity(staging),
        )
        _reject_reparse_chain(source_path, "Skill source")
        _validate_source_tree(source_path)
        shutil.copytree(source_path, staging, symlinks=True, dirs_exist_ok=True, ignore=COPY_IGNORE)
        # Revalidate the copied bytes immediately before activation. This
        # closes the source-change window between the initial walk and copy;
        # a redirect introduced concurrently cannot enter the installed tree.
        _validate_source_tree(staging)
    except BaseException:
        _remove_owned_slot(staging, destination_path, "staging", token)
        raise
    if not _has_product_identity(staging / "SKILL.md"):
        _remove_owned_slot(staging, destination_path, "staging", token)
        raise RuntimeError(
            "Staged install is missing valid Snowe SKILL.md frontmatter; destination was not changed."
        )

    # Do not quarantine a previous interrupted tree until staging has succeeded.
    # A failed copy must leave the only recoverable install in place.  Once the
    # replacement is complete, a recognized prior tree remains available as a
    # rollback candidate until activation has passed its final validation.
    legacy_previous = False
    recovered_previous: Path | None = None
    destination_was_present = _path_exists(destination_path)
    destination_identity: dict[str, int] | None = None
    try:
        if destination_was_present and not _is_recognized_install_tree(destination_path):
            _remove_owned_slot(staging, destination_path, "staging", token)
            raise ValueError(
                "Destination already exists but is not a recognized Snowe install; "
                f"refusing to replace it: {destination_path}"
            )
        if destination_was_present:
            destination_identity = _filesystem_identity(destination_path)
            if destination_identity is None:
                _remove_owned_slot(staging, destination_path, "staging", token)
                raise ValueError(
                    "Destination has no stable filesystem identity; refusing to replace it: "
                    f"{destination_path}"
                )
        legacy_previous, recovered_previous = _recover_previous(fixed_previous, destination_path)
        operation = "updated" if destination_was_present or legacy_previous else "installed"
        previous = _claim_slot(fixed_previous, destination_path, "previous", token)
    except BaseException:
        _remove_owned_slot(staging, destination_path, "staging", token)
        _restore_recovered_previous(recovered_previous, destination_path)
        raise

    moved_previous = False
    moved_staging = False
    try:
        _reject_reparse_chain(destination_path, "Destination")
        staging_identity = _owned_identity(staging, destination_path, "staging", token)
        if not _owns_path(staging, destination_path, "staging", token):
            _remove_owned_slot(staging, destination_path, "staging", token)
            if _path_exists(staging):
                _quarantine_unowned(staging)
            raise ValueError(
                "Staged install changed identity before activation; refusing to activate an unverified path: "
                f"{staging}"
            )
        current_destination_exists = _path_exists(destination_path)
        if destination_was_present:
            if (
                not current_destination_exists
                or not _same_identity(_filesystem_identity(destination_path), destination_identity)
                or not _is_recognized_install_tree(destination_path)
            ):
                raise ValueError(
                    "Destination changed before activation; refusing to replace an unverified path: "
                    f"{destination_path}"
                )
            previous_source_identity = destination_identity
            _rename(destination_path, previous)
            moved_previous = True
            _bind_owner_slot(
                previous,
                destination_path,
                "previous",
                token,
                expected_identity=previous_source_identity,
            )
        elif current_destination_exists:
            raise ValueError(
                "Destination appeared before activation; refusing to replace an unverified path: "
                f"{destination_path}"
            )
        _rename(staging, destination_path)
        moved_staging = True
        if not _same_identity(_filesystem_identity(destination_path), staging_identity):
            raise ValueError(
                "Activated destination changed identity or became a symlink, junction, or reparse point."
            )
        _validate_activated_tree(destination_path)
    except BaseException:
        if moved_staging and _path_exists(destination_path):
            _remove_owned_object(
                destination_path,
                staging,
                destination_path,
                "staging",
                token,
            )
        _remove_owned_slot(staging, destination_path, "staging", token)
        if moved_previous and _path_exists(previous):
            _restore_owned_previous(previous, destination_path, token)
        else:
            _restore_recovered_previous(recovered_previous, destination_path)
        _remove_owned_slot(previous, destination_path, "previous", token)
        raise

    # The staging marker remains at its old sidecar name after activation;
    # remove both the transient tree and marker only after the swap succeeds.
    _remove_owned_slot(staging, destination_path, "staging", token)
    _remove_owned_slot(previous, destination_path, "previous", token)
    return {
        "operation": operation,
        "source": str(source_path),
        "destination": str(destination_path),
    }


def _migration_fingerprint(root: Path) -> dict[str, str]:
    _validate_source_tree(root)
    # Include personal files and caches: migration preserves the complete old tree.
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob("*") if path.is_file()}


def diagnose_installations(destination=DEFAULT_DESTINATION, legacy=None):
    legacy = Path(legacy) if legacy else Path.home() / ".codex/skills" / PRODUCT_NAME
    paths = list(dict.fromkeys([Path(destination).absolute(), legacy.absolute()]))
    copies = []
    for path in paths:
        _reject_reparse_chain(path, "Installed skill")
        copies.append({"path": str(path), "exists": path.exists(), "recognized": _is_recognized_install_tree(path) if path.exists() else False})
    return {"copies": copies, "duplicates": sum(item["recognized"] for item in copies) > 1}


def _migration_archives(backup_root: Path, legacy: Path):
    """Recover the archive location after a process dies immediately following rename."""
    if not backup_root.exists(): return []
    _reject_reparse_chain(backup_root, "Migration backups")
    found = []
    for manifest in backup_root.glob(f"{PRODUCT_NAME}-*.migration.json"):
        _reject_reparse_chain(manifest, "Migration record")
        if not manifest.is_file() or manifest.stat().st_size > 1_000_000: raise ValueError("Invalid migration record")
        record = json.loads(manifest.read_text(encoding="utf-8"))
        if not isinstance(record, dict) or record.get("schema_version") != "1.0" or not isinstance(record.get("files"), dict):
            raise ValueError("Invalid migration record schema")
        archive = manifest.with_name(manifest.name.removesuffix(".migration.json"))
        if record.get("legacy") == str(legacy) and archive.exists():
            if _migration_fingerprint(archive) != record.get("files"): raise ValueError("Migration archive changed; preserve it for manual review")
            found.append(str(archive))
    return sorted(found)


def migrate_legacy(source=DEFAULT_SOURCE, destination=DEFAULT_DESTINATION, legacy=None, backup_root=None):
    """Install the canonical copy, then archive a verified legacy tree without deleting it."""
    source, destination = _validated_paths(source, destination)
    legacy = Path(os.path.abspath(legacy or Path.home() / ".codex/skills" / PRODUCT_NAME))
    backup_root = Path(os.path.abspath(backup_root or Path.home() / ".agents/skill-backups"))
    for candidate in (legacy, backup_root): _reject_reparse_chain(candidate, "Migration path")
    legacy = _normalize_lexical_aliases(legacy, "Legacy skill")
    backup_root = _normalize_lexical_aliases(backup_root, "Migration backups")
    if legacy.is_relative_to(destination) or destination.is_relative_to(legacy) or legacy.name != PRODUCT_NAME or source.is_relative_to(legacy) or legacy.is_relative_to(source):
        raise ValueError("Legacy must be a separate Snowe install")
    if any(backup_root == path or backup_root.is_relative_to(path) or path.is_relative_to(backup_root) for path in (source, destination.parent, legacy.parent)):
        raise ValueError("Backups must be outside source and both discovery directories")
    if legacy.exists() and not _is_recognized_install_tree(legacy): raise ValueError("Legacy is not a regular Snowe install")
    installed = install_skill(source, destination)
    if not legacy.exists(): return {**installed, "migration": "already-absent", "archives": _migration_archives(backup_root, legacy)}
    backup_root.mkdir(parents=True, exist_ok=True)
    _reject_reparse_chain(backup_root, "Migration backups")
    # Lock the same legacy parent used by its installer to avoid a concurrent update.
    with _installation_lock(legacy.parent):
        _reject_reparse_chain(legacy, "Legacy skill")
        if not legacy.exists(): return {**installed, "migration": "already-absent", "archives": _migration_archives(backup_root, legacy)}
        if not _is_recognized_install_tree(legacy): raise ValueError("Legacy changed before migration")
        before = _migration_fingerprint(legacy)
        identity = _filesystem_identity(legacy)
        backup = backup_root / f"{PRODUCT_NAME}-{uuid.uuid4().hex}"
        # All recursive paths are resolved/checked above; rename moves the complete tree atomically.
        record = backup.with_suffix(".migration.json")
        with record.open("x", encoding="utf-8") as handle:
            json.dump({"schema_version": "1.0", "legacy": str(legacy), "canonical": str(destination), "backup": str(backup), "files": before}, handle, indent=2)
            handle.flush(); os.fsync(handle.fileno())
        moved = False
        try:
            _reject_reparse_chain(legacy, "Legacy skill")
            _reject_reparse_chain(backup_root, "Migration backups")
            if not _same_identity(_filesystem_identity(legacy), identity) or _migration_fingerprint(legacy) != before:
                raise ValueError("Legacy changed before archival")
            _rename(legacy, backup)
            moved = True
            if not _same_identity(_filesystem_identity(backup), identity) or _migration_fingerprint(backup) != before:
                raise ValueError("Archived bytes or identity differ")
        except BaseException:
            if moved and not _path_exists(legacy) and _same_identity(_filesystem_identity(backup), identity):
                _rename(backup, legacy)
            raise
        return {**installed, "migration": "archived", "backup": str(backup), "manifest": str(record)}


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
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--diagnose", action="store_true", help="Read-only duplicate installation report")
    mode.add_argument("--migrate-legacy", action="store_true", help="Archive legacy copy outside discovery after canonical install")
    parser.add_argument("--legacy", type=Path)
    parser.add_argument("--backup-root", type=Path)
    args = parser.parse_args()
    try:
        if (args.legacy or args.backup_root) and not (args.migrate_legacy or args.diagnose):
            raise ValueError("Migration options require --migrate-legacy or --diagnose")
        if args.diagnose:
            print(json.dumps(diagnose_installations(args.destination, args.legacy), indent=2))
            return 0
        result = migrate_legacy(destination=args.destination, legacy=args.legacy, backup_root=args.backup_root) if args.migrate_legacy else install_skill(destination=args.destination)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Install failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2) if args.migrate_legacy else f"Snowe {result['operation']}: {result['destination']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
