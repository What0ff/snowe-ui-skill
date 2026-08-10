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

FORBIDDEN_ELEMENTS = {"script", "image", "foreignObject", "iframe", "audio", "video"}
PAINT_ATTRIBUTES = {"fill", "stroke", "color", "stop-color", "flood-color", "lighting-color"}
SAFE_MONOCHROME_PAINT = {"none", "currentcolor", "transparent", "inherit"}
EXTERNAL_REFERENCE = re.compile(r"^(?:https?:|file:|data:|//)", re.IGNORECASE)


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
    if numbers[2] <= 0 or numbers[3] <= 0:
        return None
    return numbers  # type: ignore[return-value]


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
    if metadata:
        missing = sorted(REQUIRED_METADATA - set(metadata))
        if missing:
            errors.append(f"Metadata is missing required fields: {', '.join(missing)}")
        language = metadata.get("drawing_language")
        if not isinstance(language, dict):
            errors.append("drawing_language must be an object.")
        else:
            missing_language = sorted(REQUIRED_DRAWING_LANGUAGE - set(language))
            if missing_language:
                errors.append(
                    "drawing_language is missing required fields: " + ", ".join(missing_language)
                )
        target_sizes = metadata.get("target_sizes")
        if not isinstance(target_sizes, list) or not all(isinstance(size, (int, float)) for size in target_sizes):
            errors.append("target_sizes must be a numeric array.")
        elif str(metadata.get("role", "")).casefold() in {"interface icon", "navigation icon", "product icon"}:
            missing_sizes = [size for size in (16, 20, 24) if size not in target_sizes]
            if missing_sizes:
                errors.append(
                    "Interface icon metadata must include rendered QA targets 16, 20, and 24; missing: "
                    + ", ".join(map(str, missing_sizes))
                )
        checks.append("metadata/provenance contract inspected")

    try:
        root = ET.parse(svg_file).getroot()
    except FileNotFoundError:
        errors.append(f"SVG file not found: {svg_file}")
        return {"path": str(svg_file), "valid": False, "errors": errors, "warnings": warnings, "checks": checks}
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
        grid = metadata.get("grid") if metadata else None
        if isinstance(grid, (int, float)) and (view_box[2] != float(grid) or view_box[3] != float(grid)):
            errors.append(
                f"Metadata grid {grid} does not match viewBox dimensions {view_box[2]}×{view_box[3]}."
            )

    found_graphics = False
    monochrome = str(metadata.get("drawing_language", {}).get("mode", "")).casefold() in {
        "fill",
        "stroke",
        "mixed",
        "monochrome fill",
        "monochrome stroke",
        "monochrome mixed",
    }
    for element in root.iter():
        name = _local_name(element.tag)
        if name in FORBIDDEN_ELEMENTS:
            errors.append(f"Forbidden embedded or executable element: <{name}>.")
        if name in {"path", "circle", "ellipse", "rect", "line", "polyline", "polygon"}:
            found_graphics = True
        if name == "text":
            errors.append("Interface SVGs must not embed text; keep labels in accessible HTML or platform UI.")
        if name in {"filter", "mask", "pattern"}:
            warnings.append(
                f"<{name}> needs target-size render proof; effects and masks often blur or collapse in interface icons."
            )
        for attribute, value in element.attrib.items():
            local_attribute = _local_name(attribute)
            if local_attribute in {"href", "src"} and EXTERNAL_REFERENCE.match(str(value).strip()):
                errors.append(f"External or embedded reference is not allowed: {attribute}={value!r}.")
            if monochrome and local_attribute in PAINT_ATTRIBUTES:
                paint = str(value).strip().casefold()
                if paint not in SAFE_MONOCHROME_PAINT and not paint.startswith("url(#"):
                    errors.append(
                        f"Monochrome drawing language requires currentColor/none/inherit paint; found {attribute}={value!r}."
                    )
            if local_attribute == "style":
                warnings.append("Inline style attributes make drawing-language and state auditing harder; prefer explicit attributes.")

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
