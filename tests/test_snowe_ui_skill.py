from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skill" / "snowe-ui-skill"
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from asset_quality import validate_svg_asset  # noqa: E402
from contrast import (  # noqa: E402
    best_foreground,
    check_contrast,
    contrast_ratio,
    parse_opaque_color,
)
from core import CSV_CONFIG, DOMAIN_SOURCE_ROLES, search  # noqa: E402
from decision_packet import (  # noqa: E402
    DecisionPacketGenerator,
    format_packet_json,
    format_packet_markdown,
    generate_decision_packet,
    persist_decision_packet,
    slugify_name,
)


def nested_keys(value):
    keys = set()
    if isinstance(value, dict):
        for key, child in value.items():
            keys.add(key)
            keys.update(nested_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(nested_keys(child))
    return keys


class SkillPackageTests(unittest.TestCase):
    def test_identity_and_progressive_routes_are_current(self):
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\nname: snowe-ui-skill\n"))
        self.assertNotIn("snowe-ui-pro", text.casefold())
        references = (
            "exploration-protocol.md",
            "experience-architecture.md",
            "art-direction-gate.md",
            "design-foundations.md",
            "imagery-and-assets.md",
            "iconography-system.md",
            "motion-and-interaction.md",
            "research-and-evidence.md",
            "quality-gates.md",
            "designer-evaluation.md",
            "cli-reference.md",
        )
        for filename in references:
            self.assertIn(f"references/{filename}", text)
            self.assertTrue((SKILL_ROOT / "references" / filename).is_file())
        self.assertLess(len(text.splitlines()), 500)

    def test_interface_metadata_matches_skill(self):
        text = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn('display_name: "Snowe UI Skill"', text)
        self.assertIn("$snowe-ui-skill", text)
        self.assertNotIn("snowe-ui-pro", text)

    def test_recipe_generator_and_derived_recipe_data_are_removed(self):
        removed = (
            SCRIPTS / "design_system.py",
            SCRIPTS / "design_quality.py",
            SKILL_ROOT / "data" / "ui-reasoning.csv",
            SKILL_ROOT / "data" / "design.csv",
            SKILL_ROOT / "data" / "draft.csv",
            SKILL_ROOT / "data" / "_sync_all.py",
            SKILL_ROOT / "data" / "landing.csv",
            SKILL_ROOT / "data" / "styles.csv",
            SKILL_ROOT / "data" / "colors.csv",
            SKILL_ROOT / "data" / "typography.csv",
            SKILL_ROOT / "data" / "motion.csv",
        )
        self.assertTrue(all(not path.exists() for path in removed))

    def test_packet_has_no_keyword_classifier_tables(self):
        text = (SCRIPTS / "decision_packet.py").read_text(encoding="utf-8")
        for symbol in ("_SIGNAL_RULES", "_QUERY_EXPANSIONS", "_PRESSURES", "_detect_signals"):
            self.assertNotIn(symbol, text)

    def test_public_usage_docs_match_unresolved_cli_and_current_domains(self):
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        cli = (SKILL_ROOT / "references" / "cli-reference.md").read_text(encoding="utf-8")
        for domain in ("landing", "style", "color", "typography", "gsap"):
            self.assertNotIn(f"| `{domain}` |", cli)
        self.assertIn("--analog-query", readme)
        self.assertIn("--analog-query", cli)
        self.assertIn("does not classify brief vocabulary", readme)
        self.assertIn("node scripts/browser-smoke.mjs --smoke", readme)

    def test_references_keep_none_as_a_real_design_outcome(self):
        imagery = (SKILL_ROOT / "references" / "imagery-and-assets.md").read_text(encoding="utf-8")
        motion = (SKILL_ROOT / "references" / "motion-and-interaction.md").read_text(encoding="utf-8")
        icons = (SKILL_ROOT / "references" / "iconography-system.md").read_text(encoding="utf-8")
        self.assertIn("No image", imagery)
        self.assertIn("compare the page without the asset", imagery)
        self.assertIn("omit it", motion)
        self.assertIn("Static", motion)
        self.assertIn("visible text", icons)
        self.assertIn("Mark custom work `REJECT`", icons)

    def test_evaluation_is_behavioral_and_non_numeric(self):
        text = (SKILL_ROOT / "references" / "designer-evaluation.md").read_text(encoding="utf-8")
        self.assertIn("KEEP | REVISE | REJECT | UNKNOWN", text)
        self.assertIn("Do not average taste into a number", text)
        self.assertIn("Cross-Scenario Comparison", text)
        self.assertIn("wide / pressure / narrow", text)


class DecisionPacketTests(unittest.TestCase):
    def setUp(self):
        self.generator = DecisionPacketGenerator()

    @staticmethod
    def framing_contract(packet):
        situation = packet["situation"]
        return {
            "framing_status": situation["framing_status"],
            "mode": situation["mode"],
            "platforms": situation["platforms"],
            "pressure_status": situation["pressure_status"],
            "design_pressures": situation["design_pressures"],
            "pressure_inquiry": situation["pressure_inquiry"],
            "unknowns": situation["unknowns"],
            "architecture_status": packet["architecture"]["status"],
            "local_evidence_status": packet["local_evidence"]["status"],
        }

    def test_packet_opens_instead_of_selecting_design(self):
        packet = self.generator.generate(
            "Responsive bicycle retailer with real prices, fit advice, test rides, and checkout",
            "Wheelhouse",
        )
        forbidden = {
            "pattern",
            "section_order",
            "landing_pattern",
            "style",
            "palette",
            "font",
            "typography",
            "colors",
            "motion_snippet",
            "motion_intensity",
        }
        self.assertTrue(forbidden.isdisjoint(nested_keys(packet)))
        self.assertTrue(packet["architecture"]["status"].startswith("OPEN"))
        self.assertEqual("OPEN", packet["assets"]["visual_need_decision"]["status"])
        self.assertTrue(packet["motion"]["status"].startswith("OPEN"))

    def test_markdown_states_that_packet_is_not_the_design(self):
        packet = self.generator.generate("New responsive editorial publication", "Field Notes")
        markdown = format_packet_markdown(packet)
        self.assertIn("opens decisions", markdown)
        self.assertIn("does not select a layout", markdown)
        self.assertNotIn("**Pattern:**", markdown)
        self.assertNotIn("**Section Order:**", markdown)

    def test_json_output_round_trips(self):
        packet = self.generator.generate("Keyboard-first inventory operations desktop", "Stockroom")
        self.assertEqual(packet, json.loads(format_packet_json(packet)))
        generated = json.loads(
            generate_decision_packet(
                "Keyboard-first inventory operations desktop", "Stockroom", output_format="json"
            )
        )
        self.assertEqual("Stockroom", generated["project_name"])

    def test_default_packet_has_no_semantic_classifier_output(self):
        packet = self.generator.generate("Urban bicycle retailer with prices and checkout")
        situation = packet["situation"]
        self.assertNotIn("signals", situation)
        self.assertEqual([], situation["design_pressures"])
        self.assertEqual("UNRESOLVED", situation["framing_status"])
        self.assertIn("does not detect language", situation["language_policy"])

    def test_english_and_russian_commerce_briefs_share_the_same_open_framing(self):
        english = self.generator.generate(
            "Independent bicycle retailer with prices, fit advice, test rides, and purchase."
        )
        russian = self.generator.generate(
            "Независимый магазин велосипедов с ценами, подбором посадки, тест-драйвом и покупкой."
        )
        self.assertEqual(self.framing_contract(english), self.framing_contract(russian))

    def test_english_and_russian_public_service_briefs_share_open_framing(self):
        english = self.generator.generate(
            "Municipal permit service: check eligibility, apply, upload evidence, recover, and track status."
        )
        russian = self.generator.generate(
            "Муниципальная услуга: проверка права, подача заявления, загрузка доказательств, восстановление и статус."
        )
        self.assertEqual(self.framing_contract(english), self.framing_contract(russian))

    def test_ambiguous_domain_words_never_assign_roles(self):
        briefs = (
            "Workshop service history for a bicycle store",
            "Service history audit in a warehouse platform",
            "Application platform for a literary store archive",
            "Audit the application store listing",
            "Historical platform for public-service research",
            "Store audit history as a read-only dataset",
        )
        for brief in briefs:
            with self.subTest(brief=brief):
                situation = self.generator.generate(brief)["situation"]
                self.assertEqual([], situation["design_pressures"])
                self.assertTrue(situation["mode"].startswith("UNRESOLVED"))
                self.assertNotIn("signals", situation)

    def test_mixed_language_and_unknown_domain_remain_first_class(self):
        briefs = (
            "Keyboard-first склад: live exceptions, история аудита, transfer state",
            "Design a control surface for a xenobiological spore-exchange ritual",
        )
        contracts = [self.framing_contract(self.generator.generate(brief)) for brief in briefs]
        self.assertEqual(contracts[0], contracts[1])
        self.assertTrue(all(contract["local_evidence_status"] == "NOT_REQUESTED" for contract in contracts))

    def test_correct_behavior_can_leave_the_main_pressure_unresolved(self):
        situation = self.generator.generate("A platform for a new community")["situation"]
        self.assertEqual([], situation["design_pressures"])
        self.assertTrue(situation["pressure_status"].startswith("UNRESOLVED"))
        self.assertIn("absent from every bundled vocabulary", " ".join(situation["unknowns"]))

    def test_caller_declared_context_is_passed_through_without_vocabulary_limits(self):
        pressure = "Protect a seasonal hand-off ritual that has no established software category."
        packet = self.generator.generate(
            "Mixed-language brief",
            declared_context={
                "work_mode": "evolution",
                "platforms": ["shared kiosk", "printed fallback"],
                "facts": ["The existing visual system is coherent and must be preserved."],
                "pressures": [pressure],
                "domain_owner": "field coordinator",
            },
        )
        situation = packet["situation"]
        self.assertEqual([pressure], situation["design_pressures"])
        self.assertEqual("evolution", situation["mode"])
        self.assertEqual("field coordinator", situation["other_declared_context"]["domain_owner"])
        self.assertEqual("PARTIALLY_DECLARED", situation["framing_status"])

    def test_paraphrase_does_not_churn_framing(self):
        first = self.generator.generate("Review the current account form and preserve its brand system")
        second = self.generator.generate("Keep the coherent identity while examining the existing account form")
        self.assertEqual(self.framing_contract(first), self.framing_contract(second))

    def test_meaningful_declared_business_change_changes_pressures(self):
        shared = "Member publication with an archive"
        membership = self.generator.generate(
            shared,
            declared_context={"pressures": ["Sustain paid membership after readers experience editorial value."]},
        )
        public_good = self.generator.generate(
            shared,
            declared_context={"pressures": ["Maximize free public access and institutional preservation."]},
        )
        self.assertNotEqual(
            membership["situation"]["design_pressures"],
            public_good["situation"]["design_pressures"],
        )

    def test_image_generation_is_eligible_but_not_automatic(self):
        visual = self.generator.generate("New product website")["assets"]
        outcomes = visual["visual_need_decision"]["eligible_outcomes"]
        self.assertIn("No image", outcomes)
        self.assertIn("Generated artwork or photography", outcomes)
        self.assertIn("real layout", " ".join(visual["image_generation"]["loop"]).casefold())

    def test_motion_starts_from_static_and_reduced_motion(self):
        motion = self.generator.generate("Expressive campaign website")["motion"]
        text = " ".join((motion["status"], motion["decision_question"], *motion["rules"])).casefold()
        self.assertIn("static", text)
        self.assertIn("reduced-motion", text)
        self.assertIn("no animation", text)
        self.assertNotIn("intensity", motion)

    def test_research_is_targeted_and_has_a_stop_condition(self):
        research = self.generator.generate("Новый неизвестный домен")["research"]
        self.assertIn("targeted", research["posture"])
        self.assertIn("never a mandatory moodboard", research["posture"])
        self.assertIn("never activates", research["activation_rule"])
        self.assertTrue(all(trigger["activate_when"] for trigger in research["triggers"]))
        self.assertTrue(all(trigger["stop"] for trigger in research["triggers"]))

    def test_local_analogs_are_opt_in_limited_and_non_authoritative(self):
        default = self.generator.generate("Urban bicycle retailer and fit guide")["local_evidence"]
        self.assertEqual("NOT_REQUESTED", default["status"])
        self.assertEqual([], default["product_analogs"])
        evidence = self.generator.generate(
            "Городские велосипеды",
            analog_query="bicycle cycling",
        )["local_evidence"]
        self.assertEqual("REQUESTED_BY_CALLER", evidence["status"])
        self.assertLessEqual(len(evidence["product_analogs"]), 3)
        self.assertTrue(evidence["product_analogs"])
        self.assertTrue(
            all(item["status"] == "UNVERIFIED_ANALOG" for item in evidence["product_analogs"])
        )
        self.assertTrue(all(set(item) == {"status", "label", "catalog_terms", "warning"} for item in evidence["product_analogs"]))
        self.assertIn("never classification", evidence["role"])

    def test_missing_local_analogs_do_not_change_reasoning(self):
        baseline = self.generator.generate("Unknown domain")
        with patch("decision_packet.search", return_value={"results": []}):
            absent = self.generator.generate("Unknown domain", analog_query="not in catalog")
        self.assertEqual(baseline["architecture"], absent["architecture"])
        self.assertEqual(baseline["situation"], absent["situation"])
        self.assertEqual([], absent["local_evidence"]["product_analogs"])
        self.assertIn("changes no framing", absent["local_evidence"]["absence_rule"])

    def test_candidate_contract_includes_real_architecture_dimensions(self):
        record = self.generator.generate("New public service")["architecture"]["candidate_record"]
        self.assertTrue(
            {
                "thesis",
                "site_scope",
                "topology",
                "navigation",
                "page_jobs",
                "content_sequence",
                "conversion_path",
                "responsive_transformation",
                "risk",
            }.issubset(record)
        )


class PersistenceTests(unittest.TestCase):
    def test_decisions_are_preserved_while_brief_regenerates(self):
        packet = DecisionPacketGenerator().generate("Commerce site", "North Star")
        with tempfile.TemporaryDirectory() as temporary_directory:
            first = persist_decision_packet(packet, output_dir=temporary_directory)
            project_dir = Path(first["design_intelligence_dir"])
            decisions = project_dir / "DECISIONS.md"
            decisions.write_text("accepted evidence\n", encoding="utf-8")
            packet["brief"] = "Changed inquiry"
            second = persist_decision_packet(packet, output_dir=temporary_directory)
            self.assertEqual("accepted evidence\n", decisions.read_text(encoding="utf-8"))
            self.assertIn(str(decisions), second["preserved_files"])
            self.assertIn("Changed inquiry", (project_dir / "BRIEF.md").read_text(encoding="utf-8"))

    def test_page_inquiry_does_not_prescribe_page_type_or_sections(self):
        packet = DecisionPacketGenerator().generate("Bike selection", "Wheelhouse")
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = persist_decision_packet(
                packet,
                page="find-a-bike",
                page_brief="Choose by use and fit",
                output_dir=temporary_directory,
            )
            page = Path(result["design_intelligence_dir"]) / "pages" / "find-a-bike.md"
            text = page.read_text(encoding="utf-8")
            self.assertIn("Page Inquiry", text)
            self.assertIn("does not prescribe a page type or section order", text)
            self.assertIn("pressure/intermediate", text)

    def test_slugged_project_and_page_paths_stay_under_output_root(self):
        packet = DecisionPacketGenerator().generate("Test", "../../outside")
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = persist_decision_packet(
                packet, page="../../../escape", output_dir=temporary_directory
            )
            root = Path(temporary_directory).resolve()
            project = Path(result["design_intelligence_dir"]).resolve()
            self.assertTrue(project.is_relative_to(root))
            self.assertEqual("outside", slugify_name("../../outside"))
            self.assertTrue(all(Path(path).resolve().is_relative_to(root) for path in result["created_or_updated_files"]))


class RetrievalTests(unittest.TestCase):
    def test_every_domain_exposes_an_epistemic_role(self):
        self.assertEqual(set(CSV_CONFIG), set(DOMAIN_SOURCE_ROLES))
        for domain in CSV_CONFIG:
            query = (
                "Lucide automation workflow"
                if domain == "icon-candidates"
                else "accessibility product interface"
            )
            result = search(query, domain, 1)
            self.assertIn("source_role", result)
            self.assertIn("warning", result)

    def test_product_results_expose_only_lexical_taxonomy(self):
        result = search("bicycle cycling route", "product", 3)
        self.assertIn("analogy", result["source_role"])
        self.assertTrue(result["results"])
        self.assertTrue(all(set(item) == {"Product Type", "Keywords"} for item in result["results"]))

    def test_semantic_domain_detection_is_unavailable(self):
        result = search("platform audit history store application", None, 3)
        self.assertIn("explicit evidence domain is required", result["error"])
        self.assertNotIn("domain", result)

    def test_recipe_domains_and_datasets_are_removed(self):
        removed_domains = {"landing", "style", "color", "typography", "gsap"}
        self.assertTrue(removed_domains.isdisjoint(CSV_CONFIG))
        for filename in ("landing.csv", "styles.csv", "colors.csv", "typography.csv", "motion.csv"):
            self.assertFalse((SKILL_ROOT / "data" / filename).exists())

    def test_remaining_catalog_schemas_exclude_solution_fields(self):
        forbidden = {
            "Section Order",
            "Primary CTA Placement",
            "Conversion Optimization",
            "Primary Style Recommendation",
            "Secondary Styles",
            "Landing Page Pattern",
            "Dashboard Style (if applicable)",
            "Color Palette Focus",
            "Key Considerations",
            "AI Prompt Keywords",
            "Implementation Checklist",
            "Design System Variables",
        }
        for name in ("products.csv",):
            with (SKILL_ROOT / "data" / name).open(newline="", encoding="utf-8") as handle:
                headers = set(next(csv.reader(handle)))
            self.assertTrue(forbidden.isdisjoint(headers), name)

    def test_bundled_data_has_no_numeric_conversion_claims(self):
        claim = re.compile(
            r"(?:\d+(?:\.\d+)?\s*%[^\n]{0,80}(?:conversion|engagement|time-on-page)|"
            r"(?:conversion|engagement|time-on-page)[^\n]{0,80}\d+(?:\.\d+)?\s*%)",
            re.IGNORECASE,
        )
        offenders = []
        for path in (SKILL_ROOT / "data").rglob("*.csv"):
            if claim.search(path.read_text(encoding="utf-8")):
                offenders.append(path.relative_to(SKILL_ROOT).as_posix())
        self.assertEqual([], offenders)

    def test_icon_candidate_lookup_requires_one_source_and_subject(self):
        self.assertIn("exactly one source family", search("delete", "icon-candidates")["error"])
        self.assertIn(
            "real subject",
            search("Lucide icon candidate", "icon-candidates")["error"],
        )
        result = search("Lucide automation workflow", "icon-candidates", 5)
        self.assertTrue(result["results"])
        self.assertTrue(all(item["Family"] == "Lucide" for item in result["results"]))

    def test_legacy_icon_style_rows_are_not_returned_as_symbols(self):
        result = search("delete trash", "icons", 12)
        self.assertTrue(
            all(item.get("Category", "").casefold() not in {"style config", "guideline"} for item in result["results"])
        )


class ContrastTests(unittest.TestCase):
    def test_wcag_reference_extremes(self):
        self.assertAlmostEqual(21.0, contrast_ratio("#000", "#fff"), places=6)
        self.assertEqual("PASS", check_contrast("#000000", "white")["status"])

    def test_known_near_threshold_pair_fails(self):
        result = check_contrast("#777777", "#FFFFFF", 4.5)
        self.assertEqual("FAIL", result["status"])
        self.assertAlmostEqual(4.478, result["ratio"], places=3)

    def test_best_foreground_chooses_stronger_exact_pair(self):
        result = best_foreground("#F4F0E6")
        self.assertEqual("#000000", result["foreground"])
        self.assertEqual("PASS", result["status"])

    def test_alpha_and_unsupported_colors_are_rejected(self):
        with self.assertRaises(ValueError):
            parse_opaque_color("rgba(0,0,0,.5)")
        with self.assertRaises(ValueError):
            parse_opaque_color("#00000080")


class AssetQualityTests(unittest.TestCase):
    def metadata(self):
        return {
            "name": "cargo-rack",
            "role": "interface icon",
            "grid": "24 x 24",
            "live_area": "2..22 with optical overshoot",
            "drawing_language": {
                "mode": "stroke",
                "stroke_width": 1.75,
                "linecap": "round",
                "linejoin": "round",
                "corner_language": "mechanical small radii",
                "detail_budget": "recognizable at 16 px",
            },
            "target_sizes": [16, 20, 24],
            "source": "repository-owned custom drawing",
            "license": "project-owned",
            "accessibility_owner": "owning labeled button; SVG decorative",
        }

    def test_valid_custom_icon_passes_structure_but_warns_about_optics(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            svg = root / "icon.svg"
            metadata = root / "icon.json"
            svg.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M3 15h18M6 15l2-6h8l2 6"/></svg>',
                encoding="utf-8",
            )
            metadata.write_text(json.dumps(self.metadata()), encoding="utf-8")
            result = validate_svg_asset(svg, metadata)
            self.assertTrue(result["valid"], result["errors"])
            self.assertIn("optical balance", " ".join(result["warnings"]))

    def test_interface_icon_requires_16_20_and_24_targets(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            svg = root / "icon.svg"
            metadata = root / "icon.json"
            svg.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="currentColor" d="M2 2h20v20H2z"/></svg>',
                encoding="utf-8",
            )
            value = self.metadata()
            value["target_sizes"] = [24]
            metadata.write_text(json.dumps(value), encoding="utf-8")
            result = validate_svg_asset(svg, metadata)
            self.assertFalse(result["valid"])
            self.assertIn("16, 20, and 24", " ".join(result["errors"]))

    def test_svg_rejects_external_raster_and_embedded_text(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            svg = root / "icon.svg"
            metadata = root / "icon.json"
            svg.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><image href="https://example.com/a.png"/><text x="2" y="12">A</text></svg>',
                encoding="utf-8",
            )
            metadata.write_text(json.dumps(self.metadata()), encoding="utf-8")
            result = validate_svg_asset(svg, metadata)
            self.assertFalse(result["valid"])
            errors = " ".join(result["errors"])
            self.assertIn("Forbidden", errors)
            self.assertIn("must not embed text", errors)

    def test_monochrome_contract_rejects_hard_coded_paint(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            svg = root / "icon.svg"
            metadata = root / "icon.json"
            svg.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="#ff0000" d="M2 2h20v20H2z"/></svg>',
                encoding="utf-8",
            )
            value = self.metadata()
            value["drawing_language"]["mode"] = "fill"
            metadata.write_text(json.dumps(value), encoding="utf-8")
            result = validate_svg_asset(svg, metadata)
            self.assertFalse(result["valid"])
            self.assertIn("currentColor", " ".join(result["errors"]))


class CliTests(unittest.TestCase):
    def run_cli(self, *arguments):
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "search.py"), *arguments],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

    def test_decision_packet_cli_emits_open_json(self):
        result = self.run_cli(
            "Bicycle retailer with prices",
            "--decision-packet",
            "--format",
            "json",
            "--project-name",
            "Wheelhouse",
        )
        self.assertEqual(0, result.returncode, result.stderr)
        packet = json.loads(result.stdout)
        self.assertTrue(packet["architecture"]["status"].startswith("OPEN"))
        self.assertEqual("3.0", packet["schema_version"])
        self.assertEqual("UNRESOLVED", packet["situation"]["framing_status"])
        self.assertEqual("NOT_REQUESTED", packet["local_evidence"]["status"])

    def test_historical_alias_opens_same_packet_and_dials_are_gone(self):
        alias = self.run_cli("Editorial publication", "--design-system")
        self.assertEqual(0, alias.returncode, alias.stderr)
        self.assertIn("opens decisions", alias.stdout)
        rejected = self.run_cli("Editorial publication", "--decision-packet", "--variance", "8")
        self.assertNotEqual(0, rejected.returncode)
        self.assertIn("unrecognized arguments", rejected.stderr)

    def test_persist_cli_requires_decision_packet(self):
        result = self.run_cli("test", "--persist")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("require --decision-packet", result.stderr)

    def test_local_search_requires_explicit_domain(self):
        result = self.run_cli("platform audit history")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("--domain is required", result.stderr)

    def test_analog_query_is_explicit_and_packet_only(self):
        rejected = self.run_cli("bicycle", "--analog-query", "cycling")
        self.assertNotEqual(0, rejected.returncode)
        self.assertIn("requires --decision-packet", rejected.stderr)
        accepted = self.run_cli(
            "Велосипедный магазин",
            "--decision-packet",
            "--analog-query",
            "bicycle cycling",
            "--format",
            "json",
        )
        self.assertEqual(0, accepted.returncode, accepted.stderr)
        packet = json.loads(accepted.stdout)
        self.assertEqual("REQUESTED_BY_CALLER", packet["local_evidence"]["status"])
        self.assertLessEqual(len(packet["local_evidence"]["product_analogs"]), 3)


if __name__ == "__main__":
    unittest.main()
