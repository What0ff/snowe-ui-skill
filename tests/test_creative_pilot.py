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

    def test_no_skill_snapshot_has_no_skill_and_rejects_one_added_later(self):
        briefs = self.root / "outcome/briefs.json"
        briefs.parent.mkdir()
        pilot.write(briefs, {"cases": [{"id": "fix", "name": "Fix", "brief": "Fix it", "seed": "fix"}]})
        (briefs.parent / "seeds/fix").mkdir(parents=True)
        (briefs.parent / "seeds/fix/index.html").write_text("<main>Seed</main>", encoding="utf-8")
        control = self.root / "control"
        pilot.snapshot(control, briefs=briefs, no_skill=True)
        record = pilot.validate_snapshot(control)
        self.assertEqual("no-skill", record["condition"])
        self.assertFalse((control / "snowe").exists())
        self.assertEqual(["fix/index.html"], [item["path"] for item in record["seeds"]])
        (control / "seeds/fix/index.html").write_text("<main>Edited</main>", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Frozen seeds changed"):
            pilot.validate_snapshot(control)
        (control / "seeds/fix/index.html").write_text("<main>Seed</main>", encoding="utf-8")
        (control / "snowe").mkdir()
        with self.assertRaisesRegex(ValueError, "Skill snapshot changed"):
            pilot.validate_snapshot(control)

    def test_snapshot_freezes_a_selected_skill_source(self):
        source = self.root / "old-skill"
        source.mkdir()
        (source / "SKILL.md").write_text("---\nname: snowe-ui-skill\n---\nOld", encoding="utf-8")
        frozen = self.root / "old"
        pilot.snapshot(frozen, source=source)
        self.assertEqual("skill", pilot.validate_snapshot(frozen)["condition"])
        self.assertEqual("---\nname: snowe-ui-skill\n---\nOld", (frozen / "snowe/SKILL.md").read_text(encoding="utf-8"))
        with self.assertRaisesRegex(ValueError, "no SKILL.md"):
            pilot.snapshot(self.root / "bad", source=self.root)
        with self.assertRaisesRegex(ValueError, "cannot also select"):
            pilot.snapshot(self.root / "mixed", source=source, no_skill=True)

    def test_no_skill_prompt_never_mentions_the_skill(self):
        case = {"brief": "Fixed facts"}
        self.assertNotIn("snowe", pilot.prompt_for(case, "no-skill").lower())
        self.assertIn("Use the explicitly selected local Snowe skill", pilot.prompt_for(case))
        self.assertIn(pilot.REQUIREMENTS, pilot.prompt_for(case, "no-skill"))
        self.assertIn(pilot.REQUIREMENTS, pilot.prompt_for(case))

    def test_global_install_blocks_no_skill_generation_before_any_evidence(self):
        home = self.root / "home"
        installed = home / ".agents/skills/snowe-ui-skill"
        installed.mkdir(parents=True)
        (installed / "SKILL.md").write_text("---\nname: snowe-ui-skill\n---\n", encoding="utf-8")
        (home / ".agents/skills/other").mkdir()
        self.assertEqual([str(installed)], pilot.global_skill_installations(home))
        control = self.root / "control"
        pilot.snapshot(control, no_skill=True)
        destination = self.root / "run-blocked"
        with patch.object(pilot, "global_skill_installations", return_value=[str(installed)]):
            with self.assertRaisesRegex(ValueError, "move it aside"):
                pilot.generate(control, "radio-workshop", 1, destination)
        self.assertFalse(destination.exists())

    def test_outcome_briefs_are_complete_and_seeds_exist(self):
        outcome = ROOT / "evals/skill-outcome"
        cases = json.loads((outcome / "briefs.json").read_text(encoding="utf-8"))["cases"]
        ids = [case["id"] for case in cases]
        self.assertEqual(len(ids), len(set(ids)))
        for case in cases:
            self.assertTrue(case["name"] and case["brief"], case["id"])
            if "seed" in case:
                self.assertTrue((outcome / "seeds" / case["seed"] / "index.html").is_file(), case["id"])
        legacy = {case["id"]: case for case in json.loads((ROOT / "evals/creative-search/briefs.json").read_text(encoding="utf-8"))["cases"]}
        self.assertEqual(legacy["radio-workshop"], next(case for case in cases if case["id"] == "radio-workshop"))

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
