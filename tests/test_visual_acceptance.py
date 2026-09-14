"""Protect capture identity and geometry, never judge visual taste."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
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
    def test_captures_bind_current_fixture_and_exact_image_bytes(self):
        manifest = json.loads((ROOT / "captures/geometry.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["fixtureSha256"], hashlib.sha256((ROOT / "fixture.html").read_bytes()).hexdigest())
        expected = {f"{version}-{width}.jpg" for version in "ABC" for width in (1280, 820, 390)}
        self.assertEqual(len(manifest["captures"]), len(expected))
        self.assertEqual({item["file"] for item in manifest["captures"]}, expected)
        for capture in manifest["captures"]:
            with self.subTest(capture=capture["file"]):
                image = (ROOT / "captures" / capture["file"]).read_bytes()
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


if __name__ == "__main__":
    unittest.main()
