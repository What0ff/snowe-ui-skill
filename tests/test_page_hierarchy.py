"""Authored route clauses and pilot evidence; not a visual taste test."""
import hashlib
import json
from pathlib import Path
import unittest

from tests.test_scope_contract import load_runner

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = ROOT / "skill/snowe-ui-skill"
PILOT = ROOT / "evals/titlebot-hierarchy"


class PageHierarchyTests(unittest.TestCase):
    def test_routes_and_critical_clauses_reject_removal(self):
        runner = load_runner()
        docs = {name: (PRODUCT / "references" / name).read_text(encoding="utf-8") for name in
                ("page-hierarchy.md", "experience-architecture.md", "exploration-protocol.md", "quality-gates.md")}
        docs["SKILL.md"] = (PRODUCT / "SKILL.md").read_text(encoding="utf-8")
        self.assertEqual([], runner.page_hierarchy_contract_failures(docs))
        for clause in runner.PAGE_HIERARCHY_CLAUSES:
            mutated = {**docs, "page-hierarchy.md": docs["page-hierarchy.md"].replace(clause, "")}
            self.assertTrue(runner.page_hierarchy_contract_failures(mutated), clause)
        for owner in docs.keys() - {"page-hierarchy.md"}:
            mutated = {**docs, owner: docs[owner].replace("page-hierarchy.md", "removed.md")}
            self.assertTrue(runner.page_hierarchy_contract_failures(mutated), owner)

    def test_pilot_capture_bytes_sources_states_and_geometry_are_bound(self):
        evidence = (PILOT / "captures/evidence.json").read_bytes()
        manifest = json.loads(evidence)
        review = json.loads((PILOT / "REVIEW.json").read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256(evidence).hexdigest(), review["evidence"]["sha256"])
        self.assertEqual("UNCONFIRMED", review["userAcceptance"])
        self.assertTrue(review["visualAssessment"]["finding"])
        for section, root in (("sources", PILOT), ("runnerSources", ROOT)):
            for item in manifest[section]:
                self.assertEqual(item["sha256"], hashlib.sha256((root / item["file"]).read_bytes()).hexdigest(), item["file"])
        captures = {item["file"]: item for item in manifest["captures"]}
        self.assertEqual(len(captures), len(manifest["captures"]))
        required = {f"{state}-{width}.png" for state in ("ready", "text200") for width in (320, 390, 900, 1440)}
        required |= {f"{state}-390.png" for state in ("empty", "loading", "error", "readonly", "saving", "russian", "settings")}
        required |= {f"{state}-1440.png" for state in ("justice", "duke", "architect", "scientist", "settings", "commands", "confirmation", "vip", "blocked")}
        required |= {f"error-{operation}-390.png" for operation in ("save", "advance", "remove", "add")}
        required.add("settings-russian-320.png")
        required.add("settings-russian-bottom-320.png")
        self.assertEqual(required, set(captures))
        self.assertEqual(required, set(review["inspectedCaptures"]))
        for filename, capture in captures.items():
            raw = (PILOT / "captures" / filename).read_bytes()
            self.assertEqual(b"\x89PNG\r\n\x1a\n", raw[:8])
            self.assertEqual(capture["sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(capture["image"]["width"], int.from_bytes(raw[16:20], "big"))
            self.assertEqual(capture["image"]["height"], int.from_bytes(raw[20:24], "big"))
            self.assertEqual(capture["viewport"]["width"], capture["image"]["width"])
            self.assertEqual(2 if filename.startswith("text200") else 1, capture["state"]["textScale"])
            self.assertNotIn("smoke=", capture["url"])
        self.assertTrue(captures["saving-390.png"]["state"]["pending"])
        self.assertEqual("PASS", manifest["technical"]["status"])
        self.assertNotEqual("PASS", manifest["userAcceptance"])

    def test_title_fixtures_expose_cross_context_errors(self):
        fixture = json.loads((PILOT / "fixtures.json").read_text(encoding="utf-8"))
        keys = {title["key"] for title in fixture["titles"]}
        self.assertEqual({"justice", "duke", "architect", "scientist"}, keys)
        self.assertEqual(keys, set(fixture["runtime"]["active"]))
        active = [row["player_id"] for row in fixture["runtime"]["active"].values() if row]
        queued = [row["player_id"] for rows in fixture["runtime"]["queues"].values() for row in rows]
        self.assertEqual(len(active+queued), len(set(active+queued)))
        self.assertGreater(len(fixture["runtime"]["queues"]["scientist"]), 20)
        self.assertFalse(fixture["runtime"]["active"]["duke"])
        self.assertFalse(fixture["runtime"]["queues"]["architect"])
        self.assertEqual(4, len(set(fixture["settings"]["durations"].values())))

    def test_report_notices_are_outside_customer_fixtures(self):
        for name in ("density", "acceptance-cases"):
            fixture = (ROOT / "evals" / name / "fixture.html").read_text(encoding="utf-8")
            for phrase in ("Fictional density regression", "Fictional acceptance fixture", "Passive symbols identify services", "Headings and reading text have different jobs"):
                self.assertNotIn(phrase, fixture)
        for name in ("SKILL.md", "references/page-hierarchy.md"):
            self.assertTrue((PRODUCT / name).is_file())


if __name__ == "__main__":
    unittest.main()
