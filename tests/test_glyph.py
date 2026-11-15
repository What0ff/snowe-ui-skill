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


class CharacterDocumentationTests(unittest.TestCase):
    def test_cli_reference_character_example_compiles(self):
        reference = (ROOT / "skill" / "snowe-ui-skill" / "references" / "cli-reference.md").read_text(encoding="utf-8")
        section = reference.split("## Build an Icon Family", 1)[1].split("\n## ", 1)[0]
        examples = re.findall(r"```json\s*(\{.*?\})\s*```", section, re.DOTALL)
        self.assertEqual(2, len(examples))
        spec = family_spec()
        spec["tokens"] = json.loads(examples[1])["tokens"]
        family = glyph.compile_family(spec)
        self.assertEqual(("chamfer", 1.0), (family.tokens.corner, family.tokens.junction_gap))
        for token in glyph.CHARACTER_TOKENS:
            self.assertIn(f"`{token}`", section)

    def test_icon_craft_voice_section_stays_within_its_budget(self):
        craft = (ROOT / "skill" / "snowe-ui-skill" / "references" / "icon-craft.md").read_text(encoding="utf-8")
        section = craft.split("## Give the family a voice", 1)[1].split("\n## ", 1)[0]
        self.assertLessEqual(len(section.split()), 600)
        for anchor in ("glyph.py compare", "monoline baseline", "16 px", "squint", "Lucide"):
            self.assertIn(anchor, section)


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


VOICES = ("larder-almanac", "larder-ledger", "larder-picnic", "larder-linen")
# SHA-256 over every built file and the sheet of the two baseline specs as they built before
# character tokens existed: a spec without them must keep building byte-identically.
BASELINE_DIGESTS = {
    "larder-soft": "e6b9822fcb18047e478ca1fae8a492b656a1782174836da7f4ab244bde55e241",
    "larder-crisp": "838597e90755b4ce2cc8160599b3941c83e07ff80e48bbfc2fd23eba1e6f8fc2",
}


def family_digest(content: bytes) -> str:
    import hashlib

    family = glyph.compile_family(glyph.parse_spec(content))
    files = glyph.render_family(family, content)
    digest = hashlib.sha256()
    for relative in sorted(files):
        digest.update(relative.encode() + b"\0" + files[relative] + b"\0")
    digest.update(glyph.render_sheet(family, files).encode())
    return digest.hexdigest()


def outline_area(chain: glyph.Chain, step: float = 0.002) -> float:
    return abs(glyph._signed_area(glyph._shape_points(chain, step)))


def element_paths(family: glyph.Family, probe: glyph.Glyph, variant: str) -> list[str]:
    return re.findall(r"<(?:path|circle)[^>]*>", glyph.render_variant(family, probe, variant)[0])


class CompatibilityTests(unittest.TestCase):
    def test_specs_without_character_tokens_build_byte_identically(self):
        for name, expected in BASELINE_DIGESTS.items():
            with self.subTest(family=name):
                self.assertEqual(expected, family_digest((EXAMPLES / f"{name}.json").read_bytes()))

    def test_default_tokens_add_no_character(self):
        tokens = glyph.compile_family(family_spec()).tokens
        self.assertFalse(tokens.character)
        self.assertFalse(tokens.expanded)
        self.assertEqual((0.0, 2.0), (tokens.cut, tokens.detail_stroke))


class TerminalTests(unittest.TestCase):
    def test_angled_cut_expands_a_line_into_an_exact_parallelogram(self):
        angle = math.radians(30)
        outline = glyph._stroke_outline(glyph.Chain((glyph.Line((4, 12), (20, 12)),), False), 1, "butt", "round", angle)
        lean = math.tan(angle)
        corners = {tuple(round(value, 9) for value in glyph._start(segment)) for segment in outline.segs}
        expected = {(4 + lean, 13), (20 + lean, 13), (20 - lean, 11), (4 - lean, 11)}
        self.assertEqual({tuple(round(value, 9) for value in point) for point in expected}, corners)
        self.assertTrue(all(isinstance(segment, glyph.Line) for segment in outline.segs))
        self.assertAlmostEqual(32.0, outline_area(outline), places=9)  # the cut keeps length x width

    def test_angled_cut_on_an_arc_keeps_exact_offset_circles(self):
        arc = glyph.Arc((12, 12), 6, 0.0, math.pi / 2)
        angle = math.radians(30)
        outline = glyph._stroke_outline(glyph.Chain((arc,), False), 1, "butt", "round", angle)
        arcs = [segment for segment in outline.segs if isinstance(segment, glyph.Arc)]
        cuts = [segment for segment in outline.segs if isinstance(segment, glyph.Line)]
        self.assertEqual([7, 5], sorted((round(segment.r, 12) for segment in arcs), reverse=True))
        self.assertTrue(all(segment.c == (12, 12) for segment in arcs))
        self.assertEqual(2, len(cuts))
        for end, tangent in ((glyph._end(arc), glyph._tan_end(arc)), (glyph._start(arc), glyph._mul(glyph._tan_start(arc), -1.0))):
            direction = glyph._cut_direction(tangent, angle)
            cut = next(line for line in cuts if glyph._length(glyph._sub(glyph._add(line.p0, line.p1), glyph._mul(end, 2))) < 0.5)
            for point in (cut.p0, cut.p1):
                self.assertAlmostEqual(0.0, glyph._cross(glyph._sub(point, end), direction), places=9)  # on the cut line
                self.assertIn(round(glyph._length(glyph._sub(point, (12, 12))), 9), {7.0, 5.0})  # on an offset circle

    def test_angled_family_draws_filled_outlines_that_validate_as_fill(self):
        spec = family_spec(shape_glyph("probe", {"type": "rounded-rect", "fit": "square"},
                                       {"type": "line", "from": [8, 12], "to": [16, 12], "role": "detail"}),
                           linecap="butt", terminal="angled", terminal_angle=45)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "probe.json"
            path.write_text(json.dumps(spec), encoding="utf-8")
            report = glyph.build_family(path, Path(temporary) / "out")
            outline = (Path(temporary) / "out" / "outline" / "probe.svg").read_text(encoding="utf-8")
            metadata = json.loads((Path(temporary) / "out" / "outline" / "probe.metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(3, report["validated"])
        self.assertNotIn("stroke-width", outline)
        self.assertIn('fill="currentColor"', outline)
        self.assertEqual(("fill", 0, "not applicable"), tuple(metadata["drawing_language"][key] for key in ("mode", "stroke_width", "linecap")))
        self.assertIn("45-degree angled terminals", metadata["drawing_language"]["corner_language"])

    def test_closed_strokes_expand_to_nonzero_rings_that_keep_tight_corners_painted(self):
        family, probe = compile_one({"type": "path", "d": "M5 17 L6.25 15.75 V9.5 A5.75 5.75 0 0 1 17.75 9.5 V15.75 L19 17 Z"},
                                    linecap="butt", terminal="angled", linejoin="miter", corner="sharp", stroke=1.75)
        elements = glyph._outline_elements(family, probe, "outline")
        self.assertEqual(["ring"], [element.kind for element in elements])
        svg = glyph.render_variant(family, probe, "outline")[0]
        self.assertNotIn("evenodd", svg)
        outer, inner = elements[0].shapes
        self.assertGreater(glyph._signed_area(glyph._shape_points(outer)) * glyph._signed_area(glyph._shape_points(inner)), 0)
        self.assertIn(glyph._shape_d(inner, reverse=True)[:12], svg)  # the inner edge runs the other way

    def test_miter_joins_are_exact_and_fall_back_to_a_bevel_past_the_limit(self):
        family, square = compile_one({"type": "rect", "x": 6, "y": 6, "w": 12, "h": 12}, linecap="butt", terminal="angled",
                                     linejoin="miter")
        ring = glyph._outline_elements(family, square, "outline")[0]
        self.assertEqual((5, 5, 19, 19), rounded(glyph._shape_bounds(ring.shapes[0])))
        vertices = {tuple(round(value, 9) for value in glyph._start(segment)) for segment in ring.shapes[0].segs}
        self.assertLessEqual({(5, 5), (19, 5), (19, 19), (5, 19)}, vertices)  # sharp apexes, not bevels
        acute = glyph._miter((0, 1), (0.0, -1.0), (1, 0), glyph._unit((-1, -0.25)), (0, 0), 1)
        self.assertEqual([glyph.Line((0, 1), (0.0, -1.0))], acute)  # an acute corner bevels instead of growing a horn


class ContrastTests(unittest.TestCase):
    def test_details_draw_at_the_contrast_stroke_and_cut_out_at_full_stroke(self):
        family, probe = compile_one(
            {"type": "rounded-rect", "fit": "square"},
            {"type": "line", "from": [8, 12], "to": [16, 12], "role": "detail"},
            stroke=1.75, linecap="butt", contrast=0.7,
        )
        self.assertEqual(1.25, family.tokens.detail_stroke)
        frame, detail = glyph._outline_elements(family, probe, "outline")
        self.assertEqual(("ring", "fill"), (frame.kind, detail.kind))
        self.assertEqual((8, 11.375, 16, 12.625), rounded(glyph._shape_bounds(detail.shapes[0])))
        solid = glyph._solid_elements(family, probe)[0]
        self.assertEqual((8, 11.125, 16, 12.875), rounded(glyph._shape_bounds(solid.shapes[1])))  # negative space keeps weight

    def test_contrast_rounds_to_the_eighth_unit_step(self):
        tokens = glyph.compile_family(family_spec(contrast=0.6, linecap="butt")).tokens
        self.assertEqual(1.25, tokens.detail_stroke)  # 2 x 0.6 = 1.2 rounds to 1.25
        self.assertTrue(tokens.expanded)


class OpenFormTests(unittest.TestCase):
    def test_aperture_sits_on_the_nearest_straight_run_at_the_clock_position(self):
        _, butt = compile_one({"type": "rounded-rect", "fit": "square"}, aperture=2, linecap="butt")
        _, rounded_caps = compile_one({"type": "rounded-rect", "fit": "square"}, aperture=2)
        for probe, centerline_gap in ((butt, 2.0), (rounded_caps, 4.0)):  # round caps reach a half stroke into the gap
            with self.subTest(gap=centerline_gap):
                item_index, shape_index, opened = probe.aperture
                self.assertEqual((0, 0), (item_index, shape_index))
                self.assertEqual(1, len(opened.gap.segs))
                line = opened.gap.segs[0]
                self.assertIsInstance(line, glyph.Line)
                self.assertEqual(20, round(line.p0[0], 9))  # the right edge: 2 o'clock lands on a fillet, the run below holds it
                self.assertAlmostEqual(centerline_gap, glyph._chain_length(opened.gap))
                self.assertFalse(opened.drawn.closed)

    def test_circle_aperture_centers_on_the_clock_angle(self):
        for hour, point in ((3, (19, 12)), (12, (12, 5)), (6, (12, 19))):
            with self.subTest(hour=hour):
                _, probe = compile_one({"type": "circle", "center": [12, 12], "r": 7}, aperture=2, aperture_at=hour)
                gap = probe.aperture[2].gap
                middle = glyph._chain_point(gap, glyph._chain_length(gap) / 2)
                self.assertEqual(point, tuple(round(value, 6) for value in middle))

    def test_aperture_keeps_a_stroke_clear_of_other_shapes(self):
        family, probe = compile_one(
            {"type": "rounded-rect", "x": 5, "y": 11, "w": 14, "h": 9},
            {"type": "path", "d": "M8 11 V7.5 A4 4 0 0 1 16 7.5 V11"},
            aperture=1.5, aperture_at=12, linecap="butt",
        )
        gap = probe.aperture[2].gap
        shackle = probe.items[1].shapes[0]
        clearance = min(glyph._shape_distance(point, shackle) for point in glyph._shape_points(gap, 0.05))
        self.assertGreaterEqual(clearance, 2 * family.tokens.half + family.tokens.stroke - 1e-9)

    def test_solid_notch_removes_exactly_the_gap_band(self):
        family, probe = compile_one({"type": "rect", "x": 4, "y": 4, "w": 16, "h": 16}, aperture=2, linecap="butt")
        notched = glyph._solid_elements(family, probe)[0].shapes[0]
        full = glyph._grow(probe.items[0].shapes[0], family.tokens.half, family.tokens.linejoin)
        self.assertAlmostEqual(outline_area(full) - 2 * family.tokens.stroke, outline_area(notched), places=6)

    def test_aperture_refusals_and_quiet_fallbacks(self):
        family = glyph.compile_family(family_spec(shape_glyph(
            "gear", {"type": "gear", "center": [12, 12], "r": 9, "root": 7, "teeth": 8}), aperture=2))
        self.assertIsNone(family.glyphs[0].aperture)
        self.assertTrue(any("no clear place for the aperture" in warning for warning in family.warnings))
        excluded = glyph.compile_family(family_spec(shape_glyph(
            "box", {"type": "rounded-rect", "fit": "square", "aperture": False}), aperture=2))
        self.assertIsNone(excluded.glyphs[0].aperture)

    def test_junction_gap_stops_a_t_stem_short_and_keeps_the_bar(self):
        family, probe = compile_one({"type": "line", "from": [4, 7], "to": [20, 7]}, {"type": "line", "from": [12, 7], "to": [12, 18]},
                                    junction_gap=1, linecap="butt")
        (_, bar), (_, stem) = glyph._voiced_items(family, probe, "outline")
        self.assertEqual(((4, 7), (20, 7)), (bar[0].segs[0].p0, bar[0].segs[0].p1))
        self.assertEqual((12, 9), tuple(round(value, 6) for value in stem[0].segs[0].p0))  # bar half 1 + gap 1

    def test_junction_gap_counts_the_cap_and_cuts_the_stroke_behind_a_crossing(self):
        family, probe = compile_one({"type": "line", "from": [4, 12], "to": [20, 12]},
                                    {"type": "line", "from": [12, 4], "to": [12, 20]}, junction_gap=1)  # later is behind
        (_, front), (_, behind) = glyph._voiced_items(family, probe, "outline")
        self.assertEqual(1, len(front))
        ends = sorted(round(glyph._end(piece.segs[-1])[1], 6) for piece in behind[:1]) + \
            sorted(round(glyph._start(piece.segs[0])[1], 6) for piece in behind[1:])
        self.assertEqual([9, 15], ends)  # bar half 1 + gap 1 + round cap 1 on each side

    def test_contours_stay_whole_and_strokes_that_vanish_are_refused(self):
        family, probe = compile_one({"type": "rounded-rect", "fit": "square"},
                                    {"type": "line", "from": [4, 12], "to": [9, 12], "role": "detail"},
                                    junction_gap=1, linecap="butt")
        (_, frame), (_, detail) = glyph._voiced_items(family, probe, "outline")
        self.assertEqual(probe.items[0].shapes, frame)
        self.assertEqual(6, round(glyph._start(detail[0].segs[0])[0], 6))
        with self.assertRaises(glyph.SpecError) as raised:
            compile_one({"type": "rounded-rect", "fit": "square"}, {"type": "line", "from": [4, 12], "to": [6, 12], "role": "detail"},
                        junction_gap=1, linecap="butt")
        self.assertIn("removes this stroke entirely", " ".join(raised.exception.problems))

    def test_sub_pixel_gaps_close_in_an_optical_small_set(self):
        spec = family_spec(shape_glyph("probe", {"type": "line", "from": [4, 7], "to": [20, 7]},
                                       {"type": "line", "from": [12, 7], "to": [12, 18]}), junction_gap=1, linecap="butt")
        spec["target_sizes"] = [16, 20, 24, 32]
        family = glyph.compile_family(spec)
        self.assertEqual((24, [24, 32], [16, 20]), (family.open_from, family.main_sizes, family.small_sizes))
        files = glyph.render_family(family, json.dumps(spec).encode())
        self.assertEqual(6, sum(name.endswith(".svg") for name in files))  # three variants, main and small
        main, small = (json.loads(files[f"{folder}/probe.metadata.json"]) for folder in ("outline", "outline-small"))
        self.assertEqual(([24, 32], [16, 20]), (main["target_sizes"], small["target_sizes"]))
        self.assertEqual("probe-outline-small", small["name"])
        self.assertIn("M12 9V18", files["outline/probe.svg"].decode())
        self.assertIn("M12 7V18", files["outline-small/probe.svg"].decode())
        sheet = glyph.render_sheet(family, files)
        self.assertIn("M12 7V18", sheet)
        self.assertIn("gaps closed below 24 px", sheet)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "probe.json"
            path.write_text(json.dumps(spec), encoding="utf-8")
            self.assertEqual(6, glyph.build_family(path, Path(temporary) / "out")["validated"])
        spec["target_sizes"] = [32]
        self.assertIsNone(glyph.compile_family(spec).open_from)  # 1 unit is 1.33 px at 32: no small set needed


class CornerAndProportionTests(unittest.TestCase):
    def test_corner_styles_shape_every_polyline_corner(self):
        square = {"type": "rect", "x": 4, "y": 4, "w": 16, "h": 16, "radius": 3}
        _, chamfer = compile_one(square, corner="chamfer")
        segments = chamfer.items[0].shapes[0].segs
        self.assertFalse(any(isinstance(segment, glyph.Arc) for segment in segments))
        cuts = [segment for segment in segments if abs(segment.p0[0] - segment.p1[0]) > 1e-9 and abs(segment.p0[1] - segment.p1[1]) > 1e-9]
        self.assertEqual(4, len(cuts))
        self.assertTrue(all(math.isclose(glyph._length(glyph._sub(cut.p1, cut.p0)), 3 * math.sqrt(2)) for cut in cuts))
        _, sharp = compile_one(square, corner="sharp")
        self.assertEqual(4, len(sharp.items[0].shapes[0].segs))
        _, leaf = compile_one(square, corner="leaf")
        arcs = [segment for segment in leaf.items[0].shapes[0].segs if isinstance(segment, glyph.Arc)]
        self.assertEqual({(7, 7), (17, 17)}, {tuple(round(value, 6) for value in arc.c) for arc in arcs})  # upper left, lower right

    def test_corner_style_reaches_polylines_and_polygons(self):
        _, probe = compile_one(
            {"type": "polyline", "points": [[4, 18], [4, 6], [20, 6]], "radius": 2},
            {"type": "polygon", "center": [12, 14], "r": 4, "sides": 6, "radius": 1},
            corner="chamfer",
        )
        for item in probe.items:
            self.assertFalse(any(isinstance(segment, glyph.Arc) for shape in item.shapes for segment in shape.segs))

    def test_proportion_reshapes_rectangular_keylines_at_constant_area(self):
        def tokens(**extra) -> glyph.Tokens:
            return glyph._parse_tokens({**family_spec()["tokens"], **extra})

        regular, narrow, wide = tokens(), tokens(proportion="narrow"), tokens(proportion="wide")
        self.assertEqual((3.625, 2.375, 20.375, 21.625), narrow.keyline("square"))
        self.assertEqual((2.375, 3.625, 21.625, 20.375), wide.keyline("square"))
        self.assertEqual((2, 2, 22, 22), narrow.keyline("circle"))  # circles stay round
        self.assertEqual((4.5, 2, 19.5, 22), narrow.keyline("portrait"))  # the live area caps the long side
        for tokens in (narrow, wide):
            box = tokens.keyline("square")
            self.assertAlmostEqual(18 * 18, (box[2] - box[0]) * (box[3] - box[1]), delta=324 * 0.01)
            circle = tokens.keyline("circle")
            self.assertTrue(all(circle[2] - circle[0] >= tokens.keyline(kind)[2] - tokens.keyline(kind)[0] for kind in glyph.KEYLINES))
        self.assertEqual(regular.keyline("square"), (3, 3, 21, 21))

    def test_fill_shrinks_every_keyline_and_fitted_shapes_follow(self):
        family, probe = compile_one({"type": "circle", "fit": "circle"}, {"type": "rect", "fit": "square"}, fill=0.9, crisp=False)
        self.assertEqual((3, 3, 21, 21), family.tokens.keyline("circle"))
        self.assertEqual((3.875, 3.875, 20.125, 20.125), family.tokens.keyline("square"))
        circle, square = (item.shapes[0] for item in probe.items)
        self.assertEqual(8, circle.r)
        self.assertEqual((4.875, 4.875, 19.125, 19.125), rounded(glyph._shape_bounds(square)))


class AccentTests(unittest.TestCase):
    def accent_family(self, accent: dict) -> tuple[glyph.Family, glyph.Glyph]:
        return compile_one({"type": "circle", "center": [10.5, 10.5], "r": 6.5}, {"type": "line", "from": [15.5, 15.5], "to": [20, 20]},
                           accent, accent="the working part, filled")

    def test_accent_is_filled_inside_the_outline_variant(self):
        family, probe = self.accent_family({"type": "circle", "center": [8.5, 8.5], "r": 1, "role": "accent"})
        svg, mode = glyph.render_variant(family, probe, "outline")
        self.assertEqual("mixed", mode)
        self.assertIn('<circle cx="8.5" cy="8.5" r="2" fill="currentColor" stroke="none"/>', svg)  # grown by half a stroke

    def test_accent_cuts_out_of_a_solid_mass_or_stays_positive_on_open_ground(self):
        family, probe = self.accent_family({"type": "circle", "center": [8.5, 8.5], "r": 1, "role": "accent"})
        lens = glyph._solid_elements(family, probe)[0]
        self.assertEqual(glyph.Circle((8.5, 8.5), 2), lens.shapes[1])
        family, probe = self.accent_family({"type": "dot", "at": [19.5, 5], "d": 2.5, "role": "accent"})
        self.assertEqual(glyph.Circle((19.5, 5), 1.25), glyph._solid_elements(family, probe)[-1].shapes[0])

    def test_duotone_keeps_its_own_logic_for_the_accent(self):
        family, probe = self.accent_family({"type": "circle", "center": [8.5, 8.5], "r": 1, "role": "accent"})
        svg = glyph.render_variant(family, probe, "duotone")[0]
        primary = svg.split('data-icon-layer="primary"', 1)[1]
        self.assertIn('<circle cx="8.5" cy="8.5" r="1"/>', primary)  # stroked like any closed shape
        self.assertEqual(2, svg.split('data-icon-layer="primary"', 1)[0].count("<circle"))  # and tinted in the secondary layer

    def test_accent_refusals(self):
        lens = {"type": "circle", "center": [10.5, 10.5], "r": 6.5}
        cases = [
            (family_spec(shape_glyph("probe", lens, {"type": "dot", "at": [8, 8], "role": "accent"})), "declare tokens.accent"),
            (family_spec(shape_glyph("probe", lens, {"type": "dot", "at": [8, 8], "role": "accent", "repeat": {"count": 2, "step": [2, 0]}}),
                         accent="spark"), "one small element per glyph"),
            (family_spec(shape_glyph("probe", lens, {"type": "line", "from": [8, 8], "to": [9, 9], "role": "accent"}), accent="spark"),
             "closed shape or a dot"),
            (family_spec(shape_glyph("probe", {"type": "circle", "center": [12, 12], "r": 4, "role": "accent"}), accent="spark"),
             "at most a third of the live area"),
        ]
        for spec, expected in cases:
            with self.subTest(expected=expected):
                with self.assertRaises(glyph.SpecError) as raised:
                    glyph.compile_family(spec)
                self.assertIn(expected, " ".join(raised.exception.problems))


class CharacterRefusalTests(unittest.TestCase):
    def test_every_character_token_refusal(self):
        line = {"type": "line", "from": [4, 12], "to": [20, 12]}

        def spec(shape: dict = line, **tokens) -> dict:
            return family_spec(shape_glyph("probe", shape), **tokens)

        cases = [
            (spec(terminal="chisel"), "tokens.terminal must be one of"),
            (spec(terminal="angled"), 'set tokens.linecap to "butt"'),
            (spec(terminal="angled", linecap="butt", terminal_angle=7), "multiple of 5 degrees from 10 to 60"),
            (spec(terminal="angled", linecap="butt", terminal_angle=75), "multiple of 5 degrees from 10 to 60"),
            (spec(terminal="angled", linecap="butt", terminal_angle=30.0), "multiple of 5 degrees"),
            (spec(terminal_angle=30), 'applies only to tokens.terminal "angled"'),
            (spec(contrast=0.4), "tokens.contrast must be from 0.5 to 1"),
            (spec(contrast=0.975), "at most 2 decimals"),
            (spec(contrast=0.97, linecap="butt"), "rounds the detail stroke back to 2"),
            (spec(contrast="0.7"), "tokens.contrast must be a number"),
            (spec(aperture=0.25), "visible gap from 0.5 to 4 units"),
            (spec(aperture=1.3), "off the 0.25-unit construction grid"),
            (spec(aperture=2, aperture_at=13), "tokens.aperture_at must be an integer from 1 to 12"),
            (spec(aperture_at=2), "applies only with tokens.aperture"),
            (spec(junction_gap=3), "tokens.junction_gap must be from 0.25 to 2"),
            (spec(corner="scalloped"), "tokens.corner must be one of"),
            (spec(proportion="condensed"), "tokens.proportion must be one of"),
            (spec(fill=0.7), "tokens.fill must be from 0.75 to 1"),
            (spec(fill=0.875), "at most 2 decimals"),
            (spec(accent="<meaning>"), "placeholder"),
            (spec(linejoin="miter"), "miter joins need expanded outlines"),
            (spec({**line, "aperture": True}), "applies only with tokens.aperture"),
            (spec({**line, "junction": False}), "applies only with tokens.junction_gap"),
            (spec({**line, "aperture": True}, aperture=2), "only closed paths, polygons, rects and circles"),
            (spec({"type": "dot", "at": [12, 12], "role": "accent", "aperture": True}, aperture=2, accent="spark"),
             "cannot host the aperture"),
            (spec(junction_gap=0.25, linecap="butt"), "paint under 1 CSS px at every target size"),
            (spec(stroke=1, contrast=0.5, linecap="butt"), "below 0.5 CSS px"),
            (spec({"type": "arc", "center": [12, 12], "r": 2.5, "start": 40, "end": 140},
                  terminal="angled", terminal_angle=60, linecap="butt", stroke=2), "angled cut misses its curved stroke end"),
        ]
        for case, expected in cases:
            with self.subTest(expected=expected):
                with self.assertRaises(glyph.SpecError) as raised:
                    glyph.compile_family(case)
                self.assertIn(expected, " ".join(raised.exception.problems))

    def test_painted_geometry_is_bounded_as_the_validator_measures_it(self):
        with self.assertRaises(glyph.SpecError) as raised:
            glyph.compile_family(family_spec(shape_glyph("probe", {"type": "line", "from": [12, 4], "to": [12, 21]}),
                                             linecap="butt", terminal="angled", terminal_angle=60))
        self.assertIn("painted geometry reaches", " ".join(raised.exception.problems))


class VoiceDemoTests(unittest.TestCase):
    def test_voice_specs_build_validate_and_regenerate_byte_identically(self):
        for name in VOICES:
            with self.subTest(family=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                spec = EXAMPLES / f"{name}.json"
                first = glyph.build_family(spec, root / "a", root / "a.html")
                second = glyph.build_family(spec, root / "b", root / "b.html")
                family = glyph.compile_family(glyph.load_spec(spec))
                self.assertTrue(family.tokens.character)
                self.assertEqual(42 * len(family.sets()), first["validated"])
                self.assertEqual([], first["warnings"])
                self.assertEqual(first["files"], second["files"])
                for relative in first["files"]:
                    self.assertEqual((root / "a" / relative).read_bytes(), (root / "b" / relative).read_bytes(), relative)
                self.assertEqual((root / "a.html").read_bytes(), (root / "b.html").read_bytes())
                for svg in sorted((root / "a").rglob("*.svg")):
                    result = validate_svg_asset(svg, svg.with_name(f"{svg.stem}.metadata.json"))
                    self.assertTrue(result["valid"], (svg, result["errors"]))

    def test_each_voice_differs_from_its_monoline_baseline(self):
        for name in VOICES:
            with self.subTest(family=name):
                spec = glyph.load_spec(EXAMPLES / f"{name}.json")
                voice, baseline = glyph.compile_family(spec), glyph.compile_family(glyph.baseline_spec(spec))
                self.assertFalse(baseline.tokens.character and baseline.tokens.proportion == "regular")
                changed = sum(
                    glyph.render_variant(voice, glyph_a, "outline")[0] != glyph.render_variant(baseline, glyph_b, "outline")[0]
                    for glyph_a, glyph_b in zip(voice.glyphs, baseline.glyphs)
                )
                self.assertGreaterEqual(changed, 11, "a voice must change most glyphs, not one or two")


class CompareTests(unittest.TestCase):
    def test_compare_puts_one_spec_beside_its_monoline_baseline(self):
        spec = glyph.load_spec(EXAMPLES / "larder-almanac.json")
        baseline = glyph.baseline_spec(spec)
        self.assertEqual("larder-almanac-baseline", baseline["family"])
        self.assertEqual(("round", "round", 2), tuple(baseline["tokens"][key] for key in ("linecap", "linejoin", "radius")))
        self.assertFalse(set(glyph.CHARACTER_TOKENS) - {"proportion", "fill"} & set(baseline["tokens"]))
        self.assertEqual("narrow", baseline["tokens"]["proportion"])  # coordinates were drawn for these keylines
        with tempfile.TemporaryDirectory() as temporary:
            sheet = Path(temporary) / "compare.html"
            report = glyph.compare_families([EXAMPLES / "larder-almanac.json"], sheet, ["home", "search"])
            html_text = sheet.read_text(encoding="utf-8")
        self.assertEqual(["larder-almanac", "larder-almanac-baseline"], report["families"])
        self.assertEqual(2 * 2 * 2 * 2, html_text.count('class="i"'))  # light and dark x families x glyphs x sizes
        self.assertNotRegex(html_text, r"(?:src|href)=|url\(|@import|<script")

    def test_compare_refusals_and_cli(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(glyph.SpecError) as raised:
                glyph.compare_families([EXAMPLES / "larder-soft.json", EXAMPLES / "larder-linen.json"], root / "x.html", ["teapot"])
            self.assertIn("not in every compared family", " ".join(raised.exception.problems))
            command = [sys.executable, "-I", str(SCRIPTS / "glyph.py"), "compare", *(str(EXAMPLES / f"{name}.json") for name in VOICES),
                       "--sheet", str(root / "voices.html"), "--glyphs", "home,lock", "--sizes", "20,32", "--json"]
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False, timeout=120)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(list(VOICES), json.loads(result.stdout)["families"])
            bad = subprocess.run([*command[:-5], "--sizes", "4", "--sheet", str(root / "bad.html")], cwd=ROOT, capture_output=True,
                                 text=True, encoding="utf-8", check=False, timeout=120)
            self.assertEqual(2, bad.returncode)


if __name__ == "__main__":
    unittest.main()
