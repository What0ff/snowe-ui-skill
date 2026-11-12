from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skill" / "snowe-ui-skill" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from icon_review import ManifestError, generate_review, load_review_manifest, render_review_html  # noqa: E402
from asset_quality import validate_svg_asset  # noqa: E402


EVIDENCE = ROOT / "evals" / "icon-decisions"
MANIFEST = EVIDENCE / "manifest.json"


class SvgFixtureMixin:
    def metadata(self, source: str) -> dict:
        source_record = b"Local source record for the structural probe.\n"
        license_record = b"Local license record for the structural probe.\n"
        return {
            "name": "probe",
            "asset_type": "interface-icon",
            "role": "structural validation probe",
            "grid": 24,
            "live_area": {"min_x": 0, "min_y": 0, "max_x": 24, "max_y": 24},
            "drawing_language": {
                "mode": "stroke",
                "stroke_width": 2,
                "linecap": "round",
                "linejoin": "round",
                "corner_language": "rounded monoline probe",
                "detail_budget": "one visible path at 16 px",
            },
            "target_sizes": [16, 20, 24],
            "source": "repository-owned test probe",
            "license": "project-owned test fixture",
            "accessibility_owner": "owning labeled control; SVG decorative",
            "provenance": {
                "kind": "original",
                "creator": "test fixture author",
                "source_ref": "probe-source.md#source",
                "reviewed": "2026-08-23",
                "sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
            },
            "evidence": {
                "source": {
                    "kind": "local",
                    "path": "probe-source.md",
                    "sha256": hashlib.sha256(source_record).hexdigest(),
                    "locator": "#source",
                },
                "license": {
                    "path": "probe-license.txt",
                    "sha256": hashlib.sha256(license_record).hexdigest(),
                },
            },
        }

    def validate(self, source: str, mutate=None) -> dict:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            svg = root / "probe.svg"
            metadata = root / "probe.metadata.json"
            value = self.metadata(source)
            if mutate:
                mutate(value)
            svg.write_text(source, encoding="utf-8")
            (root / "probe-source.md").write_bytes(b"Local source record for the structural probe.\n")
            (root / "probe-license.txt").write_bytes(b"Local license record for the structural probe.\n")
            metadata.write_text(json.dumps(value), encoding="utf-8")
            return validate_svg_asset(svg, metadata)

    def assert_rejected(self, source: str, fragment: str, mutate=None) -> None:
        result = self.validate(source, mutate)
        self.assertFalse(result["valid"], result)
        self.assertIn(fragment, " ".join(result["errors"]))


class SvgStructuralHardeningTests(SvgFixtureMixin, unittest.TestCase):
    def test_rejects_nested_or_collapsed_viewports_and_miter_geometry(self):
        nested = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><svg width="1" height="1" '
            'viewBox="0 0 24 24"><path d="M4 12h16"/></svg></svg>'
        )
        self.assert_rejected(nested, "Nested <svg>")

        collapsed = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="0em" height="0em" viewBox="0 0 24 24" '
            'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M4 12h16"/></svg>'
        )
        self.assert_rejected(collapsed, "positive unitless or px")

        distorted = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="12" viewBox="0 0 24 24" '
            'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M4 12h16"/></svg>'
        )
        self.assert_rejected(distorted, "aspect ratio contradicts the viewBox")

        # Library exports declare a default render size; only the aspect ratio
        # can contradict the viewBox.
        for width, height in (("48", "48"), ("1", "1"), ("20px", "20px")):
            scaled = (
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 24 24" '
                'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
                '<path d="M4 12h16"/></svg>'
            )
            with self.subTest(width=width):
                result = self.validate(scaled)
                self.assertTrue(result["valid"], result["errors"])

        miter = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="miter"><path d="M11 23L12 1L13 23"/></svg>'
        )
        self.assert_rejected(miter, "not a supported SVG line-join", lambda value: value["drawing_language"].update({"linejoin": "miter"}))

    def test_rejects_arcs_join_that_browsers_render_as_miter(self):
        # Browsers do not implement "arcs" and fall back to miter, whose spike
        # this validator cannot bound.
        arcs = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="arcs"><path d="M2 20L12 1.5L22 20"/></svg>'
        )
        self.assert_rejected(arcs, "not a supported SVG line-join", lambda value: value["drawing_language"].update({"linejoin": "arcs"}))

    def test_square_caps_on_diagonals_count_their_corner_extent(self):
        def square(value):
            value["drawing_language"].update({"linecap": "square"})
        diagonal = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="square" stroke-linejoin="round"><path d="M1 1L23 23"/></svg>'
        )
        self.assert_rejected(diagonal, "can clip", square)
        inset = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="square" stroke-linejoin="round"><path d="M4 12H20"/></svg>'
        )
        result = self.validate(inset, square)
        self.assertTrue(result["valid"], result["errors"])

    def test_rejects_effectively_invisible_or_non_currentcolor_artwork(self):
        partial = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" opacity="0.000001">'
            '<path d="M4 12h16"/></svg>'
        )
        self.assert_rejected(partial, "apply disabled or muted opacity")

        tiny = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="0.000001" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h16"/></svg>'
        )
        self.assert_rejected(
            tiny,
            "0.5 CSS-pixel viability floor",
            lambda value: value["drawing_language"].update({"stroke_width": 0.000001}),
        )

        implicit_black = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M4 4h16v16H4z"/></svg>'
        def fill_contract(value):
            value["drawing_language"].update({"mode": "fill", "stroke_width": 0, "linecap": "not applicable", "linejoin": "not applicable"})
        self.assert_rejected(implicit_black, "visible fill other than currentColor", fill_contract)

    def test_rejects_unsubstantiated_structure_namespace_and_provenance_claims(self):
        unsupported = (
            '<svg xmlns="http://www.w3.org/2000/svg" xmlns:probe="https://example.invalid/ns" viewBox="0 0 24 24" '
            'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<path stroke-dasharray="1 1" d="M4 12h16"/></svg>'
        )
        result = self.validate(unsupported)
        errors = " ".join(result["errors"])
        self.assertIn("Prefixed namespace declarations", errors)
        self.assertIn("Unsupported attribute", errors)

        base = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h16"/></svg>'
        )
        def misleading_metadata(value):
            value["provenance"]["reviewed"] = "2999-01-01"
            value["claimed_optical_quality"] = "perfect"
        result = self.validate(base, misleading_metadata)
        errors = " ".join(result["errors"])
        self.assertIn("future review date", errors)
        self.assertIn("unsupported fields", errors)

    def test_structured_evidence_binds_exact_local_bytes_and_external_status(self):
        source = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h16"/></svg>'
        )
        self.assert_rejected(
            source,
            "evidence.source.sha256 does not match",
            lambda value: value["evidence"]["source"].update({"sha256": "0" * 64}),
        )
        self.assert_rejected(
            source,
            "evidence.license.sha256 does not match",
            lambda value: value["evidence"]["license"].update({"sha256": "0" * 64}),
        )
        self.assert_rejected(
            source,
            "metadata-relative local path without a fragment",
            lambda value: value["evidence"]["source"].update({"path": "probe-source.md#unbound"}),
        )
        self.assert_rejected(
            source,
            "metadata-relative local path without a fragment",
            lambda value: value["evidence"]["source"].update({"path": "C:probe-source.md"}),
        )
        self.assert_rejected(
            source,
            "evidence.source external binding must explicitly declare verification='unverified'",
            lambda value: value.update(
                {
                    "provenance": {
                        **value["provenance"],
                        "kind": "external",
                        "source_ref": "https://example.com/probe.svg",
                    },
                    "evidence": {
                        **value["evidence"],
                        "source": {"kind": "external", "verification": "verified"},
                    },
                }
            ),
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            svg = root / "probe.svg"
            metadata = root / "probe.metadata.json"
            svg.write_text(source, encoding="utf-8")
            (root / "probe-source.md").write_bytes(b"Local source record for the structural probe.\n")
            (root / "probe-license.txt").write_bytes(b"Local license record for the structural probe.\n")
            value = self.metadata(source)
            value["provenance"].update({"kind": "external", "source_ref": "https://example.com/probe.svg"})
            value["evidence"]["source"] = {"kind": "external", "verification": "unverified"}
            metadata.write_text(json.dumps(value), encoding="utf-8")
            result = validate_svg_asset(svg, metadata)
            self.assertTrue(result["valid"], result)

    def test_smooth_curve_bounds_include_reflected_control_points(self):
        source = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M2 12C2 12 2 12 22 12S22 13 21 13"/></svg>'
        )
        self.assert_rejected(source, "extends outside the viewBox")

    def test_rejects_malformed_rounded_rectangle_geometry(self):
        source = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<rect x="4" y="4" width="16" height="16" rx="-1"/></svg>'
        )
        self.assert_rejected(source, "rect rx must be a finite non-negative number")

    def test_arc_flags_use_exact_svg_grammar_and_extreme_radii_fail_cleanly(self):
        malformed_flag = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M2 12A8 8 0 0.0 1 22 12"/></svg>'
        )
        self.assert_rejected(malformed_flag, "exact SVG lexical forms 0 or 1")

        extreme = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M2 12A1e308 1e-308 0 0 1 22 12"/></svg>'
        )
        self.assert_rejected(extreme, "arc geometry cannot be bounded safely")

        numerically_extreme = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M2 12A1e100 1e100 0 1 1 22 12"/></svg>'
        )
        self.assert_rejected(numerically_extreme, "arc geometry cannot be bounded safely")

    def test_malformed_svg_depth_and_external_url_fail_closed(self):
        nested = "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">"
        nested += "<g>" * 80 + "<path d=\"M4 12h16\"/>" + "</g>" * 80 + "</svg>"
        result = self.validate(nested)
        self.assertFalse(result["valid"], result)
        self.assertIn("nesting exceeds", " ".join(result["errors"]))

        malformed_url = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h16"/></svg>'
        )
        for source_ref in (
            "https://[",
            "https://exa mple.com/icon.svg",
            "https://example.com:bad/icon.svg",
            "https://example.com:/icon.svg",
            "https://example.com/%ZZ",
            "https://user:password@example.com/icon.svg",
            "https://example.com./icon.svg",
        ):
            result = self.validate(
                malformed_url,
                lambda value, source_ref=source_ref: value["provenance"].update(
                    {"kind": "external", "source_ref": source_ref}
                ),
            )
            self.assertFalse(result["valid"], result)
            self.assertIn("canonical HTTPS", " ".join(result["errors"]))

    def test_metadata_json_depth_and_unicode_scalars_fail_closed(self):
        source = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h16"/></svg>'
        )
        nested = 0
        for _ in range(256):
            nested = [nested]
        result = self.validate(source, lambda value: value.update({"nested": nested}))
        self.assertFalse(result["valid"], result)
        self.assertIn("JSON nesting limit", " ".join(result["errors"]))

        result = self.validate(source, lambda value: value.update({"name": "\ud800"}))
        self.assertFalse(result["valid"], result)
        self.assertIn("unpaired Unicode surrogate", " ".join(result["errors"]))

    def test_json_integer_limits_and_numeric_overflow_fail_as_structured_asset_errors(self):
        source = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h16"/></svg>'
        )
        for digits, message in ((4300, "represented safely"), (4301, "parsed safely")):
            with self.subTest(digits=digits):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory)
                    svg = root / "probe.svg"
                    metadata = root / "probe.metadata.json"
                    svg.write_text(source, encoding="utf-8")
                    (root / "probe-source.md").write_bytes(b"Local source record for the structural probe.\n")
                    (root / "probe-license.txt").write_bytes(b"Local license record for the structural probe.\n")
                    metadata_text = json.dumps(self.metadata(source)).replace(
                        "[16, 20, 24]", f"[{('9' * digits)}]"
                    )
                    metadata.write_text(metadata_text, encoding="utf-8")
                    result = validate_svg_asset(svg, metadata)
                self.assertFalse(result["valid"], result)
                self.assertIn(message, " ".join(result["errors"]))

    def test_validator_rejects_uninspectable_evidence_paths_as_structured_errors(self):
        source = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h16"/></svg>'
        )
        result = self.validate(
            source,
            lambda value: value["evidence"]["license"].update({"path": "x" * 100_000}),
        )
        self.assertFalse(result["valid"], result)
        self.assertIn("cannot be inspected safely", " ".join(result["errors"]))

    def test_direct_validator_rejects_redirected_asset_paths(self):
        source = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h16"/></svg>'
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            outside = root / "outside"
            outside.mkdir()
            (outside / "probe.svg").write_text(source, encoding="utf-8")
            (outside / "probe.metadata.json").write_text(
                json.dumps(self.metadata(source)), encoding="utf-8"
            )
            (outside / "probe-source.md").write_bytes(b"Local source record for the structural probe.\n")
            (outside / "probe-license.txt").write_bytes(b"Local license record for the structural probe.\n")
            redirect = root / "redirect"
            is_junction = False
            try:
                redirect.symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError):
                if os.name != "nt":
                    self.skipTest("directory redirects are unavailable on this platform")
                created = subprocess.run(
                    ["cmd", "/c", "mklink", "/J", str(redirect), str(outside)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if created.returncode != 0:
                    self.skipTest(f"directory redirect creation unavailable: {created.stderr or created.stdout}")
                is_junction = True
            try:
                result = validate_svg_asset(
                    redirect / "probe.svg", redirect / "probe.metadata.json"
                )
                self.assertFalse(result["valid"], result)
                self.assertIn("reparse", " ".join(result["errors"]))
            finally:
                if redirect.exists() or redirect.is_symlink():
                    if is_junction:
                        os.rmdir(redirect)
                else:
                    redirect.unlink()

    def test_structured_local_evidence_rejects_directory_redirects(self):
        source = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h16"/></svg>'
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            records = root / "records"
            records.mkdir()
            source_record = b"Local source record for the structural probe.\n"
            license_record = b"Local license record for the structural probe.\n"
            (records / "probe-source.md").write_bytes(source_record)
            (records / "probe-license.txt").write_bytes(license_record)
            redirect = root / "redirect"
            is_junction = False
            try:
                redirect.symlink_to(records, target_is_directory=True)
            except (OSError, NotImplementedError):
                if os.name != "nt":
                    self.skipTest("directory redirects are unavailable on this platform")
                created = subprocess.run(
                    ["cmd", "/c", "mklink", "/J", str(redirect), str(records)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if created.returncode != 0:
                    self.skipTest(f"evidence redirect creation unavailable: {created.stderr or created.stdout}")
                is_junction = True
            try:
                svg = root / "probe.svg"
                metadata = root / "probe.metadata.json"
                value = self.metadata(source)
                value["evidence"]["source"]["path"] = "redirect/probe-source.md"
                value["evidence"]["license"]["path"] = "redirect/probe-license.txt"
                svg.write_text(source, encoding="utf-8")
                metadata.write_text(json.dumps(value), encoding="utf-8")
                result = validate_svg_asset(svg, metadata)
                self.assertFalse(result["valid"], result)
                self.assertIn("reparse", " ".join(result["errors"]))
            finally:
                if redirect.exists() or redirect.is_symlink():
                    if is_junction:
                        os.rmdir(redirect)
                    else:
                        redirect.unlink()

    def test_public_metadata_example_matches_the_validator_schema(self):
        reference = (ROOT / "skill" / "snowe-ui-skill" / "references" / "cli-reference.md").read_text(encoding="utf-8")
        match = re.search(r"Required metadata fields:\s*```json\s*(\{.*?\})\s*```", reference, re.DOTALL)
        self.assertIsNotNone(match, "CLI reference must contain a parseable metadata example")
        metadata = json.loads(match.group(1))
        source = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M3 15h18M6 15l2-6h8l2 6"/></svg>'
        )
        metadata["provenance"]["sha256"] = hashlib.sha256(source.encode("utf-8")).hexdigest()
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            svg = root / "cargo-rack.svg"
            companion = root / "cargo-rack.metadata.json"
            source_record = b"Public metadata example source record.\n"
            license_record = b"Public metadata example license record.\n"
            metadata["evidence"]["source"] = {
                "kind": "local",
                "path": "source-record.md",
                "sha256": hashlib.sha256(source_record).hexdigest(),
                "locator": "#source",
            }
            metadata["evidence"]["license"] = {
                "path": "license-record.txt",
                "sha256": hashlib.sha256(license_record).hexdigest(),
            }
            (root / "source-record.md").write_bytes(source_record)
            (root / "license-record.txt").write_bytes(license_record)
            svg.write_text(source, encoding="utf-8")
            companion.write_text(json.dumps(metadata), encoding="utf-8")
            result = validate_svg_asset(svg, companion)
        self.assertTrue(result["valid"], result)


SVG_OPEN = '<svg xmlns="http://www.w3.org/2000/svg"'
HEROICONS_SOLID_CHECK_CIRCLE = (
    SVG_OPEN + ' viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" data-slot="icon">'
    '<path fill-rule="evenodd" d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 '
    '17.385 2.25 12Zm13.36-1.814a.75.75 0 1 0-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 0 0-1.06 1.06l2.25 2.25a.75.75 '
    '0 0 0 1.14-.094l3.75-5.25Z" clip-rule="evenodd"/></svg>'
)
PHOSPHOR_HEART_SECONDARY = (
    'd="M232,102c0,66-104,122-104,122S24,168,24,102A54,54,0,0,1,78,48c22.59,0,41.94,12.31,50,32,'
    '8.06-19.69,27.41-32,50-32A54,54,0,0,1,232,102Z"'
)
PHOSPHOR_HEART_PRIMARY = (
    'd="M178,40c-20.65,0-38.73,8.88-50,23.89C116.73,48.88,98.65,40,78,40a62.07,62.07,0,0,0-62,62c0,70,103.79,'
    '126.66,108.21,129a8,8,0,0,0,7.58,0C136.21,228.66,240,172,240,102A62.07,62.07,0,0,0,178,40ZM128,214.8C109.74,'
    '204.16,32,155.69,32,102A46.06,46.06,0,0,1,78,56c19.45,0,35.78,10.36,42.6,27a8,8,0,0,0,14.8,0c6.82-16.67,23.15-27,'
    '42.6-27a46.06,46.06,0,0,1,46,46C224,155.61,146.24,204.15,128,214.8Z"'
)
PHOSPHOR_DUOTONE_HEART = (
    SVG_OPEN + ' viewBox="0 0 256 256" fill="currentColor"><rect width="256" height="256" fill="none"/>'
    f'<path data-icon-layer="secondary" {PHOSPHOR_HEART_SECONDARY} opacity="0.2"/>'
    f'<path data-icon-layer="primary" {PHOSPHOR_HEART_PRIMARY}/></svg>'
)
PHOSPHOR_FILL_HEART = (
    SVG_OPEN + ' viewBox="0 0 256 256" fill="currentColor"><rect width="256" height="256" fill="none"/>'
    '<path d="M240,102c0,70-103.79,126.66-108.21,129a8,8,0,0,1-7.58,0C119.79,228.66,16,172,16,102A62.07,62.07,0,0,1,'
    '78,40c20.65,0,38.73,8.88,50,23.89C139.27,48.88,157.35,40,178,40A62.07,62.07,0,0,1,240,102Z"/></svg>'
)
TABLER_FILLED_HEART = (
    SVG_OPEN + ' width="24" height="24" viewBox="0 0 24 24" fill="currentColor" '
    'class="icon icon-tabler icons-tabler-filled icon-tabler-heart">'
    '<path stroke="none" d="M0 0h24v24H0z" fill="none"/>'
    '<path d="M6.979 3.074a6 6 0 0 1 4.988 1.425l.037 .033l.034 -.03a6 6 0 0 1 4.733 -1.44l.246 .036a6 6 0 0 1 3.364 '
    '10.008l-.18 .185l-.048 .041l-7.45 7.379a1 1 0 0 1 -1.313 .082l-.094 -.082l-7.493 -7.422a6 6 0 0 1 3.176 -10.215z" />'
    '</svg>'
)
MATERIAL_SYMBOLS_FAVORITE = (
    SVG_OPEN + ' height="24px" viewBox="0 -960 960 960" width="24px" fill="currentColor">'
    '<path d="m480-120-58-52q-101-91-167-157T150-447.5Q111-500 95.5-544T80-634q0-94 63-157t157-63q52 0 99 22t81 62q34-40 '
    '81-62t99-22q94 0 157 63t63 157q0 46-15.5 90T810-447.5Q771-395 705-329T538-172l-58 52Z"/></svg>'
)
# Bootstrap's heart-fill curve, nudged inside the grid: its Bezier control
# points reach -7.5..23.5, while the drawn curve stays within 0..16.
BOOTSTRAP_LIKE_HEART_FILL = (
    SVG_OPEN + ' width="16" height="16" fill="currentColor" class="bi bi-heart-fill" viewBox="0 0 16 16">'
    '<path fill-rule="evenodd" d="M8 1.324C12.438-3.238 23.534 4.745 8 15.01-7.534 4.746 3.562-3.238 8 1.324"/></svg>'
)


def fill_language(value: dict) -> None:
    value["drawing_language"].update(
        {"mode": "fill", "stroke_width": 0, "linecap": "not applicable", "linejoin": "not applicable"}
    )


def duotone_language(value: dict, tone: float = 0.2) -> None:
    value["drawing_language"].update(
        {
            "mode": "duotone",
            "stroke_width": 0,
            "linecap": "not applicable",
            "linejoin": "not applicable",
            "tones": {"secondary_opacity": tone},
        }
    )


def grid_language(grid, live_area=None, sizes=None):
    def mutate(value: dict) -> None:
        value["grid"] = grid
        value["live_area"] = live_area or {"min_x": 0, "min_y": 0, "max_x": grid, "max_y": grid}
        if sizes is not None:
            value["target_sizes"] = sizes
    return mutate


def chain(*mutations):
    def mutate(value: dict) -> None:
        for mutation in mutations:
            mutation(value)
    return mutate


class SolidAndDuotoneValidatorTests(SvgFixtureMixin, unittest.TestCase):
    """Library-shaped solid and duotone output under the interface-icon profile."""

    def assert_valid(self, source: str, mutate=None) -> dict:
        result = self.validate(source, mutate)
        self.assertTrue(result["valid"], result["errors"])
        return result

    def test_heroicons_solid_with_evenodd_and_inert_markup_passes(self):
        result = self.assert_valid(HEROICONS_SOLID_CHECK_CIRCLE, fill_language)
        self.assertFalse([warning for warning in result["warnings"] if "winding" in warning])

    def test_phosphor_duotone_with_declared_tone_passes(self):
        result = self.assert_valid(PHOSPHOR_DUOTONE_HEART, chain(grid_language(256), duotone_language))
        self.assertFalse([warning for warning in result["warnings"] if "winding" in warning], result["warnings"])

    def test_phosphor_fill_with_spacer_rect_passes(self):
        self.assert_valid(PHOSPHOR_FILL_HEART, chain(grid_language(256), fill_language))

    def test_tabler_filled_with_class_and_spacer_path_passes(self):
        self.assert_valid(TABLER_FILLED_HEART, fill_language)

    def test_material_symbols_viewbox_origin_and_relative_live_area_pass(self):
        live_area = {"min_x": 40, "min_y": 40, "max_x": 920, "max_y": 920}
        self.assert_valid(MATERIAL_SYMBOLS_FAVORITE, chain(grid_language(960, live_area, [20, 24]), fill_language))
        # live_area is relative to the viewBox origin, so geometry outside the
        # declared offset still fails.
        tight = {"min_x": 40, "min_y": 200, "max_x": 920, "max_y": 920}
        self.assert_rejected(
            MATERIAL_SYMBOLS_FAVORITE,
            "contradicts metadata live_area",
            chain(grid_language(960, tight, [20, 24]), fill_language),
        )

    def test_rounded_solid_uses_exact_curve_extents_near_the_edge(self):
        self.assert_valid(BOOTSTRAP_LIKE_HEART_FILL, chain(grid_language(16, sizes=[16]), fill_language))

    def test_compact_svgo_arc_flags_parse_like_spaced_flags(self):
        for path in ("M4 15a8 8 0 0116 0", "M4 15a8 8 0 0 1 16 0", "M4 15A8 8 0 0120 15"):
            source = (
                SVG_OPEN + ' viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
                f'stroke-linecap="round" stroke-linejoin="round"><path d="{path}"/></svg>'
            )
            with self.subTest(path=path):
                self.assert_valid(source)
        clipped = (
            SVG_OPEN + ' viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            'stroke-linecap="round" stroke-linejoin="round"><path d="M0.5 15a11.5 11.5 0 0123 0"/></svg>'
        )
        self.assert_rejected(clipped, "extends outside the viewBox")

    def test_inert_presentation_attributes_pass_with_fixed_values(self):
        source = (
            SVG_OPEN + ' viewBox="0 0 24 24" role="img" focusable="false" aria-hidden="true" class="icon icon--close" '
            'data-slot="icon" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            'stroke-linejoin="round" shape-rendering="geometricPrecision">'
            '<path pathLength="1" vector-effect="non-scaling-stroke" fill-rule="nonzero" clip-rule="evenodd" '
            'd="M6 6l12 12M18 6L6 18"/></svg>'
        )
        self.assert_valid(source)

    def test_inert_attributes_reject_values_that_change_meaning(self):
        base = (
            SVG_OPEN + ' viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            'stroke-linecap="round" stroke-linejoin="round"{root}><path{child} d="M6 6l12 12"/></svg>'
        )
        for root, child, fragment in (
            ("", ' role="img"', "Unsupported attribute"),
            (' role="presentation"', "", "role"),
            (' aria-hidden="false"', "", "aria-hidden"),
            (' focusable="true"', "", "focusable"),
            (' shape-rendering="crispEdges"', "", "shape-rendering"),
            ("", ' vector-effect="non-scaling-size"', "vector-effect"),
            ("", ' fill-rule="inherit-ish"', "fill-rule"),
            (' class="icon{color:red}"', "", "class"),
            (' data-slot="two words"', "", "data-slot"),
            ("", ' pathLength="-1"', "pathLength"),
            ("", ' id="shape"', "id is not allowed"),
            ("", ' data-icon-layer="primary"', "duotone"),
        ):
            with self.subTest(root=root, child=child):
                self.assert_rejected(base.format(root=root, child=child), fragment)

    def test_non_scaling_strokes_are_bounded_at_the_smallest_target(self):
        # At 12 px a 2-unit non-scaling stroke spans 2 CSS px, i.e. 4 grid units.
        source = (
            SVG_OPEN + ' viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            'stroke-linecap="round" stroke-linejoin="round"><path vector-effect="non-scaling-stroke" d="M1.5 12h21"/></svg>'
        )
        self.assert_valid(source.replace('vector-effect="non-scaling-stroke" ', ""))
        self.assert_rejected(source, "can clip", lambda value: value.update({"target_sizes": [12, 24]}))

    def test_duotone_layer_and_tone_failures(self):
        language = chain(grid_language(256), duotone_language)
        undeclared = PHOSPHOR_DUOTONE_HEART.replace('opacity="0.2"', 'opacity="0.3"')
        self.assert_rejected(undeclared, "declared tones.secondary_opacity", language)

        secondary_only = (
            SVG_OPEN + ' viewBox="0 0 256 256" fill="currentColor">'
            f'<path data-icon-layer="secondary" {PHOSPHOR_HEART_SECONDARY} opacity="0.2"/></svg>'
        )
        self.assert_rejected(secondary_only, "without a primary layer", language)

        bad_layer = PHOSPHOR_DUOTONE_HEART.replace('data-icon-layer="primary"', 'data-icon-layer="tertiary"')
        self.assert_rejected(bad_layer, "data-icon-layer", language)

        unlayered = PHOSPHOR_DUOTONE_HEART.replace(' data-icon-layer="primary"', "")
        self.assert_rejected(unlayered, "must resolve to data-icon-layer", language)

        clipped = PHOSPHOR_DUOTONE_HEART.replace('data-icon-layer="primary"', 'data-icon-layer="primary" clip-path="url(#c)"')
        self.assert_rejected(clipped, "clip-path", language)
        masked = PHOSPHOR_DUOTONE_HEART.replace("</svg>", '<mask><rect width="256" height="256"/></mask></svg>')
        self.assert_rejected(masked, "<mask>", language)

        root_opacity = PHOSPHOR_DUOTONE_HEART.replace('fill="currentColor">', 'fill="currentColor" opacity="0.5">', 1)
        self.assert_rejected(root_opacity, "must be 1 outside the duotone secondary layer", language)

        colored = PHOSPHOR_DUOTONE_HEART.replace('opacity="0.2"', 'opacity="0.2" fill="#000000"')
        self.assert_rejected(colored, "currentColor", language)

        out_of_range = PHOSPHOR_DUOTONE_HEART.replace('opacity="0.2"', 'opacity="0.8"')
        self.assert_rejected(
            out_of_range,
            "secondary_opacity must be a finite number from 0.12 to 0.6",
            chain(grid_language(256), lambda value: duotone_language(value, 0.8)),
        )

        stacked = PHOSPHOR_DUOTONE_HEART.replace('opacity="0.2"', 'opacity="0.2" fill-opacity="0.2"')
        self.assert_rejected(stacked, "renders at alpha", language)

        full_alpha_secondary = PHOSPHOR_DUOTONE_HEART.replace(' opacity="0.2"', "")
        self.assert_rejected(full_alpha_secondary, "renders at alpha", language)

        conflicting = (
            SVG_OPEN + ' viewBox="0 0 256 256" fill="currentColor"><g data-icon-layer="secondary" opacity="0.2">'
            f'<path data-icon-layer="primary" {PHOSPHOR_HEART_PRIMARY}/></g></svg>'
        )
        self.assert_rejected(conflicting, "cannot change inside", language)

        on_root = PHOSPHOR_DUOTONE_HEART.replace('fill="currentColor">', 'fill="currentColor" data-icon-layer="primary">', 1)
        self.assert_rejected(on_root, "data-icon-layer", language)

    def test_duotone_metadata_requires_declared_tones_and_keeps_other_modes_strict(self):
        def without_tones(value):
            duotone_language(value)
            del value["drawing_language"]["tones"]
        self.assert_rejected(PHOSPHOR_DUOTONE_HEART, "tones", chain(grid_language(256), without_tones))

        def undeclared_key(value):
            duotone_language(value)
            value["drawing_language"]["tones"]["primary_opacity"] = 1
        self.assert_rejected(PHOSPHOR_DUOTONE_HEART, "tones", chain(grid_language(256), undeclared_key))

        for tone in (True, "0.2", 0.05):
            with self.subTest(tone=tone):
                self.assert_rejected(
                    PHOSPHOR_DUOTONE_HEART,
                    "secondary_opacity",
                    chain(grid_language(256), lambda value, tone=tone: duotone_language(value, tone)),
                )

        def tones_on_fill(value):
            fill_language(value)
            value["drawing_language"]["tones"] = {"secondary_opacity": 0.2}
        self.assert_rejected(PHOSPHOR_FILL_HEART, "applies only to duotone", chain(grid_language(256), tones_on_fill))

        # Muted SVG-level opacity remains rejected outside duotone mode.
        muted_fill = PHOSPHOR_FILL_HEART.replace("<path ", '<path opacity="0.2" ')
        self.assert_rejected(muted_fill, "apply disabled or muted opacity", chain(grid_language(256), fill_language))

    def test_duotone_may_combine_fill_and_stroke_with_declared_stroke_language(self):
        source = (
            SVG_OPEN + ' viewBox="0 0 24 24">'
            '<rect data-icon-layer="secondary" x="4" y="4" width="16" height="16" rx="3" fill="currentColor" opacity="0.25"/>'
            '<path data-icon-layer="primary" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            'stroke-linejoin="round" d="M8 12l3 3 5-6"/></svg>'
        )

        def stroked(value):
            duotone_language(value, 0.25)
            value["drawing_language"].update({"stroke_width": 2, "linecap": "round", "linejoin": "round"})
        self.assert_valid(source, stroked)
        self.assert_rejected(source, "stroke", lambda value: duotone_language(value, 0.25))

        def stroke_without_strokes(value):
            stroked(value)
        filled_only = source.replace(
            'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M8 12l3 3 5-6"',
            'fill="currentColor" d="M8 11h8v2H8z"',
        )
        self.assert_rejected(filled_only, "draws no stroke", stroke_without_strokes)

    def test_unpainted_rect_that_does_not_cover_the_viewbox_still_fails(self):
        source = PHOSPHOR_FILL_HEART.replace('<rect width="256" height="256" fill="none"/>', '<rect width="200" height="256" fill="none"/>')
        self.assert_rejected(source, "has no visible fill or stroke", chain(grid_language(256), fill_language))

    def test_same_winding_inner_subpath_warns_but_does_not_fail(self):
        def winding_warnings(source):
            result = self.validate(source, fill_language)
            self.assertTrue(result["valid"], result["errors"])
            return [warning for warning in result["warnings"] if "winding" in warning]

        same = SVG_OPEN + ' viewBox="0 0 24 24" fill="currentColor"><path d="M4 4h16v16H4zM8 8h8v8H8z"/></svg>'
        self.assertEqual(1, len(winding_warnings(same)))
        reversed_hole = SVG_OPEN + ' viewBox="0 0 24 24" fill="currentColor"><path d="M4 4h16v16H4zM8 8v8h8V8z"/></svg>'
        self.assertEqual([], winding_warnings(reversed_hole))
        evenodd = same.replace("<path ", '<path fill-rule="evenodd" ')
        self.assertEqual([], winding_warnings(evenodd))
        island_in_hole = (
            SVG_OPEN + ' viewBox="0 0 24 24" fill="currentColor">'
            '<path d="M2 2h20v20H2zM5 5v14h14V5zM10 10h4v4h-4z"/></svg>'
        )
        self.assertEqual([], winding_warnings(island_in_hole))

    def test_fill_details_below_one_css_pixel_warn_at_the_smallest_target(self):
        source = (
            SVG_OPEN + ' viewBox="0 0 24 24" fill="currentColor"><path fill-rule="evenodd" '
            'd="M4 4h16v16H4zM11.6 11.6h0.8v0.8h-0.8z"/></svg>'
        )
        result = self.validate(source, fill_language)
        self.assertTrue(result["valid"], result["errors"])
        self.assertTrue(any("below 1 CSS px" in warning for warning in result["warnings"]), result["warnings"])
        result = self.validate(source, chain(fill_language, lambda value: value.update({"target_sizes": [48]})))
        self.assertFalse(any("below 1 CSS px" in warning for warning in result["warnings"]), result["warnings"])

    def test_project_owned_license_binding_applies_only_to_original_artwork(self):
        source = (
            SVG_OPEN + ' viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            'stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h16"/></svg>'
        )
        project_owned = lambda value: value["evidence"].update({"license": {"kind": "project-owned"}})
        self.assert_valid(source, project_owned)

        def external(value):
            project_owned(value)
            value["provenance"].update({"kind": "external", "source_ref": "https://example.com/probe.svg"})
            value["evidence"]["source"] = {"kind": "external", "verification": "unverified"}
        self.assert_rejected(source, "project-owned", external)
        self.assert_rejected(
            source,
            "evidence.license",
            lambda value: value["evidence"].update({"license": {"kind": "project-owned", "path": "probe-license.txt"}}),
        )
        self.assert_rejected(
            source,
            "evidence.license",
            lambda value: value["evidence"].update({"license": {"kind": "borrowed"}}),
        )


class MetadataErgonomicsTests(unittest.TestCase):
    STROKE_SVG = (
        SVG_OPEN + ' viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h16"/></svg>'
    )

    def run_cli(self, *arguments: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "asset_quality.py"), *arguments],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

    def fill_placeholders(self, value: dict) -> None:
        value.update(
            {
                "role": "close action icon",
                "source": "repository-owned custom drawing",
                "license": "project-owned",
                "accessibility_owner": "owning labeled button; SVG decorative",
                "target_sizes": [16, 20, 24],
            }
        )
        value["drawing_language"].update(
            {"corner_language": "rounded monoline terminals", "detail_budget": "one horizontal stroke at 16 px"}
        )
        value["provenance"].update({"creator": "test fixture author", "source_ref": "icon.source.md#icon", "reviewed": "2026-08-23"})
        value["evidence"]["source"]["path"] = "icon.source.md"

    def test_init_metadata_and_rehash_round_trip(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            svg = root / "icon.svg"
            svg.write_text(self.STROKE_SVG, encoding="utf-8")
            metadata = root / "icon.metadata.json"

            created = self.run_cli(str(svg), "--init-metadata")
            self.assertEqual(0, created.returncode, created.stderr)
            self.assertIn("icon.metadata.json", created.stdout)
            value = json.loads(metadata.read_text(encoding="utf-8"))
            self.assertEqual("icon", value["name"])
            self.assertEqual(hashlib.sha256(svg.read_bytes()).hexdigest(), value["provenance"]["sha256"])
            self.assertEqual(
                {"mode": "stroke", "stroke_width": 2, "linecap": "round", "linejoin": "round"},
                {key: value["drawing_language"][key] for key in ("mode", "stroke_width", "linecap", "linejoin")},
            )
            self.assertEqual({"kind": "project-owned"}, value["evidence"]["license"])

            # Placeholders still fail until a person fills them.
            unfilled = validate_svg_asset(svg, metadata)
            self.assertFalse(unfilled["valid"])
            self.assertIn("non-placeholder", " ".join(unfilled["errors"]))

            refused = self.run_cli(str(svg), "--init-metadata")
            self.assertNotEqual(0, refused.returncode)
            self.assertIn("already exists", refused.stderr + refused.stdout)

            self.fill_placeholders(value)
            metadata.write_text(json.dumps(value, indent=2), encoding="utf-8")
            (root / "icon.source.md").write_bytes(b"# icon\nDrawn for the test fixture.\n")

            rehashed = self.run_cli(str(svg), "--metadata", str(metadata), "--rehash")
            self.assertEqual(0, rehashed.returncode, rehashed.stdout + rehashed.stderr)
            self.assertIn("evidence.source.sha256", rehashed.stdout)
            self.assertIn("PASS", rehashed.stdout)

            svg.write_text(self.STROKE_SVG.replace("M4 12h16", "M5 12h14"), encoding="utf-8")
            stale = validate_svg_asset(svg, metadata)
            self.assertIn("provenance.sha256 does not match", " ".join(stale["errors"]))
            rehashed = self.run_cli(str(svg), "--metadata", str(metadata), "--rehash", "--json")
            self.assertEqual(0, rehashed.returncode, rehashed.stdout + rehashed.stderr)
            report = json.loads(rehashed.stdout)
            self.assertTrue(report["valid"], report)
            self.assertEqual(["provenance.sha256"], [change["field"] for change in report["rehash"]["changed"]])
            self.assertEqual(
                hashlib.sha256(svg.read_bytes()).hexdigest(),
                json.loads(metadata.read_text(encoding="utf-8"))["provenance"]["sha256"],
            )

    def test_rehash_never_rebinds_external_or_brand_artwork(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            svg = root / "icon.svg"
            svg.write_text(self.STROKE_SVG, encoding="utf-8")
            created = self.run_cli(str(svg), "--init-metadata", "--provenance", "external")
            self.assertEqual(0, created.returncode, created.stderr)
            metadata = root / "icon.metadata.json"
            value = json.loads(metadata.read_text(encoding="utf-8"))
            self.assertEqual({"kind": "external", "verification": "unverified"}, value["evidence"]["source"])
            self.assertIn("path", value["evidence"]["license"])
            original_digest = value["provenance"]["sha256"]

            svg.write_text(self.STROKE_SVG.replace("M4 12h16", "M5 12h14"), encoding="utf-8")
            rehashed = self.run_cli(str(svg), "--metadata", str(metadata), "--rehash")
            self.assertNotEqual(0, rehashed.returncode)
            self.assertIn("external", rehashed.stdout)
            self.assertEqual(original_digest, json.loads(metadata.read_text(encoding="utf-8"))["provenance"]["sha256"])

    def test_rehash_refuses_unsafe_evidence_paths_without_writing(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            svg = root / "icon.svg"
            svg.write_text(self.STROKE_SVG, encoding="utf-8")
            self.assertEqual(0, self.run_cli(str(svg), "--init-metadata").returncode)
            metadata = root / "icon.metadata.json"
            value = json.loads(metadata.read_text(encoding="utf-8"))
            self.fill_placeholders(value)
            value["evidence"]["source"]["path"] = "C:/outside.md"
            before = json.dumps(value, indent=2)
            metadata.write_text(before, encoding="utf-8")
            rehashed = self.run_cli(str(svg), "--metadata", str(metadata), "--rehash")
            self.assertNotEqual(0, rehashed.returncode)
            self.assertEqual(before, metadata.read_text(encoding="utf-8"))

    def test_validation_still_requires_metadata(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            svg = Path(temporary_directory) / "icon.svg"
            svg.write_text(self.STROKE_SVG, encoding="utf-8")
            result = self.run_cli(str(svg))
            self.assertNotEqual(0, result.returncode)
            self.assertIn("--metadata", result.stderr)


class IconDecisionWorkflowTests(unittest.TestCase):
    def test_multilingual_stress_sheet_matches_validated_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "stress.html"
            generate_review(EVIDENCE / "stress.json", output)
            self.assertEqual((EVIDENCE / "stress.html").read_bytes(), output.read_bytes())

    def test_context_language_v11_and_legacy_default(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            value = self.compact_manifest()
            legacy = load_review_manifest(self.write_manifest(root, value))
            self.assertEqual("en", legacy["contexts"][0]["lang"])
            self.assertEqual("ltr", legacy["contexts"][0]["dir"])
            value["schema_version"] = "1.1"
            for lang, direction, label in [("ru", "ltr", "Закрыть"), ("de", "ltr", "Produktinformationen schließen"), ("ar", "rtl", "إغلاق ABC-123")]:
                value["contexts"][0].update(lang=lang, dir=direction, label=label)
                loaded = load_review_manifest(self.write_manifest(root, value))
                rendered = render_review_html(loaded)
                self.assertIn(f'lang="{lang}" dir="{direction}"', rendered)
                self.assertIn(label, rendered)

    def test_context_language_v11_rejects_missing_or_invalid_declaration(self):
        with tempfile.TemporaryDirectory() as temporary:
            value = self.compact_manifest()
            value["schema_version"] = "1.1"
            for declaration in [{}, {"lang": "en\" onclick=", "dir": "ltr"}, {"lang": "ru", "dir": "sideways"}]:
                value["contexts"][0].pop("lang", None)
                value["contexts"][0].pop("dir", None)
                value["contexts"][0].update(declaration)
                with self.assertRaises(ManifestError):
                    load_review_manifest(self.write_manifest(Path(temporary), value))

    def checked_manifest(self) -> dict:
        return json.loads(MANIFEST.read_text(encoding="utf-8"))

    def portable_checked_manifest(self) -> dict:
        manifest = self.checked_manifest()
        for context in manifest["contexts"]:
            evidence = context["context_evidence"]
            evidence["source"] = str((EVIDENCE / evidence["source"]).resolve())
            for candidate in context["candidates"]:
                for field in ("asset", "metadata"):
                    if candidate.get(field):
                        candidate[field] = str((EVIDENCE / candidate[field]).resolve())
        return manifest

    def write_manifest(self, root: Path, value: dict) -> Path:
        path = root / "manifest.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def compact_manifest(self) -> dict:
        return {
            "schema_version": "1.0",
            "title": "Probe",
            "contexts": [
                {
                    "id": "probe",
                    "role": "Close a probe",
                    "component": "icon-button",
                    "label": "Close",
                    "sizes": [16, 20, 24],
                    "states": ["default", "focus"],
                    "selected": "lucide-x",
                    "verdict": "KEEP",
                    "decision_evidence": "The selected learned symbol is clearer in this representative control.",
                    "context_evidence": {
                        "basis": "representative",
                        "source": "Compact dialog convention",
                        "selector": "semantic icon button",
                        "viewport": "16, 20, and 24 px targets",
                    },
                    "candidates": [
                        {
                            "id": "lucide-x",
                            "name": "Lucide X",
                            "kind": "existing",
                            "asset": str(EVIDENCE / "assets" / "lucide-x.svg"),
                            "asset_sha256": "4a9cdab38fbb96162e7dace28e33f4ca0e49d8963a6162abc3d4691b7d675117",
                            "metadata": str(EVIDENCE / "assets" / "lucide-x.metadata.json"),
                            "source": "Lucide X SVG at pinned upstream revision",
                            "license": "Lucide ISC / Feather-derived icons MIT; see ../LUCIDE_LICENSE.txt",
                            "rationale": "Learned close metaphor.",
                        },
                        {
                            "id": "custom-orbit-close",
                            "name": "Orbit close",
                            "kind": "custom",
                            "asset": str(EVIDENCE / "assets" / "custom-orbit-close.svg"),
                            "asset_sha256": "6d234a50eae15f70e60826fc53191f899e2d31964852ee93a89aed525a67428a",
                            "metadata": str(EVIDENCE / "assets" / "custom-orbit-close.metadata.json"),
                            "source": "repository-owned custom challenger drawn for rejection proof",
                            "license": "project-owned repository evaluation asset",
                            "rationale": "A deliberately weaker challenger.",
                        },
                    ],
                }
            ],
        }

    def assert_manifest_rejected(self, value: dict, message: str) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = self.write_manifest(Path(temporary_directory), value)
            with self.assertRaisesRegex(ManifestError, message):
                load_review_manifest(path)

    def test_checked_manifest_is_bound_to_sources_and_regenerates_exactly(self):
        manifest = load_review_manifest(MANIFEST)
        self.assertEqual(3, len(manifest["contexts"]))
        self.assertEqual(
            {"existing", "custom", "none"},
            {candidate["kind"] for context in manifest["contexts"] for candidate in context["candidates"]},
        )
        self.assertEqual(
            {"repository-derived"},
            {context["context_evidence"]["basis"] for context in manifest["contexts"]},
        )
        generated = render_review_html(manifest)
        self.assertEqual(generated, (EVIDENCE / "comparison.html").read_text(encoding="utf-8"))
        self.assertNotIn("<script", generated.casefold())
        self.assertNotIn("url(http", generated.casefold())
        self.assertIn("declared-provenance byte-binding", generated)
        self.assertIn("source and license truth still require current primary-source verification", generated)
        self.assertNotIn("provenance checks", generated)

    def test_no_icon_alternatives_render_once_and_visible_text_is_truthful(self):
        generated = render_review_html(load_review_manifest(MANIFEST))
        close_card = generated.split('data-candidate="close-text"', 1)[1].split("</article>", 1)[0]
        self.assertEqual(1, close_card.count('<div class="size-label">No icon</div>'))
        self.assertIn(">Close</span></button>", close_card)
        self.assertNotIn("sr-only", close_card)

    def test_manifest_rejects_unbound_sizes_digests_names_kinds_and_verdicts(self):
        too_large = self.compact_manifest()
        too_large["contexts"][0]["sizes"] = [16, 20, 24, 64]
        self.assert_manifest_rejected(too_large, "omits context target sizes")

        duplicate = self.compact_manifest()
        duplicate["contexts"][0]["candidates"][1]["asset"] = duplicate["contexts"][0]["candidates"][0]["asset"]
        duplicate["contexts"][0]["candidates"][1]["asset_sha256"] = duplicate["contexts"][0]["candidates"][0]["asset_sha256"]
        duplicate["contexts"][0]["candidates"][1]["metadata"] = duplicate["contexts"][0]["candidates"][0]["metadata"]
        self.assert_manifest_rejected(duplicate, "identical SVG bytes")

        wrong_name = self.compact_manifest()
        wrong_name["contexts"][0]["candidates"][1]["id"] = "unbound-name"
        self.assert_manifest_rejected(wrong_name, "must exactly match metadata name")

        external_custom = self.compact_manifest()
        external_custom["contexts"][0]["candidates"] = [
            copy.deepcopy(external_custom["contexts"][0]["candidates"][0]),
            {
                "id": "no-icon",
                "name": "No icon",
                "kind": "none",
                "source": "Visible text",
                "license": "Not applicable",
                "rationale": "Text can carry the role.",
            },
        ]
        external_custom["contexts"][0]["candidates"][0]["kind"] = "custom"
        self.assert_manifest_rejected(external_custom, "custom candidates require original provenance")

        rejected_with_selection = self.compact_manifest()
        rejected_with_selection["contexts"][0]["verdict"] = "REJECT"
        self.assert_manifest_rejected(rejected_with_selection, "selected must be null")

        forged_source = self.compact_manifest()
        forged_source["contexts"][0]["candidates"][0]["source"] = "Unbound source claim"
        self.assert_manifest_rejected(forged_source, "source must exactly match validated metadata")

    def test_manifest_asset_paths_refuse_symlinks_and_junctions(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            redirect = root / "assets"
            is_junction = False
            try:
                redirect.symlink_to(EVIDENCE / "assets", target_is_directory=True)
            except (OSError, NotImplementedError):
                if os.name != "nt":
                    self.skipTest("directory symlinks are unavailable on this platform")
                created = subprocess.run(
                    ["cmd", "/c", "mklink", "/J", str(redirect), str(EVIDENCE / "assets")],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if created.returncode != 0:
                    self.skipTest(f"asset redirect creation unavailable: {created.stderr or created.stdout}")
                is_junction = True
            try:
                value = self.compact_manifest()
                candidate = value["contexts"][0]["candidates"][0]
                candidate["asset"] = str(redirect / "lucide-x.svg")
                candidate["metadata"] = str(redirect / "lucide-x.metadata.json")
                self.assert_manifest_rejected(value, "symlink, junction, or reparse point")
            finally:
                if redirect.exists() or redirect.is_symlink():
                    if is_junction:
                        os.rmdir(redirect)
                    else:
                        redirect.unlink()

    def test_icon_review_cli_help_and_representative_generation_smoke(self):
        help_result = subprocess.run(
            [sys.executable, str(SCRIPTS / "icon_review.py"), "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(0, help_result.returncode, help_result.stderr)
        self.assertIn("representative-control", help_result.stdout)

        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "comparison.html"
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "icon_review.py"), str(MANIFEST), "--output", str(output), "--json"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            summary = json.loads(result.stdout)
            self.assertEqual({"contexts": 3, "candidates": 8}, {key: summary[key] for key in ("contexts", "candidates")})
            self.assertEqual((EVIDENCE / "comparison.html").read_bytes(), output.read_bytes())

    def test_generation_does_not_overwrite_an_external_hardlink_target(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            outside = root / "outside.html"
            outside.write_bytes(b"external sentinel")
            output = root / "comparison.html"
            try:
                output.hardlink_to(outside)
            except OSError as error:
                self.skipTest(f"hardlinks are unavailable: {error}")

            generate_review(MANIFEST, output)

            self.assertEqual(b"external sentinel", outside.read_bytes())
            self.assertFalse(os.path.samefile(outside, output))
            self.assertIn("representative controls", output.read_text(encoding="utf-8"))

    def test_manifest_malformed_types_are_rejected_as_manifest_errors(self):
        for field, value, message in (
            ("component", [], "component must be one of"),
            ("states", [{}], "states must use only"),
            ("verdict", {}, "verdict must be KEEP"),
        ):
            malformed = self.compact_manifest()
            malformed["contexts"][0][field] = value
            self.assert_manifest_rejected(malformed, message)
        malformed = self.compact_manifest()
        malformed["contexts"][0]["candidates"][0]["kind"] = {}
        self.assert_manifest_rejected(malformed, "kind must be existing")

    def test_dark_host_state_requires_an_exact_surface_binding(self):
        manifest = self.portable_checked_manifest()
        proof = manifest["contexts"][1]["host_proof"]
        del proof["dark_surface_selector"]
        self.assert_manifest_rejected(manifest, "dark_surface_selector must be a non-empty string")

        manifest = self.portable_checked_manifest()
        proof = manifest["contexts"][1]["host_proof"]
        del proof["expected_dark_background"]
        self.assert_manifest_rejected(manifest, "expected_dark_background must be a non-empty string")

    def test_manifest_requires_one_exercised_host_state_for_each_comparison_state(self):
        manifest = self.portable_checked_manifest()
        proof = manifest["contexts"][0]["host_proof"]
        del proof["state_map"]["hover"]
        self.assert_manifest_rejected(manifest, "state_map must map every comparison state exactly once")

        manifest = self.portable_checked_manifest()
        proof = manifest["contexts"][0]["host_proof"]
        proof["state_map"]["high-contrast"] = "dark"
        self.assert_manifest_rejected(manifest, "state_map values must exactly match exercised host states")

        manifest = self.portable_checked_manifest()
        proof = manifest["contexts"][0]["host_proof"]
        proof["states"].remove("hover")
        self.assert_manifest_rejected(manifest, "state_map values must exactly match exercised host states")

    def test_repository_derived_reject_or_unknown_contexts_cannot_claim_host_proof(self):
        manifest = self.portable_checked_manifest()
        context = manifest["contexts"][0]
        context["verdict"] = "REJECT"
        context["selected"] = None
        self.assert_manifest_rejected(manifest, "repository-derived host proof requires a selected candidate")

    def test_dialog_selection_binds_to_the_actual_owner_selector(self):
        manifest = load_review_manifest(MANIFEST)
        context = manifest["contexts"][0]
        proof = context["_host_proof"]
        self.assertEqual("lucide-x", context["selected"])
        self.assertEqual("icon-owner", proof["strategy"])
        self.assertEqual(".sheet-close-icon", proof["icon_selector"])
        source = (ROOT / "benchmarks" / "bicycle-commerce" / "index.html").read_text(encoding="utf-8")
        self.assertIn('<span class="sheet-close-icon" aria-hidden="true"></span>', source)

    def test_manifest_rejects_deep_or_surrogate_json_scalars(self):
        manifest = self.compact_manifest()
        nested = 0
        for _ in range(256):
            nested = [nested]
        manifest["nested_probe"] = nested
        self.assert_manifest_rejected(manifest, "JSON nesting limit")

        manifest = self.compact_manifest()
        manifest["title"] = "\ud800"
        self.assert_manifest_rejected(manifest, "unpaired Unicode surrogate")

    def test_manifest_rejects_unsafe_host_routes_and_asset_digest_mutation(self):
        for route in ("//evil.example/icon", "/../evil"):
            manifest = self.portable_checked_manifest()
            manifest["contexts"][0]["host_proof"]["route"] = route
            self.assert_manifest_rejected(manifest, "canonical local served route")

        manifest = self.portable_checked_manifest()
        manifest["contexts"][0]["candidates"][0]["asset_sha256"] = "0" * 64
        self.assert_manifest_rejected(manifest, "asset_sha256 does not match")

    def test_manifest_rejects_integer_limits_and_uninspectable_paths(self):
        manifest = self.compact_manifest()
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "manifest.json"
            raw = json.dumps(manifest).replace("[16, 20, 24]", f"[{('9' * 4300)}]")
            path.write_text(raw, encoding="utf-8")
            with self.assertRaisesRegex(ManifestError, "positive finite numbers"):
                load_review_manifest(path)

            raw = json.dumps(manifest)[:-1] + f', "numeric_probe": {("9" * 4301)}' + "}"
            path.write_text(raw, encoding="utf-8")
            with self.assertRaisesRegex(ManifestError, "parsed safely"):
                load_review_manifest(path)

        manifest = self.portable_checked_manifest()
        manifest["contexts"][0]["candidates"][0]["asset"] = "x" * 100_000
        self.assert_manifest_rejected(manifest, "cannot be inspected safely")

    def test_manifest_rejects_swapped_comparison_to_host_state_bindings(self):
        manifest = self.portable_checked_manifest()
        state_map = manifest["contexts"][1]["host_proof"]["state_map"]
        state_map["default"], state_map["dark"] = state_map["dark"], state_map["default"]
        self.assert_manifest_rejected(manifest, "canonical comparison-to-host state bindings")

    def test_selected_no_icon_label_is_bound_to_the_owning_control(self):
        manifest = self.portable_checked_manifest()
        candidate = manifest["contexts"][2]["candidates"][1]
        candidate["visible_label"] = "Verified"
        self.assert_manifest_rejected(manifest, "visible_label must exactly match")

        manifest = self.portable_checked_manifest()
        del manifest["contexts"][2]["candidates"][1]["visible_label"]
        self.assert_manifest_rejected(manifest, "visible_label must be a non-empty string")

    def test_manifest_path_reparse_is_rejected_before_resolution(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            redirect = root / "manifest-redirect"
            is_junction = False
            try:
                redirect.symlink_to(EVIDENCE, target_is_directory=True)
            except (OSError, NotImplementedError):
                if os.name != "nt":
                    self.skipTest("directory redirects are unavailable on this platform")
                created = subprocess.run(
                    ["cmd", "/c", "mklink", "/J", str(redirect), str(EVIDENCE)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if created.returncode != 0:
                    self.skipTest(f"manifest redirect creation unavailable: {created.stderr or created.stdout}")
                is_junction = True
            try:
                with self.assertRaisesRegex(ManifestError, "Manifest path.*symlink, junction, or reparse point"):
                    load_review_manifest(redirect / "manifest.json")
            finally:
                if redirect.exists() or redirect.is_symlink():
                    if is_junction:
                        os.rmdir(redirect)
                    else:
                        redirect.unlink()

    def test_generation_rejects_output_aliasing_manifest(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            manifest_path = self.write_manifest(root, self.compact_manifest())
            before = manifest_path.read_bytes()
            with self.assertRaisesRegex(ManifestError, "Output path must not alias manifest"):
                generate_review(manifest_path, manifest_path)
            self.assertEqual(before, manifest_path.read_bytes())

    def test_selected_host_state_requires_a_declared_selection_attribute(self):
        def with_selected_state(manifest: dict) -> dict:
            context = manifest["contexts"][0]
            context["states"].append("selected")
            context["host_proof"]["states"].append("selected")
            context["host_proof"]["state_map"]["selected"] = "selected"
            return manifest

        manifest = with_selected_state(self.portable_checked_manifest())
        self.assert_manifest_rejected(manifest, "selected_attribute")

        manifest = with_selected_state(self.portable_checked_manifest())
        manifest["contexts"][0]["host_proof"]["selected_attribute"] = "aria-checked"
        self.assert_manifest_rejected(manifest, "selected_attribute")

        manifest = self.portable_checked_manifest()
        manifest["contexts"][0]["host_proof"]["selected_attribute"] = "aria-pressed"
        self.assert_manifest_rejected(manifest, "selected_attribute requires")

        for attribute in ("aria-pressed", "aria-current", "aria-selected"):
            manifest = with_selected_state(self.portable_checked_manifest())
            manifest["contexts"][0]["host_proof"]["selected_attribute"] = attribute
            with tempfile.TemporaryDirectory() as temporary_directory, self.subTest(attribute=attribute):
                loaded = load_review_manifest(self.write_manifest(Path(temporary_directory), manifest))
                self.assertIn("selected", loaded["contexts"][0]["_host_proof"]["states"])


FAVORITE_OUTLINE = (
    SVG_OPEN + ' viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
    'stroke-linejoin="round"><path d="M12 20s-7-4.5-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.5-7 10-7 10z"/></svg>'
)
FAVORITE_SOLID = (
    SVG_OPEN + ' viewBox="0 0 24 24" fill="currentColor">'
    '<path d="M12 21s-8-5-8-11a5 5 0 0 1 8-4 5 5 0 0 1 8 4c0 6-8 11-8 11z"/></svg>'
)


class StyleComparisonTests(unittest.TestCase):
    """Outline/solid comparisons and per-state assets in the review sheet."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.outline = self.write_asset("heart-outline", FAVORITE_OUTLINE, "stroke")
        self.solid = self.write_asset("heart-solid", FAVORITE_SOLID, "fill")

    def write_asset(self, name: str, source: str, mode: str) -> dict:
        svg = self.root / f"{name}.svg"
        svg.write_text(source, encoding="utf-8")
        record = self.root / f"{name}.source.md"
        record.write_bytes(f"# {name}\nDrawn for the style comparison fixture.\n".encode("utf-8"))
        if mode == "stroke":
            language = {"mode": "stroke", "stroke_width": 2, "linecap": "round", "linejoin": "round"}
        else:
            language = {"mode": "fill", "stroke_width": 0, "linecap": "not applicable", "linejoin": "not applicable"}
        language.update({"corner_language": "rounded heart lobes", "detail_budget": "one silhouette at 16 px"})
        digest = hashlib.sha256(svg.read_bytes()).hexdigest()
        value = {
            "name": name,
            "asset_type": "interface-icon",
            "role": "favorite toggle icon",
            "grid": 24,
            "live_area": {"min_x": 0, "min_y": 0, "max_x": 24, "max_y": 24},
            "drawing_language": language,
            "target_sizes": [16, 20, 24],
            "source": "repository-owned favorite drawings",
            "license": "project-owned",
            "accessibility_owner": "owning toggle button; SVG decorative",
            "provenance": {
                "kind": "original",
                "creator": "test fixture author",
                "source_ref": f"{record.name}#{name}",
                "reviewed": "2026-08-23",
                "sha256": digest,
            },
            "evidence": {
                "source": {"kind": "local", "path": record.name, "sha256": hashlib.sha256(record.read_bytes()).hexdigest()},
                "license": {"kind": "project-owned"},
            },
        }
        (self.root / f"{name}.metadata.json").write_text(json.dumps(value), encoding="utf-8")
        return {"asset": svg.name, "asset_sha256": digest, "metadata": f"{name}.metadata.json"}

    def candidate(self, candidate_id: str, name: str, binding: dict, **extra) -> dict:
        return {
            "id": candidate_id,
            "name": name,
            "kind": "custom",
            **binding,
            "source": "repository-owned favorite drawings",
            "license": "project-owned",
            "rationale": f"{name} in the same toggle.",
            **extra,
        }

    def manifest(self) -> dict:
        return {
            "schema_version": "1.2",
            "title": "Favorite style probe",
            "contexts": [
                {
                    "id": "favorite-toggle",
                    "role": "Toggle a saved item",
                    "component": "icon-button",
                    "label": "Save",
                    "lang": "en",
                    "dir": "ltr",
                    "symbol_role": "interface-icon",
                    "comparison_axis": "style",
                    "sizes": [16, 20, 24],
                    "states": ["default", "selected"],
                    "selected": "heart-outline-selected-solid",
                    "verdict": "KEEP",
                    "decision_evidence": "The solid selected state reads as saved without making every row heavy.",
                    "context_evidence": {
                        "basis": "representative",
                        "source": "Saved-item toggle convention",
                        "selector": "favorite toggle button",
                        "viewport": "16, 20, and 24 px targets",
                    },
                    "candidates": [
                        self.candidate("heart-outline", "Outline heart", self.outline),
                        self.candidate("heart-solid", "Solid heart", self.solid),
                        self.candidate(
                            "heart-outline-selected-solid",
                            "Outline, solid when selected",
                            self.outline,
                            state_assets={"selected": self.solid},
                        ),
                    ],
                }
            ],
        }

    def load(self, value: dict) -> dict:
        path = self.root / "manifest.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return load_review_manifest(path)

    def assert_rejected(self, value: dict, message: str) -> None:
        with self.assertRaisesRegex(ManifestError, message):
            self.load(value)

    def test_style_comparison_renders_outline_by_default_and_solid_when_selected(self):
        rendered = render_review_html(self.load(self.manifest()))
        card = rendered.split('data-candidate="heart-outline-selected-solid"', 1)[1].split("</article>", 1)[0]
        cells = card.split('<div class="state-cell state-cell--')[1:]
        self.assertEqual(6, len(cells))
        for cell in cells:
            if cell.startswith("selected"):
                self.assertIn("M12 21s-8-5", cell)
                self.assertIn('aria-pressed="true"', cell)
            else:
                self.assertIn("M12 20s-7-4.5", cell)
        self.assertIn("State assets", card)
        self.assertIn(self.solid["asset_sha256"], card)
        self.assertIn("drawing style", rendered)
        outline_card = rendered.split('data-candidate="heart-outline"', 1)[1].split("</article>", 1)[0]
        self.assertNotIn("M12 21s-8-5", outline_card)
        self.assertNotIn("State assets", outline_card)

    def test_same_kind_candidates_still_need_the_explicit_style_axis(self):
        value = self.manifest()
        del value["contexts"][0]["comparison_axis"]
        self.assert_rejected(value, "materially different candidate kinds")
        value = self.manifest()
        value["contexts"][0]["comparison_axis"] = "palette"
        self.assert_rejected(value, "comparison_axis")
        value = self.manifest()
        value["schema_version"] = "1.1"
        for field in ("symbol_role",):
            del value["contexts"][0][field]
        self.assert_rejected(value, "schema 1.2")

    def test_style_comparison_requires_materially_different_drawing_styles(self):
        twin = self.write_asset("heart-outline-alt", FAVORITE_OUTLINE.replace("M12 20s", "M12 19.5s"), "stroke")
        value = self.manifest()
        value["contexts"][0]["candidates"] = [
            self.candidate("heart-outline", "Outline heart", self.outline),
            self.candidate("heart-outline-alt", "Alternative outline heart", twin),
        ]
        value["contexts"][0]["selected"] = "heart-outline"
        self.assert_rejected(value, "same drawing style")

        value = self.manifest()
        value["contexts"][0]["candidates"] = [
            self.candidate("heart-outline", "Outline heart", self.outline),
            {
                "id": "save-text",
                "name": "Visible Save text",
                "kind": "none",
                "source": "Visible text",
                "license": "Not applicable",
                "rationale": "Text can carry the role.",
            },
        ]
        value["contexts"][0]["selected"] = "heart-outline"
        self.assert_rejected(value, "at least two SVG candidates")

    def test_state_assets_are_bound_like_default_assets(self):
        value = self.manifest()
        value["contexts"][0]["candidates"][2]["state_assets"] = {"hover": self.solid}
        self.assert_rejected(value, "state_assets keys")

        value = self.manifest()
        value["contexts"][0]["candidates"][2]["state_assets"] = {"default": self.solid}
        self.assert_rejected(value, "state_assets keys")

        value = self.manifest()
        value["contexts"][0]["candidates"][2]["state_assets"]["selected"] = {**self.solid, "asset_sha256": "0" * 64}
        self.assert_rejected(value, "asset_sha256 does not match")

        value = self.manifest()
        value["contexts"][0]["candidates"][2]["state_assets"]["selected"] = {**self.solid, "extra": True}
        self.assert_rejected(value, "exactly asset, asset_sha256, and metadata")

        value = self.manifest()
        value["contexts"][0]["candidates"][2]["state_assets"] = {"selected": self.outline}
        self.assert_rejected(value, "repeats")

        value = self.manifest()
        value["contexts"][0]["candidates"].append(
            {
                "id": "save-text",
                "name": "Visible Save text",
                "kind": "none",
                "source": "Visible text",
                "license": "Not applicable",
                "rationale": "Text can carry the role.",
                "state_assets": {"selected": self.solid},
            }
        )
        self.assert_rejected(value, "no-icon candidate")

        value = self.manifest()
        stateful = value["contexts"][0]["candidates"].pop()
        stateful["id"] = "heart-solid"
        value["contexts"][0]["candidates"] = [value["contexts"][0]["candidates"][0], stateful]
        value["contexts"][0]["selected"] = "heart-solid"
        self.assert_rejected(value, "must not borrow")

        value = self.manifest()
        value["contexts"][0]["candidates"].append(
            self.candidate("heart-outline-selected-solid-copy", "Copy", self.outline, state_assets={"selected": self.solid})
        )
        self.assert_rejected(value, "identical SVG bytes in every state")

    def test_style_comparison_writes_a_deterministic_sheet(self):
        path = self.root / "manifest.json"
        path.write_text(json.dumps(self.manifest()), encoding="utf-8")
        first, second = self.root / "first.html", self.root / "second.html"
        generate_review(path, first)
        generate_review(path, second)
        self.assertEqual(first.read_bytes(), second.read_bytes())


if __name__ == "__main__":
    unittest.main()
