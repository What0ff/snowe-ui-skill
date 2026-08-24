from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = ROOT / "skill" / "snowe-ui-skill" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

from core import search, search_stack  # noqa: E402
from decision_packet import (  # noqa: E402
    DecisionPacketGenerator,
    generate_decision_packet,
    persist_decision_packet,
)
import decision_packet as decision_packet_module  # noqa: E402


INSTALLER_PATH = ROOT / "scripts" / "install_skill.py"
INSTALLER_SPEC = importlib.util.spec_from_file_location("snowe_runtime_installer", INSTALLER_PATH)
if INSTALLER_SPEC is None or INSTALLER_SPEC.loader is None:  # pragma: no cover
    raise RuntimeError(f"Cannot load installer: {INSTALLER_PATH}")
INSTALLER = importlib.util.module_from_spec(INSTALLER_SPEC)
INSTALLER_SPEC.loader.exec_module(INSTALLER)


def create_directory_redirect(link: Path, target: Path) -> bool:
    """Create a directory symlink or Windows junction; return whether it is a junction."""
    try:
        link.symlink_to(target, target_is_directory=True)
        return False
    except (OSError, NotImplementedError):
        if os.name != "nt":
            raise
        created = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True,
            text=True,
            check=False,
        )
        if created.returncode != 0:
            raise unittest.SkipTest(f"directory redirect unavailable: {created.stderr or created.stdout}")
        return True


def remove_directory_redirect(path: Path, is_junction: bool) -> None:
    if is_junction:
        os.rmdir(path)
    else:
        path.unlink()


def windows_short_path(path: Path) -> Path:
    """Return a real Windows short-name alias or the unchanged path."""
    import ctypes
    from ctypes import wintypes

    get_short_path_name = ctypes.WinDLL("kernel32", use_last_error=True).GetShortPathNameW
    get_short_path_name.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
    get_short_path_name.restype = wintypes.DWORD
    requested = os.fspath(path)
    size = int(get_short_path_name(requested, None, 0))
    if size == 0:
        raise OSError(ctypes.get_last_error(), f"Cannot obtain a short path for {path}")
    buffer = ctypes.create_unicode_buffer(size)
    written = int(get_short_path_name(requested, buffer, size))
    if written == 0 or written >= size:
        raise OSError(ctypes.get_last_error(), f"Cannot obtain a stable short path for {path}")
    return Path(buffer.value)


class PersistenceIdentityTests(unittest.TestCase):
    def test_persistence_requires_identity_before_creating_output(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            packet = DecisionPacketGenerator().generate("A brief without a project")

            with self.assertRaisesRegex(ValueError, "explicit project identity"):
                persist_decision_packet(packet, output_dir=root)

            self.assertFalse((root / "design-intelligence").exists())

            with self.assertRaisesRegex(ValueError, "explicit project identity"):
                generate_decision_packet("Another brief", persist=True, output_dir=root)
            self.assertFalse((root / "design-intelligence").exists())

    def test_slug_collision_is_rejected_without_replacing_brief_or_ledger(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first = persist_decision_packet(
                DecisionPacketGenerator().generate("Original brief", "North Star"),
                output_dir=root,
            )
            project = Path(first["design_intelligence_dir"])
            brief_before = (project / "BRIEF.md").read_bytes()
            decisions_before = (project / "DECISIONS.md").read_bytes()

            # Punctuation changes the slug but not the requested output path.
            with self.assertRaisesRegex(ValueError, "Project identity collision"):
                persist_decision_packet(
                    DecisionPacketGenerator().generate("Unrelated brief", "North-Star"),
                    output_dir=root,
                )

            self.assertEqual(brief_before, (project / "BRIEF.md").read_bytes())
            self.assertEqual(decisions_before, (project / "DECISIONS.md").read_bytes())
            manifest = json.loads((project / "PROJECT.json").read_text(encoding="utf-8"))
            self.assertEqual({"North Star", "north-star"}, {manifest["project_name"], manifest["project_slug"]})

    def test_same_project_regeneration_preserves_decisions_byte_for_byte(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first = persist_decision_packet(
                DecisionPacketGenerator().generate("Original brief", "North Star"),
                output_dir=root,
            )
            decisions = Path(first["design_intelligence_dir"]) / "DECISIONS.md"
            accepted = b"accepted evidence\r\nwith exact bytes\x00\n"
            decisions.write_bytes(accepted)

            persist_decision_packet(
                DecisionPacketGenerator().generate("Updated brief", "North Star"),
                output_dir=root,
            )
            self.assertEqual(accepted, decisions.read_bytes())

    def test_legacy_explicit_ledger_is_migrated_without_rewriting_it(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = root / "design-intelligence" / "north-star"
            project.mkdir(parents=True)
            accepted = b"# Accepted Design Decisions\n\nProject: North Star\n\naccepted\n"
            (project / "DECISIONS.md").write_bytes(accepted)

            result = persist_decision_packet(
                DecisionPacketGenerator().generate("New inquiry", "North Star"),
                output_dir=root,
            )

            self.assertEqual(accepted, (project / "DECISIONS.md").read_bytes())
            self.assertTrue(
                any(
                    os.path.samefile(project / "PROJECT.json", reported)
                    for reported in result["created_or_updated_files"]
                )
            )

    def test_page_slug_collision_is_rejected_without_replacing_first_page(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            packet = DecisionPacketGenerator().generate("Brief", "North Star")
            first = persist_decision_packet(packet, page="Account Settings", output_dir=root)
            page = Path(first["design_intelligence_dir"]) / "pages" / "account-settings.md"
            before = page.read_bytes()

            with self.assertRaisesRegex(ValueError, "Page identity collision"):
                persist_decision_packet(packet, page="Account-Settings", output_dir=root)

            self.assertEqual(before, page.read_bytes())

    def test_page_slug_collision_does_not_replace_brief_or_ledger(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first = persist_decision_packet(
                DecisionPacketGenerator().generate("Original brief", "North Star"),
                page="Account Settings",
                output_dir=root,
            )
            project = Path(first["design_intelligence_dir"])
            page_path = project / "pages" / "account-settings.md"
            before_brief = (project / "BRIEF.md").read_bytes()
            before_decisions = (project / "DECISIONS.md").read_bytes()
            before_page = page_path.read_bytes()

            with self.assertRaisesRegex(ValueError, "Page identity collision"):
                persist_decision_packet(
                    DecisionPacketGenerator().generate("Changed brief", "North Star"),
                    page="Account-Settings",
                    output_dir=root,
                )

            self.assertEqual(before_brief, (project / "BRIEF.md").read_bytes())
            self.assertEqual(before_decisions, (project / "DECISIONS.md").read_bytes())
            self.assertEqual(before_page, page_path.read_bytes())

    def test_slug_style_page_identity_is_idempotent_but_not_shared(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            packet = DecisionPacketGenerator().generate("Brief", "North Star")
            first = persist_decision_packet(packet, page="account-settings", output_dir=root)
            page = Path(first["design_intelligence_dir"]) / "pages" / "account-settings.md"
            first_bytes = page.read_bytes()

            persist_decision_packet(packet, page="account-settings", output_dir=root)
            self.assertEqual(first_bytes, page.read_bytes())
            self.assertIn('**Page identity:** "account-settings"', page.read_text(encoding="utf-8"))

            with self.assertRaisesRegex(ValueError, "Page identity collision"):
                persist_decision_packet(packet, page="Account Settings", output_dir=root)

    def test_nonprintable_project_and_page_identities_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            with self.assertRaisesRegex(ValueError, "printable characters"):
                persist_decision_packet(
                    DecisionPacketGenerator().generate("Brief", "North\nStar"),
                    output_dir=root,
                )
            self.assertFalse((root / "design-intelligence").exists())

            packet = DecisionPacketGenerator().generate("Brief", "North Star")
            with self.assertRaisesRegex(ValueError, "printable characters"):
                persist_decision_packet(packet, page="Account\nSettings", output_dir=root)

    def test_windows_reserved_identities_are_rejected_before_output_creation(self):
        for identity in ("NUL", "CON", "PRN", "AUX", "COM1", "LPT1"):
            with self.subTest(identity=identity), tempfile.TemporaryDirectory() as temporary_directory:
                root = Path(temporary_directory)
                with self.assertRaisesRegex(ValueError, "Windows-reserved"):
                    persist_decision_packet(
                        DecisionPacketGenerator().generate("Brief", identity),
                        output_dir=root,
                        project_identity=identity,
                    )
                self.assertFalse((root / "design-intelligence").exists())

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            packet = DecisionPacketGenerator().generate("Brief", "North Star")
            with self.assertRaisesRegex(ValueError, "Windows-reserved"):
                persist_decision_packet(packet, page="NUL", output_dir=root)
            self.assertFalse((root / "design-intelligence").exists())

    def test_competing_page_slug_claim_is_rejected_without_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            packet = DecisionPacketGenerator().generate("Brief", "North Star")
            first = persist_decision_packet(packet, output_dir=root)
            project = Path(first["design_intelligence_dir"])
            page = project / "pages" / "account-settings.md"
            real_create = decision_packet_module._atomic_create_text

            def competing_claim(path: Path, content: str) -> bool:
                if path == page and not path.exists():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    self.assertTrue(
                        real_create(path, decision_packet_module.format_page_inquiry("Account-Settings"))
                    )
                    return False
                return real_create(path, content)

            with patch.object(decision_packet_module, "_atomic_create_text", side_effect=competing_claim):
                with self.assertRaisesRegex(ValueError, "Page identity collision"):
                    persist_decision_packet(packet, page="Account Settings", output_dir=root)

            self.assertIn(
                '**Page identity:** "Account-Settings"',
                page.read_text(encoding="utf-8"),
            )

    def test_atomic_brief_replacement_does_not_modify_external_hardlink_target(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            packet = DecisionPacketGenerator().generate("Original", "North Star")
            first = persist_decision_packet(packet, output_dir=root)
            brief = Path(first["design_intelligence_dir"]) / "BRIEF.md"
            outside = root / "outside.txt"
            outside.write_bytes(b"external sentinel")
            brief.unlink()
            try:
                os.link(outside, brief)
            except OSError as error:
                self.skipTest(f"hardlinks are unavailable: {error}")

            persist_decision_packet(
                DecisionPacketGenerator().generate("Updated", "North Star"),
                output_dir=root,
            )

            self.assertEqual(b"external sentinel", outside.read_bytes())
            self.assertFalse(os.path.samefile(outside, brief))
            self.assertIn("Updated", brief.read_text(encoding="utf-8"))

    def test_shared_project_manifest_is_rejected_without_mutating_external_inode(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first = persist_decision_packet(
                DecisionPacketGenerator().generate("Original", "North Star"),
                output_dir=root,
            )
            project = Path(first["design_intelligence_dir"])
            manifest = project / "PROJECT.json"
            outside = root / "manifest-owner.json"
            outside.write_bytes(manifest.read_bytes())
            manifest.unlink()
            try:
                os.link(outside, manifest)
            except OSError as error:
                self.skipTest(f"hardlinks are unavailable: {error}")

            with self.assertRaisesRegex(ValueError, "shared hardlink/inode"):
                persist_decision_packet(
                    DecisionPacketGenerator().generate("Updated", "North Star"),
                    output_dir=root,
                )

            self.assertEqual(outside.read_bytes(), manifest.read_bytes())
            self.assertTrue(os.path.samefile(outside, manifest))

    def test_shared_decisions_ledger_is_rejected_without_mutating_external_inode(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first = persist_decision_packet(
                DecisionPacketGenerator().generate("Original", "North Star"),
                output_dir=root,
            )
            project = Path(first["design_intelligence_dir"])
            ledger = project / "DECISIONS.md"
            outside = root / "ledger-owner.md"
            outside.write_bytes(ledger.read_bytes())
            ledger.unlink()
            try:
                os.link(outside, ledger)
            except OSError as error:
                self.skipTest(f"hardlinks are unavailable: {error}")
            brief_before = (project / "BRIEF.md").read_bytes()

            with self.assertRaisesRegex(ValueError, "shared hardlink/inode"):
                persist_decision_packet(
                    DecisionPacketGenerator().generate("Updated", "North Star"),
                    output_dir=root,
                )

            self.assertEqual(outside.read_bytes(), ledger.read_bytes())
            self.assertTrue(os.path.samefile(outside, ledger))
            self.assertEqual(brief_before, (project / "BRIEF.md").read_bytes())

    def test_persistence_lock_rejects_shared_hardlink_without_mutating_it(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            storage = root / "design-intelligence"
            storage.mkdir()
            outside = root / "foreign-lock"
            outside.write_bytes(b"foreign lock bytes")
            lock = storage / ".north-star.persist.lock"
            try:
                os.link(outside, lock)
            except OSError as error:
                self.skipTest(f"hardlinks are unavailable: {error}")

            with self.assertRaisesRegex(ValueError, "shared hardlink"):
                with decision_packet_module._persistence_lock(root, "north-star"):
                    pass

            self.assertEqual(b"foreign lock bytes", outside.read_bytes())
            self.assertTrue(os.path.samefile(outside, lock))

    def test_torn_manifest_is_quarantined_and_recovered_from_explicit_ledger(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            packet = DecisionPacketGenerator().generate("Original", "North Star")
            first = persist_decision_packet(packet, output_dir=root)
            project = Path(first["design_intelligence_dir"])
            ledger_before = (project / "DECISIONS.md").read_bytes()
            (project / "PROJECT.json").write_text('{"schema_version":', encoding="utf-8")

            result = persist_decision_packet(
                DecisionPacketGenerator().generate("Recovered", "North Star"),
                output_dir=root,
            )

            self.assertEqual(ledger_before, (project / "DECISIONS.md").read_bytes())
            self.assertEqual(
                "North Star",
                json.loads((project / "PROJECT.json").read_text(encoding="utf-8"))["project_name"],
            )
            quarantined = list(project.glob("PROJECT.json.corrupt-*"))
            self.assertEqual(1, len(quarantined))
            self.assertIn(str(quarantined[0]), result["preserved_files"])

    def test_bounded_project_manifest_recovery_handles_deep_oversized_and_surrogate_data(self):
        manifests = {
            "deep": (
                '{"schema_version":"1","project_name":"North Star",'
                '"project_slug":"north-star","nested":'
                + ("[" * 1000)
                + "0"
                + ("]" * 1000)
                + "}"
            ),
            "oversized": json.dumps(
                {
                    "schema_version": "1",
                    "project_name": "North Star",
                    "project_slug": "north-star",
                    "padding": "x" * (decision_packet_module.PROJECT_MANIFEST_MAX_BYTES + 1),
                }
            ),
            "surrogate": json.dumps(
                {
                    "schema_version": "1",
                    "project_name": "North Star",
                    "project_slug": "north-star",
                    "bad": "\ud800",
                }
            ),
            "integer-limit": (
                '{"schema_version":"1","project_name":"North Star",'
                '"project_slug":"north-star","bad":'
                + ("9" * 5000)
                + "}"
            ),
        }
        for label, malformed_manifest in manifests.items():
            with self.subTest(manifest=label), tempfile.TemporaryDirectory() as temporary_directory:
                root = Path(temporary_directory)
                first = persist_decision_packet(
                    DecisionPacketGenerator().generate("Original", "North Star"),
                    output_dir=root,
                )
                project = Path(first["design_intelligence_dir"])
                ledger_before = (project / "DECISIONS.md").read_bytes()
                (project / "PROJECT.json").write_text(malformed_manifest, encoding="utf-8")

                result = persist_decision_packet(
                    DecisionPacketGenerator().generate("Recovered", "North Star"),
                    output_dir=root,
                )

                self.assertEqual(ledger_before, (project / "DECISIONS.md").read_bytes())
                self.assertEqual(
                    {"schema_version": "1", "project_name": "North Star", "project_slug": "north-star"},
                    json.loads((project / "PROJECT.json").read_text(encoding="utf-8")),
                )
                quarantined = list(project.glob("PROJECT.json.corrupt-*"))
                self.assertEqual(1, len(quarantined))
                self.assertIn(str(quarantined[0]), result["preserved_files"])

    def test_temp_write_failures_remove_unpublished_bytes(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            target = root / "BRIEF.md"

            with self.assertRaises(UnicodeEncodeError):
                decision_packet_module._write_complete_temp(target, "bad\ud800")
            self.assertEqual([], list(root.glob(".BRIEF.md.tmp-*")))

            with patch.object(decision_packet_module.os, "fsync", side_effect=OSError("simulated fsync failure")):
                with self.assertRaisesRegex(OSError, "simulated fsync failure"):
                    decision_packet_module._write_complete_temp(target, "complete")
            self.assertEqual([], list(root.glob(".BRIEF.md.tmp-*")))

    def test_surrogate_brief_fails_before_publishing_project_state(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            packet = DecisionPacketGenerator().generate("bad\ud800brief", "North Star")

            with self.assertRaises(UnicodeEncodeError):
                persist_decision_packet(packet, output_dir=root)

            self.assertFalse((root / "design-intelligence").exists())
            self.assertEqual([], list(root.rglob("*.tmp-*")))

    def test_page_formatter_failure_or_surrogate_does_not_publish_project_state(self):
        cases = (
            (RuntimeError("simulated page formatter failure"), RuntimeError),
            ("bad\ud800page", UnicodeEncodeError),
        )
        for formatter_result, expected_error in cases:
            with self.subTest(error=expected_error.__name__), tempfile.TemporaryDirectory() as temporary_directory:
                root = Path(temporary_directory)
                packet = DecisionPacketGenerator().generate("Brief", "North Star")
                formatter = (
                    patch.object(decision_packet_module, "format_page_inquiry", side_effect=formatter_result)
                    if isinstance(formatter_result, BaseException)
                    else patch.object(decision_packet_module, "format_page_inquiry", return_value=formatter_result)
                )
                with formatter:
                    with self.assertRaises(expected_error):
                        persist_decision_packet(packet, page="Catalog", output_dir=root)

                project = root / "design-intelligence" / "north-star"
                self.assertFalse(project.exists())
                self.assertEqual([], list(root.rglob("*.tmp-*")))

    def test_project_persistence_serializes_concurrent_callers(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            entered = threading.Event()
            release = threading.Event()
            errors: list[BaseException] = []
            results: list[dict[str, object]] = []

            def worker() -> None:
                try:
                    entered.set()
                    results.append(
                        persist_decision_packet(
                            DecisionPacketGenerator().generate("Concurrent", "North Star"),
                            output_dir=root,
                        )
                    )
                except BaseException as error:  # pragma: no cover - assertion below reports it
                    errors.append(error)

            with decision_packet_module._persistence_lock(root, "north-star"):
                thread = threading.Thread(target=worker)
                thread.start()
                self.assertTrue(entered.wait(1))
                time.sleep(0.1)
                self.assertTrue(thread.is_alive())
            thread.join(timeout=2)

            self.assertFalse(thread.is_alive())
            self.assertEqual([], errors)
            self.assertEqual(1, len(results))

    def test_corrupt_manifest_recovery_is_serialized_and_reports_existing_paths(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first = persist_decision_packet(
                DecisionPacketGenerator().generate("Original", "North Star"),
                output_dir=root,
            )
            project = Path(first["design_intelligence_dir"])
            (project / "PROJECT.json").write_text('{"schema_version":', encoding="utf-8")
            entered = threading.Event()
            release = threading.Event()
            errors: list[BaseException] = []
            results: list[dict[str, object]] = []
            real_match = decision_packet_module._legacy_project_identity_matches

            def delayed_match(project_dir: Path, identity: str) -> bool:
                if not entered.is_set():
                    entered.set()
                    self.assertTrue(release.wait(2))
                return real_match(project_dir, identity)

            def worker(brief: str) -> None:
                try:
                    results.append(
                        persist_decision_packet(
                            DecisionPacketGenerator().generate(brief, "North Star"),
                            output_dir=root,
                        )
                    )
                except BaseException as error:  # pragma: no cover - assertion below reports it
                    errors.append(error)

            with patch.object(decision_packet_module, "_legacy_project_identity_matches", side_effect=delayed_match):
                first_thread = threading.Thread(target=worker, args=("First recovery",))
                second_thread = threading.Thread(target=worker, args=("Second recovery",))
                first_thread.start()
                self.assertTrue(entered.wait(1))
                second_thread.start()
                time.sleep(0.1)
                self.assertTrue(second_thread.is_alive())
                release.set()
                first_thread.join(timeout=2)
                second_thread.join(timeout=2)

            self.assertFalse(first_thread.is_alive())
            self.assertFalse(second_thread.is_alive())
            self.assertEqual([], errors)
            self.assertEqual(2, len(results))
            for result in results:
                self.assertTrue(all(Path(path).exists() for path in result["preserved_files"]))

    def test_exact_runtime_manifest_artifacts_do_not_block_an_initial_identity_claim(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = root / "design-intelligence" / "north-star"
            project.mkdir(parents=True)
            temporary = project / f".PROJECT.json.tmp-{'a' * 32}"
            corrupt = project / f"PROJECT.json.corrupt-{'b' * 32}"
            temporary.write_bytes(b"complete but unpublished")
            corrupt.write_bytes(b"preserved prior corrupt manifest")

            result = persist_decision_packet(
                DecisionPacketGenerator().generate("Recovered", "North Star"),
                output_dir=root,
            )

            self.assertTrue((project / "PROJECT.json").is_file())
            self.assertEqual(b"complete but unpublished", temporary.read_bytes())
            self.assertEqual(b"preserved prior corrupt manifest", corrupt.read_bytes())
            for expected in (temporary, corrupt):
                self.assertTrue(
                    any(os.path.samefile(expected, reported) for reported in result["preserved_files"])
                )

            impostor_root = root / "other"
            impostor = impostor_root / "design-intelligence" / "north-star"
            impostor.mkdir(parents=True)
            (impostor / ".PROJECT.json.tmp-crash").write_bytes(b"foreign")
            with self.assertRaisesRegex(ValueError, "lacks PROJECT.json"):
                persist_decision_packet(
                    DecisionPacketGenerator().generate("Blocked", "North Star"),
                    output_dir=impostor_root,
                )

    @unittest.skipUnless(os.name == "nt", "Windows junction probe")
    def test_pages_junction_cannot_escape_selected_output(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            packet = DecisionPacketGenerator().generate("Brief", "North Star")
            first = persist_decision_packet(packet, output_dir=root)
            project = Path(first["design_intelligence_dir"])
            outside = root / "outside-pages"
            outside.mkdir()
            pages = project / "pages"
            created = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(pages), str(outside)],
                capture_output=True,
                text=True,
                check=False,
            )
            if created.returncode != 0:
                self.skipTest(f"junction creation unavailable: {created.stderr or created.stdout}")
            try:
                with self.assertRaisesRegex(ValueError, "symlink|junction|reparse|invalid pages"):
                    persist_decision_packet(packet, page="Catalog", output_dir=root)
                self.assertFalse((outside / "catalog.md").exists())
            finally:
                os.rmdir(pages)

    def test_page_parent_is_revalidated_after_inquiry_formatting(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            packet = DecisionPacketGenerator().generate("Brief", "North Star")
            first = persist_decision_packet(packet, output_dir=root)
            project = Path(first["design_intelligence_dir"])
            outside = root / "outside-pages"
            outside.mkdir()
            pages = project / "pages"
            # The formatter hook is now preflighted before persistence claims
            # the project; provide the existing parent it intentionally swaps.
            pages.mkdir()
            real_format = decision_packet_module.format_page_inquiry
            redirect_kind: bool | None = None

            def swap_parent(page_name: str, page_brief: str | None = None) -> str:
                nonlocal redirect_kind
                pages.rmdir()
                redirect_kind = create_directory_redirect(pages, outside)
                return real_format(page_name, page_brief)

            try:
                with patch.object(decision_packet_module, "format_page_inquiry", side_effect=swap_parent):
                    with self.assertRaisesRegex(ValueError, "symlink|junction|reparse|inside"):
                        persist_decision_packet(packet, page="Catalog", output_dir=root)
                self.assertFalse((outside / "catalog.md").exists())
            finally:
                if redirect_kind is not None and (pages.exists() or pages.is_symlink()):
                    remove_directory_redirect(pages, redirect_kind)

    @unittest.skipUnless(os.name == "nt", "Windows alias race probe")
    def test_output_root_redirect_inserted_during_alias_normalization_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            parent = Path(temporary_directory)
            selected_root = parent / "selected-output"
            selected_root.mkdir()
            outside = parent / "outside"
            outside.mkdir()
            sentinel = outside / "sentinel.txt"
            sentinel.write_bytes(b"outside bytes")
            packet = DecisionPacketGenerator().generate("Brief", "North Star")
            real_long_name = decision_packet_module._windows_long_path_name
            redirect_kind: bool | None = None

            def insert_redirect(path: Path, label: str) -> Path:
                nonlocal redirect_kind
                result = real_long_name(path, label)
                if label == "Selected output directory" and redirect_kind is None:
                    selected_root.rmdir()
                    redirect_kind = create_directory_redirect(selected_root, outside)
                return result

            try:
                with patch.object(
                    decision_packet_module,
                    "_windows_long_path_name",
                    side_effect=insert_redirect,
                ):
                    with self.assertRaisesRegex(ValueError, "symlink|junction|reparse"):
                        persist_decision_packet(packet, output_dir=selected_root)
                self.assertEqual(b"outside bytes", sentinel.read_bytes())
                self.assertFalse((outside / "design-intelligence").exists())
            finally:
                if redirect_kind is not None and (selected_root.exists() or selected_root.is_symlink()):
                    remove_directory_redirect(selected_root, redirect_kind)

    @unittest.skipUnless(os.name == "nt", "Windows 8.3 alias probe")
    def test_windows_short_alias_preserves_persistence_root_and_lock_identity(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            long_root = Path(temporary_directory).resolve()
            short_root = windows_short_path(long_root)
            if os.path.normcase(os.fspath(short_root)) == os.path.normcase(os.fspath(long_root)):
                self.skipTest("the temporary volume did not provide a distinct 8.3 alias")

            result = persist_decision_packet(
                DecisionPacketGenerator().generate("Alias brief", "Alias Project"),
                output_dir=short_root,
            )
            project = Path(result["design_intelligence_dir"])
            self.assertTrue(project.resolve().is_relative_to(long_root))

            with decision_packet_module._persistence_lock(long_root, "alias-lock"):
                with self.assertRaisesRegex(RuntimeError, "Another persistence operation"):
                    with decision_packet_module._persistence_lock(short_root, "alias-lock"):
                        pass


class RetrievalLimitTests(unittest.TestCase):
    def test_public_apis_reject_bool_non_int_and_non_positive_limits(self):
        for invalid in (True, False, 0, -1, 1.5, "5", None):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, "positive integer"):
                    search("interface", "product", invalid)
                with self.assertRaisesRegex(ValueError, "positive integer"):
                    search_stack("interface", "react", invalid)

    def test_positive_integer_limit_remains_valid(self):
        result = search("bicycle", "product", 5)
        self.assertIn("results", result)
        self.assertLessEqual(len(result["results"]), 5)

    def test_cli_rejects_invalid_limit_and_accepts_valid_limit(self):
        command = [sys.executable, str(SKILL_SCRIPTS / "search.py"), "interface", "--domain", "product"]
        invalid = subprocess.run(
            command + ["--max-results", "-1"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertNotEqual(0, invalid.returncode)
        self.assertIn("positive integer", invalid.stderr)

        valid = subprocess.run(
            command + ["--max-results", "5", "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(0, valid.returncode, valid.stderr)
        self.assertIn('"domain": "product"', valid.stdout)

    def test_cli_rejects_options_that_would_be_ignored_in_the_selected_mode(self):
        script = str(SKILL_SCRIPTS / "search.py")
        probes = [
            (["interface", "--domain", "product", "--format", "json"], "--format requires"),
            (["interface", "--domain", "product", "--project-name", "Ignored"], "--project-name requires"),
            (["Open inquiry", "--decision-packet", "--max-results", "2"], "--max-results is available only"),
        ]
        for arguments, expected in probes:
            with self.subTest(arguments=arguments):
                result = subprocess.run(
                    [sys.executable, script, *arguments],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    check=False,
                )
                self.assertNotEqual(0, result.returncode)
                self.assertIn(expected, result.stderr)


class InstallerOwnershipTests(unittest.TestCase):
    @staticmethod
    def make_source(root: Path) -> Path:
        source = root / "source"
        source.mkdir()
        (source / "SKILL.md").write_text("---\nname: snowe-ui-skill\n---\nsource\n", encoding="utf-8")
        return source

    def test_unowned_fixed_transient_paths_are_quarantined_not_deleted(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root)
            destination = root / "skills" / "snowe-ui-skill"
            destination.parent.mkdir()
            fixed_staging = destination.parent / ".snowe-ui-skill.installing"
            fixed_staging.mkdir()
            (fixed_staging / "user-data.txt").write_bytes(b"preserve me")
            fixed_previous = destination.parent / ".snowe-ui-skill.previous"
            fixed_previous.mkdir()
            (fixed_previous / "SKILL.md").write_text("---\nname: snowe-ui-skill\n---\nforeign install\n", encoding="utf-8")
            (fixed_previous / "user-data.txt").write_bytes(b"preserve me too")

            result = INSTALLER.install_skill(source, destination)

            self.assertEqual("updated", result["operation"])
            self.assertEqual(b"preserve me", next(destination.parent.glob(".snowe-ui-skill.installing.unowned-*")).joinpath("user-data.txt").read_bytes())
            self.assertEqual(b"preserve me too", next(destination.parent.glob(".snowe-ui-skill.previous.unowned-*")).joinpath("user-data.txt").read_bytes())
            self.assertTrue((destination / "SKILL.md").is_file())
            self.assertFalse((destination.parent / ".snowe-ui-skill.installing.owner").exists())
            self.assertFalse((destination.parent / ".snowe-ui-skill.previous.owner").exists())

    def test_unrecognized_final_file_and_directory_are_rejected_without_loss(self):
        for kind in ("file", "directory", "foreign-skill"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary_directory:
                root = Path(temporary_directory)
                source = self.make_source(root)
                destination = root / "skills" / "snowe-ui-skill"
                destination.parent.mkdir()
                if kind == "file":
                    destination.write_bytes(b"foreign destination bytes")
                    before = destination.read_bytes()
                elif kind == "directory":
                    destination.mkdir()
                    (destination / "foreign.txt").write_bytes(b"foreign directory bytes")
                    before = (destination / "foreign.txt").read_bytes()
                else:
                    destination.mkdir()
                    (destination / "SKILL.md").write_text(
                        "---\nname: another-skill\n---\nforeign skill\n",
                        encoding="utf-8",
                    )
                    before = (destination / "SKILL.md").read_bytes()

                with self.assertRaisesRegex(ValueError, "not a recognized Snowe install"):
                    INSTALLER.install_skill(source, destination)

                if kind == "file":
                    self.assertEqual(before, destination.read_bytes())
                elif kind == "directory":
                    self.assertEqual(before, (destination / "foreign.txt").read_bytes())
                else:
                    self.assertEqual(before, (destination / "SKILL.md").read_bytes())
                self.assertFalse(list(destination.parent.glob("snowe-ui-skill.unowned-*")))

    def test_final_destination_replacement_race_is_refused_without_deleting_foreign_bytes(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root)
            destination = root / "skills" / "snowe-ui-skill"
            destination.mkdir(parents=True)
            (destination / "SKILL.md").write_text("---\nname: snowe-ui-skill\n---\nold install\n", encoding="utf-8")
            moved_original = destination.parent / "moved-original-destination"
            real_recognized = INSTALLER._is_recognized_install_tree
            real_rename = INSTALLER._rename
            calls = 0

            def replace_between_checks(path: Path) -> bool:
                nonlocal calls
                calls += 1
                if calls == 2:
                    real_rename(path, moved_original)
                    path.write_bytes(b"foreign destination race")
                return real_recognized(path)

            with patch.object(INSTALLER, "_is_recognized_install_tree", side_effect=replace_between_checks):
                with self.assertRaisesRegex(ValueError, "changed before activation"):
                    INSTALLER.install_skill(source, destination)

            self.assertEqual(b"foreign destination race", destination.read_bytes())
            self.assertIn("old install", (moved_original / "SKILL.md").read_text(encoding="utf-8"))

    def test_owned_staging_cleanup_quarantines_a_replaced_inode(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root)
            destination = root / "skills" / "snowe-ui-skill"
            destination.parent.mkdir()
            staging = destination.parent / ".snowe-ui-skill.installing"
            moved_original = destination.parent / "moved-original-stage"
            real_copytree = INSTALLER.shutil.copytree
            real_rename = INSTALLER._rename

            def replace_after_copy(source_path: Path, staging_path: Path, **options):
                result = real_copytree(source_path, staging_path, **options)
                real_rename(staging_path, moved_original)
                staging_path.mkdir()
                (staging_path / "foreign.txt").write_bytes(b"replacement bytes")
                raise OSError("simulated cleanup race")

            with patch.object(INSTALLER.shutil, "copytree", side_effect=replace_after_copy):
                with self.assertRaisesRegex(OSError, "simulated cleanup race"):
                    INSTALLER.install_skill(source, destination)

            quarantined = next(destination.parent.glob(".snowe-ui-skill.installing.unowned-*"))
            self.assertEqual(b"replacement bytes", (quarantined / "foreign.txt").read_bytes())
            self.assertTrue((moved_original / "SKILL.md").is_file())

    def test_activation_refuses_a_staging_inode_replaced_after_validation(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root)
            destination = root / "skills" / "snowe-ui-skill"
            destination.mkdir(parents=True)
            (destination / "SKILL.md").write_text("---\nname: snowe-ui-skill\n---\nold install\n", encoding="utf-8")
            staging = destination.parent / ".snowe-ui-skill.installing"
            moved_original = destination.parent / "moved-before-activation"
            real_owns = INSTALLER._owns_path
            real_rename = INSTALLER._rename
            replaced = False

            def replace_before_activation(path: Path, target: Path, role: str, token: str) -> bool:
                nonlocal replaced
                if role == "staging" and not replaced and os.path.samefile(path, staging):
                    replaced = True
                    real_rename(staging, moved_original)
                    staging.mkdir()
                    (staging / "SKILL.md").write_text("foreign stage", encoding="utf-8")
                    (staging / "foreign.txt").write_bytes(b"foreign staging bytes")
                return real_owns(path, target, role, token)

            with patch.object(INSTALLER, "_owns_path", side_effect=replace_before_activation):
                with self.assertRaisesRegex(ValueError, "changed identity"):
                    INSTALLER.install_skill(source, destination)

            self.assertTrue(replaced)
            self.assertIn("old install", (destination / "SKILL.md").read_text(encoding="utf-8"))
            quarantined = next(destination.parent.glob(".snowe-ui-skill.installing.unowned-*"))
            self.assertEqual(b"foreign staging bytes", (quarantined / "foreign.txt").read_bytes())
            self.assertTrue((moved_original / "SKILL.md").is_file())

    def test_activation_cleanup_quarantines_a_replaced_destination_inode(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root)
            destination = root / "skills" / "snowe-ui-skill"
            destination.mkdir(parents=True)
            (destination / "SKILL.md").write_text("---\nname: snowe-ui-skill\n---\nold install\n", encoding="utf-8")
            moved_original = destination.parent / "moved-activated-stage"
            real_rename = INSTALLER._rename

            def replace_before_validation(path: Path) -> None:
                real_rename(path, moved_original)
                path.mkdir()
                (path / "foreign.txt").write_bytes(b"replacement destination")
                raise RuntimeError("simulated validation failure")

            with patch.object(INSTALLER, "_validate_activated_tree", side_effect=replace_before_validation):
                with self.assertRaisesRegex(RuntimeError, "simulated validation failure"):
                    INSTALLER.install_skill(source, destination)

            self.assertIn("old install", (destination / "SKILL.md").read_text(encoding="utf-8"))
            quarantined = next(destination.parent.glob("snowe-ui-skill.unowned-*"))
            self.assertEqual(b"replacement destination", (quarantined / "foreign.txt").read_bytes())
            self.assertTrue((moved_original / "SKILL.md").is_file())

    def test_rollback_quarantines_a_previous_inode_replaced_after_swap(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root)
            destination = root / "skills" / "snowe-ui-skill"
            destination.mkdir(parents=True)
            (destination / "SKILL.md").write_text(
                "---\nname: snowe-ui-skill\n---\nold install\n", encoding="utf-8"
            )
            previous = destination.parent / ".snowe-ui-skill.previous"
            moved_original = destination.parent / "moved-original-previous"
            real_rename = INSTALLER._rename

            def replace_previous_before_rollback(_path: Path) -> None:
                real_rename(previous, moved_original)
                previous.mkdir()
                (previous / "SKILL.md").write_text(
                    "---\nname: another-skill\n---\nforeign rollback\n", encoding="utf-8"
                )
                (previous / "foreign.txt").write_bytes(b"foreign previous bytes")
                raise RuntimeError("simulated activation failure")

            with patch.object(
                INSTALLER,
                "_validate_activated_tree",
                side_effect=replace_previous_before_rollback,
            ):
                with self.assertRaisesRegex(RuntimeError, "changed identity"):
                    INSTALLER.install_skill(source, destination)

            self.assertFalse(destination.exists())
            quarantined = next(destination.parent.glob(".snowe-ui-skill.previous.unowned-*"))
            self.assertEqual(b"foreign previous bytes", (quarantined / "foreign.txt").read_bytes())
            self.assertIn("old install", (moved_original / "SKILL.md").read_text(encoding="utf-8"))

    def test_invalid_interrupted_previous_tree_is_quarantined_not_rollback_state(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root)
            destination = root / "skills" / "snowe-ui-skill"
            destination.parent.mkdir()
            previous = destination.parent / ".snowe-ui-skill.previous"
            previous.mkdir()
            (previous / "SKILL.md").write_text("---\nname: snowe-ui-skill\n---\nunsafe previous\n", encoding="utf-8")
            outside = root / "outside"
            outside.mkdir()
            (outside / "sentinel.txt").write_bytes(b"outside bytes")
            redirect = previous / "redirect"
            redirect_kind = create_directory_redirect(redirect, outside)
            try:
                with patch.object(
                    INSTALLER,
                    "_validate_activated_tree",
                    side_effect=RuntimeError("simulated activation failure"),
                ):
                    with self.assertRaisesRegex(RuntimeError, "simulated activation failure"):
                        INSTALLER.install_skill(source, destination)

                self.assertFalse(destination.exists())
                self.assertEqual(b"outside bytes", (outside / "sentinel.txt").read_bytes())
                quarantined = next(destination.parent.glob(".snowe-ui-skill.previous.unowned-*"))
                self.assertTrue((quarantined / "SKILL.md").is_file())
                self.assertTrue((quarantined / "redirect").exists())
            finally:
                quarantined = next(destination.parent.glob(".snowe-ui-skill.previous.unowned-*"), None)
                if quarantined is not None:
                    quarantined_redirect = quarantined / "redirect"
                    if quarantined_redirect.exists() or quarantined_redirect.is_symlink():
                        remove_directory_redirect(quarantined_redirect, redirect_kind)

    def test_installation_lock_rejects_shared_hardlink_without_mutating_it(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            foreign = root / "foreign-lock"
            foreign.write_bytes(b"foreign installer lock bytes")
            lock = root / ".snowe-ui-skill.install.lock"
            try:
                os.link(foreign, lock)
            except OSError as error:
                self.skipTest(f"hardlinks are unavailable: {error}")

            with self.assertRaisesRegex(ValueError, "shared hardlink"):
                with INSTALLER._installation_lock(root):
                    pass

            self.assertEqual(b"foreign installer lock bytes", foreign.read_bytes())
            self.assertTrue(os.path.samefile(foreign, lock))

    def test_unowned_symlink_is_not_followed_or_deleted(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root)
            destination = root / "skills" / "snowe-ui-skill"
            destination.parent.mkdir()
            target = root / "outside"
            target.mkdir()
            (target / "sentinel.txt").write_text("keep", encoding="utf-8")
            fixed_staging = destination.parent / ".snowe-ui-skill.installing"
            try:
                fixed_staging.symlink_to(target, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("directory symlinks are unavailable on this platform")

            INSTALLER.install_skill(source, destination)

            self.assertEqual("keep", (target / "sentinel.txt").read_text(encoding="utf-8"))
            quarantined = next(destination.parent.glob(".snowe-ui-skill.installing.unowned-*"))
            self.assertTrue(quarantined.is_symlink())
            self.assertTrue(os.path.samefile(target, quarantined))

    def test_forged_owner_marker_cannot_authorize_recursive_deletion(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root)
            destination = root / "skills" / "snowe-ui-skill"
            destination.parent.mkdir()
            fixed = destination.parent / ".snowe-ui-skill.installing"
            fixed.mkdir()
            (fixed / "sentinel.txt").write_bytes(b"foreign")
            marker = destination.parent / ".snowe-ui-skill.installing.owner"
            marker.write_text(
                json.dumps(
                    {
                        "schema_version": "1",
                        "product": "snowe-ui-skill",
                        "role": "staging",
                        "path": INSTALLER._lexical_path(fixed),
                        "destination": INSTALLER._lexical_path(destination),
                        "token": "forged-token",
                    }
                ),
                encoding="utf-8",
            )

            INSTALLER.install_skill(source, destination)

            preserved = [path for path in destination.parent.glob(".snowe-ui-skill.installing.unowned-*") if path.is_dir()]
            self.assertEqual(1, len(preserved))
            self.assertEqual(b"foreign", (preserved[0] / "sentinel.txt").read_bytes())

    def test_source_redirect_is_rejected_without_copying_external_content(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root)
            destination = root / "skills" / "snowe-ui-skill"
            outside = root / "outside"
            outside.mkdir()
            (outside / "sentinel.txt").write_bytes(b"external")
            redirect = source / "assets"
            is_junction = False
            try:
                redirect.symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError):
                if os.name != "nt":
                    self.skipTest("directory symlinks are unavailable on this platform")
                created = subprocess.run(
                    ["cmd", "/c", "mklink", "/J", str(redirect), str(outside)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if created.returncode != 0:
                    self.skipTest(f"source redirect creation unavailable: {created.stderr or created.stdout}")
                is_junction = True
            try:
                with self.assertRaisesRegex(ValueError, "self-contained; symlinks, junctions"):
                    INSTALLER.install_skill(source, destination)
                self.assertFalse(destination.exists())
                self.assertEqual(b"external", (outside / "sentinel.txt").read_bytes())
            finally:
                if redirect.exists() or redirect.is_symlink():
                    if is_junction:
                        os.rmdir(redirect)
                    else:
                        redirect.unlink()

    def test_source_root_redirect_is_rejected_before_resolution(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_target = self.make_source(root)
            source_link = root / "source-link"
            destination = root / "skills" / "snowe-ui-skill"
            redirect_kind = create_directory_redirect(source_link, source_target)
            try:
                with self.assertRaisesRegex(ValueError, "Skill source.*(symlink|junction|reparse)"):
                    INSTALLER.install_skill(source_link, destination)
                self.assertFalse(destination.exists())
                self.assertTrue((source_target / "SKILL.md").is_file())
            finally:
                if source_link.exists() or source_link.is_symlink():
                    remove_directory_redirect(source_link, redirect_kind)

    @unittest.skipUnless(os.name == "nt", "Windows source race probe")
    def test_source_redirect_inserted_after_staging_claim_is_rejected_before_copy(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root)
            preserved_source = root / "preserved-source"
            outside = root / "outside-source"
            outside.mkdir()
            sentinel = outside / "sentinel.txt"
            sentinel.write_bytes(b"outside source bytes")
            destination = root / "skills" / "snowe-ui-skill"
            real_bind = INSTALLER._bind_owner_slot
            redirect_kind: bool | None = None

            def swap_source_after_claim(*args, **kwargs):
                nonlocal redirect_kind
                result = real_bind(*args, **kwargs)
                source.rename(preserved_source)
                redirect_kind = create_directory_redirect(source, outside)
                return result

            try:
                with patch.object(INSTALLER, "_bind_owner_slot", side_effect=swap_source_after_claim):
                    with self.assertRaisesRegex(ValueError, "Skill source.*(symlink|junction|reparse)"):
                        INSTALLER.install_skill(source, destination)
                self.assertFalse(destination.exists())
                self.assertEqual(b"outside source bytes", sentinel.read_bytes())
                self.assertTrue((preserved_source / "SKILL.md").is_file())
            finally:
                if redirect_kind is not None and (source.exists() or source.is_symlink()):
                    remove_directory_redirect(source, redirect_kind)

    def test_staged_tree_is_revalidated_before_activation(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root)
            destination = root / "skills" / "snowe-ui-skill"
            real_validate = INSTALLER._validate_source_tree
            validated: list[Path] = []

            def record_validation(path: Path) -> None:
                validated.append(path)
                real_validate(path)

            with patch.object(INSTALLER, "_validate_source_tree", side_effect=record_validation):
                INSTALLER.install_skill(source, destination)

            self.assertEqual([source.resolve(), source.resolve()], validated[:2])
            self.assertTrue(os.path.samefile(destination.parent, validated[2].parent))
            self.assertIn("installing", validated[2].name)
            self.assertTrue((destination / "SKILL.md").is_file())

    def test_activation_reparse_is_rejected_and_previous_install_restored(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root)
            destination = root / "skills" / "snowe-ui-skill"
            destination.mkdir(parents=True)
            (destination / "SKILL.md").write_text("---\nname: snowe-ui-skill\n---\nold install\n", encoding="utf-8")
            outside = root / "outside"
            outside.mkdir()
            (outside / "sentinel.txt").write_text("keep", encoding="utf-8")
            staging = destination.parent / ".snowe-ui-skill.installing"
            attacker_copy = destination.parent / "attacker-copy"
            real_rename = INSTALLER._rename
            redirect_kind: bool | None = None

            def replace_activation(source_path: Path, destination_path: Path) -> None:
                nonlocal redirect_kind
                if (
                    staging.exists()
                    and os.path.samefile(source_path, staging)
                    and destination_path.name == destination.name
                    and os.path.samefile(destination_path.parent, destination.parent)
                ):
                    real_rename(source_path, attacker_copy)
                    redirect_kind = create_directory_redirect(staging, outside)
                real_rename(source_path, destination_path)

            try:
                with patch.object(INSTALLER, "_rename", side_effect=replace_activation):
                    with self.assertRaisesRegex(ValueError, "symlink|junction|reparse"):
                        INSTALLER.install_skill(source, destination)
                self.assertIsNotNone(redirect_kind)
                self.assertTrue(attacker_copy.is_dir())
                self.assertIn("old install", (destination / "SKILL.md").read_text(encoding="utf-8"))
                self.assertEqual("keep", (outside / "sentinel.txt").read_text(encoding="utf-8"))
            finally:
                if redirect_kind is not None and (staging.exists() or staging.is_symlink()):
                    remove_directory_redirect(staging, redirect_kind)

    def test_concurrent_install_is_rejected_by_os_lock(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root)
            destination = root / "skills" / "snowe-ui-skill"
            destination.parent.mkdir()

            with INSTALLER._installation_lock(destination.parent):
                with self.assertRaisesRegex(RuntimeError, "Another Snowe installation"):
                    INSTALLER.install_skill(source, destination)

    @unittest.skipUnless(os.name == "nt", "Windows alias race probe")
    def test_destination_redirect_inserted_during_alias_normalization_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root)
            destination = root / "skills" / "snowe-ui-skill"
            destination.parent.mkdir()
            outside = root / "outside" / "snowe-ui-skill"
            outside.mkdir(parents=True)
            (outside / "SKILL.md").write_text(
                "---\nname: snowe-ui-skill\n---\nexternal install\n",
                encoding="utf-8",
            )
            sentinel = outside / "sentinel.txt"
            sentinel.write_bytes(b"outside bytes")
            real_long_name = INSTALLER._windows_long_path_name
            redirect_kind: bool | None = None

            def insert_redirect(path: Path, label: str) -> Path:
                nonlocal redirect_kind
                result = real_long_name(path, label)
                if label == "Destination" and redirect_kind is None:
                    redirect_kind = create_directory_redirect(destination, outside)
                return result

            try:
                with patch.object(INSTALLER, "_windows_long_path_name", side_effect=insert_redirect):
                    with self.assertRaisesRegex(ValueError, "symlink|junction|reparse"):
                        INSTALLER.install_skill(source, destination)
                self.assertEqual(b"outside bytes", sentinel.read_bytes())
                self.assertIn("external install", (outside / "SKILL.md").read_text(encoding="utf-8"))
            finally:
                if redirect_kind is not None and (destination.exists() or destination.is_symlink()):
                    remove_directory_redirect(destination, redirect_kind)

    @unittest.skipUnless(os.name == "nt", "Windows 8.3 alias probe")
    def test_windows_short_alias_preserves_overlap_and_install_lock_identity(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            long_root = Path(temporary_directory).resolve()
            short_root = windows_short_path(long_root)
            if os.path.normcase(os.fspath(short_root)) == os.path.normcase(os.fspath(long_root)):
                self.skipTest("the temporary volume did not provide a distinct 8.3 alias")

            source = self.make_source(long_root)
            nested_destination = short_root / source.relative_to(long_root) / "snowe-ui-skill"
            with self.assertRaisesRegex(ValueError, "must not contain or replace"):
                INSTALLER.install_skill(source, nested_destination)

            destination = short_root / "skills" / "snowe-ui-skill"
            (long_root / "skills").mkdir()
            with INSTALLER._installation_lock(long_root / "skills"):
                with self.assertRaisesRegex(RuntimeError, "Another Snowe installation"):
                    INSTALLER.install_skill(source, destination)

    @unittest.skipUnless(os.name == "nt", "Windows final-component 8.3 alias probe")
    def test_existing_destination_accepts_its_real_final_short_alias(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory).resolve()
            source = self.make_source(root)
            destination = root / "skills" / "snowe-ui-skill"
            INSTALLER.install_skill(source, destination)
            short_destination = windows_short_path(destination)
            if os.path.normcase(short_destination.name) == os.path.normcase(destination.name):
                self.skipTest("the temporary volume did not provide a final-component 8.3 alias")

            stale = destination / "stale.txt"
            stale.write_bytes(b"remove on exact update")
            result = INSTALLER.install_skill(source, short_destination)
            self.assertEqual("updated", result["operation"])
            self.assertFalse(stale.exists())
            self.assertTrue(os.path.samefile(destination, Path(result["destination"])))

    @unittest.skipUnless(os.name == "nt", "Windows junction probe")
    def test_destination_junction_is_rejected_without_touching_target(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root)
            destination = root / "skills" / "snowe-ui-skill"
            destination.parent.mkdir()
            outside = root / "outside" / "snowe-ui-skill"
            outside.mkdir(parents=True)
            (outside / "sentinel.txt").write_bytes(b"keep")
            created = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(destination), str(outside)],
                capture_output=True,
                text=True,
                check=False,
            )
            if created.returncode != 0:
                self.skipTest(f"junction creation unavailable: {created.stderr or created.stdout}")
            try:
                junction_argument = windows_short_path(destination)
                with self.assertRaisesRegex(ValueError, "symlink|junction|reparse"):
                    INSTALLER.install_skill(source, junction_argument)
                self.assertEqual(b"keep", (outside / "sentinel.txt").read_bytes())
            finally:
                os.rmdir(destination)


if __name__ == "__main__":
    unittest.main()
