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
        return self.current_proof()

    def current_proof(self, owner="src/page.css"):
        from tests.evidence_factory import make_review, binding
        report = make_review(self.root, owner=owner, state="default", viewport="390x844@1", image="review.png")
        return {"sources": report["sources"], "artifacts": [binding(self.root, "review.png"), binding(self.root, "review.json")],
            "results": [{"criterion": "render", "status": "PASS", "artifacts": ["review.png", "review.json"],
                "review": {"reviewer": "Authored test", "finding": "Contract fixture only", "viewport": "390x844@1", "state": "default", "method": "self-review", "verdict": "KEEP", "report": "review.json"}}]}

    def test_empty_check_creates_no_state(self):
        result = self.call("check")
        self.assertEqual("PASS", result["status"])
        self.assertEqual("absent", result["journal"])
        self.assertEqual([], list(self.root.iterdir()))

    def test_missing_workspace_fails_instead_of_passing_or_creating(self):
        missing = self.root / "typo-ws" / "deep"
        for command, data in (("check", None), ("list", None), ("record", self.record)):
            with self.assertRaises(ValueError, msg=command):
                execute(command, workspace=missing, project="Example", payload=data)
        self.assertFalse((self.root / "typo-ws").exists())

    def test_unknown_identity_beside_existing_journal_is_not_a_pass(self):
        self.call("record", self.record, project="Harbor")
        result = self.call("check", project="Harbour")
        self.assertEqual("NO_JOURNAL", result["status"])
        self.assertEqual(["Harbor"], result["known_projects"])
        self.assertEqual(["Harbor"], self.call("list", project="Harbour")["known_projects"])
        self.assertEqual("BLOCKED", self.call("check", project="Harbor")["status"])
        cli = subprocess.run([sys.executable, str(ROOT / "skill/snowe-ui-skill/scripts/corrections.py"), "check",
            "--workspace", str(self.root), "--project", "Harbour"], capture_output=True, text=True, timeout=60)
        self.assertEqual(4, cli.returncode, cli.stderr)

    def test_dot_prefixed_owner_scope_selects_the_same_record(self):
        self.call("record", self.record)
        active = {"owners": ["./src/page.css"], "routes": [], "states": []}
        self.assertEqual(["type-role"], self.call("check", active)["applicable"])

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

    def test_negative_visual_verdict_cannot_close_correction(self):
        proof = self.prepare()
        proof["results"][0]["review"].update(method="self-review", verdict="REVISE")
        with self.assertRaises(ValueError): self.call("verify", {"id": "type-role", "proof": proof})
        self.assertEqual("BLOCKED", self.call("check")["status"])

    def test_new_visual_proof_requires_method_explicit_keep_and_checked_report(self):
        proof = self.prepare()
        for field in ("method", "verdict", "report"):
            candidate = deepcopy(proof)
            del candidate["results"][0]["review"][field]
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.call("verify", {"id": "type-role", "proof": candidate})
        self.assertEqual("BLOCKED", self.call("check")["status"])

    def test_historical_inline_proof_is_readable_without_grandfathering_pass(self):
        proof = self.prepare()
        self.call("verify", {"id": "type-role", "proof": proof})
        path = self.root / "design-intelligence/example/CORRECTIONS.json"
        journal = json.loads(path.read_bytes())
        entry = journal["records"][0]
        for record in [entry, entry["history"][-1]["snapshot"]]:
            for field in ("method", "verdict", "report"): record["proof"]["results"][0]["review"].pop(field)
        path.write_text(json.dumps(journal), encoding="utf-8")
        before = path.read_bytes()
        self.assertEqual("REVIEW_REQUIRED", self.call("check")["status"])
        self.assertEqual(before, path.read_bytes())

    def test_linked_visual_report_and_its_contract_stay_current(self):
        proof = self.prepare()
        self.call("verify", {"id": "type-role", "proof": proof})
        self.assertEqual("PASS", self.call("check")["status"])
        (self.root / "attention.json").write_bytes((self.root / "attention.json").read_bytes()+b" ")
        self.assertEqual("REVIEW_REQUIRED", self.call("check")["status"])

    def test_user_rejection_reopens_verified_work_without_source_changes(self):
        proof = self.prepare()
        self.call("verify", {"id": "type-role", "proof": proof})
        self.assertEqual("PASS", self.call("check")["status"])
        self.call("update", {"id": "type-role", "status": "requested", "note": "User rejected the visual result as unfinished"})
        self.assertEqual("BLOCKED", self.call("check")["status"])
        record = self.call("list")["records"][0]
        self.assertNotIn("proof", record)
        self.assertTrue(any(item["status"] == "verified" for item in record["history"]))

    def test_definition_and_proof_edits_invalidate_confirmation_without_writing(self):
        proof = self.prepare()
        self.call("verify", {"id": "type-role", "proof": proof})
        path = self.root / "design-intelligence/example/CORRECTIONS.json"
        original = path.read_bytes()
        for field in ("requirement", "source", "criteria", "proof"):
            journal = json.loads(original)
            entry = journal["records"][0]
            if field in {"requirement", "source"}: entry[field] = "Changed after verification"
            elif field == "criteria": entry["criteria"][0]["requirement"] = "Another obligation"
            else: entry["proof"]["results"][0]["review"]["finding"] = "Another review"
            path.write_text(json.dumps(journal), encoding="utf-8")
            edited = path.read_bytes()
            with self.subTest(field=field):
                self.assertEqual("REVIEW_REQUIRED", self.call("check")["status"])
                self.assertEqual(edited, path.read_bytes())

    def test_scope_edit_cannot_hide_previous_verified_obligation(self):
        proof = self.prepare()
        self.call("verify", {"id": "type-role", "proof": proof})
        path = self.root / "design-intelligence/example/CORRECTIONS.json"
        journal = json.loads(path.read_bytes())
        journal["records"][0]["scope"] = {"owners": [], "routes": ["/elsewhere"], "states": ["default"]}
        path.write_text(json.dumps(journal), encoding="utf-8")
        result = self.call("check", self.record["scope"])
        self.assertEqual("REVIEW_REQUIRED", result["status"])
        self.assertIn("type-role", result["applicable"])

    def test_legacy_unbound_confirmation_requires_explicit_reverification(self):
        proof = self.prepare()
        self.call("verify", {"id": "type-role", "proof": proof})
        path = self.root / "design-intelligence/example/CORRECTIONS.json"
        journal = json.loads(path.read_bytes())
        for event in journal["records"][0]["history"]: event.pop("snapshot", None)
        path.write_text(json.dumps(journal), encoding="utf-8")
        self.assertEqual("REVIEW_REQUIRED", self.call("check")["status"])
        self.call("verify", {"id": "type-role", "proof": proof})
        self.assertEqual("PASS", self.call("check")["status"])

    def test_edited_owner_is_reviewable_then_requires_current_owner_proof(self):
        proof = self.prepare()
        self.call("verify", {"id": "type-role", "proof": proof})
        path = self.root / "design-intelligence/example/CORRECTIONS.json"
        journal = json.loads(path.read_bytes())
        journal["records"][0]["scope"]["owners"] = ["src/moved.css"]
        path.write_text(json.dumps(journal), encoding="utf-8")
        self.assertEqual("REVIEW_REQUIRED", self.call("check", self.record["scope"])["status"])
        self.assertTrue(self.call("list")["review_required"])
        with self.assertRaises(ValueError): self.call("verify", {"id": "type-role", "proof": proof})
        (self.root / "src/moved.css").write_bytes((self.root / "src/page.css").read_bytes())
        proof = self.current_proof("src/moved.css")
        self.call("verify", {"id": "type-role", "proof": proof})
        self.assertEqual("PASS", self.call("check")["status"])

    def test_valid_new_scope_does_not_resurrect_every_old_scope_after_drift(self):
        proof = self.prepare()
        self.call("verify", {"id": "type-role", "proof": proof})
        self.call("update", {"id": "type-role", "note": "Explicitly relocate", "scope": {"owners": ["src/page.css"], "routes": ["/new"], "states": ["default"]}})
        self.call("update", {"id": "type-role", "note": "Relocated implementation"})
        self.call("verify", {"id": "type-role", "proof": proof})
        path = self.root / "design-intelligence/example/CORRECTIONS.json"
        journal = json.loads(path.read_bytes())
        journal["records"][0]["requirement"] = "Unconfirmed change"
        path.write_text(json.dumps(journal), encoding="utf-8")
        self.assertEqual("PASS", self.call("check", {"owners": [], "routes": ["/page"], "states": []})["status"])
        self.assertEqual("REVIEW_REQUIRED", self.call("check", {"owners": [], "routes": ["/new"], "states": []})["status"])

    def test_damaged_proof_structure_fails_closed_and_preserves_bytes(self):
        proof = self.prepare()
        self.call("verify", {"id": "type-role", "proof": proof})
        path = self.root / "design-intelligence/example/CORRECTIONS.json"
        journal = json.loads(path.read_bytes())
        journal["records"][0]["proof"]["sources"] = "broken"
        path.write_text(json.dumps(journal), encoding="utf-8")
        before = path.read_bytes()
        with self.assertRaises(ValueError): self.call("check")
        self.assertEqual(before, path.read_bytes())

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
        # An identity without a journal beside a recorded one is reported, not passed.
        self.assertEqual("NO_JOURNAL", self.call("check", project="Other project")["status"])

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


def png_bytes(width=4, height=3):
    import struct
    import zlib
    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))
    pixels = (b"\0" + b"\xff\xff\xff" * width) * height
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(pixels)) + chunk(b"IEND", b""))


def digest_binding(root, name):
    return {"path": name, "sha256": hashlib.sha256((root / name).read_bytes()).hexdigest()}


class HostCaptureTests(unittest.TestCase):
    """A server-rendered app cannot be served by observe.mjs; the host's own browser capture closes the criterion."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.record = {"id": "passive-service-backings", "source": "User correction",
            "requirement": "Show passive service icons without individual backings",
            "scope": {"owners": ["app/services/page.tsx"], "routes": ["/services"], "states": ["default"]},
            "criteria": [{"id": "visual-default", "kind": "visual", "requirement": "Inspect service symbols beside labels and controls"}]}
        (self.root / "app/services").mkdir(parents=True)
        (self.root / "app/services/page.tsx").write_text("export default function Page() { return null }", encoding="utf-8")
        (self.root / "captures").mkdir()
        (self.root / "captures/services-390.png").write_bytes(png_bytes())
        self.call("record", self.record)
        self.call("update", {"id": "passive-service-backings", "status": "implemented", "note": "Removed backings in the owner"})

    def call(self, command, data=None, project="Harbor"):
        return execute(command, workspace=self.root, project=project, payload=data)

    def proof(self, method="self-review"):
        return {"sources": [digest_binding(self.root, "app/services/page.tsx")],
            "artifacts": [digest_binding(self.root, "captures/services-390.png")],
            "results": [{"criterion": "visual-default", "status": "PASS", "artifacts": ["captures/services-390.png"],
                "review": {"reviewer": "Implementing agent", "finding": "Symbols sit beside labels without backings",
                    "viewport": "390x844@3", "state": "default", "method": method, "verdict": "KEEP",
                    "capture": {"origin": "host", "tool": "Playwright 1.49 (Chromium)", "url": "http://localhost:3000/services",
                        "date": "2026-11-14", "image": "captures/services-390.png"}}}]}

    def verify(self, proof):
        return self.call("verify", {"id": "passive-service-backings", "proof": proof})

    def refused(self, proof, message=None):
        if message:
            with self.assertRaisesRegex(ValueError, message): self.verify(proof)
        else:
            with self.assertRaises(ValueError): self.verify(proof)
        self.assertEqual("BLOCKED", self.call("check")["status"])

    def test_self_reviewed_host_capture_closes_visual_criterion_and_is_labeled(self):
        self.verify(self.proof())
        result = self.call("check")
        self.assertEqual("PASS", result["status"])
        self.assertEqual("Recorded proof integrity; not independent visual certification", result["boundary"])
        self.assertEqual([{"id": "passive-service-backings", "criterion": "visual-default", "method": "self-review",
            "evidence": "host-capture", "state": "default", "viewport": "390x844@3", "tool": "Playwright 1.49 (Chromium)",
            "url": "http://localhost:3000/services", "date": "2026-11-14", "image": "captures/services-390.png"}], result["visual_closures"])

    def test_peer_and_user_review_keep_their_method_label(self):
        for method in ("peer-review", "user-review"):
            with self.subTest(method=method):
                self.verify(self.proof(method))
                self.assertEqual(method, self.call("check")["visual_closures"][0]["method"])

    def test_route_and_datetime_provenance_are_accepted(self):
        proof = self.proof()
        proof["results"][0]["review"]["capture"].update(url="/services", date="2026-11-14T09:30:00+00:00")
        self.verify(proof)
        self.assertEqual("PASS", self.call("check")["status"])

    def test_jpeg_and_webp_host_screenshots_are_accepted(self):
        for name, header in (("shot.jpg", b"\xff\xd8\xff\xe0\x00\x10JFIF\x00"), ("shot.webp", b"RIFF\x24\x00\x00\x00WEBPVP8 ")):
            with self.subTest(name=name):
                (self.root / "captures" / name).write_bytes(header + b"\x00" * 32)
                proof = self.proof()
                proof["artifacts"] = [digest_binding(self.root, f"captures/{name}")]
                proof["results"][0]["artifacts"] = [f"captures/{name}"]
                proof["results"][0]["review"]["capture"]["image"] = f"captures/{name}"
                self.verify(proof)
                self.assertEqual("PASS", self.call("check")["status"])

    def test_missing_hash_or_unbound_image_is_refused(self):
        proof = self.proof()
        del proof["artifacts"][0]["sha256"]
        self.refused(proof)
        (self.root / "notes.txt").write_text("not the capture", encoding="utf-8")
        proof = self.proof()
        proof["artifacts"] = [digest_binding(self.root, "notes.txt")]
        proof["results"][0]["artifacts"] = ["notes.txt"]
        self.refused(proof, "bound proof artifact")

    def test_hash_mismatch_is_refused(self):
        proof = self.proof()
        proof["artifacts"][0]["sha256"] = hashlib.sha256(b"another screenshot").hexdigest()
        self.refused(proof, "Changed: captures/services-390.png")

    def test_non_keep_or_unlabeled_review_is_refused(self):
        for verdict in ("REVISE", "REJECT", "UNKNOWN"):
            proof = self.proof()
            proof["results"][0]["review"]["verdict"] = verdict
            with self.subTest(verdict=verdict): self.refused(proof)
        for field in ("method", "verdict"):
            proof = self.proof()
            del proof["results"][0]["review"][field]
            with self.subTest(missing=field): self.refused(proof)
        proof = self.proof()
        proof["results"][0]["review"]["method"] = "agent-review"
        self.refused(proof, "review method")

    def test_missing_or_invalid_provenance_is_refused(self):
        for field in ("origin", "tool", "url", "date", "image"):
            proof = self.proof()
            del proof["results"][0]["review"]["capture"][field]
            with self.subTest(missing=field): self.refused(proof, "missing")
        for field, value in (("origin", "observer"), ("tool", " "), ("url", "the services page"), ("date", "yesterday"),
                             ("image", "../outside.png")):
            proof = self.proof()
            proof["results"][0]["review"]["capture"][field] = value
            with self.subTest(field=field, value=value): self.refused(proof)
        for field, value in (("viewport", "390x844"), ("state", "hover")):
            proof = self.proof()
            proof["results"][0]["review"][field] = value
            with self.subTest(field=field, value=value): self.refused(proof)
        proof = self.proof()
        proof["results"][0]["review"]["capture"]["note"] = "unplanned field"
        self.refused(proof, "unexpected")

    def test_capture_must_be_its_results_own_real_image(self):
        proof = self.proof()
        (self.root / "notes.txt").write_text("not an image", encoding="utf-8")
        proof["artifacts"].append(digest_binding(self.root, "notes.txt"))
        proof["results"][0]["artifacts"] = ["notes.txt"]
        self.refused(proof, "result")
        proof["results"][0]["artifacts"] = ["notes.txt", "captures/services-390.png"]
        proof["results"][0]["review"]["capture"]["image"] = "notes.txt"
        self.refused(proof, "PNG, JPEG or WebP")
        proof = self.proof()
        proof["results"][0]["review"]["capture"]["image"] = "app/services/page.tsx"
        self.refused(proof, "bound proof artifact")

    def test_report_and_host_capture_are_alternatives(self):
        proof = self.proof()
        proof["results"][0]["review"]["report"] = "captures/services-390.png"
        self.refused(proof, "either")

    def test_changed_capture_source_or_provenance_requires_review(self):
        self.verify(self.proof())
        image = self.root / "captures/services-390.png"
        original = image.read_bytes()
        image.write_bytes(png_bytes(5, 3))
        self.assertEqual("REVIEW_REQUIRED", self.call("check")["status"])
        image.write_bytes(original)
        self.assertEqual("PASS", self.call("check")["status"])
        source = self.root / "app/services/page.tsx"
        source.write_bytes(source.read_bytes() + b"\n")
        result = self.call("check")
        self.assertEqual("REVIEW_REQUIRED", result["status"])
        self.assertEqual([], result["visual_closures"])
        source.write_bytes(source.read_bytes()[:-1])
        path = self.root / "design-intelligence/harbor/CORRECTIONS.json"
        journal = json.loads(path.read_bytes())
        journal["records"][0]["proof"]["results"][0]["review"]["capture"]["tool"] = "Another tool"
        path.write_text(json.dumps(journal), encoding="utf-8")
        edited = path.read_bytes()
        self.assertEqual("REVIEW_REQUIRED", self.call("check")["status"])
        self.assertEqual(edited, path.read_bytes())

    def test_cli_closes_with_host_capture_and_reports_self_review(self):
        script = ROOT / "skill/snowe-ui-skill/scripts/corrections.py"
        proof_path = self.root / "proof.json"
        proof_path.write_text(json.dumps({"id": "passive-service-backings", "proof": self.proof()}), encoding="utf-8")
        verified = subprocess.run([sys.executable, "-I", str(script), "verify", "--workspace", str(self.root), "--project", "Harbor",
            "--input", str(proof_path)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        self.assertEqual(0, verified.returncode, verified.stderr)
        checked = subprocess.run([sys.executable, "-I", str(script), "check", "--workspace", str(self.root), "--project", "Harbor"],
            capture_output=True, text=True, encoding="utf-8", timeout=60)
        self.assertEqual(0, checked.returncode, checked.stderr)
        self.assertEqual("self-review", json.loads(checked.stdout)["visual_closures"][0]["method"])


class UnavailableEvidenceTests(unittest.TestCase):
    """Recording why evidence cannot be produced ends the loop honestly; it never becomes PASS."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.record = {"id": "passive-service-backings", "source": "User correction",
            "requirement": "Show passive service icons without individual backings",
            "scope": {"owners": ["app/services/page.tsx"], "routes": ["/services"], "states": ["default"]},
            "criteria": [{"id": "build", "kind": "technical", "requirement": "The page compiles"},
                         {"id": "visual-default", "kind": "visual", "requirement": "Inspect service symbols beside labels and controls"}]}
        self.reason = "No browser is available in this environment and the app server cannot start without its database"
        self.call("record", self.record)

    def call(self, command, data=None, project="Harbor"):
        return execute(command, workspace=self.root, project=project, payload=data)

    def implement(self):
        self.call("update", {"id": "passive-service-backings", "status": "implemented", "note": "Removed backings in the owner"})

    def unavailable(self, criterion="visual-default", reason=None):
        return self.call("unavailable", {"id": "passive-service-backings", "criterion": criterion, "reason": reason or self.reason})

    def test_recorded_reason_is_reported_as_blocked_never_pass(self):
        self.implement()
        self.unavailable()
        result = self.call("check")
        self.assertEqual("BLOCKED", result["status"])
        self.assertEqual(["passive-service-backings"], result["blocked"])
        self.assertEqual([{"id": "passive-service-backings", "criterion": "visual-default", "kind": "visual", "reason": self.reason}],
                         result["evidence_unavailable"])
        self.unavailable("build", "The type checker needs network access to install dependencies")
        self.assertEqual("BLOCKED", self.call("check")["status"])
        self.assertEqual(2, len(self.call("check")["evidence_unavailable"]))
        history = self.call("list")["records"][0]["history"]
        self.assertIn(self.reason, history[-2]["note"])

    def test_statement_requires_implemented_record_known_criterion_and_reason(self):
        with self.assertRaisesRegex(ValueError, "implemented"): self.unavailable()
        self.implement()
        with self.assertRaisesRegex(ValueError, "criterion"): self.unavailable("missing")
        for reason in (" ", "x" * 2001):
            with self.subTest(length=len(reason)), self.assertRaises(ValueError): self.unavailable(reason=reason)
        with self.assertRaisesRegex(ValueError, "unexpected"):
            self.call("unavailable", {"id": "passive-service-backings", "criterion": "build", "reason": self.reason, "status": "verified"})
        self.assertEqual([], self.call("check")["evidence_unavailable"])

    def test_repeated_statement_is_idempotent_and_a_new_reason_replaces_it(self):
        self.implement()
        self.assertTrue(self.unavailable()["changed"])
        self.assertFalse(self.unavailable()["changed"])
        self.unavailable(reason="The preview tool crashed while opening the route")
        reasons = [item["reason"] for item in self.call("check")["evidence_unavailable"]]
        self.assertEqual(["The preview tool crashed while opening the route"], reasons)

    def test_later_verification_or_implementation_clears_the_statement(self):
        self.implement()
        self.unavailable()
        self.implement()
        self.assertEqual([], self.call("check")["evidence_unavailable"])
        self.assertNotIn("unavailable", self.call("list")["records"][0])
        self.unavailable()
        (self.root / "app/services").mkdir(parents=True)
        (self.root / "app/services/page.tsx").write_text("export default function Page() { return null }", encoding="utf-8")
        (self.root / "shot.png").write_bytes(png_bytes())
        (self.root / "build.log").write_text("compiled", encoding="utf-8")
        proof = {"sources": [digest_binding(self.root, "app/services/page.tsx")],
            "artifacts": [digest_binding(self.root, "shot.png"), digest_binding(self.root, "build.log")],
            "results": [{"criterion": "build", "status": "PASS", "artifacts": ["build.log"]},
                {"criterion": "visual-default", "status": "PASS", "artifacts": ["shot.png"],
                 "review": {"reviewer": "Implementing agent", "finding": "No backings remain", "viewport": "390x844@3", "state": "default",
                    "method": "self-review", "verdict": "KEEP", "capture": {"origin": "host", "tool": "Host preview",
                    "url": "/services", "date": "2026-11-14", "image": "shot.png"}}}]}
        self.call("verify", {"id": "passive-service-backings", "proof": proof})
        result = self.call("check")
        self.assertEqual("PASS", result["status"])
        self.assertEqual([], result["evidence_unavailable"])
        self.assertNotIn("unavailable", self.call("list")["records"][0])

    def test_superseding_a_record_with_unavailable_evidence_keeps_the_journal_readable(self):
        self.implement()
        self.unavailable()
        replacement = deepcopy(self.record); replacement["id"] = "replacement"
        self.call("record", replacement)
        self.call("supersede", {"id": "passive-service-backings", "replacement": "replacement", "note": "New user direction"})
        result = self.call("check")
        self.assertEqual(["replacement"], result["blocked"])
        self.assertEqual([], result["evidence_unavailable"])
        record = next(item for item in self.call("list")["records"] if item["id"] == "passive-service-backings")
        self.assertNotIn("unavailable", record)
        self.assertIn("unavailable", record["history"][-2]["snapshot"])

    def test_direct_edit_of_a_reason_is_integrity_drift(self):
        self.implement()
        self.unavailable()
        path = self.root / "design-intelligence/harbor/CORRECTIONS.json"
        journal = json.loads(path.read_bytes())
        journal["records"][0]["unavailable"][0]["reason"] = "Edited afterwards"
        path.write_text(json.dumps(journal), encoding="utf-8")
        result = self.call("check")
        self.assertEqual("BLOCKED", result["status"])
        self.assertEqual("passive-service-backings", result["stale"][0]["id"])

    def test_malformed_statement_fails_closed(self):
        self.implement()
        self.unavailable()
        path = self.root / "design-intelligence/harbor/CORRECTIONS.json"
        original = path.read_bytes()
        for mutate in (lambda e: e.__setitem__("unavailable", []),
                       lambda e: e["unavailable"][0].__setitem__("criterion", "unknown"),
                       lambda e: e["unavailable"].append(dict(e["unavailable"][0])),
                       lambda e: e.update(status="requested", history=e["history"] + [{**e["history"][-1], "status": "requested", "snapshot": {**e["history"][-1]["snapshot"], "status": "requested"}}])):
            journal = json.loads(original)
            mutate(journal["records"][0])
            path.write_text(json.dumps(journal), encoding="utf-8")
            before = path.read_bytes()
            with self.subTest(journal=journal["records"][0].get("unavailable")), self.assertRaises(ValueError): self.call("check")
            self.assertEqual(before, path.read_bytes())

    def test_cli_exit_status_stays_blocked(self):
        self.implement()
        script = ROOT / "skill/snowe-ui-skill/scripts/corrections.py"
        statement = self.root / "unavailable.json"
        statement.write_text(json.dumps({"id": "passive-service-backings", "criterion": "visual-default", "reason": self.reason}), encoding="utf-8")
        recorded = subprocess.run([sys.executable, "-I", str(script), "unavailable", "--workspace", str(self.root), "--project", "Harbor",
            "--input", str(statement)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        self.assertEqual(0, recorded.returncode, recorded.stderr)
        checked = subprocess.run([sys.executable, "-I", str(script), "check", "--workspace", str(self.root), "--project", "Harbor"],
            capture_output=True, text=True, encoding="utf-8", timeout=60)
        self.assertEqual(2, checked.returncode, checked.stderr)
        self.assertEqual(self.reason, json.loads(checked.stdout)["evidence_unavailable"][0]["reason"])


class JournalCompatibilityTests(unittest.TestCase):
    """Journals and observer-based receipts written before host capture keep their exact meaning."""

    PREVIOUS_RELEASE = "92da6fb"

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "workspace"
        self.root.mkdir()

    def previous_scripts(self):
        """Extract the pre-host-capture product scripts; skip without that git history."""
        import io
        import tarfile
        try:
            raw = subprocess.check_output(["git", "archive", "--format=tar", self.PREVIOUS_RELEASE, "skill/snowe-ui-skill/scripts"],
                                          cwd=ROOT, stderr=subprocess.DEVNULL)
        except (subprocess.CalledProcessError, OSError):
            raise unittest.SkipTest(f"git history with {self.PREVIOUS_RELEASE} is unavailable")
        target = Path(self.temp.name) / "previous"
        with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
            for member in archive.getmembers():
                if not member.isfile(): continue
                destination = target / member.name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(archive.extractfile(member).read())
        return target / "skill/snowe-ui-skill/scripts/corrections.py"

    def run_previous(self, script, command, payload=None):
        arguments = [sys.executable, "-I", str(script), command, "--workspace", str(self.root), "--project", "Harbor"]
        if payload is not None:
            path = Path(self.temp.name) / f"{command}-input.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            arguments += ["--input", str(path)]
        return subprocess.run(arguments, capture_output=True, text=True, encoding="utf-8", timeout=60)

    def test_journal_written_by_previous_release_checks_identically(self):
        script = self.previous_scripts()
        (self.root / "src").mkdir()
        (self.root / "src/page.css").write_text("body{font-weight:400}", encoding="utf-8")
        (self.root / "build.log").write_text("compiled", encoding="utf-8")
        base = {"source": "User request", "requirement": "Keep body role coherent",
                "scope": {"owners": ["src/page.css"], "routes": ["/page"], "states": []},
                "criteria": [{"id": "build", "kind": "technical", "requirement": "Compiles"}]}
        for identifier in ("closed", "open", "old"):
            self.assertEqual(0, self.run_previous(script, "record", {**base, "id": identifier}).returncode)
        self.assertEqual(0, self.run_previous(script, "update", {"id": "closed", "status": "implemented", "note": "Done"}).returncode)
        proof = {"sources": [digest_binding(self.root, "src/page.css")], "artifacts": [digest_binding(self.root, "build.log")],
                 "results": [{"criterion": "build", "status": "PASS", "artifacts": ["build.log"]}]}
        self.assertEqual(0, self.run_previous(script, "verify", {"id": "closed", "proof": proof}).returncode)
        self.assertEqual(0, self.run_previous(script, "supersede", {"id": "old", "replacement": "open", "note": "New direction"}).returncode)
        path = self.root / "design-intelligence/harbor/CORRECTIONS.json"
        before = path.read_bytes()
        previous = json.loads(self.run_previous(script, "check").stdout)
        current = execute("check", workspace=self.root, project="Harbor")
        for key in ("status", "project_identity", "journal", "applicable", "blocked", "stale", "boundary"):
            self.assertEqual(previous[key], current[key], key)
        self.assertEqual("BLOCKED", current["status"])
        self.assertEqual([], current["evidence_unavailable"])
        self.assertEqual(before, path.read_bytes())
        self.assertEqual(json.loads(self.run_previous(script, "list").stdout)["records"],
                         execute("list", workspace=self.root, project="Harbor")["records"])

    def test_observer_report_closure_keeps_its_record_shape_and_label(self):
        from tests.evidence_factory import make_review, binding
        record = {"id": "type-role", "source": "User request", "requirement": "Keep body role coherent",
            "scope": {"owners": ["src/page.css"], "routes": ["/page"], "states": ["default"]},
            "criteria": [{"id": "render", "kind": "visual", "requirement": "Review page typography"}]}
        execute("record", workspace=self.root, project="Example", payload=record)
        execute("update", workspace=self.root, project="Example", payload={"id": "type-role", "status": "implemented", "note": "Corrected owner"})
        (self.root / "src").mkdir()
        (self.root / "src/page.css").write_text("body{font-weight:400}")
        report = make_review(self.root, owner="src/page.css", state="default", viewport="390x844@1", image="review.png")
        proof = {"sources": report["sources"], "artifacts": [binding(self.root, "review.png"), binding(self.root, "review.json")],
            "results": [{"criterion": "render", "status": "PASS", "artifacts": ["review.png", "review.json"],
                "review": {"reviewer": "Authored test", "finding": "Contract fixture only", "viewport": "390x844@1", "state": "default",
                           "method": "self-review", "verdict": "KEEP", "report": "review.json"}}]}
        written = execute("verify", workspace=self.root, project="Example", payload={"id": "type-role", "proof": proof})["record"]
        self.assertEqual({"id", "source", "requirement", "scope", "criteria", "status", "history", "proof"}, set(written))
        self.assertEqual(proof, written["proof"])
        result = execute("check", workspace=self.root, project="Example")
        self.assertEqual("PASS", result["status"])
        self.assertEqual([{"id": "type-role", "criterion": "render", "method": "self-review", "evidence": "checked-report",
                           "state": "default", "viewport": "390x844@1", "report": "review.json"}], result["visual_closures"])


class CheckedEvidenceMessageTests(unittest.TestCase):
    """Input diagnostics name the file, the encoding problem, the object and its fields."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.script = ROOT / "skill/snowe-ui-skill/scripts/corrections.py"
        self.record = {"id": "type-role", "source": "User request", "requirement": "Keep body role coherent",
            "scope": {"owners": ["src/page.css"], "routes": ["/page"], "states": ["default"]},
            "criteria": [{"id": "render", "kind": "visual", "requirement": "Review page typography"}]}

    def record_cli(self, input_path):
        return subprocess.run([sys.executable, str(self.script), "record", "--workspace", str(self.root),
            "--project", "Example", "--input", str(input_path)], capture_output=True, text=True, encoding="utf-8", timeout=60)

    def test_missing_directory_and_oversized_inputs_name_their_path(self):
        from checked_evidence import read_json
        missing = self.root / "absent.json"
        with self.assertRaisesRegex(ValueError, "does not exist") as raised: read_json(missing)
        self.assertIn(str(missing), str(raised.exception))
        with self.assertRaisesRegex(ValueError, "regular file") as raised: read_json(self.root)
        self.assertIn(str(self.root), str(raised.exception))
        large = self.root / "large.json"
        large.write_text(json.dumps("x" * 2000), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "exceeds 1000 bytes") as raised: read_json(large, max_bytes=1000)
        self.assertIn(str(large), str(raised.exception))

    def test_utf8_bom_is_accepted_and_utf16_is_named_as_an_encoding_problem(self):
        bom = self.root / "bom.json"
        bom.write_bytes(b"\xef\xbb\xbf" + json.dumps(self.record).encode("utf-8"))
        accepted = self.record_cli(bom)
        self.assertEqual(0, accepted.returncode, accepted.stderr)
        self.assertTrue(json.loads(accepted.stdout)["changed"])
        # Windows PowerShell 5.1 redirection and Out-File write UTF-16LE with a BOM.
        for name, payload in (("utf16-bom.json", json.dumps(self.record).encode("utf-16")),
                              ("utf16-plain.json", json.dumps(self.record).encode("utf-16-le"))):
            with self.subTest(name=name):
                path = self.root / name
                path.write_bytes(payload)
                rejected = self.record_cli(path)
                self.assertEqual(1, rejected.returncode)
                error = json.loads(rejected.stderr)["error"]
                self.assertIn("UTF-8", error)
                self.assertIn("UTF-16", error)
                # The CLI reports the expanded path; Windows runners give tests an 8.3 short one.
                self.assertTrue(str(path) in error or str(path.resolve()) in error, error)
        latin = self.root / "latin.json"
        latin.write_bytes(json.dumps({"note": "café"}, ensure_ascii=False).encode("latin-1"))
        from checked_evidence import read_json
        with self.assertRaisesRegex(ValueError, "must be UTF-8") as raised: read_json(latin)
        self.assertIn(str(latin), str(raised.exception))

    def test_invalid_json_names_path_and_position(self):
        from checked_evidence import read_json
        broken = self.root / "broken.json"
        broken.write_text('{"id": "x",}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, r"Invalid JSON in .*broken\.json.*line 1"): read_json(broken)
        nonfinite = self.root / "nonfinite.json"
        nonfinite.write_text('{"ratio": NaN}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, r"nonfinite\.json.*NaN"): read_json(nonfinite)

    def test_object_field_errors_name_the_object_and_the_missing_and_extra_keys(self):
        from checked_evidence import object_fields
        with self.assertRaises(ValueError) as raised:
            object_fields({"id": "hero", "actoin": "click"}, {"id", "action"}, {"key"}, name="Replay step")
        message = str(raised.exception)
        for expected in ("Replay step 'hero'", "is missing ['action']", "has unexpected ['actoin']", "optional ['key']"):
            self.assertIn(expected, message)
        with self.assertRaisesRegex(ValueError, "Scope must be a JSON object, not list"):
            object_fields([], {"owners"}, name="scope")
        record = deepcopy(self.record); record["scope"] = {"owners": ["a.css"], "routes": []}
        with self.assertRaisesRegex(ValueError, r"Scope is missing \['states'\]"):
            execute("record", workspace=self.root, project="Example", payload=record)


if __name__ == "__main__": unittest.main()
