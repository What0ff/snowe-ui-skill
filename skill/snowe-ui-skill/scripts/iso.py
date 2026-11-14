#!/usr/bin/env python3
"""Render a validated isometric scene description to a deterministic SVG.

A scene is JSON in grid units. Every object stands on an axis-aligned
footprint, and the generator owns projection, face shading, back-to-front
order, connector routing and label placement, so the projection, occlusion and
stroke errors of freehand drawing cannot occur. Intersecting volumes, unknown
types or fields, non-finite or out-of-range numbers, cyclic occlusion and
oversized scenes are refused with a message instead of being guessed.

The SVG is self-contained: colors resolve through CSS custom properties with
fallbacks (``--iso-top``, ``--iso-left``, ``--iso-right``, ``--iso-stroke``,
``--iso-detail``, ``--iso-accent``, ``--iso-text``, ``--iso-grid``,
``--iso-shadow``, ``--iso-font``), labels stay real ``<text>``, and every
object and connector carries a stable id, class and ``data-*`` attributes for
animation. Identical input produces identical bytes. A successful render
proves geometry and structure only; composition, legibility and fit still need
inspection at real size.

Schema 1.1 adds the ``technical`` hairline style, richer primitives (``tile``,
``core``, ``rack``, ``dashboard``, ``trees`` and new building and tree
options), currentColor icon SVGs projected onto faces, and connectors that end
on the visible surface, rise between levels and keep their markers visible. A
scene that uses none of them renders exactly as under schema 1.0.

Schema 1.2 draws objects as constructed things rather than labelled blocks:
openings with real depth, stepped buildings with lobbies, portals, parapets and
rooftop plant, tree species built from overlapping canopy volumes, a seeded and
collision-free micro-detail kit on boards and cores, database and document
models, bezelled screens on stands, rack bays, shadows clipped to their
support, pixel-snapped hairlines, upright or hidden label modes and warnings for
implausible relative sizes or labels that collide with lines and marks. It
applies only to scenes that declare it or use one of its fields, so 1.0 and 1.1
scenes keep their exact bytes.

    python iso.py render scene.json -o scene.svg --manifest scene.json
"""

from __future__ import annotations

import argparse
import heapq
import json
import math
import os
import re
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Callable

SCHEMA = "1.2"
SCHEMAS = ("1.0", "1.1", "1.2")
MAX_SCENE_BYTES = 1_000_000
MAX_ITEMS = 200
MAX_COORD = 100.0
MAX_SIZE = 60.0
MAX_CANVAS = 12_000.0
MAX_ELEMENTS = 20_000
MAX_LABEL = 40
MAX_TEXT_TOTAL = 4_000
MAX_VIA = 12
MAX_GRID_LINES = 400
MAX_GRID_DOTS = 6_000
EPS = 1e-9
SORT_MARGIN = 0.05
SQRT2 = math.sqrt(2.0)
TOKEN = re.compile(r"^[a-z][a-z0-9-]{0,47}$")
HEX = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f\u2028\u2029]")

PROJECTIONS = ("isometric", "dimetric")
STYLES = ("line", "solid", "technical")
FACES = ("top", "x+", "y+")
SIDES = ("x+", "x-", "y+", "y-")
GLYPHS_V10 = ("dot", "ring", "check", "plus", "bars", "user", "spark", "play")
GLYPHS_V11 = ("database", "docs", "apps", "chat", "layers", "chart")
GLYPHS = GLYPHS_V10 + GLYPHS_V11
TREE_SHAPES = ("round", "cone", "oval", "pine")
SPECIES = ("broadleaf", "columnar", "conifer")
TREE_SHAPES_V12 = SPECIES + ("mixed",)
LABEL_MODES = ("face", "upright", "hidden")
COLOR_ROLES = ("top", "left", "right", "stroke", "detail", "accent", "text", "grid", "shadow")
DEFAULT_COLORS = {
    "line": {
        "top": "#ffffff", "left": "#eef1f7", "right": "#dce2ec", "stroke": "#1b2232",
        "detail": "#8a94a8", "accent": "#3d5afe", "text": "#1b2232", "grid": "#d3d9e4", "shadow": "#1b2232",
    },
    "solid": {
        "top": "#e9edf6", "left": "#c5cde0", "right": "#a0abc6", "stroke": "#1b2232",
        "detail": "#56617d", "accent": "#3d5afe", "text": "#1b2232", "grid": "#d3d9e4", "shadow": "#1b2232",
    },
    "technical": {
        "top": "#ffffff", "left": "#f3f4f7", "right": "#e3e6ec", "stroke": "#2a303c",
        "detail": "#9aa2b1", "accent": "#3d5afe", "text": "#262c38", "grid": "#dadee6", "shadow": "#1b2232",
    },
}
# Outline and detail stroke widths (px) and connector gap (grid units) when the scene does not set them.
STYLE_DEFAULTS = {
    "line": {"stroke": 1.5, "detail_stroke": 1.0, "gap": 0.3},
    "solid": {"stroke": 1.5, "detail_stroke": 1.0, "gap": 0.3},
    "technical": {"stroke": 1.0, "detail_stroke": 0.6, "gap": 0.0},
}
# Schema 1.2 keeps every stroke at 1 CSS px or more: sub-pixel hairlines blur at 1x, so detail is told
# apart from outlines by tone instead of width.
STYLE_DEFAULTS_V12 = {**STYLE_DEFAULTS, "technical": {"stroke": 1.0, "detail_stroke": 1.0, "gap": 0.0}}
MIN_STROKE_V12 = 1.0
MIN_LABEL_PX = 11.0
# Face tone by the axis its outward normal points along: x -> right, y -> left, z -> top.
AXIS_TONE = ("iso-r", "iso-l", "iso-t")
ARROW_LENGTH = 0.3
PIN = 0.18
ARROW_HALF_WIDTH = 0.15
END_DOT = 0.09
PORT_DOT = 0.085
PLINTH_H = 0.14
CANOPY_DEPTH = 0.34
SIGN_H = 0.6
ROOF_UNIT_H = 0.36
CORE_PACKAGE_H = 0.2
CORE_PLATE_H = 0.06
CORE_CAP_H = 0.24
LANE = 0.6
MAX_ICONS = 32
MAX_ICON_BYTES = 65_536
MAX_ICON_NUMBERS = 4_000
SVG_NS = "{http://www.w3.org/2000/svg}"


class SceneError(ValueError):
    """A scene that cannot be rendered truthfully; ``errors`` lists every reason found."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = list(errors)
        super().__init__("; ".join(self.errors))


# --------------------------------------------------------------------------
# Projection


class Projection:
    """Orthographic camera at azimuth 45 degrees; one grid unit on x or y spans ``unit`` px.

    ``isometric`` draws both ground axes at 30 degrees with equal foreshortening
    on all three axes. ``dimetric`` is the 2:1 pixel-art projection (ground axes
    at about 26.57 degrees); its vertical axis is 1.095 times longer, as an
    orthographic camera at 30 degrees elevation requires.
    """

    def __init__(self, kind: str = "isometric", unit: float = 32.0) -> None:
        if kind not in PROJECTIONS:
            raise ValueError(f"unknown projection {kind!r}")
        theta = math.asin(math.tan(math.radians(30.0))) if kind == "isometric" else math.radians(30.0)
        self.kind = kind
        self.unit = float(unit)
        self.sin = math.sin(theta)
        self.cos = math.cos(theta)
        self.k = self.unit / math.sqrt(0.5 + 0.5 * self.sin * self.sin)
        # Direction toward the viewer; every component is positive.
        self.view = (self.cos / SQRT2, self.cos / SQRT2, self.sin)

    def vec(self, dx: float, dy: float, dz: float) -> tuple[float, float]:
        k = self.k
        return (k * (dx - dy) / SQRT2, k * ((dx + dy) / SQRT2 * self.sin - dz * self.cos))

    def __call__(self, x: float, y: float, z: float) -> tuple[float, float]:
        return self.vec(x, y, z)


def project(x: float, y: float, z: float, projection: str = "isometric", unit: float = 32.0) -> tuple[float, float]:
    """Project one grid point to unshifted screen coordinates (y grows downward)."""
    return Projection(projection, unit)(x, y, z)


# --------------------------------------------------------------------------
# Field validation

REQUIRED = object()


class Field:
    """One validated field. ``since`` names the schema that added the field; ``new`` maps enum values added
    after 1.0 to their schema (a plain tuple means 1.1)."""

    def __init__(self, kind: str, default: Any = REQUIRED, lo: float | None = None, hi: float | None = None,
                 choices: tuple[str, ...] = (), lo_open: bool = False, since: str | None = None,
                 new: tuple[str, ...] | dict[str, str] = ()) -> None:
        self.kind, self.default, self.lo, self.hi = kind, default, lo, hi
        self.choices, self.lo_open, self.since = choices, lo_open, since
        self.new = dict(new) if isinstance(new, dict) else dict.fromkeys(new, "1.1")


def _size(default: Any = REQUIRED, lo: float = 0.0, hi: float = MAX_SIZE) -> Field:
    return Field("num", default, lo, hi, lo_open=lo == 0.0)


def _v11(field: Field) -> Field:
    field.since = "1.1"
    return field


def _v12(field: Field) -> Field:
    field.since = "1.2"
    return field


def _v12_values(values: tuple[str, ...]) -> dict[str, str]:
    return dict.fromkeys(values, "1.2")


COMMON = {
    "id": Field("token"),
    "type": Field("type"),
    "role": Field("token", None),
    "order": Field("int", None, 0, 999),
    "accent": Field("bool", False),
}
PLACED = {
    "x": Field("num", REQUIRED, -MAX_COORD, MAX_COORD),
    "y": Field("num", REQUIRED, -MAX_COORD, MAX_COORD),
    "z": Field("num", 0.0, 0.0, MAX_SIZE),
}
LABEL = {
    "label": Field("text", ""),
    "label_size": Field("num", 11.0, 6.0, 36.0),
}
FACE_LABEL = {
    **LABEL,
    "label_face": Field("enum", "top", choices=FACES),
    "label_axis": Field("enum", None, choices=("x", "y")),
}
GLYPH = {"glyph": Field("enum", None, choices=GLYPHS, new=GLYPHS_V11)}
ICON = {"icon": _v11(Field("token", None))}
# Fields of the types added in schema 1.1 carry no ``since`` mark: the type itself is the 1.1 feature.
MARK = {"glyph": Field("enum", None, choices=GLYPHS), "icon": Field("token", None)}
AXIS = {"label_axis": Field("enum", None, choices=("x", "y"))}
SEED = Field("int", 1, 0, 9999)
TREE_SHAPE_NEW = _v12_values(TREE_SHAPES_V12)

TYPES: dict[str, dict[str, Field]] = {
    "box": {**COMMON, **PLACED, **FACE_LABEL, **GLYPH, **ICON, "w": _size(), "d": _size(), "h": _size(),
            "radius": Field("num", 0.0, 0.0, MAX_SIZE), "bands": Field("int", 0, 0, 24)},
    "slab": {**COMMON, **PLACED, **FACE_LABEL, **GLYPH, **ICON, "w": _size(), "d": _size(), "h": _size(0.25),
             "radius": Field("num", 0.2, 0.0, MAX_SIZE), "inset": Field("num", 0.0, 0.0, MAX_SIZE),
             "detail": _v12(Field("int", 0, 0, 3)), "seed": _v12(Field("int", 1, 0, 9999))},
    "stack": {**COMMON, **PLACED, **FACE_LABEL, "w": _size(), "d": _size(), "count": Field("int", REQUIRED, 2, 12),
              "h": _size(0.3), "gap": Field("num", 0.16, 0.0, 4.0), "radius": Field("num", 0.12, 0.0, MAX_SIZE),
              "leds": Field("bool", True), "front": Field("enum", "x+", choices=("x+", "y+"))},
    "chip": {**COMMON, **PLACED, **FACE_LABEL, **GLYPH, **ICON, "w": _size(), "d": _size(), "h": _size(0.3),
             "radius": Field("num", 0.12, 0.0, MAX_SIZE), "pins": Field("int", None, 0, 16), "die": Field("bool", True)},
    "cylinder": {**COMMON, **PLACED, **LABEL, **GLYPH, **ICON, "w": _size(), "h": _size(), "bands": Field("int", 0, 0, 24)},
    "building": {**COMMON, **PLACED, **FACE_LABEL, "w": _size(), "d": _size(), "floors": Field("int", REQUIRED, 1, 40),
                 "floor_h": _size(0.55, 0.0, 4.0), "roof": Field("bool", True),
                 "windows": Field("enum", "grid", choices=("grid", "ribbon", "none", "curtain", "bands", "fins", "punched"),
                                  new={"curtain": "1.1", "bands": "1.1", "fins": "1.2", "punched": "1.2"}),
                 "entrance": _v11(Field("enum", None, choices=("x+", "y+"))),
                 "plinth": _v11(Field("num", 0.0, 0.0, 2.0)),
                 "roof_unit": _v11(Field("bool", False)),
                 "sign": _v11(Field("text", "")),
                 "sign_face": _v11(Field("enum", None, choices=("x+", "y+"))),
                 "glyph": _v11(Field("enum", None, choices=GLYPHS)), **ICON,
                 "massing": _v12(Field("enum", "block", choices=("block", "stepped"))),
                 "lobby": _v12(Field("bool", True)),
                 "parapet": _v12(Field("bool", True)),
                 "rooftop": _v12(Field("enum", "plant", choices=("none", "plant"))),
                 "sign_mount": _v12(Field("enum", "wall", choices=("wall", "plaque", "roof"))),
                 "seed": _v12(Field("int", 1, 0, 9999))},
    "card": {**COMMON, **PLACED, **LABEL, **GLYPH, **ICON, "w": _size(), "d": _size(None), "h": _size(None),
             "orient": Field("enum", "flat", choices=("flat", "x+", "y+")), "t": _size(0.12, 0.0, 2.0),
             "radius": Field("num", 0.16, 0.0, MAX_SIZE), "lines": Field("int", 0, 0, 4)},
    "screen": {**COMMON, **PLACED, **LABEL, "w": _size(), "h": _size(), "orient": Field("enum", "y+", choices=("x+", "y+")),
               "t": _size(0.14, 0.0, 2.0), "radius": Field("num", 0.08, 0.0, MAX_SIZE), "lines": Field("int", 3, 0, 6),
               "stand": Field("bool", False)},
    "tree": {**COMMON, **PLACED, "w": _size(), "h": _size(),
             "shape": Field("enum", "round", choices=TREE_SHAPES + SPECIES,
                            new={"oval": "1.1", "pine": "1.1", **_v12_values(SPECIES)}),
             "planter": _v11(Field("bool", False)), "seed": _v12(Field("int", 1, 0, 9999))},
    "trees": {**COMMON, **PLACED, "w": _size(), "d": _size(), "count": Field("int", REQUIRED, 1, 24),
              "layout": Field("enum", "row", choices=("row", "grid", "scatter")), "size": _size(0.6, 0.0, 4.0),
              "h": _size(None, 0.0, 12.0), "shape": Field("enum", "oval", choices=TREE_SHAPES + TREE_SHAPES_V12,
                                                         new=TREE_SHAPE_NEW),
              "planter": Field("bool", False), "seed": Field("int", 1, 0, 9999), "vary": _v12(Field("bool", True))},
    "tile": {**COMMON, **PLACED, **LABEL, **AXIS, **MARK, "w": _size(), "d": _size(), "h": _size(0.35),
             "radius": Field("num", 0.22, 0.0, MAX_SIZE), "inset": Field("num", 0.0, 0.0, MAX_SIZE),
             "layout": Field("enum", "stack", choices=("stack", "row")),
             "model": _v12(Field("enum", "none", choices=("none", "database", "documents")))},
    "core": {**COMMON, **PLACED, **LABEL, **AXIS, **MARK, "label_face": Field("enum", "top", choices=FACES),
             "w": _size(), "d": _size(), "h": _size(0.3, 0.0, 4.0), "radius": Field("num", 0.16, 0.0, MAX_SIZE),
             "layers": Field("int", 2, 0, 4), "spacing": Field("num", 0.6, 0.2, 4.0), "cap": Field("bool", True),
             "pins": Field("bool", True), "parts": Field("bool", True),
             "detail": _v12(Field("int", 2, 0, 3)), "seed": _v12(Field("int", 1, 0, 9999))},
    "rack": {**COMMON, **PLACED, **FACE_LABEL, **MARK, "w": _size(), "d": _size(), "units": Field("int", 4, 1, 16),
             "unit_h": _size(0.32, 0.0, 2.0), "front": Field("enum", "y+", choices=("x+", "y+")),
             "radius": Field("num", 0.06, 0.0, MAX_SIZE), "leds": Field("bool", True)},
    "dashboard": {**COMMON, **PLACED, **LABEL, **MARK, "w": _size(), "h": _size(),
                  "orient": Field("enum", "y+", choices=("x+", "y+")), "t": _size(0.14, 0.0, 2.0),
                  "radius": Field("num", 0.1, 0.0, MAX_SIZE), "stand": Field("bool", False),
                  "chart": Field("enum", "both", choices=("line", "bars", "both", "none")),
                  "rows": Field("int", 3, 0, 5), "series": Field("series", None), "header": Field("bool", True)},
    "database": {**COMMON, **PLACED, **LABEL, **MARK, "w": _size(), "h": _size(),
                 "drums": Field("int", 3, 1, 6), "leds": Field("bool", True)},
    "documents": {**COMMON, **PLACED, **LABEL, "w": _size(), "d": _size(None), "h": _size(None),
                  "orient": Field("enum", "y+", choices=("flat", "x+", "y+")), "sheets": Field("int", 3, 1, 5),
                  "lines": Field("int", 4, 0, 6)},
    "ground-grid": {"id": Field("token"), "type": Field("type"), "x": PLACED["x"], "y": PLACED["y"],
                    "w": _size(), "d": _size(), "step": Field("num", 1.0, 0.25, 10.0),
                    "pattern": Field("enum", "lines", choices=("lines", "dots", "mesh"), new=("mesh",)),
                    "fade": Field("bool", True)},
    "connector": {"id": Field("token", None), "type": Field("type"), "role": Field("token", None),
                  "order": Field("int", None, 0, 999), "accent": Field("bool", False),
                  "from": Field("token"), "to": Field("token"),
                  "from_side": Field("enum", None, choices=SIDES), "to_side": Field("enum", None, choices=SIDES),
                  "from_offset": Field("num", 0.0, -MAX_SIZE, MAX_SIZE), "to_offset": Field("num", 0.0, -MAX_SIZE, MAX_SIZE),
                  "via": Field("points", []),
                  "start": Field("enum", "none", choices=("none", "dot", "port"), new=("port",)),
                  "end": Field("enum", "arrow", choices=("none", "dot", "arrow", "port"), new=("port",)),
                  "gap": Field("num", None, 0.0, 4.0), "radius": Field("num", 0.35, 0.0, 4.0),
                  "z": Field("num", None, 0.0, MAX_SIZE),
                  "route": _v11(Field("enum", "level", choices=("level", "ground"))),
                  "from_z": _v11(Field("num", None, 0.0, MAX_SIZE)), "to_z": _v11(Field("num", None, 0.0, MAX_SIZE)),
                  "joints": _v11(Field("bool", False))},
}
V11_TYPES = ("trees", "tile", "core", "rack", "dashboard")
V12_TYPES = ("database", "documents")
SCENE_FIELDS = {
    "schema": Field("enum", None, choices=SCHEMAS),
    "projection": Field("enum", "isometric", choices=PROJECTIONS),
    "style": Field("enum", "line", choices=STYLES, new=("technical",)),
    "unit": Field("num", 32.0, 8.0, 96.0),
    "padding": Field("num", 16.0, 0.0, 400.0),
    "stroke": Field("num", None, 0.25, 6.0),
    "detail_stroke": Field("num", None, 0.25, 6.0),
    "title": Field("desc", ""),
    "desc": Field("desc", ""),
    "id_prefix": Field("prefix", "iso-"),
    "colors": Field("colors", {}),
    "icons": _v11(Field("icons", {})),
    "shadows": _v11(Field("bool", None)),
    "labels": _v12(Field("enum", "face", choices=LABEL_MODES)),
    "objects": Field("objects"),
}


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _check(field: Field, value: Any, where: str, errors: list[str]) -> Any:
    kind = field.kind
    if kind in ("num", "int"):
        if _is_number(value) and isinstance(value, int) and abs(value) > 10 ** 15:
            errors.append(f"{where} is out of range; got {value!r}")
            return None
        if not _is_number(value) or (kind == "int" and (not isinstance(value, int) and not float(value).is_integer())):
            errors.append(f"{where} must be {'an integer' if kind == 'int' else 'a number'}; got {value!r}")
            return None
        number = float(value)
        if not math.isfinite(number):
            errors.append(f"{where} must be finite; got {value!r}")
            return None
        too_low = field.lo is not None and (number <= field.lo if field.lo_open else number < field.lo)
        too_high = field.hi is not None and number > field.hi
        if too_low or too_high:
            low = "(" if field.lo_open else "["
            errors.append(f"{where} must be in {low}{_num_text(field.lo)}, {_num_text(field.hi)}]; got {value!r}")
            return None
        return int(number) if kind == "int" else number
    if kind == "bool":
        if not isinstance(value, bool):
            errors.append(f"{where} must be true or false; got {value!r}")
            return None
        return value
    if kind == "enum":
        if value not in field.choices:
            errors.append(f"{where} must be one of {', '.join(field.choices)}; got {value!r}")
            return None
        return value
    if kind in ("token", "prefix"):
        pattern = TOKEN if kind == "token" else re.compile(r"^[a-z][a-z0-9-]{0,23}$")
        if not isinstance(value, str) or not pattern.match(value):
            errors.append(f"{where} must be a lowercase token (a-z, 0-9, '-', starting with a letter); got {value!r}")
            return None
        return value
    if kind in ("text", "desc"):
        limit = MAX_LABEL if kind == "text" else 400
        if not isinstance(value, str) or CONTROL.search(value) or len(value) > limit or value != value.strip():
            errors.append(f"{where} must be a single-line string of at most {limit} characters without "
                          f"control characters or surrounding spaces; got {value!r}")
            return None
        return value
    if kind == "points":
        if not isinstance(value, list) or len(value) > MAX_VIA:
            errors.append(f"{where} must be a list of at most {MAX_VIA} [x, y] points")
            return None
        points = []
        for index, point in enumerate(value):
            if (not isinstance(point, list) or len(point) != 2 or not all(_is_number(v) for v in point)
                    or not all(abs(v) <= MAX_COORD for v in point)):
                errors.append(f"{where}[{index}] must be [x, y] with finite numbers in [-{_num_text(MAX_COORD)}, "
                              f"{_num_text(MAX_COORD)}]; got {point!r}")
                return None
            points.append((float(point[0]), float(point[1])))
        return points
    if kind == "colors":
        if not isinstance(value, dict):
            errors.append(f"{where} must be an object mapping color roles to #rgb or #rrggbb")
            return None
        colors = {}
        for key in value:
            if key not in COLOR_ROLES:
                errors.append(f"{where}: unknown color role {key!r}; allowed: {', '.join(COLOR_ROLES)}")
            elif not isinstance(value[key], str) or not HEX.match(value[key]):
                errors.append(f"{where}.{key} must be #rgb or #rrggbb; got {value[key]!r}")
            else:
                colors[key] = value[key].lower()
        return colors
    if kind == "series":
        if (not isinstance(value, list) or not 2 <= len(value) <= 16
                or not all(_is_number(v) and math.isfinite(float(v)) and 0.0 <= float(v) <= 1.0 for v in value)):
            errors.append(f"{where} must be a list of 2 to 16 numbers in [0, 1]; got {value!r}"[:300])
            return None
        return [float(v) for v in value]
    if kind == "icons":
        if not isinstance(value, dict) or len(value) > MAX_ICONS:
            errors.append(f"{where} must be an object mapping at most {MAX_ICONS} icon names to relative .svg paths")
            return None
        icons = {}
        for key in value:
            path = value[key]
            if not isinstance(key, str) or not TOKEN.match(key):
                errors.append(f"{where}: icon name {key!r} must be a lowercase token")
            elif (not isinstance(path, str) or not path.lower().endswith(".svg") or len(path) > 260
                  or CONTROL.search(path) or "\x00" in path or Path(path).is_absolute() or path.startswith(("/", "\\"))):
                errors.append(f"{where}.{key} must be a relative path to an .svg file; got {path!r}")
            else:
                icons[key] = path
        return icons
    raise AssertionError(kind)


def _num_text(value: float | None) -> str:
    if value is None:
        return "inf"
    return _fmt(value)


def _read_fields(raw: dict[str, Any], spec: dict[str, Field], where: str, errors: list[str],
                 features: list[tuple[str, str]] | None = None) -> dict[str, Any]:
    """Validate every field; ``features`` collects (schema, description) for each post-1.0 feature used."""
    out: dict[str, Any] = {}
    for key in raw:
        if key not in spec:
            errors.append(f"{where}: unknown field {key!r}; allowed: {', '.join(spec)}")
    for key, field in spec.items():
        if field.kind in ("type", "objects"):
            continue
        if key in raw:
            out[key] = _check(field, raw[key], f"{where}.{key}", errors)
            if features is not None:
                value = raw[key]
                if field.since:
                    features.append((field.since, f"{where}.{key}"))
                elif field.new and isinstance(value, str) and value in field.new:
                    features.append((field.new[value], f"{where}.{key} {value!r}"))
                elif field.kind == "colors" and isinstance(value, dict) and "shadow" in value:
                    features.append(("1.1", f"{where}.shadow"))
        elif field.default is REQUIRED:
            errors.append(f"{where}: missing required field {key!r}")
            out[key] = None
        else:
            out[key] = field.default
    return out


# --------------------------------------------------------------------------
# Scene normalization


def _parse_json(text: str) -> Any:
    def no_constant(name: str) -> Any:
        raise SceneError([f"scene: non-finite number {name} is not allowed"])

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        seen: dict[str, Any] = {}
        for key, value in pairs:
            if key in seen:
                raise SceneError([f"scene: duplicate key {key!r}"])
            seen[key] = value
        return seen

    try:
        return json.loads(text, parse_constant=no_constant, object_pairs_hook=unique)
    except json.JSONDecodeError as error:
        raise SceneError([f"scene: invalid JSON at line {error.lineno} column {error.colno}: {error.msg}"]) from None
    except RecursionError:
        raise SceneError(["scene: JSON nesting is too deep"]) from None
    except ValueError as error:
        raise SceneError([f"scene: invalid JSON: {error}"]) from None


def load_scene(source: str | Path) -> dict[str, Any]:
    """Read a scene file under the byte budget and parse it strictly (no NaN, no duplicate keys)."""
    path = Path(source)
    try:
        if not path.is_file():
            raise SceneError([f"scene: {path} is not a regular file"])
        if path.stat().st_size > MAX_SCENE_BYTES:
            raise SceneError([f"scene: {path} exceeds the {MAX_SCENE_BYTES}-byte budget"])
        data = path.read_bytes()
    except OSError as error:
        raise SceneError([f"scene: cannot read {path}: {error.strerror or error}"]) from None
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise SceneError([f"scene: {path} is not UTF-8"]) from None
    scene = _parse_json(text)
    if not isinstance(scene, dict):
        raise SceneError(["scene: the top level must be a JSON object"])
    return scene


# --------------------------------------------------------------------------
# Icons: a strict currentColor SVG subset, re-serialized from parsed numbers only.

ICON_GEOMETRY = {
    "path": ("d",), "circle": ("cx", "cy", "r"), "ellipse": ("cx", "cy", "rx", "ry"),
    "rect": ("x", "y", "width", "height", "rx", "ry"), "line": ("x1", "y1", "x2", "y2"),
    "polyline": ("points",), "polygon": ("points",),
}
ICON_REQUIRED = {"path": ("d",), "circle": ("r",), "ellipse": ("rx", "ry"), "rect": ("width", "height"),
                 "line": (), "polyline": ("points",), "polygon": ("points",)}
ICON_PAINT = ("fill", "stroke", "opacity", "fill-opacity", "stroke-opacity", "fill-rule")
ICON_IGNORED = ("id", "class", "role", "focusable", "version", "stroke-width", "stroke-linecap", "stroke-linejoin",
                "stroke-miterlimit", "clip-rule", "shape-rendering")
PATH_ARGS = {"M": 2, "L": 2, "T": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "A": 7, "Z": 0}
NUMBER = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")
SEPARATORS = re.compile(r"[\s,]*")


class IconError(ValueError):
    """An icon SVG outside the accepted currentColor subset."""


def _icon_number(text: str, what: str) -> float:
    if not isinstance(text, str) or not re.fullmatch(r"\s*" + NUMBER.pattern + r"\s*", text):
        raise IconError(f"{what} must be a plain number; got {text!r}"[:160])
    value = float(text)
    if not math.isfinite(value) or abs(value) > 1e6:
        raise IconError(f"{what} is out of range")
    return value


def _icon_path(d: str, budget: list[int]) -> str:
    """Re-emit path data from its parsed commands and numbers; refuse anything else."""
    parts: list[str] = []
    pos, cmd = 0, None
    while True:
        pos = SEPARATORS.match(d, pos).end()
        if pos >= len(d):
            break
        char = d[pos]
        if char.upper() in PATH_ARGS:
            cmd = char
            pos += 1
            if not parts and cmd not in "Mm":
                raise IconError("path data must start with M")
            if cmd in "Zz":
                parts.append("Z")
                continue
        elif cmd is None or cmd in "Zz":
            raise IconError(f"path data has a number without a command near position {pos}")
        args = PATH_ARGS[cmd.upper()]
        values: list[str] = []
        for k in range(args):
            pos = SEPARATORS.match(d, pos).end()
            if cmd in "Aa" and k in (3, 4):
                if pos < len(d) and d[pos] in "01":
                    values.append(d[pos])
                    pos += 1
                    continue
                raise IconError("arc flags must be 0 or 1")
            match = NUMBER.match(d, pos)
            if not match:
                raise IconError(f"path command {cmd} needs {args} numbers")
            values.append(_fmt(_icon_number(match.group(), "a path number"), 3))
            pos = match.end()
        budget[0] -= args
        if budget[0] < 0:
            raise IconError(f"the icon holds more than {MAX_ICON_NUMBERS} numbers")
        parts.append(cmd + " ".join(values))
        if cmd in "Mm":
            cmd = "L" if cmd == "M" else "l"
    if not parts:
        raise IconError("path data is empty")
    return " ".join(parts)


def _icon_paint(value: str, what: str) -> str:
    lowered = value.strip().lower()
    if lowered == "currentcolor":
        return "c"
    if lowered == "none":
        return "n"
    raise IconError(f"{what} must be currentColor or none; got {value!r}"[:160])


def _icon_opacity(value: str, what: str) -> float:
    number = _icon_number(value, what)
    if not 0.0 <= number <= 1.0:
        raise IconError(f"{what} must be in [0, 1]")
    return number


def parse_icon(text: str) -> dict[str, Any]:
    """Parse a currentColor icon SVG into a viewBox and re-serializable elements, or raise IconError."""
    if re.search(r"<!(?:DOCTYPE|ENTITY)", text, re.IGNORECASE):
        raise IconError("DOCTYPE and ENTITY declarations are not allowed")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as error:
        raise IconError(f"not well-formed XML ({error})") from None
    if root.tag != SVG_NS + "svg":
        raise IconError("the root element must be an SVG <svg> in the SVG namespace")
    box_text = root.get("viewBox")
    if box_text is None:
        raise IconError("the root <svg> needs a viewBox")
    numbers = [_icon_number(v, "viewBox") for v in re.split(r"[\s,]+", box_text.strip())] if box_text.strip() else []
    if len(numbers) != 4 or numbers[2] <= 0 or numbers[3] <= 0:
        raise IconError("viewBox must be four numbers with a positive width and height")
    elements: list[tuple[str, str, str]] = []
    budget = [MAX_ICON_NUMBERS]

    def walk(node: ET.Element, state: dict[str, Any], depth: int) -> None:
        tag = node.tag[len(SVG_NS):] if node.tag.startswith(SVG_NS) else None
        if tag in ("title", "desc"):
            return
        if tag is None or (tag not in ICON_GEOMETRY and tag not in ("svg", "g")) or (tag == "svg" and depth):
            raise IconError(f"element {node.tag!r} is not allowed (use svg, g, path, circle, ellipse, rect, line, "
                            f"polyline or polygon)")
        if depth > 8:
            raise IconError("groups are nested too deeply")
        state = dict(state)
        geometry: dict[str, str] = {}
        for key, value in node.attrib.items():
            if key.startswith("{"):
                raise IconError(f"namespaced attribute {key!r} is not allowed")
            if tag in ICON_GEOMETRY and key in ICON_GEOMETRY[tag]:
                geometry[key] = value
            elif key in ("fill", "stroke"):
                state[key] = _icon_paint(value, key)
            elif key in ("opacity", "fill-opacity", "stroke-opacity"):
                state[key] = state[key] * _icon_opacity(value, key)
            elif key == "fill-rule":
                if value not in ("nonzero", "evenodd"):
                    raise IconError(f"fill-rule must be nonzero or evenodd; got {value!r}")
                state["fill-rule"] = value
            elif (key in ICON_IGNORED or key.startswith(("data-", "aria-"))
                  or (tag == "svg" and key in ("viewBox", "width", "height", "xmlns"))):
                continue
            else:
                raise IconError(f"attribute {key!r} is not allowed on <{tag}>")
        if tag in ("svg", "g"):
            if len(elements) > 400:
                raise IconError("the icon holds more than 400 elements")
            for child in node:
                walk(child, state, depth + 1)
            return
        if len(node):
            raise IconError(f"<{tag}> must not contain child elements")
        for key in ICON_REQUIRED[tag]:
            if key not in geometry:
                raise IconError(f"<{tag}> needs {key!r}")
        fill, stroke = state["fill"], state["stroke"]
        if fill is None:
            raise IconError(f"<{tag}> inherits the default black fill; set fill to currentColor or none")
        kind = ("f" if fill == "c" else "") + ("s" if stroke == "c" else "")
        if not kind:
            return
        attrs: list[str] = []
        for key in ICON_GEOMETRY[tag]:
            if key not in geometry:
                continue
            if key == "d":
                attrs.append(f'd="{_icon_path(geometry[key], budget)}"')
            elif key == "points":
                values = [v for v in re.split(r"[\s,]+", geometry[key].strip()) if v]
                if len(values) < 4 or len(values) % 2:
                    raise IconError(f"<{tag}> points must hold at least two x,y pairs")
                budget[0] -= len(values)
                if budget[0] < 0:
                    raise IconError(f"the icon holds more than {MAX_ICON_NUMBERS} numbers")
                attrs.append(f'points="{" ".join(_fmt(_icon_number(v, "a point"), 3) for v in values)}"')
            else:
                number = _icon_number(geometry[key], f"<{tag}> {key}")
                if key in ("r", "rx", "ry", "width", "height") and number < 0:
                    raise IconError(f"<{tag}> {key} must not be negative")
                attrs.append(f'{key}="{_fmt(number, 3)}"')
        if "f" in kind and state["fill-rule"] == "evenodd":
            attrs.append('fill-rule="evenodd"')
        if "f" in kind and state["opacity"] * state["fill-opacity"] < 1.0:
            attrs.append(f'fill-opacity="{_fmt(state["opacity"] * state["fill-opacity"], 3)}"')
        if "s" in kind and state["opacity"] * state["stroke-opacity"] < 1.0:
            attrs.append(f'stroke-opacity="{_fmt(state["opacity"] * state["stroke-opacity"], 3)}"')
        elements.append((tag, kind, " ".join(attrs)))

    walk(root, {"fill": None, "stroke": "n", "opacity": 1.0, "fill-opacity": 1.0, "stroke-opacity": 1.0,
                "fill-rule": "nonzero"}, 0)
    if not elements:
        raise IconError("the icon draws nothing in currentColor")
    return {"viewbox": tuple(numbers), "elements": elements}


def _load_icons(icons: dict[str, str], base: Path, errors: list[str]) -> dict[str, dict[str, Any]]:
    loaded: dict[str, dict[str, Any]] = {}
    for name, relative in icons.items():
        where = f"scene.icons.{name}"
        path = base / relative
        try:
            if not path.is_file():
                errors.append(f"{where}: {relative} is not a file next to the scene")
                continue
            if path.stat().st_size > MAX_ICON_BYTES:
                errors.append(f"{where}: {relative} exceeds the {MAX_ICON_BYTES}-byte icon budget")
                continue
            text = path.read_bytes().decode("utf-8-sig")
        except OSError as error:
            errors.append(f"{where}: cannot read {relative}: {error.strerror or error}")
            continue
        except UnicodeDecodeError:
            errors.append(f"{where}: {relative} is not UTF-8")
            continue
        try:
            loaded[name] = parse_icon(text)
        except IconError as error:
            errors.append(f"{where}: {relative}: {error}")
    return loaded


def _box(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> tuple[float, ...]:
    return (x0, x1, y0, y1, z0, z1)


TREE_MIN_H = {"round": 1.1, "cone": 1.0, "oval": 1.4, "pine": 1.2}
TREE_DEFAULT_H = {"round": 1.7, "cone": 1.6, "oval": 1.9, "pine": 1.8}


def _tree_positions(item: dict[str, Any], where: str, errors: list[str]) -> list[tuple[float, float]] | None:
    """Place a group's tree centers deterministically: a row, a near-square grid, or a seeded jitter inside grid cells."""
    x, y, w, d, count, size = item["x"], item["y"], item["w"], item["d"], item["count"], item["size"]
    if size > min(w, d) + EPS:
        errors.append(f"{where}: tree size {_fmt(size)} exceeds the area's shorter side ({_fmt(min(w, d))})")
        return None
    if item["layout"] == "row":
        along_x = w >= d - EPS
        length = w if along_x else d
        if count * size > length + EPS:
            errors.append(f"{where}: {count} trees of size {_fmt(size)} need {_fmt(count * size)} along the row; "
                          f"the area offers {_fmt(length)}")
            return None
        pitch = length / count
        if along_x:
            return [(x + pitch * (i + 0.5), y + d / 2) for i in range(count)]
        return [(x + w / 2, y + pitch * (i + 0.5)) for i in range(count)]
    cols = max(1, min(count, int(round(math.sqrt(count * w / d)))))
    rows = math.ceil(count / cols)
    cell_w, cell_d = w / cols, d / rows
    if size > min(cell_w, cell_d) + EPS:
        errors.append(f"{where}: {count} trees of size {_fmt(size)} do not fit a {cols} x {rows} {item['layout']} "
                      f"in {_fmt(w)} x {_fmt(d)}; enlarge the area or lower count or size")
        return None
    state = item["seed"] * 7919 + 17
    points = []
    for i in range(count):
        row, col = divmod(i, cols)
        cx, cy = x + cell_w * (col + 0.5), y + cell_d * (row + 0.5)
        if item["layout"] == "scatter":
            state = (state * 1103515245 + 12345) % 2147483648
            cx += (state / 2147483648 - 0.5) * (cell_w - size)
            state = (state * 1103515245 + 12345) % 2147483648
            cy += (state / 2147483648 - 0.5) * (cell_d - size)
        points.append((cx, cy))
    return points


# --------------------------------------------------------------------------
# Schema 1.2 geometry: relative sizes, species, building massing and stands.

# Canopy diameter to height: a species reads by its proportions before its outline.
SPECIES_RATIO = {"broadleaf": 1.6, "columnar": 2.3, "conifer": 1.9}
SPECIES_MIN = {"broadleaf": 1.2, "columnar": 1.8, "conifer": 1.5}
SPECIES_OF = {"round": "broadleaf", "oval": "broadleaf", "cone": "conifer", "pine": "conifer"}
TREE_SIZE_V12 = 0.5
LOBBY_RATIO = 1.45
PARAPET_H = 0.1
PARAPET_T = 0.07
PORTAL_DEPTH = 0.3
PORTAL_LIP = 0.1
ROOFTOP_H = 0.44
STAND_LIFT = 0.3
MODEL_SHARE = 0.36
# Documented relative-size rules (grid units, or multiples of the scene's floor height). render() warns when a
# 1.2 scene leaves them; see the scale table in illustration-craft.md.
SCALE = {
    "floor_h": (0.4, 0.75),
    "tree_floors": (0.9, 2.0),
    "satellite_h_floors": 1.0,
    "satellite_share": 0.4,
}


class _Rand:
    """A small deterministic generator: identical seeds give identical sequences on every platform."""

    def __init__(self, seed: int, salt: int = 0) -> None:
        self.state = (seed * 7919 + 17 + salt * 104729) % 2147483648

    def random(self) -> float:
        self.state = (self.state * 1103515245 + 12345) % 2147483648
        return self.state / 2147483648

    def uniform(self, lo: float, hi: float) -> float:
        return lo + (hi - lo) * self.random()


def _v12_defaults(item: dict[str, Any]) -> None:
    """Defaults that schema 1.2 changes for fields older schemas already had."""
    kind, given = item["type"], item["given"]
    if kind == "trees":
        if "shape" not in given:
            item["shape"] = "broadleaf"
        if "size" not in given:
            item["size"] = TREE_SIZE_V12
    if kind == "tree" and "shape" not in given:
        item["shape"] = "broadleaf"
    if kind in ("screen", "dashboard") and "stand" not in given:
        item["stand"] = True


def _tree_plan(item: dict[str, Any], where: str, errors: list[str]) -> list[dict[str, Any]] | None:
    """Species, size and seeded variation for every tree of a 1.2 ``tree`` or ``trees`` object."""
    if item["type"] == "tree":
        species = SPECIES_OF.get(item["shape"], item["shape"])
        w, h = item["w"], item["h"]
        if h < w * SPECIES_MIN[species] - EPS:
            errors.append(f"{where}: a {species} tree needs h >= {_fmt(SPECIES_MIN[species])} * w; "
                          f"got h={_fmt(h)}, w={_fmt(w)}")
            return None
        return [{"cx": item["x"] + w / 2, "cy": item["y"] + w / 2, "species": species, "w": w, "h": h,
                 "mirror": item["seed"] % 2 == 1, "seed": item["seed"]}]
    shape, size = item["shape"], item["size"]
    rng = _Rand(item["seed"], 3)
    if shape != "mixed":
        species = SPECIES_OF.get(shape, shape)
        height = item["h"] if item["h"] is not None else size * SPECIES_RATIO[species]
        if height < size * SPECIES_MIN[species] - EPS:
            errors.append(f"{where}: {species} trees need h >= {_fmt(SPECIES_MIN[species])} * size; "
                          f"got h={_fmt(height)}, size={_fmt(size)}")
            return None
    positions = _tree_positions(item, where, errors)
    if positions is None:
        return None
    plan = []
    for index, (cx, cy) in enumerate(positions):
        pick = rng.random()
        scale = rng.uniform(0.86, 1.0) if item["vary"] else 1.0
        mirror = rng.random() < 0.5 if item["vary"] else False
        if shape == "mixed":
            species = "broadleaf" if pick < 0.6 else ("columnar" if pick < 0.8 else "conifer")
        else:
            species = SPECIES_OF.get(shape, shape)
        base = item["h"] if item["h"] is not None else size * SPECIES_RATIO["broadleaf" if shape == "mixed" else species]
        if shape == "mixed":
            base *= SPECIES_RATIO[species] / SPECIES_RATIO["broadleaf"]
        plan.append({"cx": cx, "cy": cy, "species": species, "w": size * scale, "h": base * scale,
                     "mirror": mirror, "seed": item["seed"] * 31 + index})
    return plan


def _building_volumes(item: dict[str, Any], base: float, where: str, errors: list[str]) -> list[dict[str, Any]] | None:
    """The volumes of a 1.2 building: one block, or a tall main block, a lower front block holding the entrance
    and a low wing, each with its own floors and setbacks."""
    x, y, w, d = item["x"], item["y"], item["w"], item["d"]
    floors, floor_h = item["floors"], item["floor_h"]
    lobby = floor_h * LOBBY_RATIO if item["lobby"] else floor_h
    cap = PARAPET_H if item["parapet"] else 0.0

    def height(count: int) -> float:
        return lobby + (count - 1) * floor_h + cap

    if item["massing"] == "block":
        return [{"box": _box(x, x + w, y, y + d, base, base + height(floors)), "floors": floors, "role": "main",
                 "lobby": lobby, "cap": cap}]
    if floors < 3 or min(w, d) < 2.0 - EPS:
        errors.append(f"{where}: stepped massing needs at least 3 floors and w and d of at least 2")
        return None
    face = item.get("entrance") or item.get("sign_face") or "x+"
    a, b, c = 0.56, 0.72, 0.8
    if face == "x+":
        main, wing, front = (x, x + a * w, y, y + b * d), (x, x + a * w, y + b * d, y + d), (x + a * w, x + w, y, y + c * d)
    else:
        main, wing, front = (x, x + b * w, y, y + a * d), (x + b * w, x + w, y, y + a * d), (x, x + c * w, y + a * d, y + d)
    counts = {"main": floors, "wing": max(1, round(floors * 0.3)), "front": max(2, round(floors * 0.6))}
    return [{"box": _box(*rect, base, base + height(counts[role])), "floors": counts[role], "role": role,
             "lobby": lobby, "cap": cap}
            for role, rect in (("main", main), ("wing", wing), ("front", front))]


def _geometry_building_v12(item: dict[str, Any], where: str, errors: list[str]) -> bool:
    x, y, z, w, d = item["x"], item["y"], item["z"], item["w"], item["d"]
    plinth = item.get("plinth") or 0.0
    base = z + (PLINTH_H if plinth > 0 else 0.0)
    volumes = _building_volumes(item, base, where, errors)
    if volumes is None:
        return False
    entry = volumes[-1]
    item["volumes"], item["entry"] = volumes, entry
    top = max(v["box"][5] for v in volumes)
    body = _box(x, x + w, y, y + d, base, top)
    x0, x1, y0, y1 = x - plinth, x + w + plinth, y - plinth, y + d + plinth
    portal = None
    face = item.get("entrance")
    if face:
        ex0, ex1, ey0, ey1 = entry["box"][:4]
        span = (ey1 - ey0) if face == "x+" else (ex1 - ex0)
        width = min(1.3, span * 0.5)
        height = entry["lobby"] + 0.16
        mid = (ey0 + ey1) / 2 if face == "x+" else (ex0 + ex1) / 2
        reach = PORTAL_DEPTH + PORTAL_LIP
        if face == "x+":
            portal = _box(ex1, ex1 + PORTAL_DEPTH, mid - width / 2, mid + width / 2, base, base + height)
            x1 = max(x1, ex1 + reach)
        else:
            portal = _box(mid - width / 2, mid + width / 2, ey1, ey1 + PORTAL_DEPTH, base, base + height)
            y1 = max(y1, ey1 + reach)
    item["portal"] = portal
    space_top = top
    if item["rooftop"] == "plant":
        main = volumes[0]
        space_top = max(space_top, main["box"][5] - main["cap"] + ROOFTOP_H)
    if item.get("sign") and item["sign_mount"] == "roof":
        space_top = max(space_top, top + SIGN_H)
    item["body"], item["space"] = body, _box(x0, x1, y0, y1, z, space_top)
    return True


def _stand_boxes(item: dict[str, Any], panel: tuple[float, ...]) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """A monitor stand: a foot plate under the panel and a neck rising behind it to mid-height."""
    x0, x1, y0, y1, z0, z1 = panel
    base = item["z"]
    if item["orient"] == "x+":
        cy = (y0 + y1) / 2
        half = min(0.45, (y1 - y0) * 0.16)
        foot = _box(x0 - 0.3, x1 + 0.24, cy - half, cy + half, base, base + 0.05)
        neck = _box(x0 - 0.13, x0, cy - 0.08, cy + 0.08, base + 0.05, z0 + (z1 - z0) * 0.42)
    else:
        cx = (x0 + x1) / 2
        half = min(0.45, (x1 - x0) * 0.16)
        foot = _box(cx - half, cx + half, y0 - 0.3, y1 + 0.24, base, base + 0.05)
        neck = _box(cx - 0.08, cx + 0.08, y0 - 0.13, y0, base + 0.05, z0 + (z1 - z0) * 0.42)
    return foot, neck


def _geometry_v12(item: dict[str, Any], where: str, errors: list[str]) -> bool | None:
    """Fill body and space for types whose 1.2 geometry differs; None leaves the object to the 1.1 rules."""
    kind = item["type"]
    x, y, z = item["x"], item["y"], item["z"]
    if kind == "building":
        return _geometry_building_v12(item, where, errors)
    if kind in ("tree", "trees"):
        plan = _tree_plan(item, where, errors)
        if plan is None:
            return False
        item["plan"] = plan
        top = z + max(tree["h"] for tree in plan)
        if kind == "tree":
            body = _box(x, x + item["w"], y, y + item["w"], z, top)
        else:
            body = _box(x, x + item["w"], y, y + item["d"], z, top)
        item["body"], item["space"] = body, body
        return True
    if kind in ("screen", "dashboard") and item["stand"]:
        t, w, h = item["t"], item["w"], item["h"]
        lift = z + STAND_LIFT
        if item["orient"] == "x+":
            panel = _box(x, x + t, y, y + w, lift, lift + h)
        else:
            panel = _box(x, x + w, y, y + t, lift, lift + h)
        foot, neck = _stand_boxes(item, panel)
        item["body"], item["foot"], item["neck"] = panel, foot, neck
        item["space"] = _box(min(foot[0], neck[0], panel[0]), max(foot[1], panel[1]), min(foot[2], neck[2], panel[2]),
                             max(foot[3], panel[3]), z, panel[5])
        return True
    if kind == "tile" and item["model"] != "none":
        body = _box(x, x + item["w"], y, y + item["d"], z, z + item["h"])
        size = min(item["w"], item["d"]) * MODEL_SHARE
        rise = size * (0.9 if item["model"] == "database" else 1.05)
        item["body"], item["space"] = body, _box(*body[:5], body[5] + rise)
        item["model_size"] = size
        return True
    if kind == "database":
        body = _box(x, x + item["w"], y, y + item["w"], z, z + item["h"])
        item["body"], item["space"] = body, body
        if item["h"] < item["drums"] * 0.12:
            errors.append(f"{where}: {item['drums']} drums need h >= {_fmt(item['drums'] * 0.12)}")
            return False
        return True
    if kind == "documents":
        orient = item["orient"]
        need, other = ("d", "h") if orient == "flat" else ("h", "d")
        if item.get(need) is None:
            errors.append(f"{where}: documents with orient {orient!r} require {need!r}")
        if item.get(other) is not None:
            errors.append(f"{where}: documents with orient {orient!r} do not take {other!r}")
        if item.get(need) is None or item.get(other) is not None:
            return False
        n, w = item["sheets"], item["w"]
        if orient == "flat":
            body = _box(x, x + w + (n - 1) * 0.07, y, y + item["d"] + (n - 1) * 0.05, z, z + n * DOC_T * 1.6)
        elif orient == "x+":
            body = _box(x, x + (n - 1) * DOC_GAP + DOC_T, y, y + w + (n - 1) * DOC_SHIFT, z, z + item["h"] + (n - 1) * DOC_SHIFT)
        else:
            body = _box(x, x + w + (n - 1) * DOC_SHIFT, y, y + (n - 1) * DOC_GAP + DOC_T, z, z + item["h"] + (n - 1) * DOC_SHIFT)
        item["body"], item["space"] = body, body
        return True
    return None


DOC_T = 0.025
DOC_GAP = 0.09
DOC_SHIFT = 0.07


def _object_geometry(item: dict[str, Any], where: str, errors: list[str]) -> None:
    """Fill body and occupied boxes for a validated object, or report geometric contradictions."""
    kind = item["type"]
    x, y, z = item["x"], item["y"], item["z"]
    w = item.get("w")
    before = len(errors)
    handled = _geometry_v12(item, where, errors) if item.get("v12") else None
    if handled is False:
        return
    if handled:
        pass
    elif kind == "card":
        orient = item["orient"]
        need, other = ("d", "h") if orient == "flat" else ("h", "d")
        if item.get(need) is None:
            errors.append(f"{where}: a card with orient {orient!r} requires {need!r}")
        if item.get(other) is not None:
            errors.append(f"{where}: a card with orient {orient!r} does not take {other!r}")
        if len(errors) > before:
            return
        t = item["t"]
        if orient == "flat":
            body = _box(x, x + w, y, y + item["d"], z, z + t)
        elif orient == "x+":
            body = _box(x, x + t, y, y + w, z, z + item["h"])
        else:
            body = _box(x, x + w, y, y + t, z, z + item["h"])
        item["body"], item["space"] = body, body
    elif kind in ("screen", "dashboard"):
        t, h = item["t"], item["h"]
        lift = 0.34 if item["stand"] else 0.0
        if item["orient"] == "x+":
            body = _box(x, x + t, y, y + w, z + lift, z + lift + h)
        else:
            body = _box(x, x + w, y, y + t, z + lift, z + lift + h)
        item["body"] = body
        if item["stand"]:
            cx, cy = (body[0] + body[1]) / 2, (body[2] + body[3]) / 2
            if item["orient"] == "x+":
                base = _box(cx - 0.3, cx + 0.3, cy - w * 0.22, cy + w * 0.22, z, z + 0.06)
            else:
                base = _box(cx - w * 0.22, cx + w * 0.22, cy - 0.3, cy + 0.3, z, z + 0.06)
            item["base"] = base
            item["space"] = _box(min(base[0], body[0]), max(base[1], body[1]), min(base[2], body[2]),
                                 max(base[3], body[3]), z, body[5])
        else:
            item["space"] = body
    elif kind == "cylinder":
        body = _box(x, x + w, y, y + w, z, z + item["h"])
        item["body"], item["space"] = body, body
    elif kind == "tree":
        if item["shape"] == "cone" and item["h"] < w:
            errors.append(f"{where}: a cone tree needs h >= w; got h={_fmt(item['h'])}, w={_fmt(w)}")
            return
        if item["shape"] == "round" and item["h"] < w * 1.1:
            errors.append(f"{where}: a round tree needs h >= 1.1 * w so the trunk shows; got h={_fmt(item['h'])}, w={_fmt(w)}")
            return
        if item["shape"] in ("oval", "pine") and item["h"] < w * TREE_MIN_H[item["shape"]] - EPS:
            errors.append(f"{where}: an {item['shape']} tree needs h >= {_fmt(TREE_MIN_H[item['shape']])} * w; "
                          f"got h={_fmt(item['h'])}, w={_fmt(w)}")
            return
        body = _box(x, x + w, y, y + w, z, z + item["h"])
        item["body"], item["space"] = body, body
    elif kind == "trees":
        shape, size = item["shape"], item["size"]
        height = item["h"] if item["h"] is not None else size * TREE_DEFAULT_H[shape]
        if height < size * TREE_MIN_H[shape] - EPS:
            errors.append(f"{where}: {shape} trees need h >= {_fmt(TREE_MIN_H[shape])} * size; "
                          f"got h={_fmt(height)}, size={_fmt(size)}")
            return
        positions = _tree_positions(item, where, errors)
        if positions is None:
            return
        item["tree_h"], item["positions"] = height, positions
        body = _box(x, x + w, y, y + item["d"], z, z + height)
        item["body"], item["space"] = body, body
    elif kind == "core":
        if min(w, item["d"]) < 1.2 - EPS:
            errors.append(f"{where}: a core needs w and d of at least 1.2 to hold its package")
            return
        board_top = z + item["h"]
        top = board_top + CORE_PACKAGE_H
        if item["layers"]:
            top += item["layers"] * item["spacing"] + CORE_PLATE_H
        if item["cap"]:
            top += CORE_CAP_H
        item["body"] = _box(x, x + w, y, y + item["d"], z, board_top)
        item["space"] = _box(x, x + w, y, y + item["d"], z, top)
        if item.get("v12"):
            # The package, plates and cap stand on an inset column; occlusion tests use it instead of the full box.
            dense = item["detail"] if item["parts"] else 0
            margin = (max(0.4, min(w, item["d"]) * 0.2) if dense else max(0.24, min(w, item["d"]) * 0.14)) - 0.1
            item["column"] = _box(x + margin, x + w - margin, y + margin, y + item["d"] - margin, board_top, top)
    elif kind == "rack":
        body = _box(x, x + w, y, y + item["d"], z, z + item["units"] * item["unit_h"])
        item["body"], item["space"] = body, body
    elif kind == "stack":
        count, h, gap = item["count"], item["h"], item["gap"]
        body = _box(x, x + w, y, y + item["d"], z, z + count * h + (count - 1) * gap)
        item["body"], item["space"] = body, body
    elif kind == "building":
        plinth = item.get("plinth") or 0.0
        base = z + (PLINTH_H if plinth > 0 else 0.0)
        body = _box(x, x + w, y, y + item["d"], base, base + item["floors"] * item["floor_h"])
        x0, x1, y0, y1 = x - plinth, x + w + plinth, y - plinth, y + item["d"] + plinth
        if item.get("entrance") == "x+":
            x1 = max(x1, x + w + CANOPY_DEPTH)
        elif item.get("entrance") == "y+":
            y1 = max(y1, y + item["d"] + CANOPY_DEPTH)
        top = body[5] + max(SIGN_H if item.get("sign") else 0.0, ROOF_UNIT_H if item.get("roof_unit") else 0.0)
        item["body"], item["space"] = body, _box(x0, x1, y0, y1, z, top)
    elif kind == "chip":
        body = _box(x, x + w, y, y + item["d"], z, z + item["h"])
        reach = PIN if item["pins"] != 0 else 0.0
        item["body"] = body
        item["space"] = _box(body[0] - reach, body[1] + reach, body[2] - reach, body[3] + reach, body[4], body[5])
    else:
        body = _box(x, x + w, y, y + item["d"], z, z + item["h"])
        item["body"], item["space"] = body, body
    body = item["body"]
    inset = item.get("inset") or 0.0
    if inset and inset * 2 >= min(body[1] - body[0], body[3] - body[2]) - EPS:
        errors.append(f"{where}.inset must be less than half the shorter side ({_fmt(min(body[1] - body[0], body[3] - body[2]) / 2)})")
    radius = item.get("radius")
    if radius is not None:
        if kind == "card":
            span = (body[1] - body[0], body[3] - body[2]) if item["orient"] == "flat" else (w, item["h"])
        elif kind in ("screen", "dashboard"):
            span = (w, item["h"])
        else:
            span = (body[1] - body[0], body[3] - body[2])
        if radius > min(span) / 2 + EPS:
            errors.append(f"{where}.radius must be at most half the shorter side ({_fmt(min(span) / 2)}); got {_fmt(radius)}")


def normalize_scene(raw: dict[str, Any], base: str | Path | None = None) -> dict[str, Any]:
    """Validate a parsed scene and return its normalized form, or raise SceneError with every problem found.

    ``base`` is the directory that relative icon paths resolve against (the current directory when omitted).
    """
    errors: list[str] = []
    features: list[tuple[str, str]] = []
    if not isinstance(raw, dict):
        raise SceneError(["scene: the top level must be a JSON object"])
    scene = _read_fields(raw, SCENE_FIELDS, "scene", errors, features)
    items_raw = raw.get("objects")
    if not isinstance(items_raw, list) or not items_raw:
        errors.append("scene.objects must be a non-empty list")
        raise SceneError(errors)
    if len(items_raw) > MAX_ITEMS:
        raise SceneError(errors + [f"scene.objects holds {len(items_raw)} items; the limit is {MAX_ITEMS}"])
    items: list[dict[str, Any]] = []
    ids: set[str] = set()
    text_total = len(scene.get("title") or "") + len(scene.get("desc") or "")
    for index, raw_item in enumerate(items_raw):
        where = f"objects[{index}]"
        if not isinstance(raw_item, dict):
            errors.append(f"{where} must be an object")
            continue
        kind = raw_item.get("type")
        if not isinstance(kind, str) or kind not in TYPES:
            errors.append(f"{where}.type must be one of {', '.join(TYPES)}; got {kind!r}")
            continue
        if isinstance(raw_item.get("id"), str) and TOKEN.match(raw_item["id"]):
            where = f"objects[{index}] ({raw_item['id']!r})"
        before = len(errors)
        item = _read_fields(raw_item, TYPES[kind], where, errors, features)
        if kind in V11_TYPES:
            features.append(("1.1", f"{where} type {kind!r}"))
        if kind in V12_TYPES:
            features.append(("1.2", f"{where} type {kind!r}"))
        item["type"] = kind
        item["index"] = index
        item["given"] = frozenset(raw_item)
        text_total += len(item.get("label") or "") + len(item.get("sign") or "")
        if item.get("glyph") and item.get("icon"):
            errors.append(f"{where}: give either glyph or icon, not both")
        if kind == "tile" and item.get("model") not in (None, "none") and (item.get("glyph") or item.get("icon")):
            errors.append(f"{where}: give either model or a glyph or icon, not both")
        if kind == "connector" and item.get("id") is None and isinstance(item.get("from"), str) and isinstance(item.get("to"), str):
            item["id"] = f"{item['from']}-to-{item['to']}"
        if item.get("id") is not None:
            if item["id"] in ids:
                hint = "; give each connector between the same objects an explicit id" if kind == "connector" and "id" not in raw_item else ""
                errors.append(f"{where}: duplicate id {item['id']!r}{hint}")
            ids.add(item["id"])
        item["ok"] = len(errors) == before
        if len(errors) == before and kind == "ground-grid":
            lines = (item["w"] / item["step"] + 1) + (item["d"] / item["step"] + 1)
            dots = (item["w"] / item["step"] + 1) * (item["d"] / item["step"] + 1)
            if item["pattern"] == "lines" and lines > MAX_GRID_LINES:
                errors.append(f"{where}: {int(lines)} grid lines exceed the limit of {MAX_GRID_LINES}; raise step")
            if item["pattern"] in ("dots", "mesh") and dots > MAX_GRID_DOTS:
                noun = "dots" if item["pattern"] == "dots" else "mesh cells"
                errors.append(f"{where}: {int(dots)} grid {noun} exceed the limit of {MAX_GRID_DOTS}; raise step")
        item["where"] = where
        items.append(item)
    if text_total > MAX_TEXT_TOTAL:
        errors.append(f"scene: {text_total} characters of text exceed the limit of {MAX_TEXT_TOTAL}")
    needed = max((version for version, _ in features), default="1.0")
    declared = scene.get("schema")
    if declared is not None and needed > declared:
        above = [text for version, text in features if version > declared]
        shown = ", ".join(above[:6]) + (f" and {len(above) - 6} more" if len(above) > 6 else "")
        errors.append(f"scene: schema {declared} does not include {shown}; declare \"schema\": \"{needed}\" "
                      f"or remove them")
    level = max(declared or "1.0", needed)
    v11, v12 = level >= "1.1", level >= "1.2"
    for item in items:
        item["v12"] = v12
        if item["ok"] and item["type"] not in ("connector", "ground-grid"):
            if v12:
                _v12_defaults(item)
            _object_geometry(item, item["where"], errors)
    if errors:
        raise SceneError(errors)

    scene["v11"] = v11
    scene["v12"] = v12
    scene["schema"] = level
    style_defaults = (STYLE_DEFAULTS_V12 if v12 else STYLE_DEFAULTS)[scene["style"]]
    for key in ("stroke", "detail_stroke"):
        if scene[key] is None:
            scene[key] = style_defaults[key]
    if scene["shadows"] is None:
        scene["shadows"] = scene["style"] == "technical"
    for item in items:
        if item["type"] == "connector" and item["gap"] is None:
            item["gap"] = style_defaults["gap"]
    icons = _load_icons(scene["icons"], Path(base) if base is not None else Path("."), errors) if scene["icons"] else {}
    for item in items:
        name = item.get("icon")
        if name is None:
            continue
        if name not in scene["icons"]:
            known = f"; declared icons: {', '.join(sorted(scene['icons']))}" if scene["icons"] else "; declare it in scene.icons"
            errors.append(f"{item['where']}.icon names unknown icon {name!r}{known}")
        elif name in icons:
            item["icon_data"] = icons[name]
    if scene["shadows"] and any(item.get("id") == "shadow-layer" for item in items):
        errors.append("scene: the id 'shadow-layer' is reserved for the shadow layer when shadows are on")
    if errors:
        raise SceneError(errors)

    solids = [item for item in items if item["type"] not in ("connector", "ground-grid")]
    for i, first in enumerate(solids):
        for second in solids[i + 1:]:
            if _intersects(first["space"], second["space"]):
                errors.append(f"{first['where']} and {second['where']} intersect; volumes may touch but not overlap "
                              f"(each object occupies its bounding box, including chip pins and screen stands)")
    by_id = {item["id"]: item for item in solids}
    for item in items:
        if item["type"] != "connector":
            continue
        for end in ("from", "to"):
            target = item[end]
            if target not in by_id:
                hint = " (connectors cannot attach to ground grids or other connectors)" if target in ids else ""
                errors.append(f"{item['where']}.{end} names unknown object {target!r}{hint}")
    if errors:
        raise SceneError(errors)
    scene["items"] = items
    return scene


def _intersects(a: tuple[float, ...], b: tuple[float, ...]) -> bool:
    return all(min(a[i + 1], b[i + 1]) - max(a[i], b[i]) > EPS for i in (0, 2, 4))


# --------------------------------------------------------------------------
# Path model: ("M", p) ("L", p) ("E", center, pu, pv, t0, t1) ("Z",); an "E"
# segment draws center + cos(t) * pu + sin(t) * pv for t from t0 to t1 (radians).

Point = tuple[float, float]


def _arc_point(seg: tuple[Any, ...], t: float) -> Point:
    _, c, pu, pv, _, _ = seg
    return (c[0] + math.cos(t) * pu[0] + math.sin(t) * pv[0], c[1] + math.cos(t) * pu[1] + math.sin(t) * pv[1])


def _arc_bounds_points(seg: tuple[Any, ...]) -> list[Point]:
    _, c, pu, pv, t0, t1 = seg
    lo, hi = min(t0, t1), max(t0, t1)
    points = [_arc_point(seg, t0), _arc_point(seg, t1)]
    for axis in (0, 1):
        base = math.atan2(pv[axis], pu[axis])
        for n in range(-3, 4):
            t = base + n * math.pi
            if lo < t < hi:
                points.append(_arc_point(seg, t))
    return points


def _segs_points(segs: list[tuple[Any, ...]]) -> list[Point]:
    points: list[Point] = []
    for seg in segs:
        if seg[0] in ("M", "L"):
            points.append(seg[1])
        elif seg[0] == "E":
            points.extend(_arc_bounds_points(seg))
    return points


def _fmt(value: float, places: int = 2) -> str:
    # Platform math libraries can differ in the last bit of sin/cos results; a value that
    # lands on a rounding boundary (379.685) then rounds differently on macOS and Linux.
    # Rounding to 6 places first collapses those last-bit differences before the final cut.
    rounded = round(round(value, 6), places)
    if rounded == 0:
        return "0"
    text = f"{rounded:.{places}f}".rstrip("0").rstrip(".")
    return text


def _ellipse(pu: Point, pv: Point) -> tuple[float, float, float, float]:
    """Return rx, ry, rotation (degrees in [0, 180)) and the determinant of the column matrix [pu pv]."""
    a = pu[0] * pu[0] + pv[0] * pv[0]
    b = pu[0] * pu[1] + pv[0] * pv[1]
    d = pu[1] * pu[1] + pv[1] * pv[1]
    if abs(b) < 1e-9:
        b = 0.0
    mean = (a + d) / 2
    spread = math.sqrt(((a - d) / 2) ** 2 + b * b)
    rx = math.sqrt(max(mean + spread, 0.0))
    ry = math.sqrt(max(mean - spread, 0.0))
    if spread < 1e-9:
        rotation = 0.0
    else:
        rotation = math.degrees(0.5 * math.atan2(2 * b, a - d)) % 180.0
        if rotation > 180.0 - 1e-6:
            rotation = 0.0
    det = pu[0] * pv[1] - pu[1] * pv[0]
    return rx, ry, rotation, det


def _snap_key(value: float) -> float:
    return round(value, 3)


def _snap_sets(paths: list[list[tuple[Any, ...]]]) -> tuple[set[float], set[float]]:
    """Screen x of every vertical segment and y of every horizontal one, so those hairlines can sit on pixel centers."""
    xs: set[float] = set()
    ys: set[float] = set()
    for segs in paths:
        start = current = None
        for seg in segs:
            op = seg[0]
            if op == "M":
                start = current = seg[1]
                continue
            if op == "E":
                current = _arc_point(seg, seg[5])
                continue
            target = start if op == "Z" else seg[1]
            if current is not None and target is not None:
                dx, dy = target[0] - current[0], target[1] - current[1]
                if abs(dx) < 1e-6 and abs(dy) > 0.5:
                    xs.add(_snap_key(current[0]))
                    xs.add(_snap_key(target[0]))
                elif abs(dy) < 1e-6 and abs(dx) > 0.5:
                    ys.add(_snap_key(current[1]))
                    ys.add(_snap_key(target[1]))
            current = target
    return xs, ys


def _path_data(segs: list[tuple[Any, ...]], ox: float, oy: float,
               snap: tuple[set[float], set[float]] | None = None) -> str:
    out: list[str] = []
    current: Point | None = None

    def pt(p: Point) -> str:
        x, y = p[0] - ox, p[1] - oy
        if snap is not None:
            if _snap_key(p[0]) in snap[0]:
                x = math.floor(x) + 0.5
            if _snap_key(p[1]) in snap[1]:
                y = math.floor(y) + 0.5
        return f"{_fmt(x)} {_fmt(y)}"

    for seg in segs:
        op = seg[0]
        if op == "M":
            out.append("M" + pt(seg[1]))
            current = seg[1]
        elif op == "L":
            if current is not None and abs(seg[1][0] - current[0]) < 1e-6 and abs(seg[1][1] - current[1]) < 1e-6:
                continue
            out.append("L" + pt(seg[1]))
            current = seg[1]
        elif op == "E":
            _, c, pu, pv, t0, t1 = seg
            rx, ry, rotation, det = _ellipse(pu, pv)
            span = t1 - t0
            pieces = 1 if abs(span) <= math.pi + 1e-9 else 2
            for piece in range(pieces):
                start = t0 + span * piece / pieces
                end = t0 + span * (piece + 1) / pieces
                sweep = 1 if (end > start) == (det > 0) else 0
                target = _arc_point(seg, end)
                out.append(f"A{_fmt(rx)} {_fmt(ry)} {_fmt(rotation)} 0 {sweep} {pt(target)}")
                current = target
        elif op == "Z":
            out.append("Z")
    return " ".join(out)


# --------------------------------------------------------------------------
# Geometry builders


class Prism:
    """A rounded rectangle in the plane of axes (p, q), extruded along axis e.

    Outline points are addressed by the angle a of their outward normal,
    n = cos(a) * P + sin(a) * Q; corner arcs sit in quadrants and straight
    edges at multiples of 90 degrees. The viewer sees the cap at the high end
    of e and the side band whose normals lie within 90 degrees of the view.
    """

    def __init__(self, proj: Projection, e: int, p: int, q: int, box: tuple[float, ...], radius: float) -> None:
        self.proj, self.e, self.p, self.q = proj, e, p, q
        self.p0, self.p1 = box[2 * p], box[2 * p + 1]
        self.q0, self.q1 = box[2 * q], box[2 * q + 1]
        self.e0, self.e1 = box[2 * e], box[2 * e + 1]
        self.r = max(0.0, min(radius, (self.p1 - self.p0) / 2, (self.q1 - self.q0) / 2))
        alpha = math.degrees(math.atan2(proj.view[q], proj.view[p]))
        self.s0, self.s1 = alpha - 90.0, alpha + 90.0

    def _xyz(self, pv: float, qv: float, ev: float) -> tuple[float, float, float]:
        out = [0.0, 0.0, 0.0]
        out[self.p], out[self.q], out[self.e] = pv, qv, ev
        return (out[0], out[1], out[2])

    def _center(self, quadrant: int) -> tuple[float, float]:
        r = self.r
        return ((self.p1 - r, self.q1 - r), (self.p0 + r, self.q1 - r),
                (self.p0 + r, self.q0 + r), (self.p1 - r, self.q0 + r))[quadrant % 4]

    def at(self, angle: float, ev: float, quadrant: int | None = None) -> Point:
        if quadrant is None:
            quadrant = math.floor(angle / 90.0)
        cp, cq = self._center(quadrant)
        rad = math.radians(angle)
        return self.proj(*self._xyz(cp + self.r * math.cos(rad), cq + self.r * math.sin(rad), ev))

    def trace(self, a0: float, a1: float, ev: float, segs: list[tuple[Any, ...]]) -> None:
        """Append the outline from normal angle a0 to a1 (neither a multiple of 90) at extrusion ev."""
        step = 1 if a1 > a0 else -1
        quadrant = math.floor(a0 / 90.0)
        current = a0
        while True:
            bound = 90.0 * (quadrant + 1) if step > 0 else 90.0 * quadrant
            done = a1 <= bound if step > 0 else a1 >= bound
            end = a1 if done else bound
            if self.r > 0 and end != current:
                cp, cq = self._center(quadrant)
                segs.append(("E", self.proj(*self._xyz(cp, cq, ev)), self.proj.vec(*self._xyz(self.r, 0, 0)),
                             self.proj.vec(*self._xyz(0, self.r, 0)), math.radians(current), math.radians(end)))
            if done:
                return
            quadrant += step
            segs.append(("L", self.at(bound, ev, quadrant)))
            current = bound

    def hull(self) -> list[tuple[Any, ...]]:
        segs: list[tuple[Any, ...]] = [("M", self.at(self.s1, self.e1))]
        self.trace(self.s1, self.s0 + 360.0, self.e1, segs)
        segs.append(("L", self.at(self.s0, self.e0)))
        self.trace(self.s0, self.s1, self.e0, segs)
        segs.append(("Z",))
        return segs

    def q_side(self) -> list[tuple[Any, ...]]:
        segs: list[tuple[Any, ...]] = [("M", self.at(45.0, self.e1))]
        self.trace(45.0, self.s1, self.e1, segs)
        segs.append(("L", self.at(self.s1, self.e0)))
        self.trace(self.s1, 45.0, self.e0, segs)
        segs.append(("Z",))
        return segs

    def cap(self, ev: float | None = None) -> list[tuple[Any, ...]]:
        ev = self.e1 if ev is None else ev
        segs: list[tuple[Any, ...]] = [("M", self.at(self.s1, ev))]
        self.trace(self.s1, self.s1 + 360.0, ev, segs)
        segs.append(("Z",))
        return segs

    def outline(self) -> list[tuple[Any, ...]]:
        segs = self.cap()
        segs.append(("M", self.at(self.s1, self.e1)))
        segs.append(("L", self.at(self.s1, self.e0)))
        self.trace(self.s1, self.s0, self.e0, segs)
        segs.append(("L", self.at(self.s0, self.e1)))
        if self.r <= 0:
            segs.append(("M", self.at(45.0, self.e0)))
            segs.append(("L", self.at(45.0, self.e1)))
        return segs

    def band(self, ev: float) -> list[tuple[Any, ...]]:
        segs: list[tuple[Any, ...]] = [("M", self.at(self.s0, ev))]
        self.trace(self.s0, self.s1, ev, segs)
        return segs

    def ops(self, style: str, extra: str = "") -> list[tuple[Any, ...]]:
        out: list[tuple[Any, ...]] = [
            ("path", AXIS_TONE[self.p] + extra, self.hull()),
            ("path", AXIS_TONE[self.q] + extra, self.q_side()),
            ("path", AXIS_TONE[self.e] + extra, self.cap()),
        ]
        if style != "solid":
            out.append(("path", "iso-o", self.outline()))
        return out


def _prism_axes(e: int) -> tuple[int, int]:
    return {2: (0, 1), 0: (1, 2), 1: (0, 2)}[e]


def _prism(proj: Projection, box: tuple[float, ...], radius: float, e: int = 2) -> Prism:
    p, q = _prism_axes(e)
    return Prism(proj, e, p, q, box, radius)


class Frame:
    """A flat face addressed in local (u, v) grid units; u reads left to right, v runs down."""

    def __init__(self, proj: Projection, origin: tuple[float, float, float], u: tuple[float, float, float],
                 v: tuple[float, float, float], width: float, height: float) -> None:
        self.proj, self.origin, self.u, self.v = proj, origin, u, v
        self.w, self.h = width, height

    def at(self, a: float, b: float) -> Point:
        o, u, v = self.origin, self.u, self.v
        return self.proj(o[0] + a * u[0] + b * v[0], o[1] + a * u[1] + b * v[1], o[2] + a * u[2] + b * v[2])

    def vec(self, a: float, b: float) -> Point:
        u, v = self.u, self.v
        return self.proj.vec(a * u[0] + b * v[0], a * u[1] + b * v[1], a * u[2] + b * v[2])

    def poly(self, points: list[tuple[float, float]], closed: bool = True) -> list[tuple[Any, ...]]:
        segs: list[tuple[Any, ...]] = [("M", self.at(*points[0]))]
        segs.extend(("L", self.at(*point)) for point in points[1:])
        if closed:
            segs.append(("Z",))
        return segs

    def arc(self, cu: float, cv: float, radius: float, t0: float, t1: float) -> tuple[Any, ...]:
        return ("E", self.at(cu, cv), self.vec(radius, 0), self.vec(0, radius), t0, t1)

    def circle(self, cu: float, cv: float, radius: float) -> list[tuple[Any, ...]]:
        return [("M", self.at(cu + radius, cv)), self.arc(cu, cv, radius, 0.0, 2 * math.pi), ("Z",)]

    def earc(self, cu: float, cv: float, ru: float, rv: float, t0: float, t1: float) -> tuple[Any, ...]:
        return ("E", self.at(cu, cv), self.vec(ru, 0), self.vec(0, rv), t0, t1)

    def ellipse(self, cu: float, cv: float, ru: float, rv: float) -> list[tuple[Any, ...]]:
        return [("M", self.at(cu + ru, cv)), self.earc(cu, cv, ru, rv, 0.0, 2 * math.pi), ("Z",)]

    def rrect(self, u0: float, v0: float, u1: float, v1: float, radius: float) -> list[tuple[Any, ...]]:
        r = max(0.0, min(radius, (u1 - u0) / 2, (v1 - v0) / 2))
        segs: list[tuple[Any, ...]] = [("M", self.at(u0 + r, v0)), ("L", self.at(u1 - r, v0))]
        corners = ((u1 - r, v0 + r, -90), (u1 - r, v1 - r, 0), (u0 + r, v1 - r, 90), (u0 + r, v0 + r, 180))
        follow = ((u1, v1 - r), (u0 + r, v1), (u0, v0 + r), None)
        for (cu, cv, start), nxt in zip(corners, follow):
            if r > 0:
                segs.append(self.arc(cu, cv, r, math.radians(start), math.radians(start + 90)))
            if nxt is not None:
                segs.append(("L", self.at(*nxt)))
        segs.append(("Z",))
        return segs

    def text(self, cls: str, text: str, a: float, b: float, size: float, anchor: str) -> tuple[Any, ...]:
        unit = self.proj.unit
        ux, uy = self.vec(1.0 / unit, 0)
        vx, vy = self.vec(0, 1.0 / unit)
        region = (self.at(0, 0), self.at(self.w, 0), self.at(self.w, self.h), self.at(0, self.h))
        return ("text", cls, text, (ux, uy, vx, vy, *self.at(a, b)), size, anchor, region)


def _face(proj: Projection, box: tuple[float, ...], face: str, axis: str = "x") -> Frame:
    x0, x1, y0, y1, z0, z1 = box
    if face == "top":
        if axis == "x":
            return Frame(proj, (x0, y0, z1), (1, 0, 0), (0, 1, 0), x1 - x0, y1 - y0)
        return Frame(proj, (x0, y1, z1), (0, -1, 0), (1, 0, 0), y1 - y0, x1 - x0)
    if face == "x+":
        return Frame(proj, (x1, y1, z1), (0, -1, 0), (0, 0, -1), y1 - y0, z1 - z0)
    return Frame(proj, (x0, y1, z1), (1, 0, 0), (0, 0, -1), x1 - x0, z1 - z0)


def _text_width(text: str, size: float) -> float:
    """Approximate rendered width in px for a proportional sans at the given size."""
    width = 0.0
    for ch in text:
        if ch in "il.,:;|!'":
            width += 0.28
        elif ch in "mwMW":
            width += 0.86
        elif ch.isupper() or ch.isdigit():
            width += 0.64
        elif ch == " ":
            width += 0.28
        else:
            width += 0.54
    return width * size


def _glyph(frame: Frame, glyph: str, cu: float, cv: float, size: float, cls: str) -> list[tuple[Any, ...]]:
    """Draw one of GLYPHS inside a size x size square centered at (cu, cv) of a face."""
    def p(gx: float, gy: float) -> tuple[float, float]:
        return (cu + (gx - 0.5) * size, cv + (gy - 0.5) * size)

    stroke, fill = cls, cls + "f"
    if glyph == "dot":
        return [("path", fill, frame.circle(cu, cv, size * 0.22))]
    if glyph == "ring":
        return [("path", stroke, frame.circle(cu, cv, size * 0.36))]
    if glyph == "check":
        return [("path", stroke, frame.poly([p(0.2, 0.52), p(0.42, 0.74), p(0.82, 0.3)], closed=False))]
    if glyph == "plus":
        return [("path", stroke, frame.poly([p(0.5, 0.18), p(0.5, 0.82)], False) + frame.poly([p(0.18, 0.5), p(0.82, 0.5)], False))]
    if glyph == "bars":
        segs: list[tuple[Any, ...]] = []
        for gx, top in ((0.24, 0.52), (0.5, 0.22), (0.76, 0.4)):
            segs += frame.poly([p(gx, 0.82), p(gx, top)], False)
        return [("path", stroke, segs)]
    if glyph == "user":
        head = frame.circle(*p(0.5, 0.34), size * 0.17)
        shoulders = [("M", frame.at(*p(0.18, 0.86))), frame.arc(*p(0.5, 0.86), size * 0.32, math.pi, 2 * math.pi), ("Z",)]
        return [("path", stroke, head + shoulders)]
    if glyph == "spark":
        pts = [p(0.5, 0.1), p(0.6, 0.4), p(0.9, 0.5), p(0.6, 0.6), p(0.5, 0.9), p(0.4, 0.6), p(0.1, 0.5), p(0.4, 0.4)]
        return [("path", fill, frame.poly(pts))]
    if glyph == "play":
        return [("path", fill, frame.poly([p(0.3, 0.2), p(0.8, 0.5), p(0.3, 0.8)]))]
    s = size
    if glyph == "database":
        top = frame.ellipse(*p(0.5, 0.24), s * 0.32, s * 0.11)
        sides = frame.poly([p(0.18, 0.24), p(0.18, 0.76)], False) + frame.poly([p(0.82, 0.24), p(0.82, 0.76)], False)
        rims = []
        for gy in (0.5, 0.76):
            rims += [("M", frame.at(*p(0.18, gy))), frame.earc(*p(0.5, gy), s * 0.32, s * 0.11, math.pi, 0.0)]
        return [("path", stroke, top + sides + rims)]
    if glyph == "docs":
        back = frame.poly([p(0.3, 0.16), p(0.3, 0.1), p(0.78, 0.1), p(0.78, 0.7), p(0.72, 0.7)], False)
        page = frame.poly([p(0.2, 0.2), p(0.56, 0.2), p(0.7, 0.34), p(0.7, 0.9), p(0.2, 0.9)])
        fold = frame.poly([p(0.56, 0.2), p(0.56, 0.34), p(0.7, 0.34)], False)
        lines = frame.poly([p(0.3, 0.52), p(0.6, 0.52)], False) + frame.poly([p(0.3, 0.68), p(0.52, 0.68)], False)
        return [("path", stroke, back + page + fold + lines)]
    if glyph == "apps":
        segs = []
        for gx, gy in ((0.16, 0.16), (0.56, 0.16), (0.16, 0.56), (0.56, 0.56)):
            u0, v0 = p(gx, gy)
            segs += frame.rrect(u0, v0, u0 + s * 0.28, v0 + s * 0.28, s * 0.07)
        return [("path", stroke, segs)]
    if glyph == "chat":
        bubble = frame.poly([p(0.14, 0.2), p(0.86, 0.2), p(0.86, 0.68), p(0.42, 0.68), p(0.24, 0.84), p(0.26, 0.68),
                             p(0.14, 0.68)])
        dots = frame.circle(*p(0.34, 0.44), s * 0.045) + frame.circle(*p(0.5, 0.44), s * 0.045) + frame.circle(*p(0.66, 0.44), s * 0.045)
        return [("path", stroke, bubble), ("path", fill, dots)]
    if glyph == "layers":
        segs = frame.poly([p(0.5, 0.14), p(0.88, 0.34), p(0.5, 0.54), p(0.12, 0.34)])
        for gy in (0.52, 0.7):
            segs += frame.poly([p(0.12, gy), p(0.5, gy + 0.2), p(0.88, gy)], False)
        return [("path", stroke, segs)]
    if glyph == "chart":
        axis = frame.poly([p(0.14, 0.14), p(0.14, 0.86), p(0.88, 0.86)], False)
        trend = frame.poly([p(0.26, 0.68), p(0.44, 0.5), p(0.58, 0.6), p(0.84, 0.28)], False)
        return [("path", stroke, axis + trend)]
    raise AssertionError(glyph)


def _icon_op(frame: Frame, icon: dict[str, Any], cu: float, cv: float, size: float, cls: str) -> tuple[Any, ...]:
    """Project an icon's viewBox onto a size x size square of a face, centered at (cu, cv), as one affine matrix."""
    vx, vy, vw, vh = icon["viewbox"]
    scale = size / max(vw, vh)
    u0 = cu - vw * scale / 2 - vx * scale
    v0 = cv - vh * scale / 2 - vy * scale
    a, b = frame.vec(scale, 0)
    c, d = frame.vec(0, scale)
    e, f = frame.at(u0, v0)
    corners = [frame.at(u0 + (vx + i * vw) * scale, v0 + (vy + j * vh) * scale) for i in (0, 1) for j in (0, 1)]
    return ("icon", cls, icon, (a, b, c, d, e, f), corners)


def _mark(frame: Frame, item: dict[str, Any], cu: float, cv: float, size: float, cls: str = "iso-g") -> list[tuple[Any, ...]]:
    """The object's icon when it has one, otherwise its built-in glyph, centered at (cu, cv)."""
    if item.get("icon_data"):
        return [_icon_op(frame, item["icon_data"], cu, cv, size, cls)]
    if item.get("glyph"):
        return _glyph(frame, item["glyph"], cu, cv, size, cls)
    return []


def _face_content(frame: Frame, item: dict[str, Any], warnings: list[str], *, fit: float | None = None) -> list[tuple[Any, ...]]:
    """Center an optional glyph and label on a face, warning when the label cannot fit."""
    label = item.get("label")
    glyph = item.get("glyph") or item.get("icon_data")
    size = item.get("label_size", 11.0)
    unit = frame.proj.unit
    usable = frame.w if fit is None else fit
    ops: list[tuple[Any, ...]] = []
    text_w = _text_width(label, size) / unit if label else 0.0
    g = min(frame.h * 0.56, 0.8, usable * 0.45) if glyph else 0.0
    gap = 0.12 if glyph and label else 0.0
    total = g + gap + text_w
    if label and total > usable * 0.9:
        warnings.append(f"{item['where']}: label {label!r} needs about {_fmt(total)} grid units but the face offers "
                        f"{_fmt(usable * 0.9)}; shorten it, lower label_size or enlarge the object")
    if label and size > frame.h * unit * 0.8:
        warnings.append(f"{item['where']}: label_size {_fmt(size)} px is taller than its face "
                        f"({_fmt(frame.h * unit * 0.8)} px usable)")
    start = (frame.w - total) / 2
    cls = "iso-g"
    if glyph:
        ops += _mark(frame, item, start + g / 2, frame.h / 2, g, cls)
    if label:
        if glyph:
            ops.append(frame.text("iso-txt", label, start + g + gap, frame.h / 2, size, "start"))
        else:
            ops.append(frame.text("iso-txt", label, frame.w / 2, frame.h / 2, size, "middle"))
    return ops


def _label_axis(item: dict[str, Any], box: tuple[float, ...]) -> str:
    if item.get("label_axis"):
        return item["label_axis"]
    return "x" if (box[1] - box[0]) >= (box[3] - box[2]) - EPS else "y"


def _labelled_faces(proj: Projection, item: dict[str, Any], box: tuple[float, ...], warnings: list[str]) -> list[tuple[Any, ...]]:
    if not item.get("label") and not item.get("glyph") and not item.get("icon_data"):
        return []
    face = item.get("label_face") or "top"
    frame = _face(proj, box, face, _label_axis(item, box))
    return _face_content(frame, item, warnings)


# --------------------------------------------------------------------------
# Primitive renderers return paint-ordered ops for one object group.


def _render_box(proj: Projection, item: dict[str, Any], style: str, warnings: list[str]) -> list[tuple[Any, ...]]:
    box = item["body"]
    prism = _prism(proj, box, item["radius"])
    ops = prism.ops(style)
    bands = item.get("bands", 0)
    for i in range(1, bands + 1):
        ops.append(("path", "iso-d", prism.band(box[4] + (box[5] - box[4]) * i / (bands + 1))))
    inset = item.get("inset", 0.0)
    if inset > 0:
        frame = _face(proj, box, "top", "x")
        radius = max(0.0, item["radius"] - inset * 0.5)
        ops.append(("path", "iso-d", frame.rrect(inset, inset, frame.w - inset, frame.h - inset, radius)))
    if item.get("v12") and item["type"] == "slab" and item.get("detail"):
        edge = max(item["radius"], inset, 0.12) + 0.04
        blocked = []
        if item.get("label") and (item.get("label_face") or "top") == "top":
            frame = _face(proj, box, "top", _label_axis(item, box))
            band = item["label_size"] / proj.unit + 0.24
            blocked.append(_frame_box(frame, 0.0, frame.h / 2 - band / 2, frame.w, frame.h / 2 + band / 2, box[5], box[5])[:4])
        detail, _ = _populate(proj, (box[0] + edge, box[1] - edge, box[2] + edge, box[3] - edge), box[5], None, blocked,
                              item["detail"], item["seed"], style)
        ops += detail
    return ops + _labelled_faces(proj, item, box, warnings)


def _render_stack(proj: Projection, item: dict[str, Any], style: str, warnings: list[str]) -> list[tuple[Any, ...]]:
    x0, x1, y0, y1, z0, _ = item["body"]
    ops: list[tuple[Any, ...]] = []
    top_box = None
    for i in range(item["count"]):
        zb = z0 + i * (item["h"] + item["gap"])
        box = _box(x0, x1, y0, y1, zb, zb + item["h"])
        ops += _prism(proj, box, item["radius"]).ops(style)
        if item["leds"]:
            frame = _face(proj, box, item["front"])
            mid = frame.h / 2
            inset = max(item["radius"], 0.12) + 0.14
            ops.append(("path", "iso-af", frame.circle(frame.w - inset, mid, min(0.055, frame.h * 0.22))))
            ops.append(("path", "iso-d", frame.poly([(inset - 0.04, mid), (inset + min(0.9, frame.w * 0.35), mid)], False)))
        top_box = box
    assert top_box is not None
    return ops + _labelled_faces(proj, item, top_box, warnings)


def _render_chip(proj: Projection, item: dict[str, Any], style: str, warnings: list[str]) -> list[tuple[Any, ...]]:
    body = item["body"]
    x0, x1, y0, y1, z0, z1 = body
    r = item["radius"]
    pins = item["pins"]
    if pins is None:
        pins = max(2, min(12, int(round(min(x1 - x0, y1 - y0) * 2.0))))
    zp = z0 + (z1 - z0) * 0.3

    def side_pins(side: str) -> list[tuple[Any, ...]]:
        segs: list[tuple[Any, ...]] = []
        along = (y0, y1) if side in ("x+", "x-") else (x0, x1)
        margin = r + (along[1] - along[0]) * 0.12
        span = (along[1] - along[0]) - 2 * margin
        for i in range(pins):
            t = along[0] + margin + (span * (i + 0.5) / pins if pins else 0)
            if side == "x+":
                a, b = (x1, t, zp), (x1 + PIN, t, zp)
            elif side == "x-":
                a, b = (x0 - PIN, t, zp), (x0, t, zp)
            elif side == "y+":
                a, b = (t, y1, zp), (t, y1 + PIN, zp)
            else:
                a, b = (t, y0 - PIN, zp), (t, y0, zp)
            segs += [("M", proj(*a)), ("L", proj(*b))]
        return segs

    ops: list[tuple[Any, ...]] = []
    if pins:
        ops.append(("path", "iso-pin", side_pins("x-") + side_pins("y-")))
    ops += _prism(proj, body, r).ops(style)
    if pins:
        ops.append(("path", "iso-pin", side_pins("x+") + side_pins("y+")))
    face_box = body
    if item["die"]:
        inset = min(x1 - x0, y1 - y0) * 0.2
        die = _box(x0 + inset, x1 - inset, y0 + inset, y1 - inset, z1, z1 + min(0.08, (z1 - z0) * 0.4))
        ops += _prism(proj, die, max(0.0, r * 0.6)).ops(style, " iso-die")
        face_box = die
    return ops + _labelled_faces(proj, item, face_box, warnings)


def _render_cylinder(proj: Projection, item: dict[str, Any], style: str, warnings: list[str]) -> list[tuple[Any, ...]]:
    box = item["body"]
    prism = _prism(proj, box, (box[1] - box[0]) / 2)
    ops = prism.ops(style)
    bands = item["bands"]
    for i in range(1, bands + 1):
        ops.append(("path", "iso-o" if style == "line" else "iso-d", prism.band(box[4] + (box[5] - box[4]) * i / (bands + 1))))
    if item.get("label") or item.get("glyph") or item.get("icon_data"):
        frame = _face(proj, box, "top", "x")
        ops += _face_content(frame, item, warnings, fit=frame.w * 0.72)
    return ops


def _frame_box(frame: Frame, u0: float, v0: float, u1: float, v1: float, z0: float, z1: float) -> tuple[float, ...]:
    """The world box spanning a rectangle of a top-face frame, extruded from z0 to z1."""
    o, u, v = frame.origin, frame.u, frame.v
    xs = [o[0] + a * u[0] + b * v[0] for a in (u0, u1) for b in (v0, v1)]
    ys = [o[1] + a * u[1] + b * v[1] for a in (u0, u1) for b in (v0, v1)]
    return _box(min(xs), max(xs), min(ys), max(ys), z0, z1)


def _door_span(frame: Frame, item: dict[str, Any]) -> tuple[float, float, float, float]:
    """The entrance opening on a facade frame as (u0, v0, u1, v1)."""
    width = min(1.15, frame.w * 0.46)
    height = min(max(item["floor_h"] * 1.3, 0.72), frame.h * 0.62)
    u0 = (frame.w - width) / 2
    return (u0, frame.h - height, u0 + width, frame.h)


def _overlaps(rect: tuple[float, float, float, float], door: tuple[float, float, float, float] | None, pad: float = 0.1) -> bool:
    if door is None:
        return False
    return rect[0] < door[2] + pad and door[0] - pad < rect[2] and rect[1] < door[3] + pad and door[1] - pad < rect[3]


def _facade(frame: Frame, item: dict[str, Any], door: tuple[float, float, float, float] | None) -> list[tuple[Any, ...]]:
    """Window treatment of one facade; v1 kinds keep their exact geometry when there is no door."""
    floors, floor_h, kind = item["floors"], item["floor_h"], item["windows"]
    margin = min(0.18, frame.w * 0.12)
    if kind in ("grid", "ribbon"):
        segs: list[tuple[Any, ...]] = []
        for row in range(floors):
            top = row * floor_h + floor_h * 0.28
            bottom = (row + 1) * floor_h - floor_h * 0.2
            if kind == "ribbon":
                if not _overlaps((margin, top, frame.w - margin, bottom), door):
                    segs += frame.poly([(margin, top), (frame.w - margin, top), (frame.w - margin, bottom), (margin, bottom)])
                continue
            cols = max(1, int((frame.w - 2 * margin) / 0.42))
            cell = (frame.w - 2 * margin) / cols
            for col in range(cols):
                left = margin + col * cell + cell * 0.2
                right = margin + (col + 1) * cell - cell * 0.2
                if not _overlaps((left, top, right, bottom), door):
                    segs += frame.poly([(left, top), (right, top), (right, bottom), (left, bottom)])
        return [("path", "iso-win", segs)]
    glass: list[tuple[Any, ...]] = []
    lines: list[tuple[Any, ...]] = []
    cols = max(2, int(round((frame.w - 2 * margin) / 0.34)))
    cell = (frame.w - 2 * margin) / cols
    if kind == "curtain":
        top, bottom = margin, frame.h - margin * 0.6
        lower = door[1] - 0.12 if door else bottom
        glass += frame.poly([(margin, top), (frame.w - margin, top), (frame.w - margin, lower), (margin, lower)])
        for col in range(1, cols):
            u = margin + col * cell
            lines += frame.poly([(u, top), (u, lower)], False)
        for row in range(1, floors):
            v = row * floor_h
            if top < v < lower - 0.05:
                lines += frame.poly([(margin, v), (frame.w - margin, v)], False)
        if door:
            for left, right in ((margin, door[0] - 0.12), (door[2] + 0.12, frame.w - margin)):
                if right - left > 0.2:
                    glass += frame.poly([(left, lower + 0.12), (right, lower + 0.12), (right, bottom), (left, bottom)])
        return [("path", "iso-glass", glass), ("path", "iso-mull", lines)]
    for row in range(floors):
        top = row * floor_h + floor_h * 0.22
        bottom = (row + 1) * floor_h - floor_h * 0.16
        spans = [(margin, frame.w - margin)]
        if door and _overlaps((margin, top, frame.w - margin, bottom), door, 0.0):
            spans = [(margin, door[0] - 0.14), (door[2] + 0.14, frame.w - margin)]
        for left, right in spans:
            if right - left < 0.2:
                continue
            glass += frame.poly([(left, top), (right, top), (right, bottom), (left, bottom)])
            for col in range(1, cols):
                u = margin + col * cell
                if left + 0.05 < u < right - 0.05:
                    lines += frame.poly([(u, top), (u, bottom)], False)
    return [("path", "iso-glass", glass), ("path", "iso-mull", lines)]


def _entrance(proj: Projection, box: tuple[float, ...], face: str, frame: Frame, door: tuple[float, float, float, float],
              style: str) -> list[tuple[Any, ...]]:
    """A recessed glazed doorway with mullions, a shadowed jamb and a canopy slab above it."""
    u0, v0, u1, v1 = door
    ops: list[tuple[Any, ...]] = [("path", "iso-glass", frame.poly([(u0, v0), (u1, v0), (u1, v1), (u0, v1)]))]
    jamb = 0.07
    ops.append(("path", "iso-r", frame.poly([(u0, v0), (u1, v0), (u1, v0 + jamb), (u0 + jamb, v0 + jamb), (u0 + jamb, v1), (u0, v1)])))
    panes = max(2, int(round((u1 - u0) / 0.28)))
    segs: list[tuple[Any, ...]] = []
    for i in range(1, panes):
        u = u0 + jamb + (u1 - u0 - jamb) * i / panes
        segs += frame.poly([(u, v0 + jamb), (u, v1)], False)
    transom = v0 + jamb + (v1 - v0) * 0.28
    segs += frame.poly([(u0 + jamb, transom), (u1, transom)], False)
    ops.append(("path", "iso-mull", segs))
    ops.append(("path", "iso-o" if style != "solid" else "iso-d", frame.poly([(u0, v0), (u1, v0), (u1, v1), (u0, v1)])))
    x0, x1, y0, y1, _, z1 = box
    ztop = z1 - v0 + 0.16
    if face == "y+":
        canopy = _box(x0 + u0 - 0.16, x0 + u1 + 0.16, y1, y1 + CANOPY_DEPTH, ztop - 0.07, ztop)
    else:
        canopy = _box(x1, x1 + CANOPY_DEPTH, y1 - u1 - 0.16, y1 - u0 + 0.16, ztop - 0.07, ztop)
    ops += _prism(proj, canopy, 0.0).ops(style)
    return ops


def _render_building(proj: Projection, item: dict[str, Any], style: str, warnings: list[str]) -> list[tuple[Any, ...]]:
    if item.get("v12"):
        return _render_building_v12(proj, item, style, warnings)
    box = item["body"]
    ops: list[tuple[Any, ...]] = []
    plinth = item.get("plinth") or 0.0
    if plinth > 0:
        base = _box(box[0] - plinth, box[1] + plinth, box[2] - plinth, box[3] + plinth, item["z"], box[4])
        ops += _prism(proj, base, min(0.1, plinth / 2)).ops(style)
        paving = _face(proj, base, "top", "x")
        joints: list[tuple[Any, ...]] = []
        for i in range(1, int((base[1] - base[0]) / 0.5)):
            u = i * 0.5
            if u < plinth - 0.05 or u > base[1] - base[0] - plinth + 0.05:
                joints += paving.poly([(u, 0.06), (u, paving.h - 0.06)], False)
        if joints:
            ops.append(("path", "iso-d iso-faint", joints))
    ops += _prism(proj, box, 0.0).ops(style)
    entrance = item.get("entrance")
    for face in ("y+", "x+"):
        frame = _face(proj, box, face)
        door = _door_span(frame, item) if entrance == face else None
        if item["windows"] != "none":
            ops += _facade(frame, item, door)
        if door:
            ops += _entrance(proj, box, face, frame, door, style)
    x0, x1, y0, y1, _, z1 = box
    if item["roof"]:
        inset = min(0.14, (box[1] - box[0]) * 0.1, (box[3] - box[2]) * 0.1)
        frame = _face(proj, box, "top", "x")
        ops.append(("path", "iso-d", frame.poly([(inset, inset), (frame.w - inset, inset),
                                                  (frame.w - inset, frame.h - inset), (inset, frame.h - inset)])))
    if item.get("roof_unit"):
        w, d = x1 - x0, y1 - y0
        unit = _box(x0 + w * 0.14, x0 + w * 0.14 + w * 0.42, y0 + d * 0.14, y0 + d * 0.14 + d * 0.42, z1, z1 + ROOF_UNIT_H)
        ops += _prism(proj, unit, 0.04).ops(style)
        lid = _face(proj, unit, "top", "x")
        ops.append(("path", "iso-d", lid.rrect(0.1, 0.1, lid.w - 0.1, lid.h - 0.1, 0.04)))
        louver = _face(proj, unit, "x+")
        vents: list[tuple[Any, ...]] = []
        for i in range(1, 4):
            v = louver.h * i / 4
            vents += louver.poly([(0.1, v), (louver.w - 0.1, v)], False)
        ops.append(("path", "iso-d", vents))
    label_item = item
    sign = item.get("sign")
    if sign:
        face = item.get("sign_face") or entrance or "y+"
        size = min(item["label_size"], 11.0)
        mark = 0.34 if (item.get("glyph") or item.get("icon_data")) else 0.0
        length = (_text_width(sign, size) / proj.unit + mark + (0.12 if mark else 0.0)) / 0.88 + 0.12
        span = (x1 - x0) if face == "y+" else (y1 - y0)
        length = min(length, span - 0.2)
        mid = ((x0 + x1) / 2) if face == "y+" else ((y0 + y1) / 2)
        if face == "y+":
            board = _box(mid - length / 2, mid + length / 2, y1 - 0.18, y1 - 0.12, z1 + 0.1, z1 + SIGN_H)
        else:
            board = _box(x1 - 0.18, x1 - 0.12, mid - length / 2, mid + length / 2, z1 + 0.1, z1 + SIGN_H)
        legs = _face(proj, _box(board[0], board[1], board[2], board[3], z1, board[4]), face)
        ops.append(("path", "iso-d", legs.poly([(0.16, 0), (0.16, legs.h)], False) +
                    legs.poly([(legs.w - 0.16, 0), (legs.w - 0.16, legs.h)], False)))
        ops += _prism(proj, board, 0.04, 1 if face == "y+" else 0).ops(style)
        sign_item = {"label": sign, "label_size": size, "glyph": item.get("glyph"), "icon_data": item.get("icon_data"),
                     "where": f"{item['where']}.sign"}
        ops += _face_content(_face(proj, board, face), sign_item, warnings)
        label_item = {**item, "glyph": None, "icon_data": None}
    return ops + _labelled_faces(proj, label_item, box, warnings)


def _plate_axis(orient: str) -> int:
    return {"flat": 2, "x+": 0, "y+": 1}[orient]


def _plate_face(orient: str) -> str:
    return {"flat": "top", "x+": "x+", "y+": "y+"}[orient]


def _render_card(proj: Projection, item: dict[str, Any], style: str, warnings: list[str]) -> list[tuple[Any, ...]]:
    box = item["body"]
    orient = item["orient"]
    ops = _prism(proj, box, item["radius"], _plate_axis(orient)).ops(style)
    if item.get("v12") and orient == "flat":
        ops += _tile_depth(proj, box, item["radius"])
    frame = _face(proj, box, _plate_face(orient), "x" if orient != "flat" else _label_axis(item, box))
    lines = item["lines"]
    if not lines:
        return ops + _face_content(frame, item, warnings)
    margin = min(0.24, frame.h * 0.16, frame.w * 0.12)
    row_h = (frame.h - 2 * margin) / (lines + 2.0)
    header = _subframe(frame, margin, margin, frame.w - margin, margin + row_h * 2.0)
    ops += _face_content(header, item, warnings)
    segs: list[tuple[Any, ...]] = []
    for i in range(lines):
        v = margin + row_h * (2.0 + i + 0.5)
        length = (frame.w - 2 * margin) * (0.86, 0.62, 0.74, 0.5)[i % 4]
        segs += frame.poly([(margin, v), (margin + length, v)], False)
    ops.append(("path", "iso-d", segs))
    return ops


def _subframe(frame: Frame, u0: float, v0: float, u1: float, v1: float) -> Frame:
    o, u, v = frame.origin, frame.u, frame.v
    origin = (o[0] + u0 * u[0] + v0 * v[0], o[1] + u0 * u[1] + v0 * v[1], o[2] + u0 * u[2] + v0 * v[2])
    return Frame(frame.proj, origin, u, v, u1 - u0, v1 - v0)


def _render_screen(proj: Projection, item: dict[str, Any], style: str, warnings: list[str]) -> list[tuple[Any, ...]]:
    if item.get("v12"):
        return _render_screen_v12(proj, item, style, warnings)
    body = item["body"]
    orient = item["orient"]
    ops: list[tuple[Any, ...]] = []
    if item["stand"]:
        base = item["base"]
        ops += _prism(proj, base, min(0.12, (base[1] - base[0]) / 2, (base[3] - base[2]) / 2)).ops(style)
        cx, cy = (body[0] + body[1]) / 2, (body[2] + body[3]) / 2
        neck = _box(cx - 0.05, cx + 0.05, cy - 0.05, cy + 0.05, base[5], body[4])
        ops += _prism(proj, neck, 0.0).ops(style)
    ops += _prism(proj, body, item["radius"], _plate_axis(orient)).ops(style)
    frame = _face(proj, body, _plate_face(orient))
    inset = min(0.14, frame.w * 0.08, frame.h * 0.1)
    display = _subframe(frame, inset, inset, frame.w - inset, frame.h - inset)
    ops.append(("path", "iso-t iso-display", display.rrect(0, 0, display.w, display.h, max(0.0, item["radius"] - inset / 2))))
    if style != "solid":
        ops.append(("path", "iso-d", display.rrect(0, 0, display.w, display.h, max(0.0, item["radius"] - inset / 2))))
    return _screen_content(proj, item, display, ops, warnings)


def _screen_content(proj: Projection, item: dict[str, Any], display: Frame, ops: list[tuple[Any, ...]],
                    warnings: list[str]) -> list[tuple[Any, ...]]:
    """An optional title line and placeholder text lines inside a display frame."""
    pad = min(0.22, display.w * 0.1, display.h * 0.12)
    top = pad
    if item.get("label"):
        head = _subframe(display, pad, pad, display.w - pad, pad + min(0.42, display.h * 0.3))
        text_w = _text_width(item["label"], item["label_size"]) / proj.unit
        if text_w > head.w * 0.95:
            warnings.append(f"{item['where']}: label {item['label']!r} needs about {_fmt(text_w)} grid units but the "
                            f"screen offers {_fmt(head.w * 0.95)}")
        ops.append(head.text("iso-txt", item["label"], 0, head.h / 2, item["label_size"], "start"))
        top = pad + head.h + pad * 0.6
    lines = item["lines"]
    if lines:
        row = (display.h - top - pad) / lines
        segs: list[tuple[Any, ...]] = []
        accent: list[tuple[Any, ...]] = []
        for i in range(lines):
            v = top + row * (i + 0.5)
            length = (display.w - 2 * pad) * (0.42, 0.88, 0.66, 0.78, 0.54, 0.7)[i % 6]
            target = accent if i == 0 and not item.get("label") else segs
            target += display.poly([(pad, v), (pad + length, v)], False)
        if accent:
            ops.append(("path", "iso-a", accent))
        if segs:
            ops.append(("path", "iso-d", segs))
    return ops


def _render_tree(proj: Projection, item: dict[str, Any], style: str, warnings: list[str]) -> list[tuple[Any, ...]]:
    if item.get("v12"):
        return _render_trees_v12(proj, item, style, warnings)
    return _tree_ops(proj, item["body"], item["shape"], style, item.get("planter", False))


def _render_trees(proj: Projection, item: dict[str, Any], style: str, warnings: list[str]) -> list[tuple[Any, ...]]:
    if item.get("v12"):
        return _render_trees_v12(proj, item, style, warnings)
    size, height, z = item["size"], item["tree_h"], item["z"]
    ops: list[tuple[Any, ...]] = []
    for cx, cy in sorted(item["positions"], key=lambda p: (round(p[0] + p[1], 9), p[0])):
        body = _box(cx - size / 2, cx + size / 2, cy - size / 2, cy + size / 2, z, z + height)
        ops += _tree_ops(proj, body, item["shape"], style, item["planter"])
    return ops


def _cone(proj: Projection, cx: float, cy: float, base_z: float, apex_z: float, radius: float,
          style: str) -> list[tuple[Any, ...]]:
    center = proj(cx, cy, base_z)
    rx, ry = proj.k * radius, proj.k * radius * proj.sin
    height = (apex_z - base_z) * proj.k * proj.cos
    apex = (center[0], center[1] - height)
    lean = math.asin(min(1.0, ry / height))
    left_t, right_t = math.pi + lean, -lean
    pu, pv = (rx, 0.0), (0.0, ry)

    def ell(t: float) -> Point:
        return (center[0] + rx * math.cos(t), center[1] + ry * math.sin(t))

    ops = [("path", "iso-l", [("M", apex), ("L", ell(left_t)), ("E", center, pu, pv, left_t, math.pi / 2), ("Z",)]),
           ("path", "iso-r", [("M", apex), ("L", ell(math.pi / 2)), ("E", center, pu, pv, math.pi / 2, right_t), ("Z",)])]
    if style != "solid":
        ops.append(("path", "iso-o", [("M", apex), ("L", ell(left_t)), ("E", center, pu, pv, left_t, right_t), ("Z",)]))
    return ops


def _tree_ops(proj: Projection, body: tuple[float, ...], shape: str, style: str, planter: bool) -> list[tuple[Any, ...]]:
    ops: list[tuple[Any, ...]] = []
    if planter:
        x0, x1, y0, y1, z0, z1 = body
        pot = _box(x0 + (x1 - x0) * 0.18, x1 - (x1 - x0) * 0.18, y0 + (y1 - y0) * 0.18, y1 - (y1 - y0) * 0.18, z0, z0 + 0.1)
        ops += _prism(proj, pot, 0.02).ops(style)
        body = _box(x0, x1, y0, y1, z0 + 0.1, z1)
    if shape in ("round", "cone"):
        return ops + _tree_v1(proj, body, shape, style)
    x0, x1, y0, y1, z0, z1 = body
    w = x1 - x0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    trunk_w = max(0.04, w * 0.06)
    if shape == "pine":
        trunk_top = z0 + (z1 - z0) * 0.24
        ops += _prism(proj, _box(cx - trunk_w, cx + trunk_w, cy - trunk_w, cy + trunk_w, z0, trunk_top + 0.05), 0.0).ops(style)
        span = z1 - trunk_top
        ops += _cone(proj, cx, cy, trunk_top, trunk_top + span * 0.68, w / 2, style)
        ops += _cone(proj, cx, cy, trunk_top + span * 0.4, z1, w * 0.36, style)
        return ops
    rx = proj.k * w / 2
    ry = rx * 1.22
    rise = ry / (proj.k * proj.cos)
    zc = z1 - rise
    ops += _prism(proj, _box(cx - trunk_w, cx + trunk_w, cy - trunk_w, cy + trunk_w, z0, zc), 0.0).ops(style)
    center = proj(cx, cy, zc)
    ccx, ccy = center
    canopy = [("M", (ccx + rx, ccy)), ("E", center, (rx, 0.0), (0.0, ry), 0.0, 2 * math.pi), ("Z",)]
    shade = [("M", (ccx, ccy - ry)), ("E", center, (rx, 0.0), (0.0, ry), -math.pi / 2, math.pi / 2),
             ("E", center, (rx * 0.38, 0.0), (0.0, ry), math.pi / 2, -math.pi / 2), ("Z",)]
    ops += [("path", "iso-t", canopy), ("path", "iso-r iso-soft", shade)]
    fork = (ccx, ccy + ry * 0.18)
    branches = [("M", (ccx, ccy + ry * 0.92)), ("L", (ccx, ccy - ry * 0.42)),
                ("M", fork), ("L", (ccx - rx * 0.42, ccy - ry * 0.3)),
                ("M", (ccx, ccy + ry * 0.42)), ("L", (ccx + rx * 0.4, ccy - ry * 0.06))]
    ops.append(("path", "iso-d", branches))
    if style != "solid":
        ops.append(("path", "iso-o", canopy))
    return ops


def _tree_v1(proj: Projection, body: tuple[float, ...], shape: str, style: str) -> list[tuple[Any, ...]]:
    x0, x1, y0, y1, z0, z1 = body
    w = x1 - x0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    ops: list[tuple[Any, ...]] = []
    trunk_w = max(0.06, w * 0.09)
    if shape == "round":
        radius = w / 2
        center = proj(cx, cy, z1 - radius)
        trunk = _box(cx - trunk_w, cx + trunk_w, cy - trunk_w, cy + trunk_w, z0, z1 - radius)
        ops += _prism(proj, trunk, 0.0).ops(style)
        screen_r = proj.k * radius
        ccx, ccy = center
        circle = [("M", (ccx + screen_r, ccy)), ("E", center, (screen_r, 0.0), (0.0, screen_r), 0.0, 2 * math.pi), ("Z",)]
        shade = [("M", (ccx, ccy - screen_r)), ("E", center, (screen_r, 0.0), (0.0, screen_r), -math.pi / 2, math.pi / 2),
                 ("E", center, (screen_r * 0.42, 0.0), (0.0, screen_r), math.pi / 2, -math.pi / 2), ("Z",)]
        ops += [("path", "iso-t", circle), ("path", "iso-r", shade)]
        if style != "solid":
            ops.append(("path", "iso-o", circle))
        return ops
    base_z = z0 + (z1 - z0) * 0.22
    trunk = _box(cx - trunk_w, cx + trunk_w, cy - trunk_w, cy + trunk_w, z0, base_z + 0.05)
    ops += _prism(proj, trunk, 0.0).ops(style)
    center = proj(cx, cy, base_z)
    rx, ry = proj.k * w / 2, proj.k * w / 2 * proj.sin
    height = (z1 - base_z) * proj.k * proj.cos
    apex = (center[0], center[1] - height)
    lean = math.asin(min(1.0, ry / height))
    left_t, right_t = math.pi + lean, -lean
    pu, pv = (rx, 0.0), (0.0, ry)

    def ell(t: float) -> Point:
        return (center[0] + rx * math.cos(t), center[1] + ry * math.sin(t))

    left = [("M", apex), ("L", ell(left_t)), ("E", center, pu, pv, left_t, math.pi / 2), ("Z",)]
    right = [("M", apex), ("L", ell(math.pi / 2)), ("E", center, pu, pv, math.pi / 2, right_t), ("Z",)]
    ops += [("path", "iso-l", left), ("path", "iso-r", right)]
    if style != "solid":
        ops.append(("path", "iso-o", [("M", apex), ("L", ell(left_t)), ("E", center, pu, pv, left_t, right_t), ("Z",)]))
    return ops


def _render_grid(proj: Projection, item: dict[str, Any], style: str, warnings: list[str]) -> list[tuple[Any, ...]]:
    x0, y0, w, d, step = item["x"], item["y"], item["w"], item["d"], item["step"]
    nx, ny = int(math.floor(w / step + EPS)), int(math.floor(d / step + EPS))
    if item["pattern"] == "lines":
        segs: list[tuple[Any, ...]] = []
        for i in range(ny + 1):
            yy = y0 + i * step
            segs += [("M", proj(x0, yy, 0)), ("L", proj(x0 + nx * step, yy, 0))]
        for i in range(nx + 1):
            xx = x0 + i * step
            segs += [("M", proj(xx, y0, 0)), ("L", proj(xx, y0 + ny * step, 0))]
        return [("path", "iso-grid", segs)]
    levels: dict[int, list[tuple[Any, ...]]] = {}
    cx, cy = x0 + nx * step / 2, y0 + ny * step / 2
    rx, ry = max(nx * step / 2, EPS), max(ny * step / 2, EPS)
    if item["pattern"] == "mesh":
        def level_at(px: float, py: float) -> int:
            if not item["fade"]:
                return 10
            dist = math.sqrt(((px - cx) / rx) ** 2 + ((py - cy) / ry) ** 2)
            return int(round(max(0.0, min(1.0, 1.4 - dist)) * 10))

        def run(points: list[tuple[float, float]]) -> None:
            """Split one grid line into cell edges, merging neighbors that share a fade level."""
            start, current = points[0], None
            for a, b in zip(points, points[1:]):
                level = level_at((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                if level != current:
                    if current:
                        levels.setdefault(current, []).extend([("M", proj(*start, 0)), ("L", proj(*a, 0))])
                    start, current = a, level
            if current:
                levels.setdefault(current, []).extend([("M", proj(*start, 0)), ("L", proj(*points[-1], 0))])

        for j in range(ny + 1):
            run([(x0 + i * step, y0 + j * step) for i in range(nx + 1)])
        for i in range(nx + 1):
            run([(x0 + i * step, y0 + j * step) for j in range(ny + 1)])
        return [("path", f"iso-grid iso-f{level}", levels[level]) for level in sorted(levels)]
    dot = min(0.045, step * 0.06)
    frame = Frame(proj, (0, 0, 0), (1, 0, 0), (0, 1, 0), 0, 0)
    for i in range(nx + 1):
        for j in range(ny + 1):
            xx, yy = x0 + i * step, y0 + j * step
            level = 10
            if item["fade"]:
                dist = math.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
                level = int(round(max(0.0, min(1.0, 1.15 - dist)) * 10))
            if level <= 0:
                continue
            levels.setdefault(level, []).extend(frame.circle(xx, yy, dot))
    return [("path", f"iso-gdot iso-f{level}", levels[level]) for level in sorted(levels)]


def _label_fits(frame: Frame, item: dict[str, Any], width: float, warnings: list[str], what: str = "the face") -> None:
    label, size = item.get("label"), item.get("label_size", 11.0)
    if not label:
        return
    need = _text_width(label, size) / frame.proj.unit
    if need > width + EPS:
        warnings.append(f"{item['where']}: label {label!r} needs about {_fmt(need)} grid units but {what} offers "
                        f"{_fmt(width)}; shorten it, lower label_size or enlarge the object")


def _render_tile(proj: Projection, item: dict[str, Any], style: str, warnings: list[str]) -> list[tuple[Any, ...]]:
    box = item["body"]
    ops = _render_box(proj, {**item, "label": "", "glyph": None, "icon_data": None, "bands": 0}, style, warnings)
    if item.get("v12"):
        ops += _tile_depth(proj, box, item["radius"])
    frame = _face(proj, box, "top", _label_axis(item, box))
    if item["layout"] == "row":
        return ops + _face_content(frame, item, warnings)
    model = item.get("v12") and item.get("model", "none") != "none"
    has_mark = bool(item.get("glyph") or item.get("icon_data"))
    label = item.get("label")
    text_h = item["label_size"] / proj.unit if label else 0.0
    g = item["model_size"] if model else (min(frame.h * 0.42, frame.w * 0.46, 0.95) if has_mark else 0.0)
    gap = (0.2 if model else 0.14) if (has_mark or model) and label else 0.0
    top = (frame.h - (g + gap + text_h * 1.1)) / 2
    if model:
        o, u, v = frame.origin, frame.u, frame.v
        a, b = frame.w / 2, top + g / 2
        ops += _tile_model_ops(proj, item, (o[0] + a * u[0] + b * v[0], o[1] + a * u[1] + b * v[1]), style)
    elif has_mark:
        ops += _mark(frame, item, frame.w / 2, top + g / 2, g)
    if label:
        _label_fits(frame, item, frame.w * 0.9, warnings)
        ops.append(frame.text("iso-txt", label, frame.w / 2, top + g + gap + text_h * 0.55, item["label_size"], "middle"))
    return ops


def _trace_pattern(mirror: bool) -> tuple[list[list[tuple[float, float]]], list[tuple[float, float]]]:
    """Circuit traces in plate-relative units; most of them sit in the front half, which stays visible."""
    traces = [[(0.08, 0.62), (0.3, 0.62), (0.42, 0.74)], [(0.42, 0.74), (0.58, 0.58), (0.92, 0.58)],
              [(0.42, 0.74), (0.42, 0.92)], [(0.58, 0.58), (0.58, 0.36), (0.74, 0.22)],
              [(0.66, 0.92), (0.66, 0.8), (0.92, 0.8)], [(0.2, 0.92), (0.2, 0.8), (0.3, 0.8)]]
    nodes = [(0.42, 0.74), (0.92, 0.58), (0.42, 0.92), (0.74, 0.22), (0.08, 0.62), (0.92, 0.8), (0.3, 0.8)]
    if mirror:
        traces = [[(v, u) for u, v in trace] for trace in traces]
        nodes = [(v, u) for u, v in nodes]
    return traces, nodes


def _render_core(proj: Projection, item: dict[str, Any], style: str, warnings: list[str]) -> list[tuple[Any, ...]]:
    """A layered processor: board with side ports and parts, pinned package with an inset die, exploded
    circuit plates joined by dashed guides, and an inverted cap carrying the glyph or icon."""
    if item.get("v12"):
        return _render_core_v12(proj, item, style, warnings)
    board = item["body"]
    x0, x1, y0, y1, z0, zb = board
    r = item["radius"]
    ops: list[tuple[Any, ...]] = _prism(proj, board, r).ops(style)
    detail: list[tuple[Any, ...]] = []
    slots: list[tuple[Any, ...]] = []
    for face in ("y+", "x+"):
        frame = _face(proj, board, face)
        bh = frame.h
        if frame.w > 1.6 and bh > 0.16:
            for i in range(2):
                u = frame.w - r - 0.3 - i * 0.42
                slots += frame.rrect(u - 0.3, bh * 0.3, u, bh * 0.72, min(0.04, bh * 0.2))
            for i in range(int(min(frame.w * 0.3, 1.4) / 0.08)):
                u = r + 0.24 + i * 0.08
                detail += frame.poly([(u, bh * 0.34), (u, bh * 0.68)], False)
    ops += [("path", "iso-slot", slots), ("path", "iso-d", detail)]
    axis = _label_axis(item, board)
    top = _face(proj, board, "top", axis)
    label = item.get("label")
    strip = max(0.44, item["label_size"] / proj.unit + 0.24) if label and item["label_face"] == "top" else 0.0
    margin = max(0.24, min(x1 - x0, y1 - y0) * 0.14)
    pu0, pv0, pu1, pv1 = margin, margin, top.w - margin, top.h - margin - strip
    if pv1 - pv0 < 0.5:
        warnings.append(f"{item['where']}: the label strip leaves the package only {_fmt(max(0.0, pv1 - pv0))} grid "
                        f"units; enlarge the core or move the label to a side face")
        pv1 = pv0 + max(0.5, pv1 - pv0)
    pkg_top = zb + CORE_PACKAGE_H
    package = _frame_box(top, pu0, pv0, pu1, pv1, zb, pkg_top)
    px0, px1, py0, py1 = package[:4]
    if item["parts"]:
        back_y, back_x = py0 - y0, px0 - x0
        parts = []
        if back_y >= 0.3:
            depth = min(0.24, back_y * 0.55)
            yy = y0 + (back_y - depth) / 2
            parts += [_box(px0 + 0.1, px0 + 0.62, yy, yy + depth, zb, zb + 0.1),
                      _box(px0 + (px1 - px0) * 0.55, px0 + (px1 - px0) * 0.55 + 0.34, yy, yy + depth, zb, zb + 0.14)]
        if back_x >= 0.3:
            depth = min(0.24, back_x * 0.55)
            xx = x0 + (back_x - depth) / 2
            parts += [_box(xx, xx + depth, py0 + (py1 - py0) * 0.2, py0 + (py1 - py0) * 0.2 + 0.5, zb, zb + 0.12)]
        for part in parts:
            ops += _prism(proj, part, 0.03).ops(style)
    front_parts = []
    if item["parts"] and x1 - px1 >= 0.3:
        depth = min(0.22, (x1 - px1) * 0.5)
        xx = px1 + (x1 - px1 - depth) / 2
        front_parts = [_box(xx, xx + depth, py0 + 0.15, py0 + 0.6, zb, zb + 0.1),
                       _box(xx, xx + depth, py0 + 0.8, py0 + 1.05, zb, zb + 0.1)]
    pins_back: list[tuple[Any, ...]] = []
    pins_front: list[tuple[Any, ...]] = []
    if item["pins"]:
        reach = min(0.12, margin * 0.45)
        for x_side, target in ((px0, pins_back), (px1, pins_front)):
            n = int((py1 - py0 - 0.24) / 0.11)
            for i in range(n):
                yy = py0 + 0.12 + (py1 - py0 - 0.24) * (i + 0.5) / n
                xa = x_side - reach if x_side == px0 else x_side
                target += [("M", proj(xa, yy, zb)), ("L", proj(xa + reach, yy, zb))]
        for y_side, target in ((py0, pins_back), (py1, pins_front)):
            n = int((px1 - px0 - 0.24) / 0.11)
            for i in range(n):
                xx = px0 + 0.12 + (px1 - px0 - 0.24) * (i + 0.5) / n
                ya = y_side - reach if y_side == py0 else y_side
                target += [("M", proj(xx, ya, zb)), ("L", proj(xx, ya + reach, zb))]
        ops.append(("path", "iso-d", pins_back))
    ops += _prism(proj, package, 0.06).ops(style)
    if pins_front:
        ops.append(("path", "iso-d", pins_front))
    for part in front_parts:
        if part[3] < py1 - 0.1:
            ops += _prism(proj, part, 0.03).ops(style)
    die = _face(proj, package, "top", "x")
    ops.append(("path", "iso-d", die.rrect(0.14, 0.14, die.w - 0.14, die.h - 0.14, 0.05)))
    ops.append(("path", "iso-glass", die.rrect(0.3, 0.3, die.w - 0.3, die.h - 0.3, 0.04)))
    ops.append(("path", "iso-dotf", die.circle(0.24, 0.24, 0.035)))
    grow = 0.08
    plate_fp = (px0 - grow, px1 + grow, py0 - grow, py1 + grow)
    corner = max(0.0, min(r, 0.2))
    inset = corner * (1 - 1 / SQRT2)
    guide_xy = [(plate_fp[0] + inset, plate_fp[2] + inset), (plate_fp[1] - inset, plate_fp[2] + inset),
                (plate_fp[0] + inset, plate_fp[3] - inset), (plate_fp[1] - inset, plate_fp[3] - inset)]
    level = pkg_top
    surface = package
    for i in range(item["layers"]):
        zp = pkg_top + item["spacing"] * (i + 1)
        ops.append(("path", "iso-guide", [seg for gx, gy in guide_xy for seg in (("M", proj(gx, gy, level)), ("L", proj(gx, gy, zp)))]))
        plate = _box(*plate_fp, zp, zp + CORE_PLATE_H)
        ops += _prism(proj, plate, corner).ops(style)
        face = _face(proj, plate, "top", "x")
        ops.append(("path", "iso-d iso-faint", face.rrect(0.12, 0.12, face.w - 0.12, face.h - 0.12, max(0.0, corner - 0.06))))
        if i < item["layers"] - 1 or not item["cap"]:
            traces, nodes = _trace_pattern(i % 2 == 1)
            segs = []
            for trace in traces:
                segs += face.poly([(0.16 + u * (face.w - 0.32), 0.16 + v * (face.h - 0.32)) for u, v in trace], False)
            rings = []
            for u, v in nodes:
                rings += face.circle(0.16 + u * (face.w - 0.32), 0.16 + v * (face.h - 0.32), 0.055)
            ops += [("path", "iso-d", segs), ("path", "iso-node", rings)]
        level = zp + CORE_PLATE_H
        surface = plate
    mark_frame: Frame | None = None
    if item["cap"]:
        sx0, sx1, sy0, sy1 = surface[:4]
        side = min(sx1 - sx0, sy1 - sy0) * 0.46
        cx, cy = (sx0 + sx1) / 2, (sy0 + sy1) / 2
        cap = _box(cx - side / 2, cx + side / 2, cy - side / 2, cy + side / 2, level, level + CORE_CAP_H)
        ops += _prism(proj, cap, side * 0.22).ops(style, " iso-inv")
        mark_frame = _face(proj, cap, "top", "x")
        ops += _mark(mark_frame, item, mark_frame.w / 2, mark_frame.h / 2, side * 0.6, "iso-gi")
    else:
        mark_frame = _face(proj, surface, "top", "x")
        ops += _mark(mark_frame, item, mark_frame.w / 2, mark_frame.h / 2, min(mark_frame.w, mark_frame.h) * 0.4)
    if label:
        if item["label_face"] == "top":
            band = _subframe(top, margin, top.h - strip, top.w - margin, top.h - 0.06)
            _label_fits(band, item, band.w, warnings, "the label strip")
            ops.append(band.text("iso-txt", label, band.w / 2, band.h / 2, item["label_size"], "middle"))
        else:
            frame = _face(proj, board, item["label_face"])
            ops += _face_content(frame, {**item, "glyph": None, "icon_data": None}, warnings)
    return ops


def _render_rack(proj: Projection, item: dict[str, Any], style: str, warnings: list[str]) -> list[tuple[Any, ...]]:
    if item.get("v12"):
        return _render_rack_v12(proj, item, style, warnings)
    body = item["body"]
    ops = _prism(proj, body, item["radius"]).ops(style)
    units, unit_h = item["units"], item["unit_h"]
    front = _face(proj, body, item["front"])
    side = _face(proj, body, "x+" if item["front"] == "y+" else "y+")
    seams: list[tuple[Any, ...]] = []
    for i in range(1, units):
        for frame in (front, side):
            seams += frame.poly([(0.05, i * unit_h), (frame.w - 0.05, i * unit_h)], False)
    slots: list[tuple[Any, ...]] = []
    vents: list[tuple[Any, ...]] = []
    on: list[tuple[Any, ...]] = []
    off: list[tuple[Any, ...]] = []
    pad = max(0.12, item["radius"] + 0.06)
    count = max(1, int((front.w * 0.58 - pad) / 0.15))
    for i in range(units):
        mid = (i + 0.5) * unit_h
        for j in range(count):
            u = pad + j * 0.15
            slots += front.rrect(u, mid - unit_h * 0.24, u + 0.09, mid + unit_h * 0.24, 0.02)
        if item["leds"]:
            dot = min(0.045, unit_h * 0.14)
            on += front.circle(front.w - pad - 0.04, mid, dot)
            off += front.circle(front.w - pad - 0.18, mid, dot)
        for k in range(3):
            v = mid - unit_h * 0.18 + k * unit_h * 0.18
            vents += side.poly([(side.w - 0.5, v), (side.w - 0.16, v)], False)
    ops += [("path", "iso-d", seams), ("path", "iso-slot", slots), ("path", "iso-d iso-faint", vents)]
    if on:
        ops += [("path", "iso-dotf", off), ("path", "iso-ledon", on)]
    return ops + _labelled_faces(proj, item, body, warnings)


DEFAULT_SERIES = (0.22, 0.36, 0.3, 0.52, 0.46, 0.68, 0.6, 0.84)


def _render_dashboard(proj: Projection, item: dict[str, Any], style: str, warnings: list[str]) -> list[tuple[Any, ...]]:
    if item.get("v12"):
        return _render_dashboard_v12(proj, item, style, warnings)
    body = item["body"]
    orient = item["orient"]
    ops: list[tuple[Any, ...]] = []
    if item["stand"]:
        base = item["base"]
        ops += _prism(proj, base, min(0.12, (base[1] - base[0]) / 2, (base[3] - base[2]) / 2)).ops(style)
        cx, cy = (body[0] + body[1]) / 2, (body[2] + body[3]) / 2
        ops += _prism(proj, _box(cx - 0.05, cx + 0.05, cy - 0.05, cy + 0.05, base[5], body[4]), 0.0).ops(style)
    ops += _prism(proj, body, item["radius"], _plate_axis(orient)).ops(style)
    frame = _face(proj, body, _plate_face(orient))
    inset = min(0.12, frame.w * 0.06, frame.h * 0.08)
    display = _subframe(frame, inset, inset, frame.w - inset, frame.h - inset)
    corner = max(0.0, item["radius"] - inset / 2)
    ops.append(("path", "iso-t iso-display", display.rrect(0, 0, display.w, display.h, corner)))
    if style != "solid":
        ops.append(("path", "iso-d", display.rrect(0, 0, display.w, display.h, corner)))
    return _dashboard_content(proj, item, display, ops, warnings)


def _dashboard_content(proj: Projection, item: dict[str, Any], display: Frame, ops: list[tuple[Any, ...]],
                       warnings: list[str]) -> list[tuple[Any, ...]]:
    """Window header, title with mark, check rows and the chart, laid out inside a display frame."""
    pad = min(0.2, display.w * 0.06, display.h * 0.08)
    v = 0.0
    if item["header"]:
        head = min(0.3, display.h * 0.14)
        dots: list[tuple[Any, ...]] = []
        for i in range(3):
            dots += display.circle(pad + 0.04 + i * 0.13, head / 2, 0.035)
        pills = display.rrect(display.w - pad - 0.62, head * 0.3, display.w - pad - 0.36, head * 0.7, head * 0.2)
        pills += display.rrect(display.w - pad - 0.3, head * 0.3, display.w - pad, head * 0.7, head * 0.2)
        ops += [("path", "iso-dotf", dots), ("path", "iso-d", pills),
                ("path", "iso-d", display.poly([(0, head), (display.w, head)], False))]
        v = head
    v += pad
    label = item.get("label")
    has_mark = bool(item.get("glyph") or item.get("icon_data"))
    if label or has_mark:
        size = item["label_size"]
        line = max(size / proj.unit * 1.25, 0.3)
        u = pad
        if has_mark:
            ops += _mark(display, item, u + line * 0.4, v + line / 2, line * 0.8)
            u += line + 0.06
        if label:
            _label_fits(display, item, display.w - u - pad, warnings, "the dashboard title")
            ops.append(display.text("iso-txt", label, u, v + line / 2, size, "start"))
        v += line + pad * 0.7
    bottom = display.h - pad
    rows, chart = item["rows"], item["chart"]
    series = item["series"] or list(DEFAULT_SERIES)
    if bottom - v < 0.3:
        if rows or chart != "none":
            warnings.append(f"{item['where']}: the dashboard has no room left for rows or a chart; enlarge h or w")
        return ops
    width = display.w - 2 * pad
    left_w = width * (0.4 if chart != "none" else 1.0) if rows else 0.0
    if rows:
        row_h = min(0.36, (bottom - v) / rows)
        lines: list[tuple[Any, ...]] = []
        for i in range(rows):
            mid = v + row_h * (i + 0.5)
            check = min(row_h * 0.62, 0.22)
            ops += _glyph(display, "check", pad + check / 2, mid, check, "iso-g")
            start = pad + check + 0.08
            lines += display.poly([(start, mid - row_h * 0.12), (start + (left_w - check - 0.1) * (0.9, 0.7, 0.8, 0.6, 0.75)[i]
                                    , mid - row_h * 0.12)], False)
            lines += display.poly([(start, mid + row_h * 0.16), (start + (left_w - check - 0.1) * (0.5, 0.62, 0.42, 0.55, 0.36)[i],
                                    mid + row_h * 0.16)], False)
        ops.append(("path", "iso-d", lines))
    if chart == "none":
        return ops
    cu0 = pad + left_w + (0.18 if rows else 0.0)
    cu1 = display.w - pad
    if cu1 - cu0 < 0.4:
        warnings.append(f"{item['where']}: the dashboard chart has under 0.4 grid units of width; enlarge w or lower rows")
        return ops
    split = v + (bottom - v) * (0.58 if chart == "both" else 1.0)
    if chart in ("line", "both"):
        lo, hi = split - 0.04, v + 0.06
        n = len(series)
        points = [(cu0 + (cu1 - cu0) * i / (n - 1), lo + (hi - lo) * value) for i, value in enumerate(series)]
        ops.append(("path", "iso-area", display.poly(points + [(cu1, lo), (cu0, lo)])))
        ops.append(("path", "iso-cl", display.poly(points, False)))
        ops.append(("path", "iso-d iso-faint", display.poly([(cu0, lo), (cu1, lo)], False)))
    if chart in ("bars", "both"):
        top = split + (0.1 if chart == "both" else 0.0)
        count = min(len(series), max(2, int((cu1 - cu0) / 0.16)))
        pitch = (cu1 - cu0) / count
        bars: list[tuple[Any, ...]] = []
        for i in range(count):
            value = series[len(series) - count + i]
            left = cu0 + pitch * i + pitch * 0.22
            bars += display.poly([(left, bottom), (left + pitch * 0.56, bottom),
                                  (left + pitch * 0.56, bottom - (bottom - top) * max(0.08, value)),
                                  (left, bottom - (bottom - top) * max(0.08, value))])
        ops.append(("path", "iso-bar", bars))
    return ops


# --------------------------------------------------------------------------
# Schema 1.2 drawing kit


def _cross(a: tuple[float, ...], b: tuple[float, ...]) -> tuple[float, float, float]:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _axis_of(vector: tuple[float, ...]) -> int:
    return max(range(3), key=lambda i: abs(vector[i]))


def _depth_shift(frame: Frame) -> tuple[float, float]:
    """Where a point one grid unit behind a face appears on that face, in face units (u, v)."""
    normal = _cross(frame.u, frame.v)
    view = frame.proj.view
    facing = _dot(view, normal)
    delta = tuple(view[i] / facing - normal[i] for i in range(3))
    return _dot(delta, frame.u), _dot(delta, frame.v)


def _clip_rect(points: list[tuple[float, float]], u0: float, v0: float, u1: float, v1: float) -> list[tuple[float, float]]:
    """Clip a convex polygon given in face units to an axis-aligned rectangle (Sutherland-Hodgman)."""
    def at_u(value: float) -> Callable[[tuple[float, float], tuple[float, float]], tuple[float, float]]:
        return lambda a, b: (value, a[1] + (b[1] - a[1]) * (value - a[0]) / (b[0] - a[0]))

    def at_v(value: float) -> Callable[[tuple[float, float], tuple[float, float]], tuple[float, float]]:
        return lambda a, b: (a[0] + (b[0] - a[0]) * (value - a[1]) / (b[1] - a[1]), value)

    tests = ((lambda p: p[0] >= u0 - 1e-9, at_u(u0)), (lambda p: p[0] <= u1 + 1e-9, at_u(u1)),
             (lambda p: p[1] >= v0 - 1e-9, at_v(v0)), (lambda p: p[1] <= v1 + 1e-9, at_v(v1)))
    pts = list(points)
    for keep, cross in tests:
        if not pts:
            break
        out: list[tuple[float, float]] = []
        for i, cur in enumerate(pts):
            prev = pts[i - 1]
            if keep(cur):
                if not keep(prev):
                    out.append(cross(prev, cur))
                out.append(cur)
            elif keep(prev):
                out.append(cross(prev, cur))
        pts = out
    return pts


class _Batch:
    """Collect segments by class so many small parts draw as one path per class, in a fixed paint order."""

    def __init__(self) -> None:
        self.parts: dict[str, list[tuple[Any, ...]]] = {}

    def add(self, cls: str, segs: list[tuple[Any, ...]]) -> None:
        if segs:
            self.parts.setdefault(cls, []).extend(segs)

    def ops(self, order: tuple[str, ...]) -> list[tuple[Any, ...]]:
        unknown = [cls for cls in self.parts if cls not in order]
        if unknown:
            raise AssertionError(unknown)
        return [("path", cls, self.parts[cls]) for cls in order if self.parts.get(cls)]


RECESS_ORDER = ("iso-hole", "iso-glass", "iso-deck", "iso-l", "iso-r", "iso-t", "iso-mull", "iso-d iso-faint",
                "iso-d", "iso-o")


def _recess(batch: _Batch, frame: Frame, u0: float, v0: float, u1: float, v1: float, depth: float,
            back: str = "iso-glass", edge: str | None = "iso-d", inner: str | None = "iso-d iso-faint") -> tuple[float, ...]:
    """Cut an opening (u0..u1, v0..v1) ``depth`` grid units into a face: the visible back plane, the walls that
    face the viewer (each in the tone of its own normal), the recess line and the opening's frame line.
    Returns the visible back rectangle in face units."""
    su, sv = _depth_shift(frame)
    su, sv = su * depth, sv * depth
    rect = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
    seen = _clip_rect([(u + su, v + sv) for u, v in rect], u0, v0, u1, v1)
    if len(seen) >= 3:
        batch.add(back, frame.poly(seen))
    view = frame.proj.view
    walls = []
    facing_u, facing_v = _dot(frame.u, view), _dot(frame.v, view)
    if facing_u > EPS:
        walls.append(((u0, v0), (u0, v1), frame.u))
    elif facing_u < -EPS:
        walls.append(((u1, v0), (u1, v1), frame.u))
    if facing_v > EPS:
        walls.append(((u0, v0), (u1, v0), frame.v))
    elif facing_v < -EPS:
        walls.append(((u0, v1), (u1, v1), frame.v))
    for a, b, normal in walls:
        quad = _clip_rect([a, b, (b[0] + su, b[1] + sv), (a[0] + su, a[1] + sv)], u0, v0, u1, v1)
        if len(quad) >= 3:
            batch.add(AXIS_TONE[_axis_of(normal)], frame.poly(quad))
    if inner and len(seen) >= 3:
        batch.add(inner, frame.poly(seen))
    if edge:
        batch.add(edge, frame.poly(rect))
    us = [p[0] for p in seen] or [u0]
    vs = [p[1] for p in seen] or [v0]
    return (min(us), min(vs), max(us), max(vs))


def _rrect_ground(proj: Projection, z: float, x0: float, x1: float, y0: float, y1: float, r: float) -> list[tuple[Any, ...]]:
    return Frame(proj, (0.0, 0.0, z), (1, 0, 0), (0, 1, 0), 0, 0).rrect(x0, y0, x1, y1, r)


# Trees ---------------------------------------------------------------------

# Canopy volumes in units of the canopy radius: (dx, dy, rx, ry); screen y grows downward. The first volume is the
# crown behind; later ones overlap it toward the viewer, so their partial contours read as separate masses.
LOBES = {
    "broadleaf": ((0.0, -0.22, 0.72, 0.74), (-0.36, 0.22, 0.5, 0.5), (0.34, 0.3, 0.52, 0.5)),
    "columnar": ((0.0, -0.14, 0.6, 1.0), (-0.2, 0.36, 0.42, 0.62), (0.22, 0.54, 0.42, 0.56)),
}
TRUNK_SHARE = {"broadleaf": 0.3, "columnar": 0.18, "conifer": 0.2}


def _ellipse_segs(center: Point, rx: float, ry: float) -> list[tuple[Any, ...]]:
    cx, cy = center
    return [("M", (cx + rx, cy)), ("E", center, (rx, 0.0), (0.0, ry), 0.0, 2 * math.pi), ("Z",)]


def _crescent(center: Point, rx: float, ry: float, angle: float, depth: float) -> list[tuple[Any, ...]]:
    """The part of an ellipse between its rim and a flatter ellipse through the same two points; it bulges toward
    ``angle`` + 90 degrees. Conjugate half-diameters keep both arcs on the original ellipse's rim."""
    a = math.radians(angle)
    pu = (rx * math.cos(a), ry * math.sin(a))
    pv = (-rx * math.sin(a), ry * math.cos(a))
    start = (center[0] + pu[0], center[1] + pu[1])
    return [("M", start), ("E", center, pu, pv, 0.0, math.pi),
            ("E", center, pu, (pv[0] * depth, pv[1] * depth), math.pi, 0.0), ("Z",)]


def _canopy_ops(volumes: list[tuple[Point, float, float]], style: str) -> list[tuple[Any, ...]]:
    """Overlapping canopy volumes under one silhouette: a doubled stroke behind every fill leaves only the outer
    contour, each volume has a light crown and a shaded underside, and the front volumes add the partial contour
    where they overlap the crown behind them."""
    ops: list[tuple[Any, ...]] = []
    if style != "solid":
        ops.append(("path", "iso-silh", [seg for c, rx, ry in volumes for seg in _ellipse_segs(c, rx, ry)]))
    for center, rx, ry in volumes:
        ops += [("path", "iso-l iso-leaf", _ellipse_segs(center, rx, ry)),
                ("path", "iso-t iso-leaf", _crescent(center, rx, ry, 150.0, 0.45)),
                ("path", "iso-shade", _crescent(center, rx, ry, -30.0, 0.5))]
    # One partial contour over the upper side of the frontmost volume, where it overlaps the crown behind it.
    contours: list[tuple[Any, ...]] = []
    if len(volumes) > 1:
        center, rx, ry = max(volumes[1:], key=lambda v: v[0][1] + v[2])
        t0, t1 = math.radians(196), math.radians(292)
        contours += [("M", (center[0] + rx * math.cos(t0), center[1] + ry * math.sin(t0))),
                     ("E", center, (rx, 0.0), (0.0, ry), t0, t1)]
    if contours and style != "solid":
        ops.append(("path", "iso-leafline", contours))
    return ops


def _tree_v12(proj: Projection, tree: dict[str, Any], z0: float, style: str, planter: bool) -> list[tuple[Any, ...]]:
    """A tree with a round ground patch (or an opt-in planter), a short visible trunk and a canopy built from
    overlapping volumes, or tiers for a conifer."""
    cx, cy, w, h, species = tree["cx"], tree["cy"], tree["w"], tree["h"], tree["species"]
    rng = _Rand(tree["seed"], 11)
    ops: list[tuple[Any, ...]] = []
    ground = Frame(proj, (0.0, 0.0, z0), (1, 0, 0), (0, 1, 0), 0, 0)
    if planter:
        half = w * 0.32
        pot = _box(cx - half, cx + half, cy - half, cy + half, z0, z0 + 0.1)
        ops += _prism(proj, pot, 0.02).ops(style)
        ops.append(("path", "iso-hole", _face(proj, pot, "top").rrect(0.04, 0.04, half * 2 - 0.04, half * 2 - 0.04, 0.02)))
        z0 += 0.1
    else:
        patch = ground.circle(cx, cy, w * 0.34)
        ops += [("path", "iso-patch", patch), ("path", "iso-d iso-faint", patch)]
    base = proj(cx, cy, z0)
    top_y = proj(cx, cy, z0 + h)[1]
    span = base[1] - top_y
    k = proj.k
    radius = k * w / 2
    mirror = -1.0 if tree["mirror"] else 1.0
    if species == "conifer":
        trunk_top = base[1] - span * TRUNK_SHARE["conifer"]
        ops.append(("path", "iso-trunk", [("M", base), ("L", (base[0], trunk_top - span * 0.06))]))
        tiers = ((1.0, 0.0, 0.48), (0.78, 0.3, 0.74), (0.54, 0.56, 1.0))
        bottom = trunk_top
        height = span * (1 - TRUNK_SHARE["conifer"])
        for share, start, end in tiers:
            r = radius * share * rng.uniform(0.95, 1.05)
            b_y = bottom - height * start
            apex = (base[0] + mirror * r * 0.03, bottom - height * end)
            ry = r * proj.sin
            center = (base[0], b_y)
            lean = math.asin(min(1.0, ry / max(b_y - apex[1], 1e-6)))
            left_t, right_t = math.pi + lean, -lean

            def ell(t: float, c: Point = center, rr: float = r, yy: float = ry) -> Point:
                return (c[0] + rr * math.cos(t), c[1] + yy * math.sin(t))

            pu, pv = (r, 0.0), (0.0, ry)
            ops += [("path", "iso-l iso-leaf", [("M", apex), ("L", ell(left_t)), ("E", center, pu, pv, left_t, math.pi / 2), ("Z",)]),
                    ("path", "iso-r iso-leaf", [("M", apex), ("L", ell(math.pi / 2)), ("E", center, pu, pv, math.pi / 2, right_t), ("Z",)])]
            if style != "solid":
                ops.append(("path", "iso-o", [("M", apex), ("L", ell(left_t)), ("E", center, pu, pv, left_t, right_t), ("Z",)]))
        return ops
    trunk_share = TRUNK_SHARE[species]
    canopy_h = span * (1 - trunk_share)
    lobes = LOBES[species]
    width = radius * (0.88 if species == "broadleaf" else 0.7)
    top = min(dy - ry for _, dy, _, ry in lobes)
    bottom = max(dy + ry for _, dy, _, ry in lobes)
    left = min(dx - rx for dx, _, rx, _ in lobes)
    right = max(dx + rx for dx, _, rx, _ in lobes)
    scale_y = canopy_h / (bottom - top)
    scale_x = 2 * width / (right - left)
    trunk_top = top_y + canopy_h
    volumes = []
    for dx, dy, rx, ry in lobes:
        jx, jy, jr = rng.uniform(-0.05, 0.05), rng.uniform(-0.04, 0.04), rng.uniform(0.95, 1.03)
        px = base[0] + mirror * (dx - (left + right) / 2 + jx) * scale_x
        py = top_y + (dy - top + jy) * scale_y
        volumes.append(((px, py), rx * scale_x * jr, ry * scale_y * jr))
    ops.append(("path", "iso-trunk", [("M", base), ("L", (base[0], trunk_top - canopy_h * 0.1))]))
    return ops + _canopy_ops(volumes, style)


def _paint_order(boxes: list[tuple[float, ...]], view: tuple[float, float, float]) -> list[int]:
    """Back-to-front order of a few boxes inside one object; ties and cycles fall back to the depth key."""
    count = len(boxes)
    after: list[set[int]] = [set() for _ in range(count)]
    for i in range(count):
        for j in range(i + 1, count):
            relation = _relation(boxes[i], boxes[j], view)
            if relation < 0:
                after[i].add(j)
            elif relation > 0:
                after[j].add(i)
    indegree = [0] * count
    for i in range(count):
        for j in after[i]:
            indegree[j] += 1

    def key(i: int) -> tuple[float, int]:
        b = boxes[i]
        return (round(b[0] + b[1] + b[2] + b[3] + b[4] + b[5], 6), i)

    heap = [(key(i), i) for i in range(count) if indegree[i] == 0]
    heapq.heapify(heap)
    order: list[int] = []
    while heap:
        _, i = heapq.heappop(heap)
        order.append(i)
        for j in sorted(after[i]):
            indegree[j] -= 1
            if indegree[j] == 0:
                heapq.heappush(heap, (key(j), j))
    if len(order) != count:
        order = sorted(range(count), key=key)
    return order


# Buildings -----------------------------------------------------------------

FACADE_ORDER = ("iso-hole", "iso-glass", "iso-dim", "iso-deck", "iso-l", "iso-r", "iso-t", "iso-mull", "iso-d iso-faint",
                "iso-d", "iso-o")


def _fins(batch: _Batch, frame: Frame, us: list[float], v0: float, v1: float, reach: float) -> None:
    """Thin vertical fins standing ``reach`` out of a face: the side the viewer sees and the fin's front edge."""
    su, sv = _depth_shift(frame)
    du, dv = -su * reach, -sv * reach
    tone = AXIS_TONE[_axis_of(frame.u)]
    for u in us:
        batch.add(tone, frame.poly([(u, v0), (u, v1), (u + du, v1 + dv), (u + du, v0 + dv)]))
        batch.add("iso-d", frame.poly([(u + du, v0 + dv), (u + du, v1 + dv)], False))
        batch.add("iso-d iso-faint", frame.poly([(u, v0), (u, v1)], False))


def _mullions(batch: _Batch, frame: Frame, rect: tuple[float, float, float, float], shift: tuple[float, float],
              opening: tuple[float, float, float, float], pitch: float, transom: float | None = None) -> None:
    """Glazing bars on the back plane of a recessed opening, clipped to the part the viewer can see."""
    u0, v0, u1, v1 = opening
    su, sv = shift
    count = max(1, int(round((u1 - u0) / pitch)))
    seen_u0, seen_v0, seen_u1, seen_v1 = rect
    for i in range(1, count):
        u = u0 + (u1 - u0) * i / count + su
        if seen_u0 + 0.02 < u < seen_u1 - 0.02:
            batch.add("iso-mull", frame.poly([(u, max(v0 + sv, seen_v0)), (u, min(v1 + sv, seen_v1))], False))
    if transom is not None:
        v = v0 + (v1 - v0) * transom + sv
        if seen_v0 + 0.02 < v < seen_v1 - 0.02:
            batch.add("iso-mull", frame.poly([(max(u0 + su, seen_u0), v), (min(u1 + su, seen_u1), v)], False))


def _facade_v12(batch: _Batch, frame: Frame, item: dict[str, Any], vol: dict[str, Any], door: tuple[float, float] | None,
                sign_band: bool) -> None:
    """Window openings with depth on one face of a building volume: a glazed lobby, upper floors by window kind and
    an optional blank band that carries the wall lettering."""
    floor_h, kind, cap = item["floor_h"], item["windows"], vol["cap"]
    floors, lobby = vol["floors"], vol["lobby"]
    fw, fh = frame.w, frame.h
    margin = min(0.16, fw * 0.08)
    lobby_top = fh - lobby
    rows = [(cap + i * floor_h, cap + (i + 1) * floor_h) for i in range(floors - 1)]
    if sign_band and rows:
        rows = rows[1:]
    if kind in ("grid", "punched"):
        depth = 0.07 if kind == "punched" else 0.05
        cols = max(1, int((fw - 2 * margin) / 0.42))
        cell = (fw - 2 * margin) / cols
        for top, bottom in rows:
            for col in range(cols):
                left = margin + col * cell + cell * 0.2
                right = margin + (col + 1) * cell - cell * 0.2
                _recess(batch, frame, left, top + floor_h * 0.24, right, bottom - floor_h * 0.18, depth)
    elif kind in ("ribbon", "bands"):
        su, sv = _depth_shift(frame)
        for top, bottom in rows:
            opening = (margin, top + floor_h * 0.22, fw - margin, bottom - floor_h * 0.16)
            seen = _recess(batch, frame, *opening, 0.05)
            _mullions(batch, frame, seen, (su * 0.05, sv * 0.05), opening, 0.3)
    elif kind in ("curtain", "fins") and rows:
        top, bottom = rows[0][0] + 0.04, rows[-1][1] - 0.04
        batch.add("iso-glass", frame.poly([(margin, top), (fw - margin, top), (fw - margin, bottom), (margin, bottom)]))
        for row_top, _ in rows[1:]:
            batch.add("iso-mull", frame.poly([(margin, row_top), (fw - margin, row_top)], False))
        pitch = 0.17 if kind == "fins" else 0.3
        count = max(2, int(round((fw - 2 * margin) / pitch)))
        us = [margin + (fw - 2 * margin) * i / count for i in range(count + 1)]
        _fins(batch, frame, us, top, bottom, 0.08 if kind == "fins" else 0.035)
        batch.add("iso-d", frame.poly([(margin, top), (fw - margin, top), (fw - margin, bottom), (margin, bottom)]))
    # A slab edge between the upper floors and the lobby, then the lobby glazing around the door.
    if floors > 1:
        batch.add("iso-d", frame.poly([(0.0, lobby_top), (fw, lobby_top)], False))
    spans = [(margin, fw - margin)]
    if door is not None:
        spans = [(margin, door[0] - 0.1), (door[1] + 0.1, fw - margin)]
    su, sv = _depth_shift(frame)
    glazed = item["lobby"] and kind != "none"
    for left, right in spans:
        if right - left < 0.24:
            continue
        if glazed:
            opening = (left, lobby_top + 0.1, right, fh - 0.05)
            seen = _recess(batch, frame, *opening, 0.07)
            _mullions(batch, frame, seen, (su * 0.07, sv * 0.07), opening, 0.34, 0.68)
        elif kind not in ("none",):
            cols = max(1, int((right - left) / 0.42))
            cell = (right - left) / cols
            for col in range(cols):
                _recess(batch, frame, left + col * cell + cell * 0.2, lobby_top + floor_h * 0.24,
                        left + (col + 1) * cell - cell * 0.2, fh - floor_h * 0.18, 0.05)


def _place_rects(area: tuple[float, float, float, float], sizes: list[tuple[str, float, float]], rng: _Rand,
                 gap: float, blocked: list[tuple[float, float, float, float]] | None = None,
                 tries: int = 48) -> list[tuple[str, tuple[float, float, float, float]]]:
    """Seeded rejection placement: each part takes the first candidate inside ``area`` that keeps ``gap`` from
    every part already placed and every blocked rectangle. Rectangles are (x0, x1, y0, y1)."""
    ax0, ax1, ay0, ay1 = area
    taken = list(blocked or [])
    placed: list[tuple[str, tuple[float, float, float, float]]] = []
    for kind, w, d in sizes:
        for _ in range(tries):
            if rng.random() < 0.5 and kind not in ("cap", "vent-pipe", "hvac"):
                w, d = d, w
            if w > ax1 - ax0 + EPS or d > ay1 - ay0 + EPS:
                continue
            x0 = ax0 + round(rng.random() * (ax1 - ax0 - w) / 0.02) * 0.02
            y0 = ay0 + round(rng.random() * (ay1 - ay0 - d) / 0.02) * 0.02
            rect = (x0, x0 + w, y0, y0 + d)
            if all(rect[1] + gap <= o[0] or o[1] + gap <= rect[0] or rect[3] + gap <= o[2] or o[3] + gap <= rect[2]
                   for o in taken):
                placed.append((kind, rect))
                taken.append(rect)
                break
    return placed


def _rooftop_ops(proj: Projection, vol: dict[str, Any], item: dict[str, Any], style: str) -> list[tuple[Any, ...]]:
    """Rooftop plant on a volume's roof deck: a stair core with a door, fan units and vent pipes, placed by seed
    clear of the parapet that would hide them."""
    x0, x1, y0, y1, _, z1 = vol["box"]
    deck = z1 - vol["cap"]
    near = PARAPET_T + 0.06
    far = PARAPET_T + vol["cap"] * 1.6 + 0.08
    area = (x0 + near, x1 - far, y0 + near, y1 - far)
    if area[1] - area[0] < 0.4 or area[3] - area[2] < 0.4:
        return []
    rng = _Rand(item["seed"], 7)
    wanted = [("core", 0.56, 0.46), ("hvac", 0.34, 0.34), ("hvac", 0.34, 0.34), ("vent-pipe", 0.12, 0.12),
              ("vent-pipe", 0.12, 0.12), ("vent-pipe", 0.12, 0.12)]
    placed = _place_rects(area, wanted, rng, 0.1)
    heights = {"core": 0.4, "hvac": 0.15, "vent-pipe": 0.12}
    boxes = [_box(r[0], r[1], r[2], r[3], deck, deck + heights[kind]) for kind, r in placed]
    ops: list[tuple[Any, ...]] = []
    door_face = item.get("entrance") or "x+"
    for index in _paint_order(boxes, proj.view):
        kind, box = placed[index][0], boxes[index]
        if kind == "vent-pipe":
            cx, cy = (box[0] + box[1]) / 2, (box[2] + box[3]) / 2
            pipe = _box(cx - 0.035, cx + 0.035, cy - 0.035, cy + 0.035, deck, box[5] - 0.025)
            ops += _prism(proj, pipe, 0.035).ops(style)
            ops += _prism(proj, _box(cx - 0.06, cx + 0.06, cy - 0.06, cy + 0.06, box[5] - 0.025, box[5]), 0.06).ops(style)
            continue
        ops += _prism(proj, box, 0.02).ops(style)
        batch = _Batch()
        lid = _face(proj, box, "top")
        if kind == "core":
            batch.add("iso-d", lid.rrect(0.05, 0.05, lid.w - 0.05, lid.h - 0.05, 0.02))
            front = _face(proj, box, door_face)
            _recess(batch, front, front.w * 0.36, front.h * 0.3, front.w * 0.66, front.h, 0.04, back="iso-hole",
                    edge="iso-d", inner=None)
        else:
            batch.add("iso-d", lid.circle(lid.w / 2, lid.h / 2, min(lid.w, lid.h) * 0.36))
            batch.add("iso-hole", lid.circle(lid.w / 2, lid.h / 2, min(lid.w, lid.h) * 0.1))
            for frame in (_face(proj, box, "x+"), _face(proj, box, "y+")):
                for i in range(1, 4):
                    v = frame.h * i / 4
                    batch.add("iso-d iso-faint", frame.poly([(0.05, v), (frame.w - 0.05, v)], False))
        ops += batch.ops(FACADE_ORDER)
    return ops


def _wall_sign(proj: Projection, item: dict[str, Any], frame: Frame, top: float, bottom: float,
               warnings: list[str]) -> list[tuple[Any, ...]]:
    """Lettering set into a facade band, with the building's mark as a logo before it."""
    sign = item["sign"]
    size = max(MIN_LABEL_PX, item["label_size"])
    mark = bool(item.get("glyph") or item.get("icon_data"))
    text_w = _text_width(sign, size) / proj.unit
    g = min((bottom - top) * 0.7, size * 1.3 / proj.unit) if mark else 0.0
    gap = 0.08 if mark else 0.0
    total = g + gap + text_w
    if total > frame.w * 0.9:
        warnings.append(f"{item['where']}: sign {sign!r} needs about {_fmt(total)} grid units but the facade band "
                        f"offers {_fmt(frame.w * 0.9)}; shorten it or widen the building")
    if size / proj.unit > (bottom - top) * 0.9:
        warnings.append(f"{item['where']}: the sign band is shorter than the {_fmt(size)} px lettering; raise floor_h")
    start = (frame.w - total) / 2
    mid = (top + bottom) / 2
    ops: list[tuple[Any, ...]] = []
    if mark:
        ops += _mark(frame, item, start + g / 2, mid, g, "iso-g")
    ops.append(frame.text("iso-sign", sign, start + g + gap, mid, size, "start"))
    return ops


def _portal_ops(proj: Projection, item: dict[str, Any], style: str) -> list[tuple[Any, ...]]:
    """A deep entrance portal: a framed box standing out of the facade, glazed doors set deep inside it, and a
    thin canopy slab over it."""
    portal, face = item["portal"], item["entrance"]
    ops = _prism(proj, portal, 0.0).ops(style)
    frame = _face(proj, portal, face)
    side, fascia = min(0.13, frame.w * 0.12), min(0.2, frame.h * 0.2)
    opening = (side, fascia, frame.w - side, frame.h)
    depth = PORTAL_DEPTH + 0.06
    batch = _Batch()
    seen = _recess(batch, frame, *opening, depth, back="iso-glass", edge="iso-o", inner="iso-d")
    batch.add("iso-dim", frame.poly([(seen[0], seen[1]), (seen[2], seen[1]), (seen[2], seen[3]), (seen[0], seen[3])]))
    su, sv = _depth_shift(frame)
    _mullions(batch, frame, seen, (su * depth, sv * depth), opening, (opening[2] - opening[0]) / 4, 0.3)
    mid = (opening[0] + opening[2]) / 2 + su * depth
    for du in (-0.05, 0.05):
        if seen[0] < mid + du < seen[2]:
            batch.add("iso-d", frame.poly([(mid + du, frame.h * 0.55 + sv * depth), (mid + du, frame.h * 0.72 + sv * depth)], False))
    ops += batch.ops(FACADE_ORDER)
    x0, x1, y0, y1, _, z1 = portal
    if face == "x+":
        canopy = _box(x0, x1 + PORTAL_LIP, y0 - 0.08, y1 + 0.08, z1, z1 + 0.06)
    else:
        canopy = _box(x0 - 0.08, x1 + 0.08, y0, y1 + PORTAL_LIP, z1, z1 + 0.06)
    return ops + _prism(proj, canopy, 0.0).ops(style)


def _render_building_v12(proj: Projection, item: dict[str, Any], style: str, warnings: list[str]) -> list[tuple[Any, ...]]:
    ops: list[tuple[Any, ...]] = []
    plinth = item.get("plinth") or 0.0
    body = item["body"]
    if plinth > 0:
        base = _box(body[0] - plinth, body[1] + plinth, body[2] - plinth, body[3] + plinth, item["z"], body[4])
        ops += _prism(proj, base, min(0.1, plinth / 2)).ops(style)
        paving = _face(proj, base, "top", "x")
        joints: list[tuple[Any, ...]] = []
        for i in range(1, int((base[1] - base[0]) / 0.5)):
            u = i * 0.5
            if u < plinth - 0.05 or u > base[1] - base[0] - plinth + 0.05:
                joints += paving.poly([(u, 0.06), (u, paving.h - 0.06)], False)
        if joints:
            ops.append(("path", "iso-d iso-faint", joints))
    volumes, entry = item["volumes"], item["entry"]
    entrance = item.get("entrance")
    sign_face = item.get("sign_face") or entrance or "x+"
    wall_sign = bool(item.get("sign")) and item["sign_mount"] == "wall" and entry["floors"] >= 2
    if item.get("sign") and item["sign_mount"] == "wall" and not wall_sign:
        warnings.append(f"{item['where']}: wall lettering needs a volume of at least 2 floors; use sign_mount 'plaque'")
    for index in _paint_order([v["box"] for v in volumes], proj.view):
        vol = volumes[index]
        box = vol["box"]
        ops += _prism(proj, box, 0.0).ops(style)
        batch = _Batch()
        texts: list[tuple[Any, ...]] = []
        for face in ("y+", "x+"):
            frame = _face(proj, box, face)
            door = None
            if vol is entry and entrance == face and item["portal"] is not None:
                p = item["portal"]
                lo, hi = (box[3] - p[3], box[3] - p[2]) if face == "x+" else (p[0] - box[0], p[1] - box[0])
                door = (lo, hi)
            band = wall_sign and vol is entry and face == sign_face
            _facade_v12(batch, frame, item, vol, door, band)
            if band:
                top = vol["cap"]
                texts += _wall_sign(proj, item, frame, top, top + item["floor_h"], warnings)
            if vol is entry and face == sign_face and item.get("sign") and item["sign_mount"] == "plaque":
                texts += _plaque(proj, item, frame, vol, door, warnings)
        if vol["cap"] > 0:
            roof = _face(proj, box, "top", "x")
            _recess(batch, roof, PARAPET_T, PARAPET_T, roof.w - PARAPET_T, roof.h - PARAPET_T, vol["cap"],
                    back="iso-deck", edge="iso-d", inner=None)
        ops += batch.ops(FACADE_ORDER) + texts
        if vol["role"] == "main" and item["rooftop"] == "plant":
            ops += _rooftop_ops(proj, vol, item, style)
        if vol is entry and item["portal"] is not None:
            ops += _portal_ops(proj, item, style)
    if item.get("sign") and item["sign_mount"] == "roof":
        ops += _roof_sign(proj, item, volumes[0]["box"], style, warnings)
    label_item = {**item, "glyph": None, "icon_data": None} if item.get("sign") else item
    return ops + _labelled_faces(proj, label_item, volumes[0]["box"], warnings)


def _roof_sign(proj: Projection, item: dict[str, Any], box: tuple[float, ...], style: str,
               warnings: list[str]) -> list[tuple[Any, ...]]:
    """The schema 1.1 sign board on two legs above the roof edge, kept as the ``roof`` mount."""
    x0, x1, y0, y1, _, z1 = box
    face = item.get("sign_face") or item.get("entrance") or "y+"
    size = max(MIN_LABEL_PX, item["label_size"])
    mark = 0.34 if (item.get("glyph") or item.get("icon_data")) else 0.0
    length = (_text_width(item["sign"], size) / proj.unit + mark + (0.12 if mark else 0.0)) / 0.88 + 0.12
    span = (x1 - x0) if face == "y+" else (y1 - y0)
    length = min(length, span - 0.2)
    mid = ((x0 + x1) / 2) if face == "y+" else ((y0 + y1) / 2)
    if face == "y+":
        board = _box(mid - length / 2, mid + length / 2, y1 - 0.18, y1 - 0.12, z1 + 0.1, z1 + SIGN_H)
    else:
        board = _box(x1 - 0.18, x1 - 0.12, mid - length / 2, mid + length / 2, z1 + 0.1, z1 + SIGN_H)
    legs = _face(proj, _box(board[0], board[1], board[2], board[3], z1, board[4]), face)
    ops: list[tuple[Any, ...]] = [("path", "iso-d", legs.poly([(0.16, 0), (0.16, legs.h)], False) +
                                   legs.poly([(legs.w - 0.16, 0), (legs.w - 0.16, legs.h)], False))]
    ops += _prism(proj, board, 0.04, 1 if face == "y+" else 0).ops(style)
    sign_item = {"label": item["sign"], "label_size": size, "glyph": item.get("glyph"), "icon_data": item.get("icon_data"),
                 "where": f"{item['where']}.sign"}
    return ops + _face_content(_face(proj, board, face), sign_item, warnings)


def _plaque(proj: Projection, item: dict[str, Any], frame: Frame, vol: dict[str, Any], door: tuple[float, float] | None,
            warnings: list[str]) -> list[tuple[Any, ...]]:
    """A small name plate on the lobby wall beside the door."""
    sign = item["sign"]
    size = max(MIN_LABEL_PX, item["label_size"])
    width = _text_width(sign, size) / proj.unit + 0.2
    height = size / proj.unit * 1.5
    lobby_top = frame.h - vol["lobby"]
    candidates = [door[1] + 0.12, door[0] - 0.12 - width] if door else [(frame.w - width) / 2]
    fits = [u for u in candidates if 0.08 - EPS <= u and u + width <= frame.w - 0.08 + EPS]
    if not fits or height > vol["lobby"] - 0.1:
        warnings.append(f"{item['where']}: the plaque for {sign!r} does not fit the lobby wall beside the door; "
                        f"shorten the sign, widen the building or use sign_mount 'wall'")
        return []
    left = fits[0]
    top = lobby_top + (vol["lobby"] - height) * 0.4
    return [("path", "iso-t", frame.rrect(left, top, left + width, top + height, 0.04)),
            ("path", "iso-o", frame.rrect(left, top, left + width, top + height, 0.04)),
            frame.text("iso-sign", sign, left + width / 2, top + height / 2, size, "middle")]


# Micro-detail kit -------------------------------------------------------------

# Part footprints along and across their strip, and heights, in grid units.
PARTS = {
    "ic": (0.44, 0.3, 0.06), "chip": (0.24, 0.24, 0.05), "cap": (0.13, 0.13, 0.15), "socket": (0.46, 0.17, 0.1),
    "header": (0.5, 0.1, 0.04), "vent": (0.46, 0.18, 0.0), "plate": (0.58, 0.26, 0.012),
}
PART_MIX = {
    1: ("ic", "cap", "socket", "cap"),
    2: ("ic", "cap", "socket", "chip", "cap", "header", "vent", "ic", "cap"),
    3: ("ic", "cap", "chip", "cap", "socket", "header", "chip", "vent", "cap", "ic", "cap", "chip"),
}
PART_GAP = {1: 0.22, 2: 0.13, 3: 0.09}
DETAIL_ORDER = ("iso-hole", "iso-trace", "iso-node")


def _rects_clear(a: tuple[float, ...], b: tuple[float, ...], gap: float) -> bool:
    return a[1] + gap <= b[0] + EPS or b[1] + gap <= a[0] + EPS or a[3] + gap <= b[2] + EPS or b[3] + gap <= a[2] + EPS


def _subtract(rect: tuple[float, float, float, float], hole: tuple[float, float, float, float]
              ) -> tuple[float, float, float, float] | None:
    """The largest axis-aligned piece of rect that avoids hole (x0, x1, y0, y1)."""
    if _rects_clear(rect, hole, 0.0):
        return rect
    x0, x1, y0, y1 = rect
    pieces = [(x0, min(x1, hole[0]), y0, y1), (max(x0, hole[1]), x1, y0, y1),
              (x0, x1, y0, min(y1, hole[2])), (x0, x1, max(y0, hole[3]), y1)]
    pieces = [p for p in pieces if p[1] - p[0] > EPS and p[3] - p[2] > EPS]
    if not pieces:
        return None
    return max(pieces, key=lambda p: ((p[1] - p[0]) * (p[3] - p[2]), -p[0], -p[2]))


def _pack_strip(strip: tuple[float, float, float, float], rng: _Rand, density: int, toward: str | None,
                first: str | None = None) -> list[tuple[str, tuple[float, float, float, float]]]:
    """Fill a strip with parts in one tidy row along its long axis: seeded kinds and spacing, never overlapping.
    ``toward`` (x-, x+, y-, y+) aligns parts to the strip edge that faces the package."""
    sx0, sx1, sy0, sy1 = strip
    along_x = (sx1 - sx0) >= (sy1 - sy0)
    start, end = (sx0, sx1) if along_x else (sy0, sy1)
    lo, hi = (sy0, sy1) if along_x else (sx0, sx1)
    depth = hi - lo
    mix, gap = PART_MIX[density], PART_GAP[density]
    placed: list[tuple[str, tuple[float, float, float, float]]] = []
    cursor = start + rng.uniform(0.0, gap)
    pending = [first] if first else []
    misses = 0
    while misses < 6:
        kind = pending.pop() if pending else mix[int(rng.random() * len(mix)) % len(mix)]
        along, across, _ = PARTS[kind]
        if across > depth - 0.04:
            along, across = across, along
            if across > depth - 0.04 or kind in ("header", "vent", "plate", "socket", "ic"):
                misses += 1
                continue
        if cursor + along > end - 0.02:
            misses += 1
            continue
        if toward in ("x-", "y-"):
            offset = lo + 0.03
        elif toward in ("x+", "y+"):
            offset = hi - 0.03 - across
        else:
            offset = lo + (depth - across) / 2
        rect = (cursor, cursor + along, offset, offset + across) if along_x else (offset, offset + across, cursor, cursor + along)
        placed.append((kind, rect))
        cursor += along + gap + rng.uniform(0.0, gap * 0.8)
    return placed


def _part_ops(proj: Projection, kind: str, rect: tuple[float, float, float, float], zb: float,
              style: str) -> list[tuple[Any, ...]]:
    """One populated part on a board plane: back pins, body, top markings, front pins."""
    x0, x1, y0, y1 = rect
    h = PARTS[kind][2]
    ground = Frame(proj, (0.0, 0.0, zb), (1, 0, 0), (0, 1, 0), 0, 0)
    ops: list[tuple[Any, ...]] = []
    if kind == "vent":
        batch = _Batch()
        along_x = x1 - x0 >= y1 - y0
        count = max(3, int(((x1 - x0) if along_x else (y1 - y0)) / 0.075))
        for i in range(count):
            t0 = (x0 if along_x else y0) + 0.02 + i * 0.075
            if along_x:
                _recess(batch, ground, t0, y0, t0 + 0.035, y1, 0.03, back="iso-hole", edge="iso-d", inner=None)
            else:
                _recess(batch, ground, x0, t0, x1, t0 + 0.035, 0.03, back="iso-hole", edge="iso-d", inner=None)
        return batch.ops(FACADE_ORDER)
    if kind == "plate":
        return [("path", "iso-t", ground.rrect(x0, y0, x1, y1, 0.03)), ("path", "iso-d", ground.rrect(x0, y0, x1, y1, 0.03)),
                ("path", "iso-d iso-faint", ground.poly([(x0 + 0.06, y0 + 0.09), (x1 - 0.18, y0 + 0.09)], False)
                 + ground.poly([(x0 + 0.06, y1 - 0.08), (x1 - 0.26, y1 - 0.08)], False))]
    body = _box(x0, x1, y0, y1, zb, zb + h)
    pins_back: list[tuple[Any, ...]] = []
    pins_front: list[tuple[Any, ...]] = []
    if kind in ("ic", "chip"):
        along_x = x1 - x0 >= y1 - y0
        sides = (("y-", "y+") if along_x else ("x-", "x+")) if kind == "ic" else ("x-", "y-", "x+", "y+")
        for side in sides:
            target = pins_back if side.endswith("-") else pins_front
            span = (x0, x1) if side[0] == "y" else (y0, y1)
            count = max(2, int((span[1] - span[0] - 0.08) / 0.07))
            for i in range(count):
                t = span[0] + 0.04 + (span[1] - span[0] - 0.08) * (i + 0.5) / count
                if side == "y-":
                    target += ground.poly([(t, y0 - 0.045), (t, y0)], False)
                elif side == "y+":
                    target += ground.poly([(t, y1), (t, y1 + 0.045)], False)
                elif side == "x-":
                    target += ground.poly([(x0 - 0.045, t), (x0, t)], False)
                else:
                    target += ground.poly([(x1, t), (x1 + 0.045, t)], False)
    if pins_back:
        ops.append(("path", "iso-tick", pins_back))
    radius = (x1 - x0) / 2 if kind == "cap" else 0.02
    ops += _prism(proj, body, radius).ops(style)
    lid = _face(proj, body, "top")
    if kind == "cap":
        cx, cy = lid.w / 2, lid.h / 2
        ops.append(("path", "iso-d", lid.poly([(cx - 0.035, cy), (cx + 0.035, cy)], False)
                    + lid.poly([(cx, cy - 0.035), (cx, cy + 0.035)], False)))
    elif kind == "socket":
        batch = _Batch()
        _recess(batch, lid, 0.05, 0.045, lid.w - 0.05, lid.h - 0.045, 0.07, back="iso-hole", edge="iso-d", inner=None)
        ops += batch.ops(FACADE_ORDER)
    elif kind == "header":
        posts: list[tuple[Any, ...]] = []
        along_x = x1 - x0 >= y1 - y0
        count = max(2, int(((x1 - x0) if along_x else (y1 - y0)) / 0.075))
        for i in range(count):
            t = (x0 if along_x else y0) + 0.04 + i * 0.075
            px, py = (t, (y0 + y1) / 2) if along_x else ((x0 + x1) / 2, t)
            posts += [("M", proj(px, py, zb + h)), ("L", proj(px, py, zb + h + 0.1))]
        ops.append(("path", "iso-o", posts))
    else:
        ops.append(("path", "iso-d iso-faint", lid.rrect(0.04, 0.04, lid.w - 0.04, lid.h - 0.04, 0.015)))
        ops.append(("path", "iso-dotf", lid.circle(0.07, 0.07, 0.018)))
    if pins_front:
        ops.append(("path", "iso-tick", pins_front))
    return ops


def _traces(ground: Frame, parts: list[tuple[str, tuple[float, float, float, float]]],
            target: tuple[float, float, float, float], batch: _Batch) -> None:
    """Short buses from the parts that face the target (a package) straight to its nearest edge."""
    tx0, tx1, ty0, ty1 = target
    for kind, (x0, x1, y0, y1) in parts:
        if kind not in ("ic", "chip", "socket", "header"):
            continue
        if x1 <= tx0 or x0 >= tx1:
            lane = None
        else:
            lane = "y"
        if lane is None and (y1 <= ty0 or y0 >= ty1):
            continue
        lines = 3 if kind in ("ic", "socket") else 2
        if lane == "y":
            lo, hi = max(x0, tx0) + 0.05, min(x1, tx1) - 0.05
            if hi - lo < 0.06:
                continue
            a, b = (y1, ty0) if y1 <= ty0 else (ty1, y0)
            for i in range(lines):
                u = lo + (hi - lo) * (i + 0.5) / lines
                batch.add("iso-trace", ground.poly([(u, a), (u, b)], False))
                batch.add("iso-node", ground.circle(u, a if y1 <= ty0 else b, 0.022))
        else:
            lo, hi = max(y0, ty0) + 0.05, min(y1, ty1) - 0.05
            if hi - lo < 0.06:
                continue
            a, b = (x1, tx0) if x1 <= tx0 else (tx1, x0)
            for i in range(lines):
                v = lo + (hi - lo) * (i + 0.5) / lines
                batch.add("iso-trace", ground.poly([(a, v), (b, v)], False))
                batch.add("iso-node", ground.circle(a if x1 <= tx0 else b, v, 0.022))


def _populate(proj: Projection, area: tuple[float, float, float, float], zb: float, package: tuple[float, ...] | None,
              blocked: list[tuple[float, float, float, float]], density: int, seed: int,
              style: str) -> tuple[list[tuple[Any, ...]], list[tuple[str, tuple[float, float, float, float]]]]:
    """Corner screws, seeded rows of parts in the strips around an optional package, buses to it and trace runs.
    Returns the ops (traces under parts) and the placed parts, which never overlap each other or ``blocked``."""
    ax0, ax1, ay0, ay1 = area
    rng = _Rand(seed, 5)
    ground = Frame(proj, (0.0, 0.0, zb), (1, 0, 0), (0, 1, 0), 0, 0)
    ops: list[tuple[Any, ...]] = []
    screws: list[tuple[Any, ...]] = []
    slots: list[tuple[Any, ...]] = []
    corner = 0.2
    for cx, cy in ((ax0 + 0.08, ay0 + 0.08), (ax1 - 0.08, ay0 + 0.08), (ax0 + 0.08, ay1 - 0.08), (ax1 - 0.08, ay1 - 0.08)):
        screws += ground.circle(cx, cy, 0.05)
        slots += ground.poly([(cx - 0.032, cy + 0.02), (cx + 0.032, cy - 0.02)], False)
    if density <= 0:
        return [("path", "iso-node", screws), ("path", "iso-d", slots)], []
    clear = 0.16
    if package is not None:
        px0, px1, py0, py1 = package[:4]
        hole = (px0 - clear, px1 + clear, py0 - clear, py1 + clear)
        strips = [((ax0 + corner, ax1 - corner, ay0, hole[2]), "y+"), ((ax0 + corner, ax1 - corner, hole[3], ay1), "y-"),
                  ((ax0, hole[0], hole[2], hole[3]), "x+"), ((hole[1], ax1, hole[2], hole[3]), "x-")]
    else:
        rows = max(1, int((ay1 - ay0) / 0.5))
        pitch = (ay1 - ay0) / rows
        strips = [((ax0 + corner, ax1 - corner, ay0 + i * pitch, ay0 + (i + 1) * pitch), None) for i in range(rows)]
    placed: list[tuple[str, tuple[float, float, float, float]]] = []
    first = "plate" if density >= 2 else None
    for strip, toward in strips:
        for hole in blocked:
            strip = _subtract(strip, hole) if strip else None
        if strip is None or strip[1] - strip[0] < 0.2 or strip[3] - strip[2] < 0.2:
            continue
        parts = _pack_strip(strip, rng, density, toward, first)
        if first and any(kind == first for kind, _ in parts):
            first = None
        placed += [(kind, rect) for kind, rect in parts
                   if all(_rects_clear(rect, b, 0.02) for b in blocked) and all(_rects_clear(rect, r, 0.02) for _, r in placed)]
    batch = _Batch()
    if package is not None:
        _traces(ground, placed, package[:4], batch)
    # Trace runs along the long free edges of the board, broken where a part sits.
    if density >= 2:
        for v in (ay0 + 0.02, ay1 - 0.02):
            run = (ax0 + corner + 0.04, ax1 - corner - 0.04, v - 0.01, v + 0.01)
            if all(_rects_clear(run, hole, 0.04) for hole in blocked):
                batch.add("iso-trace", ground.poly([(run[0], v), (run[1], v)], False))
    ops += batch.ops(DETAIL_ORDER)
    ops += [("path", "iso-node", screws), ("path", "iso-d", slots)]
    boxes = [_box(*rect, zb, zb + max(PARTS[kind][2], 0.001)) for kind, rect in placed]
    for index in _paint_order(boxes, proj.view):
        ops += _part_ops(proj, placed[index][0], placed[index][1], zb, style)
    return ops, placed


def _render_core_v12(proj: Projection, item: dict[str, Any], style: str, warnings: list[str]) -> list[tuple[Any, ...]]:
    """A populated processor board: an enclosure with ports and vents, seeded parts with buses to a pinned package
    whose lid carries a fin comb and a die window, exploded circuit plates and the inverted cap with the mark."""
    board = item["body"]
    x0, x1, y0, y1, z0, zb = board
    r = item["radius"]
    density = item["detail"] if item["parts"] else 0
    ops: list[tuple[Any, ...]] = _prism(proj, board, r).ops(style)
    batch = _Batch()
    for face in ("y+", "x+"):
        frame = _face(proj, board, face)
        bh = frame.h
        batch.add("iso-d iso-faint", frame.poly([(r + 0.04, bh * 0.66), (frame.w - r - 0.04, bh * 0.66)], False))
        if frame.w > 1.6 and bh > 0.16:
            for i in range(2):
                u = frame.w - r - 0.26 - i * 0.5
                _recess(batch, frame, u - 0.34, bh * 0.22, u, bh * 0.58, 0.08, back="iso-hole", edge="iso-d", inner=None)
            count = int(min(frame.w * 0.28, 1.3) / 0.075)
            for i in range(count):
                u = r + 0.2 + i * 0.075
                _recess(batch, frame, u, bh * 0.24, u + 0.032, bh * 0.56, 0.03, back="iso-hole", edge=None, inner=None)
            batch.add("iso-led", frame.circle(r + 0.28 + count * 0.075, bh * 0.4, 0.035))
    ops += batch.ops(FACADE_ORDER + ("iso-led",))
    axis = _label_axis(item, board)
    top = _face(proj, board, "top", axis)
    ops.append(("path", "iso-d iso-faint", top.rrect(0.1, 0.1, top.w - 0.1, top.h - 0.1, max(0.0, r - 0.06))))
    label = item.get("label")
    strip = max(0.44, item["label_size"] / proj.unit + 0.26) if label and item["label_face"] == "top" else 0.0
    margin = max(0.4, min(x1 - x0, y1 - y0) * 0.2) if density else max(0.24, min(x1 - x0, y1 - y0) * 0.14)
    pu0, pv0, pu1, pv1 = margin, margin, top.w - margin, top.h - margin - strip
    if pv1 - pv0 < 0.5:
        warnings.append(f"{item['where']}: the label strip leaves the package only {_fmt(max(0.0, pv1 - pv0))} grid "
                        f"units; enlarge the core or move the label to a side face")
        pv1 = pv0 + max(0.5, pv1 - pv0)
    pkg_top = zb + CORE_PACKAGE_H
    package = _frame_box(top, pu0, pv0, pu1, pv1, zb, pkg_top)
    px0, px1, py0, py1 = package[:4]
    blocked = []
    if strip:
        blocked.append(_frame_box(top, 0.0, top.h - strip - 0.04, top.w, top.h, zb, zb)[:4])
    lip = 0.16
    detail_ops, _ = _populate(proj, (x0 + lip, x1 - lip, y0 + lip, y1 - lip), zb, package, blocked, density,
                              item["seed"], style)
    ops += detail_ops
    # The package: a substrate ringed by leads, then a lid with a fin comb on its sides and a die window.
    ground = Frame(proj, (0.0, 0.0, zb), (1, 0, 0), (0, 1, 0), 0, 0)
    substrate = _box(px0 - 0.06, px1 + 0.06, py0 - 0.06, py1 + 0.06, zb, zb + 0.045)
    leads_back: list[tuple[Any, ...]] = []
    leads_front: list[tuple[Any, ...]] = []
    if item["pins"]:
        sx0, sx1, sy0, sy1 = substrate[:4]
        for lo, hi, fixed, horizontal, back in ((sx0, sx1, sy0, True, True), (sx0, sx1, sy1, True, False),
                                                (sy0, sy1, sx0, False, True), (sy0, sy1, sx1, False, False)):
            count = int((hi - lo - 0.2) / 0.065)
            target = leads_back if back else leads_front
            for i in range(count):
                t = lo + 0.1 + (hi - lo - 0.2) * (i + 0.5) / count
                reach = -0.07 if back else 0.07
                if horizontal:
                    target += ground.poly([(t, fixed), (t, fixed + reach)], False)
                else:
                    target += ground.poly([(fixed, t), (fixed + reach, t)], False)
        ops.append(("path", "iso-tick", leads_back))
    ops += _prism(proj, substrate, 0.05).ops(style)
    if leads_front:
        ops.append(("path", "iso-tick", leads_front))
    lid = _box(px0 + 0.1, px1 - 0.1, py0 + 0.1, py1 - 0.1, substrate[5], pkg_top)
    ops += _prism(proj, lid, 0.07).ops(style)
    comb = _Batch()
    for face in ("y+", "x+"):
        frame = _face(proj, lid, face)
        count = int((frame.w - 0.24) / 0.06)
        for i in range(count):
            u = 0.12 + (frame.w - 0.24) * (i + 0.5) / count
            comb.add("iso-tick", frame.poly([(u, frame.h * 0.28), (u, frame.h * 0.8)], False))
    die = _face(proj, lid, "top", "x")
    comb.add("iso-d iso-faint", die.rrect(0.07, 0.07, die.w - 0.07, die.h - 0.07, 0.05))
    _recess(comb, die, die.w * 0.24, die.h * 0.24, die.w * 0.76, die.h * 0.76, 0.03, back="iso-glass", edge="iso-d",
            inner=None)
    comb.add("iso-dotf", die.circle(0.18, 0.18, 0.035))
    ops += comb.ops(FACADE_ORDER + ("iso-tick", "iso-dotf"))
    # Exploded plates: a memory layer, then circuit layers, joined to the package by dashed guides.
    grow = 0.08
    plate_fp = (px0 - grow, px1 + grow, py0 - grow, py1 + grow)
    corner = max(0.0, min(r, 0.2))
    inset = corner * (1 - 1 / SQRT2)
    guide_xy = [(plate_fp[0] + inset, plate_fp[2] + inset), (plate_fp[1] - inset, plate_fp[2] + inset),
                (plate_fp[0] + inset, plate_fp[3] - inset), (plate_fp[1] - inset, plate_fp[3] - inset)]
    level, surface = pkg_top, package
    for i in range(item["layers"]):
        zp = pkg_top + item["spacing"] * (i + 1)
        ops.append(("path", "iso-guide", [seg for gx, gy in guide_xy for seg in (("M", proj(gx, gy, level)), ("L", proj(gx, gy, zp)))]))
        plate = _box(*plate_fp, zp, zp + CORE_PLATE_H)
        ops += _prism(proj, plate, corner).ops(style)
        face = _face(proj, plate, "top", "x")
        layer = _Batch()
        layer.add("iso-d iso-faint", face.rrect(0.12, 0.12, face.w - 0.12, face.h - 0.12, max(0.0, corner - 0.06)))
        if i == 0 and item["layers"] > 1 and density:
            cols = max(2, int((face.w - 0.5) / 0.42))
            cell = (face.w - 0.5) / cols
            for row in range(2):
                v = face.h * 0.55 + row * 0.42
                if v + 0.3 > face.h - 0.16:
                    continue
                for col in range(cols):
                    u = 0.25 + col * cell
                    layer.add("iso-l", face.rrect(u + 0.04, v, u + cell - 0.04, v + 0.3, 0.03))
                    layer.add("iso-d", face.rrect(u + 0.04, v, u + cell - 0.04, v + 0.3, 0.03))
                    layer.add("iso-trace", face.poly([(u + cell / 2, v), (u + cell / 2, v - 0.16)], False))
            layer.add("iso-trace", face.poly([(0.3, face.h * 0.55 - 0.16), (face.w - 0.3, face.h * 0.55 - 0.16)], False))
        else:
            traces, nodes = _trace_pattern(i % 2 == 1)
            for trace in traces:
                layer.add("iso-d", face.poly([(0.16 + u * (face.w - 0.32), 0.16 + v * (face.h - 0.32)) for u, v in trace], False))
            for u, v in nodes:
                layer.add("iso-node", face.circle(0.16 + u * (face.w - 0.32), 0.16 + v * (face.h - 0.32), 0.055))
        ops += layer.ops(("iso-l", "iso-trace", "iso-d iso-faint", "iso-d", "iso-node"))
        level, surface = zp + CORE_PLATE_H, plate
    if item["cap"]:
        sx0, sx1, sy0, sy1 = surface[:4]
        side = min(sx1 - sx0, sy1 - sy0) * 0.46
        cx, cy = (sx0 + sx1) / 2, (sy0 + sy1) / 2
        cap = _box(cx - side / 2, cx + side / 2, cy - side / 2, cy + side / 2, level, level + CORE_CAP_H)
        ops += _prism(proj, cap, side * 0.22).ops(style, " iso-inv")
        mark_frame = _face(proj, cap, "top", "x")
        ops.append(("path", "iso-gi iso-faint", mark_frame.rrect(0.07, 0.07, mark_frame.w - 0.07, mark_frame.h - 0.07,
                                                                  max(0.0, side * 0.22 - 0.06))))
        ops += _mark(mark_frame, item, mark_frame.w / 2, mark_frame.h / 2, side * 0.56, "iso-gi")
    else:
        mark_frame = _face(proj, surface, "top", "x")
        ops += _mark(mark_frame, item, mark_frame.w / 2, mark_frame.h / 2, min(mark_frame.w, mark_frame.h) * 0.4)
    if label:
        if item["label_face"] == "top":
            band = _subframe(top, margin, top.h - strip, top.w - margin, top.h - 0.06)
            _label_fits(band, item, band.w, warnings, "the label strip")
            ops.append(band.text("iso-txt", label, band.w / 2, band.h / 2, item["label_size"], "middle"))
        else:
            frame = _face(proj, board, item["label_face"])
            ops += _face_content(frame, {**item, "glyph": None, "icon_data": None}, warnings)
    return ops


# Object recipes --------------------------------------------------------------


def _stand_ops(proj: Projection, item: dict[str, Any], style: str) -> list[tuple[Any, ...]]:
    foot, neck = item["foot"], item["neck"]
    ops = _prism(proj, foot, min(0.1, (foot[1] - foot[0]) / 2, (foot[3] - foot[2]) / 2)).ops(style)
    plate = _face(proj, foot, "top")
    ops.append(("path", "iso-d iso-faint", plate.rrect(0.06, 0.06, plate.w - 0.06, plate.h - 0.06, 0.05)))
    return ops + _prism(proj, neck, 0.03).ops(style)


def _bezel(proj: Projection, item: dict[str, Any], style: str, side: float, chin: float
           ) -> tuple[list[tuple[Any, ...]], Frame]:
    """A panel with real thickness whose display sits recessed behind a bezel; returns the ops and the display frame."""
    body, orient = item["body"], item["orient"]
    ops = _prism(proj, body, item["radius"], _plate_axis(orient)).ops(style)
    frame = _face(proj, body, _plate_face(orient))
    side = min(side, frame.w * 0.06, frame.h * 0.08)
    chin = min(chin, frame.h * 0.12)
    batch = _Batch()
    seen = _recess(batch, frame, side, side, frame.w - side, frame.h - chin, 0.035, back="iso-t", edge="iso-d", inner=None)
    batch.add("iso-dotf", frame.circle(frame.w / 2, side / 2, min(0.03, side * 0.25)))
    ops += batch.ops(FACADE_ORDER + ("iso-dotf",))
    return ops, _subframe(frame, seen[0], seen[1], seen[2], seen[3])


def _render_dashboard_v12(proj: Projection, item: dict[str, Any], style: str, warnings: list[str]) -> list[tuple[Any, ...]]:
    """A monitor: foot and neck, a panel with thickness, a bezel around a recessed display, a slim navigation rail
    and the dashboard content."""
    ops = _stand_ops(proj, item, style) if item["stand"] else []
    panel_ops, display = _bezel(proj, item, style, 0.12, 0.18)
    ops += panel_ops
    if display.w > 2.6:
        rail = 0.36
        batch = _Batch()
        batch.add("iso-d", display.poly([(rail, 0.0), (rail, display.h)], False))
        for i in range(4):
            v = 0.42 + i * 0.3
            if v + 0.1 < display.h - 0.1:
                batch.add("iso-d" if i else "iso-g", display.rrect(rail / 2 - 0.07, v - 0.07, rail / 2 + 0.07, v + 0.07, 0.03))
        ops += batch.ops(("iso-g", "iso-d"))
        display = _subframe(display, rail, 0.0, display.w, display.h)
    return _dashboard_content(proj, item, display, ops, warnings)


def _render_screen_v12(proj: Projection, item: dict[str, Any], style: str, warnings: list[str]) -> list[tuple[Any, ...]]:
    ops = _stand_ops(proj, item, style) if item["stand"] else []
    panel_ops, display = _bezel(proj, item, style, 0.1, 0.16)
    return _screen_content(proj, item, display, ops + panel_ops, warnings)


def _render_rack_v12(proj: Projection, item: dict[str, Any], style: str, warnings: list[str]) -> list[tuple[Any, ...]]:
    """A server rack: each unit a recessed front panel with handles, drive bays and status lights; a perforated side
    and a vented top."""
    body = item["body"]
    ops = _prism(proj, body, item["radius"]).ops(style)
    units, unit_h = item["units"], item["unit_h"]
    front = _face(proj, body, item["front"])
    side = _face(proj, body, "x+" if item["front"] == "y+" else "y+")
    batch = _Batch()
    ear = max(0.12, item["radius"] + 0.05)
    lights: list[tuple[Any, ...]] = []
    for i in range(units):
        top, bottom = i * unit_h + 0.025, (i + 1) * unit_h - 0.025
        mid = (top + bottom) / 2
        _recess(batch, front, ear, top, front.w - ear, bottom, 0.035, back="iso-deck", edge="iso-d", inner=None)
        for u in (ear * 0.5, front.w - ear * 0.5):
            batch.add("iso-o", front.poly([(u, mid - unit_h * 0.26), (u, mid + unit_h * 0.26)], False))
        bays = max(1, int((front.w * 0.56 - ear) / 0.16))
        for j in range(bays):
            u = ear + 0.08 + j * 0.16
            _recess(batch, front, u, top + unit_h * 0.18, u + 0.11, bottom - unit_h * 0.18, 0.025, back="iso-hole",
                    edge="iso-d", inner=None)
        if item["leds"]:
            lights += front.circle(front.w - ear - 0.12, mid, min(0.04, unit_h * 0.12))
            batch.add("iso-dotf", front.circle(front.w - ear - 0.26, mid, min(0.04, unit_h * 0.12)))
        for k in range(1, 4):
            v = i * unit_h + unit_h * k / 4
            for c in range(int((side.w - 0.3) / 0.09)):
                batch.add("iso-perf", side.circle(0.15 + c * 0.09, v, 0.018))
    lid = _face(proj, body, "top")
    for i in range(int((lid.h - 0.3) / 0.1)):
        batch.add("iso-d iso-faint", lid.poly([(lid.w * 0.3, 0.15 + i * 0.1), (lid.w * 0.7, 0.15 + i * 0.1)], False))
    ops += batch.ops(FACADE_ORDER + ("iso-perf", "iso-dotf"))
    if lights:
        ops.append(("path", "iso-ledon", lights))
    return ops + _labelled_faces(proj, item, body, warnings)


def _tile_depth(proj: Projection, box: tuple[float, ...], radius: float) -> list[tuple[Any, ...]]:
    """A chamfer line inside the top edge and a seam where the shell meets its base, so a tile reads as a device."""
    prism = _prism(proj, box, radius)
    top = _face(proj, box, "top")
    return [("path", "iso-d iso-faint", top.rrect(0.06, 0.06, top.w - 0.06, top.h - 0.06, max(0.0, radius - 0.05))),
            ("path", "iso-d iso-faint", prism.band(box[4] + (box[5] - box[4]) * 0.3))]


def _database_ops(proj: Projection, box: tuple[float, ...], drums: int, leds: bool, style: str) -> list[tuple[Any, ...]]:
    """Stacked drums separated by recessed grooves, a rim line on each drum, a status light and a lidded top."""
    x0, x1, y0, y1, z0, z1 = box
    r = (x1 - x0) / 2
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    groove = min(0.04, (z1 - z0) * 0.06)
    drum_h = (z1 - z0 - (drums - 1) * groove) / drums
    ops: list[tuple[Any, ...]] = []
    z = z0
    angle = math.radians(45)
    for i in range(drums):
        drum = _box(cx - r, cx + r, cy - r, cy + r, z, z + drum_h)
        prism = _prism(proj, drum, r)
        ops += prism.ops(style)
        ops.append(("path", "iso-d iso-faint", prism.band(z + drum_h * 0.78)))
        if leds:
            spot = (cx + r * math.cos(angle), cy + r * math.sin(angle), z + drum_h * 0.42)
            ops.append(("path", "iso-led", _disc(proj, spot, (-math.sin(angle), math.cos(angle), 0.0), (0.0, 0.0, 1.0),
                                                 min(0.035, drum_h * 0.18))))
        z += drum_h
        if i < drums - 1:
            neck = r - min(0.06, r * 0.12)
            ops += _prism(proj, _box(cx - neck, cx + neck, cy - neck, cy + neck, z, z + groove), neck).ops(style)
            z += groove
    lid = Frame(proj, (0.0, 0.0, z1), (1, 0, 0), (0, 1, 0), 0, 0)
    ops.append(("path", "iso-d", lid.circle(cx, cy, r * 0.62)))
    ops.append(("path", "iso-dotf", lid.circle(cx, cy, r * 0.12)))
    return ops


def _sheet_frame(proj: Projection, orient: str, x: float, y: float, z: float, w: float, h: float) -> Frame:
    """The front face of one sheet, u to the right and v down, for upright or flat sheets."""
    if orient == "flat":
        return Frame(proj, (x, y, z), (1, 0, 0), (0, 1, 0), w, h)
    if orient == "x+":
        return Frame(proj, (x, y + w, z + h), (0, -1, 0), (0, 0, -1), w, h)
    return Frame(proj, (x, y, z + h), (1, 0, 0), (0, 0, -1), w, h)


def _documents_ops(proj: Projection, box: tuple[float, ...], orient: str, sheets: int, lines: int, w: float, h: float,
                   style: str) -> list[tuple[Any, ...]]:
    """Offset sheets drawn back to front; the front sheet has a folded corner and lines of text."""
    x0, x1, y0, y1, z0, _ = box
    ops: list[tuple[Any, ...]] = []
    fold = min(w, h) * 0.24
    tone = {"flat": "iso-t", "x+": "iso-r", "y+": "iso-l"}[orient]
    for k in range(sheets - 1, -1, -1):
        if orient == "flat":
            frame = _sheet_frame(proj, orient, x0 + k * 0.07, y0 + k * 0.05, z0 + (sheets - 1 - k) * DOC_T * 1.6, w, h)
        elif orient == "x+":
            frame = _sheet_frame(proj, orient, x0 + (sheets - 1 - k) * DOC_GAP + DOC_T, y0 + k * DOC_SHIFT, z0 + k * DOC_SHIFT, w, h)
        else:
            frame = _sheet_frame(proj, orient, x0 + k * DOC_SHIFT, y0 + (sheets - 1 - k) * DOC_GAP + DOC_T, z0 + k * DOC_SHIFT, w, h)
        if k:
            outline = frame.poly([(0, 0), (w, 0), (w, h), (0, h)])
            ops += [("path", tone, outline), ("path", "iso-o", outline)]
            continue
        outline = frame.poly([(0, 0), (w - fold, 0), (w, fold), (w, h), (0, h)])
        flap = frame.poly([(w - fold, 0), (w - fold, fold), (w, fold)])
        ops += [("path", "iso-t" if orient != "flat" else "iso-l", outline), ("path", "iso-o", outline),
                ("path", "iso-shade", flap), ("path", "iso-o", flap)]
        text: list[tuple[Any, ...]] = []
        if lines:
            text += frame.poly([(w * 0.14, h * 0.2), (w * 0.52, h * 0.2)], False)
            for i in range(lines):
                v = h * (0.36 + 0.5 * (i + 0.5) / lines)
                text += frame.poly([(w * 0.14, v), (w * (0.86, 0.7, 0.8, 0.56, 0.74, 0.62)[i % 6], v)], False)
            ops.append(("path", "iso-d", text))
    return ops


def _render_database(proj: Projection, item: dict[str, Any], style: str, warnings: list[str]) -> list[tuple[Any, ...]]:
    box = item["body"]
    ops = _database_ops(proj, box, item["drums"], item["leds"], style)
    if item.get("label") or item.get("glyph") or item.get("icon_data"):
        frame = _face(proj, box, "top", "x")
        ops += _face_content(frame, {**item, "glyph": None, "icon_data": None}, warnings, fit=frame.w * 0.72) \
            if item.get("label") else []
    return ops


def _render_documents(proj: Projection, item: dict[str, Any], style: str, warnings: list[str]) -> list[tuple[Any, ...]]:
    h = item["d"] if item["orient"] == "flat" else item["h"]
    ops = _documents_ops(proj, item["body"], item["orient"], item["sheets"], item["lines"], item["w"], h, style)
    if item.get("label"):
        frame = _face(proj, item["body"], "top", "x")
        ops += _face_content(frame, item, warnings)
    return ops


def _tile_model_ops(proj: Projection, item: dict[str, Any], center: tuple[float, float], style: str) -> list[tuple[Any, ...]]:
    size, z = item["model_size"], item["body"][5]
    cx, cy = center
    if item["model"] == "database":
        box = _box(cx - size / 2, cx + size / 2, cy - size / 2, cy + size / 2, z, z + size * 0.9)
        return _database_ops(proj, box, 3, True, style)
    w = size * 0.78
    h = size * 1.05 - 2 * DOC_SHIFT
    box = _box(cx - (w + 2 * DOC_SHIFT) / 2, cx + (w + 2 * DOC_SHIFT) / 2, cy - DOC_GAP, cy + DOC_GAP + DOC_T, z, z + size * 1.05)
    return _documents_ops(proj, box, "y+", 3, 3, w, h, style)


def _render_trees_v12(proj: Projection, item: dict[str, Any], style: str, warnings: list[str]) -> list[tuple[Any, ...]]:
    ops: list[tuple[Any, ...]] = []
    for tree in sorted(item["plan"], key=lambda t: (round(t["cx"] + t["cy"], 9), t["cx"])):
        ops += _tree_v12(proj, tree, item["z"], style, item.get("planter", False))
    return ops


def _shadow_ops(proj: Projection, item: dict[str, Any]) -> list[tuple[Any, ...]]:
    """A soft contact shadow on the supporting plane, cast toward +x (away from the light)."""
    kind = item["type"]
    if kind == "trees":
        size, z, height = item["size"], item["z"], item["tree_h"]
        ops: list[tuple[Any, ...]] = []
        for cx, cy in item["positions"]:
            body = _box(cx - size / 2, cx + size / 2, cy - size / 2, cy + size / 2, z, z + height)
            ops += _shadow_ops(proj, {"type": "tree", "space": body, "body": body})
        return ops
    x0, x1, y0, y1, z0, z1 = item["space"] if kind in ("trees", "tree") else item["body"]
    if kind == "building":
        z0 = item["z"]
        x0, x1, y0, y1 = item["space"][:4]
    if kind == "core":
        z1 = item["body"][5] + CORE_PACKAGE_H
    if kind in ("screen", "dashboard") and item.get("stand"):
        x0, x1, y0, y1 = item["space"][:4]
    height = z1 - z0
    reach = min(height, 2.4) * 0.38 + 0.08
    radius = 0.0
    if kind in ("cylinder", "tree"):
        radius = (x1 - x0) / 2
    elif isinstance(item.get("radius"), float) and kind not in ("card", "screen", "dashboard"):
        radius = item["radius"]
    ground = Frame(proj, (0.0, 0.0, z0), (1, 0, 0), (0, 1, 0), 0, 0)
    ops = []
    for share in (1.0, 0.6, 0.28):
        right = x1 + reach * share
        r = min(radius + 0.06, (right - x0 + 0.08) / 2, (y1 - y0 + 0.08) / 2)
        ops.append(("path", "iso-sh", ground.rrect(x0 - 0.04, y0 - 0.04, right, y1 + 0.04 + reach * share * 0.18, r)))
    return ops


def _support_of(item: dict[str, Any], solids: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The solid whose top carries an object: its body top equals the object's base and holds the footprint center."""
    x0, x1, y0, y1, z, _ = item["space"]
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for solid in solids:
        if solid is item:
            continue
        sx0, sx1, sy0, sy1, _, top = solid["body"]
        if abs(top - z) < 1e-6 and sx0 - EPS <= cx <= sx1 + EPS and sy0 - EPS <= cy <= sy1 + EPS:
            return solid
    return None


def _clip_box2(rect: tuple[float, float, float, float], bounds: tuple[float, float, float, float] | None
               ) -> tuple[float, float, float, float] | None:
    if bounds is None:
        return rect
    x0, x1 = max(rect[0], bounds[0]), min(rect[1], bounds[1])
    y0, y1 = max(rect[2], bounds[2]), min(rect[3], bounds[3])
    return (x0, x1, y0, y1) if x1 - x0 > 0.02 and y1 - y0 > 0.02 else None


def _shadow_ops_v12(proj: Projection, item: dict[str, Any], solids: list[dict[str, Any]]) -> list[tuple[Any, ...]]:
    """A dense contact band hugging the base and a soft shadow cast toward +x, both clipped to the surface that
    carries the object, so a raised object's shadow never hangs past its platform. Floating objects cast none."""
    kind = item["type"]
    z0 = item["space"][4]
    support = _support_of(item, solids) if z0 > EPS else None
    if z0 > EPS and support is None:
        return []
    bounds = None
    if support is not None:
        sx0, sx1, sy0, sy1 = support["body"][:4]
        inset = 0.04
        bounds = (sx0 + inset, sx1 - inset, sy0 + inset, sy1 - inset)
    ground = Frame(proj, (0.0, 0.0, z0), (1, 0, 0), (0, 1, 0), 0, 0)
    ops: list[tuple[Any, ...]] = []
    if kind in ("tree", "trees"):
        for tree in item["plan"]:
            cx, cy, w, h = tree["cx"], tree["cy"], tree["w"], tree["h"]
            reach = min(h, 2.0) * 0.3
            radius = w * 0.4
            sx, sy = cx + reach, cy + reach * 0.12
            if bounds is not None:
                radius = max(0.0, min(radius, (bounds[1] - bounds[0]) / 2, (bounds[3] - bounds[2]) / 2))
                sx = min(max(sx, bounds[0] + radius), bounds[1] - radius)
                sy = min(max(sy, bounds[2] + radius), bounds[3] - radius)
            if radius > 0.02:
                ops.append(("path", "iso-sh", ground.ellipse(sx, sy, radius * 1.1, radius * 0.8)))
                ops.append(("path", "iso-sh", ground.ellipse((sx + cx) / 2, (sy + cy) / 2, radius * 0.8, radius * 0.6)))
            ops.append(("path", "iso-ao", ground.circle(cx, cy, w * 0.14)))
        return ops
    if kind == "building":
        x0, x1, y0, y1 = item["space"][:4]
    elif kind in ("screen", "dashboard") and item.get("stand"):
        x0, x1, y0, y1 = item["foot"][:4]
    else:
        x0, x1, y0, y1 = item["body"][:4]
    top = item["body"][5]
    if kind == "core":
        top += CORE_PACKAGE_H
    reach = min(top - z0, 2.4) * 0.34 + 0.06
    if kind in ("screen", "dashboard"):
        reach = min(reach, 0.3)
    radius = 0.0
    if kind in ("cylinder", "database"):
        radius = (x1 - x0) / 2
    elif isinstance(item.get("radius"), float) and kind not in ("card", "screen", "dashboard"):
        radius = item["radius"]
    for share, cls, grow in ((0.0, "iso-ao", 0.07), (1.0, "iso-sh", 0.02), (0.62, "iso-sh", 0.02), (0.3, "iso-sh", 0.02)):
        rect = _clip_box2((x0 - grow, x1 + grow + reach * share, y0 - grow, y1 + grow + reach * share * 0.2), bounds)
        if rect is None:
            continue
        r = min(radius + grow, (rect[1] - rect[0]) / 2, (rect[3] - rect[2]) / 2)
        if bounds is not None and support is not None:
            r = max(r, min(float(support.get("radius") or 0.0), (rect[1] - rect[0]) / 2, (rect[3] - rect[2]) / 2))
        ops.append(("path", cls, ground.rrect(rect[0], rect[2], rect[1], rect[3], r)))
    return ops


def _scale_warnings(items: list[dict[str, Any]]) -> list[str]:
    """Relative-size checks against the scene's floor height (the median building floor, else 0.55): trees of 1 to 1.5
    floors, satellites thinner than a floor and smaller than the buildings, a focal core larger than any satellite."""
    solids = [item for item in items if item["type"] not in ("connector", "ground-grid")]
    buildings = [item for item in solids if item["type"] == "building"]
    floors = sorted(item["floor_h"] for item in buildings)
    floor = floors[len(floors) // 2] if floors else 0.55
    out: list[str] = []
    lo, hi = SCALE["floor_h"]
    for item in buildings:
        if not lo - EPS <= item["floor_h"] <= hi + EPS:
            out.append(f"{item['where']}: floor_h {_fmt(item['floor_h'])} is outside the plausible {_fmt(lo)}-{_fmt(hi)}; "
                       f"other objects are sized against it")
    t_lo, t_hi = SCALE["tree_floors"]
    for item in solids:
        if item["type"] in ("tree", "trees"):
            heights = [tree["h"] / floor for tree in item["plan"]]
            if min(heights) < t_lo - EPS or max(heights) > t_hi + EPS:
                out.append(f"{item['where']}: trees are {_fmt(min(heights), 1)}-{_fmt(max(heights), 1)} floors tall; "
                           f"plausible trees stand 1-1.5 floors ({_fmt(floor * 1.25)} grid units at floor_h {_fmt(floor)})")
    satellites = [item for item in solids if item["type"] == "tile" or (item["type"] == "card" and item["orient"] == "flat")]
    largest = max(((b["space"][1] - b["space"][0]) * (b["space"][3] - b["space"][2]) for b in buildings), default=None)
    for item in satellites:
        x0, x1, y0, y1, z0, z1 = item["body"]
        if z1 - z0 > SCALE["satellite_h_floors"] * floor + EPS:
            out.append(f"{item['where']}: it is {_fmt((z1 - z0) / floor, 1)} floors thick; a tile or card reads as a "
                       f"device at up to 1 floor ({_fmt(floor)})")
        if largest and (x1 - x0) * (y1 - y0) > SCALE["satellite_share"] * largest + EPS:
            out.append(f"{item['where']}: its footprint is {int(round((x1 - x0) * (y1 - y0) / largest * 100))}% of the "
                       f"largest building's; keep satellites under {int(SCALE['satellite_share'] * 100)}% so the "
                       f"building keeps its scale")
    for core in (item for item in solids if item["type"] == "core"):
        area = (core["body"][1] - core["body"][0]) * (core["body"][3] - core["body"][2])
        bigger = [s["id"] for s in satellites
                  if (s["body"][1] - s["body"][0]) * (s["body"][3] - s["body"][2]) > area + EPS]
        if bigger:
            out.append(f"{core['where']}: the focal core is smaller than {', '.join(repr(b) for b in bigger)}; make the "
                       f"focal object the largest")
    tallest = max((b["space"][5] - b["space"][4] for b in buildings), default=None)
    for item in solids:
        if item["type"] == "dashboard" and tallest and item["h"] > tallest + EPS:
            out.append(f"{item['where']}: the dashboard is taller than the tallest building; shrink it or let it "
                       f"stand apart as a page element")
    return out


def _sample(segs: list[tuple[Any, ...]], steps: int = 8) -> list[list[Point]]:
    """Polylines through a path's segments; arcs are sampled."""
    runs: list[list[Point]] = []
    run: list[Point] = []
    start: Point | None = None
    for seg in segs:
        op = seg[0]
        if op == "M":
            if len(run) > 1:
                runs.append(run)
            run, start = [seg[1]], seg[1]
        elif op == "L":
            run.append(seg[1])
        elif op == "E":
            for i in range(1, steps + 1):
                run.append(_arc_point(seg, seg[4] + (seg[5] - seg[4]) * i / steps))
        elif op == "Z" and start is not None:
            run.append(start)
    if len(run) > 1:
        runs.append(run)
    return runs


def _hull(points: list[Point]) -> list[Point]:
    pts = sorted(set((round(p[0], 3), round(p[1], 3)) for p in points))
    if len(pts) < 3:
        return pts

    def turn(o: Point, a: Point, b: Point) -> float:
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: list[Point] = []
    for p in pts:
        while len(lower) >= 2 and turn(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: list[Point] = []
    for p in reversed(pts):
        while len(upper) >= 2 and turn(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _separated(a: list[Point], b: list[Point]) -> bool:
    """True when two convex polygons (or a polygon and a segment) do not overlap, by separating axes."""
    for poly in (a, b):
        count = len(poly)
        for i in range(count if count > 2 else 1):
            p, q = poly[i], poly[(i + 1) % count]
            nx, ny = q[1] - p[1], p[0] - q[0]
            if abs(nx) < 1e-12 and abs(ny) < 1e-12:
                continue
            pa = [nx * x + ny * y for x, y in a]
            pb = [nx * x + ny * y for x, y in b]
            if max(pa) <= min(pb) + 1e-6 or max(pb) <= min(pa) + 1e-6:
                return True
    return False


def _shrink(poly: list[Point], amount: float) -> list[Point]:
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    out = []
    for x, y in poly:
        dx, dy = x - cx, y - cy
        length = math.hypot(dx, dy) or 1.0
        out.append((x - dx / length * amount, y - dy / length * amount))
    return out


MARK_CLASSES = ("iso-g", "iso-gf", "iso-gi", "iso-gif")


def _label_collisions(groups: dict[int, dict[str, Any]], ordered: list[int]) -> list[str]:
    """Warn when a label is crossed by a connector or covered by a mark, another label or an object painted after it."""
    labels: list[tuple[int, dict[str, Any], str, list[Point]]] = []
    lines: list[tuple[int, str, list[Point]]] = []
    covers: list[tuple[int, str, str, list[Point]]] = []
    for pos, index in enumerate(ordered):
        group = groups[index]
        item = group["item"]
        if item["type"] in ("ground-grid", "shadows"):
            continue
        for op in group["ops"]:
            if op[0] == "text":
                corners = _text_points(op)
                labels.append((pos, item, op[2], _shrink([corners[0], corners[1], corners[3], corners[2]], 0.75)))
            elif op[0] == "icon":
                covers.append((pos, item["id"], "mark", _hull(list(op[4]))))
            elif item["type"] == "connector":
                for run in _sample(op[2]):
                    lines.extend((pos, item["id"], [a, b]) for a, b in zip(run, run[1:]))
            else:
                first = op[1].split()[0]
                kind = "mark" if op[1] in MARK_CLASSES else ("object" if first in ("iso-t", "iso-l", "iso-r", "iso-silh") else None)
                if kind:
                    for run in _sample(op[2], 6):
                        if len(run) >= 3:
                            covers.append((pos, item["id"], kind, _hull(run)))
    out: list[str] = []
    seen: set[tuple[str, str]] = set()
    for pos, item, text, poly in labels:
        xs, ys = [p[0] for p in poly], [p[1] for p in poly]
        box = (min(xs), min(ys), max(xs), max(ys))

        def near(points: list[Point]) -> bool:
            return not (max(p[0] for p in points) < box[0] or min(p[0] for p in points) > box[2]
                        or max(p[1] for p in points) < box[1] or min(p[1] for p in points) > box[3])

        problems: list[str] = []
        for lpos, lid, segment in lines:
            if lpos > pos and lid not in problems and near(segment) and not _separated(poly, segment):
                problems.append(lid)
                key = (item["id"] + text, "line" + lid)
                if key not in seen:
                    seen.add(key)
                    out.append(f"{item['where']}: label {text!r} is crossed by connector {lid!r}; move the label, "
                               f"the object or the route")
        for cpos, cid, kind, hull in covers:
            if cpos > pos and cid != item["id"] and len(hull) >= 3 and near(hull) and not _separated(poly, hull):
                key = (item["id"] + text, kind + cid)
                if key not in seen:
                    seen.add(key)
                    noun = "the mark of" if kind == "mark" else "the object"
                    out.append(f"{item['where']}: label {text!r} is covered by {noun} {cid!r}; move one of them")
        for opos, other, other_text, other_poly in labels:
            if other is item and other_text == text:
                continue
            key = tuple(sorted((item["id"] + text, other["id"] + other_text)))
            if key in seen or not near(other_poly) or _separated(poly, other_poly):
                continue
            seen.add(key)
            out.append(f"{item['where']}: label {text!r} overlaps label {other_text!r} of {other['id']!r}")
    return out


def _upright_text(op: tuple[Any, ...]) -> tuple[Any, ...]:
    """The same label set level on screen: centered where the face label's text was centered."""
    _, cls, text, (a, b, c, d, e, f), size, anchor, region = op
    if anchor == "start":
        half = _text_width(text, size) / 2
        e, f = e + a * half, f + b * half
    return ("text", cls, text, (1.0, 0.0, 0.0, 1.0, e, f), size, "middle", region)


def _upright_fit(groups: dict[int, dict[str, Any]]) -> list[str]:
    """Upright labels must stay inside the face region their face label was given."""
    out: list[str] = []
    for group in groups.values():
        for op in group["ops"]:
            if op[0] != "text" or op[3][:4] != (1.0, 0.0, 0.0, 1.0):
                continue
            region = list(op[6])
            width, size = _text_width(op[2], op[4]), op[4]
            e, f = op[3][4], op[3][5]
            # The glyph body (about 0.35 em above and below the central baseline) must stay on the face.
            corners = [(e - width / 2, f - size * 0.35), (e + width / 2, f - size * 0.35),
                       (e - width / 2, f + size * 0.35), (e + width / 2, f + size * 0.35)]
            outside = False
            for x, y in corners:
                for i in range(4):
                    (ax, ay), (bx, by) = region[i], region[(i + 1) % 4]
                    cross = (bx - ax) * (y - ay) - (by - ay) * (x - ax)
                    sign = (region[1][0] - region[0][0]) * (region[2][1] - region[0][1]) -                         (region[1][1] - region[0][1]) * (region[2][0] - region[0][0])
                    if cross * (1 if sign > 0 else -1) < -1.5 * math.hypot(bx - ax, by - ay):
                        outside = True
            if outside:
                out.append(f"{group['item']['where']}: upright label {op[2]!r} runs past its face; keep face labels on "
                           f"long or narrow faces, shorten it or enlarge the object")
    return out


RENDERERS: dict[str, Callable[[Projection, dict[str, Any], str, list[str]], list[tuple[Any, ...]]]] = {
    "box": _render_box, "slab": _render_box, "stack": _render_stack, "chip": _render_chip,
    "cylinder": _render_cylinder, "building": _render_building, "card": _render_card,
    "screen": _render_screen, "tree": _render_tree, "ground-grid": _render_grid,
    "trees": _render_trees, "tile": _render_tile, "core": _render_core, "rack": _render_rack,
    "dashboard": _render_dashboard, "database": _render_database, "documents": _render_documents,
}


# --------------------------------------------------------------------------
# Connectors

SIDE_NORMAL = {"x+": (1.0, 0.0), "x-": (-1.0, 0.0), "y+": (0.0, 1.0), "y-": (0.0, -1.0)}


def _auto_side(source: tuple[float, ...], target: tuple[float, ...], towards: bool) -> str:
    sx, sy = (source[0] + source[1]) / 2, (source[2] + source[3]) / 2
    tx, ty = (target[0] + target[1]) / 2, (target[2] + target[3]) / 2
    dx, dy = (tx - sx, ty - sy) if towards else (sx - tx, sy - ty)
    if abs(dx) >= abs(dy):
        return "x+" if dx >= 0 else "x-"
    return "y+" if dy >= 0 else "y-"


def _anchor(item: dict[str, Any], side: str, offset: float, gap: float, where: str, errors: list[str]) -> tuple[float, float]:
    x0, x1, y0, y1, _, _ = item["space"]
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    half = (y1 - y0) / 2 if side in ("x+", "x-") else (x1 - x0) / 2
    if abs(offset) >= half - EPS:
        errors.append(f"{where}: offset {_fmt(offset)} leaves the {side} side of {item['id']!r} (half length {_fmt(half)})")
    if side == "x+":
        return (x1 + gap, cy + offset)
    if side == "x-":
        return (x0 - gap, cy + offset)
    if side == "y+":
        return (cx + offset, y1 + gap)
    return (cx + offset, y0 - gap)


def _straighten(source: tuple[float, ...], target: tuple[float, ...], direction: tuple[float, float],
                start: tuple[float, float], end: tuple[float, float]) -> tuple[tuple[float, float], tuple[float, float]]:
    """Share one lateral coordinate when two facing sides overlap enough, so the link runs straight."""
    axis = 1 if direction[0] else 0
    margins = [min(0.25, (box[2 * axis + 1] - box[2 * axis]) * 0.25) for box in (source, target)]
    lo = max(source[2 * axis] + margins[0], target[2 * axis] + margins[1])
    hi = min(source[2 * axis + 1] - margins[0], target[2 * axis + 1] - margins[1])
    if hi < lo:
        return start, end
    narrow = min((source, target), key=lambda box: box[2 * axis + 1] - box[2 * axis])
    shared = min(max((narrow[2 * axis] + narrow[2 * axis + 1]) / 2, lo), hi)
    if axis == 1:
        return (start[0], shared), (end[0], shared)
    return (shared, start[1]), (shared, end[1])


def _route_points(start: tuple[float, float], heading: str, via: list[tuple[float, float]],
                  end: tuple[float, float], arrive: str) -> list[tuple[float, float]]:
    points = [start]
    for target in via:
        cur = points[-1]
        if abs(cur[0] - target[0]) < EPS or abs(cur[1] - target[1]) < EPS:
            heading = "x" if abs(cur[1] - target[1]) < EPS else "y"
            points.append(target)
        else:
            corner = (target[0], cur[1]) if heading == "x" else (cur[0], target[1])
            points += [corner, target]
            heading = "y" if heading == "x" else "x"
    cur = points[-1]
    if arrive == "x":
        if abs(cur[1] - end[1]) < EPS:
            points.append(end)
        elif heading == "x":
            mid = (cur[0] + end[0]) / 2
            points += [(mid, cur[1]), (mid, end[1]), end]
        else:
            points += [(cur[0], end[1]), end]
    else:
        if abs(cur[0] - end[0]) < EPS:
            points.append(end)
        elif heading == "y":
            mid = (cur[1] + end[1]) / 2
            points += [(cur[0], mid), (end[0], mid), end]
        else:
            points += [(end[0], cur[1]), end]
    clean = [points[0]]
    for point in points[1:]:
        if abs(point[0] - clean[-1][0]) < EPS and abs(point[1] - clean[-1][1]) < EPS:
            continue
        if len(clean) >= 2:
            a, b = clean[-2], clean[-1]
            if (abs(a[0] - b[0]) < EPS and abs(b[0] - point[0]) < EPS) or (abs(a[1] - b[1]) < EPS and abs(b[1] - point[1]) < EPS):
                if (b[0] - a[0]) * (point[0] - b[0]) + (b[1] - a[1]) * (point[1] - b[1]) >= 0:
                    clean[-1] = point
                    continue
        clean.append(point)
    return clean


def _direction(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    return (dx / length, dy / length)


def _connector(proj: Projection, item: dict[str, Any], by_id: dict[str, dict[str, Any]],
               solids: list[dict[str, Any]], errors: list[str]) -> dict[str, Any] | None:
    where = item["where"]
    source, target = by_id[item["from"]], by_id[item["to"]]
    if source is target:
        errors.append(f"{where}: a connector needs two different objects")
        return None
    level = item["z"]
    if level is None:
        level = source["space"][4]
        if abs(target["space"][4] - level) > EPS:
            errors.append(f"{where}: {item['from']!r} stands at z={_fmt(level)} and {item['to']!r} at "
                          f"z={_fmt(target['space'][4])}; set an explicit z inside both objects' heights")
            return None
    for end_item in (source, target):
        if not end_item["space"][4] - EPS <= level < end_item["space"][5] - EPS:
            errors.append(f"{where}: z={_fmt(level)} is outside the height of {end_item['id']!r}")
            return None
    from_side = item["from_side"] or _auto_side(source["space"], target["space"], True)
    to_side = item["to_side"] or _auto_side(target["space"], source["space"], True)
    before = len(errors)
    start = _anchor(source, from_side, item["from_offset"], item["gap"], where, errors)
    end = _anchor(target, to_side, item["to_offset"], item["gap"], where, errors)
    if len(errors) > before:
        return None
    exit_dir = SIDE_NORMAL[from_side]
    arrive_dir = (-SIDE_NORMAL[to_side][0], -SIDE_NORMAL[to_side][1])
    if (not item["via"] and exit_dir == arrive_dir and not {"from_offset", "to_offset"} & item["given"]):
        start, end = _straighten(source["space"], target["space"], exit_dir, start, end)
    points = _route_points(start, "x" if exit_dir[0] else "y", item["via"], end, "x" if arrive_dir[0] else "y")
    if len(points) < 2:
        errors.append(f"{where}: the anchors of {item['from']!r} and {item['to']!r} coincide; move the objects apart")
        return None
    first, last = _direction(points[0], points[1]), _direction(points[-2], points[-1])
    if first[0] * exit_dir[0] + first[1] * exit_dir[1] < 0.5:
        errors.append(f"{where}: the route leaves {item['from']!r} backwards through its {from_side} side; "
                      f"choose another from_side or add via points")
        return None
    if last[0] * arrive_dir[0] + last[1] * arrive_dir[1] < 0.5:
        errors.append(f"{where}: the route enters {item['to']!r} from behind its {to_side} side; "
                      f"choose another to_side or add via points")
        return None
    for a, b in zip(points, points[1:]):
        lo_x, hi_x, lo_y, hi_y = min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1])
        for solid in solids:
            sx0, sx1, sy0, sy1, sz0, sz1 = solid["space"]
            if not (sz0 - EPS <= level < sz1 - EPS):
                continue
            if hi_x - lo_x < EPS:
                crosses = sx0 + EPS < lo_x < sx1 - EPS and min(hi_y, sy1) - max(lo_y, sy0) > EPS
            else:
                crosses = sy0 + EPS < lo_y < sy1 - EPS and min(hi_x, sx1) - max(lo_x, sx0) > EPS
            if crosses:
                errors.append(f"{where}: the route passes through {solid['id']!r}; add via points or choose other sides")
                return None
    tail = ARROW_LENGTH if item["end"] == "arrow" else 0.0
    if math.dist(points[-2], points[-1]) < tail + 0.05:
        errors.append(f"{where}: the last leg into {item['to']!r} is too short for an arrow; move the objects apart or use end 'dot'")
        return None
    segs: list[tuple[Any, ...]] = [("M", proj(points[0][0], points[0][1], level))]
    count = len(points)
    for i in range(1, count - 1):
        prev, corner, nxt = points[i - 1], points[i], points[i + 1]
        din, dout = _direction(prev, corner), _direction(corner, nxt)
        len_in, len_out = math.dist(prev, corner), math.dist(corner, nxt)
        avail_in = len_in if i == 1 else len_in / 2
        avail_out = (len_out - tail - 0.05) if i == count - 2 else len_out / 2
        radius = max(0.0, min(item["radius"], avail_in, avail_out))
        if radius > 1e-6:
            s = (corner[0] - radius * din[0], corner[1] - radius * din[1])
            center = (s[0] + radius * dout[0], s[1] + radius * dout[1])
            a0 = math.atan2(-dout[1], -dout[0])
            delta = (math.atan2(din[1], din[0]) - a0 + math.pi) % (2 * math.pi) - math.pi
            segs.append(("L", proj(s[0], s[1], level)))
            segs.append(("E", proj(center[0], center[1], level), proj.vec(radius, 0, 0), proj.vec(0, radius, 0), a0, a0 + delta))
        else:
            segs.append(("L", proj(corner[0], corner[1], level)))
    final = points[-1]
    stop = (final[0] - tail * arrive_dir[0], final[1] - tail * arrive_dir[1])
    segs.append(("L", proj(stop[0], stop[1], level)))
    ground = Frame(proj, (0, 0, level), (1, 0, 0), (0, 1, 0), 0, 0)
    markers: list[tuple[Any, ...]] = []
    if item["start"] == "dot":
        markers.append(("path", "iso-end", ground.circle(points[0][0], points[0][1], END_DOT)))
    if item["end"] == "dot":
        markers.append(("path", "iso-end", ground.circle(final[0], final[1], END_DOT)))
    elif item["end"] == "arrow":
        px, py = -arrive_dir[1], arrive_dir[0]
        wing = ARROW_HALF_WIDTH
        markers.append(("path", "iso-end iso-arrow", ground.poly([
            final, (stop[0] + px * wing, stop[1] + py * wing), (stop[0] - px * wing, stop[1] - py * wing)])))
    boxes = []
    for a, b in zip(points, points[1:]):
        boxes.append(_box(min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1]), level, level))
    length = sum(math.dist(a, b) for a, b in zip(points, points[1:]))
    return {"segs": segs, "markers": markers, "boxes": boxes, "level": level, "points": points,
            "length": length, "from_side": from_side, "to_side": to_side}


def _footprint_radius(item: dict[str, Any]) -> float:
    """Corner radius of a solid's drawn footprint (a cylinder is fully round), 0 for square or irregular ones."""
    kind = item["type"]
    x0, x1 = item["space"][:2]
    if kind == "cylinder":
        return (x1 - x0) / 2
    if kind in ("box", "slab", "tile", "core", "rack") or (kind == "card" and item["orient"] == "flat") \
            or (kind == "chip" and item["pins"] == 0):
        return item["radius"]
    return 0.0


def _ray_interval(point: tuple[float, ...], view: tuple[float, float, float], box: tuple[float, ...],
                  circle: tuple[float, float, float] | None = None) -> tuple[float, float]:
    """Parameter interval in which the view ray from point lies inside a box, or inside a vertical cylinder within it."""
    enter, leave = -math.inf, math.inf
    for axis in range(3):
        a = (box[2 * axis] - point[axis]) / view[axis]
        b = (box[2 * axis + 1] - point[axis]) / view[axis]
        enter, leave = max(enter, min(a, b)), min(leave, max(a, b))
    if circle is not None and enter < leave:
        cx, cy, r = circle
        dx, dy = point[0] - cx, point[1] - cy
        qa = view[0] ** 2 + view[1] ** 2
        qb = 2 * (dx * view[0] + dy * view[1])
        disc = qb * qb - 4 * qa * (dx * dx + dy * dy - r * r)
        if disc <= 0:
            return (0.0, 0.0)
        root = math.sqrt(disc)
        enter, leave = max(enter, (-qb - root) / (2 * qa)), min(leave, (-qb + root) / (2 * qa))
    return (enter, leave)


def _hidden_by(point: tuple[float, ...], solids: list[dict[str, Any]],
               view: tuple[float, float, float]) -> str | None:
    """The id of the first solid that the ray from point toward the viewer passes through, if any.

    A solid counts as its bounding volume with the drawn corner radius: a rounded-rectangle extrusion, or a
    vertical cylinder for cylinders.
    """
    for solid in solids:
        x0, x1, y0, y1, z0, z1 = solid["body"] if solid.get("column") else solid["space"]
        r = min(_footprint_radius(solid), (x1 - x0) / 2, (y1 - y0) / 2)
        parts: list[tuple[tuple[float, ...], tuple[float, float, float] | None]] = [((x0, x1, y0, y1, z0, z1), None)]
        if solid.get("column"):
            parts.append((solid["column"], None))
        if r > EPS:
            parts = [((x0 + r, x1 - r, y0, y1, z0, z1), None), ((x0, x1, y0 + r, y1 - r, z0, z1), None)] + parts[1:]
            for cx in (x0 + r, x1 - r):
                for cy in (y0 + r, y1 - r):
                    parts.append(((cx - r, cx + r, cy - r, cy + r, z0, z1), (cx, cy, r)))
        for box, circle in parts:
            enter, leave = _ray_interval(point, view, box, circle)
            if max(enter, 0.0) < leave - 1e-6:
                return solid["id"]
    return None


def _surface_inset(item: dict[str, Any], side: str, offset: float) -> float:
    """How far the drawn surface sits inside the bounding side at a lateral offset (rounded corners, cylinders)."""
    x0, x1, y0, y1 = item["space"][:4]
    half = (y1 - y0) / 2 if side in ("x+", "x-") else (x1 - x0) / 2
    r = _footprint_radius(item)
    reach = abs(offset) - (half - r)
    if r <= 0 or reach <= 0:
        return 0.0
    reach = min(reach, r)
    return r - math.sqrt(max(0.0, r * r - reach * reach))


def _anchor_v11(item: dict[str, Any], side: str, offset: float, gap: float) -> tuple[float, float] | str:
    """The point ``gap`` outside the bounding side at ``offset``; ``_onto_surface`` later moves it onto the drawn surface."""
    x0, x1, y0, y1, _, _ = item["space"]
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    half = (y1 - y0) / 2 if side in ("x+", "x-") else (x1 - x0) / 2
    if abs(offset) >= half - EPS:
        return f"offset {_fmt(offset)} leaves the {side} side of {item['id']!r} (half length {_fmt(half)})"
    if side == "x+":
        return (x1 + gap, cy + offset)
    if side == "x-":
        return (x0 - gap, cy + offset)
    if side == "y+":
        return (cx + offset, y1 + gap)
    return (cx + offset, y0 - gap)


def _onto_surface(item: dict[str, Any], side: str, point: tuple[float, float]) -> tuple[float, float]:
    """Move an anchor inward by the distance between the bounding side and the rounded surface behind it."""
    x0, x1, y0, y1 = item["space"][:4]
    lateral = point[1] - (y0 + y1) / 2 if side in ("x+", "x-") else point[0] - (x0 + x1) / 2
    inset = _surface_inset(item, side, lateral)
    nx, ny = SIDE_NORMAL[side]
    return (point[0] - nx * inset, point[1] - ny * inset)


def _side_candidates(explicit: str | None, own: tuple[float, ...], other: tuple[float, ...]) -> list[str]:
    if explicit:
        return [explicit]
    facing = _auto_side(own, other, True)
    return [facing] + [side for side in ("x+", "y+", "x-", "y-") if side != facing]


def _dir3(a: tuple[float, ...], b: tuple[float, ...]) -> tuple[float, float, float]:
    d = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    length = math.sqrt(d[0] ** 2 + d[1] ** 2 + d[2] ** 2)
    return (d[0] / length, d[1] / length, d[2] / length)


def _add3(a: tuple[float, ...], b: tuple[float, ...], k: float = 1.0) -> tuple[float, float, float]:
    return (a[0] + k * b[0], a[1] + k * b[1], a[2] + k * b[2])


def _disc(proj: Projection, center: tuple[float, ...], a: tuple[float, float, float], b: tuple[float, float, float],
          radius: float) -> list[tuple[Any, ...]]:
    return [("M", proj(*_add3(center, a, radius))),
            ("E", proj(*center), proj.vec(*(radius * c for c in a)), proj.vec(*(radius * c for c in b)), 0.0, 2 * math.pi),
            ("Z",)]


def _try_route(item: dict[str, Any], source: dict[str, Any], target: dict[str, Any], solids: list[dict[str, Any]],
               view: tuple[float, float, float], from_side: str, to_side: str, template: int, level: float,
               from_z: float, to_z: float) -> dict[str, Any] | str:
    """One candidate route; a dict when it is valid, otherwise the reason it is not."""
    start = _anchor_v11(source, from_side, item["from_offset"], item["gap"])
    end = _anchor_v11(target, to_side, item["to_offset"], item["gap"])
    for anchor in (start, end):
        if isinstance(anchor, str):
            return anchor
    exit_dir = SIDE_NORMAL[from_side]
    arrive_dir = (-SIDE_NORMAL[to_side][0], -SIDE_NORMAL[to_side][1])
    via = list(item["via"])
    if template == 0 and not via and exit_dir == arrive_dir and not {"from_offset", "to_offset"} & item["given"]:
        start, end = _straighten(source["space"], target["space"], exit_dir, start, end)
    if template >= 1:
        via = via + [(end[0] - arrive_dir[0] * LANE, end[1] - arrive_dir[1] * LANE)]
    if template == 2:
        via = [(start[0] + exit_dir[0] * LANE, start[1] + exit_dir[1] * LANE)] + via
    points = _route_points(start, "x" if exit_dir[0] else "y", via, end, "x" if arrive_dir[0] else "y")
    if len(points) < 2:
        return f"the anchors of {item['from']!r} and {item['to']!r} coincide; move the objects apart"
    plane_points = points
    points = [_onto_surface(source, from_side, points[0])] + points[1:-1] + [_onto_surface(target, to_side, points[-1])]
    start, end = points[0], points[-1]
    first, last = _direction(points[0], points[1]), _direction(points[-2], points[-1])
    if first[0] * exit_dir[0] + first[1] * exit_dir[1] < 0.5:
        return f"the route leaves {item['from']!r} backwards through its {from_side} side"
    if last[0] * arrive_dir[0] + last[1] * arrive_dir[1] < 0.5:
        return f"the route enters {item['to']!r} from behind its {to_side} side"
    for a, b in zip(plane_points, plane_points[1:]):
        lo_x, hi_x, lo_y, hi_y = min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1])
        for solid in solids:
            sx0, sx1, sy0, sy1, sz0, sz1 = solid["space"]
            if not (sz0 - EPS <= level < sz1 - EPS):
                continue
            if hi_x - lo_x < EPS:
                crosses = sx0 + EPS < lo_x < sx1 - EPS and min(hi_y, sy1) - max(lo_y, sy0) > EPS
            else:
                crosses = sy0 + EPS < lo_y < sy1 - EPS and min(hi_x, sx1) - max(lo_x, sx0) > EPS
            if crosses:
                return f"the route passes through {solid['id']!r}"
    path: list[tuple[float, float, float]] = []
    if abs(from_z - level) > EPS:
        path.append((start[0], start[1], from_z))
    path += [(p[0], p[1], level) for p in points]
    if abs(to_z - level) > EPS:
        path.append((end[0], end[1], to_z))
    for (x, y), za, zb, name in ((plane_points[0], from_z, level, item["from"]), (plane_points[-1], level, to_z, item["to"])):
        lo, hi = min(za, zb), max(za, zb)
        if hi - lo < EPS:
            continue
        for solid in solids:
            sx0, sx1, sy0, sy1, sz0, sz1 = solid["space"]
            if sx0 + EPS < x < sx1 - EPS and sy0 + EPS < y < sy1 - EPS and min(hi, sz1) - max(lo, sz0) > EPS:
                return f"the riser at {name!r} passes through {solid['id']!r}"
    tail = ARROW_LENGTH if item["end"] == "arrow" else 0.0
    if math.dist(path[-2], path[-1]) < tail + 0.05:
        return f"the last leg into {item['to']!r} is too short for an arrow"
    markers = _marker_points(item, path, to_side, from_side)
    for which, points3 in markers:
        for point in points3:
            blocker = _hidden_by(point, solids, view)
            if blocker:
                side = to_side if which == "end" else from_side
                return f"the {which} marker at the {side} side of {(item['to'] if which == 'end' else item['from'])!r} " \
                       f"is hidden behind {blocker!r}"
    return {"path": path, "from_side": from_side, "to_side": to_side, "level": level}


def _face_tangent(side: str) -> tuple[float, float, float]:
    return (0.0, 1.0, 0.0) if side in ("x+", "x-") else (1.0, 0.0, 0.0)


def _arrow_geometry(path: list[tuple[float, float, float]], side: str) -> tuple[tuple[float, ...], tuple[float, ...], tuple[float, ...]]:
    final = path[-1]
    direction = _dir3(path[-2], final)
    stop = _add3(final, direction, -ARROW_LENGTH)
    if abs(direction[2]) > 0.5:
        wing = _face_tangent(side)
    else:
        wing = (-direction[1], direction[0], 0.0)
    return final, _add3(stop, wing, ARROW_HALF_WIDTH), _add3(stop, wing, -ARROW_HALF_WIDTH)


def _marker_points(item: dict[str, Any], path: list[tuple[float, float, float]], to_side: str,
                   from_side: str) -> list[tuple[str, list[tuple[float, ...]]]]:
    out: list[tuple[str, list[tuple[float, ...]]]] = []
    if item["end"] == "arrow":
        out.append(("end", list(_arrow_geometry(path, to_side))))
    elif item["end"] in ("dot", "port"):
        out.append(("end", [path[-1]]))
    if item["start"] in ("dot", "port"):
        out.append(("start", [path[0]]))
    return out


def _marker_plane(path: list[tuple[float, ...]], at_end: bool, side: str) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    a, b = (path[-2], path[-1]) if at_end else (path[0], path[1])
    if abs(a[2] - b[2]) > EPS:
        return _face_tangent(side), (0.0, 0.0, 1.0)
    return (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)


def _connector_v11(proj: Projection, item: dict[str, Any], by_id: dict[str, dict[str, Any]],
                   solids: list[dict[str, Any]], errors: list[str]) -> dict[str, Any] | None:
    where = item["where"]
    source, target = by_id[item["from"]], by_id[item["to"]]
    if source is target:
        errors.append(f"{where}: a connector needs two different objects")
        return None
    ground = item["route"] == "ground"
    level = item["z"]
    if level is None:
        if ground:
            level = 0.0
        else:
            level = source["space"][4]
            if abs(target["space"][4] - level) > EPS:
                errors.append(f"{where}: {item['from']!r} stands at z={_fmt(level)} and {item['to']!r} at "
                              f"z={_fmt(target['space'][4])}; set an explicit z, from_z and to_z, or route 'ground'")
                return None
    from_z = item["from_z"] if item["from_z"] is not None else (source["space"][4] if ground else level)
    to_z = item["to_z"] if item["to_z"] is not None else (target["space"][4] if ground else level)
    for end_item, height, name in ((source, from_z, "from_z"), (target, to_z, "to_z")):
        if not end_item["space"][4] - EPS <= height < end_item["space"][5] - EPS:
            label = name if item[name] is not None else "z"
            errors.append(f"{where}: {label}={_fmt(height)} is outside the height of {end_item['id']!r}")
            return None
    froms = _side_candidates(item["from_side"], source["space"], target["space"])
    tos = _side_candidates(item["to_side"], target["space"], source["space"])
    pairs = sorted(((f, t) for f in froms for t in tos), key=lambda p: (froms.index(p[0]) + tos.index(p[1]), tos.index(p[1])))
    templates = (0,) if item["via"] else (0, 1, 2)
    first_reason = None
    found = None
    for from_side, to_side in pairs:
        for template in templates:
            result = _try_route(item, source, target, solids, proj.view, from_side, to_side, template, level, from_z, to_z)
            if isinstance(result, dict):
                found = result
                break
            if first_reason is None:
                first_reason = result
        if found:
            break
    if found is None:
        explicit = item["from_side"] and item["to_side"]
        hint = ("choose other sides, add via points or set end 'none'" if explicit
                else "no side pair routes cleanly; add via points or move the objects")
        errors.append(f"{where}: {first_reason}; {hint}")
        return None
    path = found["path"]
    tail = ARROW_LENGTH if item["end"] == "arrow" else 0.0
    segs: list[tuple[Any, ...]] = [("M", proj(*path[0]))]
    count = len(path)
    for i in range(1, count - 1):
        prev, corner, nxt = path[i - 1], path[i], path[i + 1]
        din, dout = _dir3(prev, corner), _dir3(corner, nxt)
        len_in, len_out = math.dist(prev, corner), math.dist(corner, nxt)
        avail_in = len_in if i == 1 else len_in / 2
        avail_out = (len_out - tail - 0.05) if i == count - 2 else len_out / 2
        radius = max(0.0, min(item["radius"], avail_in, avail_out))
        if radius > 1e-6:
            arc_start = _add3(corner, din, -radius)
            center = _add3(arc_start, dout, radius)
            segs.append(("L", proj(*arc_start)))
            segs.append(("E", proj(*center), proj.vec(*(-radius * c for c in dout)), proj.vec(*(radius * c for c in din)),
                         0.0, math.pi / 2))
        else:
            segs.append(("L", proj(*corner)))
    final = path[-1]
    stop = _add3(final, _dir3(path[-2], final), -tail)
    segs.append(("L", proj(*stop)))
    markers: list[tuple[Any, ...]] = []
    accent_end = "iso-end"
    for which, kind, side in (("start", item["start"], found["from_side"]), ("end", item["end"], found["to_side"])):
        at_end = which == "end"
        center = path[-1] if at_end else path[0]
        a, b = _marker_plane(path, at_end, side)
        if kind == "dot":
            markers.append(("path", accent_end, _disc(proj, center, a, b, END_DOT)))
        elif kind == "port":
            if item.get("v12"):
                owner = target if at_end else source
                hw, hh = 0.15, 0.1
                if abs(b[2]) > 0.5:
                    lo, hi = owner["space"][4], owner["space"][5]
                    hh = min(hh, center[2] - lo - 0.03, hi - center[2] - 0.03)
                if hh > 0.04:
                    origin = _add3(_add3(center, a, -hw), b, hh)
                    sock = Frame(proj, origin, a, (-b[0], -b[1], -b[2]), 2 * hw, 2 * hh)
                    markers.append(("path", "iso-sock", sock.rrect(0, 0, 2 * hw, 2 * hh, min(0.04, hh * 0.5))))
            markers.append(("path", "iso-port", _disc(proj, center, a, b, PORT_DOT)))
            markers.append(("path", "iso-portc", _disc(proj, center, a, b, PORT_DOT * 0.42)))
        elif kind == "arrow":
            tip, left, right = _arrow_geometry(path, side)
            markers.append(("path", "iso-end iso-arrow", [("M", proj(*tip)), ("L", proj(*left)), ("L", proj(*right)), ("Z",)]))
    if item["joints"]:
        for vx, vy in item["via"]:
            markers.append(("path", "iso-joint", _disc(proj, (vx, vy, level), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), END_DOT * 0.8)))
    boxes = []
    for a, b in zip(path, path[1:]):
        boxes.append(_box(min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1]), min(a[2], b[2]), max(a[2], b[2])))
    length = sum(math.dist(a, b) for a, b in zip(path, path[1:]))
    return {"segs": segs, "markers": markers, "boxes": boxes, "level": level, "points": path, "length": length,
            "from_side": found["from_side"], "to_side": found["to_side"]}


# --------------------------------------------------------------------------
# Depth order


def _ranges(box: tuple[float, ...], view: tuple[float, float, float], margin: float) -> tuple[tuple[float, float], ...]:
    x0, x1, y0, y1, z0, z1 = box
    vx, vy, vz = view
    raw = ((x0 - y1, x1 - y0), (vz * x0 - vx * z1, vz * x1 - vx * z0), (vz * y0 - vy * z1, vz * y1 - vy * z0))
    return tuple((lo - margin, hi + margin) for lo, hi in raw)


def _screen_overlap(a: tuple[tuple[float, float], ...], b: tuple[tuple[float, float], ...]) -> bool:
    return all(ra[0] < rb[1] - EPS and rb[0] < ra[1] - EPS for ra, rb in zip(a, b))


def _behind(a: tuple[float, ...], b: tuple[float, ...]) -> bool:
    """True when box a lies wholly behind box b along some axis (the viewer looks from +x, +y, +z)."""
    return a[1] <= b[0] + EPS or a[3] <= b[2] + EPS or a[5] <= b[4] + EPS


def _relation(a: tuple[float, ...], b: tuple[float, ...], view: tuple[float, float, float]) -> int:
    """-1 when a paints before b, 1 when after, 0 when their projections do not overlap."""
    if not _screen_overlap(_ranges(a, view, SORT_MARGIN), _ranges(b, view, SORT_MARGIN)):
        return 0
    back, front = _behind(a, b), _behind(b, a)
    if back and not front:
        return -1
    if front and not back:
        return 1
    return 0


def depth_order(nodes: list[dict[str, Any]], view: tuple[float, float, float]) -> list[dict[str, Any]]:
    """Topologically sort nodes ({id, boxes, key, connector, level}) back to front; refuse cycles."""
    count = len(nodes)
    after: list[set[int]] = [set() for _ in range(count)]
    errors: list[str] = []
    for i in range(count):
        for j in range(i + 1, count):
            a, b = nodes[i], nodes[j]
            if a["connector"] and b["connector"] and abs(a["level"] - b["level"]) < EPS:
                continue
            relations = {_relation(ba, bb, view) for ba in a["boxes"] for bb in b["boxes"]} - {0}
            if relations == {-1}:
                after[i].add(j)
            elif relations == {1}:
                after[j].add(i)
            elif relations == {-1, 1}:
                connector, other = (a, b) if a["connector"] else (b, a)
                errors.append(f"connector {connector['id']!r} passes both behind and in front of {other['id']!r}; "
                              f"route it on one side or split it into two connectors")
    if errors:
        raise SceneError(errors)
    indegree = [0] * count
    for i in range(count):
        for j in after[i]:
            indegree[j] += 1
    heap = [(nodes[i]["key"], i) for i in range(count) if indegree[i] == 0]
    heapq.heapify(heap)
    ordered: list[dict[str, Any]] = []
    while heap:
        _, i = heapq.heappop(heap)
        ordered.append(nodes[i])
        for j in sorted(after[i]):
            indegree[j] -= 1
            if indegree[j] == 0:
                heapq.heappush(heap, (nodes[j]["key"], j))
    if len(ordered) != count:
        stuck = sorted(nodes[i]["id"] for i in range(count) if indegree[i] > 0)
        raise SceneError([f"cyclic occlusion among {', '.join(repr(s) for s in stuck)}; no back-to-front order "
                          f"exists, so split one of these objects or move it"])
    return ordered


# --------------------------------------------------------------------------
# SVG assembly


def _xml(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;").replace("'", "&#39;"))


def _style(style: str, colors: dict[str, str], outline: float, detail: float, extended: bool = False,
           v12: bool = False) -> str:
    def var(name: str) -> str:
        return f"var(--iso-{name},{colors[name]})"

    def tint(name: str, share: int) -> str:
        return f"color-mix(in srgb,{var('accent')} {share}%,{var(name)})"

    def mix(first: str, share: int, second: str) -> str:
        return f"color-mix(in srgb,{var(first)} {share}%,{var(second)})"

    s = ".iso-scene "
    rules = [
        f".iso-scene{{font-family:var(--iso-font,ui-sans-serif,system-ui,-apple-system,'Segoe UI',Roboto,sans-serif)}}",
        f"{s}.iso-t{{fill:{var('top')}}}",
        f"{s}.iso-l{{fill:{var('left')}}}",
        f"{s}.iso-r{{fill:{var('right')}}}",
        f"{s}.iso-accent .iso-t{{fill:{var('top')};fill:{tint('top', 10)}}}",
        f"{s}.iso-accent .iso-l{{fill:{var('left')};fill:{tint('left', 16)}}}",
        f"{s}.iso-accent .iso-r{{fill:{var('right')};fill:{tint('right', 22)}}}",
        f"{s}.iso-o,{s}.iso-d,{s}.iso-g,{s}.iso-a,{s}.iso-grid,{s}.iso-pin,{s}.iso-path,{s}.iso-end"
        f"{{stroke-linecap:round;stroke-linejoin:round;vector-effect:non-scaling-stroke}}",
        f"{s}.iso-o{{fill:none;stroke:{var('stroke')};stroke-width:{_fmt(outline)}}}",
        f"{s}.iso-pin{{fill:none;stroke:{var('stroke')};stroke-width:{_fmt(outline)}}}",
        f"{s}.iso-d{{fill:none;stroke:{var('detail')};stroke-width:{_fmt(detail)}}}",
        f"{s}.iso-a{{fill:none;stroke:{var('accent')};stroke-width:{_fmt(outline)}}}",
        f"{s}.iso-af{{fill:{var('accent')}}}",
        f"{s}.iso-win{{fill:{var('detail')};fill-opacity:.32}}",
        f"{s}.iso-accent .iso-win{{fill:{var('accent')};fill-opacity:.55}}",
        f"{s}.iso-g{{fill:none;stroke:{var('text')};stroke-width:{_fmt(outline)}}}",
        f"{s}.iso-gf{{fill:{var('text')}}}",
        f"{s}.iso-accent .iso-g{{stroke:{var('accent')}}}",
        f"{s}.iso-accent .iso-gf{{fill:{var('accent')}}}",
        f"{s}.iso-txt{{fill:{var('text')};font-weight:600;letter-spacing:.01em}}",
        f"{s}.iso-grid{{fill:none;stroke:{var('grid')};stroke-width:{_fmt(detail)}}}",
        f"{s}.iso-gdot{{fill:{var('grid')}}}",
        f"{s}.iso-path{{fill:none;stroke:{var('detail')};stroke-width:{_fmt(outline)}}}",
        f"{s}.iso-end{{fill:{var('detail')};stroke:{var('detail')};stroke-width:{_fmt(detail)}}}",
        f"{s}.iso-link.iso-accent .iso-path{{stroke:{var('accent')}}}",
        f"{s}.iso-link.iso-accent .iso-end{{fill:{var('accent')};stroke:{var('accent')}}}",
    ]
    rules += [f"{s}.iso-f{level}{{opacity:{_fmt(level / 10, 1)}}}" for level in range(1, 10)]
    if style == "solid":
        rules.append(f"{s}.iso-die.iso-t{{fill:{var('accent')}}}")
    if not extended:
        return "".join(rules)
    hair = _fmt(detail)
    if style == "technical":
        rules += [
            f"{s}.iso-txt{{font-weight:500;letter-spacing:.005em}}",
            f"{s}.iso-win{{fill:{var('detail')};fill-opacity:.16;stroke:{var('detail')};stroke-width:{hair};"
            f"vector-effect:non-scaling-stroke}}",
            f"{s}.iso-end{{fill:{var('stroke')};stroke:{var('stroke')}}}",
            f"{s}.iso-path{{stroke:{var('stroke')}}}",
            f"{s}.iso-accent .iso-t{{fill:{tint('top', 7)}}}",
            f"{s}.iso-accent .iso-l{{fill:{tint('left', 11)}}}",
            f"{s}.iso-accent .iso-r{{fill:{tint('right', 15)}}}",
        ]
    rules += [
        f"{s}.iso-mull,{s}.iso-guide,{s}.iso-cl,{s}.iso-port,{s}.iso-node,{s}.iso-slot,{s}.iso-gi"
        f"{{stroke-linecap:round;stroke-linejoin:round;vector-effect:non-scaling-stroke}}",
        f"{s}.iso-glass{{fill:{var('detail')};fill-opacity:.14}}",
        f"{s}.iso-mull{{fill:none;stroke:{var('detail')};stroke-width:{hair}}}",
        f"{s}.iso-faint{{stroke-opacity:.55}}",
        f"{s}.iso-soft{{fill-opacity:.7}}",
        f"{s}.iso-guide{{fill:none;stroke:{var('detail')};stroke-width:{hair};stroke-dasharray:2 3}}",
        f"{s}.iso-node{{fill:{var('top')};stroke:{var('detail')};stroke-width:{hair}}}",
        f"{s}.iso-slot{{fill:{var('right')};stroke:{var('detail')};stroke-width:{hair}}}",
        f"{s}.iso-dotf{{fill:{var('detail')}}}",
        f"{s}.iso-ledon{{fill:{var('stroke')}}}",
        f"{s}.iso-accent .iso-ledon{{fill:{var('accent')}}}",
        f"{s}.iso-sh{{fill:{var('shadow')};fill-opacity:.045}}",
        f"{s}.iso-inv.iso-t{{fill:{mix('stroke', 84, 'top')}}}",
        f"{s}.iso-inv.iso-l{{fill:{mix('stroke', 94, 'top')}}}",
        f"{s}.iso-inv.iso-r{{fill:{var('stroke')}}}",
        f"{s}.iso-accent .iso-inv.iso-t{{fill:{var('accent')}}}",
        f"{s}.iso-accent .iso-inv.iso-l{{fill:{mix('accent', 86, 'stroke')}}}",
        f"{s}.iso-accent .iso-inv.iso-r{{fill:{mix('accent', 72, 'stroke')}}}",
        f"{s}.iso-gi{{fill:none;stroke:{var('top')};stroke-width:{_fmt(outline)}}}",
        f"{s}.iso-gif{{fill:{var('top')}}}",
        f"{s}.iso-cl{{fill:none;stroke:{var('stroke')};stroke-width:{_fmt(outline)}}}",
        f"{s}.iso-accent .iso-cl{{stroke:{var('accent')}}}",
        f"{s}.iso-area{{fill:{var('detail')};fill-opacity:.16}}",
        f"{s}.iso-accent .iso-area{{fill:{var('accent')}}}",
        f"{s}.iso-bar{{fill:{var('detail')};fill-opacity:.55}}",
        f"{s}.iso-port{{fill:{var('top')};stroke:{var('stroke')};stroke-width:{_fmt(outline)}}}",
        f"{s}.iso-portc,{s}.iso-joint{{fill:{var('stroke')}}}",
        f"{s}.iso-link.iso-accent .iso-port{{stroke:{var('accent')}}}",
        f"{s}.iso-link.iso-accent .iso-portc,{s}.iso-link.iso-accent .iso-joint{{fill:{var('accent')}}}",
    ]
    if v12:
        rules += [
            f"{s}.iso-trunk,{s}.iso-trace,{s}.iso-tick,{s}.iso-sock,{s}.iso-hole,{s}.iso-led"
            f"{{stroke-linecap:round;stroke-linejoin:round;vector-effect:non-scaling-stroke}}",
            f"{s}.iso-txt{{fill:{mix('text', 86, 'top')};font-weight:500;letter-spacing:.012em}}",
            f"{s}.iso-sign{{fill:{var('text')};font-weight:600;letter-spacing:.03em}}",
            f"{s}.iso-trunk{{fill:none;stroke:{var('stroke')};stroke-width:{_fmt(outline)}}}",
            f"{s}.iso-silh{{fill:none;stroke:{var('stroke')};stroke-width:{_fmt(outline * 2)};"
            f"vector-effect:non-scaling-stroke}}",
            f"{s}.iso-shade{{fill:{mix('detail', 34, 'right')}}}",
            f"{s}.iso-leafline{{fill:none;stroke:{var('detail')};stroke-width:{hair};stroke-linecap:round;"
            f"vector-effect:non-scaling-stroke}}",
            f"{s}.iso-patch{{fill:{var('shadow')};fill-opacity:.07}}",
            f"{s}.iso-hole{{fill:{mix('stroke', 58, 'right')}}}",
            f"{s}.iso-deck{{fill:{mix('right', 45, 'top')}}}",
            f"{s}.iso-trace{{fill:none;stroke:{var('detail')};stroke-width:{hair};stroke-opacity:.8}}",
            f"{s}.iso-tick{{fill:none;stroke:{var('detail')};stroke-width:{hair}}}",
            f"{s}.iso-sock{{fill:{var('left')};stroke:{var('stroke')};stroke-width:{_fmt(outline)}}}",
            f"{s}.iso-led{{fill:{var('detail')}}}",
            f"{s}.iso-accent .iso-led{{fill:{var('accent')}}}",
            f"{s}.iso-ao{{fill:{var('shadow')};fill-opacity:.1}}",
            f"{s}.iso-dim{{fill:{var('shadow')};fill-opacity:.12}}",
            f"{s}.iso-perf{{fill:{var('detail')};fill-opacity:.6}}",
            f"{s}.iso-sh{{fill-opacity:.04}}",
            f"{s}.iso-glass{{fill:{var('detail')};fill-opacity:.2}}",
            f"{s}.iso-mull{{stroke-opacity:.9}}",
            f"{s}.iso-faint{{stroke-opacity:.5}}",
        ]
    return "".join(rules)


def _text_points(op: tuple[Any, ...]) -> list[Point]:
    _, _, text, matrix, size, anchor = op[:6]
    a, b, c, d, e, f = matrix
    width = _text_width(text, size)
    left = -width / 2 if anchor == "middle" else 0.0
    corners = [(left, -size * 0.6), (left + width, -size * 0.6), (left, size * 0.6), (left + width, size * 0.6)]
    return [(e + a * u + c * v, f + b * u + d * v) for u, v in corners]


def _op_points(op: tuple[Any, ...]) -> list[Point]:
    if op[0] == "icon":
        return list(op[4])
    return _text_points(op) if op[0] == "text" else _segs_points(op[2])


def _bounds(points: list[Point], pad: float = 0.0) -> tuple[float, float, float, float]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


def render(raw_scene: dict[str, Any], base: str | Path | None = None,
           labels: str | None = None) -> tuple[str, dict[str, Any]]:
    """Validate a parsed scene and return (svg_text, manifest) or raise SceneError.

    ``base`` is the directory that the scene's relative icon paths resolve against. ``labels`` overrides the
    scene's label mode: ``"hidden"`` drops every label and sign, under any schema, so the drawing can be checked
    for recognizable objects; ``"upright"`` and ``"face"`` apply to schema 1.2 scenes.
    """
    if labels is not None and labels not in LABEL_MODES:
        raise ValueError(f"labels must be one of {', '.join(LABEL_MODES)}")
    scene = normalize_scene(raw_scene, base)
    v11, v12 = scene["v11"], scene["v12"]
    label_mode = labels or scene["labels"]
    proj = Projection(scene["projection"], scene["unit"])
    style = scene["style"]
    colors = {**DEFAULT_COLORS[style], **scene["colors"]}
    prefix = scene["id_prefix"]
    items = scene["items"]
    warnings: list[str] = []
    errors: list[str] = []
    solids = [item for item in items if item["type"] not in ("connector", "ground-grid")]
    by_id = {item["id"]: item for item in solids}

    groups: dict[int, dict[str, Any]] = {}
    shadow_layer: list[tuple[Any, ...]] = []
    for item in items:
        if item["type"] == "connector":
            route = (_connector_v11 if v11 else _connector)(proj, item, by_id, solids, errors)
            if route is not None:
                ops = [("path", "iso-path", route["segs"])] + route["markers"]
                groups[item["index"]] = {"item": item, "ops": ops, "route": route}
        else:
            ops = RENDERERS[item["type"]](proj, item, style, warnings)
            if scene["shadows"] and item["type"] != "ground-grid":
                shadow = _shadow_ops_v12(proj, item, solids) if v12 else _shadow_ops(proj, item)
                if item["space"][4] > EPS:
                    ops = shadow + ops
                else:
                    shadow_layer += shadow
            groups[item["index"]] = {"item": item, "ops": ops}
    if errors:
        raise SceneError(errors)
    if v11 and scene["detail_stroke"] > scene["stroke"] + EPS:
        warnings.append(f"scene: detail_stroke {_fmt(scene['detail_stroke'])} is heavier than the outline stroke "
                        f"{_fmt(scene['stroke'])}; keep detail lines thinner than outlines")
    if v12:
        for key in ("stroke", "detail_stroke"):
            if scene[key] < MIN_STROKE_V12 - EPS:
                warnings.append(f"scene: {key} {_fmt(scene[key])} px is below 1 CSS px and blurs at 1x; "
                                f"tell detail apart by tone instead")
        warnings += _scale_warnings(items)
    if label_mode == "hidden":
        for group in groups.values():
            group["ops"] = [op for op in group["ops"] if op[0] != "text"]
    elif v12 and label_mode == "upright":
        for group in groups.values():
            group["ops"] = [_upright_text(op) if op[0] == "text" else op for op in group["ops"]]
        warnings += _upright_fit(groups)
    if v12 and label_mode != "hidden":
        for item in items:
            text = item.get("label") or item.get("sign")
            if text and item.get("label_size", MIN_LABEL_PX) < MIN_LABEL_PX - EPS:
                warnings.append(f"{item['where']}: label_size {_fmt(item['label_size'])} px is below {_fmt(MIN_LABEL_PX)} "
                                f"px at the natural size; keep labels at 11 px or more where the SVG renders")

    nodes = []
    for item in items:
        if item["type"] == "ground-grid":
            continue
        group = groups[item["index"]]
        if item["type"] == "connector":
            boxes = group["route"]["boxes"]
            key = min((b[0] + b[1] + b[2] + b[3]) / 2 + b[4] * 2 for b in boxes)
            nodes.append({"id": item["id"], "boxes": boxes, "key": (round(key, 6), 0, item["index"]),
                          "connector": True, "level": group["route"]["level"], "index": item["index"]})
        else:
            b = item["space"]
            key = (b[0] + b[1] + b[2] + b[3] + b[4] + b[5]) / 2
            nodes.append({"id": item["id"], "boxes": [b], "key": (round(key, 6), 1, item["index"]),
                          "connector": False, "level": b[4], "index": item["index"]})
    ordered = [item["index"] for item in items if item["type"] == "ground-grid"]
    if shadow_layer:
        groups[-1] = {"item": {"id": "shadow-layer", "type": "shadows", "role": "shadows"}, "ops": shadow_layer}
        ordered.append(-1)
    ordered += [node["index"] for node in depth_order(nodes, proj.view)]

    element_count = sum(len(op[2]["elements"]) if op[0] == "icon" else 1 for i in ordered for op in groups[i]["ops"])
    if element_count > MAX_ELEMENTS:
        raise SceneError([f"scene: {element_count} drawing elements exceed the limit of {MAX_ELEMENTS}"])
    stroke_pad = scene["stroke"] / 2 + 1.0
    all_points: list[Point] = []
    group_bounds: dict[int, tuple[float, float, float, float]] = {}
    for index in ordered:
        points = [p for op in groups[index]["ops"] for p in _op_points(op)]
        group_bounds[index] = _bounds(points, stroke_pad)
        all_points.extend(points)
    min_x, min_y, max_x, max_y = _bounds(all_points, stroke_pad)
    pad = scene["padding"]
    snap = None
    if v12:
        # A whole-pixel origin keeps snapped hairlines on pixel centers at 1x and 2x.
        ox, oy = math.floor(min_x - pad), math.floor(min_y - pad)
        width = math.ceil(max_x + pad - ox)
        height = math.ceil(max_y + pad - oy)
        snap = _snap_sets([op[2] for index in ordered for op in groups[index]["ops"] if op[0] == "path"])
        warnings += _label_collisions(groups, ordered)
    else:
        ox, oy = min_x - pad, min_y - pad
        width = math.ceil(max_x - min_x + 2 * pad)
        height = math.ceil(max_y - min_y + 2 * pad)
    if width > MAX_CANVAS or height > MAX_CANVAS:
        raise SceneError([f"scene: the drawing spans {width} x {height} px; the limit is {int(MAX_CANVAS)} px per side "
                          f"(lower unit or shrink the scene)"])

    title, desc = scene["title"], scene["desc"]
    root = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}"',
            f' class="iso-scene iso-{style}" data-projection="{proj.kind}" data-unit="{_fmt(proj.unit)}"']
    if title:
        labelled = f"{prefix}title" + (f" {prefix}desc" if desc else "")
        root.append(f' role="img" aria-labelledby="{labelled}">')
    else:
        root.append(' aria-hidden="true" focusable="false">')
    lines = ["".join(root)]
    if title:
        lines.append(f'<title id="{prefix}title">{_xml(title)}</title>')
        if desc:
            lines.append(f'<desc id="{prefix}desc">{_xml(desc)}</desc>')
    lines.append(f"<style>{_style(style, colors, scene['stroke'], scene['detail_stroke'], v11, v12)}</style>")

    manifest_elements = []
    for paint, index in enumerate(ordered):
        group = groups[index]
        item = group["item"]
        kind = item["type"]
        element_id = f"{prefix}{item['id']}"
        layer = {"connector": "iso-link", "ground-grid": "iso-grid-layer", "shadows": "iso-shadow-layer"}
        classes = [layer.get(kind, "iso-obj"), f"iso-{kind}"]
        if item.get("accent"):
            classes.append("iso-accent")
        attrs = [f'id="{element_id}"', f'class="{" ".join(classes)}"', f'data-kind="{kind}"']
        role = item.get("role") or kind
        attrs.append(f'data-role="{role}"')
        if item.get("order") is not None:
            attrs.append(f'data-order="{item["order"]}"')
        attrs.append(f'data-paint="{paint}"')
        if kind == "connector":
            attrs += [f'data-from="{prefix}{item["from"]}"', f'data-to="{prefix}{item["to"]}"']
        lines.append(f"<g {' '.join(attrs)}>")
        for op in group["ops"]:
            if op[0] == "text":
                _, cls, text, (a, b, c, d, e, f), size, anchor = op[:6]
                matrix = " ".join([_fmt(a, 4), _fmt(b, 4), _fmt(c, 4), _fmt(d, 4), _fmt(e - ox), _fmt(f - oy)])
                lines.append(f'<text class="{cls}" transform="matrix({matrix})" font-size="{_fmt(size)}" '
                             f'text-anchor="{anchor}" dominant-baseline="central">{_xml(text)}</text>')
            elif op[0] == "icon":
                _, cls, icon, (a, b, c, d, e, f), _ = op
                matrix = " ".join([_fmt(a, 4), _fmt(b, 4), _fmt(c, 4), _fmt(d, 4), _fmt(e - ox), _fmt(f - oy)])
                lines.append(f'<g class="iso-icon" transform="matrix({matrix})">')
                for tag, paint, attrs in icon["elements"]:
                    klass = {"s": cls, "f": cls + "f", "fs": f"{cls} {cls}f"}[paint]
                    lines.append(f'<{tag} class="{klass}" {attrs}/>')
                lines.append("</g>")
            elif op[1] == "iso-path":
                lines.append(f'<path id="{element_id}-path" class="iso-path" pathLength="1" d="{_path_data(op[2], ox, oy, snap)}"/>')
            else:
                lines.append(f'<path class="{op[1]}" d="{_path_data(op[2], ox, oy, snap)}"/>')
        lines.append("</g>")
        bx0, by0, bx1, by1 = group_bounds[index]
        entry: dict[str, Any] = {
            "id": element_id, "source_id": item["id"], "kind": kind, "role": role,
            "order": item.get("order"), "paint": paint, "accent": bool(item.get("accent")),
            "bbox": {"x": float(_fmt(bx0 - ox)), "y": float(_fmt(by0 - oy)),
                     "width": float(_fmt(bx1 - bx0)), "height": float(_fmt(by1 - by0))},
        }
        if kind == "connector":
            route = group["route"]
            entry.update({"from": f"{prefix}{item['from']}", "to": f"{prefix}{item['to']}",
                          "from_side": route["from_side"], "to_side": route["to_side"],
                          "length": float(_fmt(route["length"], 3)), "path": f"{element_id}-path"})
            if v11:
                entry["level"] = float(_fmt(route["level"], 3))
        manifest_elements.append(entry)
    lines.append("</svg>")
    svg = "\n".join(lines) + "\n"
    manifest = {
        "schema": scene["schema"], "projection": proj.kind, "style": style, "unit": proj.unit,
        "width": width, "height": height, "viewBox": [0, 0, width, height],
        "elements": manifest_elements, "warnings": warnings,
    }
    if label_mode != "face":
        manifest["labels"] = label_mode
    return svg, manifest


def render_file(scene_path: str | Path, labels: str | None = None) -> tuple[str, dict[str, Any]]:
    """Render a scene file; its icon paths resolve against the scene's directory."""
    return render(load_scene(scene_path), Path(scene_path).parent, labels)


# --------------------------------------------------------------------------
# CLI


def _atomic_write(path: Path, text: str) -> None:
    directory = path.parent if str(path.parent) else Path(".")
    handle, temp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
        os.replace(temp, path)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise


def _same_path(a: Path, b: Path) -> bool:
    try:
        return a.resolve() == b.resolve()
    except OSError:
        return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="iso.py",
        description="Render a JSON isometric scene (grid units) to a deterministic, themeable SVG.")
    commands = parser.add_subparsers(dest="command", required=True)
    render_cmd = commands.add_parser("render", help="validate a scene and write its SVG")
    render_cmd.add_argument("scene", help="scene JSON file")
    render_cmd.add_argument("-o", "--output", help="SVG path (default: standard output)")
    render_cmd.add_argument("--manifest", help="write element ids, paint order and projected bounding boxes as JSON")
    render_cmd.add_argument("--no-labels", action="store_true",
                            help="drop every label and sign to check that the objects are recognizable without text")
    args = parser.parse_args(argv)

    scene_path = Path(args.scene)
    outputs = [Path(p) for p in (args.output, args.manifest) if p]
    for output in outputs:
        if _same_path(output, scene_path):
            print(f"iso.py: error: {output} would overwrite the scene file", file=sys.stderr)
            return 1
    if len(outputs) == 2 and _same_path(outputs[0], outputs[1]):
        print("iso.py: error: --output and --manifest name the same file", file=sys.stderr)
        return 1
    try:
        svg, manifest = render_file(scene_path, "hidden" if args.no_labels else None)
    except SceneError as error:
        for message in error.errors:
            print(f"iso.py: error: {message}", file=sys.stderr)
        return 1
    for warning in manifest["warnings"]:
        print(f"iso.py: warning: {warning}", file=sys.stderr)
    try:
        if args.output:
            _atomic_write(Path(args.output), svg)
        else:
            sys.stdout.write(svg)
        if args.manifest:
            _atomic_write(Path(args.manifest), json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    except OSError as error:
        print(f"iso.py: error: cannot write output: {error.strerror or error}", file=sys.stderr)
        return 1
    if args.output:
        print(f"WROTE {args.output} ({manifest['width']} x {manifest['height']} px, "
              f"{len(manifest['elements'])} elements, {len(manifest['warnings'])} warnings)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
