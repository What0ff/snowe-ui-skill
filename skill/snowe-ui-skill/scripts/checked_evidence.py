"""Shared bounded JSON and current-file evidence reads; no write operations."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat

from decision_packet import _reject_reparse_chain


def text(value, field):
    if not isinstance(value, str) or not value.strip() or len(value) > 8000 or not value.isprintable():
        raise ValueError(f"{field} must be nonempty printable text")
    return value


def object_fields(value, required, optional=()):
    if not isinstance(value, dict) or not set(required) <= value.keys() or set(value) - set(required) - set(optional):
        raise ValueError(f"Expected fields {sorted(required)} with optional {sorted(optional)}")


def read_json(path):
    path = Path(path)
    _reject_reparse_chain(path, "JSON input")
    if not path.is_file() or path.stat().st_size > 1_000_000:
        raise ValueError("JSON input must be a regular file of at most 1 MB")
    try:
        value = json.loads(path.read_text(encoding="utf-8"), parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))
    except (RecursionError, UnicodeError) as error:
        raise ValueError("Invalid or excessive JSON") from error
    def bounded(node, depth=0):
        if depth > 32:
            raise ValueError("JSON nesting exceeds 32")
        if isinstance(node, dict):
            for child in node.values(): bounded(child, depth + 1)
        elif isinstance(node, list):
            for child in node: bounded(child, depth + 1)
    bounded(value)
    return value


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
