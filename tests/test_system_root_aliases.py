"""OS-owned root aliases (macOS /tmp, /var, /etc into /private) are not caller redirects.

macOS keeps the default temporary directory below /var, a root symlink to /private/var.
Every other symlink, junction or reparse point in a path stays refused.
"""
from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = ROOT / "skill" / "snowe-ui-skill" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

import asset_quality  # noqa: E402
import decision_packet  # noqa: E402
import icon_review  # noqa: E402

INSTALLER_SPEC = importlib.util.spec_from_file_location("snowe_alias_installer", ROOT / "scripts" / "install_skill.py")
installer = importlib.util.module_from_spec(INSTALLER_SPEC)
INSTALLER_SPEC.loader.exec_module(installer)

ANCHOR = Path(os.path.abspath(os.sep))
ALIAS = ANCHOR / "var"
NESTED = ANCHOR / "home" / "var"
TARGET = ALIAS / "folders" / "ab" / "T" / "probe.svg"
NESTED_TARGET = NESTED / "probe.svg"
REAL_REALPATH = os.path.realpath


def rejected(module, path: Path) -> bool:
    """Whether a module's redirect-chain check refuses the path."""
    if module is asset_quality:
        return asset_quality._reparse_in_chain(path) is not None
    error = icon_review.ManifestError if module is icon_review else ValueError
    try:
        module._reject_reparse_chain(path, "Probe")
    except error:
        return True
    return False


class SystemRootAliasTests(unittest.TestCase):
    modules = (asset_quality, icon_review, decision_packet, installer)

    def simulate(self, stack: ExitStack, module, *, platform: str, links: set[Path], alias_target: str) -> None:
        def realpath(path, *args, **kwargs):
            return alias_target if Path(path) == ALIAS else REAL_REALPATH(path, *args, **kwargs)

        stack.enter_context(patch.object(module, "_is_reparse_path", side_effect=lambda path: Path(path) in links))
        stack.enter_context(patch.object(sys, "platform", platform))
        stack.enter_context(patch.object(os.path, "realpath", side_effect=realpath))

    def test_macos_root_alias_is_accepted(self):
        for module in self.modules:
            with self.subTest(module=module.__name__), ExitStack() as stack:
                self.simulate(stack, module, platform="darwin", links={ALIAS}, alias_target="/private/var")
                self.assertFalse(rejected(module, TARGET))

    def test_same_link_is_refused_on_other_platforms(self):
        for module in self.modules:
            with self.subTest(module=module.__name__), ExitStack() as stack:
                self.simulate(stack, module, platform="linux", links={ALIAS}, alias_target="/private/var")
                self.assertTrue(rejected(module, TARGET))

    def test_root_link_with_another_target_is_refused(self):
        for module in self.modules:
            with self.subTest(module=module.__name__), ExitStack() as stack:
                self.simulate(stack, module, platform="darwin", links={ALIAS}, alias_target="/Volumes/elsewhere")
                self.assertTrue(rejected(module, TARGET))

    def test_same_name_below_the_root_is_refused(self):
        for module in self.modules:
            with self.subTest(module=module.__name__), ExitStack() as stack:
                self.simulate(stack, module, platform="darwin", links={NESTED}, alias_target="/private/var")
                self.assertTrue(rejected(module, NESTED_TARGET))

    def test_redirect_below_an_accepted_alias_is_refused(self):
        redirect = ALIAS / "folders" / "ab"
        for module in self.modules:
            with self.subTest(module=module.__name__), ExitStack() as stack:
                self.simulate(stack, module, platform="darwin", links={ALIAS, redirect}, alias_target="/private/var")
                self.assertTrue(rejected(module, TARGET))


if __name__ == "__main__":
    unittest.main()
