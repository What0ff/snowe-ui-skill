from __future__ import annotations

import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = REPO_ROOT / "benchmarks" / "bicycle-commerce"
SKILL_SCRIPTS = REPO_ROOT / "skill" / "snowe-ui-skill" / "scripts"

import sys

sys.path.insert(0, str(SKILL_SCRIPTS))

from asset_quality import validate_svg_asset  # noqa: E402


class BenchmarkHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids: list[str] = []
        self.images: list[dict[str, str | None]] = []
        self.dialog_labels: list[str | None] = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"])
        if tag == "img":
            self.images.append({"src": values.get("src"), "alt": values.get("alt")})
        if tag == "dialog":
            self.dialog_labels.append(values.get("aria-labelledby"))


def jpeg_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if not data.startswith(b"\xff\xd8"):
        raise AssertionError(f"{path} is not JPEG data")
    index = 2
    start_of_frame = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    while index + 8 < len(data):
        if data[index] != 0xFF:
            index += 1
            continue
        marker = data[index + 1]
        index += 2
        if marker in {0xD8, 0xD9}:
            continue
        segment_length = int.from_bytes(data[index : index + 2], "big")
        if marker in start_of_frame:
            height = int.from_bytes(data[index + 3 : index + 5], "big")
            width = int.from_bytes(data[index + 5 : index + 7], "big")
            return width, height
        index += segment_length
    raise AssertionError(f"No JPEG dimensions found in {path}")


class BicycleBenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (BENCHMARK / "index.html").read_text(encoding="utf-8")
        cls.css = (BENCHMARK / "styles.css").read_text(encoding="utf-8")
        cls.javascript = (BENCHMARK / "app.js").read_text(encoding="utf-8")
        cls.parser = BenchmarkHTMLParser()
        cls.parser.feed(cls.html)

    def test_offer_is_concrete_and_commercially_legible(self):
        for name, price in (("Turn One", "€1,290"), ("Turn Step", "€1,490"), ("Turn Cargo", "€2,790")):
            self.assertIn(name, self.html)
            self.assertIn(price, self.html + self.javascript)
        for evidence in ("Personal fit", "Free test rides", "12-month care", "Reserve for €50", "city delivery €35"):
            self.assertIn(evidence.casefold(), self.html.casefold())
        self.assertIn("fictional", self.html.casefold())
        self.assertIn("generated", self.html.casefold())

    def test_page_assets_are_local_labeled_and_complete(self):
        self.assertEqual(5, len(self.parser.images))  # hero + 3 rows + one dialog template
        self.assertTrue(all(image["alt"] is not None for image in self.parser.images))
        self.assertTrue(all(not str(image["src"]).startswith(("http://", "https://")) for image in self.parser.images))
        for filename in ("goodturn-hero.webp", "turn-one.webp", "turn-step.webp", "turn-cargo.webp"):
            path = BENCHMARK / "assets" / "images" / filename
            self.assertGreater(path.stat().st_size, 100_000)

    def test_semantics_and_dialog_references_are_stable(self):
        self.assertEqual(len(self.parser.ids), len(set(self.parser.ids)))
        self.assertEqual(1, len(re.findall(r"<h1\b", self.html)))
        self.assertEqual(1, len(re.findall(r"<main\b", self.html)))
        self.assertIn('lang="en"', self.html)
        for label_id in self.parser.dialog_labels:
            self.assertIsNotNone(label_id)
            self.assertIn(label_id, self.parser.ids)
        self.assertIn('aria-label="Open menu"', self.html)
        self.assertIn('tabindex="-1">Turn One', self.html)

    def test_interactions_cover_choice_comparison_and_conversion(self):
        for contract in (
            "renderCompareState",
            "finishFinder",
            "fillProductDialog",
            "showBooking",
            "renderCart",
            "showModal",
            "reportValidity",
            "prefers-reduced-motion",
            'setAttribute("aria-label", willOpen ? "Close menu" : "Open menu")',
        ):
            source = self.css if contract == "prefers-reduced-motion" else self.javascript
            self.assertIn(contract, source)
        self.assertIn("Choose Tuesday through Saturday", self.javascript)
        self.assertIn("refundable hold", self.javascript.casefold())

    def test_responsive_and_accessibility_branches_are_explicit(self):
        for breakpoint in ("1240px", "980px", "720px"):
            self.assertIn(f"@media (max-width: {breakpoint})", self.css)
        self.assertIn("@media (prefers-reduced-motion: reduce)", self.css)
        self.assertIn("@media (forced-colors: active)", self.css)
        self.assertIn(":focus-visible", self.css)
        self.assertIn("min-width: 44px", self.css)
        self.assertNotRegex(self.css, r"url\([\"']?https?://")

    def test_custom_icons_pass_structural_and_provenance_validation(self):
        icon_root = BENCHMARK / "assets" / "icons"
        for name in ("fit", "test-ride", "workshop", "delivery"):
            result = validate_svg_asset(icon_root / f"{name}.svg", icon_root / f"{name}.metadata.json")
            self.assertTrue(result["valid"], result["errors"])
            metadata = json.loads((icon_root / f"{name}.metadata.json").read_text(encoding="utf-8"))
            self.assertTrue({16, 20, 24}.issubset(metadata["target_sizes"]))

    def test_design_trace_records_rejected_alternative_and_rendered_learning(self):
        record = BENCHMARK / "design-intelligence" / "goodturn-cycles"
        decisions = (record / "DECISIONS.md").read_text(encoding="utf-8")
        qa = (record / "QA.md").read_text(encoding="utf-8")
        self.assertIn("Strongest rejected alternative", decisions)
        self.assertIn("causal decision graph", decisions.casefold())
        self.assertIn("Pass 1 findings", qa)
        self.assertIn("REVISE", qa)
        self.assertIn("Pass 2 evidence", qa)
        self.assertIn("Remaining limits", qa)

    def test_final_screenshots_cover_wide_pressure_narrow_and_states(self):
        screenshot_root = BENCHMARK / "screenshots"
        required = (
            "desktop-home.jpg",
            "desktop-products.jpg",
            "desktop-compare.jpg",
            "desktop-finder.jpg",
            "desktop-workshop.jpg",
            "intermediate-home.jpg",
            "mobile-home.jpg",
            "mobile-menu.jpg",
            "mobile-product-sheet.jpg",
        )
        dimensions = {name: jpeg_dimensions(screenshot_root / name) for name in required}
        self.assertGreaterEqual(dimensions["desktop-home.jpg"][0], 1400)
        self.assertGreaterEqual(dimensions["intermediate-home.jpg"][0], 850)
        self.assertLessEqual(dimensions["intermediate-home.jpg"][0], 920)
        self.assertGreaterEqual(dimensions["mobile-home.jpg"][0], 360)
        self.assertLessEqual(dimensions["mobile-home.jpg"][0], 400)
        self.assertTrue(all(height >= 800 for _, height in dimensions.values()))
        self.assertTrue(all((screenshot_root / name).stat().st_size > 30_000 for name in required))

        root_readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        for name in (
            "desktop-home.jpg",
            "desktop-products.jpg",
            "desktop-compare.jpg",
            "desktop-finder.jpg",
            "intermediate-home.jpg",
            "mobile-home.jpg",
            "mobile-product-sheet.jpg",
        ):
            self.assertIn(f"benchmarks/bicycle-commerce/screenshots/{name}", root_readme)


if __name__ == "__main__":
    unittest.main()
