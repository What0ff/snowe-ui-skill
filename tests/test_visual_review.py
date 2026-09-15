"""Proof-record checks only. Fixture bytes and verdicts are authored test data."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skill/snowe-ui-skill/scripts"
sys.path.insert(0, str(SCRIPTS))


class VisualReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "page.css").write_text("body{color:black}", encoding="utf-8")
        (self.root / "render.png").write_bytes(b"unit-test artifact; not an inspected picture")
        self.contract = {"schema": "1.0", "scope": "Run monitoring", "states": [{"id": "running",
            "question": "How is the current run progressing?", "priority": ["Run progress", "Kingdom status"],
            "cues": ["Progress value and related data form one group"], "competing": ["Create new"]}]}
        self.write("attention.json", self.contract)
        self.report = {"schema": "2.0", "scope": "Run monitoring", "method": "self-review", "reviewer": "Authored unit test",
            "contract": self.binding("attention.json"), "sources": [self.binding("page.css")],
            "renders": [{**self.binding("render.png"), "state": "running", "viewport": "900x700@1"}],
            "visualAssessment": {"verdict": "KEEP", "finding": "Authored passing record, not a visual assertion",
                "assessments": [{"state": "running", "renders": ["render.png"], "observedAttention": ["Run progress", "Kingdom status"], "finding": "Authored comparison", "verdict": "KEEP"}], "findings": []},
            "userAcceptance": "UNCONFIRMED"}

    def write(self, filename, value):
        (self.root / filename).write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    def binding(self, filename):
        return {"path": filename, "sha256": hashlib.sha256((self.root / filename).read_bytes()).hexdigest()}

    def inspect(self, report=None):
        from visual_review import inspect_review
        self.write("review.json", self.report if report is None else report)
        return inspect_review(self.root, "review.json")

    def issue(self, status="open"):
        return {"id": "attention", "states": ["running"], "owner": "Progress group", "observation": "Create new competes with progress",
            "consequence": "Current work is harder to identify", "blocking": True, "status": status, "renders": ["render.png"]}

    def test_method_is_not_a_verdict_and_legacy_never_becomes_keep(self):
        report = deepcopy(self.report)
        del report["visualAssessment"]["verdict"]
        self.assertEqual("REVIEW_REQUIRED", self.inspect(report)["status"])
        report["visualAssessment"]["verdict"] = "SELF_REVIEWED"
        with self.assertRaises(ValueError): self.inspect(report)
        legacy = {"schema": "1.0", "reviewer": "Earlier self-review", "visualAssessment": {"status": "SELF_REVIEWED", "finding": "Everything fits"}}
        self.assertEqual("REVIEW_REQUIRED", self.inspect(legacy)["status"])

    def test_explicit_keep_checks_evidence_without_claiming_user_acceptance(self):
        result = self.inspect()
        self.assertEqual("PASS", result["status"])
        self.assertEqual("KEEP", result["visual_verdict"])
        self.assertEqual("UNCONFIRMED", result["user_acceptance"])
        self.assertIn("not automated", result["boundary"])

    def test_open_finding_or_negative_state_blocks_claimed_keep(self):
        self.report["visualAssessment"]["findings"] = [self.issue()]
        self.assertEqual("BLOCKED", self.inspect()["status"])
        self.report["visualAssessment"]["verdict"] = "REVISE"
        self.report["visualAssessment"]["assessments"][0]["verdict"] = "REVISE"
        self.assertEqual("BLOCKED", self.inspect()["status"])
        self.report["visualAssessment"]["verdict"] = "KEEP"
        self.assertEqual("BLOCKED", self.inspect()["status"])

    def test_resolution_needs_current_render_and_a_reason(self):
        issue = self.issue("resolved")
        self.report["visualAssessment"]["findings"] = [issue]
        with self.assertRaises(ValueError): self.inspect()
        issue["resolution"] = "Progress emphasis restored in the bound render"
        self.assertEqual("PASS", self.inspect()["status"])
        (self.root / "render.png").write_bytes(b"different render")
        self.assertEqual("REVIEW_REQUIRED", self.inspect()["status"])

    def test_changed_contract_source_or_missing_render_invalidates_review(self):
        for filename in ("attention.json", "page.css", "render.png"):
            path = self.root / filename
            original = path.read_bytes()
            with self.subTest(filename=filename):
                path.write_bytes(original + b" ")
                self.assertEqual("REVIEW_REQUIRED", self.inspect()["status"])
                path.write_bytes(original)
        (self.root / "render.png").unlink()
        self.assertEqual("REVIEW_REQUIRED", self.inspect()["status"])

    def test_incomplete_state_coverage_cannot_pass(self):
        self.contract["states"].append({**self.contract["states"][0], "id": "complete", "priority": ["Result"]})
        self.write("attention.json", self.contract)
        self.report["contract"] = self.binding("attention.json")
        self.assertEqual("REVIEW_REQUIRED", self.inspect()["status"])

    def test_unbound_render_and_unsafe_path_are_invalid(self):
        self.report["visualAssessment"]["assessments"][0]["renders"] = ["other.png"]
        with self.assertRaises(ValueError): self.inspect()
        self.report["visualAssessment"]["assessments"][0]["renders"] = ["render.png"]
        self.report["sources"][0]["path"] = "../outside.css"
        with self.assertRaises(ValueError): self.inspect()

    def test_unknown_and_user_rejection_do_not_pass(self):
        self.report["visualAssessment"]["verdict"] = "UNKNOWN"
        self.assertEqual("REVIEW_REQUIRED", self.inspect()["status"])
        self.report["visualAssessment"]["verdict"] = "KEEP"
        self.report["userAcceptance"] = "REJECTED"
        self.assertEqual("BLOCKED", self.inspect()["status"])

    def test_check_is_read_only_and_cli_returns_machine_status(self):
        self.write("review.json", self.report)
        before = {path.name: path.read_bytes() for path in self.root.iterdir()}
        result = subprocess.run([sys.executable, str(SCRIPTS / "visual_review.py"), "review.json", "--workspace", str(self.root)], capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("PASS", json.loads(result.stdout)["status"])
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.root.iterdir()})


if __name__ == "__main__": unittest.main()
