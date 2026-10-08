"""Role-specific asset integrity and declared geometry; neither certifies taste."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

from tests.evidence_factory import binding, make_review, write
from tests import test_icon_workflow as existing_icon_tests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skill/snowe-ui-skill/scripts"))
from asset_quality import validate_svg_asset, _path_bounds
from icon_review import ManifestError, load_review_manifest
from visual_system import inspect_system


class BrandAssetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="#0560ff" d="M4 4h16v16H4z"/></svg>'
        self.metadata = existing_icon_tests.SvgStructuralHardeningTests().metadata(self.source)
        self.metadata.update(asset_type="brand-mark", brand={
            "schema": "1.0", "identity": "Fictional external service",
            "variant": "Unmodified supplied blue symbol",
            "artwork": {"path": "upstream.svg", "sha256": hashlib.sha256(self.source.encode()).hexdigest()},
            "usage": {"path": "usage.txt", "sha256": hashlib.sha256(b"Fixture usage terms, not a real trademark grant.").hexdigest()},
        })
        self.metadata["drawing_language"].update(mode="fill", stroke_width=0, linecap="not applicable", linejoin="not applicable")
        self.metadata["provenance"].update(kind="external", source_ref="https://example.org/official/mark.svg")
        self.metadata["evidence"]["source"] = {"kind": "external", "verification": "unverified"}
        (self.root / "upstream.svg").write_text(self.source, encoding="utf-8")
        (self.root / "usage.txt").write_bytes(b"Fixture usage terms, not a real trademark grant.")
        (self.root / "probe-license.txt").write_bytes(b"Local license record for the structural probe.\n")

    def check(self, source=None):
        (self.root / "probe.svg").write_text(source or self.source, encoding="utf-8")
        write(self.root, "probe.metadata.json", self.metadata)
        return validate_svg_asset(self.root / "probe.svg", self.root / "probe.metadata.json")

    def test_brand_color_is_preserved_but_not_certified_as_official(self):
        result = self.check()
        self.assertTrue(result["valid"], result)
        self.assertIn("unverified", " ".join(result["warnings"]).lower())
        self.assertEqual(self.source, (self.root / "probe.svg").read_text(encoding="utf-8"))

    def test_interface_profile_still_rejects_brand_colors(self):
        self.metadata.pop("brand")
        self.metadata["asset_type"] = "interface-icon"
        result = self.check()
        self.assertFalse(result["valid"])
        self.assertIn("currentColor", " ".join(result["errors"]))

    def test_imported_curve_extrema_differ_from_the_control_hull(self):
        curve = "M2 12C2 -4 22 -4 22 12"
        self.assertEqual((2.0, -4.0, 22.0, 12.0), _path_bounds(curve)[0])
        bounds, error = _path_bounds(curve, exact_curves=True)
        self.assertIsNone(error)
        self.assertEqual((2.0, 0.0, 22.0, 12.0), bounds)
        self.assertLess(_path_bounds("M2 12C2 -8 22 -8 22 12", exact_curves=True)[0][1], 0)
        quadratic = _path_bounds("M2 12Q12 -12 22 12", exact_curves=True)[0]
        self.assertEqual((2.0, 0.0, 22.0, 12.0), quadratic)

    def test_exact_curve_bounds_include_smooth_relative_and_real_clipping(self):
        for curve in ("M2 12c0 -16 20 -16 20 0s-20 16-20 0", "M2 12q10 -24 20 0t-20 0"):
            bounds, error = _path_bounds(curve, exact_curves=True)
            self.assertIsNone(error)
            self.assertAlmostEqual(0, bounds[1])
            self.assertAlmostEqual(24, bounds[3])
        changed = self.source.replace("M4 4h16v16H4z", "M4 -1h16v21H4z")
        digest = hashlib.sha256(changed.encode()).hexdigest()
        self.metadata["provenance"]["sha256"] = digest
        self.metadata["brand"]["artwork"]["sha256"] = digest
        (self.root / "upstream.svg").write_text(changed, encoding="utf-8")
        self.assertIn("outside the viewBox", " ".join(self.check(changed)["errors"]))

    def test_checked_declarations_regenerate_with_portable_exact_bytes(self):
        fixture = ROOT / "evals/identity-alignment"
        generated = self.root / "regenerated"
        shutil.copytree(fixture / "assets", generated / "assets")
        shutil.copytree(fixture / "upstream", generated / "upstream")
        shutil.copyfile(fixture / "SOURCES.md", generated / "SOURCES.md")
        spec = importlib.util.spec_from_file_location("identity_contracts", fixture / "build_contracts.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.ROOT = generated
        module.build()
        for name in ("PLAN.json", "SYSTEM.json", "manifest.json", "assets/span.metadata.json", "assets/span-before.metadata.json", "assets/bluesky-black.metadata.json"):
            with self.subTest(name=name):
                self.assertEqual((fixture / name).read_bytes(), (generated / name).read_bytes())

    def test_real_official_artwork_preserves_bytes_and_passes_the_import_profile(self):
        path = ROOT / "evals/identity-alignment/assets/bluesky-black.svg"
        before = path.read_bytes()
        result = validate_svg_asset(path, path.with_suffix(".metadata.json"))
        self.assertTrue(result["valid"], result)
        self.assertEqual(before, path.read_bytes())

    def test_brand_requires_external_origin_and_bound_usage(self):
        for mutate in (
            lambda m: m["provenance"].update(kind="original"),
            lambda m: m.pop("brand"),
            lambda m: m["brand"].update(schema="2.0"),
            lambda m: m["brand"]["usage"].update(sha256="0" * 64),
            lambda m: m["brand"].update(identity=""),
        ):
            original = deepcopy(self.metadata)
            with self.subTest(mutate=mutate):
                mutate(self.metadata)
                self.assertFalse(self.check()["valid"])
            self.metadata = original

    def test_brand_bindings_respect_resource_and_regular_file_boundaries(self):
        (self.root / "usage.txt").write_bytes(b"x" * 1_000_001)
        self.assertIn("evidence budget", " ".join(self.check()["errors"]))
        self.metadata["brand"]["artwork"]["path"] = "https://example.org/mark.svg"
        self.assertIn("metadata-relative", " ".join(self.check()["errors"]))

    def test_recolor_or_redraw_cannot_rebind_only_the_delivery_digest(self):
        for changed in (self.source.replace("#0560ff", "#ff0000"), self.source.replace("h16", "h12")):
            with self.subTest(changed=changed):
                self.metadata["provenance"]["sha256"] = hashlib.sha256(changed.encode()).hexdigest()
                result = self.check(changed)
                self.assertFalse(result["valid"])
                self.assertIn("artwork", " ".join(result["errors"]))

    def test_brand_profile_does_not_admit_active_or_dependent_content(self):
        for changed in (
            self.source.replace("<path", '<script>alert(1)</script><path'),
            self.source.replace('fill="#0560ff"', 'fill="url(https://example.org/paint)"'),
            self.source.replace("<path", '<image href="https://example.org/a.png"/><path'),
        ):
            with self.subTest(changed=changed):
                digest = hashlib.sha256(changed.encode()).hexdigest()
                self.metadata["provenance"]["sha256"] = digest
                self.metadata["brand"]["artwork"]["sha256"] = digest
                (self.root / "upstream.svg").write_text(changed, encoding="utf-8")
                self.assertFalse(self.check(changed)["valid"])

    def test_brand_context_cannot_offer_a_custom_substitute(self):
        manifest = json.loads((ROOT / "evals/icon-decisions/manifest.json").read_text(encoding="utf-8"))
        manifest["schema_version"] = "1.2"
        context = manifest["contexts"][0]
        manifest["contexts"] = [context]
        context.update(symbol_role="brand-mark", brand_identity="Fictional external service", lang="en", dir="ltr")
        context["context_evidence"].update(basis="representative")
        context.pop("host_proof")
        # Keep valid paths to establish that the semantic boundary, not a missing file, fails.
        for candidate in context["candidates"]:
            for key in ("asset", "metadata"):
                if key in candidate:
                    candidate[key] = str((ROOT / "evals/icon-decisions" / candidate[key]).resolve())
        write(self.root, "manifest.json", manifest)
        with self.assertRaisesRegex(ManifestError, "brand.*custom|custom.*brand"):
            load_review_manifest(self.root / "manifest.json")

    def manifest(self):
        self.check()
        return {"schema_version": "1.2", "title": "Imported identity proof", "contexts": [{
            "id": "brand", "role": "Identify an external service", "symbol_role": "brand-mark",
            "brand_identity": self.metadata["brand"]["identity"], "lang": "en", "dir": "ltr",
            "component": "labeled-button", "label": "External service", "sizes": [16, 20, 24],
            "states": ["default"], "selected": "probe", "verdict": "KEEP",
            "decision_evidence": "Fixture only; source authority is not certified",
            "context_evidence": {"basis": "representative", "source": "Fictional test", "selector": "button", "viewport": "900x700"},
            "candidates": [{"id": "probe", "name": "Supplied mark", "kind": "existing", "asset": "probe.svg",
                            "asset_sha256": self.metadata["provenance"]["sha256"], "metadata": "probe.metadata.json",
                            "source": self.metadata["source"], "license": self.metadata["license"],
                            "rationale": "Preserve supplied artwork"}],
        }]}

    def test_imported_brand_does_not_require_a_manufactured_challenger(self):
        manifest = self.manifest()
        write(self.root, "manifest.json", manifest)
        loaded = load_review_manifest(self.root / "manifest.json")
        self.assertEqual(1, len(loaded["contexts"][0]["candidates"]))
        for mutate in (
            lambda c: c.update(brand_identity="Another service"),
            lambda c: (c.update(symbol_role="interface-icon"), c.pop("brand_identity")),
        ):
            changed = deepcopy(manifest)
            mutate(changed["contexts"][0])
            write(self.root, "manifest.json", changed)
            with self.assertRaises(ManifestError): load_review_manifest(self.root / "manifest.json")

    def test_visible_text_is_a_valid_missing_brand_asset_fallback(self):
        manifest = self.manifest()
        context = manifest["contexts"][0]
        context["selected"] = "text"
        context["candidates"] = [{"id": "text", "name": "Service name", "kind": "none", "visible_label": "External service",
                                  "source": "Visible wording", "license": "No artwork", "rationale": "Source asset unavailable"}]
        write(self.root, "manifest.json", manifest)
        self.assertEqual("none", load_review_manifest(self.root / "manifest.json")["contexts"][0]["candidates"][0]["kind"])


class AlignmentRelationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "page.css").write_text("main{}")
        make_review(self.root)
        self.system = json.loads((self.root / "visual-system.json").read_text())
        self.system["schema"] = "1.1"
        self.plan = json.loads((self.root / "plan.json").read_text())
        self.receipt = json.loads((self.root / "receipt.json").read_text())
        self.receipt["observations"][0]["probes"] = [
            {"selector": "input", "pseudo": "", "matches": [{"bounds": {"x": 0, "y": 30, "width": 250, "height": 40}}]},
            {"selector": ".actions button", "pseudo": "", "matches": [
                {"bounds": {"x": 270, "y": 30, "width": 100, "height": 40}},
                {"bounds": {"x": 390, "y": 34, "width": 130, "height": 32}},
            ]},
        ]
        self.check = {"id": "control-axis", "case": "main", "selector": ".actions button", "pseudo": "", "property": "bounds.centerY",
                      "sameAs": {"selector": "input", "pseudo": ""}, "tolerance": {"cssPixels": 0.25, "reason": "Fixture control centers share one axis; allow subpixel layout rounding"}}
        self.system["relations"] = [{"id": "toolbar", "members": ["page"], "intent": "Align visible controls independently of the field label", "checks": [self.check]}]

    def inspect(self):
        write(self.root, "visual-system.json", self.system)
        return inspect_system(self.root, binding(self.root, "visual-system.json"), self.plan, self.receipt)

    def test_different_heights_and_horizontal_positions_can_share_an_axis(self):
        self.assertEqual([], self.inspect()["issues"])

    def test_upward_drift_in_any_sibling_is_detected(self):
        self.receipt["observations"][0]["probes"][1]["matches"][1]["bounds"]["y"] -= 8
        self.assertIn("control-axis", " ".join(self.inspect()["issues"]))

    def test_bottom_alignment_and_justified_subpixel_tolerance(self):
        self.check["property"] = "bounds.bottom"
        bounds = self.receipt["observations"][0]["probes"][1]["matches"][1]["bounds"]
        bounds["y"] = 38.2
        self.assertEqual([], self.inspect()["issues"])
        bounds["y"] = 38.5
        self.assertTrue(self.inspect()["issues"])

    def test_invalid_geometry_or_ambiguous_anchor_cannot_be_excepted_away(self):
        self.system["exceptions"] = [{"check": "control-axis", "reason": "Approved staggered composition", "revisit": "Changed composition"}]
        for change in (
            lambda: self.receipt["observations"][0]["probes"][0].update(matches=[]),
            lambda: self.receipt["observations"][0]["probes"][0]["matches"].append(deepcopy(self.receipt["observations"][0]["probes"][0]["matches"][0])),
            lambda: self.receipt["observations"][0]["probes"][1]["matches"][0]["bounds"].update(height=-1),
            lambda: self.check["tolerance"].update(cssPixels=True),
            lambda: self.check["tolerance"].update(cssPixels=-1),
            lambda: self.check["tolerance"].update(reason=""),
            lambda: self.check.update(pseudo="::before"),
        ):
            original_receipt, original_check = deepcopy(self.receipt), deepcopy(self.check)
            with self.subTest(change=change):
                change()
                with self.assertRaises(ValueError):
                    self.inspect()
            self.receipt = original_receipt
            self.check.clear(); self.check.update(original_check)

    def test_legacy_schema_does_not_silently_gain_geometry_semantics(self):
        self.system["schema"] = "1.0"
        with self.assertRaises(ValueError):
            self.inspect()

    def test_approved_staggering_is_a_scoped_exception(self):
        self.receipt["observations"][0]["probes"][1]["matches"][0]["bounds"]["y"] = 20
        self.system["exceptions"] = [{"check": "control-axis", "reason": "Explicitly supplied staggered target", "revisit": "User reopens the target"}]
        self.assertEqual([], self.inspect()["issues"])


if __name__ == "__main__":
    unittest.main()
