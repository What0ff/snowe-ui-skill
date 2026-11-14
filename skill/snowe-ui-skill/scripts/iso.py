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
``--iso-font``), labels stay real ``<text>``, and every object and connector
carries a stable id, class and ``data-*`` attributes for animation. Identical
input produces identical bytes. A successful render proves geometry and
structure only; composition, legibility and fit still need inspection at real
size.

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
from pathlib import Path
from typing import Any, Callable

SCHEMA = "1.0"
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
STYLES = ("line", "solid")
FACES = ("top", "x+", "y+")
SIDES = ("x+", "x-", "y+", "y-")
GLYPHS = ("dot", "ring", "check", "plus", "bars", "user", "spark", "play")
COLOR_ROLES = ("top", "left", "right", "stroke", "detail", "accent", "text", "grid")
DEFAULT_COLORS = {
    "line": {
        "top": "#ffffff", "left": "#eef1f7", "right": "#dce2ec", "stroke": "#1b2232",
        "detail": "#8a94a8", "accent": "#3d5afe", "text": "#1b2232", "grid": "#d3d9e4",
    },
    "solid": {
        "top": "#e9edf6", "left": "#c5cde0", "right": "#a0abc6", "stroke": "#1b2232",
        "detail": "#56617d", "accent": "#3d5afe", "text": "#1b2232", "grid": "#d3d9e4",
    },
}
# Face tone by the axis its outward normal points along: x -> right, y -> left, z -> top.
AXIS_TONE = ("iso-r", "iso-l", "iso-t")
ARROW_LENGTH = 0.3
PIN = 0.18
ARROW_HALF_WIDTH = 0.15
END_DOT = 0.09


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
    def __init__(self, kind: str, default: Any = REQUIRED, lo: float | None = None, hi: float | None = None,
                 choices: tuple[str, ...] = (), lo_open: bool = False) -> None:
        self.kind, self.default, self.lo, self.hi = kind, default, lo, hi
        self.choices, self.lo_open = choices, lo_open


def _size(default: Any = REQUIRED, lo: float = 0.0, hi: float = MAX_SIZE) -> Field:
    return Field("num", default, lo, hi, lo_open=lo == 0.0)


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
GLYPH = {"glyph": Field("enum", None, choices=GLYPHS)}

TYPES: dict[str, dict[str, Field]] = {
    "box": {**COMMON, **PLACED, **FACE_LABEL, **GLYPH, "w": _size(), "d": _size(), "h": _size(),
            "radius": Field("num", 0.0, 0.0, MAX_SIZE), "bands": Field("int", 0, 0, 24)},
    "slab": {**COMMON, **PLACED, **FACE_LABEL, **GLYPH, "w": _size(), "d": _size(), "h": _size(0.25),
             "radius": Field("num", 0.2, 0.0, MAX_SIZE), "inset": Field("num", 0.0, 0.0, MAX_SIZE)},
    "stack": {**COMMON, **PLACED, **FACE_LABEL, "w": _size(), "d": _size(), "count": Field("int", REQUIRED, 2, 12),
              "h": _size(0.3), "gap": Field("num", 0.16, 0.0, 4.0), "radius": Field("num", 0.12, 0.0, MAX_SIZE),
              "leds": Field("bool", True), "front": Field("enum", "x+", choices=("x+", "y+"))},
    "chip": {**COMMON, **PLACED, **FACE_LABEL, **GLYPH, "w": _size(), "d": _size(), "h": _size(0.3),
             "radius": Field("num", 0.12, 0.0, MAX_SIZE), "pins": Field("int", None, 0, 16), "die": Field("bool", True)},
    "cylinder": {**COMMON, **PLACED, **LABEL, **GLYPH, "w": _size(), "h": _size(), "bands": Field("int", 0, 0, 24)},
    "building": {**COMMON, **PLACED, **FACE_LABEL, "w": _size(), "d": _size(), "floors": Field("int", REQUIRED, 1, 40),
                 "floor_h": _size(0.55, 0.0, 4.0), "roof": Field("bool", True),
                 "windows": Field("enum", "grid", choices=("grid", "ribbon", "none"))},
    "card": {**COMMON, **PLACED, **LABEL, **GLYPH, "w": _size(), "d": _size(None), "h": _size(None),
             "orient": Field("enum", "flat", choices=("flat", "x+", "y+")), "t": _size(0.12, 0.0, 2.0),
             "radius": Field("num", 0.16, 0.0, MAX_SIZE), "lines": Field("int", 0, 0, 4)},
    "screen": {**COMMON, **PLACED, **LABEL, "w": _size(), "h": _size(), "orient": Field("enum", "y+", choices=("x+", "y+")),
               "t": _size(0.14, 0.0, 2.0), "radius": Field("num", 0.08, 0.0, MAX_SIZE), "lines": Field("int", 3, 0, 6),
               "stand": Field("bool", False)},
    "tree": {**COMMON, **PLACED, "w": _size(), "h": _size(), "shape": Field("enum", "round", choices=("round", "cone"))},
    "ground-grid": {"id": Field("token"), "type": Field("type"), "x": PLACED["x"], "y": PLACED["y"],
                    "w": _size(), "d": _size(), "step": Field("num", 1.0, 0.25, 10.0),
                    "pattern": Field("enum", "lines", choices=("lines", "dots")), "fade": Field("bool", True)},
    "connector": {"id": Field("token", None), "type": Field("type"), "role": Field("token", None),
                  "order": Field("int", None, 0, 999), "accent": Field("bool", False),
                  "from": Field("token"), "to": Field("token"),
                  "from_side": Field("enum", None, choices=SIDES), "to_side": Field("enum", None, choices=SIDES),
                  "from_offset": Field("num", 0.0, -MAX_SIZE, MAX_SIZE), "to_offset": Field("num", 0.0, -MAX_SIZE, MAX_SIZE),
                  "via": Field("points", []), "start": Field("enum", "none", choices=("none", "dot")),
                  "end": Field("enum", "arrow", choices=("none", "dot", "arrow")),
                  "gap": Field("num", 0.3, 0.0, 4.0), "radius": Field("num", 0.35, 0.0, 4.0),
                  "z": Field("num", None, 0.0, MAX_SIZE)},
}
SCENE_FIELDS = {
    "schema": Field("enum", SCHEMA, choices=(SCHEMA,)),
    "projection": Field("enum", "isometric", choices=PROJECTIONS),
    "style": Field("enum", "line", choices=STYLES),
    "unit": Field("num", 32.0, 8.0, 96.0),
    "padding": Field("num", 16.0, 0.0, 400.0),
    "stroke": Field("num", 1.5, 0.25, 6.0),
    "detail_stroke": Field("num", 1.0, 0.25, 6.0),
    "title": Field("desc", ""),
    "desc": Field("desc", ""),
    "id_prefix": Field("prefix", "iso-"),
    "colors": Field("colors", {}),
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
    raise AssertionError(kind)


def _num_text(value: float | None) -> str:
    if value is None:
        return "inf"
    return _fmt(value)


def _read_fields(raw: dict[str, Any], spec: dict[str, Field], where: str, errors: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in raw:
        if key not in spec:
            errors.append(f"{where}: unknown field {key!r}; allowed: {', '.join(spec)}")
    for key, field in spec.items():
        if field.kind in ("type", "objects"):
            continue
        if key in raw:
            out[key] = _check(field, raw[key], f"{where}.{key}", errors)
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


def _box(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> tuple[float, ...]:
    return (x0, x1, y0, y1, z0, z1)


def _object_geometry(item: dict[str, Any], where: str, errors: list[str]) -> None:
    """Fill body and occupied boxes for a validated object, or report geometric contradictions."""
    kind = item["type"]
    x, y, z = item["x"], item["y"], item["z"]
    w = item.get("w")
    before = len(errors)
    if kind == "card":
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
    elif kind == "screen":
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
        body = _box(x, x + w, y, y + w, z, z + item["h"])
        item["body"], item["space"] = body, body
    elif kind == "stack":
        count, h, gap = item["count"], item["h"], item["gap"]
        body = _box(x, x + w, y, y + item["d"], z, z + count * h + (count - 1) * gap)
        item["body"], item["space"] = body, body
    elif kind == "building":
        body = _box(x, x + w, y, y + item["d"], z, z + item["floors"] * item["floor_h"])
        item["body"], item["space"] = body, body
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
        elif kind == "screen":
            span = (w, item["h"])
        else:
            span = (body[1] - body[0], body[3] - body[2])
        if radius > min(span) / 2 + EPS:
            errors.append(f"{where}.radius must be at most half the shorter side ({_fmt(min(span) / 2)}); got {_fmt(radius)}")


def normalize_scene(raw: dict[str, Any]) -> dict[str, Any]:
    """Validate a parsed scene and return its normalized form, or raise SceneError with every problem found."""
    errors: list[str] = []
    if not isinstance(raw, dict):
        raise SceneError(["scene: the top level must be a JSON object"])
    scene = _read_fields(raw, SCENE_FIELDS, "scene", errors)
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
        item = _read_fields(raw_item, TYPES[kind], where, errors)
        item["type"] = kind
        item["index"] = index
        item["given"] = frozenset(raw_item)
        text_total += len(item.get("label") or "")
        if kind == "connector" and item.get("id") is None and isinstance(item.get("from"), str) and isinstance(item.get("to"), str):
            item["id"] = f"{item['from']}-to-{item['to']}"
        if item.get("id") is not None:
            if item["id"] in ids:
                hint = "; give each connector between the same objects an explicit id" if kind == "connector" and "id" not in raw_item else ""
                errors.append(f"{where}: duplicate id {item['id']!r}{hint}")
            ids.add(item["id"])
        if len(errors) == before and kind not in ("connector", "ground-grid"):
            _object_geometry(item, where, errors)
        if len(errors) == before and kind == "ground-grid":
            lines = (item["w"] / item["step"] + 1) + (item["d"] / item["step"] + 1)
            dots = (item["w"] / item["step"] + 1) * (item["d"] / item["step"] + 1)
            if item["pattern"] == "lines" and lines > MAX_GRID_LINES:
                errors.append(f"{where}: {int(lines)} grid lines exceed the limit of {MAX_GRID_LINES}; raise step")
            if item["pattern"] == "dots" and dots > MAX_GRID_DOTS:
                errors.append(f"{where}: {int(dots)} grid dots exceed the limit of {MAX_GRID_DOTS}; raise step")
        item["where"] = where
        items.append(item)
    if text_total > MAX_TEXT_TOTAL:
        errors.append(f"scene: {text_total} characters of text exceed the limit of {MAX_TEXT_TOTAL}")
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
    rounded = round(value, places)
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


def _path_data(segs: list[tuple[Any, ...]], ox: float, oy: float) -> str:
    out: list[str] = []
    current: Point | None = None

    def pt(p: Point) -> str:
        return f"{_fmt(p[0] - ox)} {_fmt(p[1] - oy)}"

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
        if style == "line":
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
        return ("text", cls, text, (ux, uy, vx, vy, *self.at(a, b)), size, anchor)


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
    raise AssertionError(glyph)


def _face_content(frame: Frame, item: dict[str, Any], warnings: list[str], *, fit: float | None = None) -> list[tuple[Any, ...]]:
    """Center an optional glyph and label on a face, warning when the label cannot fit."""
    label = item.get("label")
    glyph = item.get("glyph")
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
        ops += _glyph(frame, glyph, start + g / 2, frame.h / 2, g, cls)
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
    if not item.get("label") and not item.get("glyph"):
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
    if item.get("label") or item.get("glyph"):
        frame = _face(proj, box, "top", "x")
        ops += _face_content(frame, item, warnings, fit=frame.w * 0.72)
    return ops


def _render_building(proj: Projection, item: dict[str, Any], style: str, warnings: list[str]) -> list[tuple[Any, ...]]:
    box = item["body"]
    ops = _prism(proj, box, 0.0).ops(style)
    floors, floor_h = item["floors"], item["floor_h"]
    if item["windows"] != "none":
        for face in ("y+", "x+"):
            frame = _face(proj, box, face)
            margin = min(0.18, frame.w * 0.12)
            segs: list[tuple[Any, ...]] = []
            for row in range(floors):
                top = row * floor_h + floor_h * 0.28
                bottom = (row + 1) * floor_h - floor_h * 0.2
                if item["windows"] == "ribbon":
                    segs += frame.poly([(margin, top), (frame.w - margin, top), (frame.w - margin, bottom), (margin, bottom)])
                    continue
                cols = max(1, int((frame.w - 2 * margin) / 0.42))
                cell = (frame.w - 2 * margin) / cols
                for col in range(cols):
                    left = margin + col * cell + cell * 0.2
                    right = margin + (col + 1) * cell - cell * 0.2
                    segs += frame.poly([(left, top), (right, top), (right, bottom), (left, bottom)])
            ops.append(("path", "iso-win", segs))
    if item["roof"]:
        inset = min(0.14, (box[1] - box[0]) * 0.1, (box[3] - box[2]) * 0.1)
        frame = _face(proj, box, "top", "x")
        ops.append(("path", "iso-d", frame.poly([(inset, inset), (frame.w - inset, inset),
                                                  (frame.w - inset, frame.h - inset), (inset, frame.h - inset)])))
    return ops + _labelled_faces(proj, item, box, warnings)


def _plate_axis(orient: str) -> int:
    return {"flat": 2, "x+": 0, "y+": 1}[orient]


def _plate_face(orient: str) -> str:
    return {"flat": "top", "x+": "x+", "y+": "y+"}[orient]


def _render_card(proj: Projection, item: dict[str, Any], style: str, warnings: list[str]) -> list[tuple[Any, ...]]:
    box = item["body"]
    orient = item["orient"]
    ops = _prism(proj, box, item["radius"], _plate_axis(orient)).ops(style)
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
    if style == "line":
        ops.append(("path", "iso-d", display.rrect(0, 0, display.w, display.h, max(0.0, item["radius"] - inset / 2))))
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
    x0, x1, y0, y1, z0, z1 = item["body"]
    w = x1 - x0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    ops: list[tuple[Any, ...]] = []
    trunk_w = max(0.06, w * 0.09)
    if item["shape"] == "round":
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
        if style == "line":
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
    if style == "line":
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


RENDERERS: dict[str, Callable[[Projection, dict[str, Any], str, list[str]], list[tuple[Any, ...]]]] = {
    "box": _render_box, "slab": _render_box, "stack": _render_stack, "chip": _render_chip,
    "cylinder": _render_cylinder, "building": _render_building, "card": _render_card,
    "screen": _render_screen, "tree": _render_tree, "ground-grid": _render_grid,
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


def _style(style: str, colors: dict[str, str], outline: float, detail: float) -> str:
    def var(name: str) -> str:
        return f"var(--iso-{name},{colors[name]})"

    def tint(name: str, share: int) -> str:
        return f"color-mix(in srgb,{var('accent')} {share}%,{var(name)})"

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
    return "".join(rules)


def _text_points(op: tuple[Any, ...]) -> list[Point]:
    _, _, text, matrix, size, anchor = op
    a, b, c, d, e, f = matrix
    width = _text_width(text, size)
    left = -width / 2 if anchor == "middle" else 0.0
    corners = [(left, -size * 0.6), (left + width, -size * 0.6), (left, size * 0.6), (left + width, size * 0.6)]
    return [(e + a * u + c * v, f + b * u + d * v) for u, v in corners]


def _op_points(op: tuple[Any, ...]) -> list[Point]:
    return _text_points(op) if op[0] == "text" else _segs_points(op[2])


def _bounds(points: list[Point], pad: float = 0.0) -> tuple[float, float, float, float]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


def render(raw_scene: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Validate a parsed scene and return (svg_text, manifest) or raise SceneError."""
    scene = normalize_scene(raw_scene)
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
    for item in items:
        if item["type"] == "connector":
            route = _connector(proj, item, by_id, solids, errors)
            if route is not None:
                ops = [("path", "iso-path", route["segs"])] + route["markers"]
                groups[item["index"]] = {"item": item, "ops": ops, "route": route}
        else:
            groups[item["index"]] = {"item": item, "ops": RENDERERS[item["type"]](proj, item, style, warnings)}
    if errors:
        raise SceneError(errors)

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
    ordered += [node["index"] for node in depth_order(nodes, proj.view)]

    element_count = sum(len(groups[i]["ops"]) for i in ordered)
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
    lines.append(f"<style>{_style(style, colors, scene['stroke'], scene['detail_stroke'])}</style>")

    manifest_elements = []
    for paint, index in enumerate(ordered):
        group = groups[index]
        item = group["item"]
        kind = item["type"]
        element_id = f"{prefix}{item['id']}"
        classes = ["iso-link" if kind == "connector" else ("iso-grid-layer" if kind == "ground-grid" else "iso-obj"),
                   f"iso-{kind}"]
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
                _, cls, text, (a, b, c, d, e, f), size, anchor = op
                matrix = " ".join([_fmt(a, 4), _fmt(b, 4), _fmt(c, 4), _fmt(d, 4), _fmt(e - ox), _fmt(f - oy)])
                lines.append(f'<text class="{cls}" transform="matrix({matrix})" font-size="{_fmt(size)}" '
                             f'text-anchor="{anchor}" dominant-baseline="central">{_xml(text)}</text>')
            elif op[1] == "iso-path":
                lines.append(f'<path id="{element_id}-path" class="iso-path" pathLength="1" d="{_path_data(op[2], ox, oy)}"/>')
            else:
                lines.append(f'<path class="{op[1]}" d="{_path_data(op[2], ox, oy)}"/>')
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
        manifest_elements.append(entry)
    lines.append("</svg>")
    svg = "\n".join(lines) + "\n"
    manifest = {
        "schema": SCHEMA, "projection": proj.kind, "style": style, "unit": proj.unit,
        "width": width, "height": height, "viewBox": [0, 0, width, height],
        "elements": manifest_elements, "warnings": warnings,
    }
    return svg, manifest


def render_file(scene_path: str | Path) -> tuple[str, dict[str, Any]]:
    return render(load_scene(scene_path))


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
        svg, manifest = render_file(scene_path)
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
