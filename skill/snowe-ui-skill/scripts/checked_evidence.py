"""Shared bounded JSON and current-file evidence reads; no write operations."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat

from decision_packet import _reject_reparse_chain, _resolve_selected_file


def text(value, field):
    if not isinstance(value, str) or not value.strip() or len(value) > 8000 or not value.isprintable():
        raise ValueError(f"{field} must be nonempty printable text")
    return value


def object_fields(value, required, optional=(), *, name="object"):
    """Require exactly the declared fields; errors name the object, missing and unexpected keys."""
    label = name[:1].upper() + name[1:]
    expected = f"expected {sorted(required)}" + (f" with optional {sorted(optional)}" if optional else "")
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object, not {type(value).__name__}; {expected}")
    missing = set(required) - value.keys()
    extra = value.keys() - set(required) - set(optional)
    if missing or extra:
        identity = value.get("id")
        if isinstance(identity, str) and identity.strip():
            label += f" {identity[:80]!r}"
        problems = ([f"is missing {sorted(missing)}"] if missing else []) + ([f"has unexpected {sorted(map(str, extra))}"] if extra else [])
        raise ValueError(f"{label} {' and '.join(problems)}; {expected}")


def _reject_nonfinite(constant):
    raise ValueError(f"nonfinite number {constant} is not valid JSON")


def read_json(path, *, max_bytes=1_000_000):
    """Read bounded UTF-8 JSON (a UTF-8 BOM is accepted); errors name the file."""
    path = Path(path)
    _reject_reparse_chain(path, "JSON input")
    try:
        information = path.stat()
    except FileNotFoundError:
        raise ValueError(f"JSON input does not exist: {path}") from None
    except OSError as error:
        raise ValueError(f"JSON input cannot be inspected: {path} ({error.strerror or error})") from None
    if not stat.S_ISREG(information.st_mode):
        raise ValueError(f"JSON input must be a regular file: {path}")
    if information.st_size > max_bytes:
        raise ValueError(f"JSON input exceeds {max_bytes} bytes: {path} ({information.st_size} bytes)")
    with path.open("rb") as handle:
        raw = handle.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise ValueError(f"JSON input exceeds {max_bytes} bytes: {path}")
    # UTF-8 JSON never contains NUL bytes; UTF-16/32 text (Windows PowerShell 5.1's default
    # for > and Out-File) does, with or without a byte-order mark.
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")) or b"\x00" in raw:
        raise ValueError(
            f"JSON input must be UTF-8 text, but {path} looks like UTF-16 or UTF-32; "
            "re-save it as UTF-8 (for example Out-File -Encoding utf8, or Set-Content -Encoding utf8)"
        )
    try:
        decoded = raw.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValueError(
            f"JSON input must be UTF-8 text: {path} has a byte that is not UTF-8 at offset {error.start}"
        ) from None
    try:
        value = json.loads(decoded, parse_constant=_reject_nonfinite)
    except RecursionError:
        raise ValueError(f"Invalid JSON in {path}: nesting is too deep") from None
    except ValueError as error:
        raise ValueError(f"Invalid JSON in {path}: {error}") from None
    def bounded(node, depth=0):
        if depth > 32:
            raise ValueError("JSON nesting exceeds 32")
        if isinstance(node, dict):
            for child in node.values(): bounded(child, depth + 1)
        elif isinstance(node, list):
            for child in node: bounded(child, depth + 1)
    bounded(value)
    return value


def read_selected_json(path, *, max_bytes=1_000_000):
    """Read a caller-named JSON file (a CLI argument), resolving its directory once.

    Redirected ancestors such as macOS /tmp are resolved; the file itself must
    still be a regular file, not a symlink, junction or reparse point.
    """
    return read_json(_resolve_selected_file(path, "JSON input"), max_bytes=max_bytes)


def file_digest(root, relative):
    text(relative, "evidence path")
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or path.drive or ":" in relative:
        raise ValueError("Evidence paths must remain relative to the workspace")
    path = root / path
    _reject_reparse_chain(path, "Evidence")
    before = path.stat()
    if not stat.S_ISREG(before.st_mode): raise ValueError("Evidence must be a regular file")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        opened = os.fstat(handle.fileno())
        if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino): raise ValueError("Evidence changed before reading")
        for chunk in iter(lambda: handle.read(65536), b""): digest.update(chunk)
        after = os.fstat(handle.fileno())
    _reject_reparse_chain(path, "Evidence")
    current = path.stat()
    if (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) != (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns) or opened.st_mtime_ns != after.st_mtime_ns:
        raise ValueError("Evidence changed during reading")
    return digest.hexdigest()
