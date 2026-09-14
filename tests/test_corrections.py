from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skill/snowe-ui-skill/scripts"))
from corrections import execute
from decision_packet import DecisionPacketGenerator, persist_decision_packet


class CorrectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.record = {"id": "type-role", "source": "User request", "requirement": "Keep body role coherent",
            "scope": {"owners": ["src/page.css"], "routes": ["/page"], "states": ["default"]},
            "criteria": [{"id": "render", "kind": "visual", "requirement": "Review page typography"}]}

    def call(self, command, data=None, project="Example"):
        return execute(command, workspace=self.root, project=project, payload=data)

    def prepare(self):
        self.call("record", self.record)
        self.call("update", {"id": "type-role", "status": "implemented", "note": "Corrected owner"})
        (self.root / "src").mkdir(exist_ok=True)
        (self.root / "src/page.css").write_text("body{font-weight:400}")
        (self.root / "review.png").write_bytes(b"authored test bytes, not an actual visual claim")
        def binding(name):
            return {"path": name, "sha256": hashlib.sha256((self.root / name).read_bytes()).hexdigest()}
        return {"sources": [binding("src/page.css")], "artifacts": [binding("review.png")],
            "results": [{"criterion": "render", "status": "PASS", "artifacts": ["review.png"],
                "review": {"reviewer": "Authored test", "finding": "Contract fixture only", "viewport": "390x844", "state": "default"}}]}

    def test_empty_check_creates_no_state(self):
        self.assertEqual("PASS", self.call("check")["status"])
        self.assertEqual([], list(self.root.iterdir()))

    def test_lifecycle_stale_source_and_lost_artifact(self):
        proof = self.prepare()
        self.assertEqual("BLOCKED", self.call("check")["status"])
        self.call("verify", {"id": "type-role", "proof": proof})
        self.assertEqual("PASS", self.call("check")["status"])
        (self.root / "src/page.css").write_text("body{font-weight:800}")
        self.assertEqual("REVIEW_REQUIRED", self.call("check")["status"])
        (self.root / "src/page.css").write_text("body{font-weight:400}")
        (self.root / "review.png").unlink()
        self.assertEqual("REVIEW_REQUIRED", self.call("check")["status"])

    def test_visual_screenshot_alone_cannot_verify(self):
        proof = self.prepare()
        del proof["results"][0]["review"]
        with self.assertRaises(ValueError): self.call("verify", {"id": "type-role", "proof": proof})
        self.assertEqual("BLOCKED", self.call("check")["status"])

    def test_proof_cannot_omit_owner_or_required_visual_state(self):
        proof = self.prepare()
        proof["sources"][0]["path"] = "unrelated.css"
        with self.assertRaises(ValueError): self.call("verify", {"id": "type-role", "proof": proof})
        self.call("update", {"id": "type-role", "note": "Include error state", "scope": {**self.record["scope"], "states": ["default", "error"]}})
        self.call("update", {"id": "type-role", "note": "Implemented states"})
        proof["sources"][0]["path"] = "src/page.css"
        with self.assertRaises(ValueError): self.call("verify", {"id": "type-role", "proof": proof})

    def test_invalid_creation_does_not_initialize_a_project(self):
        with self.assertRaises(ValueError): self.call("record", {"id": "bad"})
        with self.assertRaises(ValueError): self.call("update", {"id": "missing", "note": "unknown"})
        self.assertEqual([], list(self.root.iterdir()))

    def test_duplicate_conflict_and_scope_filter(self):
        self.call("record", self.record)
        self.assertFalse(self.call("record", self.record)["changed"])
        other = deepcopy(self.record); other["requirement"] = "Other meaning"
        with self.assertRaises(ValueError): self.call("record", other)
        unrelated = {"owners": ["other.css"], "routes": ["/elsewhere"], "states": ["default"]}
        self.assertEqual("PASS", self.call("check", unrelated)["status"])
        self.assertEqual("PASS", self.call("check", project="Other project")["status"])

    def test_supersession_remains_applicable_after_replacement_scope_edit(self):
        self.call("record", self.record)
        other = deepcopy(self.record); other["id"] = "replacement"
        self.call("record", other)
        self.call("supersede", {"id": "type-role", "replacement": "replacement", "note": "New user direction"})
        self.call("update", {"id": "replacement", "note": "Moved owner", "scope": {"owners": ["new.css"], "routes": ["/new"], "states": ["default"]}})
        self.assertIn("replacement", self.call("check", self.record["scope"])["blocked"])
        with self.assertRaises(ValueError): self.call("supersede", {"id": "replacement", "replacement": "type-role", "note": "cycle"})

    def test_decision_ledger_byte_preservation(self):
        packet = DecisionPacketGenerator().generate("Existing", "Example")
        result = persist_decision_packet(packet, output_dir=str(self.root))
        ledger = Path(result["design_intelligence_dir"]) / "DECISIONS.md"
        ledger.write_bytes("Принято\r\naccepted".encode())
        expected = ledger.read_bytes()
        self.prepare()
        self.assertEqual(expected, ledger.read_bytes())

    def test_failed_atomic_write_preserves_journal(self):
        self.call("record", self.record)
        path = self.root / "design-intelligence/example/CORRECTIONS.json"
        previous = path.read_bytes()
        with patch("corrections._atomic_write_text", side_effect=OSError("injected failure")):
            with self.assertRaises(OSError): self.call("update", {"id": "type-role", "note": "test"})
        self.assertEqual(previous, path.read_bytes())
        self.assertEqual("BLOCKED", self.call("check")["status"])

    def test_invalid_proof_paths_and_project_collision(self):
        proof = self.prepare()
        proof["sources"][0]["path"] = "../outside.css"
        with self.assertRaises(ValueError): self.call("verify", {"id": "type-role", "proof": proof})
        with self.assertRaises(ValueError): self.call("check", project="example")

    def test_journal_hardlink_refused(self):
        self.call("record", self.record)
        path = self.root / "design-intelligence/example/CORRECTIONS.json"
        (self.root / "other.json").hardlink_to(path)
        with self.assertRaises(ValueError): self.call("update", {"id": "type-role", "note": "test"})

    def test_concurrent_records_and_cli_exit_status(self):
        processes = []
        script = ROOT / "skill/snowe-ui-skill/scripts/corrections.py"
        for index in range(2):
            record = deepcopy(self.record); record["id"] = f"record-{index}"
            input_path = self.root / f"input-{index}.json"
            input_path.write_text(json.dumps(record))
            processes.append(subprocess.Popen([sys.executable, str(script), "record", "--workspace", str(self.root), "--project", "Example", "--input", str(input_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE))
        outputs = [process.communicate(timeout=30) for process in processes]
        for process, (stdout, stderr) in zip(processes, outputs):
            self.assertEqual(0, process.returncode, stderr)
            self.assertTrue(json.loads(stdout)["changed"])
        self.assertEqual(2, len(self.call("list")["records"]))
        result = subprocess.run([sys.executable, str(script), "check", "--workspace", str(self.root), "--project", "Example"], capture_output=True)
        self.assertEqual(2, result.returncode)
        self.assertEqual("BLOCKED", json.loads(result.stdout)["status"])


if __name__ == "__main__": unittest.main()
