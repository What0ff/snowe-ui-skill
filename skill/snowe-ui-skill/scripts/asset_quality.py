#!/usr/bin/env python3
"""Structural QA for repository-owned SVG interface assets.

This validator intentionally does not score beauty or optical balance.  It
checks scalable structure, provenance metadata, unsafe/embedded content, and a
declared drawing-language contract.  The asset still needs same-context renders
at its actual sizes and states before it can be accepted.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


REQUIRED_METADATA = {
    "name",
    "role",
    "grid",
    "live_area",
    "drawing_language",
    "target_sizes",
    "source",
    "license",
    "accessibility_owner",
}

REQUIRED_DRAWING_LANGUAGE = {
    "mode",
    "stroke_width",
    "linecap",
    "linejoin",
    "corner_language",
    "detail_budget",
}

FORBIDDEN_ELEMENTS = {
    "a",
    "animate",
    "animatemotion",
    "animatetransform",
    "audio",
    "discard",
    "foreignobject",
    "iframe",
    "image",
    "script",
    "set",
    "style",
    "video",
}
PAINT_ATTRIBUTES = {"fill", "stroke", "color", "stop-color", "flood-color", "lighting-color"}
SAFE_MONOCHROME_PAINT = {"none", "currentcolor", "transparent", "inherit"}
MONOCHROME_MODES = {
    "fill",
    "stroke",
    "mixed",
    "monochrome fill",
    "monochrome stroke",
    "monochrome mixed",
}
REQUIRED_TEXT_METADATA = {
    "name",
    "role",
    "live_area",
    "source",
    "license",
    "accessibility_owner",
}
REQUIRED_TEXT_DRAWING_LANGUAGE = {
    "mode",
    "linecap",
    "linejoin",
    "corner_language",
    "detail_budget",
}
PLACEHOLDER_TEXT = {"", "-", "n/a", "na", "none", "not provided", "tbd", "todo", "unknown", "unspecified"}
EVENT_HANDLER_ATTRIBUTE = re.compile(r"^on[a-z0-9_:-]+$", re.IGNORECASE)
CSS_URL = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.IGNORECASE)
UNSAFE_CSS = re.compile(r"(?:@import\b|expression\s*\(|(?:java|vb)script\s*:)", re.IGNORECASE)
UNSAFE_DECLARATION = re.compile(
    r"(?:<!\s*(?:DOCTYPE|ENTITY)\b|<\?xml-stylesheet\b)",
    re.IGNORECASE,
)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _parse_view_box(value: str | None) -> tuple[float, float, float, float] | None:
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


def _positive_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) and number > 0 else None


def _parse_grid(value: Any) -> tuple[float, float] | None:
    number = _positive_number(value)
    if number is not None:
        return number, number
    if not isinstance(value, str):
        return None
    match = re.fullmatch(
        r"\s*(\d+(?:\.\d+)?)\s*(?:x|×)\s*(\d+(?:\.\d+)?)\s*",
        value,
        re.IGNORECASE,
    )
    if not match:
        return None
    width, height = (float(part) for part in match.groups())
    if width <= 0 or height <= 0:
        return None
    return width, height


def _is_meaningful_text(value: Any) -> bool:
    return isinstance(value, str) and value.strip().casefold() not in PLACEHOLDER_TEXT


def _validate_metadata(metadata: dict[str, Any], errors: list[str]) -> tuple[float, float] | None:
    missing = sorted(REQUIRED_METADATA - set(metadata))
    if missing:
        errors.append(f"Metadata is missing required fields: {', '.join(missing)}")

    for field in sorted(REQUIRED_TEXT_METADATA & set(metadata)):
        if not _is_meaningful_text(metadata[field]):
            errors.append(f"Metadata field {field!r} must be a specific non-empty string, not a placeholder.")

    grid = _parse_grid(metadata.get("grid"))
    if "grid" in metadata and grid is None:
        errors.append("grid must be a positive number or '<width> x <height>' string.")

    language = metadata.get("drawing_language")
    if not isinstance(language, dict):
        errors.append("drawing_language must be an object.")
    else:
        missing_language = sorted(REQUIRED_DRAWING_LANGUAGE - set(language))
        if missing_language:
            errors.append(
                "drawing_language is missing required fields: " + ", ".join(missing_language)
            )
        for field in sorted(REQUIRED_TEXT_DRAWING_LANGUAGE & set(language)):
            if not _is_meaningful_text(language[field]):
                errors.append(
                    f"drawing_language field {field!r} must be a specific non-empty string, not a placeholder."
                )
        mode = str(language.get("mode", "")).strip().casefold()
        if _is_meaningful_text(language.get("mode")) and mode not in MONOCHROME_MODES:
            errors.append(
                "drawing_language mode must be one of: " + ", ".join(sorted(MONOCHROME_MODES)) + "."
            )
        if "stroke_width" in language and _positive_number(language.get("stroke_width")) is None:
            errors.append("drawing_language stroke_width must be a positive finite number.")

    target_sizes = metadata.get("target_sizes")
    valid_sizes = (
        isinstance(target_sizes, list)
        and bool(target_sizes)
        and all(_positive_number(size) is not None for size in target_sizes)
    )
    if not valid_sizes:
        errors.append("target_sizes must be a non-empty array of positive finite numbers.")
    else:
        normalized_sizes = [float(size) for size in target_sizes]
        if len(set(normalized_sizes)) != len(normalized_sizes):
            errors.append("target_sizes must not contain duplicate values.")
        elif str(metadata.get("role", "")).strip().casefold() in {"interface icon", "navigation icon", "product icon"}:
            missing_sizes = [size for size in (16, 20, 24) if float(size) not in normalized_sizes]
            if missing_sizes:
                errors.append(
                    "Interface icon metadata must include rendered QA targets 16, 20, and 24; missing: "
                    + ", ".join(map(str, missing_sizes))
                )
    return grid


def _css_reference_errors(value: str) -> list[str]:
    errors: list[str] = []
    if UNSAFE_CSS.search(value):
        errors.append("CSS contains an active or importing construct.")
    for match in CSS_URL.finditer(value):
        target = match.group(2).strip()
        if not target.startswith("#") or len(target) == 1:
            errors.append(f"CSS reference must be a non-empty local fragment; found {target!r}.")
    return errors


def _load_metadata(path: Path | None) -> tuple[dict[str, Any], list[str]]:
    if path is None:
        return {}, ["A companion metadata JSON file is required for repository-owned interface assets."]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, [f"Metadata file not found: {path}"]
    except json.JSONDecodeError as error:
        return {}, [f"Metadata is not valid JSON: {error}"]
    if not isinstance(value, dict):
        return {}, ["Metadata root must be a JSON object."]
    return value, []


def validate_svg_asset(svg_path: str | Path, metadata_path: str | Path | None = None) -> dict[str, Any]:
    svg_file = Path(svg_path)
    meta_file = Path(metadata_path) if metadata_path else None
    errors: list[str] = []
    warnings: list[str] = []
    checks: list[str] = []

    metadata, metadata_errors = _load_metadata(meta_file)
    errors.extend(metadata_errors)
    grid = None
    if not metadata_errors:
        grid = _validate_metadata(metadata, errors)
        checks.append("metadata/provenance contract inspected")

    try:
        svg_source = svg_file.read_text(encoding="utf-8")
    except FileNotFoundError:
        errors.append(f"SVG file not found: {svg_file}")
        return {"path": str(svg_file), "valid": False, "errors": errors, "warnings": warnings, "checks": checks}
    except UnicodeDecodeError as error:
        errors.append(f"SVG is not valid UTF-8 text: {error}")
        return {"path": str(svg_file), "valid": False, "errors": errors, "warnings": warnings, "checks": checks}

    if UNSAFE_DECLARATION.search(svg_source):
        errors.append(
            "DOCTYPE, ENTITY, and xml-stylesheet declarations are not allowed in repository-owned SVG assets."
        )
    try:
        root = ET.fromstring(svg_source)
    except ET.ParseError as error:
        errors.append(f"SVG is not valid XML: {error}")
        return {"path": str(svg_file), "valid": False, "errors": errors, "warnings": warnings, "checks": checks}

    if _local_name(root.tag) != "svg":
        errors.append("Root element must be <svg>.")
    view_box = _parse_view_box(root.attrib.get("viewBox"))
    if view_box is None:
        errors.append("SVG must declare a valid positive viewBox for scalable rendering.")
    else:
        checks.append(f"scalable viewBox {root.attrib.get('viewBox')} inspected")
        if grid is not None and (
            not math.isclose(view_box[2], grid[0]) or not math.isclose(view_box[3], grid[1])
        ):
            errors.append(
                f"Metadata grid {grid[0]}×{grid[1]} does not match viewBox dimensions {view_box[2]}×{view_box[3]}."
            )

    found_graphics = False
    language = metadata.get("drawing_language")
    monochrome = (
        isinstance(language, dict)
        and str(language.get("mode", "")).strip().casefold() in MONOCHROME_MODES
    )
    for element in root.iter():
        name = _local_name(element.tag)
        if name.casefold() in FORBIDDEN_ELEMENTS:
            errors.append(f"Forbidden embedded or executable element: <{name}>.")
        if name in {"path", "circle", "ellipse", "rect", "line", "polyline", "polygon"}:
            found_graphics = True
        if name == "text":
            errors.append("Interface SVGs must not embed text; keep labels in accessible HTML or platform UI.")
        if name in {"filter", "mask", "pattern"}:
            warnings.append(
                f"<{name}> needs target-size render proof; effects and masks often blur or collapse in interface icons."
            )
        if name.casefold() == "style":
            for detail in _css_reference_errors("".join(element.itertext())):
                errors.append(f"Unsafe <style> content: {detail}")
        for attribute, value in element.attrib.items():
            local_attribute = _local_name(attribute)
            attribute_value = str(value).strip()
            if attribute == "{http://www.w3.org/XML/1998/namespace}base":
                errors.append(f"xml:base is not allowed because it can make local references external: {value!r}.")
            if EVENT_HANDLER_ATTRIBUTE.match(local_attribute):
                errors.append(f"Event-handler attributes are not allowed: {attribute}={value!r}.")
            if local_attribute.casefold() in {"href", "src"} and (
                not attribute_value.startswith("#") or len(attribute_value) == 1
            ):
                errors.append(
                    f"URI references must be non-empty local fragments; found {attribute}={value!r}."
                )
            for detail in _css_reference_errors(attribute_value):
                errors.append(f"Unsafe attribute content in {attribute}: {detail}")
            if monochrome and local_attribute in PAINT_ATTRIBUTES:
                paint = attribute_value.casefold()
                if paint not in SAFE_MONOCHROME_PAINT and not paint.startswith("url(#"):
                    errors.append(
                        f"Monochrome drawing language requires currentColor/none/inherit paint; found {attribute}={value!r}."
                    )
            if local_attribute.casefold() == "style":
                errors.append("Inline style attributes are not allowed; use explicit auditable SVG attributes.")

    if not found_graphics:
        errors.append("SVG contains no supported vector geometry.")
    else:
        checks.append("vector geometry present; no raster image is embedded")

    checks.append("executable and external-reference scan completed")
    warnings.append(
        "Structural validation cannot approve recognition or optical balance. Render beside neighboring assets at every target size and real UI state before acceptance."
    )
    return {
        "path": str(svg_file),
        "metadata": str(meta_file) if meta_file else None,
        "valid": not errors,
        "errors": errors,
        "warnings": list(dict.fromkeys(warnings)),
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a repository-owned SVG asset and its drawing-language metadata")
    parser.add_argument("svg", help="Path to the SVG asset")
    parser.add_argument("--metadata", "-m", required=True, help="Path to companion asset metadata JSON")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    result = validate_svg_asset(args.svg, args.metadata)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        state = "PASS" if result["valid"] else "FAIL"
        print(f"{state}: {result['path']}")
        for error in result["errors"]:
            print(f"ERROR: {error}")
        for warning in result["warnings"]:
            print(f"WARNING: {warning}")
        for check in result["checks"]:
            print(f"CHECK: {check}")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
