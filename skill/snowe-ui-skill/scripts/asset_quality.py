#!/usr/bin/env python3
"""Deterministic structural QA for repository-owned SVG interface icons.

This validator checks a compact self-contained SVG subset, painted finite
geometry inside the declared bounds, drawing-language consistency, and exact
provenance binding. Recognition and optical/UI quality still require rendered
human comparison against existing and no-icon alternatives.
"""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import math
import os
import re
import stat
import sys
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


SVG_NAMESPACE = "http://www.w3.org/2000/svg"
XML_NAMESPACE = "http://www.w3.org/XML/1998/namespace"
REQUIRED_METADATA = {
    "name", "asset_type", "role", "grid", "live_area", "drawing_language",
    "target_sizes", "source", "license", "accessibility_owner", "provenance", "evidence",
}
REQUIRED_DRAWING_LANGUAGE = {
    "mode", "stroke_width", "linecap", "linejoin", "corner_language", "detail_budget",
}
REQUIRED_PROVENANCE = {"kind", "creator", "source_ref", "reviewed", "sha256"}
REQUIRED_EVIDENCE = {"source", "license"}
TEXT_METADATA = {"name", "role", "source", "license", "accessibility_owner"}
TEXT_DRAWING_LANGUAGE = {"mode", "linecap", "linejoin", "corner_language", "detail_budget"}
SAFE_ELEMENTS = {
    "svg", "g", "title", "desc", "path", "circle", "ellipse", "rect", "line",
    "polyline", "polygon",
}
GEOMETRY_ELEMENTS = {"path", "circle", "ellipse", "rect", "line", "polyline", "polygon"}
PAINT_ATTRIBUTES = {"fill", "stroke", "color", "stop-color", "flood-color", "lighting-color"}
SAFE_PAINT = {"none", "currentcolor", "transparent"}
PLACEHOLDERS = {"", "-", "n/a", "na", "none", "not provided", "tbd", "todo", "unknown", "unspecified"}
LINECAPS = {"butt", "round", "square", "not applicable"}
LINEJOINS = {"arcs", "bevel", "round", "not applicable"}
EVENT_HANDLER = re.compile(r"^on[a-z0-9_:-]+$", re.IGNORECASE)
CSS_URL = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.IGNORECASE)
UNSAFE_CSS = re.compile(r"(?:@import\b|expression\s*\(|(?:java|vb)script\s*:)", re.IGNORECASE)
UNSAFE_DECLARATION = re.compile(r"(?:<!\s*(?:DOCTYPE|ENTITY)\b|<\?xml-stylesheet\b)", re.IGNORECASE)
PREFIXED_NAMESPACE_DECLARATION = re.compile(r"\bxmlns:[A-Za-z_][\w.-]*\s*=", re.IGNORECASE)
NUMBER = r"[-+]?(?:(?:\d+(?:\.\d*)?)|(?:\.\d+))(?:[eE][-+]?\d+)?"
NUMBER_RE = re.compile(rf"^{NUMBER}$")
PATH_TOKEN_RE = re.compile(rf"[AaCcHhLlMmQqSsTtVvZz]|{NUMBER}")
PATH_ARITY = {"a": 7, "c": 6, "h": 1, "l": 2, "m": 2, "q": 4, "s": 4, "t": 2, "v": 1, "z": 0}
MAX_SVG_BYTES = 1_000_000
MAX_SVG_DEPTH = 64
MAX_SVG_NODES = 2_048
MAX_SAFE_ARC_MAGNITUDE = 1_000_000.0
MAX_JSON_BYTES = 1_000_000
MAX_JSON_DEPTH = 128
COMMON_ATTRIBUTES = {
    "display", "fill", "fill-opacity", "opacity", "stroke", "stroke-linecap",
    "stroke-linejoin", "stroke-opacity", "stroke-width", "visibility",
}
ELEMENT_ATTRIBUTES = {
    "svg": {"height", "preserveaspectratio", "viewbox", "width"},
    "g": set(),
    "title": set(),
    "desc": set(),
    "path": {"d"},
    "circle": {"cx", "cy", "r"},
    "ellipse": {"cx", "cy", "rx", "ry"},
    "rect": {"height", "rx", "ry", "width", "x", "y"},
    "line": {"x1", "x2", "y1", "y2"},
    "polyline": {"points"},
    "polygon": {"points"},
}

Bounds = tuple[float, float, float, float]


class AssetValidationError(ValueError):
    """Raised when an asset input cannot be inspected within the validator contract."""


def _is_reparse_path(path: Path) -> bool:
    try:
        information = os.lstat(path)
    except FileNotFoundError:
        return False
    except (OSError, ValueError) as error:
        raise AssetValidationError(f"Path cannot be inspected safely: {path}: {error}") from error
    attributes = getattr(information, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return stat.S_ISLNK(information.st_mode) or bool(attributes & reparse_flag)


def _reparse_in_chain(path: Path) -> Path | None:
    try:
        current = Path(os.path.abspath(os.fspath(path)))
    except (OSError, ValueError) as error:
        raise AssetValidationError(f"Path cannot be inspected safely: {path}: {error}") from error
    while True:
        if _is_reparse_path(current):
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _namespace(tag: str) -> str | None:
    return tag[1:].split("}", 1)[0] if tag.startswith("{") and "}" in tag else None


def _finite(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        number = float(value)
    except (OverflowError, ValueError) as error:
        raise AssetValidationError(
            "Numeric metadata value cannot be represented safely as a finite number."
        ) from error
    return number if math.isfinite(number) else None


def _positive(value: Any) -> float | None:
    number = _finite(value)
    return number if number is not None and number > 0 else None


def _svg_number(value: str | None, default: float | None = None) -> float | None:
    if value is None:
        return default
    text = value.strip()
    if not NUMBER_RE.fullmatch(text):
        return None
    number = float(text)
    return number if math.isfinite(number) else None


def _root_dimension(value: str | None) -> float | None:
    if value is None:
        return None
    match = re.fullmatch(rf"\s*({NUMBER})(?:px)?\s*", value, re.IGNORECASE)
    if not match:
        return math.nan
    number = float(match.group(1))
    return number if math.isfinite(number) and number > 0 else math.nan


def _view_box(value: str | None) -> tuple[float, float, float, float] | None:
    if not value:
        return None
    parts = re.split(r"[\s,]+", value.strip())
    if len(parts) != 4:
        return None
    try:
        numbers = tuple(float(part) for part in parts)
    except ValueError:
        return None
    if not all(math.isfinite(number) for number in numbers) or numbers[2] <= 0 or numbers[3] <= 0:
        return None
    return numbers  # type: ignore[return-value]


def _grid(value: Any) -> tuple[float, float] | None:
    number = _positive(value)
    if number is not None:
        return number, number
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*(?:x|×)\s*(\d+(?:\.\d+)?)\s*", value, re.I)
    if not match:
        return None
    width, height = (float(part) for part in match.groups())
    return (width, height) if width > 0 and height > 0 else None


def _live_area(value: Any) -> Bounds | None:
    keys = ("min_x", "min_y", "max_x", "max_y")
    if not isinstance(value, dict) or set(value) != set(keys):
        return None
    values = [_finite(value[key]) for key in keys]
    if any(item is None for item in values):
        return None
    min_x, min_y, max_x, max_y = (float(item) for item in values if item is not None)
    return (min_x, min_y, max_x, max_y) if min_x < max_x and min_y < max_y else None


def _meaningful(value: Any) -> bool:
    return isinstance(value, str) and value.strip().casefold() not in PLACEHOLDERS


def _json_tree_error(value: Any, label: str) -> str | None:
    """Reject non-scalar JSON values that Python's permissive decoder accepts."""
    pending: list[tuple[Any, int]] = [(value, 0)]
    while pending:
        current, depth = pending.pop()
        if depth > MAX_JSON_DEPTH:
            return f"{label} exceeds the deterministic {MAX_JSON_DEPTH}-level JSON nesting limit."
        if isinstance(current, str):
            if any(0xD800 <= ord(character) <= 0xDFFF for character in current):
                return f"{label} contains unpaired Unicode surrogate code points."
        elif isinstance(current, float) and not math.isfinite(current):
            return f"{label} contains a non-finite JSON number."
        elif isinstance(current, dict):
            for key, child in current.items():
                if any(0xD800 <= ord(character) <= 0xDFFF for character in key):
                    return f"{label} contains unpaired Unicode surrogate code points."
                pending.append((child, depth + 1))
        elif isinstance(current, list):
            pending.extend((child, depth + 1) for child in current)
    return None


def _canonical_https_url(value: Any) -> bool:
    """Accept only a stable, authority-bearing HTTPS source URL."""
    if not isinstance(value, str) or not value or value != value.strip():
        return False
    if any(character == "\\" or ord(character) < 0x21 or ord(character) == 0x7F for character in value):
        return False
    try:
        parsed = urlsplit(value)
        host = parsed.hostname
        port = parsed.port
    except ValueError:
        return False
    if parsed.scheme.casefold() != "https" or not parsed.netloc or not host:
        return False
    authority = parsed.netloc.rsplit("@", 1)[-1]
    if (
        parsed.username is not None
        or parsed.password is not None
        or port is not None
        or authority.endswith(":")
        or parsed.fragment
    ):
        return False
    if re.search(r"%(?![0-9A-Fa-f]{2})", parsed.path + parsed.query):
        return False
    try:
        ipaddress.ip_address(host)
    except ValueError:
        try:
            ascii_host = host.encode("idna").decode("ascii")
        except UnicodeError:
            return False
        if len(ascii_host) > 253 or ascii_host.endswith("."):
            return False
        labels = ascii_host.split(".")
        if any(
            not label
            or len(label) > 63
            or not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?", label)
            for label in labels
        ):
            return False
    return True


def _validate_provenance(value: Any, errors: list[str]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        errors.append("provenance must be an object bound to the exact SVG source.")
        return None
    missing = sorted(REQUIRED_PROVENANCE - set(value))
    extra = sorted(set(value) - REQUIRED_PROVENANCE)
    if missing:
        errors.append("provenance is missing required fields: " + ", ".join(missing))
    if extra:
        errors.append("provenance contains unsupported fields: " + ", ".join(extra))
    kind = str(value.get("kind", "")).strip().casefold()
    if kind not in {"original", "external"}:
        errors.append("provenance.kind must be 'original' or 'external'.")
    for field in ("creator", "source_ref"):
        if not _meaningful(value.get(field)):
            errors.append(f"provenance.{field} must be a specific non-placeholder string.")
    if kind == "external":
        if not _canonical_https_url(value.get("source_ref")):
            errors.append("External provenance.source_ref must be a canonical HTTPS source URL.")
    try:
        reviewed = date.fromisoformat(str(value.get("reviewed", "")).strip())
    except ValueError:
        errors.append("provenance.reviewed must be an ISO date (YYYY-MM-DD).")
    else:
        if reviewed > date.today():
            errors.append("provenance.reviewed must not claim a future review date.")
    if not re.fullmatch(r"[0-9a-f]{64}", str(value.get("sha256", ""))):
        errors.append("provenance.sha256 must be a 64-character lowercase hexadecimal digest.")
    return value


def _evidence_file(
    metadata_path: Path,
    value: Any,
    field: str,
    errors: list[str],
) -> tuple[Path | None, str | None]:
    if not isinstance(value, dict):
        errors.append(f"{field} must be an object with a metadata-relative path and SHA-256 digest.")
        return None, None
    if set(value) != {"path", "sha256"}:
        errors.append(f"{field} must contain exactly path and sha256 fields.")
        return None, None
    path_value = value.get("path")
    digest_value = value.get("sha256")
    if not isinstance(path_value, str) or not path_value.strip():
        errors.append(f"{field}.path must be a non-empty metadata-relative local path.")
        return None, None
    path_text = path_value.strip()
    path_object = Path(path_text)
    if (
        path_object.is_absolute()
        or bool(path_object.drive)
        or bool(path_object.root)
        or path_text.startswith(("/", "\\"))
        or re.match(r"^[A-Za-z]:", path_text)
        or "://" in path_text
        or "#" in path_text
        or "\x00" in path_text
    ):
        errors.append(f"{field}.path must be a metadata-relative local path without a fragment.")
        return None, None
    if not re.fullmatch(r"[0-9a-f]{64}", str(digest_value)):
        errors.append(f"{field}.sha256 must be a 64-character lowercase hexadecimal digest.")
        return None, None
    try:
        lexical = Path(os.path.abspath(os.fspath(metadata_path.parent / path_text)))
    except (OSError, ValueError) as error:
        errors.append(f"{field}.path cannot be inspected safely: {error}")
        return None, None
    try:
        redirect = _reparse_in_chain(lexical)
    except AssetValidationError as error:
        errors.append(f"{field}.path cannot be inspected safely: {error}")
        return None, None
    if redirect is not None:
        errors.append(f"{field}.path must resolve through regular non-reparse files: {redirect}")
        return None, None
    try:
        resolved = lexical.resolve(strict=True)
        information = resolved.stat()
        if not stat.S_ISREG(information.st_mode):
            errors.append(f"{field}.path must resolve to a regular file: {resolved}")
            return None, None
        content = resolved.read_bytes()
    except (FileNotFoundError, OSError, RuntimeError, ValueError) as error:
        errors.append(f"{field}.path file cannot be read: {lexical}: {error}")
        return None, None
    actual = hashlib.sha256(content).hexdigest()
    if actual != digest_value:
        errors.append(f"{field}.sha256 does not match the exact local evidence bytes.")
    return resolved, actual


def _validate_evidence(
    metadata: dict[str, Any],
    metadata_path: Path | None,
    provenance: dict[str, Any] | None,
    errors: list[str],
) -> None:
    evidence = metadata.get("evidence")
    if not isinstance(evidence, dict):
        errors.append("evidence must be an object containing structured source and license bindings.")
        return
    if set(evidence) != REQUIRED_EVIDENCE:
        missing = sorted(REQUIRED_EVIDENCE - set(evidence))
        extra = sorted(set(evidence) - REQUIRED_EVIDENCE)
        if missing:
            errors.append("evidence is missing required fields: " + ", ".join(missing) + ".")
        if extra:
            errors.append("evidence contains unsupported fields: " + ", ".join(extra) + ".")
    if metadata_path is None:
        errors.append("evidence requires a companion metadata file path.")
        return
    provenance_kind = str((provenance or {}).get("kind", "")).strip().casefold()
    source = evidence.get("source")
    if not isinstance(source, dict):
        errors.append("evidence.source must declare local or external source evidence.")
    else:
        source_kind = str(source.get("kind", "")).strip().casefold()
        if source_kind == "local":
            allowed = {"kind", "path", "sha256", "locator"}
            if set(source) - allowed or not {"kind", "path", "sha256"}.issubset(source):
                errors.append("evidence.source local binding must contain kind, path, sha256, and optional locator.")
            locator = source.get("locator")
            if locator is not None and (
                not isinstance(locator, str) or not locator.strip().startswith("#") or "\n" in locator or "\r" in locator
            ):
                errors.append("evidence.source.locator must be an optional fragment locator beginning with '#'.")
            _evidence_file(
                metadata_path,
                {"path": source.get("path"), "sha256": source.get("sha256")},
                "evidence.source",
                errors,
            )
        elif source_kind == "external":
            if set(source) != {"kind", "verification"} or source.get("verification") != "unverified":
                errors.append("evidence.source external binding must explicitly declare verification='unverified'.")
        else:
            errors.append("evidence.source.kind must be local or external.")
        expected_kind = "local" if provenance_kind == "original" else "external" if provenance_kind == "external" else ""
        if expected_kind and source_kind != expected_kind:
            errors.append(f"evidence.source.kind must be {expected_kind!r} for provenance.kind {provenance_kind!r}.")
    _evidence_file(metadata_path, evidence.get("license"), "evidence.license", errors)


def _validate_metadata(metadata: dict[str, Any], errors: list[str], metadata_path: Path | None = None) -> tuple[tuple[float, float] | None, Bounds | None, dict[str, Any] | None]:
    missing = sorted(REQUIRED_METADATA - set(metadata))
    extra = sorted(set(metadata) - REQUIRED_METADATA)
    if missing:
        errors.append("Metadata is missing required fields: " + ", ".join(missing))
    if extra:
        errors.append("Metadata contains unsupported fields that the validator cannot substantiate: " + ", ".join(extra))
    for field in sorted(TEXT_METADATA & set(metadata)):
        if not _meaningful(metadata[field]):
            errors.append(f"Metadata field {field!r} must be a specific non-placeholder string.")
    if metadata.get("asset_type") != "interface-icon":
        errors.append("asset_type must be exactly 'interface-icon'; free-form role wording cannot bypass icon checks.")

    grid = _grid(metadata.get("grid"))
    if grid is None:
        errors.append("grid must be a positive number or '<width> x <height>' string.")
    live_area = _live_area(metadata.get("live_area"))
    if live_area is None:
        errors.append("live_area must contain exactly finite min_x, min_y, max_x, and max_y values with positive area.")
    elif grid is not None and (live_area[0] < 0 or live_area[1] < 0 or live_area[2] > grid[0] or live_area[3] > grid[1]):
        errors.append("live_area must stay inside the declared grid.")

    language = metadata.get("drawing_language")
    if not isinstance(language, dict):
        errors.append("drawing_language must be an object.")
    else:
        language_missing = sorted(REQUIRED_DRAWING_LANGUAGE - set(language))
        if language_missing:
            errors.append("drawing_language is missing required fields: " + ", ".join(language_missing))
        for field in sorted(TEXT_DRAWING_LANGUAGE & set(language)):
            if not _meaningful(language[field]):
                errors.append(f"drawing_language field {field!r} must be a specific non-placeholder string.")
        mode = str(language.get("mode", "")).strip().casefold()
        width = _finite(language.get("stroke_width"))
        if mode not in {"fill", "stroke", "mixed"}:
            errors.append("drawing_language.mode must be fill, stroke, or mixed.")
        elif mode == "fill" and width != 0:
            errors.append("Fill drawing languages must declare stroke_width as 0.")
        elif mode in {"stroke", "mixed"} and (width is None or width <= 0):
            errors.append("Stroke and mixed drawing languages require a positive finite stroke_width.")
        cap = str(language.get("linecap", "")).strip().casefold()
        join = str(language.get("linejoin", "")).strip().casefold()
        if cap not in LINECAPS:
            errors.append("drawing_language.linecap is not a supported SVG line-cap value.")
        if join not in LINEJOINS:
            errors.append("drawing_language.linejoin is not a supported SVG line-join value.")
        if mode != "fill" and (cap == "not applicable" or join == "not applicable"):
            errors.append("Stroke and mixed modes require concrete linecap and linejoin values.")

    sizes = metadata.get("target_sizes")
    if not isinstance(sizes, list) or not sizes or any(_positive(size) is None for size in sizes):
        errors.append("target_sizes must be a non-empty array of positive finite numbers.")
    else:
        normalized = [float(size) for size in sizes]
        if len(set(normalized)) != len(normalized):
            errors.append("target_sizes must not contain duplicate values.")
        missing_sizes = [size for size in (16, 20, 24) if float(size) not in normalized]
        if missing_sizes:
            errors.append("Interface icon metadata must include 16, 20, and 24; missing: " + ", ".join(map(str, missing_sizes)))
        if grid is not None and isinstance(language, dict):
            declared_width = _positive(language.get("stroke_width"))
            if declared_width is not None and str(language.get("mode", "")).strip().casefold() in {"stroke", "mixed"}:
                rendered_width = declared_width * min(normalized) / max(grid)
                if rendered_width < 0.5:
                    errors.append(
                        "Declared stroke renders below the deterministic 0.5 CSS-pixel viability floor at the smallest target size."
                    )
    provenance = _validate_provenance(metadata.get("provenance"), errors)
    _validate_evidence(metadata, metadata_path, provenance, errors)
    return grid, live_area, provenance


def _load_metadata(path: Path | None) -> tuple[dict[str, Any], list[str]]:
    if path is None:
        return {}, ["A companion metadata JSON file is required."]
    try:
        if path.stat().st_size > MAX_JSON_BYTES:
            return {}, [f"Metadata JSON exceeds the deterministic {MAX_JSON_BYTES}-byte safety limit."]
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, [f"Metadata file not found: {path}"]
    except (OSError, UnicodeDecodeError) as error:
        return {}, [f"Metadata file cannot be read as UTF-8 JSON: {path}: {error}"]
    except json.JSONDecodeError as error:
        return {}, [f"Metadata is not valid JSON: {error}"]
    except ValueError as error:
        raise AssetValidationError(
            f"Metadata JSON cannot be parsed safely: {path}: {error}"
        ) from error
    except RecursionError:
        return {}, [f"Metadata JSON exceeds the deterministic {MAX_JSON_DEPTH}-level nesting limit."]
    tree_error = _json_tree_error(value, "Metadata JSON")
    if tree_error:
        return {}, [tree_error]
    return (value, []) if isinstance(value, dict) else ({}, ["Metadata root must be a JSON object."])


def _union(left: Bounds | None, right: Bounds) -> Bounds:
    if left is None:
        return right
    return min(left[0], right[0]), min(left[1], right[1]), max(left[2], right[2]), max(left[3], right[3])


def _expand(bounds: Bounds, amount: float) -> Bounds:
    return bounds[0] - amount, bounds[1] - amount, bounds[2] + amount, bounds[3] + amount


def _contains(container: Bounds, child: Bounds, tolerance: float = 1e-7) -> bool:
    return child[0] >= container[0] - tolerance and child[1] >= container[1] - tolerance and child[2] <= container[2] + tolerance and child[3] <= container[3] + tolerance


def _intersects(left: Bounds, right: Bounds) -> bool:
    return left[0] < right[2] and left[2] > right[0] and left[1] < right[3] and left[3] > right[1]


def _path_tokens(value: str) -> tuple[list[str], str | None]:
    tokens: list[str] = []
    cursor = 0
    for match in PATH_TOKEN_RE.finditer(value):
        if re.sub(r"[\s,]+", "", value[cursor:match.start()]):
            return [], f"invalid token near {value[cursor:match.start()]!r}"
        tokens.append(match.group(0))
        cursor = match.end()
    if re.sub(r"[\s,]+", "", value[cursor:]):
        return [], f"invalid trailing token {value[cursor:]!r}"
    return (tokens, None) if tokens else ([], "path data is empty")


def _arc_extrema(
    start: tuple[float, float],
    end: tuple[float, float],
    rx: float,
    ry: float,
    rotation: float,
    large_arc: float,
    sweep: float,
) -> list[tuple[float, float]]:
    """Return endpoints and exact x/y extrema for one SVG elliptical arc."""
    if rx == 0 or ry == 0 or start == end:
        return [start, end]
    rx, ry = abs(rx), abs(ry)
    if max(rx, ry, *(abs(value) for point in (start, end) for value in point)) > MAX_SAFE_ARC_MAGNITUDE:
        raise ArithmeticError("arc values exceed the deterministic safety envelope")
    phi = math.radians(rotation % 360)
    cos_phi, sin_phi = math.cos(phi), math.sin(phi)
    dx, dy = (start[0] - end[0]) / 2, (start[1] - end[1]) / 2
    x1p = cos_phi * dx + sin_phi * dy
    y1p = -sin_phi * dx + cos_phi * dy
    scale = x1p * x1p / (rx * rx) + y1p * y1p / (ry * ry)
    if scale > 1:
        factor = math.sqrt(scale)
        rx, ry = rx * factor, ry * factor
    numerator = max(0.0, rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p)
    denominator = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    coefficient = 0.0 if denominator == 0 else math.sqrt(numerator / denominator)
    if large_arc == sweep:
        coefficient = -coefficient
    cxp = coefficient * rx * y1p / ry
    cyp = -coefficient * ry * x1p / rx
    cx = cos_phi * cxp - sin_phi * cyp + (start[0] + end[0]) / 2
    cy = sin_phi * cxp + cos_phi * cyp + (start[1] + end[1]) / 2

    def vector_angle(left: tuple[float, float], right: tuple[float, float]) -> float:
        return math.atan2(left[0] * right[1] - left[1] * right[0], left[0] * right[0] + left[1] * right[1])

    unit_start = ((x1p - cxp) / rx, (y1p - cyp) / ry)
    unit_end = ((-x1p - cxp) / rx, (-y1p - cyp) / ry)
    theta = vector_angle((1.0, 0.0), unit_start)
    delta = vector_angle(unit_start, unit_end)
    if not sweep and delta > 0:
        delta -= math.tau
    elif sweep and delta < 0:
        delta += math.tau

    def on_arc(angle: float) -> bool:
        if delta >= 0:
            return (angle - theta) % math.tau <= delta + 1e-9
        return (theta - angle) % math.tau <= -delta + 1e-9

    candidates = [
        math.atan2(-ry * sin_phi, rx * cos_phi),
        math.atan2(-ry * sin_phi, rx * cos_phi) + math.pi,
        math.atan2(ry * cos_phi, rx * sin_phi),
        math.atan2(ry * cos_phi, rx * sin_phi) + math.pi,
    ]
    points = [start, end]
    for angle in candidates:
        if on_arc(angle):
            points.append(
                (
                    cx + rx * cos_phi * math.cos(angle) - ry * sin_phi * math.sin(angle),
                    cy + rx * sin_phi * math.cos(angle) + ry * cos_phi * math.sin(angle),
                )
            )
    return points


def _path_bounds(value: str | None) -> tuple[Bounds | None, str | None]:
    if value is None or not value.strip():
        return None, "path d must be non-empty"
    tokens, error = _path_tokens(value)
    if error:
        return None, error
    index = 0
    command: str | None = None
    current = (0.0, 0.0)
    start = (0.0, 0.0)
    bounds: Bounds | None = None
    has_segment = False
    previous_command: str | None = None
    cubic_control: tuple[float, float] | None = None
    quadratic_control: tuple[float, float] | None = None

    def include(points: list[tuple[float, float]]) -> None:
        nonlocal bounds
        xs, ys = [point[0] for point in points], [point[1] for point in points]
        bounds = _union(bounds, (min(xs), min(ys), max(xs), max(ys)))

    while index < len(tokens):
        if tokens[index].isalpha():
            command = tokens[index]
            index += 1
            if command.casefold() == "z":
                if current != start:
                    include([current, start])
                    has_segment = True
                current, command = start, None
                previous_command = "z"
                cubic_control = quadratic_control = None
                continue
        elif command is None:
            return None, "path data must begin with a command"
        assert command is not None
        lower, arity = command.casefold(), PATH_ARITY[command.casefold()]
        if index + arity > len(tokens) or any(item.isalpha() for item in tokens[index:index + arity]):
            return None, f"command {command} has incomplete parameters"
        raw_values = tokens[index:index + arity]
        if lower == "a" and (raw_values[3] not in {"0", "1"} or raw_values[4] not in {"0", "1"}):
            return None, "arc flags must use the exact SVG lexical forms 0 or 1"
        values = [float(item) for item in raw_values]
        if not all(math.isfinite(number) for number in values):
            return None, f"command {command} contains a non-finite number"
        index += arity
        relative, old = command.islower(), current
        point = lambda x, y: (old[0] + x, old[1] + y) if relative else (x, y)
        if lower == "m":
            current, command = point(values[0], values[1]), ("l" if relative else "L")
            start = current
        elif lower == "l":
            current = point(values[0], values[1]); include([old, current]); has_segment |= current != old
        elif lower == "h":
            current = ((old[0] + values[0]) if relative else values[0], old[1]); include([old, current]); has_segment |= current != old
        elif lower == "v":
            current = (old[0], (old[1] + values[0]) if relative else values[0]); include([old, current]); has_segment |= current != old
        elif lower == "c":
            points = [old, point(values[0], values[1]), point(values[2], values[3]), point(values[4], values[5])]
            current = points[-1]; cubic_control = points[-2]; include(points); has_segment |= len(set(points)) > 1
        elif lower == "s":
            reflected = (
                (2 * old[0] - cubic_control[0], 2 * old[1] - cubic_control[1])
                if previous_command in {"c", "s"} and cubic_control is not None
                else old
            )
            points = [old, reflected, point(values[0], values[1]), point(values[2], values[3])]
            current = points[-1]; cubic_control = points[-2]; include(points); has_segment |= len(set(points)) > 1
        elif lower == "q":
            points = [old, point(values[0], values[1]), point(values[2], values[3])]
            current = points[-1]; quadratic_control = points[-2]; include(points); has_segment |= len(set(points)) > 1
        elif lower == "t":
            reflected = (
                (2 * old[0] - quadratic_control[0], 2 * old[1] - quadratic_control[1])
                if previous_command in {"q", "t"} and quadratic_control is not None
                else old
            )
            current = point(values[0], values[1]); quadratic_control = reflected
            include([old, reflected, current]); has_segment |= len({old, reflected, current}) > 1
        elif lower == "a":
            rx, ry, rotation, large, sweep, x, y = values
            if rx < 0 or ry < 0 or large not in {0.0, 1.0} or sweep not in {0.0, 1.0}:
                return None, "arc radii must be non-negative and flags must be 0 or 1"
            current = point(x, y)
            try:
                arc_points = _arc_extrema(old, current, rx, ry, rotation, large, sweep)
            except ArithmeticError:
                return None, "arc geometry cannot be bounded safely"
            if not all(math.isfinite(coordinate) for arc_point in arc_points for coordinate in arc_point):
                return None, "arc geometry cannot be bounded safely"
            include(arc_points)
            has_segment |= rx > 0 and ry > 0 and current != old
        if lower not in {"c", "s"}:
            cubic_control = None
        if lower not in {"q", "t"}:
            quadratic_control = None
        previous_command = lower
    return (bounds, None) if has_segment and bounds is not None else (None, "path contains no non-zero drawable segment")


def _points(value: str | None) -> tuple[list[tuple[float, float]], str | None]:
    if value is None or not value.strip():
        return [], "points must be non-empty"
    pieces = [part for part in re.split(r"[\s,]+", value.strip()) if part]
    if len(pieces) % 2:
        return [], "points must contain x/y pairs"
    try:
        numbers = [float(part) for part in pieces]
    except ValueError:
        return [], "points contain a non-number"
    if not all(math.isfinite(number) for number in numbers):
        return [], "points contain a non-finite number"
    return list(zip(numbers[::2], numbers[1::2])), None


def _geometry_bounds(element: ET.Element, name: str) -> tuple[Bounds | None, str | None]:
    if name == "path":
        return _path_bounds(element.attrib.get("d"))
    if name in {"circle", "ellipse"}:
        cx, cy = _svg_number(element.attrib.get("cx"), 0), _svg_number(element.attrib.get("cy"), 0)
        rx = _svg_number(element.attrib.get("r" if name == "circle" else "rx"))
        ry = rx if name == "circle" else _svg_number(element.attrib.get("ry"))
        if cx is None or cy is None or rx is None or ry is None or rx <= 0 or ry <= 0:
            return None, f"{name} requires finite center and positive radius values"
        return (cx - rx, cy - ry, cx + rx, cy + ry), None
    if name == "rect":
        x, y = _svg_number(element.attrib.get("x"), 0), _svg_number(element.attrib.get("y"), 0)
        width, height = _svg_number(element.attrib.get("width")), _svg_number(element.attrib.get("height"))
        if x is None or y is None or width is None or height is None or width <= 0 or height <= 0:
            return None, "rect requires finite x/y and positive width/height"
        for radius_name in ("rx", "ry"):
            radius = _svg_number(element.attrib.get(radius_name))
            if element.attrib.get(radius_name) is not None and (radius is None or radius < 0):
                return None, f"rect {radius_name} must be a finite non-negative number"
        return (x, y, x + width, y + height), None
    if name == "line":
        values = [_svg_number(element.attrib.get(field), 0) for field in ("x1", "y1", "x2", "y2")]
        if any(value is None for value in values):
            return None, "line coordinates must be finite"
        x1, y1, x2, y2 = (float(value) for value in values if value is not None)
        return ((min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)), None) if (x1, y1) != (x2, y2) else (None, "line endpoints must differ")
    points, error = _points(element.attrib.get("points"))
    minimum = 3 if name == "polygon" else 2
    if error or len(set(points)) < minimum:
        return None, error or f"{name} requires at least {minimum} distinct points"
    xs, ys = [point[0] for point in points], [point[1] for point in points]
    return (min(xs), min(ys), max(xs), max(ys)), None


def _opacity(value: str | None, field: str, errors: list[str]) -> float | None:
    if value is None:
        return None
    number = _svg_number(value)
    if number is None or not 0 <= number <= 1:
        errors.append(f"{field} must be a finite number from 0 to 1.")
        return None
    if not math.isclose(number, 1.0):
        errors.append(f"{field} must be 1 for an interface-icon asset; apply disabled or muted opacity in the owning component.")
    return number


def validate_svg_asset(svg_path: str | Path, metadata_path: str | Path | None = None) -> dict[str, Any]:
    svg_file, meta_file = Path(svg_path), (Path(metadata_path) if metadata_path else None)
    errors: list[str] = []
    warnings: list[str] = []
    checks: list[str] = []
    for label, path in (("SVG", svg_file), ("Metadata", meta_file)):
        if path is None:
            continue
        try:
            redirect = _reparse_in_chain(path)
        except AssetValidationError as error:
            errors.append(str(error))
            continue
        if redirect is not None:
            errors.append(
                f"{label} path must not contain a symlink, junction, or reparse point: {redirect}"
            )
    if errors:
        return {
            "path": str(svg_file),
            "metadata": str(meta_file) if meta_file else None,
            "valid": False,
            "errors": errors,
            "warnings": warnings,
            "checks": checks,
        }

    try:
        metadata, metadata_errors = _load_metadata(meta_file)
    except AssetValidationError as error:
        metadata, metadata_errors = {}, [str(error)]
    errors.extend(metadata_errors)
    grid = live_area = provenance = None
    if not metadata_errors:
        try:
            grid, live_area, provenance = _validate_metadata(metadata, errors, meta_file)
        except AssetValidationError as error:
            errors.append(str(error))
            grid = live_area = provenance = None
        else:
            checks.append("metadata, drawing-language, and provenance schema inspected")
    try:
        if svg_file.stat().st_size > MAX_SVG_BYTES:
            errors.append(f"SVG exceeds the deterministic {MAX_SVG_BYTES}-byte safety limit.")
            return {"path": str(svg_file), "valid": False, "errors": errors, "warnings": warnings, "checks": checks}
        svg_bytes = svg_file.read_bytes()
        svg_source = svg_bytes.decode("utf-8")
    except FileNotFoundError:
        errors.append(f"SVG file not found: {svg_file}")
        return {"path": str(svg_file), "valid": False, "errors": errors, "warnings": warnings, "checks": checks}
    except OSError as error:
        errors.append(f"SVG file cannot be read safely: {svg_file}: {error}")
        return {"path": str(svg_file), "valid": False, "errors": errors, "warnings": warnings, "checks": checks}
    except UnicodeDecodeError as error:
        errors.append(f"SVG is not valid UTF-8 text: {error}")
        return {"path": str(svg_file), "valid": False, "errors": errors, "warnings": warnings, "checks": checks}

    digest = hashlib.sha256(svg_bytes).hexdigest()
    if isinstance(provenance, dict) and re.fullmatch(r"[0-9a-f]{64}", str(provenance.get("sha256", ""))):
        if provenance["sha256"] != digest:
            errors.append("provenance.sha256 does not match the SVG bytes.")
        else:
            checks.append("provenance SHA-256 matches the exact SVG bytes")
    if UNSAFE_DECLARATION.search(svg_source):
        errors.append("DOCTYPE, ENTITY, and xml-stylesheet declarations are not allowed.")
    if PREFIXED_NAMESPACE_DECLARATION.search(svg_source):
        errors.append("Prefixed namespace declarations are not allowed in self-contained interface icons.")
    try:
        root = ET.fromstring(svg_source)
    except (ET.ParseError, RecursionError, ValueError) as error:
        errors.append(f"SVG is not valid XML: {error}")
        return {"path": str(svg_file), "valid": False, "errors": errors, "warnings": warnings, "checks": checks}

    if _local_name(root.tag) != "svg" or _namespace(root.tag) != SVG_NAMESPACE:
        errors.append(f"Root element must be <svg> in the {SVG_NAMESPACE!r} namespace.")
    view_box = _view_box(root.attrib.get("viewBox"))
    if view_box is None:
        errors.append("SVG must declare a valid positive viewBox.")
    else:
        checks.append(f"scalable viewBox {root.attrib.get('viewBox')} inspected")
        if grid is not None and (not math.isclose(view_box[2], grid[0]) or not math.isclose(view_box[3], grid[1])):
            errors.append(f"Metadata grid {grid[0]}×{grid[1]} does not match viewBox {view_box[2]}×{view_box[3]}.")
    dimensions = {name: _root_dimension(root.attrib.get(name)) for name in ("width", "height")}
    for dimension, parsed in dimensions.items():
        if root.attrib.get(dimension) is not None and (parsed is None or not math.isfinite(parsed)):
            errors.append(f"Root {dimension} must be a positive unitless or px length when declared.")
    if view_box:
        for dimension, expected in (("width", view_box[2]), ("height", view_box[3])):
            parsed = dimensions[dimension]
            if parsed is not None and math.isfinite(parsed) and not math.isclose(parsed, expected):
                errors.append(f"Root {dimension} must match the corresponding viewBox dimension or be omitted.")
    if view_box and all(value is not None and math.isfinite(value) for value in dimensions.values()):
        assert dimensions["width"] is not None and dimensions["height"] is not None
        if not math.isclose(dimensions["width"] / dimensions["height"], view_box[2] / view_box[3]):
            errors.append("Root width/height aspect ratio contradicts the viewBox.")
    aspect = " ".join(str(root.attrib.get("preserveAspectRatio", "")).split()).casefold()
    if aspect not in {"", "xmidymid", "xmidymid meet"}:
        errors.append("preserveAspectRatio must use the default xMidYMid meet behavior when declared.")

    language = metadata.get("drawing_language") if isinstance(metadata.get("drawing_language"), dict) else {}
    mode = str(language.get("mode", "")).strip().casefold()
    declared_width = _finite(language.get("stroke_width"))
    declared_cap = str(language.get("linecap", "")).strip().casefold()
    declared_join = str(language.get("linejoin", "")).strip().casefold()
    viewport = (view_box[0], view_box[1], view_box[0] + view_box[2], view_box[1] + view_box[3]) if view_box else None
    drawable_count, saw_fill, saw_stroke = 0, False, False
    art_bounds: Bounds | None = None
    node_count = 0
    depth_error_reported = False
    node_budget_error_reported = False
    default_style = {"fill": "black", "stroke": "none", "stroke_width": 1.0, "linecap": "butt", "linejoin": "miter", "fill_opacity": 1.0, "stroke_opacity": 1.0, "opacity": 1.0, "hidden": False}

    def walk(element: ET.Element, inherited: dict[str, Any], depth: int = 0) -> None:
        nonlocal drawable_count, saw_fill, saw_stroke, art_bounds, node_count, depth_error_reported, node_budget_error_reported
        node_count += 1
        if depth > MAX_SVG_DEPTH:
            if not depth_error_reported:
                errors.append(f"SVG nesting exceeds the deterministic {MAX_SVG_DEPTH}-level safety limit.")
                depth_error_reported = True
            return
        if node_count > MAX_SVG_NODES:
            if not node_budget_error_reported:
                errors.append(f"SVG exceeds the deterministic {MAX_SVG_NODES}-node safety limit.")
                node_budget_error_reported = True
            return
        name, namespace = _local_name(element.tag), _namespace(element.tag)
        style = dict(inherited)
        if namespace != SVG_NAMESPACE:
            errors.append(f"Foreign or missing namespace is not allowed: <{name}> ({namespace!r}).")
        if name not in SAFE_ELEMENTS:
            errors.append(f"Unsupported or externally dependent element: <{name}>.")
        if name == "svg" and element is not root:
            errors.append("Nested <svg> viewports are not supported; flatten the icon to one root viewBox.")
        if name == "style":
            css_text = "".join(element.itertext())
            if UNSAFE_CSS.search(css_text):
                errors.append("Unsafe active/importing content in <style>.")
            for match in CSS_URL.finditer(css_text):
                errors.append(f"CSS/SVG references are not allowed; found {match.group(2).strip()!r} in <style>.")
        if str(element.attrib.get("display", "")).strip().casefold() == "none" or str(element.attrib.get("visibility", "")).strip().casefold() in {"hidden", "collapse"}:
            style["hidden"] = True
        own_opacity = _opacity(element.attrib.get("opacity"), "opacity", errors)
        if own_opacity is not None:
            style["opacity"] *= own_opacity
        for key, attribute in (("fill_opacity", "fill-opacity"), ("stroke_opacity", "stroke-opacity")):
            parsed = _opacity(element.attrib.get(attribute), attribute, errors)
            if parsed is not None:
                style[key] = parsed
        for key, attribute in (("fill", "fill"), ("stroke", "stroke"), ("linecap", "stroke-linecap"), ("linejoin", "stroke-linejoin")):
            if attribute in element.attrib and element.attrib[attribute].strip().casefold() != "inherit":
                style[key] = element.attrib[attribute].strip().casefold()
        if "stroke-width" in element.attrib:
            width = _svg_number(element.attrib.get("stroke-width"))
            if width is None or width <= 0:
                errors.append("stroke-width must be a positive finite number.")
            else:
                style["stroke_width"] = width

        for attribute, value in element.attrib.items():
            local = _local_name(attribute).casefold()
            text = str(value).strip()
            namespace = _namespace(attribute)
            if namespace not in {None, XML_NAMESPACE}:
                errors.append(f"Namespaced attributes are not allowed: {attribute}={value!r}.")
            allowed = COMMON_ATTRIBUTES | ELEMENT_ATTRIBUTES.get(name, set())
            if local not in allowed:
                errors.append(f"Unsupported attribute on <{name}>: {attribute}={value!r}.")
            if attribute == f"{{{XML_NAMESPACE}}}base":
                errors.append("xml:base is not allowed.")
            if EVENT_HANDLER.match(local):
                errors.append(f"Event-handler attributes are not allowed: {attribute}={value!r}.")
            if local in {"href", "src"}:
                errors.append(f"References are not allowed in self-contained icons: {attribute}={value!r}.")
            if local in {"clip-path", "filter", "mask", "transform"}:
                errors.append(f"{local} can change visibility or geometry; flatten it before structural validation.")
            if local in {"class", "id"}:
                errors.append(f"{local} is not allowed; the icon must not depend on CSS or fragment identity.")
            if UNSAFE_CSS.search(text):
                errors.append(f"Unsafe active/importing content in {attribute}.")
            for match in CSS_URL.finditer(text):
                errors.append(f"CSS/SVG references are not allowed; found {match.group(2).strip()!r} in {attribute}.")
            if local == "style":
                errors.append("Inline style attributes are not allowed.")
            if local in PAINT_ATTRIBUTES and (text.casefold() == "inherit" or text.casefold() not in SAFE_PAINT):
                errors.append(f"Monochrome icons require explicit currentColor/none/transparent paint; found {attribute}={value!r}.")
        if name in {"title", "desc"} and list(element):
            errors.append(f"<{name}> must contain plain text only.")

        if name in GEOMETRY_ELEMENTS:
            bounds, geometry_error = _geometry_bounds(element, name)
            if geometry_error or bounds is None:
                errors.append(f"<{name}> has empty or malformed geometry: {geometry_error}.")
            else:
                fill_visible = name not in {"line", "polyline"} and style["fill"] not in {"none", "transparent"} and style["fill_opacity"] > 0 and style["opacity"] > 0
                stroke_visible = style["stroke"] not in {"none", "transparent"} and style["stroke_opacity"] > 0 and style["opacity"] > 0 and style["stroke_width"] > 0
                if style["hidden"]:
                    errors.append(f"<{name}> is hidden and cannot count as artwork.")
                if not fill_visible and not stroke_visible:
                    errors.append(f"<{name}> has no visible fill or stroke.")
                if fill_visible and style["fill"] != "currentcolor":
                    errors.append(f"<{name}> resolves to a visible fill other than currentColor.")
                if stroke_visible and style["stroke"] != "currentcolor":
                    errors.append(f"<{name}> resolves to a visible stroke other than currentColor.")
                if mode == "stroke" and (fill_visible or not stroke_visible):
                    errors.append(f"<{name}> contradicts drawing_language.mode 'stroke'.")
                if mode == "fill" and (stroke_visible or not fill_visible):
                    errors.append(f"<{name}> contradicts drawing_language.mode 'fill'.")
                if stroke_visible:
                    saw_stroke = True
                    if declared_width is not None and not math.isclose(style["stroke_width"], declared_width):
                        errors.append(f"<{name}> stroke-width {style['stroke_width']} contradicts metadata {declared_width}.")
                    if declared_cap and style["linecap"] != declared_cap:
                        errors.append(f"<{name}> stroke-linecap {style['linecap']!r} contradicts metadata {declared_cap!r}.")
                    if declared_join and style["linejoin"] != declared_join:
                        errors.append(f"<{name}> stroke-linejoin {style['linejoin']!r} contradicts metadata {declared_join!r}.")
                    bounds = _expand(bounds, style["stroke_width"] / 2)
                saw_fill |= fill_visible
                if not style["hidden"] and (fill_visible or stroke_visible):
                    if viewport and not _intersects(viewport, bounds):
                        errors.append(f"<{name}> lies entirely outside the viewBox.")
                    elif viewport and not _contains(viewport, bounds):
                        errors.append(f"<{name}> extends outside the viewBox and can clip.")
                    elif live_area and not _contains(live_area, bounds):
                        errors.append(f"<{name}> contradicts metadata live_area.")
                    else:
                        drawable_count += 1
                        art_bounds = _union(art_bounds, bounds)
        for child in list(element):
            walk(child, style, depth + 1)

    walk(root, default_style)
    if mode == "mixed" and not (saw_fill and saw_stroke):
        errors.append("drawing_language.mode 'mixed' requires both fill and stroke geometry.")
    if drawable_count == 0 or art_bounds is None:
        errors.append("SVG contains no painted, finite, in-viewBox vector geometry.")
    else:
        checks.append(f"{drawable_count} painted vector element(s) stay inside the viewBox and live area")
        sizes = metadata.get("target_sizes")
        if grid is not None and isinstance(sizes, list) and sizes and all(_positive(size) is not None for size in sizes):
            smallest = min(float(size) for size in sizes)
            rendered_width = (art_bounds[2] - art_bounds[0]) * smallest / grid[0]
            rendered_height = (art_bounds[3] - art_bounds[1]) * smallest / grid[1]
            if min(rendered_width, rendered_height) < 0.5:
                errors.append(
                    "Painted artwork collapses below 0.5 CSS pixels in one dimension at the smallest target size."
                )
    checks.append("strict namespace, element, declaration, attribute, and reference scan completed")
    warnings.append("Structural PASS cannot approve recognition, silhouette, optical balance, metaphor, or family/UI fit. Compare existing, custom, and no-icon candidates in the real component at every declared size and applicable state.")
    return {"path": str(svg_file), "metadata": str(meta_file) if meta_file else None, "valid": not errors, "errors": list(dict.fromkeys(errors)), "warnings": warnings, "checks": checks}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a self-contained SVG interface icon and exact provenance metadata")
    parser.add_argument("svg", help="Path to the SVG asset")
    parser.add_argument("--metadata", "-m", required=True, help="Path to companion asset metadata JSON")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()
    result = validate_svg_asset(args.svg, args.metadata)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"{'PASS' if result['valid'] else 'FAIL'}: {result['path']}")
        for error in result["errors"]:
            print(f"ERROR: {error}")
        for warning in result["warnings"]:
            print(f"WARNING: {warning}")
        for check in result["checks"]:
            print(f"CHECK: {check}")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
