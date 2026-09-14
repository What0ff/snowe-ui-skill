"""Protect capture identity and geometry, never judge visual taste."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1] / "evals" / "visual-acceptance"


def jpeg_size(data: bytes) -> tuple[int, int]:
    """Read the SOF size in Chrome's baseline/progressive JPEG captures."""
    if data[:2] != b"\xff\xd8":
        raise ValueError("Not a JPEG capture")
    offset = 2
    while offset + 4 <= len(data):
        if data[offset] != 0xFF:
            raise ValueError("Malformed JPEG marker")
        marker = data[offset + 1]
        length = int.from_bytes(data[offset + 2:offset + 4], "big")
        if length < 2 or offset + 2 + length > len(data):
            raise ValueError("Malformed JPEG segment")
        if marker in (0xC0, 0xC2):
            height = int.from_bytes(data[offset + 5:offset + 7], "big")
            width = int.from_bytes(data[offset + 7:offset + 9], "big")
            return width, height
        offset += 2 + length
    raise ValueError("No supported JPEG size marker")


class VisualAcceptanceEvidenceTests(unittest.TestCase):
    def test_density_capture_states_and_geometry_bind_current_source(self):
        root = ROOT.parent / "density"
        manifest = json.loads((root / "captures/evidence.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["fixtureSha256"], hashlib.sha256((root / "fixture.html").read_bytes()).hexdigest())
        self.assertEqual(manifest["fontSha256"], hashlib.sha256((ROOT.parents[1] / "benchmarks/bicycle-commerce/assets/fonts/manrope-latin.woff2").read_bytes()).hexdigest())
        expected = {f"{version}-{state}-{width}.png" for version in ("before", "after") for state in ("empty", "sparse", "populated") for width in (1280, 820, 390)}
        self.assertEqual(expected, {item["file"] for item in manifest["captures"]})
        self.assertEqual(len(expected), len(manifest["captures"]))
        for capture in manifest["captures"]:
            raw = (root / "captures" / capture["file"]).read_bytes()
            self.assertEqual(b"\x89PNG\r\n\x1a\n", raw[:8])
            self.assertEqual(capture["sha256"], hashlib.sha256(raw).hexdigest())
            report = capture["report"]
            self.assertEqual(report["width"], int.from_bytes(raw[16:20], "big"))
            self.assertEqual(report["height"], int.from_bytes(raw[20:24], "big"))
            self.assertEqual(capture["file"], f"{report['version']}-{report['state']}-{report['width']}.png")

    def test_six_case_native_captures_are_current_and_complete(self):
        root = ROOT.parent / "acceptance-cases"
        manifest = json.loads((root / "captures/evidence.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["fixtureSha256"], hashlib.sha256((root / "fixture.html").read_bytes()).hexdigest())
        names = {f"{case}-{variant}-{width}.png" for case in ("coherent", "typography", "custom", "backings", "workspace", "resume") for variant in ("before", "after") for width in (900, 390)}
        self.assertEqual(names, {capture["file"] for capture in manifest["captures"]})
        self.assertEqual(len(names), len(manifest["captures"]))
        for capture in manifest["captures"]:
            image = (root / "captures" / capture["file"]).read_bytes()
            self.assertEqual(b"\x89PNG\r\n\x1a\n", image[:8])
            self.assertEqual(capture["sha256"], hashlib.sha256(image).hexdigest())
            self.assertEqual(capture["report"]["width"], int.from_bytes(image[16:20], "big"))
            self.assertEqual(844, int.from_bytes(image[20:24], "big"))
            self.assertEqual(0, capture["report"]["overflow"])

    def test_captures_bind_current_fixture_and_exact_image_bytes(self):
        self.assert_capture_set(ROOT)

    def test_correction_transfer_captures_bind_current_fixture_and_geometry(self):
        self.assert_capture_set(ROOT.parent / "correction-transfer")

    def assert_capture_set(self, root):
        manifest = json.loads((root / "captures/geometry.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["fixtureSha256"], hashlib.sha256((root / "fixture.html").read_bytes()).hexdigest())
        expected = {f"{version}-{width}.jpg" for version in "ABC" for width in (1280, 820, 390)}
        self.assertEqual(len(manifest["captures"]), len(expected))
        self.assertEqual({item["file"] for item in manifest["captures"]}, expected)
        for capture in manifest["captures"]:
            with self.subTest(capture=capture["file"]):
                image = (root / "captures" / capture["file"]).read_bytes()
                self.assertEqual(capture["sha256"], hashlib.sha256(image).hexdigest())
                width, height = jpeg_size(image)
                viewport = capture["viewport"]
                geometry = capture["geometry"]
                self.assertEqual(width, viewport["width"])
                self.assertGreaterEqual(height, viewport["height"])
                self.assertEqual(geometry["width"], viewport["width"])
                self.assertEqual(geometry["height"], viewport["height"])
                self.assertEqual(geometry["scrollWidth"], viewport["width"])
                self.assertEqual(geometry["version"], capture["file"][0])

    def test_stale_fixture_cannot_reuse_correction_transfer_proof(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            copied = Path(temporary_directory) / "proof"
            shutil.copytree(ROOT.parent / "correction-transfer", copied)
            with (copied / "fixture.html").open("a", encoding="utf-8") as source:
                source.write("\n<style>.marker { display: none }</style>\n")
            with self.assertRaises(AssertionError):
                self.assert_capture_set(copied)


if __name__ == "__main__":
    unittest.main()
