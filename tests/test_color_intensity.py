"""Declared example color roles and contrast, not a global saturation score."""
import colorsys
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skill/snowe-ui-skill/scripts"))
from contrast import contrast_ratio, parse_opaque_color
from visual_review import inspect_review


class ColorIntensityTests(unittest.TestCase):
    def setUp(self):
        self.base = ROOT / "evals/color-intensity"
        self.palettes = json.loads((self.base / "PALETTES.json").read_text(encoding="utf-8"))

    def test_declared_richer_example_is_not_just_a_lighter_tint(self):
        def hls(color): return colorsys.rgb_to_hls(*(channel/255 for channel in parse_opaque_color(color)))
        soft, vivid = self.palettes["soft"], self.palettes["vivid"]
        self.assertLess(hls(vivid["fill"])[1], hls(soft["fill"])[1])
        for role in ("fill", "foreground", "success", "danger"):
            self.assertGreater(hls(vivid[role])[2], hls(soft[role])[2], role)
        self.assertNotEqual(vivid["fill"], vivid["foreground"])
        # These relations protect this explicitly authored comparison only.

    def test_both_palettes_keep_contrast_with_role_specific_foregrounds(self):
        for name in ("soft", "vivid", "ocean", "plum"):
            p = self.palettes[name]
            for state in ("fill", "hover", "active"):
                self.assertGreaterEqual(contrast_ratio(p["onFill"], p[state]), 4.5, (name, state))
            for role in ("foreground", "success", "danger"):
                self.assertGreaterEqual(contrast_ratio(p[role], p["surface"]), 4.5, (name, role))
            for foreground, background in (("text", "canvas"), ("text", "surface"), ("muted", "tableHead"), ("dialogText", "dialog"), ("text", "control")):
                self.assertGreaterEqual(contrast_ratio(p[foreground], p[background]), 4.5, (name, foreground, background))
        self.assertLess(contrast_ratio("#ffffff", self.palettes["vivid"]["fill"]), 4.5)

    def test_native_color_captures_and_resolved_paint_are_current(self):
        evidence = json.loads((self.base / "captures/evidence.json").read_text(encoding="utf-8"))
        for item in evidence["sources"]:
            self.assertEqual(item["sha256"], hashlib.sha256((ROOT / item["file"]).read_bytes()).hexdigest())
        expected = {(palette, state, width) for palette in ("soft", "vivid", "ocean", "plum") for state in ("complete", "error") for width in (900, 390)}
        self.assertEqual(expected, {(item["palette"], item["state"], item["width"]) for item in evidence["captures"]})
        for item in evidence["captures"]:
            raw = (self.base / "captures" / item["file"]).read_bytes()
            self.assertEqual(item["sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(b"\x89PNG\r\n\x1a\n", raw[:8])
            self.assertEqual(item["width"], int.from_bytes(raw[16:20], "big"))
            for state in ("button", "hover", "active"):
                role = item[state]
                self.assertGreaterEqual(contrast_ratio(role["color"], role["background"]), 4.5)
                self.assertEqual(1, role["opacity"])
                self.assertFalse(role["filters"])
            if item["state"] == "complete":
                modal = item["modal"]
                raw = (self.base / "captures" / modal["file"]).read_bytes()
                self.assertEqual(modal["sha256"], hashlib.sha256(raw).hexdigest())
                self.assertEqual(item["width"], int.from_bytes(raw[16:20], "big"))
                self.assertGreaterEqual(contrast_ratio(modal["content"]["color"], modal["panel"]["background"]), 4.5)

    def test_colored_surfaces_are_not_an_acceptance_shortcut(self):
        for name in ("ocean", "plum"):
            palette = self.palettes[name]
            for role in ("canvas", "surface", "tableHead", "dialog", "control"):
                rgb = parse_opaque_color(palette[role])
                saturation = colorsys.rgb_to_hls(*(channel/255 for channel in rgb))[2]
                self.assertGreater(saturation, .35, (name, role))
                self.assertNotEqual(palette[role], self.palettes["soft"][role])
            review = inspect_review(ROOT, f"evals/color-intensity/reviews/{name}.json")
            self.assertEqual("PASS", review["integrity"])
            self.assertEqual("REJECT", review["visual_verdict"])
            self.assertEqual("BLOCKED", review["status"])
        # The measurable non-neutral colors still fail the recorded contextual judgment.


if __name__ == "__main__": unittest.main()
