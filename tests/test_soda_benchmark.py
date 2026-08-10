from __future__ import annotations

import re
import struct
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SODA = ROOT / "benchmarks" / "soda-campaign"


class SodaHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids: set[str] = set()
        self.duplicates: set[str] = set()
        self.tags: list[str] = []
        self.references: list[str] = []
        self.buttons: list[str] = []
        self._button_depth = 0

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        self.tags.append(tag)
        element_id = values.get("id")
        if element_id:
            if element_id in self.ids:
                self.duplicates.add(element_id)
            self.ids.add(element_id)
        if tag in {"link", "script", "img"}:
            reference = values.get("href") or values.get("src")
            if reference:
                self.references.append(reference)
        if tag == "button":
            self._button_depth += 1
            self.buttons.append(values.get("aria-label", ""))

    def handle_endtag(self, tag):
        if tag == "button" and self._button_depth:
            self._button_depth -= 1

    def handle_data(self, data):
        if self._button_depth and data.strip():
            self.buttons[-1] += " " + data.strip()


class SodaBenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (SODA / "index.html").read_text(encoding="utf-8")
        cls.css = (SODA / "styles.css").read_text(encoding="utf-8")
        cls.js = (SODA / "app.js").read_text(encoding="utf-8")
        cls.parser = SodaHTMLParser()
        cls.parser.feed(cls.html)

    def test_complete_semantic_static_experience_and_local_references(self):
        for filename in ("index.html", "styles.css", "app.js", "README.md"):
            self.assertTrue((SODA / filename).is_file(), filename)
        for tag in ("header", "nav", "main", "h1", "form", "footer"):
            self.assertIn(tag, self.parser.tags)
        self.assertEqual(set(), self.parser.duplicates)
        self.assertTrue(all(label.strip() for label in self.parser.buttons))
        for reference in self.parser.references:
            self.assertFalse(reference.startswith(("http://", "https://", "//")), reference)
            self.assertTrue((SODA / reference).is_file(), reference)
        runtime = "\n".join((self.html, self.css, self.js))
        self.assertNotRegex(runtime, r"https?://")

    def test_product_flavors_conversion_and_disclosure_are_explicit(self):
        for phrase in (
            "carbonated soft drink",
            "Sun Shift",
            "Pink Noise",
            "Night Signal",
            "330 ml",
            "fictional mixed six-pack",
            "no order or payment is processed",
        ):
            self.assertIn(phrase.casefold(), self.html.casefold())
        self.assertIn('role="status"', self.html)
        self.assertIn('aria-pressed="true"', self.html)
        self.assertIn("Fictional demo only—no order or payment was sent.", self.js)

    def test_motion_interaction_responsive_and_reduced_modes_are_owned(self):
        for marker in (
            'pointerdown',
            'ArrowLeft',
            'ArrowRight',
            'visibilitychange',
            'window.__benchmarkReady = true',
            'window.__doppler',
            'return 32',
            'return 40',
            'return 48',
            'window.setTimeout(clearBubbles, 2600)',
        ):
            self.assertIn(marker, self.js)
        self.assertIn("@media (prefers-reduced-motion: reduce)", self.css)
        reduced_css = self.css.split("@media (prefers-reduced-motion: reduce)", 1)[1].split(
            "@media (forced-colors: active)", 1
        )[0]
        self.assertIn("transition: none !important;", reduced_css)
        self.assertNotIn("transition-duration:", reduced_css)
        self.assertIn("@media (max-width: 760px)", self.css)
        self.assertIn("@media (max-width: 1120px)", self.css)
        self.assertIn("data-static-can", self.html)
        self.assertIn("Math.ceil(yaw / 360) * 360", self.js)

    def test_design_trace_and_asset_provenance_are_complete(self):
        trace = SODA / "design-intelligence"
        for filename in ("BRIEF.md", "CANDIDATES.md", "DECISIONS.md", "ASSETS.md", "MOTION.md", "QA.md"):
            text = (trace / filename).read_text(encoding="utf-8")
            self.assertGreater(len(text), 500, filename)
        decisions = (trace / "DECISIONS.md").read_text(encoding="utf-8")
        candidates = (trace / "CANDIDATES.md").read_text(encoding="utf-8")
        qa = (trace / "QA.md").read_text(encoding="utf-8")
        self.assertIn("## Strongest rejected alternative", candidates)
        self.assertIn("## Responsive invariants and transformations", decisions)
        self.assertIn("Status: passed", qa)
        self.assertNotIn("proof pending", qa)
        for path in sorted((SODA / "assets" / "labels").glob("*.svg")):
            tree = ET.parse(path)
            root = tree.getroot()
            self.assertEqual("0 0 2760 1600", root.attrib.get("viewBox"), path.name)
            source = path.read_text(encoding="utf-8").casefold()
            self.assertNotIn("<script", source)
            runtime_source = source.replace('xmlns="http://www.w3.org/2000/svg"', "")
            self.assertNotRegex(runtime_source, r"https?://|data:image")

    def test_rendered_evidence_and_browser_smoke_contract(self):
        expected = {
            "wide-overview.jpg",
            "wide-hero.jpg",
            "wide-flavor.jpg",
            "intermediate.jpg",
            "mobile-hero.jpg",
            "mobile-interaction.jpg",
            "reduced-motion.jpg",
            "hero-motion.gif",
        }
        screenshot_dir = SODA / "screenshots"
        self.assertEqual(expected, {path.name for path in screenshot_dir.iterdir() if path.is_file()})
        self.assertTrue(all((screenshot_dir / name).stat().st_size > 20_000 for name in expected))
        gif = (screenshot_dir / "hero-motion.gif").read_bytes()
        self.assertIn(gif[:6], {b"GIF87a", b"GIF89a"})
        self.assertEqual((720, 560), struct.unpack("<HH", gif[6:10]))
        self.assertIn(b"NETSCAPE2.0", gif)

        smoke = (ROOT / "scripts" / "browser-smoke.mjs").read_text(encoding="utf-8")
        for marker in (
            'slug: "soda-campaign"',
            'interactSoda',
            'auditSodaReduced',
            'dragHorizontally',
            '--capture-soda',
            '--soda-motion-frames',
            'Doppler: expected ${expectedPanels} can segments',
            'Doppler: product lid layer is duplicated, detached, or misaligned',
            'Doppler: transient motion did not stop',
        ):
            self.assertIn(marker, smoke)

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        cross = (ROOT / "benchmarks" / "CROSS-BENCHMARK.md").read_text(encoding="utf-8")
        self.assertIn("Flagship expressive-motion showcase — Doppler Soda", readme)
        self.assertIn("benchmarks/soda-campaign/screenshots/hero-motion.gif", readme)
        self.assertIn("## Expressive-motion companion", cross)


if __name__ == "__main__":
    unittest.main()
