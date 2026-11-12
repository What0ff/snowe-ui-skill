#!/usr/bin/env python3
"""Deterministic structural QA for repository-owned SVG interface icons.

This validator checks a compact self-contained SVG subset, painted finite
geometry inside the declared bounds, drawing-language consistency (stroke,
fill, mixed, or layered duotone), and exact provenance binding. Recognition and
optical/UI quality still require rendered human comparison against existing
and no-icon alternatives.

``--init-metadata`` writes a complete metadata skeleton whose ``<...>``
placeholders fail validation until a person fills them; ``--rehash`` rebinds
original-provenance and local evidence digests after an intentional edit.
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
import uuid
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
# --init-metadata writes "<...>" prompts; a whole-value angle-bracket string is
# never a real declaration, so it fails exactly like the words above.
PLACEHOLDER_RE = re.compile(r"\s*<[^<>]*>\s*")
LINECAPS = {"butt", "round", "square", "not applicable"}
# "arcs" is excluded: browsers do not implement it and fall back to miter,
# whose spike extent the bounds proof below cannot certify.
LINEJOINS = {"bevel", "round", "not applicable"}
DRAWING_MODES = {"fill", "stroke", "mixed", "duotone"}
DUOTONE_LAYERS = {"primary", "secondary"}
DUOTONE_TONE_RANGE = (0.12, 0.6)
EVENT_HANDLER = re.compile(r"^on[a-z0-9_:-]+$", re.IGNORECASE)
CSS_URL = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.IGNORECASE)
UNSAFE_CSS = re.compile(r"(?:@import\b|expression\s*\(|(?:java|vb)script\s*:)", re.IGNORECASE)
UNSAFE_DECLARATION = re.compile(r"(?:<!\s*(?:DOCTYPE|ENTITY)\b|<\?xml-stylesheet\b)", re.IGNORECASE)
PREFIXED_NAMESPACE_DECLARATION = re.compile(r"\bxmlns:[A-Za-z_][\w.-]*\s*=", re.IGNORECASE)
NUMBER = r"[-+]?(?:(?:\d+(?:\.\d*)?)|(?:\.\d+))(?:[eE][-+]?\d+)?"
NUMBER_RE = re.compile(rf"^{NUMBER}$")
NUMBER_PREFIX_RE = re.compile(NUMBER)
PATH_SEPARATOR_RE = re.compile(r"[\s,]*")
PATH_COMMANDS = frozenset("AaCcHhLlMmQqSsTtVvZz")
PATH_ARITY = {"a": 7, "c": 6, "h": 1, "l": 2, "m": 2, "q": 4, "s": 4, "t": 2, "v": 1, "z": 0}
CURVE_SAMPLES = 8
ARC_SAMPLES = 12
MAX_WINDING_SUBPATHS = 64
MAX_WINDING_POINTS = 4_096
MAX_SVG_BYTES = 1_000_000
MAX_SVG_DEPTH = 64
MAX_SVG_NODES = 2_048
MAX_SAFE_ARC_MAGNITUDE = 1_000_000.0
MAX_JSON_BYTES = 1_000_000
MAX_JSON_DEPTH = 128
COMMON_ATTRIBUTES = {
    "display", "fill", "fill-opacity", "opacity", "stroke", "stroke-linecap",
    "stroke-linejoin", "stroke-opacity", "stroke-width", "visibility",
    # Inert or fixed-value markup that common icon libraries emit.
    "aria-hidden", "class", "clip-rule", "data-icon-layer", "data-slot", "fill-rule",
    "focusable", "shape-rendering", "vector-effect",
}
GEOMETRY_ATTRIBUTES = {"pathlength"}
ELEMENT_ATTRIBUTES = {
    "svg": {"height", "preserveaspectratio", "role", "viewbox", "width"},
    "g": set(),
    "title": set(),
    "desc": set(),
    "path": {"d"} | GEOMETRY_ATTRIBUTES,
    "circle": {"cx", "cy", "r"} | GEOMETRY_ATTRIBUTES,
    "ellipse": {"cx", "cy", "rx", "ry"} | GEOMETRY_ATTRIBUTES,
    "rect": {"height", "rx", "ry", "width", "x", "y"} | GEOMETRY_ATTRIBUTES,
    "line": {"x1", "x2", "y1", "y2"} | GEOMETRY_ATTRIBUTES,
    "polyline": {"points"} | GEOMETRY_ATTRIBUTES,
    "polygon": {"points"} | GEOMETRY_ATTRIBUTES,
}
# Accepted spellings for fixed-value attributes (compared ASCII case-insensitively).
FIXED_ATTRIBUTE_VALUES = {
    "aria-hidden": ("true",),
    "clip-rule": ("nonzero", "evenodd"),
    "data-icon-layer": ("primary", "secondary"),
    "fill-rule": ("nonzero", "evenodd"),
    "focusable": ("false",),
    "role": ("img",),
    "shape-rendering": ("auto", "geometricPrecision"),
    "vector-effect": ("none", "non-scaling-stroke"),
}
NAME_TOKEN_RE = re.compile(r"[A-Za-z0-9_-]+")
CLASS_TOKENS_RE = re.compile(r"[A-Za-z0-9_-]+(?:[ \t\r\n]+[A-Za-z0-9_-]+)*")

Bounds = tuple[float, float, float, float]
Point = tuple[float, float]


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
    return (
        isinstance(value, str)
        and value.strip().casefold() not in PLACEHOLDERS
        and not PLACEHOLDER_RE.fullmatch(value)
    )


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


def _evidence_path_text(path_value: Any, field: str, errors: list[str]) -> str | None:
    """Return a metadata-relative evidence path, or record why it is unusable."""
    if not isinstance(path_value, str) or not path_value.strip():
        errors.append(f"{field}.path must be a non-empty metadata-relative local path.")
        return None
    path_text = path_value.strip()
    if PLACEHOLDER_RE.fullmatch(path_text):
        errors.append(f"{field}.path is an unfilled placeholder; name the metadata-relative evidence file.")
        return None
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
        return None
    return path_text


def _evidence_digest(
    metadata_path: Path,
    path_text: str,
    field: str,
    errors: list[str],
    *,
    max_bytes: int | None = None,
) -> tuple[Path | None, str | None]:
    """Hash one metadata-relative regular evidence file without following redirects."""
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
        if max_bytes is not None and information.st_size > max_bytes:
            errors.append(f"{field}.path exceeds the {max_bytes}-byte evidence budget.")
            return None, None
        content = resolved.read_bytes()
    except (FileNotFoundError, OSError, RuntimeError, ValueError) as error:
        errors.append(f"{field}.path file cannot be read: {lexical}: {error}")
        return None, None
    return resolved, hashlib.sha256(content).hexdigest()


def _evidence_file(
    metadata_path: Path,
    value: Any,
    field: str,
    errors: list[str],
    *,
    max_bytes: int | None = None,
) -> tuple[Path | None, str | None]:
    if not isinstance(value, dict):
        errors.append(f"{field} must be an object with a metadata-relative path and SHA-256 digest.")
        return None, None
    if set(value) != {"path", "sha256"}:
        errors.append(f"{field} must contain exactly path and sha256 fields.")
        return None, None
    path_text = _evidence_path_text(value.get("path"), field, errors)
    if path_text is None:
        return None, None
    digest_value = value.get("sha256")
    if not re.fullmatch(r"[0-9a-f]{64}", str(digest_value)):
        errors.append(f"{field}.sha256 must be a 64-character lowercase hexadecimal digest.")
        return None, None
    resolved, actual = _evidence_digest(metadata_path, path_text, field, errors, max_bytes=max_bytes)
    if actual is not None and actual != digest_value:
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
    license_binding = evidence.get("license")
    if isinstance(license_binding, dict) and "kind" in license_binding:
        # A drawing the project made itself carries its own license; only
        # imported artwork needs a retained license file to bind.
        if license_binding != {"kind": "project-owned"}:
            errors.append(
                'evidence.license must be a {path, sha256} file binding or exactly {"kind": "project-owned"}.'
            )
        elif provenance_kind != "original" or metadata.get("asset_type") == "brand-mark":
            errors.append(
                "evidence.license kind 'project-owned' applies only to original provenance; "
                "external sources still require a local license file binding."
            )
    else:
        _evidence_file(metadata_path, license_binding, "evidence.license", errors)


def _duotone_tone(tones: Any, errors: list[str] | None = None) -> float | None:
    """Return the one declared secondary-layer opacity, or None when undeclared/invalid."""
    sink: list[str] = [] if errors is None else errors
    if not isinstance(tones, dict) or set(tones) != {"secondary_opacity"}:
        sink.append(
            'Duotone drawing languages require tones exactly {"secondary_opacity": <0.12-0.6>}; '
            "undeclared tones are not allowed."
        )
        return None
    tone = _finite(tones["secondary_opacity"])
    low, high = DUOTONE_TONE_RANGE
    if tone is None or not low <= tone <= high:
        sink.append(f"drawing_language.tones.secondary_opacity must be a finite number from {low:g} to {high:g}.")
        return None
    return tone


def _validate_metadata(metadata: dict[str, Any], errors: list[str], metadata_path: Path | None = None) -> tuple[tuple[float, float] | None, Bounds | None, dict[str, Any] | None]:
    missing = sorted(REQUIRED_METADATA - set(metadata))
    brand_mark = metadata.get("asset_type") == "brand-mark"
    extra = sorted(set(metadata) - REQUIRED_METADATA - ({"brand"} if brand_mark else set()))
    if missing:
        errors.append("Metadata is missing required fields: " + ", ".join(missing))
    if extra:
        errors.append("Metadata contains unsupported fields that the validator cannot substantiate: " + ", ".join(extra))
    for field in sorted(TEXT_METADATA & set(metadata)):
        if not _meaningful(metadata[field]):
            errors.append(f"Metadata field {field!r} must be a specific non-placeholder string.")
    if metadata.get("asset_type") not in ("interface-icon", "brand-mark"):
        errors.append("asset_type must be exactly 'interface-icon' or 'brand-mark'; free-form role wording cannot bypass icon checks.")

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
        if mode not in DRAWING_MODES:
            errors.append("drawing_language.mode must be fill, stroke, mixed, or duotone.")
        elif mode == "fill" and width != 0:
            errors.append("Fill drawing languages must declare stroke_width as 0.")
        elif mode in {"stroke", "mixed"} and (width is None or width <= 0):
            errors.append("Stroke and mixed drawing languages require a positive finite stroke_width.")
        elif mode == "duotone" and (width is None or width < 0):
            errors.append(
                "Duotone drawing languages require stroke_width 0 when no layer is stroked, or the positive stroked width."
            )
        cap = str(language.get("linecap", "")).strip().casefold()
        join = str(language.get("linejoin", "")).strip().casefold()
        if cap not in LINECAPS:
            errors.append("drawing_language.linecap is not a supported SVG line-cap value.")
        if join not in LINEJOINS:
            errors.append("drawing_language.linejoin is not a supported SVG line-join value.")
        if mode not in {"fill", "duotone"} and (cap == "not applicable" or join == "not applicable"):
            errors.append("Stroke and mixed modes require concrete linecap and linejoin values.")
        if mode == "duotone" and width is not None and width > 0 and (cap == "not applicable" or join == "not applicable"):
            errors.append("Stroked duotone artwork requires concrete linecap and linejoin values.")
        if mode == "duotone":
            _duotone_tone(language.get("tones"), errors)
        elif "tones" in language:
            errors.append("drawing_language.tones applies only to duotone mode.")

    sizes = metadata.get("target_sizes")
    if not isinstance(sizes, list) or not sizes or any(_positive(size) is None for size in sizes):
        errors.append("target_sizes must be a non-empty array of positive finite numbers.")
    else:
        normalized = [float(size) for size in sizes]
        if len(set(normalized)) != len(normalized):
            errors.append("target_sizes must not contain duplicate values.")
        # Actual host slots are authoritative. A fictitious 20px declaration
        # cannot prove an implemented 18px control; icon_review checks exact coverage.
        if grid is not None and isinstance(language, dict):
            declared_width = _positive(language.get("stroke_width"))
            if declared_width is not None and str(language.get("mode", "")).strip().casefold() in {"stroke", "mixed", "duotone"}:
                rendered_width = declared_width * min(normalized) / max(grid)
                if rendered_width < 0.5:
                    errors.append(
                        "Declared stroke renders below the deterministic 0.5 CSS-pixel viability floor at the smallest target size."
                    )
    provenance = _validate_provenance(metadata.get("provenance"), errors)
    _validate_evidence(metadata, metadata_path, provenance, errors)
    if brand_mark:
        brand = metadata.get("brand")
        if not isinstance(brand, dict) or set(brand) != {"schema", "identity", "variant", "artwork", "usage"}:
            errors.append("brand-mark requires brand schema, identity, variant, artwork and usage bindings.")
        else:
            if brand["schema"] != "1.0": errors.append("brand.schema must be '1.0'.")
            for field in ("identity", "variant"):
                if not _meaningful(brand[field]): errors.append(f"brand.{field} must identify the supplied brand and variant.")
            if metadata_path is not None:
                for field in ("artwork", "usage"):
                    _evidence_file(metadata_path, brand[field], f"brand.{field}", errors, max_bytes=MAX_SVG_BYTES)
            if isinstance(brand["artwork"], dict) and isinstance(provenance, dict) and brand["artwork"].get("sha256") != provenance.get("sha256"):
                errors.append("brand.artwork must bind the unmodified delivered SVG bytes; recoloring or redrawing is a different asset.")
        if not isinstance(provenance, dict) or provenance.get("kind") != "external":
            errors.append("brand-mark requires external provenance; original drawings cannot claim an imported identity.")
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


def _same_bounds(left: Bounds, right: Bounds, tolerance: float = 1e-7) -> bool:
    return all(math.isclose(a, b, rel_tol=0.0, abs_tol=tolerance) for a, b in zip(left, right))


def _path_commands(value: str) -> tuple[list[tuple[str, list[str]]], str | None]:
    """Lex SVG path data into commands with raw parameter strings.

    Arc flags are read as single ``0``/``1`` characters, as in the SVG path
    grammar, so optimizer output such as ``a8 8 0 0116 0`` parses exactly
    like ``a8 8 0 0 1 16 0``.
    """
    commands: list[tuple[str, list[str]]] = []
    length = len(value)
    position = PATH_SEPARATOR_RE.match(value, 0).end()  # type: ignore[union-attr]
    if position >= length:
        return [], "path data is empty"
    command: str | None = None
    while True:
        position = PATH_SEPARATOR_RE.match(value, position).end()  # type: ignore[union-attr]
        if position >= length:
            break
        character = value[position]
        if character in PATH_COMMANDS:
            position += 1
            if character in "Zz":
                commands.append((character, []))
                command = None
                continue
            command = character
        elif not NUMBER_PREFIX_RE.match(value, position):
            return [], f"invalid token near {value[position:position + 24]!r}"
        elif command is None:
            return [], "path data must begin with a command"
        assert command is not None
        lower = command.casefold()
        raw: list[str] = []
        for index in range(PATH_ARITY[lower]):
            position = PATH_SEPARATOR_RE.match(value, position).end()  # type: ignore[union-attr]
            at_end = position >= length or value[position] in PATH_COMMANDS
            if lower == "a" and index in (3, 4):
                if not at_end and value[position] in "01":
                    raw.append(value[position])
                    position += 1
                    continue
                if at_end:
                    return [], f"command {command} has incomplete parameters"
                return [], "arc flags must use the exact SVG lexical forms 0 or 1"
            match = None if at_end else NUMBER_PREFIX_RE.match(value, position)
            if match is None:
                if at_end:
                    return [], f"command {command} has incomplete parameters"
                return [], f"invalid token near {value[position:position + 24]!r}"
            raw.append(match.group(0))
            position = match.end()
        commands.append((command, raw))
        if lower == "m":
            command = "l" if command == "m" else "L"
    return commands, None


def _arc_parameters(
    start: Point,
    end: Point,
    rx: float,
    ry: float,
    rotation: float,
    large_arc: float,
    sweep: float,
) -> tuple[float, float, float, float, float, float, float, float] | None:
    """Return (cx, cy, rx, ry, cos_phi, sin_phi, theta, delta) for one SVG arc.

    Returns None for an arc that renders as a straight segment.
    """
    if rx == 0 or ry == 0 or start == end:
        return None
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

    def vector_angle(left: Point, right: Point) -> float:
        return math.atan2(left[0] * right[1] - left[1] * right[0], left[0] * right[0] + left[1] * right[1])

    unit_start = ((x1p - cxp) / rx, (y1p - cyp) / ry)
    unit_end = ((-x1p - cxp) / rx, (-y1p - cyp) / ry)
    theta = vector_angle((1.0, 0.0), unit_start)
    delta = vector_angle(unit_start, unit_end)
    if not sweep and delta > 0:
        delta -= math.tau
    elif sweep and delta < 0:
        delta += math.tau
    return cx, cy, rx, ry, cos_phi, sin_phi, theta, delta


def _arc_point(parameters: tuple[float, ...], angle: float) -> Point:
    cx, cy, rx, ry, cos_phi, sin_phi = parameters[:6]
    return (
        cx + rx * cos_phi * math.cos(angle) - ry * sin_phi * math.sin(angle),
        cy + rx * sin_phi * math.cos(angle) + ry * cos_phi * math.sin(angle),
    )


def _arc_extrema(
    start: Point,
    end: Point,
    rx: float,
    ry: float,
    rotation: float,
    large_arc: float,
    sweep: float,
) -> list[Point]:
    """Return endpoints and exact x/y extrema for one SVG elliptical arc."""
    parameters = _arc_parameters(start, end, rx, ry, rotation, large_arc, sweep)
    if parameters is None:
        return [start, end]
    _, _, rx, ry, cos_phi, sin_phi, theta, delta = parameters

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
            points.append(_arc_point(parameters, angle))
    return points


def _arc_samples(start: Point, end: Point, values: list[float]) -> list[Point]:
    """Flatten one arc for winding analysis; bounds use _arc_extrema instead."""
    rx, ry, rotation, large, sweep = values[:5]
    parameters = _arc_parameters(start, end, rx, ry, rotation, large, sweep)
    if parameters is None:
        return [end]
    theta, delta = parameters[6], parameters[7]
    return [_arc_point(parameters, theta + delta * step / ARC_SAMPLES) for step in range(1, ARC_SAMPLES)] + [end]


def _bezier_extrema(points: list[Point]) -> list[Point]:
    """Bound a quadratic/cubic curve by its actual axis extrema.

    Every profile uses these exact extents: a solid shape whose control points
    lie outside the grid (rounded hearts, pills) is not clipped when the drawn
    curve stays inside it.
    """
    if any(not math.isfinite(value) or abs(value) > MAX_SAFE_ARC_MAGNITUDE for point in points for value in point):
        raise ArithmeticError("curve values exceed the deterministic safety envelope")
    times = {0.0, 1.0}
    for axis in (0, 1):
        values = [point[axis] for point in points]
        if len(points) == 3:
            p0, p1, p2 = values
            denominator = p0 - 2 * p1 + p2
            roots = [(p0 - p1) / denominator] if denominator else []
        else:
            p0, p1, p2, p3 = values
            a, b, c = -p0 + 3 * p1 - 3 * p2 + p3, 2 * (p0 - 2 * p1 + p2), p1 - p0
            scale = max(abs(a), abs(b), abs(c))
            if scale: a, b, c = a / scale, b / scale, c / scale
            if a == 0:
                roots = [-c / b] if b else []
            else:
                discriminant = b * b - 4 * a * c
                if discriminant < 0:
                    roots = []
                else:
                    q = -0.5 * (b + math.copysign(math.sqrt(discriminant), b))
                    roots = [q / a, c / q] if q else [-b / (2 * a)]
        times.update(t for t in roots if 0 < t < 1)
    return [_bezier_point(points, t) for t in times]


def _bezier_point(points: list[Point], t: float) -> Point:
    weights = [(1-t)**2, 2*(1-t)*t, t*t] if len(points) == 3 else [(1-t)**3, 3*(1-t)**2*t, 3*(1-t)*t*t, t**3]
    return tuple(sum(weight * point[axis] for weight, point in zip(weights, points)) for axis in (0, 1))  # type: ignore[return-value]


def _path_geometry(
    value: str | None, *, exact_curves: bool = True
) -> tuple[list[dict[str, Any]] | None, Bounds | None, str | None]:
    """Parse path data into bounded subpaths.

    Each subpath records its own bounds and a flattened outline (curves and
    arcs sampled) used only for winding analysis. Curve extrema may raise
    ArithmeticError beyond the deterministic safety envelope.
    """
    if value is None or not value.strip():
        return None, None, "path d must be non-empty"
    commands, error = _path_commands(value)
    if error:
        return None, None, error
    if commands[0][0] not in "Mm":
        return None, None, "path data must begin with a moveto (M/m) command"
    current: Point = (0.0, 0.0)
    start: Point = (0.0, 0.0)
    bounds: Bounds | None = None
    has_segment = False
    previous_command: str | None = None
    cubic_control: Point | None = None
    quadratic_control: Point | None = None
    subpaths: list[dict[str, Any]] = []
    active: dict[str, Any] | None = None

    def begin(point: Point) -> None:
        nonlocal active
        active = {"bounds": None, "points": [point], "closed": False}
        subpaths.append(active)

    def include(extent: list[Point], samples: list[Point]) -> None:
        nonlocal bounds
        assert active is not None
        xs, ys = [point[0] for point in extent], [point[1] for point in extent]
        box = (min(xs), min(ys), max(xs), max(ys))
        bounds = _union(bounds, box)
        active["bounds"] = _union(active["bounds"], box)
        active["points"].extend(samples)

    def include_curve(points: list[Point]) -> None:
        samples = [_bezier_point(points, step / CURVE_SAMPLES) for step in range(1, CURVE_SAMPLES)] + [points[-1]]
        include(_bezier_extrema(points) if exact_curves else points, samples)

    for command, raw_values in commands:
        lower = command.casefold()
        if lower == "z":
            if active is not None:
                if current != start:
                    include([current, start], [start])
                    has_segment = True
                active["closed"] = True
            current = start
            previous_command = "z"
            cubic_control = quadratic_control = None
            active = None
            continue
        values = [float(item) for item in raw_values]
        if not all(math.isfinite(number) for number in values):
            return None, None, f"command {command} contains a non-finite number"
        relative, old = command.islower(), current
        point = lambda x, y: (old[0] + x, old[1] + y) if relative else (x, y)
        if lower == "m":
            current = point(values[0], values[1])
            start = current
            begin(current)
        else:
            if active is None:
                # A drawing command after closepath starts a new subpath at its start point.
                begin(current)
            if lower == "l":
                current = point(values[0], values[1]); include([old, current], [current]); has_segment |= current != old
            elif lower == "h":
                current = ((old[0] + values[0]) if relative else values[0], old[1]); include([old, current], [current]); has_segment |= current != old
            elif lower == "v":
                current = (old[0], (old[1] + values[0]) if relative else values[0]); include([old, current], [current]); has_segment |= current != old
            elif lower == "c":
                points = [old, point(values[0], values[1]), point(values[2], values[3]), point(values[4], values[5])]
                current = points[-1]; cubic_control = points[-2]; include_curve(points); has_segment |= len(set(points)) > 1
            elif lower == "s":
                reflected = (
                    (2 * old[0] - cubic_control[0], 2 * old[1] - cubic_control[1])
                    if previous_command in {"c", "s"} and cubic_control is not None
                    else old
                )
                points = [old, reflected, point(values[0], values[1]), point(values[2], values[3])]
                current = points[-1]; cubic_control = points[-2]; include_curve(points); has_segment |= len(set(points)) > 1
            elif lower == "q":
                points = [old, point(values[0], values[1]), point(values[2], values[3])]
                current = points[-1]; quadratic_control = points[-2]; include_curve(points); has_segment |= len(set(points)) > 1
            elif lower == "t":
                reflected = (
                    (2 * old[0] - quadratic_control[0], 2 * old[1] - quadratic_control[1])
                    if previous_command in {"q", "t"} and quadratic_control is not None
                    else old
                )
                current = point(values[0], values[1]); quadratic_control = reflected
                include_curve([old, reflected, current]); has_segment |= len({old, reflected, current}) > 1
            elif lower == "a":
                rx, ry, rotation, large, sweep, x, y = values
                if rx < 0 or ry < 0 or large not in {0.0, 1.0} or sweep not in {0.0, 1.0}:
                    return None, None, "arc radii must be non-negative and flags must be 0 or 1"
                current = point(x, y)
                try:
                    arc_points = _arc_extrema(old, current, rx, ry, rotation, large, sweep)
                    samples = _arc_samples(old, current, values)
                except ArithmeticError:
                    return None, None, "arc geometry cannot be bounded safely"
                if not all(math.isfinite(coordinate) for arc_point in arc_points + samples for coordinate in arc_point):
                    return None, None, "arc geometry cannot be bounded safely"
                include(arc_points, samples)
                has_segment |= rx > 0 and ry > 0 and current != old
        if lower not in {"c", "s"}:
            cubic_control = None
        if lower not in {"q", "t"}:
            quadratic_control = None
        previous_command = lower
    if not has_segment or bounds is None:
        return None, None, "path contains no non-zero drawable segment"
    return [subpath for subpath in subpaths if subpath["bounds"] is not None], bounds, None


def _path_bounds(value: str | None, *, exact_curves: bool = False) -> tuple[Bounds | None, str | None]:
    _, bounds, error = _path_geometry(value, exact_curves=exact_curves)
    return (bounds, None) if error is None else (None, error)


def _signed_area(points: list[Point]) -> float:
    total = 0.0
    for index, (x1, y1) in enumerate(points):
        x2, y2 = points[(index + 1) % len(points)]
        total += x1 * y2 - x2 * y1
    return total / 2


def _inside_polygon(point: Point, polygon: list[Point]) -> bool:
    x, y = point
    inside = False
    for index, (x1, y1) in enumerate(polygon):
        x2, y2 = polygon[index - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def _same_winding_holes(subpaths: list[dict[str, Any]]) -> list[tuple[int, int]] | None:
    """Return (inner, outer) subpath pairs where a nonzero-fill hole stays solid.

    Each subpath's parent is its smallest enclosing subpath. The region inside
    a subpath has winding number W = W(parent) + direction. An inner subpath
    that winds the same way as its filled parent leaves the region filled, so
    a drawn hole renders solid. Islands inside real holes are not reported.
    Returns None when the path exceeds the deterministic analysis budget.
    """
    if len(subpaths) > MAX_WINDING_SUBPATHS or sum(len(subpath["points"]) for subpath in subpaths) > MAX_WINDING_POINTS:
        return None
    areas = [_signed_area(subpath["points"]) for subpath in subpaths]
    scale = max((abs(area) for area in areas), default=0.0)
    regions = [index for index, area in enumerate(areas) if scale and abs(area) > scale * 1e-9]
    parents: dict[int, int | None] = {}
    for inner in regions:
        containers = [
            outer
            for outer in regions
            if outer != inner
            and abs(areas[outer]) > abs(areas[inner])
            and _contains(subpaths[outer]["bounds"], subpaths[inner]["bounds"], 0.0)
            and all(_inside_polygon(point, subpaths[outer]["points"]) for point in subpaths[inner]["points"])
        ]
        parents[inner] = min(containers, key=lambda outer: abs(areas[outer])) if containers else None
    winding: dict[int, int] = {}

    def level(index: int) -> int:
        if index not in winding:
            parent = parents[index]
            winding[index] = (1 if areas[index] > 0 else -1) + (level(parent) if parent is not None else 0)
        return winding[index]

    pairs: list[tuple[int, int]] = []
    for inner in regions:
        outer = parents[inner]
        if outer is None:
            continue
        same_direction = (areas[inner] > 0) == (areas[outer] > 0)
        if same_direction and level(outer) != 0 and level(inner) != 0:
            pairs.append((inner, outer))
    return pairs


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


def _geometry_bounds(element: ET.Element, name: str, *, exact_curves: bool = True) -> tuple[Bounds | None, str | None]:
    if name == "path":
        try:
            return _path_bounds(element.attrib.get("d"), exact_curves=exact_curves)
        except ArithmeticError:
            return None, "curve geometry cannot be bounded safely"
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


def _opacity_number(value: str | None, field: str, errors: list[str]) -> float | None:
    if value is None:
        return None
    number = _svg_number(value)
    if number is None or not 0 <= number <= 1:
        errors.append(f"{field} must be a finite number from 0 to 1.")
        return None
    return number


def _smallest_target(sizes: Any) -> float | None:
    """Return the smallest declared target, or None when sizes are absent or invalid.

    Invalid sizes are reported by metadata validation; this never raises.
    """
    if not isinstance(sizes, list) or not sizes:
        return None
    try:
        values = [_positive(size) for size in sizes]
    except AssetValidationError:
        return None
    return min(values) if all(value is not None for value in values) else None  # type: ignore[type-var]


def _inspect_svg_root(
    root: ET.Element,
    metadata: dict[str, Any],
    grid: tuple[float, float] | None,
    live_area: Bounds | None,
    errors: list[str],
    warnings: list[str],
    checks: list[str],
) -> dict[str, Any]:
    """Check one parsed SVG tree against declared metadata and return observations.

    ``live_area`` is relative to the viewBox origin. Observations (paint,
    stroke language, layers) let --init-metadata describe the artwork.
    """
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
    # Library exports declare a default render size (Tabler 24, Material 24px
    # on a 960 grid); only a contradictory aspect ratio would distort the art.
    if view_box and all(value is not None and math.isfinite(value) for value in dimensions.values()):
        assert dimensions["width"] is not None and dimensions["height"] is not None
        if not math.isclose(dimensions["width"] / dimensions["height"], view_box[2] / view_box[3]):
            errors.append("Root width/height aspect ratio contradicts the viewBox.")
    aspect = " ".join(str(root.attrib.get("preserveAspectRatio", "")).split()).casefold()
    if aspect not in {"", "xmidymid", "xmidymid meet"}:
        errors.append("preserveAspectRatio must use the default xMidYMid meet behavior when declared.")

    language = metadata.get("drawing_language") if isinstance(metadata.get("drawing_language"), dict) else {}
    brand_mark = metadata.get("asset_type") == "brand-mark"
    def allowed_paint(value: str) -> bool:
        return value in SAFE_PAINT or (brand_mark and (value in {"black", "white"} or re.fullmatch(r"#[0-9a-f]{3}(?:[0-9a-f]{3})?", value) is not None))
    mode = str(language.get("mode", "")).strip().casefold()
    duotone = mode == "duotone"
    tone = _duotone_tone(language.get("tones")) if duotone else None
    declared_width = _finite(language.get("stroke_width"))
    declared_cap = str(language.get("linecap", "")).strip().casefold()
    declared_join = str(language.get("linejoin", "")).strip().casefold()
    smallest_size = _smallest_target(metadata.get("target_sizes"))
    viewport = (view_box[0], view_box[1], view_box[0] + view_box[2], view_box[1] + view_box[3]) if view_box else None
    absolute_live = (
        (view_box[0] + live_area[0], view_box[1] + live_area[1], view_box[0] + live_area[2], view_box[1] + live_area[3])
        if live_area and view_box
        else live_area
    )
    # Source decimal rounding scales with its coordinate system. At a 24px
    # slot this imported-only envelope is below 0.000003 CSS px, not a visual
    # clipping exemption. Keep the existing interface contract unchanged.
    containment_tolerance = min(view_box[2:]) * 1e-7 if brand_mark and view_box else 1e-7
    drawable_count, spacer_count, saw_fill, saw_stroke = 0, 0, False, False
    art_bounds: Bounds | None = None
    painted_layers: set[str] = set()
    smallest_fill_detail: float | None = None
    observed: dict[str, Any] = {
        "view_box": view_box,
        "fill": False,
        "stroke": False,
        "stroke_widths": set(),
        "linecaps": set(),
        "linejoins": set(),
        "layers": set(),
        "secondary_alphas": set(),
    }
    node_count = 0
    depth_error_reported = False
    node_budget_error_reported = False
    default_style = {
        "fill": "black", "stroke": "none", "stroke_width": 1.0, "linecap": "butt", "linejoin": "miter",
        "fill_opacity": 1.0, "stroke_opacity": 1.0, "opacity": 1.0, "hidden": False,
        "fill_rule": "nonzero", "layer": None,
    }

    def walk(element: ET.Element, inherited: dict[str, Any], depth: int = 0) -> None:
        nonlocal drawable_count, spacer_count, saw_fill, saw_stroke, art_bounds, smallest_fill_detail
        nonlocal node_count, depth_error_reported, node_budget_error_reported
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
        is_root = element is root
        style = dict(inherited)
        if namespace != SVG_NAMESPACE:
            errors.append(f"Foreign or missing namespace is not allowed: <{name}> ({namespace!r}).")
        if name not in SAFE_ELEMENTS:
            errors.append(f"Unsupported or externally dependent element: <{name}>.")
        if name == "svg" and not is_root:
            errors.append("Nested <svg> viewports are not supported; flatten the icon to one root viewBox.")
        if name == "style":
            css_text = "".join(element.itertext())
            if UNSAFE_CSS.search(css_text):
                errors.append("Unsafe active/importing content in <style>.")
            for match in CSS_URL.finditer(css_text):
                errors.append(f"CSS/SVG references are not allowed; found {match.group(2).strip()!r} in <style>.")
        if str(element.attrib.get("display", "")).strip().casefold() == "none" or str(element.attrib.get("visibility", "")).strip().casefold() in {"hidden", "collapse"}:
            style["hidden"] = True

        raw_layer = element.attrib.get("data-icon-layer")
        if raw_layer is not None:
            layer = raw_layer.strip().casefold()
            observed["layers"].add(layer)
            if is_root or name in {"title", "desc"}:
                errors.append(f"data-icon-layer belongs on <g> or drawing elements, not <{name}>.")
            elif mode and not duotone:
                errors.append("data-icon-layer requires drawing_language.mode 'duotone'; other modes draw one tone.")
            elif layer in DUOTONE_LAYERS:
                if style["layer"] is not None and style["layer"] != layer:
                    errors.append(
                        f"data-icon-layer cannot change inside a {style['layer']} layer; group each layer's elements separately."
                    )
                else:
                    style["layer"] = layer

        for key, attribute in (("opacity", "opacity"), ("fill_opacity", "fill-opacity"), ("stroke_opacity", "stroke-opacity")):
            number = _opacity_number(element.attrib.get(attribute), attribute, errors)
            if number is None:
                continue
            if not math.isclose(number, 1.0):
                if duotone and style["layer"] == "secondary":
                    if tone is None or not math.isclose(number, tone, rel_tol=0.0, abs_tol=1e-9):
                        declared = "" if tone is None else f" {tone:g}"
                        errors.append(
                            f"{attribute}={number:g} on the duotone secondary layer is not the declared "
                            f"tones.secondary_opacity{declared}; undeclared tones are not allowed."
                        )
                elif duotone:
                    errors.append(
                        f"{attribute} must be 1 outside the duotone secondary layer; apply disabled or muted opacity in the owning component."
                    )
                else:
                    errors.append(
                        f"{attribute} must be 1 for an interface-icon asset; apply disabled or muted opacity in the owning component."
                    )
            if key == "opacity":
                style["opacity"] *= number
            else:
                style[key] = number
        for key, attribute in (
            ("fill", "fill"), ("stroke", "stroke"), ("linecap", "stroke-linecap"),
            ("linejoin", "stroke-linejoin"), ("fill_rule", "fill-rule"),
        ):
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
            elif local in FIXED_ATTRIBUTE_VALUES:
                accepted = FIXED_ATTRIBUTE_VALUES[local]
                if text.casefold() not in {item.casefold() for item in accepted}:
                    errors.append(f"{attribute}={value!r} is not allowed; use {' or '.join(repr(item) for item in accepted)}.")
            elif local == "class" and not CLASS_TOKENS_RE.fullmatch(text):
                errors.append(f"class={value!r} must contain only whitespace-separated name tokens; classes never change validation.")
            elif local == "data-slot" and not NAME_TOKEN_RE.fullmatch(text):
                errors.append(f"data-slot={value!r} must be a single name token.")
            elif local == "pathlength":
                length = _svg_number(text)
                if length is None or length <= 0:
                    errors.append(f"pathLength={value!r} must be a positive finite number.")
            if attribute == f"{{{XML_NAMESPACE}}}base":
                errors.append("xml:base is not allowed.")
            if EVENT_HANDLER.match(local):
                errors.append(f"Event-handler attributes are not allowed: {attribute}={value!r}.")
            if local in {"href", "src"}:
                errors.append(f"References are not allowed in self-contained icons: {attribute}={value!r}.")
            if local in {"clip-path", "filter", "mask", "transform"}:
                errors.append(f"{local} can change visibility or geometry; flatten it before structural validation.")
            if local == "id":
                errors.append("id is not allowed; the icon must not depend on CSS or fragment identity.")
            if UNSAFE_CSS.search(text):
                errors.append(f"Unsafe active/importing content in {attribute}.")
            for match in CSS_URL.finditer(text):
                errors.append(f"CSS/SVG references are not allowed; found {match.group(2).strip()!r} in {attribute}.")
            if local == "style":
                errors.append("Inline style attributes are not allowed.")
            if local in PAINT_ATTRIBUTES and not allowed_paint(text.casefold()):
                contract = "Brand marks permit only self-contained opaque hex/black/white or currentColor paint" if brand_mark else "Monochrome icons require explicit currentColor/none/transparent paint"
                errors.append(f"{contract}; found {attribute}={value!r}.")
        if name in {"title", "desc"} and list(element):
            errors.append(f"<{name}> must contain plain text only.")

        if name in GEOMETRY_ELEMENTS:
            subpaths: list[dict[str, Any]] | None = None
            if name == "path":
                try:
                    subpaths, bounds, geometry_error = _path_geometry(element.attrib.get("d"))
                except ArithmeticError:
                    subpaths, bounds, geometry_error = None, None, "curve geometry cannot be bounded safely"
            else:
                bounds, geometry_error = _geometry_bounds(element, name, exact_curves=True)
            if geometry_error or bounds is None:
                errors.append(f"<{name}> has empty or malformed geometry: {geometry_error}.")
            else:
                fill_visible = name not in {"line", "polyline"} and style["fill"] not in {"none", "transparent"} and style["fill_opacity"] > 0 and style["opacity"] > 0
                stroke_visible = style["stroke"] not in {"none", "transparent"} and style["stroke_opacity"] > 0 and style["opacity"] > 0 and style["stroke_width"] > 0
                if (
                    not fill_visible
                    and not stroke_visible
                    and name in {"rect", "path"}
                    and viewport is not None
                    and _same_bounds(bounds, viewport, containment_tolerance)
                ):
                    # Phosphor/Tabler-style unpainted spacer that only fixes the
                    # export frame; it draws nothing and is not artwork.
                    spacer_count += 1
                else:
                    geometry_box = bounds
                    if style["hidden"]:
                        errors.append(f"<{name}> is hidden and cannot count as artwork.")
                    if not fill_visible and not stroke_visible:
                        errors.append(f"<{name}> has no visible fill or stroke.")
                    if fill_visible and (not allowed_paint(style["fill"]) or (not brand_mark and style["fill"] != "currentcolor")):
                        errors.append(f"<{name}> resolves to a visible fill other than currentColor.")
                    if stroke_visible and (not allowed_paint(style["stroke"]) or (not brand_mark and style["stroke"] != "currentcolor")):
                        errors.append(f"<{name}> resolves to a visible stroke other than currentColor.")
                    if mode == "stroke" and (fill_visible or not stroke_visible):
                        errors.append(f"<{name}> contradicts drawing_language.mode 'stroke'.")
                    if mode == "fill" and (stroke_visible or not fill_visible):
                        errors.append(f"<{name}> contradicts drawing_language.mode 'fill'.")
                    if fill_visible or stroke_visible:
                        observed["fill"] |= fill_visible
                        observed["stroke"] |= stroke_visible
                        layer = style["layer"]
                        alphas = [
                            alpha
                            for alpha, visible in (
                                (style["opacity"] * style["fill_opacity"], fill_visible),
                                (style["opacity"] * style["stroke_opacity"], stroke_visible),
                            )
                            if visible
                        ]
                        if layer == "secondary":
                            observed["secondary_alphas"].update(round(alpha, 9) for alpha in alphas)
                        if duotone:
                            if layer not in DUOTONE_LAYERS:
                                errors.append(
                                    f"<{name}> in duotone mode must resolve to data-icon-layer primary or secondary on itself or an ancestor <g>."
                                )
                            else:
                                painted_layers.add(layer)
                                if layer == "secondary" and tone is not None:
                                    for alpha in alphas:
                                        if not math.isclose(alpha, tone, rel_tol=0.0, abs_tol=1e-9):
                                            errors.append(
                                                f"<{name}> on the duotone secondary layer renders at alpha {alpha:g}; "
                                                f"it must render at exactly the declared tones.secondary_opacity {tone:g}."
                                            )
                    if stroke_visible:
                        saw_stroke = True
                        observed["stroke_widths"].add(style["stroke_width"])
                        observed["linecaps"].add(style["linecap"])
                        observed["linejoins"].add(style["linejoin"])
                        if duotone and declared_width == 0:
                            errors.append(
                                f"<{name}> draws a stroke, but drawing_language.stroke_width is 0; stroked duotone artwork "
                                "declares its positive stroke width and concrete linecap/linejoin."
                            )
                        if declared_width is not None and not math.isclose(style["stroke_width"], declared_width):
                            errors.append(f"<{name}> stroke-width {style['stroke_width']} contradicts metadata {declared_width}.")
                        if declared_cap and style["linecap"] != declared_cap:
                            errors.append(f"<{name}> stroke-linecap {style['linecap']!r} contradicts metadata {declared_cap!r}.")
                        if declared_join and style["linejoin"] != declared_join:
                            errors.append(f"<{name}> stroke-linejoin {style['linejoin']!r} contradicts metadata {declared_join!r}.")
                        # A square cap's corner reaches half-width * sqrt(2) on a
                        # diagonal; round caps/joins and bevels stay within half-width.
                        reach = style["stroke_width"] / 2 * (math.sqrt(2) if style["linecap"] == "square" else 1)
                        # vector-effect is not inherited. A non-scaling stroke keeps
                        # its width in CSS px, so it spans the most grid units at the
                        # smallest declared target.
                        if (
                            str(element.attrib.get("vector-effect", "")).strip().casefold() == "non-scaling-stroke"
                            and view_box is not None
                            and smallest_size is not None
                        ):
                            reach *= max(view_box[2], view_box[3]) / smallest_size
                        bounds = _expand(bounds, reach)
                    saw_fill |= fill_visible
                    if not style["hidden"] and (fill_visible or stroke_visible):
                        if viewport and not _intersects(viewport, bounds):
                            errors.append(f"<{name}> lies entirely outside the viewBox.")
                        elif viewport and not _contains(viewport, bounds, containment_tolerance):
                            errors.append(f"<{name}> extends outside the viewBox and can clip.")
                        elif absolute_live and not _contains(absolute_live, bounds, containment_tolerance):
                            errors.append(f"<{name}> contradicts metadata live_area.")
                        else:
                            drawable_count += 1
                            art_bounds = _union(art_bounds, bounds)
                    if fill_visible and not style["hidden"]:
                        if name == "path" and subpaths and style["fill_rule"] == "nonzero":
                            pairs = _same_winding_holes(subpaths)
                            if pairs is None:
                                checks.append("winding analysis skipped for one <path> beyond the deterministic subpath budget")
                            for inner, outer in pairs or []:
                                warnings.append(
                                    f"<path> subpath {inner + 1} lies inside subpath {outer + 1} with the same winding "
                                    "direction; under fill-rule nonzero the intended hole renders solid. Reverse the "
                                    'inner subpath or declare fill-rule="evenodd".'
                                )
                        if mode in {"fill", "duotone"}:
                            for box in [subpath["bounds"] for subpath in subpaths] if subpaths else [geometry_box]:
                                extent = min(box[2] - box[0], box[3] - box[1])
                                smallest_fill_detail = extent if smallest_fill_detail is None else min(smallest_fill_detail, extent)
        for child in list(element):
            walk(child, style, depth + 1)

    walk(root, default_style)
    observed["art_bounds"] = art_bounds
    if mode == "mixed" and not (saw_fill and saw_stroke):
        errors.append("drawing_language.mode 'mixed' requires both fill and stroke geometry.")
    if duotone:
        if "primary" not in painted_layers:
            if "secondary" in painted_layers:
                errors.append(
                    'Duotone secondary layer is drawn without a primary layer; mark the full-strength geometry data-icon-layer="primary".'
                )
            else:
                errors.append("drawing_language.mode 'duotone' requires painted primary-layer geometry.")
        if declared_width is not None and declared_width > 0 and not saw_stroke:
            errors.append(
                f"drawing_language declares stroke_width {declared_width:g}, but the duotone artwork draws no stroke; "
                "declare 0 with linecap/linejoin 'not applicable'."
            )
        if "primary" in painted_layers:
            secondary = f"secondary layer at {tone:g}" if "secondary" in painted_layers and tone is not None else "no secondary layer"
            checks.append(f"duotone layers inspected: currentColor primary layer and {secondary}")
    if spacer_count:
        checks.append(f"{spacer_count} unpainted viewBox spacer element(s) ignored")
    if drawable_count == 0 or art_bounds is None:
        errors.append("SVG contains no painted, finite, in-viewBox vector geometry.")
    else:
        checks.append(f"{drawable_count} painted vector element(s) stay inside the viewBox and live area")
        if grid is not None and smallest_size is not None:
            rendered_width = (art_bounds[2] - art_bounds[0]) * smallest_size / grid[0]
            rendered_height = (art_bounds[3] - art_bounds[1]) * smallest_size / grid[1]
            if min(rendered_width, rendered_height) < 0.5:
                errors.append(
                    "Painted artwork collapses below 0.5 CSS pixels in one dimension at the smallest target size."
                )
            if mode in {"fill", "duotone"} and smallest_fill_detail is not None:
                rendered_detail = smallest_fill_detail * smallest_size / max(grid)
                if rendered_detail < 1:
                    warnings.append(
                        f"Smallest filled subpath spans {smallest_fill_detail:g} grid units ({rendered_detail:.2f} CSS px at "
                        f"{smallest_size:g} px); filled details and counters below 1 CSS px can close up or vanish. "
                        "Inspect it rendered at the smallest target."
                    )
    checks.append("strict namespace, element, declaration, attribute, and reference scan completed")
    return observed


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

    _inspect_svg_root(root, metadata, grid, live_area, errors, warnings, checks)
    brand_mark = metadata.get("asset_type") == "brand-mark"
    if brand_mark:
        checks.append("imported brand artwork and usage records are byte-bound; source truth is not certified")
        warnings.append("Official source, usage permission and variant suitability remain unverified by this offline validator. Inspect current primary-source evidence and the actual host; do not generate a custom substitute. Unsupported official SVG constructs need a suitable official variant or host-supported asset proof, never a silent redraw.")
    else:
        warnings.append("Structural PASS cannot approve recognition, silhouette, optical balance, metaphor, or family/UI fit. Compare existing, custom, and no-icon candidates in the real component at every declared size and applicable state.")
    return {"path": str(svg_file), "metadata": str(meta_file) if meta_file else None, "valid": not errors, "errors": list(dict.fromkeys(errors)), "warnings": list(dict.fromkeys(warnings)), "checks": checks}


def default_metadata_path(svg_path: str | Path) -> Path:
    svg_file = Path(svg_path)
    return svg_file.with_name(f"{svg_file.stem}.metadata.json")


def _read_svg_for_metadata(svg_file: Path) -> tuple[bytes, ET.Element]:
    redirect = _reparse_in_chain(svg_file)
    if redirect is not None:
        raise AssetValidationError(f"SVG path must not contain a symlink, junction, or reparse point: {redirect}")
    try:
        if svg_file.stat().st_size > MAX_SVG_BYTES:
            raise AssetValidationError(f"SVG exceeds the deterministic {MAX_SVG_BYTES}-byte safety limit.")
        svg_bytes = svg_file.read_bytes()
        source = svg_bytes.decode("utf-8")
    except FileNotFoundError as error:
        raise AssetValidationError(f"SVG file not found: {svg_file}") from error
    except OSError as error:
        raise AssetValidationError(f"SVG file cannot be read safely: {svg_file}: {error}") from error
    except UnicodeDecodeError as error:
        raise AssetValidationError(f"SVG is not valid UTF-8 text: {error}") from error
    if UNSAFE_DECLARATION.search(source):
        raise AssetValidationError("DOCTYPE, ENTITY, and xml-stylesheet declarations are not allowed.")
    try:
        root = ET.fromstring(source)
    except (ET.ParseError, RecursionError, ValueError) as error:
        raise AssetValidationError(f"SVG is not valid XML: {error}") from error
    return svg_bytes, root


def _json_number(value: float) -> int | float:
    return int(value) if float(value).is_integer() else value


def _placeholder_fields(value: Any, prefix: str = "") -> list[str]:
    if isinstance(value, dict):
        return [field for key, child in value.items() for field in _placeholder_fields(child, f"{prefix}{key}.")]
    return [prefix.rstrip(".")] if isinstance(value, str) and PLACEHOLDER_RE.fullmatch(value) else []


def _atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.tmp-{uuid.uuid4().hex}")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def init_metadata(
    svg_path: str | Path,
    metadata_path: str | Path | None = None,
    *,
    provenance: str = "original",
) -> dict[str, Any]:
    """Write a complete metadata skeleton beside an SVG without overwriting anything.

    Facts the SVG proves (name, grid, digest, observed drawing language) are
    computed. Judgments only a person can make stay as ``<...>`` placeholders,
    which fail validation until replaced.
    """
    if provenance not in {"original", "external"}:
        raise AssetValidationError("--provenance must be original or external.")
    svg_file = Path(svg_path)
    meta_file = Path(metadata_path) if metadata_path else default_metadata_path(svg_file)
    svg_bytes, root = _read_svg_for_metadata(svg_file)
    redirect = _reparse_in_chain(meta_file)
    if redirect is not None:
        raise AssetValidationError(f"Metadata path must not contain a symlink, junction, or reparse point: {redirect}")
    if os.path.lexists(meta_file):
        raise AssetValidationError(
            f"Metadata file already exists: {meta_file}; edit it, or run --rehash after an intentional SVG edit."
        )
    observed = _inspect_svg_root(root, {}, None, None, [], [], [])
    view_box = observed["view_box"]
    if view_box is None:
        raise AssetValidationError("SVG must declare a valid positive viewBox before metadata can be initialized.")
    width, height = view_box[2], view_box[3]
    if observed["layers"]:
        mode = "duotone"
    elif observed["fill"] and observed["stroke"]:
        mode = "mixed"
    elif observed["stroke"]:
        mode = "stroke"
    else:
        mode = "fill"
    language: dict[str, Any] = {"mode": mode}
    if observed["stroke"]:
        widths, caps, joins = observed["stroke_widths"], observed["linecaps"], observed["linejoins"]
        language["stroke_width"] = (
            _json_number(next(iter(widths)))
            if len(widths) == 1
            else f"<one stroke width; the artwork uses {', '.join(f'{item:g}' for item in sorted(widths))}>"
        )
        language["linecap"] = next(iter(caps)) if len(caps) == 1 else f"<one linecap; the artwork uses {', '.join(sorted(caps))}>"
        language["linejoin"] = next(iter(joins)) if len(joins) == 1 else f"<one linejoin; the artwork uses {', '.join(sorted(joins))}>"
    else:
        language.update({"stroke_width": 0, "linecap": "not applicable", "linejoin": "not applicable"})
    if mode == "duotone":
        alphas = observed["secondary_alphas"]
        language["tones"] = {
            "secondary_opacity": _json_number(next(iter(alphas)))
            if len(alphas) == 1
            else "<declared secondary-layer opacity from 0.12 to 0.6>"
        }
    language["corner_language"] = "<corner and terminal language shared with the family>"
    language["detail_budget"] = "<details that must survive the smallest target size>"
    digest = hashlib.sha256(svg_bytes).hexdigest()
    if provenance == "original":
        provenance_value = {
            "kind": "original",
            "creator": "<who drew this icon>",
            "source_ref": "<metadata-relative design record, e.g. icon.source.md#icon>",
            "reviewed": "<YYYY-MM-DD>",
            "sha256": digest,
        }
        evidence = {
            "source": {"kind": "local", "path": "<metadata-relative source record file>", "sha256": "<run --rehash after setting path>"},
            "license": {"kind": "project-owned"},
        }
    else:
        provenance_value = {
            "kind": "external",
            "creator": "<upstream author or project>",
            "source_ref": "<canonical HTTPS URL pinned to the upstream revision>",
            "reviewed": "<YYYY-MM-DD>",
            "sha256": digest,
        }
        evidence = {
            "source": {"kind": "external", "verification": "unverified"},
            "license": {"path": "<metadata-relative retained license file>", "sha256": "<run --rehash after setting path>"},
        }
    skeleton: dict[str, Any] = {
        "name": svg_file.stem,
        "asset_type": "interface-icon",
        "role": "<UI role this icon serves>",
        "grid": _json_number(width) if math.isclose(width, height) else f"{width:g} x {height:g}",
        "live_area": {"min_x": 0, "min_y": 0, "max_x": _json_number(width), "max_y": _json_number(height)},
        "drawing_language": language,
        "target_sizes": "<actual implemented slot sizes in CSS px, e.g. [16, 20]>",
        "source": "<where this drawing comes from>",
        "license": "<license statement, e.g. project-owned>",
        "accessibility_owner": "<element that owns the accessible name; SVG decorative or labelled>",
        "provenance": provenance_value,
        "evidence": evidence,
    }
    # Report structural problems against the inferred language, not the empty skeleton.
    svg_errors: list[str] = []
    _inspect_svg_root(root, {"drawing_language": language}, None, None, svg_errors, [], [])
    with open(meta_file, "x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(skeleton, indent=2, ensure_ascii=False) + "\n")
    return {
        "metadata": str(meta_file),
        "svg": str(svg_file),
        "sha256": digest,
        "drawing_language": {key: language[key] for key in ("mode", "stroke_width", "linecap", "linejoin")},
        "placeholders": _placeholder_fields(skeleton),
        "svg_errors": list(dict.fromkeys(svg_errors)),
    }


def rehash_metadata(svg_path: str | Path, metadata_path: str | Path) -> dict[str, Any]:
    """Rebind digests after an intentional edit; never rebinds imported artwork.

    Original provenance takes the current SVG digest. Local source/license
    evidence takes the current bytes of the files already named. External or
    brand-mark provenance keeps its upstream digest. Nothing is written when
    any named evidence file is unsafe or unreadable.
    """
    svg_file, meta_file = Path(svg_path), Path(metadata_path)
    for label, path in (("SVG", svg_file), ("Metadata", meta_file)):
        redirect = _reparse_in_chain(path)
        if redirect is not None:
            raise AssetValidationError(f"{label} path must not contain a symlink, junction, or reparse point: {redirect}")
    metadata, load_errors = _load_metadata(meta_file)
    if load_errors:
        raise AssetValidationError("; ".join(load_errors))
    try:
        if svg_file.stat().st_size > MAX_SVG_BYTES:
            raise AssetValidationError(f"SVG exceeds the deterministic {MAX_SVG_BYTES}-byte safety limit.")
        digest = hashlib.sha256(svg_file.read_bytes()).hexdigest()
    except FileNotFoundError as error:
        raise AssetValidationError(f"SVG file not found: {svg_file}") from error
    except OSError as error:
        raise AssetValidationError(f"SVG file cannot be read safely: {svg_file}: {error}") from error
    report: dict[str, Any] = {"changed": [], "unchanged": [], "skipped": [], "errors": [], "written": False}

    def bind(container: dict[str, Any], field: str, value: str) -> None:
        previous = container.get("sha256")
        if previous == value:
            report["unchanged"].append(field)
        else:
            report["changed"].append({"field": field, "old": previous, "new": value})
            container["sha256"] = value

    brand_mark = metadata.get("asset_type") == "brand-mark"
    provenance = metadata.get("provenance")
    kind = str(provenance.get("kind", "")).strip().casefold() if isinstance(provenance, dict) else ""
    if not isinstance(provenance, dict):
        report["skipped"].append({"field": "provenance.sha256", "reason": "provenance is not an object"})
    elif kind == "original" and not brand_mark:
        bind(provenance, "provenance.sha256", digest)
    elif provenance.get("sha256") == digest:
        report["unchanged"].append("provenance.sha256")
    elif kind == "external" or brand_mark:
        report["skipped"].append({
            "field": "provenance.sha256",
            "reason": "external provenance binds the upstream bytes; restore the upstream SVG, or re-import and review it, instead of rebinding an edited copy",
        })
    else:
        report["skipped"].append({"field": "provenance.sha256", "reason": "provenance.kind must be 'original' before its digest can be rebound"})
    evidence = metadata.get("evidence")
    if isinstance(evidence, dict):
        for field in ("source", "license"):
            binding = evidence.get(field)
            label = f"evidence.{field}"
            if not isinstance(binding, dict) or "path" not in binding:
                continue
            if field == "source" and str(binding.get("kind", "")).strip().casefold() != "local":
                continue
            path_value = binding.get("path")
            if isinstance(path_value, str) and PLACEHOLDER_RE.fullmatch(path_value):
                report["skipped"].append({"field": f"{label}.sha256", "reason": f"{label}.path is still a placeholder"})
                continue
            binding_errors: list[str] = []
            path_text = _evidence_path_text(path_value, label, binding_errors)
            actual = _evidence_digest(meta_file, path_text, label, binding_errors)[1] if path_text is not None else None
            if actual is None:
                report["errors"].extend(binding_errors)
            else:
                bind(binding, f"{label}.sha256", actual)
    if isinstance(metadata.get("brand"), dict):
        report["skipped"].append({
            "field": "brand.artwork.sha256, brand.usage.sha256",
            "reason": "imported brand bindings are never rehashed; they keep binding the retained upstream records",
        })
    if report["errors"]:
        report["changed"] = []
        return report
    if report["changed"]:
        _atomic_write_json(meta_file, metadata)
        report["written"] = True
    return report


def _print_result(result: dict[str, Any]) -> None:
    print(f"{'PASS' if result['valid'] else 'FAIL'}: {result['path']}")
    for error in result["errors"]:
        print(f"ERROR: {error}")
    for warning in result["warnings"]:
        print(f"WARNING: {warning}")
    for check in result["checks"]:
        print(f"CHECK: {check}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a self-contained SVG interface icon and exact provenance metadata")
    parser.add_argument("svg", help="Path to the SVG asset")
    parser.add_argument(
        "--metadata", "-m",
        help="Path to companion asset metadata JSON (required to validate or rehash; "
        "--init-metadata defaults to <svg-stem>.metadata.json beside the SVG)",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    action = parser.add_mutually_exclusive_group()
    action.add_argument(
        "--init-metadata", action="store_true",
        help="Write a complete metadata skeleton with the computed SVG digest and observed drawing language; "
        "<...> placeholders fail validation until filled. Never overwrites an existing file.",
    )
    action.add_argument(
        "--rehash", action="store_true",
        help="After an intentional edit, recompute original provenance and local evidence SHA-256 values, "
        "print what changed, then validate. External and brand artwork digests are never rebound.",
    )
    parser.add_argument(
        "--provenance", choices=("original", "external"),
        help="With --init-metadata: skeleton provenance kind (default original, with a project-owned license binding)",
    )
    args = parser.parse_args()
    if args.provenance and not args.init_metadata:
        parser.error("--provenance applies only to --init-metadata")
    if not args.init_metadata and not args.metadata:
        parser.error("--metadata is required unless --init-metadata is used")

    if args.init_metadata:
        try:
            created = init_metadata(args.svg, args.metadata, provenance=args.provenance or "original")
        except (AssetValidationError, OSError) as error:
            print(f"INIT FAILED: {error}", file=sys.stderr)
            return 1
        if args.json:
            print(json.dumps(created, indent=2, ensure_ascii=False))
        else:
            print(f"WROTE: {created['metadata']}")
            language = ", ".join(f"{key}={value}" for key, value in created["drawing_language"].items())
            print(f"INFERRED: drawing_language {language}; provenance.sha256={created['sha256']}")
            for error in created["svg_errors"]:
                print(f"SVG ERROR: {error}")
            print("FILL: " + ", ".join(created["placeholders"]))
            print("NEXT: replace every <...> placeholder (they fail validation), then run --rehash to bind evidence digests and validate.")
        return 0

    if args.rehash:
        try:
            report = rehash_metadata(args.svg, args.metadata)
        except (AssetValidationError, OSError) as error:
            print(f"REHASH FAILED: {error}", file=sys.stderr)
            return 1
        if report["errors"]:
            if args.json:
                print(json.dumps({"valid": False, "rehash": report}, indent=2, ensure_ascii=False))
            else:
                for error in report["errors"]:
                    print(f"REHASH ERROR: {error}")
                print("NOT WRITTEN: metadata left unchanged.")
            return 1
        result = validate_svg_asset(args.svg, args.metadata)
        if args.json:
            print(json.dumps({**result, "rehash": report}, indent=2, ensure_ascii=False))
        else:
            for change in report["changed"]:
                print(f"UPDATED {change['field']}: {change['old']} -> {change['new']}")
            for field in report["unchanged"]:
                print(f"UNCHANGED {field}")
            for item in report["skipped"]:
                print(f"SKIPPED {item['field']}: {item['reason']}")
            _print_result(result)
        return 0 if result["valid"] else 1

    result = validate_svg_asset(args.svg, args.metadata)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        _print_result(result)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
