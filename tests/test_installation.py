from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
INSTALLER_PATH = ROOT / "scripts" / "install_skill.py"
SPEC = importlib.util.spec_from_file_location("snowe_install_skill", INSTALLER_PATH)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - import machinery failure
    raise RuntimeError(f"Cannot load installer: {INSTALLER_PATH}")
INSTALLER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INSTALLER)


class InstallationTests(unittest.TestCase):
    @staticmethod
    def make_source(root: Path, marker: str = "first") -> Path:
        source = root / "source"
        (source / "scripts" / "__pycache__").mkdir(parents=True)
        (source / "SKILL.md").write_text(f"---\nname: snowe-ui-skill\n---\n{marker}\n", encoding="utf-8")
        (source / "scripts" / "tool.py").write_text(f"MARKER = {marker!r}\n", encoding="utf-8")
        (source / "scripts" / "__pycache__" / "tool.pyc").write_bytes(b"cache")
        return source

    def test_fresh_install_and_reinstall_are_exact_and_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root)
            destination = root / "home" / ".agents" / "skills" / "snowe-ui-skill"

            first = INSTALLER.install_skill(source, destination)
            self.assertEqual("installed", first["operation"])
            self.assertTrue((destination / "SKILL.md").is_file())
            self.assertFalse((destination / "scripts" / "__pycache__").exists())

            (destination / "stale.txt").write_text("obsolete", encoding="utf-8")
            (source / "SKILL.md").write_text("---\nname: snowe-ui-skill\n---\nsecond\n", encoding="utf-8")
            (source / "new.txt").write_text("new", encoding="utf-8")
            second = INSTALLER.install_skill(source, destination)

            self.assertEqual("updated", second["operation"])
            self.assertIn("second", (destination / "SKILL.md").read_text(encoding="utf-8"))
            self.assertTrue((destination / "new.txt").is_file())
            self.assertFalse((destination / "stale.txt").exists())
            self.assertFalse((destination / "snowe-ui-skill").exists())
            self.assertFalse((destination.parent / ".snowe-ui-skill.installing").exists())
            self.assertFalse((destination.parent / ".snowe-ui-skill.previous").exists())

    def test_interrupted_previous_swap_is_recovered_before_update(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root, "replacement")
            destination = root / "skills" / "snowe-ui-skill"
            destination.parent.mkdir(parents=True)
            previous = destination.parent / ".snowe-ui-skill.previous"
            previous.mkdir()
            (previous / "SKILL.md").write_text("---\nname: snowe-ui-skill\n---\nold\n", encoding="utf-8")
            staging = destination.parent / ".snowe-ui-skill.installing"
            staging.mkdir()
            (staging / "partial.txt").write_text("partial", encoding="utf-8")

            result = INSTALLER.install_skill(source, destination)

            self.assertEqual("updated", result["operation"])
            self.assertIn("replacement", (destination / "SKILL.md").read_text(encoding="utf-8"))
            self.assertFalse(previous.exists())
            self.assertFalse(staging.exists())

    def test_activation_failure_restores_previous_install(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root, "replacement")
            destination = root / "skills" / "snowe-ui-skill"
            destination.mkdir(parents=True)
            (destination / "SKILL.md").write_text("---\nname: snowe-ui-skill\n---\nold\n", encoding="utf-8")
            destination_argument = destination.parent / "path-alias" / ".." / destination.name
            resolved_destination = destination_argument.resolve(strict=False)
            staging = resolved_destination.parent / f".{INSTALLER.PRODUCT_NAME}.installing"
            self.assertNotEqual(destination_argument, resolved_destination)
            real_rename = INSTALLER._rename

            def fail_staging_activation(source_path: Path, destination_path: Path) -> None:
                if source_path == staging and destination_path == resolved_destination:
                    raise OSError("simulated activation failure")
                real_rename(source_path, destination_path)

            with patch.object(INSTALLER, "_rename", side_effect=fail_staging_activation):
                with self.assertRaisesRegex(OSError, "simulated activation failure"):
                    INSTALLER.install_skill(source, destination_argument)

            self.assertIn("old", (destination / "SKILL.md").read_text(encoding="utf-8"))
            self.assertFalse((destination.parent / ".snowe-ui-skill.installing").exists())
            self.assertFalse((destination.parent / ".snowe-ui-skill.previous").exists())

    def test_staging_copy_failure_preserves_destination_and_removes_partial_state(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root, "replacement")
            destination = root / "skills" / "snowe-ui-skill"
            destination.mkdir(parents=True)
            (destination / "SKILL.md").write_text("---\nname: snowe-ui-skill\n---\nold\n", encoding="utf-8")

            def fail_after_partial_copy(_source: Path, staging: Path, **_options) -> None:
                staging.mkdir(exist_ok=True)
                (staging / "partial.txt").write_text("partial", encoding="utf-8")
                raise OSError("simulated staging failure")

            with patch.object(INSTALLER.shutil, "copytree", side_effect=fail_after_partial_copy):
                with self.assertRaisesRegex(OSError, "simulated staging failure"):
                    INSTALLER.install_skill(source, destination)

            self.assertIn("old", (destination / "SKILL.md").read_text(encoding="utf-8"))
            self.assertFalse((destination.parent / ".snowe-ui-skill.installing").exists())
            self.assertFalse((destination.parent / ".snowe-ui-skill.previous").exists())

    def test_staging_failure_preserves_interrupted_previous_tree(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root, "replacement")
            destination = root / "skills" / "snowe-ui-skill"
            destination.parent.mkdir(parents=True)
            previous = destination.parent / ".snowe-ui-skill.previous"
            previous.mkdir()
            (previous / "SKILL.md").write_text("---\nname: snowe-ui-skill\n---\nold install\n", encoding="utf-8")
            (previous / "user-data.txt").write_bytes(b"foreign bytes")

            with patch.object(INSTALLER.shutil, "copytree", side_effect=OSError("simulated staging failure")):
                with self.assertRaisesRegex(OSError, "simulated staging failure"):
                    INSTALLER.install_skill(source, destination)

            self.assertFalse(destination.exists())
            self.assertIn("old install", (previous / "SKILL.md").read_text(encoding="utf-8"))
            self.assertEqual(b"foreign bytes", (previous / "user-data.txt").read_bytes())

    def test_overlapping_source_and_destination_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = self.make_source(Path(temporary_directory))
            destination = source / "nested" / "snowe-ui-skill"
            with self.assertRaisesRegex(ValueError, "must not contain or replace"):
                INSTALLER.install_skill(source, destination)

    def test_public_cli_installs_actual_product_to_explicit_destination(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "skills" / "snowe-ui-skill"
            completed = subprocess.run(
                [sys.executable, str(INSTALLER_PATH), "--destination", str(destination)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertIn("Snowe installed", completed.stdout)
            self.assertTrue((destination / "SKILL.md").is_file())
            self.assertTrue((destination / "scripts" / "search.py").is_file())
            self.assertFalse((destination / "snowe-ui-skill").exists())
            ignored_names = {"__pycache__", ".DS_Store"}
            expected = {
                path.relative_to(INSTALLER.DEFAULT_SOURCE).as_posix()
                for path in INSTALLER.DEFAULT_SOURCE.rglob("*")
                if path.is_file()
                and not any(part in ignored_names for part in path.relative_to(INSTALLER.DEFAULT_SOURCE).parts)
                and path.suffix not in {".pyc", ".pyo"}
            }
            installed = {
                path.relative_to(destination).as_posix()
                for path in destination.rglob("*")
                if path.is_file()
            }
            self.assertEqual(expected, installed)

    def test_public_install_guidance_uses_current_exact_update_path(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("$HOME/.agents/skills", readme)
        self.assertIn("$skill-installer", readme)
        self.assertIn("scripts/install_skill.py", readme)
        self.assertIn("repeated runs replace the destination exactly", readme)
        self.assertIn("~/.codex/skills/snowe-ui-skill", readme)
        self.assertNotIn("Copy-Item -Recurse", readme)
        self.assertNotIn("cp -R snowe-ui-skill/skill", readme)


if __name__ == "__main__":
    unittest.main()
