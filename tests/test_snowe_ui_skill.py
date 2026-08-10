from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


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
        )
        self.assertTrue(all(not path.exists() for path in removed))

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

    def test_service_word_does_not_turn_bicycle_retail_into_service_transaction(self):
        packet = self.generator.generate(
            "Bicycle retailer with workshop service, prices, test rides, and purchase",
            "Bike shop",
        )
        self.assertIn("commerce", packet["situation"]["signals"])
        self.assertNotIn("service_transaction", packet["situation"]["signals"])

    def test_platform_word_does_not_match_form_or_service(self):
        packet = self.generator.generate(
            "Independent literary magazine platform with issues, authors, and archives"
        )
        self.assertIn("editorial_content", packet["situation"]["signals"])
        self.assertNotIn("service_transaction", packet["situation"]["signals"])

    def test_domain_audit_history_does_not_change_work_mode(self):
        packet = self.generator.generate(
            "New warehouse operations workspace with inventory transfers and audit history"
        )
        self.assertEqual("new_direction", packet["situation"]["mode"])

    def test_explicit_usability_audit_changes_work_mode(self):
        packet = self.generator.generate("Perform a usability audit of the existing permit form")
        self.assertEqual("review", packet["situation"]["mode"])

    def test_scenarios_create_distinct_pressure_profiles(self):
        briefs = (
            "Urban bicycle retailer with prices and checkout",
            "Municipal permit eligibility, application, status, multilingual and high stakes",
            "Literary magazine with issues, long-form articles, authors, events and membership",
            "Keyboard-first warehouse inventory operations desktop workspace",
            "Experimental musician shop with releases and expressive brand",
        )
        profiles = {
            tuple(self.generator.generate(brief)["situation"]["signals"]) for brief in briefs
        }
        self.assertGreaterEqual(len(profiles), 5)

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
        research = self.generator.generate("New commerce brand and shop")["research"]
        self.assertIn("targeted", research["posture"])
        self.assertIn("never a mandatory moodboard", research["posture"])
        self.assertTrue(all(trigger["stop"] for trigger in research["triggers"]))

    def test_local_analogs_are_limited_labeled_and_non_authoritative(self):
        evidence = self.generator.generate("Urban bicycle retailer and fit guide")["local_evidence"]
        self.assertLessEqual(len(evidence["product_analogs"]), 3)
        self.assertTrue(evidence["product_analogs"])
        self.assertTrue(
            all(item["status"] == "UNVERIFIED_ANALOG" for item in evidence["product_analogs"])
        )
        self.assertTrue(
            any("Cycling" in item["label"] for item in evidence["product_analogs"])
        )
        self.assertIn("not classification", evidence["role"])

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

    def test_product_results_expose_considerations_not_only_recipes(self):
        result = search("bicycle cycling route", "product", 3)
        self.assertIn("analogy", result["source_role"])
        self.assertTrue(result["results"])
        self.assertTrue(all("Key Considerations" in item for item in result["results"]))

    def test_style_search_returns_snapshot_evidence_without_hidden_aesthetic_filter(self):
        result = search("cyberpunk neon glow", "style", 5)
        text = json.dumps(result["results"], ensure_ascii=False).casefold()
        self.assertIn("visual vocabulary", result["source_role"])
        self.assertTrue(any(term in text for term in ("cyberpunk", "neon", "glow")))

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


if __name__ == "__main__":
    unittest.main()
