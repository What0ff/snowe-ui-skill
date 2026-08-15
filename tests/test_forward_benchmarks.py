from __future__ import annotations

import json
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORWARD = ROOT / "benchmarks" / "forward-tests"


class ForwardHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.id_set = set()
        self.duplicate_ids = set()
        self.tags = []
        self.references = []
        self.dialog_labels = []
        self.current_button = 0
        self.button_text = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        self.tags.append(tag)
        if values.get("id"):
            if values["id"] in self.id_set:
                self.duplicate_ids.add(values["id"])
            self.id_set.add(values["id"])
            self.ids.append(values["id"])
        if tag in {"link", "script", "img"}:
            reference = values.get("href") or values.get("src")
            if reference:
                self.references.append(reference)
        if tag == "dialog":
            self.dialog_labels.append(values.get("aria-labelledby"))
        if tag == "button":
            self.current_button += 1
            self.button_text.append(values.get("aria-label", ""))

    def handle_endtag(self, tag):
        if tag == "button" and self.current_button:
            self.current_button -= 1

    def handle_data(self, data):
        if self.current_button and data.strip():
            self.button_text[-1] += " " + data.strip()


class ForwardBenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((FORWARD / "manifest.json").read_text(encoding="utf-8"))["benchmarks"]

    def test_three_materially_different_experience_classes_exist(self):
        self.assertEqual(3, len(self.manifest))
        for field in ("experience_class", "topology", "navigation", "composition", "content_model", "visual_carrier"):
            values = {item[field] for item in self.manifest}
            self.assertEqual(3, len(values), field)

    def test_discretionary_absence_is_proven(self):
        self.assertTrue(any(item["imagery_decision"] == "NO_GENERATED_IMAGERY" for item in self.manifest))
        self.assertTrue(any(item["custom_asset_decision"] == "NO_CUSTOM_ASSET" for item in self.manifest))
        self.assertTrue(any(item["motion_decision"] == "STATE_FEEDBACK_ONLY" for item in self.manifest))
        for item in self.manifest:
            directory = FORWARD / item["id"]
            visual_assets = [
                path for path in directory.rglob("*")
                if path.is_file() and path.suffix.casefold() in {".png", ".webp", ".svg", ".gif"}
            ]
            self.assertEqual([], visual_assets, item["id"])

    def test_each_experience_is_complete_semantic_and_local(self):
        for item in self.manifest:
            directory = FORWARD / item["id"]
            with self.subTest(benchmark=item["id"]):
                for filename in ("index.html", "styles.css", "app.js", "DECISIONS.md", "QA.md"):
                    self.assertTrue((directory / filename).is_file(), filename)
                html = (directory / "index.html").read_text(encoding="utf-8")
                parser = ForwardHTMLParser()
                parser.feed(html)
                self.assertIn("main", parser.tags)
                self.assertIn("h1", parser.tags)
                self.assertIn("nav", parser.tags)
                self.assertEqual(set(), parser.duplicate_ids)
                self.assertTrue(all(text.strip() for text in parser.button_text))
                self.assertTrue(all(label in parser.id_set for label in parser.dialog_labels if label))
                self.assertNotIn("<img", html.casefold())
                for reference in parser.references:
                    self.assertFalse(reference.startswith(("http://", "https://")), reference)
                    self.assertTrue((directory / reference).is_file(), reference)

    def test_decision_records_cover_causal_architecture_and_absence(self):
        required = (
            "## Brief",
            "## Chosen architecture",
            "## Strongest rejected alternative",
            "## Art direction and assets",
            "## Motion",
            "## Responsive transformation",
        )
        for item in self.manifest:
            text = (FORWARD / item["id"] / "DECISIONS.md").read_text(encoding="utf-8")
            with self.subTest(benchmark=item["id"]):
                for heading in required:
                    self.assertIn(heading, text)
                self.assertIn("rejected", text.casefold())
                self.assertIn("generated imagery", text.casefold())

    def test_responsive_reduced_motion_and_interactions_are_explicit(self):
        markers = {
            "municipal-service": ("eligibility-errors", "status-dialog", "language-toggle", "@media (max-width: 600px)"),
            "warehouse-operations": ("resolve-dialog", "queue-search", "rail-toggle", "@media (max-width: 760px)"),
            "literary-publication": ("membership-dialog", "archive-search", "issue-toggle", "@media (max-width: 640px)"),
        }
        for item in self.manifest:
            directory = FORWARD / item["id"]
            combined = "\n".join(
                (directory / filename).read_text(encoding="utf-8")
                for filename in ("index.html", "styles.css", "app.js")
            )
            with self.subTest(benchmark=item["id"]):
                for marker in markers[item["id"]]:
                    self.assertIn(marker, combined)
                self.assertIn("prefers-reduced-motion: reduce", combined)
                self.assertIn("window.__benchmarkReady = true", combined)

    def test_cross_benchmark_review_covers_template_dimensions(self):
        text = (ROOT / "benchmarks" / "CROSS-BENCHMARK.md").read_text(encoding="utf-8")
        for title in ("Goodturn", "Larkhaven", "Relay North", "Morrow"):
            self.assertIn(title, text)
        for dimension in (
            "Topology", "Navigation", "Opening construction", "Action placement", "Visual carrier",
            "Card usage", "Imagery posture", "Custom assets", "Motion grammar", "Responsive transformation",
        ):
            self.assertIn(dimension, text)
        self.assertIn("Similarity", text)
        self.assertIn("Hidden-template audit", text)

    def test_final_screenshots_cover_wide_pressure_narrow_and_states(self):
        for item in self.manifest:
            directory = FORWARD / item["id"] / "screenshots"
            with self.subTest(benchmark=item["id"]):
                self.assertEqual(set(item["screenshots"]), {path.name for path in directory.glob("*.jpg")})
                self.assertTrue(all((directory / name).stat().st_size > 20_000 for name in item["screenshots"]))

    def test_rendered_qa_records_real_findings_and_completion(self):
        combined = ""
        for item in self.manifest:
            text = (FORWARD / item["id"] / "QA.md").read_text(encoding="utf-8")
            with self.subTest(benchmark=item["id"]):
                self.assertIn("Status: passed", text)
                self.assertNotIn("pending first browser pass", text)
                self.assertIn("## Findings and response", text)
            combined += text
        self.assertIn("[data-filter]", combined)
        self.assertIn("tablet grid placement", combined)

    def test_ci_runs_behavior_eval_and_dependency_free_browser_smoke(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        smoke = (ROOT / "scripts" / "browser-smoke.mjs").read_text(encoding="utf-8")
        self.assertIn("python evals/designer-behavior/run_eval.py", workflow)
        self.assertIn("node scripts/browser-smoke.mjs --smoke", workflow)
        self.assertIn("repository-context:", workflow)
        self.assertIn(
            "python scripts/check_contributor_context.py --require-tracked", workflow
        )
        self.assertIn("python scripts/atlas/generate_atlas.py --check", workflow)
        self.assertIn("actions/setup-node@v4", workflow)
        browser_job = workflow.split("  browser-smoke:", 1)[1]
        self.assertIn("os: [ubuntu-latest, windows-latest]", browser_job)
        self.assertIn('from "node:http"', smoke)
        self.assertIn("prefers-reduced-motion", smoke)
        self.assertIn("await stopBrowserProcess(browser)", smoke)
        self.assertIn("maxRetries: 12", smoke)
        self.assertNotIn("playwright", smoke.casefold())


if __name__ == "__main__":
    unittest.main()
