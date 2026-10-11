"""Pilot integrity and failure contracts; these tests never invoke a model."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("creative_pilot", ROOT / "evals/creative-search/run_pilot.py")
pilot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pilot)


class CreativePilotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.snapshot = self.root / "snapshot"
        (self.snapshot / "snowe").mkdir(parents=True)
        (self.snapshot / "snowe/SKILL.md").write_text("Frozen product", encoding="utf-8")
        pilot.write(self.snapshot / "briefs.json", {"cases": [{"id": "test", "brief": "Fixed facts"}]})
        pilot.write(self.snapshot / "snapshot.json", {
            "schema": "1.0", "files": pilot.inventory(self.snapshot / "snowe"),
            "briefs_sha256": pilot.digest(self.snapshot / "briefs.json"),
        })

    def make_run(self):
        run = self.root / "run"
        (run / "site").mkdir(parents=True)
        (run / "site/index.html").write_text("<main>Original</main>", encoding="utf-8")
        (run / "prompt.txt").write_text("Fixed prompt", encoding="utf-8")
        pilot.write(run / "run.json", {
            "status": "GENERATED", "snapshot": str(self.snapshot),
            "snapshot_sha256": pilot.digest(self.snapshot / "snapshot.json"),
            "site_files": pilot.inventory(run / "site"),
            "prompt_sha256": pilot.digest(run / "prompt.txt"),
        })
        return run

    def test_snapshot_rejects_changed_skill_and_changed_brief(self):
        pilot.validate_snapshot(self.snapshot)
        (self.snapshot / "snowe/SKILL.md").write_text("Changed product", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Skill snapshot changed"):
            pilot.validate_snapshot(self.snapshot)
        (self.snapshot / "snowe/SKILL.md").write_text("Frozen product", encoding="utf-8")
        (self.snapshot / "briefs.json").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Frozen briefs changed"):
            pilot.validate_snapshot(self.snapshot)

    def test_artifact_changes_and_added_resources_invalidate_run(self):
        run = self.make_run()
        pilot.validate_run(run)
        (run / "site/extra.css").write_text("body{}", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "artifact changed"):
            pilot.validate_run(run)

    def test_incomplete_subject_and_changed_prompt_cannot_be_accepted(self):
        run = self.make_run()
        (run / "prompt.txt").write_text("New instructions", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "prompt changed"):
            pilot.validate_run(run)
        record = json.loads((run / "run.json").read_text(encoding="utf-8"))
        record["status"] = "INCOMPLETE"
        pilot.write(run / "run.json", record)
        with self.assertRaisesRegex(ValueError, "Incomplete generation"):
            pilot.validate_run(run)

    def test_usage_comes_only_from_completed_turn_events(self):
        events = self.root / "events.jsonl"
        events.write_text('not json\n{"type":"turn.started","usage":{"input_tokens":999}}\n'
                          '{"type":"turn.completed","usage":{"input_tokens":10,"output_tokens":5}}\n'
                          '{"type":"turn.completed","usage":{"input_tokens":20,"output_tokens":4}}\n',
                          encoding="utf-8")
        self.assertEqual(pilot.usage(events), {"input_tokens": 30, "output_tokens": 9})

    def test_fresh_destination_never_overwrites_previous_evidence(self):
        with self.assertRaises(FileExistsError):
            pilot.fresh(self.snapshot)

    def test_snapshot_cannot_recursively_copy_into_the_product(self):
        product = self.root / "skill/snowe-ui-skill"
        product.mkdir(parents=True)
        target = product / "evaluation"
        with patch.object(pilot, "ROOT", self.root):
            with self.assertRaisesRegex(ValueError, "outside the installed product"):
                pilot.snapshot(target)
        self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
