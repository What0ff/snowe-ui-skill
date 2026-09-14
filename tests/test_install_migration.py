import importlib.util
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("migration_installer", ROOT / "scripts/install_skill.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        (self.source / "SKILL.md").write_text("---\nname: snowe-ui-skill\ndescription: fixture\n---\n")
        self.destination = self.root / "new-skills/snowe-ui-skill"
        self.legacy = self.root / "old-skills/snowe-ui-skill"
        self.backups = self.root / "backups"
        installer.install_skill(self.source, self.legacy)

    def migrate(self):
        return installer.migrate_legacy(self.source, self.destination, self.legacy, self.backups)

    def test_different_legacy_is_preserved_and_repeat_is_safe(self):
        (self.legacy / "personal.txt").write_text("user changes")
        result = self.migrate()
        self.assertFalse(self.legacy.exists())
        self.assertEqual("user changes", (Path(result["backup"]) / "personal.txt").read_text())
        self.assertEqual("already-absent", self.migrate()["migration"])
        self.assertEqual((self.source / "SKILL.md").read_bytes(), (self.destination / "SKILL.md").read_bytes())

    def test_failure_after_move_restores_old_copy(self):
        real = installer._migration_fingerprint
        def failure(path):
            if path.parent == self.backups and path.exists(): raise OSError("after move")
            return real(path)
        with patch.object(installer, "_migration_fingerprint", side_effect=failure):
            with self.assertRaises(OSError): self.migrate()
        self.assertTrue((self.legacy / "SKILL.md").is_file())
        self.migrate()
        self.assertFalse(self.legacy.exists())

    def test_unsafe_backup_and_other_skill_are_refused(self):
        with self.assertRaises(ValueError): installer.migrate_legacy(self.source, self.destination, self.legacy, self.legacy.parent / "backup")
        (self.legacy / "SKILL.md").write_text("---\nname: other\n---")
        with self.assertRaises(ValueError): self.migrate()
        self.assertTrue(self.legacy.exists())

    def test_identical_copies_and_crash_recovery(self):
        installer.install_skill(self.source, self.destination)
        self.assertTrue(installer.diagnose_installations(self.destination, self.legacy)["duplicates"])
        code = '''import importlib.util,os,sys
from pathlib import Path
spec=importlib.util.spec_from_file_location("installer",sys.argv[1]);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
real=m._migration_fingerprint
def crash(p):
    if p.parent==Path(sys.argv[5]) and p.exists():os._exit(77)
    return real(p)
m._migration_fingerprint=crash
m.migrate_legacy(*sys.argv[2:6])
'''
        result = subprocess.run([sys.executable, "-c", code, str(ROOT / "scripts/install_skill.py"), str(self.source), str(self.destination), str(self.legacy), str(self.backups)], capture_output=True, timeout=30)
        self.assertEqual(77, result.returncode, result.stderr)
        resumed = self.migrate()
        self.assertEqual(1, len(resumed["archives"]))
        self.assertTrue((Path(resumed["archives"][0]) / "SKILL.md").exists())
        self.assertFalse(installer.diagnose_installations(self.destination, self.legacy)["duplicates"])


if __name__ == "__main__": unittest.main()
