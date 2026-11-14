from __future__ import annotations

import copy
import json
import math
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skill" / "snowe-ui-skill" / "scripts"
EXAMPLES = ROOT / "docs" / "glyph-examples"
sys.path.insert(0, str(SCRIPTS))

import glyph  # noqa: E402
from asset_quality import validate_svg_asset  # noqa: E402


def shape_glyph(name: str, *shapes: dict, **extra) -> dict:
    return {"name": name, "role": f"{name} probe action", "shapes": list(shapes), **extra}


def family_spec(*glyphs: dict, **tokens) -> dict:
    base_tokens = {"stroke": 2, "linecap": "round", "linejoin": "round", "radius": 2, "secondary_opacity": 0.3}
    base_tokens.update(tokens)
    return {
        "schema": "1.0",
        "family": "probe",
        "tokens": base_tokens,
        "target_sizes": [16, 20, 24],
        "metadata": {"creator": "glyph test author", "reviewed": "2026-01-02"},
        "glyphs": list(glyphs) or [shape_glyph("box", {"type": "rounded-rect", "fit": "square"})],
    }


def compile_one(*shapes: dict, **tokens) -> tuple[glyph.Family, glyph.Glyph]:
    family = glyph.compile_family(family_spec(shape_glyph("probe", *shapes), **tokens))
    return family, family.glyphs[0]


def rounded(box: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(round(value, 6) for value in box)


class PrimitiveGeometryTests(unittest.TestCase):
    def test_line_renders_as_a_compact_stroked_path(self):
        family, probe = compile_one({"type": "line", "from": [4, 12], "to": [20, 12]})
        svg, mode = glyph.render_variant(family, probe, "outline")
        self.assertEqual("stroke", mode)
        self.assertIn('<path d="M4 12H20"/>', svg)
        self.assertIn('stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"', svg)

    def test_rounded_rect_corners_use_the_family_radius(self):
        _, probe = compile_one({"type": "rounded-rect", "x": 4, "y": 4, "w": 16, "h": 16})
        chain = probe.items[0].shapes[0]
        arcs = [segment for segment in chain.segs if isinstance(segment, glyph.Arc)]
        lines = [segment for segment in chain.segs if isinstance(segment, glyph.Line)]
        self.assertTrue(chain.closed)
        self.assertEqual((4, 4), (len(arcs), len(lines)))
        self.assertTrue(all(math.isclose(arc.r, 2) for arc in arcs))
        self.assertEqual((4, 4, 20, 20), rounded(glyph._shape_bounds(chain)))
        _, sharp = compile_one({"type": "rect", "x": 4, "y": 4, "w": 16, "h": 16})
        self.assertFalse(any(isinstance(segment, glyph.Arc) for segment in sharp.items[0].shapes[0].segs))

    def test_keyline_boxes_overshoot_circles_past_squares(self):
        tokens = glyph.compile_family(family_spec()).tokens
        self.assertEqual((2, 2, 22, 22), tokens.keyline("circle"))
        self.assertEqual((3, 3, 21, 21), tokens.keyline("square"))
        self.assertEqual((4, 2, 20, 22), tokens.keyline("portrait"))
        self.assertEqual((2, 4, 22, 20), tokens.keyline("landscape"))
        _, circle = compile_one({"type": "circle", "fit": "circle"})
        self.assertEqual(glyph.Circle((12, 12), 9), circle.items[0].shapes[0])
        _, square = compile_one({"type": "rounded-rect", "fit": "square"})
        self.assertEqual((4, 4, 20, 20), rounded(glyph._shape_bounds(square.items[0].shapes[0])))
        _, portrait = compile_one({"type": "rect", "fit": "portrait"})
        self.assertEqual((5, 3, 19, 21), rounded(glyph._shape_bounds(portrait.items[0].shapes[0])))

    def test_square_caps_shrink_the_circle_keyline_to_the_validator_reach(self):
        _, circle = compile_one({"type": "circle", "fit": "circle"}, linecap="square")
        self.assertAlmostEqual(10 - math.sqrt(2), circle.items[0].shapes[0].r)

    def test_polygon_gear_chevron_arrow_and_arc_construction(self):
        _, probe = compile_one(
            {"type": "polygon", "center": [12, 12], "r": 8, "sides": 6, "radius": 0},
            {"type": "gear", "center": [12, 12], "r": 9, "root": 7, "teeth": 8, "radius": 0},
            {"type": "chevron", "tip": [16, 12], "dir": "right", "span": 8},
            {"type": "arrow", "from": [12, 20], "to": [12, 6], "head": 4},
            {"type": "arc", "center": [12, 12], "r": 5, "start": 0, "end": 90},
        )
        polygon, gear, chevron, shaft, head, arc = [shape for item in probe.items for shape in item.shapes]
        self.assertEqual(6, len(polygon.segs))
        self.assertTrue(math.isclose(glyph._start(polygon.segs[0])[1], 4))  # first vertex points up
        self.assertEqual(32, len(gear.segs))
        self.assertEqual([(12, 8), (16, 12), (12, 16)], [glyph._start(chevron.segs[0]), glyph._end(chevron.segs[0]), glyph._end(chevron.segs[1])])
        self.assertEqual(((12, 20), (12, 6)), (shaft.segs[0].p0, shaft.segs[0].p1))
        self.assertEqual([(16, 10), (12, 6), (8, 10)], [glyph._start(head.segs[0]), glyph._end(head.segs[0]), glyph._end(head.segs[1])])
        start, end = glyph._start(arc.segs[0]), glyph._end(arc.segs[0])
        self.assertEqual((17, 12), tuple(round(value, 9) for value in start))
        self.assertEqual((12, 17), tuple(round(value, 9) for value in end))
        self.assertEqual("body", probe.items[0].role)
        self.assertEqual("stroke", probe.items[2].role)

    def test_path_grammar_closes_and_defaults_closed_shapes_to_body(self):
        _, probe = compile_one(
            {"type": "path", "d": "M5 20 V11 A7 7 0 0 1 19 11 V20 Z", "radius": 0},
            {"type": "path", "d": "M8 4 L16 4"},
        )
        closed, open_path = probe.items
        self.assertEqual(("body", "stroke"), (closed.role, open_path.role))
        chain = closed.shapes[0]
        self.assertTrue(chain.closed)
        self.assertEqual(1, sum(isinstance(segment, glyph.Arc) for segment in chain.segs))
        self.assertEqual((5, 4, 19, 20), rounded(glyph._shape_bounds(chain)))

    def test_transforms_mirror_repeat_radial_and_grid_snapped_rotation(self):
        _, probe = compile_one(
            {"type": "line", "from": [6, 8], "to": [6, 16], "mirror": "x"},
            {"type": "dot", "at": [8, 12], "role": "stroke", "repeat": {"count": 3, "step": [4, 0]}},
            {"type": "line", "from": [12, 4], "to": [12, 6], "radial": 4},
            {"type": "line", "from": [12, 4], "to": [12, 8], "rotate": 90},
            {"type": "line", "from": [4, 4], "to": [8, 4], "mirror": "xy"},
        )
        mirrored, dots, rays, rotated, quad = probe.items
        self.assertEqual([6, 18], [shape.segs[0].p0[0] for shape in mirrored.shapes])
        self.assertEqual([(8, 12), (12, 12), (16, 12)], [shape.c for shape in dots.shapes])
        self.assertEqual({(12, 4), (20, 12), (12, 20), (4, 12)}, {shape.segs[0].p0 for shape in rays.shapes})
        self.assertEqual(((20, 12), (16, 12)), (rotated.shapes[0].segs[0].p0, rotated.shapes[0].segs[0].p1))
        self.assertEqual(4, len(quad.shapes))

    def test_crisp_snapping_puts_axis_aligned_strokes_on_whole_pixels_toward_the_center(self):
        line = {"type": "line", "from": [3.5, 6], "to": [3.5, 18]}
        _, even = compile_one(line, stroke=2)
        self.assertEqual(4, even.items[0].shapes[0].segs[0].p0[0])
        _, odd = compile_one(line, stroke=1)
        self.assertEqual(3.5, odd.items[0].shapes[0].segs[0].p0[0])
        _, fractional = compile_one(line, stroke=1.5)
        self.assertEqual(3.5, fractional.items[0].shapes[0].segs[0].p0[0])
        _, disabled = compile_one(line, stroke=2, crisp=False)
        self.assertEqual(3.5, disabled.items[0].shapes[0].segs[0].p0[0])
        _, right = compile_one({"type": "line", "from": [20.5, 6], "to": [20.5, 18]}, stroke=2)
        self.assertEqual(20, right.items[0].shapes[0].segs[0].p0[0])

    def test_detail_density_drops_richer_items(self):
        rich = {"type": "dot", "at": [12, 12], "min_detail": "high"}
        frame = {"type": "rounded-rect", "fit": "square"}
        _, low = compile_one(frame, rich, detail="low")
        _, high = compile_one(frame, rich, detail="high")
        self.assertEqual((1, 2), (len(low.items), len(high.items)))


class OutlineAndCutoutTests(unittest.TestCase):
    def test_stroke_outline_caps_match_the_stroke(self):
        chain = glyph.Chain((glyph.Line((4, 12), (20, 12)),), False)
        expected = {"round": (3, 11, 21, 13), "butt": (4, 11, 20, 13), "square": (3, 11, 21, 13)}
        for cap, box in expected.items():
            with self.subTest(cap=cap):
                outline = glyph._stroke_outline(chain, 1, cap, "round")
                self.assertEqual(box, rounded(glyph._shape_bounds(outline)))

    def test_inner_joins_are_trimmed_instead_of_self_overlapping(self):
        chain = glyph.Chain((glyph.Line((4, 4), (4, 20)), glyph.Line((4, 20), (20, 20))), False)
        outline = glyph._stroke_outline(chain, 1, "butt", "bevel")
        area = abs(glyph._signed_area(glyph._shape_points(outline)))
        # Two 16x2 legs, minus their 1x1 overlap, plus the half-unit bevel triangle.
        self.assertAlmostEqual(63.5, area, places=6)
        round_join = glyph._stroke_outline(chain, 1, "butt", "round")
        self.assertAlmostEqual(63 + math.pi / 4, abs(glyph._signed_area(glyph._shape_points(round_join, 0.01))), places=3)

    def test_solid_turns_inner_details_into_evenodd_cutouts(self):
        family, probe = compile_one(
            {"type": "rounded-rect", "fit": "square"},
            {"type": "line", "from": [8, 12], "to": [16, 12], "role": "detail"},
        )
        elements = glyph._solid_elements(family, probe)
        self.assertEqual(1, len(elements))
        outer, cut = elements[0].shapes
        self.assertEqual((3, 3, 21, 21), rounded(glyph._shape_bounds(outer)))  # the outline's outer edge
        self.assertEqual((7, 11, 17, 13), rounded(glyph._shape_bounds(cut)))
        svg, mode = glyph.render_variant(family, probe, "solid")
        self.assertEqual("fill", mode)
        self.assertEqual(1, svg.count('fill-rule="evenodd"'))
        self.assertEqual(2, re.search(r'd="([^"]+)"', svg).group(1).count("M"))
        self.assertNotIn("stroke", svg)

    def test_closed_details_cut_filled_holes_and_open_bodies_close_by_their_chord(self):
        family, probe = compile_one(
            {"type": "circle", "center": [12, 12], "r": 8},
            {"type": "circle", "center": [12, 12], "r": 3, "role": "detail"},
            {"type": "polyline", "points": [[4, 21], [4, 19], [20, 19], [20, 21]], "role": "body", "radius": 0},
            stroke=1.5,
        )
        ring, shoulders = glyph._solid_elements(family, probe)
        self.assertEqual((glyph.Circle((12, 12), 8.75), glyph.Circle((12, 12), 3.75)), ring.shapes)
        self.assertTrue(shoulders.shapes[0].closed)

    def test_solid_cutout_refusals(self):
        body = {"type": "rounded-rect", "fit": "square"}
        cases = {
            "overlap": [body, {"type": "line", "from": [9, 12], "to": [15, 12], "role": "detail"},
                        {"type": "line", "from": [12, 9], "to": [12, 15], "role": "detail"}],
            "crosses the edge": [body, {"type": "line", "from": [4, 12], "to": [20, 12], "role": "detail"}],
            "outside every body": [body, {"type": "dot", "at": [21.5, 2.5], "d": 1}],
        }
        for expected, shapes in cases.items():
            with self.subTest(expected=expected):
                with self.assertRaises(glyph.SpecError) as raised:
                    compile_one(*shapes)
                self.assertIn(expected, " ".join(raised.exception.problems))

    def test_variants_limit_an_item_to_chosen_variants(self):
        family, probe = compile_one(
            {"type": "rounded-rect", "fit": "square"},
            {"type": "line", "from": [4, 12], "to": [20, 12], "role": "detail", "variants": ["outline", "duotone"]},
        )
        self.assertNotIn("evenodd", glyph.render_variant(family, probe, "solid")[0])
        self.assertEqual(2, glyph.render_variant(family, probe, "outline")[0].count("<path"))

    def test_duotone_layers_follow_the_validator_contract(self):
        family, probe = compile_one(
            {"type": "circle", "center": [12, 12], "r": 8},
            {"type": "circle", "center": [12, 12], "r": 3, "role": "detail"},
            {"type": "line", "from": [12, 3], "to": [12, 4], "role": "stroke", "variants": ["outline"]},
        )
        svg, mode = glyph.render_variant(family, probe, "duotone")
        self.assertEqual("duotone", mode)
        self.assertIn('<g data-icon-layer="secondary" fill="currentColor" fill-opacity="0.3">', svg)
        self.assertIn('<g data-icon-layer="primary" stroke="currentColor" stroke-width="2"', svg)
        self.assertIn('fill-rule="evenodd"', svg)  # the hub is a hole in the secondary fill
        self.assertLess(svg.index("secondary"), svg.index("primary"))


class OpticalLintTests(unittest.TestCase):
    def test_keyline_lint_flags_oversized_glyphs(self):
        family = glyph.compile_family(family_spec(shape_glyph("big", {"type": "circle", "fit": "circle"}, keyline="square")))
        self.assertTrue(any("reads larger" in warning or "read larger" in warning for warning in family.warnings))
        fitted = glyph.compile_family(family_spec(shape_glyph("fit", {"type": "circle", "fit": "circle"}, keyline="circle")))
        self.assertEqual([], fitted.warnings)

    def test_gap_lint_measures_painted_outlines(self):
        near = glyph.compile_family(family_spec(shape_glyph(
            "near", {"type": "line", "from": [4, 10], "to": [20, 10]}, {"type": "line", "from": [4, 13], "to": [20, 13]},
        )))
        self.assertTrue(any("gap" in warning for warning in near.warnings))
        clear = glyph.compile_family(family_spec(shape_glyph(
            "clear", {"type": "line", "from": [4, 10], "to": [20, 10]}, {"type": "line", "from": [4, 14], "to": [20, 14]},
        )))
        self.assertEqual([], clear.warnings)
        butt = glyph.compile_family(family_spec(shape_glyph(
            "flat", {"type": "line", "from": [12, 4], "to": [12, 8]}, {"type": "line", "from": [4, 11], "to": [20, 11]},
        ), linecap="butt"))
        self.assertEqual([], butt.warnings)


class RefusalTests(unittest.TestCase):
    def assert_refused(self, spec: dict, expected: str) -> None:
        with self.assertRaises(glyph.SpecError) as raised:
            glyph.compile_family(spec)
        self.assertIn(expected, " ".join(raised.exception.problems))

    def test_every_spec_refusal(self):
        def with_shape(shape: dict, **tokens) -> dict:
            return family_spec(shape_glyph("probe", shape), **tokens)

        line = {"type": "line", "from": [4, 12], "to": [20, 12]}
        cases = [
            (with_shape({"type": "spline", "points": []}), "type must be one of"),
            (with_shape({**line, "colour": "red"}), "unknown field(s): colour"),
            (with_shape({**line, "from": [4.3, 12]}), "off the 0.25-unit construction grid"),
            (with_shape({**line, "from": [float("inf"), 12]}), "must be finite"),
            (with_shape({**line, "from": "4,12"}), "must be an [x, y] pair"),
            (with_shape({"type": "line", "from": [1, 12], "to": [20, 12]}), "outside the live area"),
            (with_shape({"type": "arc", "center": [12, 12], "r": 9, "start": 0, "end": 180}), "touches the live-area edge"),
            (with_shape({**line, "rotate": 20}), "multiple of 15 degrees"),
            (with_shape({"type": "arc", "center": [12, 12], "r": 5, "start": 0, "end": 360}), "between 0 and 360"),
            (with_shape({"type": "path", "d": "m4 4 l8 0"}), "absolute M, L, H, V, A and Z"),
            (with_shape({"type": "path", "d": "M4 4 A4 6 0 0 1 12 4"}), "arcs must be circular"),
            (with_shape({"type": "polyline", "points": [[4, 4], [4, 4], [8, 8]]}), "repeats point"),
            (with_shape({"type": "dot", "at": [12, 12], "role": "body"}), "a dot cannot be a body"),
            (with_shape(line, linejoin="miter"), "tokens.linejoin must be one of"),
            (with_shape(line, weight=3), "unknown field(s): weight"),
            (with_shape(line, stroke=0.5), "below 0.5 CSS px"),
            (with_shape(line, grid=18), "tokens.grid must be"),
            (with_shape(line, secondary_opacity=0.9), "tokens.secondary_opacity"),
        ]
        no_tone = with_shape(line)
        del no_tone["tokens"]["secondary_opacity"]
        no_tone["variants"] = ["outline", "duotone"]
        cases.append((no_tone, "needs tokens.secondary_opacity"))
        schema = with_shape(line)
        schema["schema"] = "2.0"
        cases.append((schema, "spec.schema must be"))
        future = with_shape(line)
        future["metadata"]["reviewed"] = "2999-01-01"
        cases.append((future, "future date"))
        loose = with_shape(line)
        loose["metadata"]["reviewed"] = "14 Nov 2026"
        cases.append((loose, "ISO date"))
        placeholder = with_shape(line)
        placeholder["glyphs"][0]["role"] = "<role>"
        cases.append((placeholder, "placeholder"))
        twice = family_spec(shape_glyph("same", line), shape_glyph("same", line))
        cases.append((twice, "defined twice"))
        crowded = family_spec(*[shape_glyph(f"g{index}", line) for index in range(glyph.MAX_GLYPHS + 1)])
        cases.append((crowded, f"the limit is {glyph.MAX_GLYPHS}"))
        busy = family_spec(shape_glyph("busy", *[line] * (glyph.MAX_SHAPES + 1)))
        cases.append((busy, f"the limit is {glyph.MAX_SHAPES}"))
        expanded = family_spec(shape_glyph("expanded", *[
            {"type": "dot", "at": [3, 3], "d": 1, "role": "stroke", "repeat": {"count": 16, "step": [1, 0]}, "mirror": "xy"},
            {"type": "dot", "at": [12, 12], "role": "stroke"},
        ]))
        cases.append((expanded, f"the limit is {glyph.MAX_EXPANDED}"))
        for spec, expected in cases:
            with self.subTest(expected=expected):
                self.assert_refused(spec, expected)

    def test_strict_json_refusals(self):
        cases = {
            b'{"schema": "1.0", "schema": "1.0"}': "duplicate key",
            b'{"x": NaN}': "non-finite number",
            b'[1, 2]': "root must be a JSON object",
            b'\xff\xfe': "not UTF-8",
            b" " * (glyph.MAX_SPEC_BYTES + 1): "family budget",
        }
        for content, expected in cases.items():
            with self.subTest(expected=expected):
                with self.assertRaises(glyph.SpecError) as raised:
                    glyph.parse_spec(content)
                self.assertIn(expected, str(raised.exception))


class BuildTests(unittest.TestCase):
    def test_demo_families_build_validate_and_regenerate_byte_identically(self):
        for name in ("larder-soft", "larder-crisp"):
            with self.subTest(family=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                spec = EXAMPLES / f"{name}.json"
                first = glyph.build_family(spec, root / "a", root / "a.html")
                second = glyph.build_family(spec, root / "b", root / "b.html")
                self.assertEqual(42, first["validated"])
                self.assertEqual([], first["warnings"])
                self.assertEqual(first["files"], second["files"])
                for relative in first["files"]:
                    self.assertEqual((root / "a" / relative).read_bytes(), (root / "b" / relative).read_bytes(), relative)
                self.assertEqual((root / "a.html").read_bytes(), (root / "b.html").read_bytes())
                for svg in sorted((root / "a").rglob("*.svg")):
                    result = validate_svg_asset(svg, svg.with_name(f"{svg.stem}.metadata.json"))
                    self.assertTrue(result["valid"], (svg, result["errors"]))
                metadata = json.loads((root / "a" / "duotone" / "home.metadata.json").read_text(encoding="utf-8"))
                self.assertEqual("home-duotone", metadata["name"])
                self.assertEqual("duotone", metadata["drawing_language"]["mode"])
                self.assertIn("secondary_opacity", metadata["drawing_language"]["tones"])
                self.assertEqual(f"../{name}.spec.json", metadata["evidence"]["source"]["path"])
                self.assertEqual(spec.read_bytes(), (root / "a" / f"{name}.spec.json").read_bytes())

    def test_sheet_is_self_contained_and_covers_every_glyph_variant_and_size(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = glyph.build_family(EXAMPLES / "larder-soft.json", root / "out", root / "sheet.html")
            sheet = (root / "sheet.html").read_text(encoding="utf-8")
            self.assertNotRegex(sheet, r"(?:src|href)=|url\(|@import|<script")
            references = set(re.findall(r"https?://[^\s\"'<>]+", sheet))
            self.assertEqual({"http://www.w3.org/2000/svg"}, references)
            glyph_count = len(report["glyphs"])
            for size in glyph.SHEET_SIZES:
                # light and dark matrices: every glyph x variant at every size
                self.assertGreaterEqual(sheet.count(f'style="width:{size}px;height:{size}px"'), 2 * glyph_count * 3)
            self.assertEqual(2 * 5, sheet.count('aria-current="page"'))
            self.assertIn('class="panel dark"', sheet)

    def test_failed_validation_publishes_nothing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec = root / "probe.json"
            spec.write_text(json.dumps(family_spec()), encoding="utf-8")
            failing = {"valid": False, "errors": ["synthetic validator failure"], "warnings": [], "checks": []}
            with mock.patch.object(glyph, "validate_svg_asset", return_value=failing):
                with self.assertRaises(glyph.BuildError) as raised:
                    glyph.build_family(spec, root / "out", root / "sheet.html")
            self.assertIn("synthetic validator failure", " ".join(raised.exception.problems))
            self.assertFalse((root / "out").exists())
            self.assertFalse((root / "sheet.html").exists())
            self.assertEqual(["probe.json"], sorted(path.name for path in root.iterdir()))


class DocumentationTests(unittest.TestCase):
    def test_cli_reference_example_spec_builds(self):
        reference = (ROOT / "skill" / "snowe-ui-skill" / "references" / "cli-reference.md").read_text(encoding="utf-8")
        section = reference.split("## Build an Icon Family", 1)[1].split("\n## ", 1)[0]
        example = re.search(r"```json\s*(\{.*?\})\s*```", section, re.DOTALL)
        self.assertIsNotNone(example, "the glyph.py section must show a parseable spec")
        family = glyph.compile_family(json.loads(example.group(1)))
        self.assertEqual(["home", "search"], [item.name for item in family.glyphs])
        self.assertEqual(("outline", "solid", "duotone"), family.variants)


class CliTests(unittest.TestCase):
    def run_cli(self, *arguments: str, isolated: bool = False) -> subprocess.CompletedProcess:
        command = [sys.executable, *(["-I"] if isolated else []), str(SCRIPTS / "glyph.py"), *arguments]
        return subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False, timeout=120)

    def test_exit_codes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            good = root / "good.json"
            good.write_text(json.dumps(family_spec()), encoding="utf-8")
            bad_spec = copy.deepcopy(family_spec())
            bad_spec["glyphs"][0]["shapes"][0]["type"] = "spline"
            bad = root / "bad.json"
            bad.write_text(json.dumps(bad_spec), encoding="utf-8")

            built = self.run_cli("build", str(good), "-o", str(root / "out"), "--json")
            self.assertEqual(0, built.returncode, built.stderr)
            report = json.loads(built.stdout)
            self.assertTrue(report["ok"])
            self.assertEqual(3, report["validated"])

            refused = self.run_cli("build", str(bad), "-o", str(root / "refused"))
            self.assertEqual(1, refused.returncode)
            self.assertIn("REFUSED:", refused.stderr)
            self.assertFalse((root / "refused").exists())

            refused_json = self.run_cli("check", str(bad), "--json")
            self.assertEqual(1, refused_json.returncode)
            self.assertEqual("refused", json.loads(refused_json.stdout)["status"])

            checked = self.run_cli("check", str(good))
            self.assertEqual(0, checked.returncode, checked.stderr)
            self.assertIn("OK: probe", checked.stdout)

            missing = self.run_cli("build", str(good))
            self.assertEqual(2, missing.returncode)

    def test_runs_under_isolated_python(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = self.run_cli(
                "build", str(EXAMPLES / "larder-crisp.json"), "-o", str(root / "out"), "--sheet", str(root / "sheet.html"),
                isolated=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("VALIDATED: 42 SVGs passed asset_quality.py", result.stdout)
            self.assertTrue((root / "sheet.html").is_file())


if __name__ == "__main__":
    unittest.main()
