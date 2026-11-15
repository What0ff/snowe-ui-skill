#!/usr/bin/env python3
"""Build a coherent custom icon family from one JSON spec.

Family tokens (grid, padding, stroke, caps, joins, corner radius, detail
density, duotone tone) are declared once. Each glyph is constructed from
grid-snapped primitives, and every glyph yields three variants from the same
construction: ``outline`` (strokes), ``solid`` (filled masses whose inner
details become even-odd cut-outs) and ``duotone`` (the outline over a lighter
secondary fill). Every SVG is written with companion metadata in the
``asset_quality.py`` schema and validated by it before anything reaches the
output directory. Identical input produces byte-identical output.

Optional character tokens give the family a product voice: angled terminals,
stroke contrast, an aperture and junction gaps (open forms), chamfered, sharp or
leaf corners, narrow or wide keylines, and a filled accent. Angled terminals,
contrast and miter joins expand strokes into exact filled outlines; open-form
gaps under 1 CSS px close in an optical small set. A spec without character
tokens builds byte-identically to one written before they existed, and
``compare`` puts a family beside its plain monoline baseline.

The builder guarantees consistent geometry, not good drawing: recognition,
metaphor and optical balance still need the contact sheet and the real host.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import os
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Iterable

# Isolated interpreters (python -I, PYTHONSAFEPATH) drop the script directory
# from sys.path; the validator below belongs to this skill.
if __name__ == "__main__":
    # An installed skill may be shared or read-only: never write __pycache__ into it.
    sys.dont_write_bytecode = True
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from asset_quality import _path_geometry, validate_svg_asset  # noqa: E402


SCHEMA = "1.0"
VARIANTS = ("outline", "solid", "duotone")
GRID_PADDING = {16: 1.0, 20: 2.0, 24: 2.0, 32: 3.0}
LINECAPS = ("round", "square", "butt")
LINEJOINS = ("round", "bevel")
DETAIL_LEVELS = ("low", "medium", "high")
ROLES = ("body", "detail", "stroke", "accent")
KEYLINES = ("circle", "square", "portrait", "landscape")
# Character tokens: all optional; a spec without them builds byte-identically to one written before they existed.
TERMINALS = ("cap", "angled")
CORNERS = ("round", "chamfer", "sharp", "leaf")
PROPORTIONS = ("narrow", "regular", "wide")
ASPECT = {"narrow": 7 / 8, "regular": 1.0, "wide": 8 / 7}  # rectangular keyline width/height factor at constant area
KEYLINE_RATIOS = {"circle": (1.0, 1.0), "square": (0.9, 0.9), "portrait": (0.8, 1.0), "landscape": (1.0, 0.8)}
CONTRAST_RANGE = (0.5, 1.0)
FILL_RANGE = (0.75, 1.0)
ANGLE_RANGE = (10, 60)
ACCENT_SPAN = 1 / 3  # an accent spans at most a third of the live area in each direction
MITER_LIMIT = 2.0  # expanded miter joins: corners sharper than 60 degrees bevel instead of growing horns
SNAP_STEPS = (0.125, 0.25, 0.5, 1.0)
CHEVRON_DIRECTIONS = ("up", "down", "left", "right")
TONE_RANGE = (0.12, 0.6)  # asset_quality's accepted duotone secondary opacity
ROTATION_STEP = 15
SHEET_SIZES = (16, 20, 24, 32)
NAME_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")

MAX_SPEC_BYTES = 262_144
MAX_GLYPHS = 64
MAX_SHAPES = 24
MAX_EXPANDED = 64
MAX_COPIES = 16
MAX_POINTS = 32
MAX_PATH_COMMANDS = 48
MAX_TEXT = 240
EPS = 1e-9
ARC_CLEARANCE = 0.002

Point = tuple[float, float]


class SpecError(ValueError):
    """The family spec cannot be built; ``problems`` lists every refusal found."""

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("; ".join(problems))


class BuildError(RuntimeError):
    """A built output failed validation or could not be written; nothing was published."""

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("; ".join(problems))


class _Refusal(Exception):
    """One spec refusal raised while parsing a single shape or field."""


# --------------------------------------------------------------------------
# Small numeric helpers


def _fmt(value: float) -> str:
    text = f"{round(value, 3):.3f}".rstrip("0").rstrip(".")
    return "0" if text in {"-0", ""} else text


def _clean(value: float) -> float:
    rounded = round(value, 9)
    return 0.0 if rounded == 0 else rounded


def _add(a: Point, b: Point) -> Point:
    return a[0] + b[0], a[1] + b[1]


def _sub(a: Point, b: Point) -> Point:
    return a[0] - b[0], a[1] - b[1]


def _mul(a: Point, k: float) -> Point:
    return a[0] * k, a[1] * k


def _dot(a: Point, b: Point) -> float:
    return a[0] * b[0] + a[1] * b[1]


def _cross(a: Point, b: Point) -> float:
    return a[0] * b[1] - a[1] * b[0]


def _length(a: Point) -> float:
    return math.hypot(a[0], a[1])


def _unit(a: Point) -> Point:
    size = _length(a)
    return (a[0] / size, a[1] / size) if size > EPS else (0.0, 0.0)


def _normal(t: Point) -> Point:
    """Left normal in raw coordinates; a positive offset moves to this side."""
    return -t[1], t[0]


def _angle(v: Point) -> float:
    return math.atan2(v[1], v[0])


def _polar(center: Point, radius: float, angle: float) -> Point:
    return center[0] + radius * math.cos(angle), center[1] + radius * math.sin(angle)


def _close(a: Point, b: Point, tolerance: float = 1e-7) -> bool:
    return abs(a[0] - b[0]) <= tolerance and abs(a[1] - b[1]) <= tolerance


# --------------------------------------------------------------------------
# Geometry: centerline segments, chains and closed primitives


@dataclass(frozen=True)
class Line:
    p0: Point
    p1: Point


@dataclass(frozen=True)
class Arc:
    """Circular arc ``c + r(cos a, sin a)`` from a0 to a1 (radians, |a1 - a0| < 2π)."""

    c: Point
    r: float
    a0: float
    a1: float


Segment = Line | Arc


@dataclass(frozen=True)
class Chain:
    segs: tuple[Segment, ...]
    closed: bool


@dataclass(frozen=True)
class Circle:
    c: Point
    r: float


@dataclass(frozen=True)
class Ellipse:
    c: Point
    rx: float
    ry: float


@dataclass(frozen=True)
class Dot:
    c: Point
    r: float


@dataclass(frozen=True)
class Opened:
    """A closed contour drawn with an aperture: ``drawn`` is painted, ``gap`` is the removed piece (same direction)."""

    contour: Chain
    drawn: Chain
    gap: Chain


Shape = Chain | Circle | Ellipse | Dot


def _start(s: Segment) -> Point:
    return s.p0 if isinstance(s, Line) else _polar(s.c, s.r, s.a0)


def _end(s: Segment) -> Point:
    return s.p1 if isinstance(s, Line) else _polar(s.c, s.r, s.a1)


def _sweep_sign(s: Arc) -> float:
    return 1.0 if s.a1 > s.a0 else -1.0


def _tan_start(s: Segment) -> Point:
    if isinstance(s, Line):
        return _unit(_sub(s.p1, s.p0))
    k = _sweep_sign(s)
    return -math.sin(s.a0) * k, math.cos(s.a0) * k


def _tan_end(s: Segment) -> Point:
    if isinstance(s, Line):
        return _unit(_sub(s.p1, s.p0))
    k = _sweep_sign(s)
    return -math.sin(s.a1) * k, math.cos(s.a1) * k


def _reverse(s: Segment) -> Segment:
    return Line(s.p1, s.p0) if isinstance(s, Line) else Arc(s.c, s.r, s.a1, s.a0)


def _offset_segment(s: Segment, distance: float) -> Segment | None:
    """Offset by ``distance`` along the left normal; None when an arc collapses."""
    if isinstance(s, Line):
        shift = _mul(_normal(_tan_start(s)), distance)
        return Line(_add(s.p0, shift), _add(s.p1, shift))
    radius = s.r - distance * _sweep_sign(s)
    return Arc(s.c, radius, s.a0, s.a1) if radius > 1e-6 else None


def _arc_extrema(s: Arc) -> list[Point]:
    points = [_start(s), _end(s)]
    low, high = min(s.a0, s.a1), max(s.a0, s.a1)
    first = math.ceil(low / (math.pi / 2) - EPS)
    last = math.floor(high / (math.pi / 2) + EPS)
    for index in range(first, last + 1):
        points.append(_polar(s.c, s.r, index * math.pi / 2))
    return points


def _segment_points(s: Segment, step: float) -> list[Point]:
    """Sample a segment including both endpoints."""
    if isinstance(s, Line):
        count = max(1, math.ceil(_length(_sub(s.p1, s.p0)) / step))
        return [_add(s.p0, _mul(_sub(s.p1, s.p0), index / count)) for index in range(count + 1)]
    sweep = s.a1 - s.a0
    count = max(2, math.ceil(abs(sweep) * s.r / step), math.ceil(abs(sweep) / (math.pi / 36)))
    return [_polar(s.c, s.r, s.a0 + sweep * index / count) for index in range(count + 1)]


def _shape_points(shape: Shape, step: float = 0.25) -> list[Point]:
    """Polygonal approximation of a shape's centerline (closed shapes without repeat)."""
    if isinstance(shape, Chain):
        points: list[Point] = []
        for segment in shape.segs:
            sampled = _segment_points(segment, step)
            points.extend(sampled if not points else sampled[1:])
        if shape.closed and len(points) > 1 and _close(points[0], points[-1], 1e-6):
            points.pop()
        return points
    if isinstance(shape, Ellipse):
        count = max(48, math.ceil(2 * math.pi * max(shape.rx, shape.ry) / step))
        return [
            (shape.c[0] + shape.rx * math.cos(math.tau * i / count), shape.c[1] + shape.ry * math.sin(math.tau * i / count))
            for i in range(count)
        ]
    count = max(32, math.ceil(2 * math.pi * shape.r / step))
    return [_polar(shape.c, shape.r, math.tau * index / count) for index in range(count)]


def _shape_bounds(shape: Shape) -> tuple[float, float, float, float]:
    if isinstance(shape, Chain):
        points = [point for s in shape.segs for point in ([_start(s), _end(s)] if isinstance(s, Line) else _arc_extrema(s))]
    elif isinstance(shape, Ellipse):
        return shape.c[0] - shape.rx, shape.c[1] - shape.ry, shape.c[0] + shape.rx, shape.c[1] + shape.ry
    else:
        return shape.c[0] - shape.r, shape.c[1] - shape.r, shape.c[0] + shape.r, shape.c[1] + shape.r
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def _signed_area(points: list[Point]) -> float:
    total = 0.0
    for index, (x1, y1) in enumerate(points):
        x2, y2 = points[(index + 1) % len(points)]
        total += x1 * y2 - x2 * y1
    return total / 2


def _inside(point: Point, polygon: list[Point]) -> bool:
    x, y = point
    inside = False
    for index, (x1, y1) in enumerate(polygon):
        x2, y2 = polygon[index - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def _point_segment_distance(p: Point, a: Point, b: Point) -> float:
    ab = _sub(b, a)
    size = _dot(ab, ab)
    t = 0.0 if size <= EPS else max(0.0, min(1.0, _dot(_sub(p, a), ab) / size))
    return _length(_sub(p, _add(a, _mul(ab, t))))


def _boundary_distance(points: list[Point], polygon: list[Point]) -> float:
    """Smallest distance from any point to the polygon's edges; edges whose box is already farther are skipped,
    which leaves the exact minimum unchanged."""
    edges = []
    for index in range(len(polygon)):
        a, b = polygon[index - 1], polygon[index]
        edges.append((a, b, min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])))
    best = math.inf
    for x, y in points:
        for a, b, x0, y0, x1, y1 in edges:
            if math.hypot(max(x0 - x, 0.0, x - x1), max(y0 - y, 0.0, y - y1)) >= best:
                continue
            best = min(best, _point_segment_distance((x, y), a, b))
    return best


# --------------------------------------------------------------------------
# Intersections for inner joins


def _on_segment(s: Segment, p: Point, tolerance: float = 1e-6) -> bool:
    if isinstance(s, Line):
        d = _sub(s.p1, s.p0)
        size = _dot(d, d)
        if size <= EPS:
            return False
        t = _dot(_sub(p, s.p0), d) / size
        return -tolerance <= t <= 1 + tolerance
    delta = _arc_delta(s, p)
    return delta is not None


def _arc_delta(s: Arc, p: Point, tolerance: float = 1e-6) -> float | None:
    """Signed angular distance from a0 to p along the sweep, or None when p is off the arc span."""
    sweep = s.a1 - s.a0
    raw = _angle(_sub(p, s.c)) - s.a0
    if sweep > 0:
        delta = raw % math.tau
        if delta > sweep + tolerance and math.tau - delta <= tolerance:
            delta = 0.0
        return delta if delta <= sweep + tolerance else None
    delta = -((-raw) % math.tau)
    if delta < sweep - tolerance and math.tau + delta <= tolerance:
        delta = 0.0
    return delta if delta >= sweep - tolerance else None


def _line_circle(a: Point, b: Point, c: Point, r: float) -> list[Point]:
    d = _sub(b, a)
    f = _sub(a, c)
    qa = _dot(d, d)
    qb = 2 * _dot(f, d)
    qc = _dot(f, f) - r * r
    disc = qb * qb - 4 * qa * qc
    if qa <= EPS or disc < -1e-12:
        return []
    root = math.sqrt(max(0.0, disc))
    return [_add(a, _mul(d, t)) for t in ((-qb - root) / (2 * qa), (-qb + root) / (2 * qa))]


def _circle_circle(c1: Point, r1: float, c2: Point, r2: float) -> list[Point]:
    d = _length(_sub(c2, c1))
    if d <= EPS or d > r1 + r2 + 1e-9 or d < abs(r1 - r2) - 1e-9:
        return []
    a = (r1 * r1 - r2 * r2 + d * d) / (2 * d)
    h = math.sqrt(max(0.0, r1 * r1 - a * a))
    u = _unit(_sub(c2, c1))
    mid = _add(c1, _mul(u, a))
    n = _normal(u)
    return [_add(mid, _mul(n, h)), _sub(mid, _mul(n, h))]


def _intersect(a: Segment, b: Segment, pa: Point, pb: Point) -> Point | None:
    candidates: list[Point] = []
    if isinstance(a, Line) and isinstance(b, Line):
        da, db = _sub(a.p1, a.p0), _sub(b.p1, b.p0)
        denominator = _cross(da, db)
        if abs(denominator) > 1e-12:
            t = _cross(_sub(b.p0, a.p0), db) / denominator
            candidates.append(_add(a.p0, _mul(da, t)))
    elif isinstance(a, Line) and isinstance(b, Arc):
        candidates = _line_circle(a.p0, a.p1, b.c, b.r)
    elif isinstance(a, Arc) and isinstance(b, Line):
        candidates = _line_circle(b.p0, b.p1, a.c, a.r)
    else:
        assert isinstance(a, Arc) and isinstance(b, Arc)
        candidates = _circle_circle(a.c, a.r, b.c, b.r)
    valid = [p for p in candidates if _on_segment(a, p) and _on_segment(b, p)]
    if not valid:
        return None
    return min(valid, key=lambda p: (_length(_sub(p, pa)) + _length(_sub(p, pb)), p))


def _trim(s: Segment, start: Point | None, end: Point | None) -> Segment | None:
    if isinstance(s, Line):
        p0, p1 = start or s.p0, end or s.p1
        if _dot(_sub(p1, p0), _sub(s.p1, s.p0)) <= EPS:
            return None
        return Line(p0, p1)
    a0, a1 = s.a0, s.a1
    if start is not None:
        delta = _arc_delta(s, start)
        if delta is None:
            return s
        a0 = s.a0 + delta
    if end is not None:
        delta = _arc_delta(s, end)
        if delta is None:
            return s
        a1 = s.a0 + delta
    if (a1 - a0) * (s.a1 - s.a0) <= EPS:
        return None
    return Arc(s.c, s.r, a0, a1)


# --------------------------------------------------------------------------
# Stroke outlining: the solid variant turns strokes into filled outlines


def _offset_side(segs: tuple[Segment, ...], closed: bool, distance: float, join: str) -> list[Segment]:
    """Offset a contiguous chain to one side, joining outer corners and trimming inner ones."""
    entries = [(index, offset) for index, segment in enumerate(segs) if (offset := _offset_segment(segment, distance)) is not None]
    if not entries:
        return []
    count = len(entries)
    trim_start: list[Point | None] = [None] * count
    trim_end: list[Point | None] = [None] * count
    connectors: list[list[Segment]] = [[] for _ in range(count)]
    pairs = count if closed else count - 1
    for k in range(pairs):
        k2 = (k + 1) % count
        i1, first = entries[k]
        i2, second = entries[k2]
        pa, pb = _end(first), _start(second)
        if _close(pa, pb):
            continue
        t_in, t_out = _tan_end(segs[i1]), _tan_start(segs[i2])
        collapsed = (i1 + 1) % len(segs) != i2
        vertex = segs[(i1 + 1) % len(segs)].c if collapsed and isinstance(segs[(i1 + 1) % len(segs)], Arc) else _end(segs[i1])
        theta = math.atan2(_cross(t_in, t_out), _dot(t_in, t_out))
        outer = distance * _cross(t_in, t_out) < 0 and not collapsed
        if outer and abs(theta) > 1e-9:
            if join == "round":
                start_angle = _angle(_sub(pa, vertex))
                connectors[k] = [Arc(vertex, abs(distance), start_angle, start_angle + theta)]
            elif join == "miter":
                connectors[k] = _miter(pa, pb, t_in, t_out, vertex, abs(distance))
            else:
                connectors[k] = [Line(pa, pb)]
            continue
        crossing = _intersect(first, second, pa, pb)
        if crossing is not None:
            trim_end[k] = crossing
            trim_start[k2] = crossing
        else:
            connectors[k] = [Line(pa, vertex), Line(vertex, pb)]
    result: list[Segment] = []
    for k, (_, segment) in enumerate(entries):
        trimmed = _trim(segment, trim_start[k], trim_end[k])
        if trimmed is not None:
            result.append(trimmed)
        result.extend(connectors[k])
    return result


def _miter(pa: Point, pb: Point, t_in: Point, t_out: Point, vertex: Point, half: float) -> list[Segment]:
    """Exact miter join of two offset edges; past MITER_LIMIT x half it falls back to a bevel."""
    denominator = _cross(t_in, t_out)
    if abs(denominator) > 1e-12:
        apex = _add(pa, _mul(t_in, _cross(_sub(pb, pa), t_out) / denominator))
        if _length(_sub(apex, vertex)) <= MITER_LIMIT * half:
            return [Line(pa, apex), Line(apex, pb)]
    return [Line(pa, pb)]


def _cap(point: Point, tangent: Point, origin: Point, target: Point, half: float, cap: str) -> list[Segment]:
    if cap == "round":
        start_angle = _angle(_sub(origin, point))
        return [Arc(point, half, start_angle, start_angle - math.pi)]
    if cap == "square":
        reach = _mul(tangent, half)
        return [Line(origin, _add(origin, reach)), Line(_add(origin, reach), _add(target, reach)), Line(_add(target, reach), target)]
    return [Line(origin, target)]


def _cap_toward(point: Point, tangent: Point, origin: Point, target: Point, half: float, cap: str) -> list[Segment]:
    """A cap from either offset side to the other, bulging along ``tangent`` (round and square caps)."""
    if cap == "round":
        start_angle = _angle(_sub(origin, point))
        sweep = math.pi if _cross(_sub(origin, point), tangent) > 0 else -math.pi
        return [Arc(point, half, start_angle, start_angle + sweep)]
    return _cap(point, tangent, origin, target, half, cap)


def _wrap(angle: float) -> float:
    return (angle + math.pi) % math.tau - math.pi


def _cut_direction(tangent: Point, angle: float) -> Point:
    """An angled terminal's cut: the perpendicular to the outward ``tangent`` turned ``angle`` toward it.

    The start and end of a straight stroke get parallel cuts (a parallelogram), the chisel
    terminal of a humanist face, and the cut keeps the stroke's area: length x width.
    """
    n = _normal(tangent)
    return _add(_mul(n, math.cos(angle)), _mul(tangent, math.sin(angle)))


def _meet(segment: Segment, at_end: bool, point: Point, direction: Point) -> Segment:
    """Extend or trim one end of an offset segment exactly onto the line through ``point`` along ``direction``."""
    if isinstance(segment, Line):
        d = _sub(segment.p1, segment.p0)
        denominator = _cross(d, direction)
        if abs(denominator) < 1e-12:
            raise _Refusal("an angled cut runs parallel to its stroke")
        hit = _add(segment.p0, _mul(d, _cross(_sub(point, segment.p0), direction) / denominator))
        result = Line(segment.p0, hit) if at_end else Line(hit, segment.p1)
        if _dot(_sub(result.p1, result.p0), d) <= EPS:
            raise _Refusal("a stroke end is too short for its angled cut; lengthen it or lower tokens.terminal_angle")
        return result
    current = _end(segment) if at_end else _start(segment)
    hits = _line_circle(point, _add(point, direction), segment.c, segment.r)
    if not hits:
        raise _Refusal("an angled cut misses its curved stroke end; lower tokens.terminal_angle")
    hit = min(hits, key=lambda p: (_length(_sub(p, current)), p))
    angle = _angle(_sub(hit, segment.c))
    if at_end:
        result = Arc(segment.c, segment.r, segment.a0, segment.a1 + _wrap(angle - segment.a1))
    else:
        result = Arc(segment.c, segment.r, segment.a0 + _wrap(angle - segment.a0), segment.a1)
    if (result.a1 - result.a0) * (segment.a1 - segment.a0) <= EPS:
        raise _Refusal("a curved stroke end is too short for its angled cut; lengthen it or lower tokens.terminal_angle")
    return result


def _angled_outline(chain: Chain, half: float, join: str, angle: float) -> Chain:
    """Exact filled outline of an open chain whose ends are cut at ``angle`` from the perpendicular."""
    first, last = chain.segs[0], chain.segs[-1]
    for terminal in (first, last):
        if _offset_segment(terminal, half) is None or _offset_segment(terminal, -half) is None:
            raise _Refusal("a stroke end curves tighter than half the stroke and cannot take an angled cut")
    left = _offset_side(chain.segs, False, half, join)
    right = _offset_side(chain.segs, False, -half, join)
    end, start = _end(last), _start(first)
    end_cut = _cut_direction(_tan_end(last), angle)
    start_cut = _cut_direction(_mul(_tan_start(first), -1.0), angle)
    for side in (left, right):
        side[-1] = _meet(side[-1], True, end, end_cut)
        side[0] = _meet(side[0], False, start, start_cut)
    out: list[Segment] = list(left)
    out.append(Line(_end(left[-1]), _end(right[-1])))
    out += [_reverse(segment) for segment in reversed(right)]
    out.append(Line(_start(right[0]), _start(left[0])))
    return Chain(tuple(out), True)


def _stroke_outline(chain: Chain, half: float, cap: str, join: str, angle: float = 0.0) -> Chain:
    """Closed outline of an open stroked chain, matching its caps (or angled terminals) and joins."""
    left = _offset_side(chain.segs, False, half, join)
    right = _offset_side(chain.segs, False, -half, join)
    if not left or not right:
        raise _Refusal("a curve is tighter than half the stroke and cannot be outlined; enlarge its radius")
    if angle:
        return _angled_outline(chain, half, join, angle)
    first, last = chain.segs[0], chain.segs[-1]
    out: list[Segment] = list(left)
    out += _cap(_end(last), _tan_end(last), _end(left[-1]), _end(right[-1]), half, cap)
    out += [_reverse(segment) for segment in reversed(right)]
    back = _mul(_tan_start(first), -1.0)
    out += _cap(_start(first), back, _start(right[0]), _start(left[0]), half, cap)
    return Chain(tuple(out), True)


def _outer_sign(chain: Chain) -> float:
    return -1.0 if _signed_area(_shape_points(chain)) > 0 else 1.0


def _closed_offset(chain: Chain, distance: float, join: str) -> Chain | None:
    segs = _offset_side(chain.segs, True, distance, join)
    return Chain(tuple(segs), True) if segs else None


def _closed_by_chord(chain: Chain) -> Chain:
    if chain.closed:
        return chain
    return Chain(chain.segs + (Line(_end(chain.segs[-1]), _start(chain.segs[0])),), True)


def _grow(shape: Shape, half: float, join: str) -> Shape | None:
    """Outer edge of a closed shape stroked at width 2*half."""
    if isinstance(shape, Chain):
        return _closed_offset(shape, _outer_sign(shape) * half, join)
    if isinstance(shape, Ellipse):
        return Ellipse(shape.c, shape.rx + half, shape.ry + half)
    if isinstance(shape, Dot):
        return Circle(shape.c, shape.r)
    return Circle(shape.c, shape.r + half)


def _shrink(shape: Shape, half: float, join: str) -> Shape | None:
    """Inner edge of a closed shape stroked at width 2*half (None when it closes up)."""
    if isinstance(shape, Chain):
        return _closed_offset(shape, -_outer_sign(shape) * half, join)
    if isinstance(shape, Ellipse):
        return Ellipse(shape.c, shape.rx - half, shape.ry - half) if min(shape.rx, shape.ry) - half > 1e-6 else None
    radius = shape.r - half
    return Circle(shape.c, radius) if radius > 1e-6 else None


def _notched_mass(opened: Opened, half: float, cap: str, join: str, angle: float) -> Chain:
    """Solid mass of a body drawn with an aperture: its outer edge, notched by exactly the outline's gap.

    The notch is the stroke band the aperture removes, ends shaped like the outline's terminals,
    so the solid keeps the outline's silhouette and its signature break.
    """
    sign = _outer_sign(opened.contour)
    outer = _offset_side(opened.drawn.segs, False, sign * half, join)
    inner = _offset_side(opened.gap.segs, False, -sign * half, join)
    if not outer or not inner:
        raise _Refusal("the aperture's solid notch cannot be outlined; enlarge the curve it sits on")
    drawn = opened.drawn.segs
    end_point, start_point = _end(drawn[-1]), _start(drawn[0])
    end_tangent, start_tangent = _tan_end(drawn[-1]), _mul(_tan_start(drawn[0]), -1.0)
    if angle:
        end_cut, start_cut = _cut_direction(end_tangent, angle), _cut_direction(start_tangent, angle)
        outer[-1] = _meet(outer[-1], True, end_point, end_cut)
        inner[0] = _meet(inner[0], False, end_point, end_cut)
        inner[-1] = _meet(inner[-1], True, start_point, start_cut)
        outer[0] = _meet(outer[0], False, start_point, start_cut)
        into = [Line(_end(outer[-1]), _start(inner[0]))]
        back = [Line(_end(inner[-1]), _start(outer[0]))]
    else:
        into = _cap_toward(end_point, end_tangent, _end(outer[-1]), _start(inner[0]), half, cap)
        back = _cap_toward(start_point, start_tangent, _end(inner[-1]), _start(outer[0]), half, cap)
    return Chain(tuple(outer + into + inner + back), True)


# --------------------------------------------------------------------------
# Arc-length geometry for open forms: slicing chains and measuring distance


def _segment_length(s: Segment) -> float:
    return _length(_sub(s.p1, s.p0)) if isinstance(s, Line) else s.r * abs(s.a1 - s.a0)


def _segment_at(s: Segment, t: float) -> Point:
    if isinstance(s, Line):
        return _add(s.p0, _mul(_sub(s.p1, s.p0), t))
    return _polar(s.c, s.r, s.a0 + (s.a1 - s.a0) * t)


def _segment_part(s: Segment, t0: float, t1: float) -> Segment:
    if isinstance(s, Line):
        return Line(_segment_at(s, t0), _segment_at(s, t1))
    sweep = s.a1 - s.a0
    return Arc(s.c, s.r, s.a0 + sweep * t0, s.a0 + sweep * t1)


def _chain_length(chain: Chain) -> float:
    return sum(_segment_length(s) for s in chain.segs)


def _chain_point(chain: Chain, s: float) -> Point:
    for segment in chain.segs:
        size = _segment_length(segment)
        if s <= size or segment is chain.segs[-1]:
            return _segment_at(segment, min(1.0, max(0.0, s / size)) if size > EPS else 0.0)
        s -= size
    return _end(chain.segs[-1])


def _chain_tangent(chain: Chain, s: float) -> Point:
    for segment in chain.segs:
        size = _segment_length(segment)
        if s <= size or segment is chain.segs[-1]:
            if isinstance(segment, Line):
                return _tan_start(segment)
            t = min(1.0, max(0.0, s / size)) if size > EPS else 0.0
            return _tan_start(Arc(segment.c, segment.r, segment.a0 + (segment.a1 - segment.a0) * t, segment.a1))
        s -= size
    return _tan_end(chain.segs[-1])


def _end_probe(tokens: Tokens, half: float) -> list[Point]:
    """Points of a painted stroke end as (across, along) offsets: corners, plus the cap outline for round caps."""
    if tokens.terminal == "cap" and tokens.linecap == "round":
        return [(half * math.cos(k * math.pi / 4), half * math.sin(k * math.pi / 4)) for k in range(8)]
    along = tokens.cap_extension(half)
    return [(side * half, lean * along) for side in (-1.0, 1.0) for lean in ((-1.0, 1.0) if along else (0.0,))]


def _chain_slice(chain: Chain, start: float, end: float) -> Chain:
    """The open piece of ``chain`` between two arc lengths; a closed chain wraps past its seam."""
    total = _chain_length(chain)
    if chain.closed:
        start %= total
        end %= total
        if end <= start + 1e-9:
            end += total
        laps = [(chain.segs, 0.0), (chain.segs, total)]
    else:
        start, end = max(0.0, start), min(total, end)
        laps = [(chain.segs, 0.0)]
    pieces: list[Segment] = []
    for segs, offset in laps:
        position = offset
        for segment in segs:
            size = _segment_length(segment)
            low, high = max(start, position), min(end, position + size)
            if high - low > 1e-9 and size > EPS:
                pieces.append(_segment_part(segment, (low - position) / size, (high - position) / size))
            position += size
    return Chain(tuple(pieces), False)


def _as_chain(shape: Shape, seam: float = 0.0) -> Chain | None:
    """A closed contour as a chain (a circle becomes two half arcs from ``seam``); None for ellipses and dots."""
    if isinstance(shape, Chain):
        return shape
    if isinstance(shape, Circle):
        return Chain((Arc(shape.c, shape.r, seam, seam + math.pi), Arc(shape.c, shape.r, seam + math.pi, seam + math.tau)), True)
    return None


def _segment_distance(p: Point, s: Segment) -> float:
    if isinstance(s, Line):
        return _point_segment_distance(p, s.p0, s.p1)
    if _arc_delta(s, p) is not None:
        return abs(_length(_sub(p, s.c)) - s.r)
    return min(_length(_sub(p, _start(s))), _length(_sub(p, _end(s))))


def _shape_distance(p: Point, shape: Shape) -> float:
    """Distance from a point to a shape's centerline (a dot's center)."""
    if isinstance(shape, Chain):
        return min(_segment_distance(p, s) for s in shape.segs)
    if isinstance(shape, Circle):
        return abs(_length(_sub(p, shape.c)) - shape.r)
    if isinstance(shape, Dot):
        return _length(_sub(p, shape.c))
    polygon = _shape_points(shape, 0.1)
    return min(_point_segment_distance(p, polygon[index - 1], polygon[index]) for index in range(len(polygon)))


def _below_windows(length: float, f: Any) -> list[tuple[float, float]]:
    """Arc-length intervals in [0, length] where ``f`` is negative, edges refined by bisection."""
    steps = max(8, math.ceil(length / 0.1))
    samples = [length * index / steps for index in range(steps + 1)]
    values = [f(s) for s in samples]
    windows: list[tuple[float, float]] = []
    opened_at = 0.0 if values[0] < 0 else None
    for index in range(1, len(samples)):
        before, after = values[index - 1] < 0, values[index] < 0
        if before == after:
            continue
        low, high = samples[index - 1], samples[index]
        for _ in range(48):
            middle = (low + high) / 2
            if (f(middle) < 0) == before:
                low = middle
            else:
                high = middle
        edge = (low + high) / 2
        if after:
            opened_at = edge
        else:
            windows.append((opened_at if opened_at is not None else 0.0, edge))
            opened_at = None
    if opened_at is not None:
        windows.append((opened_at, length))
    return windows


# --------------------------------------------------------------------------
# Spec parsing


@dataclass
class Tokens:
    grid: int
    padding: float
    stroke: float
    linecap: str
    linejoin: str
    radius: float
    detail: str
    dot: float
    snap: float
    crisp: bool
    secondary_opacity: float | None
    # Character tokens; the defaults reproduce the plain monoline family exactly.
    terminal: str = "cap"
    terminal_angle: int = 0
    contrast: float = 1.0
    aperture: float = 0.0
    aperture_at: int = 2
    junction_gap: float = 0.0
    corner: str = "round"
    proportion: str = "regular"
    fill: float = 1.0
    accent: str | None = None

    @property
    def half(self) -> float:
        return self.stroke / 2

    @property
    def expanded(self) -> bool:
        """Outline strokes are drawn as exact filled outlines: SVG strokes cannot cut at an angle or vary in width."""
        return self.terminal != "cap" or self.contrast < 1

    @property
    def cut(self) -> float:
        """Angled-terminal cut in radians (0 for cap terminals)."""
        return math.radians(self.terminal_angle) if self.terminal == "angled" else 0.0

    @property
    def detail_stroke(self) -> float:
        return round(self.stroke * self.contrast / 0.125) * 0.125 if self.contrast < 1 else self.stroke

    @property
    def character(self) -> bool:
        return (self.terminal != "cap" or self.contrast < 1 or bool(self.aperture) or bool(self.junction_gap)
                or self.corner != "round" or self.proportion != "regular" or self.fill != 1.0
                or self.accent is not None)

    def cap_extension(self, half: float) -> float:
        """How far a painted terminal reaches past its centerline end, along the stroke."""
        if self.terminal == "angled":
            return half * abs(math.tan(self.cut))
        return half if self.linecap in {"round", "square"} else 0.0

    @property
    def center(self) -> Point:
        return self.grid / 2, self.grid / 2

    @property
    def live(self) -> tuple[float, float, float, float]:
        return self.padding, self.padding, self.grid - self.padding, self.grid - self.padding

    @property
    def reach(self) -> float:
        """Painted reach beyond the centerline as asset_quality bounds it."""
        return self.half * (math.sqrt(2) if self.linecap == "square" else 1.0)

    @property
    def lattice_phase(self) -> float | None:
        """Pixel phase for crisp axis-aligned strokes at the base grid, or None when no lattice exists."""
        if not self.crisp or abs(self.stroke - round(self.stroke)) > EPS:
            return None
        return (self.stroke / 2) % 1.0

    def keyline(self, kind: str) -> tuple[float, float, float, float]:
        """Keyline box: circles stay round; narrow and wide reshape rectangles at constant area within the live area."""
        live = self.grid - 2 * self.padding
        ratio = KEYLINE_RATIOS[kind]
        if kind != "circle" and self.proportion != "regular":
            root = math.sqrt(ASPECT[self.proportion])
            ratio = (min(1.0, ratio[0] * root), min(1.0, ratio[1] / root))
        width = round(live * ratio[0] * self.fill / self.snap) * self.snap
        height = round(live * ratio[1] * self.fill / self.snap) * self.snap
        cx, cy = self.center
        return cx - width / 2, cy - height / 2, cx + width / 2, cy + height / 2


@dataclass
class PathForm:
    points: list[Point]
    kinds: list[tuple]  # ("L",) or ("A", r, large, sweep) for each segment
    closed: bool
    radius: float


@dataclass
class ArcForm:
    center: Point
    r: float
    a0: float
    a1: float


@dataclass
class CircleForm:
    center: Point
    r: float


@dataclass
class EllipseForm:
    center: Point
    rx: float
    ry: float


@dataclass
class DotForm:
    center: Point
    r: float


Form = PathForm | ArcForm | CircleForm | EllipseForm | DotForm


@dataclass
class Item:
    label: str
    role: str
    variants: tuple[str, ...]
    duotone_fill: bool
    shapes: list[Shape]
    aperture: bool | None = None  # True hosts the family aperture, False never does
    junction: bool = True  # False keeps this shape out of junction gaps


@dataclass
class Glyph:
    name: str
    role: str
    keyline: str | None
    detail_budget: str | None
    items: list[Item]
    aperture: tuple[int, int, Opened] | None = None  # (item index, shape index, opened contour)
    cache: dict = field(default_factory=dict, repr=False, compare=False)  # deterministic constructions, built once


@dataclass
class Family:
    name: str
    tokens: Tokens
    variants: tuple[str, ...]
    target_sizes: list[int]
    creator: str
    reviewed: str
    license: str
    source: str
    accessibility_owner: str
    glyphs: list[Glyph]
    tabs: list[str]
    warnings: list[str] = field(default_factory=list)
    open_from: int | None = None  # smallest target size that shows open-form gaps; smaller ones get the closed optical set

    @property
    def main_sizes(self) -> list[int]:
        return [size for size in self.target_sizes if self.open_from is None or size >= self.open_from]

    @property
    def small_sizes(self) -> list[int]:
        return [size for size in self.target_sizes if self.open_from is not None and size < self.open_from]

    def sets(self) -> list[bool]:
        """Optical sets to build: the main set, then the small set (open forms closed) when sizes need one."""
        return [False, True] if self.small_sizes else [False]


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key {key!r}")
        result[key] = value
    return result


def read_spec(path: str | Path) -> bytes:
    """Read the exact spec bytes within the family size budget."""
    spec_path = Path(path)
    try:
        if spec_path.stat().st_size > MAX_SPEC_BYTES:
            raise SpecError([f"spec exceeds the {MAX_SPEC_BYTES}-byte family budget"])
        return spec_path.read_bytes()
    except FileNotFoundError:
        raise SpecError([f"spec not found: {spec_path}"]) from None
    except OSError as error:
        raise SpecError([f"spec cannot be read: {error}"]) from None


def parse_spec(content: bytes) -> dict[str, Any]:
    """Parse spec bytes as strict JSON: UTF-8, no duplicate keys, no NaN or Infinity."""
    if len(content) > MAX_SPEC_BYTES:
        raise SpecError([f"spec exceeds the {MAX_SPEC_BYTES}-byte family budget"])
    try:
        text = content.decode("utf-8-sig")
        value = json.loads(text, object_pairs_hook=_reject_duplicate_keys, parse_constant=_reject_constant)
    except UnicodeDecodeError as error:
        raise SpecError([f"spec is not UTF-8 text: {error}"]) from None
    except (ValueError, RecursionError) as error:
        raise SpecError([f"spec is not valid JSON: {error}"]) from None
    if not isinstance(value, dict):
        raise SpecError(["spec root must be a JSON object"])
    return value


def load_spec(path: str | Path) -> dict[str, Any]:
    """Read and parse a family spec file."""
    return parse_spec(read_spec(path))


def _reject_constant(name: str) -> Any:
    raise ValueError(f"non-finite number {name} is not allowed")


def _fields(value: Any, where: str, required: Iterable[str], optional: Iterable[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise _Refusal(f"{where} must be an object")
    required, optional = set(required), set(optional)
    unknown = sorted(set(value) - required - optional)
    if unknown:
        raise _Refusal(f"{where} has unknown field(s): {', '.join(unknown)}")
    missing = sorted(required - set(value))
    if missing:
        raise _Refusal(f"{where} is missing required field(s): {', '.join(missing)}")
    return value


def _number(value: Any, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _Refusal(f"{where} must be a number")
    number = float(value)
    if not math.isfinite(number):
        raise _Refusal(f"{where} must be finite")
    return number


def _on_snap(value: float, snap: float, where: str) -> float:
    if abs(value / snap - round(value / snap)) > 1e-9:
        raise _Refusal(f"{where} = {value:g} is off the {snap:g}-unit construction grid")
    return value


def _coord(value: Any, where: str, tokens: Tokens) -> float:
    number = _on_snap(_number(value, where), tokens.snap, where)
    if not -tokens.grid <= number <= 2 * tokens.grid:
        raise _Refusal(f"{where} = {number:g} lies far outside the {tokens.grid}-unit grid")
    return number


def _point(value: Any, where: str, tokens: Tokens) -> Point:
    if not isinstance(value, list) or len(value) != 2:
        raise _Refusal(f"{where} must be an [x, y] pair")
    return _coord(value[0], f"{where}[0]", tokens), _coord(value[1], f"{where}[1]", tokens)


def _size(value: Any, where: str, tokens: Tokens, *, zero: bool = False) -> float:
    number = _on_snap(_number(value, where), tokens.snap, where)
    if number < 0 or (number == 0 and not zero) or number > tokens.grid:
        raise _Refusal(f"{where} must be {'a non-negative' if zero else 'a positive'} length within the grid")
    return number


def _integer(value: Any, where: str, low: int, high: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise _Refusal(f"{where} must be an integer from {low} to {high}")
    return value


def _choice(value: Any, where: str, choices: Iterable[str]) -> str:
    options = tuple(choices)
    if value not in options:
        raise _Refusal(f"{where} must be one of: {', '.join(options)}")
    return value


def _text(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > MAX_TEXT:
        raise _Refusal(f"{where} must be non-empty text of at most {MAX_TEXT} characters")
    if any(ord(character) < 0x20 or 0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise _Refusal(f"{where} contains control characters or unpaired surrogates")
    if re.fullmatch(r"\s*<[^<>]*>\s*", value) or value.strip().casefold() in {"tbd", "todo", "unknown", "n/a", "none"}:
        raise _Refusal(f"{where} is a placeholder; write the real value")
    return value.strip()


def _name(value: Any, where: str) -> str:
    if not isinstance(value, str) or not NAME_RE.fullmatch(value) or len(value) > 64:
        raise _Refusal(f"{where} must be a lowercase name token such as 'scale-servings'")
    return value


CHARACTER_TOKENS = (
    "terminal", "terminal_angle", "contrast", "aperture", "aperture_at", "junction_gap",
    "corner", "proportion", "fill", "accent",
)


def _decimals(value: float, places: int, where: str, low: float, high: float) -> float:
    if not low <= value <= high or abs(round(value, places) - value) > 1e-12:
        raise _Refusal(f"{where} must be from {low:g} to {high:g} with at most {places} decimals")
    return value


def _parse_character(value: dict[str, Any], tokens: Tokens) -> None:
    """Validate the optional character tokens into ``tokens``; every refusal names the token and its range."""
    tokens.terminal = _choice(value.get("terminal", "cap"), "tokens.terminal", TERMINALS)
    if tokens.terminal == "angled":
        if tokens.linecap != "butt":
            raise _Refusal('tokens.terminal "angled" replaces the cap; set tokens.linecap to "butt"')
        angle = value.get("terminal_angle", 30)
        if (isinstance(angle, bool) or not isinstance(angle, int) or angle % 5
                or not ANGLE_RANGE[0] <= abs(angle) <= ANGLE_RANGE[1]):
            raise _Refusal(
                f"tokens.terminal_angle must be a multiple of 5 degrees from {ANGLE_RANGE[0]} to {ANGLE_RANGE[1]} "
                "(negative mirrors the lean)"
            )
        tokens.terminal_angle = angle
    elif "terminal_angle" in value:
        raise _Refusal('tokens.terminal_angle applies only to tokens.terminal "angled"')
    if "contrast" in value:
        tokens.contrast = _decimals(_number(value["contrast"], "tokens.contrast"), 2, "tokens.contrast", *CONTRAST_RANGE)
        if tokens.contrast < 1 and tokens.detail_stroke >= tokens.stroke:
            raise _Refusal(
                f"tokens.contrast {tokens.contrast:g} rounds the detail stroke back to {tokens.stroke:g} on the 0.125 step; lower it"
            )
    if tokens.linejoin == "miter" and not tokens.expanded:
        raise _Refusal(
            "tokens.linejoin must be one of: round, bevel; miter joins need expanded outlines "
            '(tokens.terminal "angled" or tokens.contrast below 1), because a stroked miter cannot be bounded'
        )
    if "aperture" in value:
        tokens.aperture = _on_snap(_number(value["aperture"], "tokens.aperture"), tokens.snap, "tokens.aperture")
        if not 0.5 <= tokens.aperture <= tokens.grid / 6:
            raise _Refusal(f"tokens.aperture must be a visible gap from 0.5 to {tokens.grid / 6:g} units")
        tokens.aperture_at = _integer(value.get("aperture_at", 2), "tokens.aperture_at", 1, 12)
    elif "aperture_at" in value:
        raise _Refusal("tokens.aperture_at applies only with tokens.aperture")
    if "junction_gap" in value:
        tokens.junction_gap = _on_snap(_number(value["junction_gap"], "tokens.junction_gap"), tokens.snap, "tokens.junction_gap")
        if not 0.25 <= tokens.junction_gap <= tokens.grid / 12:
            raise _Refusal(f"tokens.junction_gap must be from 0.25 to {tokens.grid / 12:g} units")
    tokens.corner = _choice(value.get("corner", "round"), "tokens.corner", CORNERS)
    tokens.proportion = _choice(value.get("proportion", "regular"), "tokens.proportion", PROPORTIONS)
    if "fill" in value:
        tokens.fill = _decimals(_number(value["fill"], "tokens.fill"), 2, "tokens.fill", *FILL_RANGE)
    if "accent" in value:
        tokens.accent = _text(value["accent"], "tokens.accent")


def _parse_tokens(raw: Any) -> Tokens:
    value = _fields(
        raw, "tokens", ("stroke", "linecap", "linejoin", "radius"),
        ("grid", "padding", "detail", "dot", "snap", "crisp", "secondary_opacity", *CHARACTER_TOKENS),
    )
    grid = value.get("grid", 24)
    if grid not in GRID_PADDING or isinstance(grid, bool):
        raise _Refusal("tokens.grid must be 16, 20, 24 or 32")
    snap = _number(value.get("snap", 0.25), "tokens.snap")
    if snap not in SNAP_STEPS:
        raise _Refusal("tokens.snap must be 0.125, 0.25, 0.5 or 1")
    stroke = _number(value["stroke"], "tokens.stroke")
    if not 0 < stroke <= grid / 8 or abs(stroke / 0.125 - round(stroke / 0.125)) > 1e-9:
        raise _Refusal(f"tokens.stroke must be a multiple of 0.125 from 0.125 to {grid / 8:g}")
    padding = _number(value.get("padding", GRID_PADDING[grid]), "tokens.padding")
    _on_snap(padding, snap, "tokens.padding")
    if not 0 <= padding <= grid / 6:
        raise _Refusal(f"tokens.padding must be from 0 to {grid / 6:g}")
    radius = _number(value["radius"], "tokens.radius")
    _on_snap(radius, snap, "tokens.radius")
    if not 0 <= radius <= grid / 4:
        raise _Refusal(f"tokens.radius must be from 0 to {grid / 4:g}")
    default_dot = max(stroke, round(stroke * 4 / 3 / snap) * snap)
    dot = _number(value.get("dot", default_dot), "tokens.dot")
    _on_snap(dot, snap, "tokens.dot")
    if not stroke * 0.5 <= dot <= stroke * 3:
        raise _Refusal("tokens.dot must be from half to three times the stroke")
    crisp = value.get("crisp", True)
    if not isinstance(crisp, bool):
        raise _Refusal("tokens.crisp must be true or false")
    tone = value.get("secondary_opacity")
    if tone is not None:
        tone = _number(tone, "tokens.secondary_opacity")
        if not TONE_RANGE[0] <= tone <= TONE_RANGE[1] or abs(round(tone, 3) - tone) > 1e-12:
            raise _Refusal(f"tokens.secondary_opacity must be {TONE_RANGE[0]:g}-{TONE_RANGE[1]:g} with at most three decimals")
    tokens = Tokens(
        grid=grid, padding=padding, stroke=stroke,
        linecap=_choice(value["linecap"], "tokens.linecap", LINECAPS),
        linejoin="miter" if value["linejoin"] == "miter" else _choice(value["linejoin"], "tokens.linejoin", LINEJOINS),
        radius=radius, detail=_choice(value.get("detail", "medium"), "tokens.detail", DETAIL_LEVELS),
        dot=dot, snap=snap, crisp=crisp, secondary_opacity=tone,
    )
    _parse_character(value, tokens)
    return tokens


# Shape grammar: required fields, optional fields, default role ("auto": body when closed, else stroke).
PRIMITIVES: dict[str, tuple[set[str], set[str], str]] = {
    "line": ({"from", "to"}, set(), "stroke"),
    "polyline": ({"points"}, {"closed", "radius"}, "auto"),
    "path": ({"d"}, {"radius"}, "auto"),
    "arc": ({"center", "r", "start", "end"}, set(), "stroke"),
    "circle": (set(), {"center", "r", "fit"}, "body"),
    "ellipse": ({"center", "rx", "ry"}, set(), "body"),
    "rect": (set(), {"x", "y", "w", "h", "radius", "fit"}, "body"),
    "rounded-rect": (set(), {"x", "y", "w", "h", "radius", "fit"}, "body"),
    "polygon": ({"center", "r", "sides"}, {"rotation", "radius"}, "body"),
    "gear": ({"center", "r", "root", "teeth"}, {"tooth", "radius"}, "body"),
    "chevron": ({"tip", "dir", "span"}, {"depth", "radius"}, "stroke"),
    "arrow": ({"from", "to"}, {"head"}, "stroke"),
    "dot": ({"at"}, {"d"}, "detail"),
}
COMMON_FIELDS = {
    "type", "id", "role", "variants", "min_detail", "rotate", "repeat", "radial", "mirror", "about", "duotone_fill",
    "aperture", "junction",
}


def _crisp(value: float, phase: float | None, center: float) -> float:
    """Nearest pixel-lattice position for an axis-aligned stroke; ties move toward the glyph center."""
    if phase is None:
        return value
    k = value - phase
    if abs(k - round(k)) < 1e-9:
        return value
    low = math.floor(k) + phase
    high = low + 1
    if abs((value - low) - (high - value)) < 1e-9:
        return high if value < center else low
    return low if value - low < high - value else high


def _crisp_path(points: list[Point], kinds: list[tuple], closed: bool, tokens: Tokens) -> list[Point]:
    phase = tokens.lattice_phase
    if phase is None:
        return points
    snap_x, snap_y = set(), set()
    count = len(points)
    for index, kind in enumerate(kinds):
        if kind[0] != "L":
            continue
        a, b = index, (index + 1) % count
        if abs(points[a][0] - points[b][0]) < 1e-9:
            snap_x.update((a, b))
        if abs(points[a][1] - points[b][1]) < 1e-9:
            snap_y.update((a, b))
    cx, cy = tokens.center
    return [
        (_crisp(x, phase, cx) if index in snap_x else x, _crisp(y, phase, cy) if index in snap_y else y)
        for index, (x, y) in enumerate(points)
    ]


def _path_form(where: str, points: list[Point], closed: bool, radius: float, tokens: Tokens,
               kinds: list[tuple] | None = None) -> PathForm:
    count = len(points) if closed else len(points) - 1
    kinds = kinds if kinds is not None else [("L",)] * count
    for index in range(count):
        if _close(points[index], points[(index + 1) % len(points)], 1e-9):
            raise _Refusal(f"{where} repeats point {index + 1}; every segment needs length")
    return PathForm(_crisp_path(points, kinds, closed, tokens), kinds, closed, radius)


def _parse_d(text: Any, where: str, tokens: Tokens) -> tuple[list[Point], list[tuple], bool]:
    if not isinstance(text, str) or len(text) > 2000:
        raise _Refusal(f"{where} must be path text of at most 2000 characters")
    tokens_list = re.findall(r"[A-Za-z]|[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?|[^\s,]", text)
    commands = [token for token in tokens_list if token.isalpha()]
    if len(commands) > MAX_PATH_COMMANDS:
        raise _Refusal(f"{where} exceeds {MAX_PATH_COMMANDS} commands")
    position = 0

    def take(count: int) -> list[float]:
        nonlocal position
        values = []
        for _ in range(count):
            if position >= len(tokens_list) or tokens_list[position].isalpha():
                raise _Refusal(f"{where} has a command with missing numbers")
            try:
                values.append(float(tokens_list[position]))
            except ValueError:
                raise _Refusal(f"{where} has an invalid token {tokens_list[position]!r}") from None
            position += 1
        return values

    points: list[Point] = []
    kinds: list[tuple] = []
    closed = False
    while position < len(tokens_list):
        command = tokens_list[position]
        position += 1
        if closed:
            raise _Refusal(f"{where} continues after Z; use one subpath per shape")
        if command not in "MLHVAZ":
            raise _Refusal(f"{where} supports only absolute M, L, H, V, A and Z commands (found {command!r})")
        if (command == "M") != (not points):
            raise _Refusal(f"{where} must start with one M and use it only once")
        if command == "M":
            x, y = take(2)
            points.append((_coord(x, f"{where} M", tokens), _coord(y, f"{where} M", tokens)))
        elif command == "L":
            x, y = take(2)
            points.append((_coord(x, f"{where} L", tokens), _coord(y, f"{where} L", tokens)))
            kinds.append(("L",))
        elif command == "H":
            (x,) = take(1)
            points.append((_coord(x, f"{where} H", tokens), points[-1][1]))
            kinds.append(("L",))
        elif command == "V":
            (y,) = take(1)
            points.append((points[-1][0], _coord(y, f"{where} V", tokens)))
            kinds.append(("L",))
        elif command == "A":
            rx, ry, rotation, large, sweep, x, y = take(7)
            if rx != ry or rotation != 0 or large not in (0, 1) or sweep not in (0, 1):
                raise _Refusal(f"{where} arcs must be circular (rx = ry, rotation 0) with 0/1 flags")
            radius = _size(rx, f"{where} A radius", tokens)
            points.append((_coord(x, f"{where} A", tokens), _coord(y, f"{where} A", tokens)))
            kinds.append(("A", radius, int(large), int(sweep)))
        else:
            closed = True
            if len(points) > 1 and _close(points[0], points[-1], 1e-9):
                # The final drawn segment already returns to the start and becomes the closing segment.
                points.pop()
            else:
                kinds.append(("L",))
    if len(points) < 2:
        raise _Refusal(f"{where} needs at least two points")
    if closed and len(points) < 3 and all(kind[0] == "L" for kind in kinds):
        raise _Refusal(f"{where} closes fewer than three points")
    if len(points) > MAX_POINTS:
        raise _Refusal(f"{where} exceeds {MAX_POINTS} points")
    return points, kinds, closed


def _primitive_forms(shape: dict[str, Any], kind: str, where: str, tokens: Tokens) -> list[Form]:
    """Translate one authored primitive into transformable construction forms."""
    family_radius = tokens.radius

    def radius_field(default: float) -> float:
        return _size(shape["radius"], f"{where}.radius", tokens, zero=True) if "radius" in shape else default

    if kind == "line":
        a, b = _point(shape["from"], f"{where}.from", tokens), _point(shape["to"], f"{where}.to", tokens)
        return [_path_form(where, [a, b], False, 0.0, tokens)]
    if kind == "polyline":
        raw = shape["points"]
        closed = shape.get("closed", False)
        if not isinstance(closed, bool):
            raise _Refusal(f"{where}.closed must be true or false")
        if not isinstance(raw, list) or not (3 if closed else 2) <= len(raw) <= MAX_POINTS:
            raise _Refusal(f"{where}.points must list {3 if closed else 2} to {MAX_POINTS} points")
        points = [_point(point, f"{where}.points[{index}]", tokens) for index, point in enumerate(raw)]
        return [_path_form(where, points, closed, radius_field(family_radius), tokens)]
    if kind == "path":
        points, kinds, closed = _parse_d(shape["d"], f"{where}.d", tokens)
        return [_path_form(where, points, closed, radius_field(family_radius), tokens, kinds)]
    if kind == "arc":
        center = _point(shape["center"], f"{where}.center", tokens)
        radius = _size(shape["r"], f"{where}.r", tokens)
        start = _integer(shape["start"], f"{where}.start", -720, 720)
        end = _integer(shape["end"], f"{where}.end", -720, 720)
        if not 0 < abs(end - start) < 360:
            raise _Refusal(f"{where} must sweep between 0 and 360 degrees; use a circle for a full ring")
        return [ArcForm(center, radius, math.radians(start), math.radians(end))]
    if kind == "circle":
        if "fit" in shape:
            if set(shape) & {"center", "r"}:
                raise _Refusal(f"{where} uses fit or center/r, not both")
            if _choice(shape["fit"], f"{where}.fit", ("circle",)) == "circle":
                box = tokens.keyline("circle")
                inset = max(tokens.half, tokens.reach - (box[0] - tokens.padding))
                return [CircleForm(tokens.center, (box[2] - box[0]) / 2 - inset)]
        if not {"center", "r"} <= set(shape):
            raise _Refusal(f"{where} needs center and r, or fit")
        return [CircleForm(_point(shape["center"], f"{where}.center", tokens), _size(shape["r"], f"{where}.r", tokens))]
    if kind == "ellipse":
        center = _point(shape["center"], f"{where}.center", tokens)
        return [EllipseForm(center, _size(shape["rx"], f"{where}.rx", tokens), _size(shape["ry"], f"{where}.ry", tokens))]
    if kind in {"rect", "rounded-rect"}:
        default = family_radius if kind == "rounded-rect" else 0.0
        if "fit" in shape:
            if set(shape) & {"x", "y", "w", "h"}:
                raise _Refusal(f"{where} uses fit or x/y/w/h, not both")
            fit = _choice(shape["fit"], f"{where}.fit", ("square", "portrait", "landscape"))
            x0, y0, x1, y1 = tokens.keyline(fit)
            x0, y0, x1, y1 = x0 + tokens.half, y0 + tokens.half, x1 - tokens.half, y1 - tokens.half
        else:
            if not {"x", "y", "w", "h"} <= set(shape):
                raise _Refusal(f"{where} needs x, y, w and h, or fit")
            x0, y0 = _coord(shape["x"], f"{where}.x", tokens), _coord(shape["y"], f"{where}.y", tokens)
            x1 = x0 + _size(shape["w"], f"{where}.w", tokens)
            y1 = y0 + _size(shape["h"], f"{where}.h", tokens)
        return [_path_form(where, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], True, radius_field(default), tokens)]
    if kind == "polygon":
        center = _point(shape["center"], f"{where}.center", tokens)
        radius = _size(shape["r"], f"{where}.r", tokens)
        sides = _integer(shape["sides"], f"{where}.sides", 3, 12)
        rotation = _integer(shape.get("rotation", -90), f"{where}.rotation", -360, 360)
        if rotation % ROTATION_STEP:
            raise _Refusal(f"{where}.rotation must be a multiple of {ROTATION_STEP} degrees")
        points = [_polar(center, radius, math.radians(rotation + index * 360 / sides)) for index in range(sides)]
        return [PathForm(points, [("L",)] * sides, True, radius_field(family_radius))]
    if kind == "gear":
        center = _point(shape["center"], f"{where}.center", tokens)
        outer = _size(shape["r"], f"{where}.r", tokens)
        root = _size(shape["root"], f"{where}.root", tokens)
        teeth = _integer(shape["teeth"], f"{where}.teeth", 4, 16)
        tooth = _number(shape.get("tooth", 0.32), f"{where}.tooth")
        if not root < outer:
            raise _Refusal(f"{where}.root must be smaller than r")
        if not 0.15 <= tooth <= 0.6:
            raise _Refusal(f"{where}.tooth must be a fraction of the tooth period from 0.15 to 0.6")
        period = math.tau / teeth
        flank = 0.1 * period
        points: list[Point] = []
        for index in range(teeth):
            axis = -math.pi / 2 + index * period
            points += [
                _polar(center, root, axis - tooth * period / 2 - flank),
                _polar(center, outer, axis - tooth * period / 2),
                _polar(center, outer, axis + tooth * period / 2),
                _polar(center, root, axis + tooth * period / 2 + flank),
            ]
        return [PathForm(points, [("L",)] * len(points), True, radius_field(min(family_radius, tokens.stroke)))]
    if kind == "chevron":
        x, y = _point(shape["tip"], f"{where}.tip", tokens)
        direction = _choice(shape["dir"], f"{where}.dir", CHEVRON_DIRECTIONS)
        span = _size(shape["span"], f"{where}.span", tokens)
        depth = _size(shape["depth"], f"{where}.depth", tokens) if "depth" in shape else span / 2
        half = span / 2
        points = {
            "up": [(x - half, y + depth), (x, y), (x + half, y + depth)],
            "down": [(x - half, y - depth), (x, y), (x + half, y - depth)],
            "left": [(x + depth, y - half), (x, y), (x + depth, y + half)],
            "right": [(x - depth, y - half), (x, y), (x - depth, y + half)],
        }[direction]
        return [PathForm(points, [("L",), ("L",)], False, radius_field(0.0))]
    if kind == "arrow":
        start, tip = _point(shape["from"], f"{where}.from", tokens), _point(shape["to"], f"{where}.to", tokens)
        shaft = _path_form(where, [start, tip], False, 0.0, tokens)
        start, tip = shaft.points
        head = _size(shape["head"], f"{where}.head", tokens) if "head" in shape else round(tokens.grid / 6 / tokens.snap) * tokens.snap
        if head * 1.5 > _length(_sub(tip, start)):
            raise _Refusal(f"{where}.head is too long for its shaft")
        u = _unit(_sub(tip, start))
        n = _normal(u)
        base = _sub(tip, _mul(u, head))
        arms = [_add(base, _mul(n, head)), tip, _sub(base, _mul(n, head))]
        return [shaft, PathForm(arms, [("L",), ("L",)], False, 0.0)]
    assert kind == "dot"
    diameter = _size(shape["d"], f"{where}.d", tokens) if "d" in shape else tokens.dot
    return [DotForm(_point(shape["at"], f"{where}.at", tokens), diameter / 2)]


# --------------------------------------------------------------------------
# Transforms: rotate -> repeat -> radial -> mirror

Matrix = tuple[float, float, float, float, float, float]  # x' = a x + c y + e, y' = b x + d y + f


def _rotation(degrees: float, about: Point) -> Matrix:
    theta = math.radians(degrees)
    cos, sin = math.cos(theta), math.sin(theta)
    for exact in (0.0, 1.0, -1.0):
        cos = exact if abs(cos - exact) < 1e-12 else cos
        sin = exact if abs(sin - exact) < 1e-12 else sin
    ax, ay = about
    return cos, sin, -sin, cos, ax - cos * ax + sin * ay, ay - sin * ax - cos * ay


def _apply_point(m: Matrix, p: Point) -> Point:
    a, b, c, d, e, f = m
    return _clean(a * p[0] + c * p[1] + e), _clean(b * p[0] + d * p[1] + f)


def _apply(m: Matrix, form: Form) -> Form:
    a, b, c, d, _, _ = m
    determinant = a * d - b * c
    if isinstance(form, PathForm):
        kinds = [kind if kind[0] == "L" or determinant > 0 else ("A", kind[1], kind[2], 1 - kind[3]) for kind in form.kinds]
        return PathForm([_apply_point(m, p) for p in form.points], kinds, form.closed, form.radius)
    if isinstance(form, ArcForm):
        start = math.atan2(b * math.cos(form.a0) + d * math.sin(form.a0), a * math.cos(form.a0) + c * math.sin(form.a0))
        return ArcForm(_apply_point(m, form.center), form.r, start, start + (form.a1 - form.a0) * determinant)
    if isinstance(form, EllipseForm):
        if abs(a) < 1e-9 and abs(d) < 1e-9:
            return EllipseForm(_apply_point(m, form.center), form.ry, form.rx)
        if abs(b) > 1e-9 or abs(c) > 1e-9:
            raise _Refusal("ellipses rotate only in 90-degree steps")
        return EllipseForm(_apply_point(m, form.center), form.rx, form.ry)
    if isinstance(form, CircleForm):
        return CircleForm(_apply_point(m, form.center), form.r)
    return DotForm(_apply_point(m, form.center), form.r)


def _transform(shape: dict[str, Any], forms: list[Form], where: str, tokens: Tokens) -> list[Form]:
    about = _point(shape["about"], f"{where}.about", tokens) if "about" in shape else tokens.center
    if "rotate" in shape:
        degrees = _integer(shape["rotate"], f"{where}.rotate", -345, 345)
        if degrees % ROTATION_STEP:
            raise _Refusal(f"{where}.rotate must be a multiple of {ROTATION_STEP} degrees")
        forms = [_apply(_rotation(degrees, about), form) for form in forms]
    if "repeat" in shape:
        repeat = _fields(shape["repeat"], f"{where}.repeat", ("count", "step"), ())
        count = _integer(repeat["count"], f"{where}.repeat.count", 2, MAX_COPIES)
        dx, dy = _point(repeat["step"], f"{where}.repeat.step", tokens)
        forms = [_apply((1, 0, 0, 1, dx * k, dy * k), form) for k in range(count) for form in forms]
    if "radial" in shape:
        count = _integer(shape["radial"], f"{where}.radial", 2, MAX_COPIES)
        if 360 % count:
            raise _Refusal(f"{where}.radial must divide 360 degrees evenly")
        forms = [_apply(_rotation(k * 360 // count, about), form) for k in range(count) for form in forms]
    if "mirror" in shape:
        axes = _choice(shape["mirror"], f"{where}.mirror", ("x", "y", "xy"))
        ax, ay = about
        flips: list[Matrix] = [(1, 0, 0, 1, 0, 0)]
        if "x" in axes:
            flips.append((-1, 0, 0, 1, 2 * ax, 0))
        if "y" in axes:
            flips.append((1, 0, 0, -1, 0, 2 * ay))
        if axes == "xy":
            flips.append((-1, 0, 0, -1, 2 * ax, 2 * ay))
        forms = [_apply(flip, form) for flip in flips for form in forms]
    return forms


# --------------------------------------------------------------------------
# Construction forms -> centerline geometry


def _endpoint_arc(p0: Point, p1: Point, radius: float, large: int, sweep: int) -> Arc:
    """SVG endpoint arc (rx = ry, no rotation) as a center-parameterized arc."""
    half = _length(_sub(p1, p0)) / 2
    radius = max(radius, half)
    x1p, y1p = (p0[0] - p1[0]) / 2, (p0[1] - p1[1]) / 2
    coefficient = math.sqrt(max(0.0, radius * radius - half * half)) / half
    if large == sweep:
        coefficient = -coefficient
    cxp, cyp = coefficient * y1p, -coefficient * x1p
    center = (cxp + (p0[0] + p1[0]) / 2, cyp + (p0[1] + p1[1]) / 2)
    start = _angle(_sub(p0, center))
    delta = _angle(_sub(p1, center)) - start
    if sweep and delta < 0:
        delta += math.tau
    elif not sweep and delta > 0:
        delta -= math.tau
    if abs(delta) < 1e-9:
        delta = math.tau if sweep else -math.tau
    return Arc(center, radius, start, start + delta)


def _fillet(vertex: Point, incoming: Point, outgoing: Point, radius: float, limit: float) -> tuple[float, Arc | None]:
    """Tangent distance and fillet arc for a corner between two straight segments."""
    a, b = _mul(incoming, -1.0), outgoing
    cosine = max(-1.0, min(1.0, _dot(a, b)))
    interior = math.acos(cosine)
    if radius <= 0 or interior < 1e-6 or math.pi - interior < 1e-6:
        return 0.0, None
    tangent = min(radius / math.tan(interior / 2), limit)
    effective = tangent * math.tan(interior / 2)
    if effective < 1e-6:
        return 0.0, None
    t1 = _add(vertex, _mul(a, tangent))
    center = _add(vertex, _mul(_unit(_add(a, b)), effective / math.sin(interior / 2)))
    turn = 1.0 if _cross(incoming, outgoing) > 0 else -1.0
    start = _angle(_sub(t1, center))
    end = start + turn * (math.pi - interior)
    return tangent, Arc(center, effective, start, end)


def _leaf_sharp(incoming: Point, outgoing: Point) -> bool:
    """Leaf corners: a corner pointing up-right or down-left stays sharp; up-left and down-right round."""
    inside = _add(_mul(incoming, -1.0), outgoing)  # toward the fillet center
    if _length(inside) < 1e-9:
        return False
    pointing = _angle(_mul(inside, -1.0))
    return math.sin(2 * pointing) < -1e-9


def _path_chain(form: PathForm, corner: str = "round") -> Chain:
    points, kinds, closed = form.points, form.kinds, form.closed
    count = len(points)
    segment_count = len(kinds)
    ends = [(points[i], points[(i + 1) % count]) for i in range(segment_count)]
    straight = [kind[0] == "L" for kind in kinds]
    lengths = [_length(_sub(b, a)) for a, b in ends]
    filleted: dict[int, bool] = {}
    for vertex in range(count):
        before, after = vertex - 1, vertex
        if not closed and (before < 0 or after >= segment_count):
            continue
        before %= segment_count
        filleted[vertex] = form.radius > 0 and straight[before] and straight[after]
        if filleted[vertex] and corner != "round":
            incoming = _unit(_sub(ends[before][1], ends[before][0]))
            outgoing = _unit(_sub(ends[after][1], ends[after][0]))
            filleted[vertex] = corner == "chamfer" or (corner == "leaf" and not _leaf_sharp(incoming, outgoing))
    tangents: dict[int, float] = {}
    arcs: dict[int, Arc] = {}
    for vertex, eligible in filleted.items():
        if not eligible:
            continue
        before, after = (vertex - 1) % segment_count, vertex
        share_in = 0.5 if filleted.get((vertex - 1) % count, False) else 1.0
        share_out = 0.5 if filleted.get((vertex + 1) % count, False) else 1.0
        limit = min(lengths[before] * share_in, lengths[after] * share_out)
        incoming = _unit(_sub(ends[before][1], ends[before][0]))
        outgoing = _unit(_sub(ends[after][1], ends[after][0]))
        tangent, arc = _fillet(points[vertex], incoming, outgoing, form.radius, limit)
        if arc is not None:
            tangents[vertex], arcs[vertex] = tangent, arc
    segments: list[Segment] = []
    for index in range(segment_count):
        start, end = ends[index]
        if straight[index]:
            u = _unit(_sub(end, start))
            trimmed_start = _add(start, _mul(u, tangents.get(index, 0.0)))
            trimmed_end = _sub(end, _mul(u, tangents.get((index + 1) % count, 0.0)))
            if _length(_sub(trimmed_end, trimmed_start)) > 1e-7:
                segments.append(Line(trimmed_start, trimmed_end))
        else:
            segments.append(_endpoint_arc(start, end, kinds[index][1], kinds[index][2], kinds[index][3]))
        next_vertex = (index + 1) % count
        if next_vertex in arcs and (closed or index + 1 < segment_count):
            arc = arcs[next_vertex]
            segments.append(Line(_start(arc), _end(arc)) if corner == "chamfer" else arc)
    return Chain(tuple(segments), closed)


def _form_shape(form: Form, corner: str = "round") -> Shape:
    if isinstance(form, PathForm):
        return _path_chain(form, corner)
    if isinstance(form, ArcForm):
        return Chain((Arc(form.center, form.r, form.a0, form.a1),), False)
    if isinstance(form, CircleForm):
        return Circle(form.center, form.r)
    if isinstance(form, EllipseForm):
        return Ellipse(form.center, form.rx, form.ry)
    return Dot(form.center, form.r)


# --------------------------------------------------------------------------
# Family compilation


def _is_closed(shape: Shape) -> bool:
    return not isinstance(shape, Chain) or shape.closed


def _parse_item(shape: Any, where: str, index: int, tokens: Tokens, variants: tuple[str, ...]) -> Item | None:
    if not isinstance(shape, dict):
        raise _Refusal(f"{where} must be an object")
    kind = shape.get("type")
    if kind not in PRIMITIVES:
        raise _Refusal(f"{where}.type must be one of: {', '.join(PRIMITIVES)}")
    required, optional, default_role = PRIMITIVES[kind]
    _fields(shape, where, required | {"type"}, optional | COMMON_FIELDS)
    label = f"'{_name(shape['id'], f'{where}.id')}'" if "id" in shape else f"shape {index} ({kind})"
    role = _choice(shape["role"], f"{where}.role", ROLES) if "role" in shape else default_role
    item_variants = tuple(variants)
    if "variants" in shape:
        raw = shape["variants"]
        if not isinstance(raw, list) or not raw or len(set(raw)) != len(raw):
            raise _Refusal(f"{where}.variants must be a non-empty list without repeats")
        for value in raw:
            _choice(value, f"{where}.variants", variants)
        item_variants = tuple(variant for variant in variants if variant in raw)
    minimum = _choice(shape.get("min_detail", "low"), f"{where}.min_detail", DETAIL_LEVELS)
    forms = _transform(shape, _primitive_forms(shape, kind, where, tokens), where, tokens)
    shapes = [_form_shape(form, tokens.corner) for form in forms]
    if role == "auto":
        role = "body" if all(_is_closed(item) for item in shapes) else "stroke"
    duotone_fill = shape.get("duotone_fill", role in {"body", "accent"})
    if not isinstance(duotone_fill, bool):
        raise _Refusal(f"{where}.duotone_fill must be true or false")
    aperture = shape.get("aperture")
    if aperture is not None and (not isinstance(aperture, bool) or not tokens.aperture):
        raise _Refusal(f"{where}.aperture must be true or false, and applies only with tokens.aperture")
    junction = shape.get("junction", True)
    if not isinstance(junction, bool) or ("junction" in shape and not tokens.junction_gap):
        raise _Refusal(f"{where}.junction must be true or false, and applies only with tokens.junction_gap")
    if role == "accent":
        if not all(_is_closed(item) for item in shapes):
            raise _Refusal(f"{where}: an accent must be a closed shape or a dot")
        if aperture:
            raise _Refusal(f"{where}: an accent cannot host the aperture")
    if aperture and not all(_as_chain(item) is not None and _is_closed(item) for item in shapes):
        raise _Refusal(f"{where}: only closed paths, polygons, rects and circles can host the aperture")
    if DETAIL_LEVELS.index(minimum) > DETAIL_LEVELS.index(tokens.detail):
        return None
    if role == "body" and any(isinstance(item, Dot) for item in shapes):
        raise _Refusal(f"{where}: a dot cannot be a body; use a circle")
    return Item(label, role, item_variants, duotone_fill, shapes, aperture, junction)


def _open_from(tokens: Tokens, sizes: list[int]) -> int | None:
    """Smallest target size at which every open-form gap paints at least 1 CSS px.

    Smaller targets get an optical set with the gaps closed: a sub-pixel gap blurs into a
    broken-looking stroke, and recognition outranks voice.
    """
    gaps = [gap for gap in (tokens.aperture, tokens.junction_gap) if gap]
    if not gaps:
        return None
    narrowest = min(gaps)
    visible = [size for size in sizes if narrowest * size / tokens.grid >= 1 - 1e-9]
    if not visible:
        raise _Refusal(
            f"open-form gaps of {narrowest:g} units paint under 1 CSS px at every target size up to {sizes[-1]} px; "
            f"widen them to at least {math.ceil(tokens.grid / sizes[-1] / tokens.snap) * tokens.snap:g} units"
        )
    return visible[0] if visible[0] > sizes[0] else None


def compile_family(spec: dict[str, Any]) -> Family:
    """Validate a parsed spec and construct every glyph; raises SpecError listing every refusal."""
    problems: list[str] = []
    try:
        top = _fields(
            spec, "spec", ("schema", "family", "tokens", "metadata", "glyphs"),
            ("variants", "target_sizes", "sheet"),
        )
        if top["schema"] != SCHEMA:
            raise _Refusal(f"spec.schema must be {SCHEMA!r}")
        family_name = _name(top["family"], "spec.family")
        tokens = _parse_tokens(top["tokens"])
        variants = tuple(VARIANTS if tokens.secondary_opacity is not None else VARIANTS[:2])
        if "variants" in top:
            raw = top["variants"]
            if not isinstance(raw, list) or not raw or len(set(raw)) != len(raw):
                raise _Refusal("spec.variants must be a non-empty list without repeats")
            for value in raw:
                _choice(value, "spec.variants", VARIANTS)
            if "duotone" in raw and tokens.secondary_opacity is None:
                raise _Refusal("the duotone variant needs tokens.secondary_opacity")
            variants = tuple(variant for variant in VARIANTS if variant in raw)
        sizes = top.get("target_sizes", [16, 20, 24, 32])
        if (not isinstance(sizes, list) or not sizes or len(set(sizes)) != len(sizes)
                or any(isinstance(size, bool) or not isinstance(size, int) or not 8 <= size <= 256 for size in sizes)):
            raise _Refusal("spec.target_sizes must list unique integer CSS pixel sizes from 8 to 256")
        sizes = sorted(sizes)
        if tokens.stroke * sizes[0] / tokens.grid < 0.5:
            raise _Refusal(
                f"stroke {tokens.stroke:g} renders below 0.5 CSS px at {sizes[0]} px; raise the stroke or the smallest target"
            )
        if tokens.detail_stroke * sizes[0] / tokens.grid < 0.5:
            raise _Refusal(
                f"tokens.contrast leaves {tokens.detail_stroke:g}-unit details, below 0.5 CSS px at {sizes[0]} px; raise it"
            )
        open_from = _open_from(tokens, sizes)
        meta = _fields(top["metadata"], "metadata", ("creator", "reviewed"), ("license", "source", "accessibility_owner"))
        creator = _text(meta["creator"], "metadata.creator")
        reviewed = meta["reviewed"]
        try:
            if not isinstance(reviewed, str) or date.fromisoformat(reviewed).isoformat() != reviewed:
                raise ValueError
        except ValueError:
            raise _Refusal("metadata.reviewed must be an ISO date (YYYY-MM-DD)") from None
        if date.fromisoformat(reviewed) > date.today():
            raise _Refusal("metadata.reviewed must not be a future date")
        license_text = _text(meta.get("license", "project-owned"), "metadata.license")
        source = _text(meta.get("source", f"glyph.py family {family_name}"), "metadata.source")
        owner = _text(
            meta.get("accessibility_owner", "owning labelled control; SVG decorative (aria-hidden)"),
            "metadata.accessibility_owner",
        )
        glyph_specs = top["glyphs"]
        if not isinstance(glyph_specs, list) or not glyph_specs:
            raise _Refusal("spec.glyphs must be a non-empty list")
        if len(glyph_specs) > MAX_GLYPHS:
            raise _Refusal(f"family has {len(glyph_specs)} glyphs; the limit is {MAX_GLYPHS}")
    except _Refusal as refusal:
        raise SpecError([str(refusal)]) from None

    glyphs: list[Glyph] = []
    seen: set[str] = set()
    for index, raw_glyph in enumerate(glyph_specs):
        where = f"glyphs[{index}]"
        try:
            glyph_value = _fields(raw_glyph, where, ("name", "role", "shapes"), ("keyline", "detail_budget"))
            name = _name(glyph_value["name"], f"{where}.name")
            where = f"glyph '{name}'"
            if name in seen:
                raise _Refusal(f"{where} is defined twice")
            seen.add(name)
            role = _text(glyph_value["role"], f"{where}.role")
            keyline = _choice(glyph_value["keyline"], f"{where}.keyline", KEYLINES) if "keyline" in glyph_value else None
            budget = _text(glyph_value["detail_budget"], f"{where}.detail_budget") if "detail_budget" in glyph_value else None
            raw_shapes = glyph_value["shapes"]
            if not isinstance(raw_shapes, list) or not raw_shapes:
                raise _Refusal(f"{where}.shapes must be a non-empty list")
            if len(raw_shapes) > MAX_SHAPES:
                raise _Refusal(f"{where} has {len(raw_shapes)} shapes; the limit is {MAX_SHAPES}")
        except _Refusal as refusal:
            problems.append(str(refusal))
            continue
        items: list[Item] = []
        refused = len(problems)
        for shape_index, raw_shape in enumerate(raw_shapes):
            try:
                item = _parse_item(raw_shape, f"{where} shapes[{shape_index}]", shape_index, tokens, variants)
            except _Refusal as refusal:
                problems.append(str(refusal))
                continue
            if item is not None:
                items.append(item)
        if len(problems) > refused:
            continue
        expanded = sum(len(item.shapes) for item in items)
        if expanded > MAX_EXPANDED:
            problems.append(f"{where} expands to {expanded} shapes after repeats; the limit is {MAX_EXPANDED}")
            continue
        if not items:
            problems.append(f"{where} has no shapes at detail density '{tokens.detail}'")
            continue
        for variant in variants:
            if not any(variant in item.variants for item in items):
                problems.append(f"{where} draws nothing in the {variant} variant")
        accents = [(item, shape) for item in items if item.role == "accent" for shape in item.shapes]
        if accents and tokens.accent is None:
            problems.append(f"{where} uses role \"accent\"; declare tokens.accent, the one meaning every accent carries")
        if len(accents) > 1:
            problems.append(f"{where} has {len(accents)} accent shapes; the family accent is one small element per glyph")
        for item, shape in accents:
            box = _shape_bounds(shape)
            reach = 0.0 if isinstance(shape, Dot) else 2 * tokens.half
            span = (tokens.grid - 2 * tokens.padding) * ACCENT_SPAN
            if max(box[2] - box[0], box[3] - box[1]) + reach > span + 1e-9:
                problems.append(f"{where} {item.label}: an accent spans at most a third of the live area ({span:g} units)")
        glyphs.append(Glyph(name, role, keyline, budget, items))

    tabs: list[str] = []
    if "sheet" in top:
        try:
            sheet = _fields(top["sheet"], "spec.sheet", (), ("tabs",))
            raw_tabs = sheet.get("tabs", [])
            if not isinstance(raw_tabs, list) or len(raw_tabs) > 6 or len(set(raw_tabs)) != len(raw_tabs):
                raise _Refusal("spec.sheet.tabs must list at most six distinct glyph names")
            for tab in raw_tabs:
                if tab not in seen:
                    raise _Refusal(f"spec.sheet.tabs names unknown glyph {tab!r}")
            tabs = list(raw_tabs)
        except _Refusal as refusal:
            problems.append(str(refusal))
    if problems:
        raise SpecError(problems)
    family = Family(
        family_name, tokens, variants, sizes, creator, reviewed, license_text, source, owner, glyphs,
        tabs or [glyph.name for glyph in glyphs[:5]], open_from=open_from,
    )
    for glyph in glyphs:
        try:
            if tokens.aperture:
                glyph.aperture = _plan_aperture(family, glyph)
            _check_glyph(family, glyph)
        except _Refusal as refusal:
            message = str(refusal)
            problems.append(message if message.startswith("glyph '") else f"glyph '{glyph.name}': {message}")
        except (ArithmeticError, ValueError, IndexError) as error:
            problems.append(f"glyph '{glyph.name}': geometry cannot be constructed ({error})")
    if problems:
        raise SpecError(problems)
    return family


# --------------------------------------------------------------------------
# Variant construction


@dataclass(frozen=True)
class Element:
    kind: str  # stroke | dot | fill | ring (expanded closed stroke: outer edge, then inner edges reversed)
    shapes: tuple[Shape, ...]  # fill: outer first, then even-odd cut-outs


RANK = {"body": 3, "accent": 3, "stroke": 2, "detail": 1}


def _item_half(tokens: Tokens, item: Item, variant: str) -> float:
    """Half stroke of an item: inner details draw lighter under tokens.contrast, except as solid cut-outs."""
    if item.role == "detail" and tokens.contrast < 1 and variant != "solid":
        return tokens.detail_stroke / 2
    return tokens.half


def _accent_region(shape: Shape, tokens: Tokens) -> Shape:
    """An accent fills the area its outline would paint: the closed shape grown by half a stroke."""
    if isinstance(shape, Dot):
        return Circle(shape.c, shape.r)
    grown = _grow(shape, tokens.half, tokens.linejoin)
    if grown is None:
        raise _Refusal("an accent outline cannot be grown; enlarge it")
    return grown


def _apply_junctions(family: Family, glyph: Glyph, present: list[tuple[int, Item]],
                     pieces: dict[int, list[list[Shape | Opened]]], variant: str) -> None:
    """Open strokes stop ``junction_gap`` short of the strokes they meet or cross; contours stay whole.

    At a T the stroke whose end touches gives way; at a crossing or a shared end the stroke
    behind gives way (detail behind stroke behind body and accent, later behind earlier).
    """
    tokens = family.tokens
    entries = [
        (index, item, shape_index, shape)
        for index, item in present if item.junction
        for shape_index, shape in enumerate(item.shapes)
    ]
    for index, item, shape_index, shape in entries:
        if not isinstance(shape, Chain) or shape.closed:
            continue
        half_a = _item_half(tokens, item, variant)
        length = _chain_length(shape)
        box_a = _shape_bounds(shape)
        windows: list[tuple[float, float]] = []
        for other_index, other, _, obstacle in entries:
            if other_index == index:
                continue
            half_b = obstacle.r if isinstance(obstacle, Dot) else _item_half(tokens, other, variant)
            reach = half_b + tokens.junction_gap + max(half_a, tokens.cap_extension(half_a))
            limit = half_b + tokens.junction_gap
            touch = half_a + half_b + 1e-6
            probe = _end_probe(tokens, half_a)
            box_b = _shape_bounds(obstacle)
            if (box_a[0] - reach > box_b[2] or box_b[0] - reach > box_a[2]
                    or box_a[1] - reach > box_b[3] or box_b[1] - reach > box_a[3]):
                continue

            def clearance(s: float, chain: Chain = shape, target: Shape = obstacle, limit: float = limit,
                          probe: list[Point] = probe) -> float:
                """Clearance of a stroke end cut at ``s``, measured from its painted corners and cap, not its centerline."""
                point, along = _chain_point(chain, s), _chain_tangent(chain, s)
                across = _normal(along)
                return min(
                    _shape_distance(_add(point, _add(_mul(across, a), _mul(along, b))), target) for a, b in probe
                ) - limit

            for low, high in _below_windows(length, clearance):
                steps = max(4, math.ceil((high - low) / 0.02))
                distance, contact = min(
                    (_shape_distance(_chain_point(shape, low + (high - low) * k / steps), obstacle), low + (high - low) * k / steps)
                    for k in range(steps + 1)
                )
                if distance > touch:
                    continue  # near but not touching: the gap lint's business, not a junction
                # The contact sits at an end when the closest approach is within the other stroke's half width of it.
                a_end = min(contact, length - contact) <= half_b + 1e-6
                if isinstance(obstacle, Chain) and not obstacle.closed:
                    point = _chain_point(shape, contact)
                    b_end = any(
                        _length(_sub(end, point)) <= half_a + 1e-6
                        for end in (_start(obstacle.segs[0]), _end(obstacle.segs[-1]))
                    )
                    behind = (RANK[item.role], -index) < (RANK[other.role], -other_index)
                    gives_way = a_end if a_end != b_end else behind
                else:
                    gives_way = True
                if gives_way:
                    windows.append(_settle_window(tokens, shape, length, half_a, obstacle, limit, low, high))
        if not windows:
            continue
        windows.sort()
        kept: list[Shape | Opened] = []
        position = 0.0
        for low, high in windows + [(length, length)]:
            if low - position >= tokens.stroke - 1e-9:
                kept.append(_chain_slice(shape, position, low))
            position = max(position, high)
        if not kept:
            raise _Refusal(
                f"glyph '{glyph.name}' {item.label}: the junction gap removes this stroke entirely; "
                "lengthen it or give it \"junction\": false"
            )
        pieces[index][shape_index] = kept


def _settle_window(tokens: Tokens, chain: Chain, length: float, half: float, obstacle: Shape, limit: float,
                   low: float, high: float) -> tuple[float, float]:
    """Widen a junction window until the painted stroke beside each cut, joins and neighbouring segments
    included, keeps the full gap; a cut just past a corner otherwise lets the next segment's band reach in."""
    step = 0.05

    def tight(start: float, end: float) -> bool:
        if end - start < 1e-6:
            return False
        try:
            outline = _stroke_outline(_chain_slice(chain, start, end), half, tokens.linecap, tokens.linejoin, tokens.cut)
        except _Refusal:
            return True
        return min(_shape_distance(point, obstacle) for point in _shape_points(outline, 0.05)) < limit - 1e-6

    reach = 2 * tokens.stroke + half
    while low > 1e-9 and tight(max(0.0, low - reach), low):
        low = max(0.0, low - step)
    while high < length - 1e-9 and tight(high, min(length, high + reach)):
        high = min(length, high + step)
    return low, high


def _clock_position(contour: Chain, hour: int) -> float:
    """Arc length where a ray from the contour's box center toward ``hour`` o'clock leaves the contour."""
    box = _shape_bounds(contour)
    center = ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
    angle = math.radians(30 * hour - 90)
    direction = (math.cos(angle), math.sin(angle))
    best: tuple[float, float] | None = None
    position = 0.0
    for segment in contour.segs:
        size = _segment_length(segment)
        samples = _segment_points(segment, 0.05)
        for index in range(len(samples) - 1):
            p, q = samples[index], samples[index + 1]
            edge = _sub(q, p)
            denominator = _cross(direction, edge)
            if abs(denominator) < 1e-12:
                continue
            t = _cross(_sub(p, center), edge) / denominator
            u = _cross(_sub(p, center), direction) / denominator
            if t > 0 and -1e-9 <= u <= 1 + 1e-9 and (best is None or t > best[0] + 1e-9):
                best = (t, position + size * (index + u) / (len(samples) - 1))
        position += size
    return best[1] if best is not None else 0.0


def _within_one_segment(contour: Chain, low: float, high: float, straight: bool) -> bool:
    """Whether arc lengths low..high lie inside one segment (one straight run when ``straight``), never across a corner."""
    total = _chain_length(contour)
    start = low % total
    end = start + (high - low)
    position = 0.0
    for segment in contour.segs:
        size = _segment_length(segment)
        if isinstance(segment, Line) or not straight:
            for shift in (0.0, total):
                if position + shift - 1e-9 <= start and end <= position + shift + size + 1e-9:
                    return True
        position += size
    return False


def _plan_aperture(family: Family, glyph: Glyph) -> tuple[int, int, Opened] | None:
    """Place the family's one signature break on the glyph's largest closed body.

    The gap centers where the ``aperture_at`` clock direction leaves the contour, slides to the
    nearest straight run that holds it (within a quarter turn) or else the nearest single curve,
    never straddles a corner, and never sits within a stroke of another shape, so it cannot read
    as a junction or break a recognizable attachment.
    """
    tokens = family.tokens
    hosts = []
    for item_index, item in enumerate(glyph.items):
        if item.aperture is False or item.role == "accent" or (item.aperture is None and item.role != "body"):
            continue
        for shape_index, shape in enumerate(item.shapes):
            # A circle's half arcs meet a quarter turn either side of the clock position, so the gap never straddles a seam.
            contour = _as_chain(shape, math.radians(30 * tokens.aperture_at - 180))
            if contour is not None and contour.closed:
                area = abs(_signed_area(_shape_points(contour)))
                hosts.append(((not item.aperture, -round(area, 6), item_index, shape_index), contour))
    if not hosts:
        return None
    (_, _, item_index, shape_index), contour = min(hosts, key=lambda host: host[0])
    half = tokens.half
    total = _chain_length(contour)
    span = tokens.aperture / math.cos(tokens.cut) + (2 * half if tokens.cap_extension(half) == half else 0.0)
    margin = half * abs(math.tan(tokens.cut))
    if span + 2 * margin >= total / 3:
        family.warnings.append(f"{glyph.name}: its contour is too small for a {_fmt(tokens.aperture)}-unit aperture")
        return None
    others = [
        (shape, shape.r if isinstance(shape, Dot) else _item_half(tokens, item, "outline"))
        for index, item in enumerate(glyph.items)
        for position, shape in enumerate(item.shapes)
        if (index, position) != (item_index, shape_index)
    ]
    target = _clock_position(contour, tokens.aperture_at)
    step = tokens.snap / 2
    deltas = [0.0] + [sign * k * step for k in range(1, int(total / 2 / step) + 1) for sign in (1, -1)]
    for straight, limit in ((True, total / 4), (False, total / 2)):
        for delta in deltas:
            if abs(delta) > limit:
                break
            low = target + delta - span / 2
            high = low + span
            if not _within_one_segment(contour, low - margin, high + margin, straight):
                continue
            region = _chain_slice(contour, low - tokens.stroke, high + tokens.stroke)
            samples = _shape_points(region, 0.1)
            if any(min(_shape_distance(p, shape) for p in samples) < half + other_half + tokens.stroke - 1e-9
                   for shape, other_half in others):
                continue
            opened = Opened(contour, _chain_slice(contour, high, low + total), _chain_slice(contour, low, high))
            return item_index, shape_index, opened
    family.warnings.append(
        f"{glyph.name}: no clear place for the aperture near {tokens.aperture_at} o'clock; its contour stays closed"
    )
    return None


def _voiced_items(family: Family, glyph: Glyph, variant: str,
                  open_forms: bool = True) -> list[tuple[Item, list[Shape | Opened]]]:
    """Each item present in ``variant`` with its shapes after junction gaps and the aperture."""
    key = ("voiced", variant, open_forms)
    if key not in glyph.cache:
        glyph.cache[key] = _voice_items(family, glyph, variant, open_forms)
    return glyph.cache[key]


def _voice_items(family: Family, glyph: Glyph, variant: str, open_forms: bool) -> list[tuple[Item, list[Shape | Opened]]]:
    present = [(index, item) for index, item in enumerate(glyph.items) if variant in item.variants]
    pieces: dict[int, list[list[Shape | Opened]]] = {index: [[shape] for shape in item.shapes] for index, item in present}
    if open_forms and family.tokens.junction_gap:
        _apply_junctions(family, glyph, present, pieces, variant)
    if open_forms and glyph.aperture is not None and glyph.aperture[0] in pieces:
        item_index, shape_index, opened = glyph.aperture
        pieces[item_index][shape_index] = [opened]
    return [(item, [shape for group in pieces[index] for shape in group]) for index, item in present]


def _outline_elements(family: Family, glyph: Glyph, variant: str, open_forms: bool = True) -> list[Element]:
    tokens = family.tokens
    elements: list[Element] = []
    for item, shapes in _voiced_items(family, glyph, variant, open_forms):
        half = _item_half(tokens, item, variant)
        for shape in shapes:
            if item.role == "accent" and variant == "outline":
                elements.append(Element("fill", (_accent_region(shape, tokens),)))  # type: ignore[arg-type]
                continue
            if isinstance(shape, Opened):
                shape = shape.drawn
            if isinstance(shape, Dot):
                elements.append(Element("fill", (Circle(shape.c, shape.r),)) if tokens.expanded else Element("dot", (shape,)))
            elif not tokens.expanded:
                elements.append(Element("stroke", (shape,)))
            elif isinstance(shape, Chain) and not shape.closed:
                outline = _stroke_outline(shape, half, tokens.linecap, tokens.linejoin, tokens.cut)
                elements.append(Element("fill", (outline,)))
            else:
                # One nonzero path, inner edge reversed: the hole winds to zero, and a loop the inner
                # offset makes at a tight corner winds to two and stays painted instead of punching a hole.
                ring = (_grow(shape, half, tokens.linejoin), _shrink(shape, half, tokens.linejoin))
                elements.append(Element("ring", tuple(part for part in ring if part is not None)))
    return elements


def _solid_elements(family: Family, glyph: Glyph, open_forms: bool = True) -> list[Element]:
    key = ("solid", open_forms)
    if key not in glyph.cache:
        glyph.cache[key] = _build_solid(family, glyph, open_forms)
    return list(glyph.cache[key])


def _build_solid(family: Family, glyph: Glyph, open_forms: bool) -> list[Element]:
    tokens = family.tokens
    half, cap, join, cut = tokens.half, tokens.linecap, tokens.linejoin, tokens.cut
    masses: list[tuple[str, Shape, list[tuple[str, Shape]]]] = []  # (label, outer, cut-outs)
    positives: list[tuple[str, Element]] = []
    details: list[tuple[str, Shape, bool]] = []  # (label, cut-out, is accent)
    order: list[tuple[str, int]] = []
    for item, shapes in _voiced_items(family, glyph, "solid", open_forms):
        for shape in shapes:
            if item.role == "body":
                if isinstance(shape, Opened):
                    outer: Shape | None = _notched_mass(shape, half, cap, join, cut)
                else:
                    closed = shape if _is_closed(shape) else _closed_by_chord(shape)  # type: ignore[arg-type]
                    outer = _grow(closed, half, join)
                if outer is None:
                    raise _Refusal(f"glyph '{glyph.name}' {item.label}: the solid outline collapses")
                masses.append((item.label, outer, []))
                order.append(("mass", len(masses) - 1))
                continue
            if isinstance(shape, Opened):
                shape = shape.drawn
            if item.role == "accent":
                details.append((item.label, _accent_region(shape, tokens), True))
            elif item.role == "detail":
                if isinstance(shape, Dot):
                    cut_out: Shape | None = Circle(shape.c, shape.r)
                elif _is_closed(shape):
                    cut_out = _grow(shape, half, join)
                else:
                    cut_out = _stroke_outline(shape, half, cap, join, cut)  # type: ignore[arg-type]
                if cut_out is None:
                    raise _Refusal(f"glyph '{glyph.name}' {item.label}: the solid cut-out collapses")
                details.append((item.label, cut_out, False))
            else:
                if isinstance(shape, Dot):
                    element = Element("fill", (Circle(shape.c, shape.r),))
                elif isinstance(shape, Chain) and not shape.closed:
                    element = Element("fill", (_stroke_outline(shape, half, cap, join, cut),))
                else:
                    grown = _grow(shape, half, join)
                    inner = _shrink(shape, half, join)
                    element = Element("fill", tuple(part for part in (grown, inner) if part is not None))
                positives.append((item.label, element))
                order.append(("positive", len(positives) - 1))
    polygons = [_shape_points(outer) for _, outer, _ in masses]
    areas = [abs(_signed_area(points)) for points in polygons]
    threshold = tokens.grid / family.target_sizes[0]
    accents: list[Element] = []
    for label, cut_out, accent in details:
        cut_points = _shape_points(cut_out)
        containing = [
            index for index, polygon in enumerate(polygons)
            if all(_inside(point, polygon) for point in cut_points)
        ]
        if not containing:
            touching = [masses[index][0] for index, polygon in enumerate(polygons) if any(_inside(point, polygon) for point in cut_points)]
            if touching:
                raise _Refusal(
                    f"glyph '{glyph.name}' {label}: its solid cut-out crosses the edge of {touching[0]}; "
                    "shorten it or limit it with \"variants\""
                )
            if accent:
                accents.append(Element("fill", (cut_out,)))  # an accent on open ground stays a positive mark
                continue
            raise _Refusal(
                f"glyph '{glyph.name}' {label}: this detail lies outside every body in the solid variant; "
                "give it role \"stroke\" or limit it with \"variants\""
            )
        host = min(containing, key=lambda index: (areas[index], index))
        clearance = _boundary_distance(cut_points, polygons[host])
        if clearance < 1e-6:
            raise _Refusal(f"glyph '{glyph.name}' {label}: its solid cut-out touches the edge of {masses[host][0]}")
        if clearance < threshold - 1e-6:
            family.warnings.append(
                f"{glyph.name} solid: cut-out {label} leaves {clearance * family.target_sizes[0] / tokens.grid:.2f} px of "
                f"{masses[host][0]} at {family.target_sizes[0]} px; the sliver can blur away"
            )
        for other_label, other in masses[host][2]:
            other_points = _shape_points(other)
            if (any(_inside(point, other_points) for point in cut_points)
                    or any(_inside(point, cut_points) for point in other_points)):
                raise _Refusal(
                    f"glyph '{glyph.name}': solid cut-outs {other_label} and {label} overlap; even-odd would refill "
                    "the overlap, so merge them into one shape or separate them"
                )
        masses[host][2].append((label, cut_out))
    elements: list[Element] = []
    for kind, index in order:
        if kind == "mass":
            _, outer, cuts = masses[index]
            elements.append(Element("fill", (outer, *(cut for _, cut in cuts))))
        else:
            elements.append(positives[index][1])
    return elements + accents


def _duotone_secondary(glyph: Glyph) -> list[Element]:
    regions: list[tuple[Shape, list[Shape]]] = []
    holes: list[Shape] = []
    for item in glyph.items:
        if "duotone" not in item.variants:
            continue
        for shape in item.shapes:
            if item.duotone_fill and not isinstance(shape, Dot):
                closed = shape if _is_closed(shape) else _closed_by_chord(shape)  # type: ignore[arg-type]
                regions.append((closed, []))
            elif item.role == "detail" and _is_closed(shape) and not isinstance(shape, Dot):
                holes.append(shape)
    polygons = [_shape_points(region) for region, _ in regions]
    for hole in holes:
        hole_points = _shape_points(hole)
        for index, polygon in enumerate(polygons):
            if all(_inside(point, polygon) for point in hole_points):
                regions[index][1].append(hole)
                break
    return [Element("fill", (region, *cuts)) for region, cuts in regions]


def _variant_elements(family: Family, glyph: Glyph, variant: str, small: bool = False) -> list[Element]:
    if variant == "outline":
        return _outline_elements(family, glyph, "outline", not small)
    if variant == "solid":
        return _solid_elements(family, glyph, not small)
    return _duotone_secondary(glyph) + _outline_elements(family, glyph, "duotone", not small)


def _check_glyph(family: Family, glyph: Glyph) -> None:
    """Refuse geometry outside the live area and pre-build the solid variant to surface cut-out faults."""
    tokens = family.tokens
    live = tokens.live
    for item in glyph.items:
        for shape in item.shapes:
            box = _shape_bounds(shape)
            reach = 0.0 if isinstance(shape, Dot) else tokens.reach
            painted = (box[0] - reach, box[1] - reach, box[2] + reach, box[3] + reach)
            over = max(live[0] - painted[0], live[1] - painted[1], painted[2] - live[2], painted[3] - live[3])
            # SVG arcs are re-derived from 3-decimal endpoints, so an arc may land
            # up to ~0.001 beyond its exact extreme; keep arcs clear of the edge.
            curved = isinstance(shape, Chain) and any(isinstance(segment, Arc) for segment in shape.segs)
            if over > (-ARC_CLEARANCE if curved else 1e-7):
                where = f"{_fmt(live[0])}..{_fmt(live[2])}"
                raise _Refusal(
                    (f"glyph '{glyph.name}' {item.label} paints {over:.3g} units outside the live area {where}"
                     if over > 1e-7 else
                     f"glyph '{glyph.name}' {item.label} touches the live-area edge {where}; curves need "
                     f"{ARC_CLEARANCE:g} units of clearance because SVG arcs are re-derived from rounded endpoints")
                    + (" (square caps are bounded by their diagonal reach)" if tokens.linecap == "square" else "")
                )
    if "solid" in family.variants:
        _solid_elements(family, glyph)
    if tokens.character:
        _check_painted(family, glyph)
    _lint_glyph(family, glyph)


def _painted_bounds(element: Element, tokens: Tokens) -> tuple[float, float, float, float]:
    """An element's bounds exactly as asset_quality.py measures the serialized SVG (3-decimal coordinates)."""
    shape = element.shapes[0]
    if len(element.shapes) == 1 and isinstance(shape, (Circle, Ellipse, Dot)):
        rx, ry = (shape.rx, shape.ry) if isinstance(shape, Ellipse) else (shape.r, shape.r)
        cx, cy, rx, ry = (float(_fmt(value)) for value in (shape.c[0], shape.c[1], rx, ry))
        box = (cx - rx, cy - ry, cx + rx, cy + ry)
    else:
        _, measured, error = _path_geometry("".join(_shape_d(part) for part in element.shapes))
        if error or measured is None:
            raise _Refusal(f"painted geometry cannot be bounded ({error})")
        box = measured
    reach = tokens.reach if element.kind == "stroke" else 0.0
    return box[0] - reach, box[1] - reach, box[2] + reach, box[3] + reach


def _check_painted(family: Family, glyph: Glyph) -> None:
    """Character geometry is bounded as painted: angled cuts, miters and expanded curves can pass the centerline check."""
    tokens = family.tokens
    live = tokens.live
    where = f"{_fmt(live[0])}..{_fmt(live[2])}"
    for small in family.sets():
        for variant in family.variants:
            for element in _variant_elements(family, glyph, variant, small):
                box = _painted_bounds(element, tokens)
                over = max(live[0] - box[0], live[1] - box[1], box[2] - live[2], box[3] - live[3])
                if over > 1e-7:
                    raise _Refusal(
                        f"glyph '{glyph.name}' {variant}{' small' if small else ''}: painted geometry reaches "
                        f"{over:.3g} units past the live area {where}; angled terminals and miter joins reach past "
                        "their endpoints and corners, and expanded curves are rebuilt from rounded endpoints"
                    )


def _lint_glyph(family: Family, glyph: Glyph) -> None:
    """Optical warnings the validator cannot see: keyline size and near-miss gaps, on painted outlines."""
    for small in family.sets():
        _lint_set(family, glyph, small)


def _lint_set(family: Family, glyph: Glyph, small: bool) -> None:
    """Lint one optical set as drawn: open forms on in the main set, closed in the small set."""
    tokens = family.tokens
    scale = tokens.grid / 24
    smallest = (family.small_sizes if small else family.main_sizes)[0]
    painted = []
    for item, shapes in _voiced_items(family, glyph, "outline", not small):
        for shape in shapes:
            if isinstance(shape, Opened):
                shape = shape.drawn
            if item.role == "accent":
                loops = [_shape_points(_accent_region(shape, tokens), 0.3)]
            else:
                loops = _painted_loops(shape, tokens, _item_half(tokens, item, "outline"))
            points = [point for loop in loops for point in loop]
            xs, ys = [p[0] for p in points], [p[1] for p in points]
            painted.append((item.label, loops, points, (min(xs), min(ys), max(xs), max(ys))))
    if glyph.keyline and painted and not small:
        width = max(box[2] for *_, box in painted) - min(box[0] for *_, box in painted)
        height = max(box[3] for *_, box in painted) - min(box[1] for *_, box in painted)
        key = tokens.keyline(glyph.keyline)
        key_width, key_height = key[2] - key[0], key[3] - key[1]
        tolerance = 1.0 * scale
        larger = width > key_width + tolerance or height > key_height + tolerance
        smaller = width < key_width - tolerance and height < key_height - tolerance
        if larger or smaller:
            family.warnings.append(
                f"{glyph.name}: paints {_fmt(width)}x{_fmt(height)} against its {glyph.keyline} keyline "
                f"{_fmt(key_width)}x{_fmt(key_height)}; it will read {'larger' if larger else 'smaller'} than its neighbours"
            )
    threshold = tokens.grid / smallest
    for i in range(len(painted)):
        for j in range(i + 1, len(painted)):
            label_a, loops_a, points_a, box_a = painted[i]
            label_b, loops_b, points_b, box_b = painted[j]
            if (box_a[0] - threshold > box_b[2] or box_b[0] - threshold > box_a[2]
                    or box_a[1] - threshold > box_b[3] or box_b[1] - threshold > box_a[3]):
                continue
            if any(_in_region(point, loops_b) for point in points_a) or any(_in_region(point, loops_a) for point in points_b):
                continue
            gap = min(_length(_sub(p, q)) for p in points_a for q in points_b)
            if 0.12 * scale < gap < threshold - 0.05 * scale:
                family.warnings.append(
                    f"{glyph.name}: {label_a} and {label_b} leave a {gap * smallest / tokens.grid:.2f} px gap "
                    f"at {smallest} px; join them or open the gap to at least 1 px"
                )


def _painted_loops(shape: Shape, tokens: Tokens, half: float | None = None, step: float = 0.3) -> list[list[Point]]:
    """Boundary loops of a shape's painted outline-variant area (even-odd)."""
    half = tokens.half if half is None else half
    if isinstance(shape, Dot):
        return [_shape_points(Circle(shape.c, shape.r), step)]
    if isinstance(shape, Chain) and not shape.closed:
        return [_shape_points(_stroke_outline(shape, half, tokens.linecap, tokens.linejoin), step)]
    outer = _grow(shape, half, tokens.linejoin)
    inner = _shrink(shape, half, tokens.linejoin)
    return [_shape_points(loop, step) for loop in (outer, inner) if loop is not None]


def _in_region(point: Point, loops: list[list[Point]]) -> bool:
    return sum(_inside(point, loop) for loop in loops) % 2 == 1


# --------------------------------------------------------------------------
# SVG serialization


def _segment_d(segment: Segment) -> str:
    if isinstance(segment, Line):
        return f"L{_fmt(segment.p1[0])} {_fmt(segment.p1[1])}"
    sweep = segment.a1 - segment.a0
    end = _end(segment)
    if abs(sweep) >= math.tau - 1e-6:
        middle = _polar(segment.c, segment.r, segment.a0 + sweep / 2)
        flag = 1 if sweep > 0 else 0
        radius = _fmt(segment.r)
        return (f"A{radius} {radius} 0 0 {flag} {_fmt(middle[0])} {_fmt(middle[1])}"
                f"A{radius} {radius} 0 0 {flag} {_fmt(end[0])} {_fmt(end[1])}")
    radius = _fmt(segment.r)
    large = 1 if abs(sweep) > math.pi + 1e-9 else 0
    flag = 1 if sweep > 0 else 0
    return f"A{radius} {radius} 0 {large} {flag} {_fmt(end[0])} {_fmt(end[1])}"


def _shape_d(shape: Shape, reverse: bool = False) -> str:
    """Path data for a shape; ``reverse`` traverses it the other way (the inner edge of a nonzero ring)."""
    if reverse and isinstance(shape, Chain):
        shape = Chain(tuple(_reverse(segment) for segment in reversed(shape.segs)), shape.closed)
    elif reverse:
        cx, cy = shape.c
        rx, ry = (shape.rx, shape.ry) if isinstance(shape, Ellipse) else (shape.r, shape.r)
        return (f"M{_fmt(cx + rx)} {_fmt(cy)}A{_fmt(rx)} {_fmt(ry)} 0 1 0 {_fmt(cx - rx)} {_fmt(cy)}"
                f"A{_fmt(rx)} {_fmt(ry)} 0 1 0 {_fmt(cx + rx)} {_fmt(cy)}Z")
    if isinstance(shape, Chain):
        start = _start(shape.segs[0])
        parts = [f"M{_fmt(start[0])} {_fmt(start[1])}"]
        previous = start
        for segment in shape.segs:
            if isinstance(segment, Line) and _close(segment.p0, segment.p1, 5e-4):
                continue
            text = _segment_d(segment)
            if isinstance(segment, Line):
                end = segment.p1
                if _fmt(end[0]) == _fmt(previous[0]):
                    text = f"V{_fmt(end[1])}"
                elif _fmt(end[1]) == _fmt(previous[1]):
                    text = f"H{_fmt(end[0])}"
            parts.append(text)
            previous = _end(segment)
        if shape.closed:
            parts.append("Z")
        return "".join(parts)
    if isinstance(shape, Ellipse):
        cx, cy, rx, ry = shape.c[0], shape.c[1], _fmt(shape.rx), _fmt(shape.ry)
        return (f"M{_fmt(cx + shape.rx)} {_fmt(cy)}A{rx} {ry} 0 1 1 {_fmt(cx - shape.rx)} {_fmt(cy)}"
                f"A{rx} {ry} 0 1 1 {_fmt(cx + shape.rx)} {_fmt(cy)}Z")
    cx, cy, r = shape.c[0], shape.c[1], _fmt(shape.r)
    return (f"M{_fmt(cx + shape.r)} {_fmt(cy)}A{r} {r} 0 1 1 {_fmt(cx - shape.r)} {_fmt(cy)}"
            f"A{r} {r} 0 1 1 {_fmt(cx + shape.r)} {_fmt(cy)}Z")


def _element_svg(element: Element, own_paint: bool = False) -> str:
    """One element; ``own_paint`` marks a fill drawn inside a stroked outline (an accent)."""
    if element.kind == "dot":
        dot = element.shapes[0]
        assert isinstance(dot, Dot)
        return f'<circle cx="{_fmt(dot.c[0])}" cy="{_fmt(dot.c[1])}" r="{_fmt(dot.r)}" fill="currentColor" stroke="none"/>'
    paint = ' fill="currentColor" stroke="none"' if own_paint else ""
    if element.kind == "ring":
        outer, *inner = element.shapes
        return f'<path{paint} d="{_shape_d(outer)}{"".join(_shape_d(part, reverse=True) for part in inner)}"/>'
    if len(element.shapes) == 1:
        shape = element.shapes[0]
        if isinstance(shape, Circle):
            return f'<circle cx="{_fmt(shape.c[0])}" cy="{_fmt(shape.c[1])}" r="{_fmt(shape.r)}"{paint}/>'
        if isinstance(shape, Ellipse):
            return f'<ellipse cx="{_fmt(shape.c[0])}" cy="{_fmt(shape.c[1])}" rx="{_fmt(shape.rx)}" ry="{_fmt(shape.ry)}"{paint}/>'
        return f'<path{paint} d="{_shape_d(shape)}"/>'
    d = "".join(_shape_d(shape) for shape in element.shapes)
    return f'<path{paint} fill-rule="evenodd" d="{d}"/>'


def _stroke_attributes(tokens: Tokens) -> str:
    return (f'stroke="currentColor" stroke-width="{_fmt(tokens.stroke)}" '
            f'stroke-linecap="{tokens.linecap}" stroke-linejoin="{tokens.linejoin}"')


def _svg(tokens: Tokens, variant: str, body: list[str]) -> str:
    grid = tokens.grid
    opening = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {grid} {grid}" '
               f'width="{grid}" height="{grid}"')
    if variant == "outline" and not tokens.expanded:
        opening += f' fill="none" {_stroke_attributes(tokens)}'
    elif variant in {"solid", "outline"}:
        opening += ' fill="currentColor"'
    else:
        opening += ' fill="none"'
    return opening + ' aria-hidden="true">\n' + "".join(line + "\n" for line in body) + "</svg>\n"


def render_variant(family: Family, glyph: Glyph, variant: str, small: bool = False) -> tuple[str, str]:
    """Return (svg text, drawing mode) for one glyph variant; ``small`` is the optical set with open forms closed."""
    tokens = family.tokens
    if variant == "outline":
        elements = _variant_elements(family, glyph, variant, small)
        kinds = {element.kind for element in elements}
        mode = ("mixed" if kinds - {"stroke"} else "stroke") if "stroke" in kinds else "fill"
        stroked = not tokens.expanded
        return _svg(tokens, variant, [_element_svg(element, stroked and element.kind != "stroke") for element in elements]), mode
    if variant == "solid":
        return _svg(tokens, variant, [_element_svg(element) for element in _variant_elements(family, glyph, variant, small)]), "fill"
    secondary = _duotone_secondary(glyph)
    primary = _outline_elements(family, glyph, "duotone", not small)
    body: list[str] = []
    if secondary:
        body.append(f'<g data-icon-layer="secondary" fill="currentColor" fill-opacity="{_fmt(tokens.secondary_opacity or 0)}">')
        body += [_element_svg(element) for element in secondary]
        body.append("</g>")
    stroked = any(element.kind == "stroke" for element in primary)
    filled = ' fill="currentColor"' if tokens.expanded else ""
    body.append(f'<g data-icon-layer="primary"{" " + _stroke_attributes(tokens) if stroked else ""}{filled}>')
    body += [_element_svg(element, not tokens.expanded and element.kind == "fill") for element in primary]
    body.append("</g>")
    return _svg(tokens, variant, body), "duotone"


def _json_number(value: float) -> int | float:
    return int(value) if float(value).is_integer() else value


def _corner_language(family: Family, variant: str, small: bool) -> str:
    """The drawing language in words: corners and terminals, then any character tokens."""
    tokens = family.tokens
    radius = _fmt(tokens.radius)
    corner = {
        "round": f"{radius}-unit corner radius",
        "chamfer": f"{radius}-unit chamfered corners",
        "sharp": "sharp corners",
        "leaf": f"{radius}-unit leaf corners (rounded upper left and lower right, sharp upper right and lower left)",
    }[tokens.corner]
    ends = f"{tokens.linecap} caps" if tokens.terminal == "cap" else f"{tokens.terminal_angle}-degree angled terminals"
    text = f"{corner}, {ends}, {tokens.linejoin} joins on a {tokens.grid}-unit grid"
    extras = []
    if tokens.expanded and variant != "solid":
        extras.append("strokes expanded to exact filled outlines")
    if tokens.contrast < 1 and variant != "solid":
        extras.append(f"inner details at stroke {_fmt(tokens.detail_stroke)} against {_fmt(tokens.stroke)}")
    if tokens.aperture or tokens.junction_gap:
        gaps = []
        if tokens.aperture:
            gaps.append(f"one {_fmt(tokens.aperture)}-unit aperture near {tokens.aperture_at} o'clock")
        if tokens.junction_gap:
            gaps.append(f"{_fmt(tokens.junction_gap)}-unit junction gaps")
        extras.append(" and ".join(gaps) + (f", closed in this optical set below {family.open_from} px" if small else ""))
    if tokens.proportion != "regular" or tokens.fill != 1.0:
        extras.append(f"{tokens.proportion} keylines at {_fmt(tokens.fill)} live-area fill")
    if tokens.accent is not None:
        extras.append(f"accent: {tokens.accent}")
    return "; ".join([text, *extras])


def render_metadata(family: Family, glyph: Glyph, variant: str, mode: str, svg_bytes: bytes,
                    small: bool = False) -> dict[str, Any]:
    """Companion metadata in the exact asset_quality.py interface-icon schema."""
    tokens = family.tokens
    stroked = mode in {"stroke", "mixed"} or (mode == "duotone" and 'stroke-width="' in svg_bytes.decode("utf-8"))
    language: dict[str, Any] = {
        "mode": mode,
        "stroke_width": _json_number(tokens.stroke) if stroked else 0,
        "linecap": tokens.linecap if stroked else "not applicable",
        "linejoin": tokens.linejoin if stroked else "not applicable",
    }
    if mode == "duotone":
        language["tones"] = {"secondary_opacity": _json_number(tokens.secondary_opacity or 0)}
    corner = _corner_language(family, variant, small)
    if variant == "solid":
        corner = f"filled from the outline's outer edge; {corner}; details cut out even-odd"
    language["corner_language"] = corner
    shapes = sum(len(item.shapes) for item in glyph.items if variant in item.variants)
    sizes = family.small_sizes if small else family.main_sizes
    language["detail_budget"] = glyph.detail_budget or (
        f"{shapes} construction shapes at {tokens.detail} detail density; gaps checked at {family.target_sizes[0]} px"
    )
    live = tokens.live
    return {
        "name": f"{glyph.name}-{variant}{'-small' if small else ''}",
        "asset_type": "interface-icon",
        "role": glyph.role,
        "grid": tokens.grid,
        "live_area": {
            "min_x": _json_number(live[0]), "min_y": _json_number(live[1]),
            "max_x": _json_number(live[2]), "max_y": _json_number(live[3]),
        },
        "drawing_language": language,
        "target_sizes": list(sizes),
        "source": family.source,
        "license": family.license,
        "accessibility_owner": family.accessibility_owner,
        "provenance": {
            "kind": "original",
            "creator": family.creator,
            "source_ref": f"{family.name}.spec.json#{glyph.name}",
            "reviewed": family.reviewed,
            "sha256": hashlib.sha256(svg_bytes).hexdigest(),
        },
        "evidence": {
            "source": {"kind": "local", "path": f"../{family.name}.spec.json", "sha256": "", "locator": f"#{glyph.name}"},
            "license": {"kind": "project-owned"},
        },
    }


def _variant_dir(variant: str, small: bool) -> str:
    return f"{variant}-small" if small else variant


def render_family(family: Family, spec_bytes: bytes) -> dict[str, bytes]:
    """Every output file as relative POSIX path -> exact bytes."""
    spec_digest = hashlib.sha256(spec_bytes).hexdigest()
    files: dict[str, bytes] = {f"{family.name}.spec.json": spec_bytes}
    for glyph in family.glyphs:
        for small in family.sets():
            for variant in family.variants:
                svg_text, mode = render_variant(family, glyph, variant, small)
                svg_bytes = svg_text.encode("utf-8")
                metadata = render_metadata(family, glyph, variant, mode, svg_bytes, small)
                metadata["evidence"]["source"]["sha256"] = spec_digest
                folder = _variant_dir(variant, small)
                files[f"{folder}/{glyph.name}.svg"] = svg_bytes
                files[f"{folder}/{glyph.name}.metadata.json"] = (
                    json.dumps(metadata, indent=2, ensure_ascii=False) + "\n"
                ).encode("utf-8")
    return files


# --------------------------------------------------------------------------
# Contact sheet


SHEET_CSS = """
:root{--paper:#e8e7e3;--ink:#1c1c1f;--muted:#5f5f66}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:14px/20px system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
header{padding:24px 32px 4px}
h1{font-size:20px;line-height:28px;margin:0}
h2{font-size:13px;line-height:20px;margin:0 0 8px;font-weight:600;letter-spacing:.02em}
.tokens{margin:0;color:var(--muted);font-size:13px}
.panels{display:flex;flex-wrap:wrap;gap:16px;padding:16px 32px 0}
.panel{border-radius:12px;padding:16px 16px 12px}
.light{background:#fff;color:#18181b;--line:#e4e4e7;--soft:#71717a}
.dark{background:#161618;color:#ececef;--line:#2e2e33;--soft:#9b9ba3}
.matrix{display:grid;grid-template-columns:104px repeat(12,40px)}
.matrix>div{height:40px;display:flex;align-items:center;justify-content:center}
.matrix .head{height:20px;font-size:11px;line-height:20px;color:var(--soft)}
.matrix .variant{grid-column:span 4;height:20px;font-size:11px;font-weight:600;line-height:20px;justify-content:flex-start;padding-left:8px;border-left:1px solid var(--line)}
.matrix .name{justify-content:flex-start;font-size:12px;color:var(--soft)}
.matrix .first{border-left:1px solid var(--line)}
.i{display:block;flex:none}
.i svg{display:block;width:100%;height:100%}
.strips{padding:16px 32px 0;display:flex;flex-wrap:wrap;gap:16px}
.strip{display:flex;gap:16px;align-items:center;height:40px}
.blur{filter:blur(1.5px)}
.tabs{padding:16px 32px 32px;display:flex;flex-wrap:wrap;gap:16px}
.bar{display:flex;border-top:1px solid var(--line);margin-top:8px}
.tab{width:76px;height:56px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;font-size:11px;line-height:12px;color:var(--soft)}
.tab.on{color:inherit;font-weight:600}
"""


def _inline_svg(svg: str, size: int) -> str:
    return f'<span class="i" style="width:{size}px;height:{size}px">{svg.strip()}</span>'


def _token_summary(family: Family) -> str:
    """One line of the family's tokens for sheet headers; character tokens appear only when set."""
    tokens = family.tokens
    summary = (
        f"{tokens.grid}-unit grid · {_fmt(tokens.padding)} padding · stroke {_fmt(tokens.stroke)} · "
        f"{tokens.linecap} caps · {tokens.linejoin} joins · radius {_fmt(tokens.radius)} · {tokens.detail} detail"
        + (f" · duotone {_fmt(tokens.secondary_opacity)}" if tokens.secondary_opacity is not None else "")
    )
    voice = []
    if tokens.terminal == "angled":
        voice.append(f"{tokens.terminal_angle}° angled terminals")
    if tokens.contrast < 1:
        voice.append(f"details {_fmt(tokens.detail_stroke)}")
    if tokens.corner != "round":
        voice.append(f"{tokens.corner} corners")
    if tokens.proportion != "regular" or tokens.fill != 1.0:
        voice.append(f"{tokens.proportion} keylines at {_fmt(tokens.fill)} fill")
    if tokens.aperture:
        voice.append(f"{_fmt(tokens.aperture)} aperture at {tokens.aperture_at} o'clock")
    if tokens.junction_gap:
        voice.append(f"{_fmt(tokens.junction_gap)} junction gaps")
    if family.open_from is not None:
        voice.append(f"gaps closed below {family.open_from} px")
    if tokens.accent is not None:
        voice.append(f"accent: {tokens.accent}")
    return summary + "".join(f" · {part}" for part in voice)


def render_sheet(family: Family, files: dict[str, bytes]) -> str:
    """Self-contained HTML contact sheet: every glyph x variant x size in light and dark, plus tab bars."""
    tokens = family.tokens

    def svg(glyph: str, variant: str, size: int) -> str:
        small = family.open_from is not None and size < family.open_from
        return files[f"{_variant_dir(variant, small)}/{glyph}.svg"].decode("utf-8")

    summary = _token_summary(family)
    parts = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{html.escape(family.name)} glyph sheet</title>",
        f"<style>{SHEET_CSS.strip()}</style>",
        "</head>",
        "<body>",
        f"<header><h1>{html.escape(family.name)}</h1><p class=\"tokens\">{html.escape(summary)}</p></header>",
        '<div class="panels">',
    ]
    columns = len(family.variants) * len(SHEET_SIZES)
    for theme in ("light", "dark"):
        parts.append(f'<section class="panel {theme}"><h2>{theme.title()}</h2>')
        parts.append(f'<div class="matrix" style="grid-template-columns:104px repeat({columns},40px)">')
        parts.append('<div class="head"></div>')
        parts += [f'<div class="variant">{variant}</div>' for variant in family.variants]
        parts.append('<div class="head"></div>')
        for variant_index, _ in enumerate(family.variants):
            for size_index, size in enumerate(SHEET_SIZES):
                first = " first" if size_index == 0 else ""
                parts.append(f'<div class="head{first}">{size}</div>')
        for glyph in family.glyphs:
            parts.append(f'<div class="name">{html.escape(glyph.name)}</div>')
            for variant in family.variants:
                for size_index, size in enumerate(SHEET_SIZES):
                    first = ' class="first"' if size_index == 0 else ""
                    parts.append(f"<div{first}>{_inline_svg(svg(glyph.name, variant, size), size)}</div>")
        parts.append("</div></section>")
    parts.append("</div>")
    parts.append('<div class="strips">')
    for theme in ("light", "dark"):
        parts.append(f'<section class="panel {theme}"><h2>Label-less at 16 px, then squinted at 24 px</h2>')
        for variant in family.variants:
            parts.append('<div class="strip">' + "".join(_inline_svg(svg(glyph.name, variant, 16), 16) for glyph in family.glyphs) + "</div>")
        parts.append('<div class="strip blur">' + "".join(_inline_svg(svg(glyph.name, family.variants[0], 24), 24) for glyph in family.glyphs) + "</div>")
        parts.append("</section>")
    parts.append("</div>")
    if "solid" in family.variants:
        parts.append('<div class="tabs">')
        for theme in ("light", "dark"):
            parts.append(f'<section class="panel {theme}"><h2>Tab bar: outline idle, solid selected</h2>')
            for selected in family.tabs:
                parts.append('<nav class="bar" aria-label="Sample tab bar">')
                for tab in family.tabs:
                    state = tab == selected
                    variant = "solid" if state else "outline"
                    current = ' aria-current="page"' if state else ""
                    parts.append(
                        f'<span class="tab{" on" if state else ""}"{current}>{_inline_svg(svg(tab, variant, 24), 24)}'
                        f"{html.escape(tab.replace('-', ' '))}</span>"
                    )
                parts.append("</nav>")
            parts.append("</section>")
        parts.append("</div>")
    parts += ["</body>", "</html>"]
    return "\n".join(parts) + "\n"


# --------------------------------------------------------------------------
# Voice comparison: does the family read as its own, or as a stock monoline set?


COMPARE_SIZES = (20, 32)
MAX_COMPARED = 8
COMPARE_CSS = """
:root{--paper:#e8e7e3;--ink:#1c1c1f;--muted:#5f5f66}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:14px/20px system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
header{padding:24px 32px 4px}
h1{font-size:20px;line-height:28px;margin:0}
h2{font-size:13px;line-height:20px;margin:0 0 8px;font-weight:600;letter-spacing:.02em}
.note{margin:0;color:var(--muted);font-size:13px}
.panel{margin:16px 32px 0;border-radius:12px;padding:16px 16px 8px}
.panel:last-child{margin-bottom:32px}
.light{background:#fff;color:#18181b;--line:#e4e4e7;--soft:#71717a}
.dark{background:#161618;color:#ececef;--line:#2e2e33;--soft:#9b9ba3}
.cmp{display:grid;align-items:center}
.cmp>div{padding:6px 12px;border-left:1px solid var(--line)}
.cmp>.name,.cmp>.corner{border-left:0;padding-left:0;font-size:12px;color:var(--soft)}
.fam{align-self:end;font-size:12px;line-height:16px;padding-bottom:10px}
.fam b{display:block;font-size:13px;line-height:18px}
.fam span{display:block;color:var(--soft)}
.cell{display:flex;gap:14px;align-items:center;height:48px}
.i{display:block;flex:none}
.i svg{display:block;width:100%;height:100%}
"""


def baseline_spec(spec: dict[str, Any]) -> dict[str, Any]:
    """The plain monoline baseline of a spec, the stock-library recipe at the family's own weight: same
    construction, stroke and keylines; round caps and joins; a 2-unit radius (per 24-unit grid); and no
    terminal, contrast, open-form, corner or accent character. A family that reads like its baseline has
    no voice beyond its stroke weight."""
    base = json.loads(json.dumps(spec))
    tokens = base["tokens"]
    for key in CHARACTER_TOKENS:
        if key not in {"proportion", "fill"}:
            tokens.pop(key, None)
    tokens["linecap"] = "round"
    tokens["linejoin"] = "round"
    grid = tokens.get("grid", 24)
    tokens["radius"] = _json_number(2 * grid / 24) if grid in GRID_PADDING else 2
    base["family"] = f"{spec['family']}-baseline"[:64].rstrip("-")
    for glyph_spec in base["glyphs"]:
        for shape in glyph_spec.get("shapes", []):
            if isinstance(shape, dict):
                shape.pop("aperture", None)
                shape.pop("junction", None)
                if shape.get("role") == "accent":
                    shape["role"] = "stroke"
    return base


def _voice_line(family: Family) -> str:
    tokens = family.tokens
    parts = [f"stroke {_fmt(tokens.stroke)}"]
    parts.append(f"{tokens.terminal_angle}° cuts" if tokens.terminal == "angled" else f"{tokens.linecap} caps")
    parts.append(f"{tokens.corner} {_fmt(tokens.radius)}" if tokens.corner in {"round", "chamfer", "leaf"} else "sharp")
    if tokens.contrast < 1:
        parts.append(f"details {_fmt(tokens.detail_stroke)}")
    if tokens.aperture:
        parts.append(f"aperture {_fmt(tokens.aperture)}")
    if tokens.junction_gap:
        parts.append(f"junctions {_fmt(tokens.junction_gap)}")
    if tokens.proportion != "regular" or tokens.fill != 1.0:
        parts.append(f"{tokens.proportion} {_fmt(tokens.fill)}")
    if tokens.accent is not None:
        parts.append("accent")
    return " · ".join(parts)


def render_comparison(families: list[Family], names: list[str], variant: str = "outline",
                      sizes: Iterable[int] = COMPARE_SIZES) -> str:
    """Self-contained HTML: the same glyphs in several families side by side, light and dark."""
    sizes = list(sizes)
    columns = f"112px repeat({len(families)}, minmax(0, auto))"
    parts = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>Glyph voice comparison</title>",
        f"<style>{COMPARE_CSS.strip()}</style>",
        "</head>",
        "<body>",
        "<header><h1>Voice comparison</h1>"
        f"<p class=\"note\">{html.escape(variant)} at {', '.join(str(size) for size in sizes)} px; one row per glyph, "
        "one column per family</p></header>",
    ]
    cache: dict[tuple[int, str, int], str] = {}
    for theme in ("light", "dark"):
        parts.append(f'<section class="panel {theme}"><h2>{theme.title()}</h2>')
        parts.append(f'<div class="cmp" style="grid-template-columns:{columns}">')
        parts.append('<div class="corner"></div>')
        for family in families:
            parts.append(f'<div class="fam"><b>{html.escape(family.name)}</b><span>{html.escape(_voice_line(family))}</span></div>')
        for name in names:
            parts.append(f'<div class="name">{html.escape(name)}</div>')
            for index, family in enumerate(families):
                glyph = next(item for item in family.glyphs if item.name == name)
                icons = []
                for size in sizes:
                    small = family.open_from is not None and size < family.open_from
                    key = (index, name, int(small))
                    if key not in cache:
                        cache[key] = render_variant(family, glyph, variant, small)[0]
                    icons.append(_inline_svg(cache[key], size))
                parts.append(f'<div class="cell">{"".join(icons)}</div>')
        parts.append("</div></section>")
    parts += ["</body>", "</html>"]
    return "\n".join(parts) + "\n"


def compare_families(spec_paths: list[str | Path], sheet_path: str | Path, glyphs: list[str] | None = None,
                     variant: str = "outline", sizes: Iterable[int] = COMPARE_SIZES) -> dict[str, Any]:
    """Compile each spec (one spec gains its monoline baseline) and write the comparison sheet."""
    families: list[Family] = []
    problems: list[str] = []
    for path in spec_paths:
        try:
            spec = load_spec(path)
            families.append(compile_family(spec))
        except SpecError as error:
            problems += [f"{path}: {problem}" for problem in error.problems]
            continue
        if len(spec_paths) == 1:
            try:
                families.append(compile_family(baseline_spec(spec)))
            except SpecError as error:
                problems += [f"{path} baseline: {problem}" for problem in error.problems]
    if problems:
        raise SpecError(problems)
    if variant not in families[0].variants or any(variant not in family.variants for family in families):
        raise SpecError([f"every compared family must build the {variant} variant"])
    common = [glyph.name for glyph in families[0].glyphs if all(any(g.name == glyph.name for g in f.glyphs) for f in families)]
    names = list(glyphs) if glyphs else common[:MAX_COMPARED]
    missing = [name for name in names if name not in common]
    if missing:
        raise SpecError([f"glyph {name!r} is not in every compared family" for name in missing])
    if not names or len(names) > MAX_COMPARED * 2:
        raise SpecError([f"compare 1 to {MAX_COMPARED * 2} glyphs at a time"])
    _write_bytes(Path(sheet_path), render_comparison(families, names, variant, sizes).encode("utf-8"))
    return {
        "families": [family.name for family in families],
        "glyphs": names,
        "variant": variant,
        "sizes": list(sizes),
        "sheet": str(sheet_path),
        "warnings": list(dict.fromkeys(warning for family in families for warning in family.warnings)),
    }


# --------------------------------------------------------------------------
# Build orchestration


def _write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        with open(temporary, "xb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def build_family(spec_path: str | Path, out_dir: str | Path, sheet_path: str | Path | None = None) -> dict[str, Any]:
    """Build, validate and publish a family; raises SpecError or BuildError and publishes nothing on failure."""
    spec_bytes = read_spec(spec_path)
    family = compile_family(parse_spec(spec_bytes))
    files = render_family(family, spec_bytes)
    output = Path(out_dir)
    if output.exists() and not output.is_dir():
        raise BuildError([f"output path exists and is not a directory: {output}"])
    if sheet_path is not None:
        sheet_file = Path(sheet_path)
        if sheet_file.resolve().parent == output.resolve() and sheet_file.name in files:
            raise BuildError(["--sheet would overwrite a built file"])
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}.glyph-", dir=output.parent))
    try:
        for relative, content in files.items():
            _write_bytes(staging / relative, content)
        failures: list[str] = []
        validated = 0
        for relative in files:
            if not relative.endswith(".svg"):
                continue
            svg_file = staging / relative
            result = validate_svg_asset(svg_file, svg_file.with_name(f"{svg_file.stem}.metadata.json"))
            validated += 1
            if not result["valid"]:
                failures += [f"{relative}: {error}" for error in result["errors"]]
        if failures:
            raise BuildError(failures)
        for relative in files:
            target = output / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staging / relative, target)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    report: dict[str, Any] = {
        "family": family.name,
        "variants": list(family.variants),
        "glyphs": [glyph.name for glyph in family.glyphs],
        "output": str(output),
        "files": sorted(files),
        "validated": validated,
        "warnings": list(dict.fromkeys(family.warnings)),
    }
    if sheet_path is not None:
        _write_bytes(Path(sheet_path), render_sheet(family, files).encode("utf-8"))
        report["sheet"] = str(sheet_path)
    return report


def check_family(spec_path: str | Path) -> dict[str, Any]:
    """Validate a spec and construct every variant without writing anything."""
    family = compile_family(load_spec(spec_path))
    for glyph in family.glyphs:
        for small in family.sets():
            for variant in family.variants:
                render_variant(family, glyph, variant, small)
    return {
        "family": family.name,
        "variants": list(family.variants),
        "glyphs": [glyph.name for glyph in family.glyphs],
        "warnings": list(dict.fromkeys(family.warnings)),
    }


def _name_list(text: str) -> list[str]:
    names = [part.strip() for part in text.split(",") if part.strip()]
    if not names or any(not NAME_RE.fullmatch(name) for name in names):
        raise argparse.ArgumentTypeError("expected comma-separated glyph names")
    return names


def _size_list(text: str) -> list[int]:
    try:
        sizes = [int(part) for part in text.split(",")]
    except ValueError:
        raise argparse.ArgumentTypeError("expected comma-separated integer sizes") from None
    if not sizes or len(sizes) > 4 or any(not 8 <= size <= 256 for size in sizes):
        raise argparse.ArgumentTypeError("expected one to four sizes from 8 to 256 px")
    return sizes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build an outline, solid and duotone icon family from one JSON spec, validated by asset_quality.py",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build", help="build, validate and write every glyph variant")
    build.add_argument("spec", help="family spec JSON")
    build.add_argument("-o", "--output", required=True, help="output directory (variant subfolders are created)")
    build.add_argument("--sheet", help="also write a self-contained HTML contact sheet here")
    build.add_argument("--json", action="store_true", help="emit a machine-readable report")
    check = commands.add_parser("check", help="validate the spec and construct every variant without writing")
    check.add_argument("spec", help="family spec JSON")
    check.add_argument("--json", action="store_true", help="emit a machine-readable report")
    compare = commands.add_parser(
        "compare", help="render the same glyphs of several families side by side (one spec: beside its monoline baseline)",
    )
    compare.add_argument("specs", nargs="+", help="family spec JSON files")
    compare.add_argument("--sheet", required=True, help="write the self-contained comparison HTML here")
    compare.add_argument("--glyphs", type=_name_list, help="comma-separated glyph names (default: the first eight shared)")
    compare.add_argument("--variant", choices=VARIANTS, default="outline", help="variant to compare (default outline)")
    compare.add_argument("--sizes", type=_size_list, default=list(COMPARE_SIZES), help="comma-separated CSS px sizes (default 20,32)")
    compare.add_argument("--json", action="store_true", help="emit a machine-readable report")
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            report = build_family(args.spec, args.output, args.sheet)
        elif args.command == "compare":
            report = compare_families(args.specs, args.sheet, args.glyphs, args.variant, args.sizes)
        else:
            report = check_family(args.spec)
    except (SpecError, BuildError) as error:
        label = "REFUSED" if isinstance(error, SpecError) else "FAILED"
        if args.json:
            print(json.dumps({"ok": False, "status": label.lower(), "problems": error.problems}, indent=2, ensure_ascii=False))
        else:
            for problem in error.problems:
                print(f"{label}: {problem}", file=sys.stderr)
            if isinstance(error, BuildError):
                print("NOT WRITTEN: the output directory was left unchanged.", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"FAILED: {error}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps({"ok": True, **report}, indent=2, ensure_ascii=False))
    else:
        if args.command == "build":
            print(f"BUILT: {report['family']} -> {report['output']} ({len(report['glyphs'])} glyphs x {', '.join(report['variants'])})")
            print(f"VALIDATED: {report['validated']} SVGs passed asset_quality.py")
            if "sheet" in report:
                print(f"SHEET: {report['sheet']}")
        elif args.command == "compare":
            print(f"COMPARED: {', '.join(report['families'])} ({len(report['glyphs'])} glyphs, {report['variant']} at "
                  f"{', '.join(str(size) for size in report['sizes'])} px)")
            print(f"SHEET: {report['sheet']}")
        else:
            print(f"OK: {report['family']} ({len(report['glyphs'])} glyphs x {', '.join(report['variants'])})")
        for warning in report["warnings"]:
            print(f"WARNING: {warning}")
        if args.command == "compare":
            print("NEXT: if a family reads like its baseline or a stock library at these sizes, its voice is not there yet.")
        else:
            print("NEXT: inspect the contact sheet at 16 px and in the real host; a PASS is structural, not optical.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
