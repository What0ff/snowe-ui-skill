"""Recorded visual judgments are authored evidence, never computed taste."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skill/snowe-ui-skill/scripts"))
from visual_review import inspect_review


class VisualJudgmentCaseTests(unittest.TestCase):
    def test_technical_success_does_not_override_recorded_visual_rejection(self):
        for variant, expected in (("a", "BLOCKED"), ("b", "BLOCKED"), ("c", "PASS"), ("d", "PASS")):
            result = inspect_review(ROOT, f"evals/visual-judgment/reviews/{variant}.json")
            self.assertEqual(expected, result["status"], result)
            self.assertEqual("PASS", result["integrity"])
            self.assertEqual("UNCONFIRMED", result["user_acceptance"])
        report = json.loads((ROOT / "evals/visual-judgment/reviews/b.json").read_text(encoding="utf-8"))
        self.assertEqual({"running": "KEEP", "complete": "REVISE", "error": "REVISE"}, {row["state"]: row["verdict"] for row in report["visualAssessment"]["assessments"]})

    def test_cases_bind_same_state_matrix_and_current_capture_bytes(self):
        base = ROOT / "evals/visual-judgment"
        manifest = json.loads((base / "captures/evidence.json").read_text(encoding="utf-8"))
        for item in manifest["sources"]:
            self.assertEqual(item["sha256"], hashlib.sha256((ROOT / item["file"]).read_bytes()).hexdigest(), item["file"])
        expected = {(v, s, w) for v in "abcd" for s in ("running", "complete", "error") for w in (900, 390)}
        self.assertEqual(expected, {(row["variant"], row["state"], row["viewport"]["width"]) for row in manifest["captures"]})
        self.assertEqual(len(expected), len(manifest["captures"]))
        for item in manifest["captures"]:
            raw = (base / "captures" / item["file"]).read_bytes()
            self.assertEqual(item["sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(b"\x89PNG\r\n\x1a\n", raw[:8])
            self.assertEqual(item["image"]["width"], int.from_bytes(raw[16:20], "big"))
            self.assertEqual(item["image"]["height"], int.from_bytes(raw[20:24], "big"))
            self.assertEqual("PASS", item["technical"])

    def test_legacy_report_is_preserved_without_implicit_keep(self):
        result = inspect_review(ROOT, "evals/titlebot-hierarchy/review-history/2026-09-15-schema1.json")
        self.assertEqual("REVIEW_REQUIRED", result["status"])
        self.assertEqual("UNKNOWN", result["visual_verdict"])
        self.assertEqual("PASS", inspect_review(ROOT, "evals/titlebot-hierarchy/REVIEW.json")["status"])


if __name__ == "__main__": unittest.main()
