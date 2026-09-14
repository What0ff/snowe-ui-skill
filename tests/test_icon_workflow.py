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


class SvgStructuralHardeningTests(unittest.TestCase):
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

        scaled = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1" viewBox="0 0 24 24" '
            'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M4 12h16"/></svg>'
        )
        self.assert_rejected(scaled, "must match the corresponding viewBox")

        miter = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="miter"><path d="M11 23L12 1L13 23"/></svg>'
        )
        self.assert_rejected(miter, "not a supported SVG line-join", lambda value: value["drawing_language"].update({"linejoin": "miter"}))

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


if __name__ == "__main__":
    unittest.main()
