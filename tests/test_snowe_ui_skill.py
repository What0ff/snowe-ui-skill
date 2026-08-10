from __future__ import annotations

import csv
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPOSITORY_ROOT / "skill" / "snowe-ui-skill"
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from core import AVAILABLE_STACKS, CSV_CONFIG, detect_domain, search  # noqa: E402
from design_quality import (  # noqa: E402
    build_art_direction_gate,
    build_creative_distinction_gate,
    build_iconography,
    build_option_exploration,
    build_contrast_checks,
    build_rendered_critic,
    build_typography_director,
    build_visual_treatment_policy,
    color_luminance,
    contrast_ratio,
    ensure_accessible_semantic_colors,
    explicit_cool_color_request,
    explicit_luminous_request,
    neutralize_unrequested_cool_foundation,
    sanitize_visual_guidance,
    style_visual_traits,
)
from design_system import (  # noqa: E402
    DesignSystemGenerator,
    format_ascii_box,
    format_markdown,
    persist_design_system,
    slugify_name,
)


class SkillPackagingTests(unittest.TestCase):
    def test_skill_identity_and_progressive_disclosure(self):
        skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: snowe-ui-skill", skill_text)
        self.assertLess(len(skill_text.splitlines()), 500)
        self.assertIn("references/design-foundations.md", skill_text)
        self.assertIn("references/exploration-protocol.md", skill_text)
        self.assertIn("references/art-direction-gate.md", skill_text)
        self.assertIn("references/iconography-system.md", skill_text)
        self.assertIn("references/quality-gates.md", skill_text)
        self.assertIn("references/cli-reference.md", skill_text)

    def test_expected_stack_inventory_is_exposed(self):
        self.assertEqual(22, len(AVAILABLE_STACKS))
        self.assertIn("react", AVAILABLE_STACKS)
        self.assertIn("react-native", AVAILABLE_STACKS)
        self.assertIn("javafx", AVAILABLE_STACKS)


class PillPolicyTests(unittest.TestCase):
    def test_known_generic_pill_phrases_are_sanitized(self):
        source = (
            "All interactive elements are pill-shaped (borderRadius: 999). "
            "Use pill buttons or 12pt radius and rounded-full navigation."
        )
        result = sanitize_visual_guidance(source).casefold()
        self.assertNotIn("pill-shaped", result)
        self.assertNotIn("pill buttons", result)
        self.assertNotIn("rounded-full", result)
        self.assertNotIn("borderradius: 999", result)

    def test_direct_style_search_applies_policy(self):
        result = search("material you mobile", "style", 1)
        self.assertEqual(1, result["count"])
        combined = " ".join(str(value) for value in result["results"][0].values()).casefold()
        self.assertNotIn("pill-shaped", combined)
        self.assertNotIn("rounded-full", combined)
        self.assertNotIn("borderradius: 999", combined)

    def test_bauhaus_style_does_not_leak_999_button_radius(self):
        result = search("bauhaus mobile geometric", "style", 1)
        self.assertEqual(1, result["count"])
        combined = " ".join(str(value) for value in result["results"][0].values()).casefold()
        self.assertNotIn("999px (buttons", combined)
        self.assertNotIn("9999px (buttons", combined)

    def test_semantic_rounding_survives_while_decorative_navigation_is_sanitized(self):
        source = (
            "Avatar uses rounded-full. Status chip uses borderRadius: 999. "
            "Navigation items use rounded-full."
        )
        result = sanitize_visual_guidance(source)
        self.assertIn("Avatar uses rounded-full", result)
        self.assertIn("Status chip uses borderRadius: 999", result)
        self.assertNotIn("Navigation items use rounded-full", result)
        self.assertIn("component-specific radius", result)

    def test_soft_roundness_never_creates_generic_pill_tokens(self):
        design_system = DesignSystemGenerator().generate(
            "consumer finance mobile dashboard",
            "Finance",
            roundness=10,
        )
        tokens = design_system["shape_system"]["tokens"]
        self.assertEqual("soft", design_system["shape_system"]["profile"])
        self.assertNotIn("pill", tokens)
        self.assertNotIn("999", " ".join(tokens.values()))
        self.assertIn("standalone icons", " ".join(design_system["anti_patterns"]))
        self.assertIn("transparent", design_system["iconography"]["container"].casefold())


class ArtDirectionGateTests(unittest.TestCase):
    def test_scope_selects_the_smallest_honest_gate(self):
        direct = build_art_direction_gate("local bug fix in a narrow component")
        refinement = build_art_direction_gate("polish an existing interface")
        full = build_art_direction_gate("new product visual identity from scratch")

        self.assertEqual("Direct execution fit check", direct["mode"])
        self.assertEqual("Refinement gate", refinement["mode"])
        self.assertEqual("Full concept gate", full["mode"])
        self.assertIn("current rendered baseline", refinement["candidate_policy"])
        self.assertIn("Compare two direction cards", full["candidate_policy"])
        self.assertIn("third only when", full["candidate_policy"])

    def test_gate_requires_evidence_without_fake_taste_scores(self):
        gate = build_art_direction_gate("new operations product")
        review_text = " ".join(gate["review_dimensions"]).casefold()

        self.assertTrue(gate["initial_status"].startswith("UNKNOWN"))
        self.assertEqual("PASS | BLOCKER | UNKNOWN | N/A", gate["status_vocabulary"])
        self.assertIn("material design trade-off", gate["distinctness_rule"])
        self.assertIn("do not force an arbitrary number", gate["distinctness_rule"])
        self.assertIn("exactly one PASS, BLOCKER, UNKNOWN, or N/A token", gate["evidence_rule"])
        self.assertIn("never invent PASS with risk", gate["evidence_rule"])
        self.assertIn("never use numeric taste scores", gate["evidence_rule"])
        self.assertIn("product-specific distinctiveness", review_text)
        self.assertIn("pill", review_text)
        self.assertIn("neon/glow", review_text)
        self.assertIn("blockers", gate["selection_rule"])

    def test_generated_system_exposes_unresolved_art_direction_protocol(self):
        design_system = DesignSystemGenerator().generate(
            "new B2B logistics product visual identity",
            "Dispatch",
        )
        markdown = format_markdown(design_system)
        ascii_output = format_ascii_box(design_system)

        self.assertEqual("Full concept gate", design_system["art_direction_gate"]["mode"])
        self.assertIn("### Art Direction Gate", markdown)
        self.assertIn("UNKNOWN — generated retrieval is a design hypothesis", markdown)
        self.assertIn("#### Critic dimensions", markdown)
        self.assertIn("Implementation contract", markdown)
        self.assertIn("ART DIRECTION GATE", ascii_output)
        self.assertIn("UNKNOWN", ascii_output)


class OptionExplorationTests(unittest.TestCase):
    def test_material_decisions_search_the_relevant_external_space_before_cost(self):
        exploration = build_option_exploration("multilingual operations product redesign")
        domain_names = {item["domain"] for item in exploration["domains"]}
        sequence = " ".join(exploration["sequence"]).casefold()
        shortcuts = " ".join(exploration["anti_shortcuts"]).casefold()

        self.assertEqual("ALWAYS ON for material design decisions", exploration["mode"])
        self.assertIn("baseline rather than the outer boundary", exploration["principle"])
        self.assertIn("Typography", domain_names)
        self.assertIn("Iconography", domain_names)
        self.assertIn("Color and material", domain_names)
        self.assertIn("Imagery and illustration", domain_names)
        self.assertIn("Motion", domain_names)
        self.assertIn("Data visualization", domain_names)
        self.assertLess(sequence.index("semantic and visual ranking"), sequence.index("license, bundle"))
        self.assertIn("first acceptable installed", shortcuts)
        self.assertIn("font-name list", shortcuts)
        self.assertIn("evidence saturation", exploration["scope_boundary"])

    def test_generated_system_exposes_option_exploration_in_all_primary_formats(self):
        design_system = DesignSystemGenerator().generate(
            "multilingual logistics product redesign with icons and data",
            "Dispatch",
        )
        markdown = format_markdown(design_system)
        ascii_output = format_ascii_box(design_system)

        self.assertIn("### Explore → Compare → Commit", markdown)
        self.assertIn("#### Domain coverage", markdown)
        self.assertIn("Typography", markdown)
        self.assertIn("strongest rejected", markdown)
        self.assertIn("OPTION EXPLORATION", ascii_output)
        self.assertIn("ALWAYS ON for material design decisions", ascii_output)


class IconographyPolicyTests(unittest.TestCase):
    def test_curated_family_and_metaphor_pools_are_real_and_searchable(self):
        with (SKILL_ROOT / "data" / "icon-families.csv").open(encoding="utf-8", newline="") as file:
            families = list(csv.DictReader(file))
        with (SKILL_ROOT / "data" / "icon-concepts.csv").open(encoding="utf-8", newline="") as file:
            concepts = list(csv.DictReader(file))
        with (SKILL_ROOT / "data" / "icon-candidates.csv").open(encoding="utf-8", newline="") as file:
            candidates = list(csv.DictReader(file))

        family_names = {row["Family"] for row in families}
        self.assertGreaterEqual(len(families), 10)
        self.assertTrue({"Lucide", "Phosphor", "Tabler Icons", "Iconoir", "Remix Icon", "Radix Icons", "Heroicons", "Material Symbols", "SF Symbols", "Hugeicons Free"}.issubset(family_names))
        self.assertTrue(all(row["Official URL"].startswith("https://") for row in families))
        self.assertTrue(all(row["License"] for row in families))
        self.assertTrue(all(row["Package Hint"] for row in families))
        self.assertGreaterEqual(len(concepts), 20)
        self.assertIn("sparkles", next(row for row in concepts if row["Concept"] == "AI assistant")["Avoid as Default"].casefold())
        self.assertGreaterEqual(len(candidates), 70)
        self.assertEqual(7, len({row["Family"] for row in candidates}))
        self.assertTrue(all(row["Icon Name"] and row["Import Hint"] and row["Verified Version"] for row in candidates))
        self.assertIn("Workflow", {row["Icon Name"] for row in candidates if row["Family"] == "Lucide"})
        self.assertIn("IconChartSankey", {row["Icon Name"] for row in candidates if row["Family"] == "Tabler Icons"})
        self.assertIn("ChartScatterIcon", {row["Icon Name"] for row in candidates if row["Family"] == "Hugeicons Free"})
        self.assertIn("icon-families", CSV_CONFIG)
        self.assertIn("icon-concepts", CSV_CONFIG)
        self.assertIn("icon-candidates", CSV_CONFIG)

    def test_icon_domains_return_family_and_metaphor_guidance(self):
        family_result = search("tabler dense technical operations", "icon-families", 2)
        concept_result = search("automation workflow trigger rule", "icon-concepts", 2)
        self.assertGreaterEqual(family_result["count"], 1)
        self.assertEqual("Tabler Icons", family_result["results"][0]["Family"])
        self.assertGreaterEqual(concept_result["count"], 1)
        self.assertEqual("Automation", concept_result["results"][0]["Concept"])
        self.assertEqual("icon-families", detect_domain("compare tabler icons icon library"))
        self.assertEqual("icon-concepts", detect_domain("automation icon metaphor"))

    def test_named_candidate_search_uses_one_source_per_auditable_lookup(self):
        lucide = search("Lucide automation workflow branching", "icon-candidates", 3)
        hugeicons = search("Hugeicons relationship scatter distribution", "icon-candidates", 3)
        missing_family = search("automation workflow branching", "icon-candidates", 3)
        multiple_families = search("Lucide Tabler automation", "icon-candidates", 3)
        missing_concept = search("Lucide icon candidate", "icon-candidates", 3)

        self.assertGreaterEqual(lucide["count"], 1)
        self.assertLessEqual(lucide["count"], 3)
        self.assertEqual("Workflow", lucide["results"][0]["Icon Name"])
        self.assertTrue(all(row["Family"] == "Lucide" for row in lucide["results"]))
        self.assertGreaterEqual(hugeicons["count"], 1)
        self.assertLessEqual(hugeicons["count"], 3)
        self.assertEqual("ChartScatterIcon", hugeicons["results"][0]["Icon Name"])
        self.assertTrue(all(row["Family"] == "Hugeicons Free" for row in hugeicons["results"]))
        self.assertIn("exactly one source family per lookup", missing_family["error"])
        self.assertIn("exactly one source family per lookup", multiple_families["error"])
        self.assertIn("real subject", missing_concept["error"])

    def test_legacy_icon_lookup_cannot_reintroduce_glow_or_wrappers(self):
        result = search("cyberpunk neon glow icon", "icons", 5)
        combined = " ".join(str(value) for row in result["results"] for value in row.values()).casefold()
        source = (SKILL_ROOT / "data" / "icons.csv").read_text(encoding="utf-8").casefold()
        self.assertNotIn("wrap every icon", combined)
        self.assertNotIn("simulate neon glow", combined)
        self.assertNotIn("circular blurview", combined)
        self.assertNotIn("wrap every icon", source)
        self.assertNotIn("circular blurview", source)

    def test_generated_system_uses_role_first_anti_cliche_policy(self):
        design_system = DesignSystemGenerator().generate(
            "AI automation analytics operations dashboard",
            "Automation Ops",
        )
        iconography = design_system["iconography"]
        markdown = format_markdown(design_system)
        family_names = {item["family"] for item in iconography["family_candidates"]}
        guard_text = " ".join(
            f"{item['concept']} {item['avoid']} {item['prefer']}" for item in iconography["cliche_guard"]
        ).casefold()

        self.assertIn("Tabler Icons", family_names)
        self.assertIn("Repository evidence first", iconography["family_strategy"])
        self.assertIn("do not use package count as a quality metric", iconography["family_strategy"])
        self.assertIn("real subject → mechanism/output", iconography["decision_record"])
        self.assertIn("sparkles", guard_text)
        self.assertIn("the actual capability", guard_text)
        self.assertIn("Installable primary-source candidates", markdown)
        self.assertIn("Anti-cliche guard", markdown)
        self.assertIn("Multi-source compatibility gate", markdown)
        self.assertIn("Cross-library exploration closure gate", markdown)
        self.assertIn("Dependency acquisition gate", markdown)
        self.assertIn("install the single selected official adapter", iconography["family_strategy"])
        self.assertIn("normal scoped implementation step", iconography["dependency_acquisition"]["authority"])
        self.assertIn("repository package manager", " ".join(iconography["dependency_acquisition"]["installation"]).casefold())
        self.assertIn("Missing-glyph and custom-SVG gate", markdown)
        self.assertIn("choose between visible text, a compatible auxiliary source", markdown)
        self.assertIn("package count alone is neither a pass nor a failure", markdown)

    def test_multiple_icon_sources_are_evaluated_by_roles_and_rendered_compatibility(self):
        iconography = build_iconography(
            False,
            "existing React app uses Lucide for interface actions, Simple Icons for provider logos, and Material Symbols in an embedded Android panel",
        )
        reference = (SKILL_ROOT / "references" / "iconography-system.md").read_text(encoding="utf-8")
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        gate_text = " ".join(iconography["custom_icon_gate"]).casefold()
        compatibility_text = " ".join(iconography["compatibility_gate"]).casefold()
        acquisition_text = " ".join(
            [
                iconography["dependency_acquisition"]["authority"],
                iconography["dependency_acquisition"]["selection_rule"],
                *iconography["dependency_acquisition"]["verification"],
                *iconography["dependency_acquisition"]["installation"],
            ]
        ).casefold()

        self.assertIn("compatible auxiliary source", gate_text)
        self.assertIn("visible text", gate_text)
        self.assertEqual("Lucide", iconography["established_family"])
        self.assertEqual(
            ["Lucide", "Simple Icons", "Material Symbols"],
            iconography["established_sources"],
        )
        self.assertIn("stable role", compatibility_text)
        self.assertIn("package count alone is neither a pass nor a failure", compatibility_text)
        self.assertIn(
            "do not stop merely because the strongest source is not already present",
            acquisition_text,
        )
        self.assertIn("review, audit, or direction-only", acquisition_text)
        self.assertIn("manifest and lockfile", acquisition_text)
        self.assertTrue(
            {item["family"] for item in iconography["family_candidates"]}
            - set(iconography["established_sources"])
        )
        self.assertIn("Source Roles and Compatibility", reference)
        self.assertIn("Dependency Acquisition Gate", reference)
        self.assertIn("dependency count as inventory, not a quality score", reference.casefold())
        self.assertIn("installed icon packages as evidence and a migration baseline, not a closed allowlist", skill)
        self.assertIn("Do not count packages as a quality metric", skill)
        self.assertNotIn("never use a second icon library", reference.casefold())
        self.assertNotIn("second icon-library dependency", skill.casefold())

    def test_installed_sources_are_baseline_not_a_closed_candidate_pool(self):
        iconography = build_iconography(
            False,
            "existing React dense operations dashboard currently uses Lucide and Hugeicons",
        )
        candidates = {item["family"]: item for item in iconography["family_candidates"]}

        self.assertEqual(["Lucide", "Hugeicons Free"], iconography["established_sources"])
        self.assertIn("Tabler Icons", candidates)
        self.assertIn("Radix Icons", candidates)
        self.assertIn("Iconoir", candidates)
        self.assertEqual("observed repository source", candidates["Lucide"]["status"])
        self.assertIn("installable candidate", candidates["Tabler Icons"]["status"])
        self.assertIn("never install the whole comparison set", iconography["dependency_acquisition"]["selection_rule"])

    def test_explicit_cross_library_request_cannot_stop_after_an_installed_winner(self):
        iconography = build_iconography(
            False,
            "В React-проекте стоят Lucide и Hugeicons. Эти самолёты не подходят: посмотри другие библиотеки и найди лучший вариант.",
        )
        gate = iconography["exploration_gate"]
        closure_text = " ".join(gate["closure_evidence"]).casefold()
        phase_text = " ".join(gate["decision_phases"]).casefold()
        selection_text = " ".join(iconography["selection_order"]).casefold()
        candidate_families = {item["family"] for item in iconography["family_candidates"]}
        external_families = candidate_families - set(iconography["established_sources"])
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8").casefold()
        reference = (SKILL_ROOT / "references" / "iconography-system.md").read_text(encoding="utf-8").casefold()
        cli_reference = (SKILL_ROOT / "references" / "cli-reference.md").read_text(encoding="utf-8").casefold()

        self.assertTrue(gate["mode"].startswith("BROAD cross-library exploration"))
        self.assertEqual(["Lucide", "Hugeicons Free"], iconography["established_sources"])
        self.assertIn("strong installed candidate", gate["early_stop_rule"].casefold())
        self.assertIn("at least three relevant uninstalled families", closure_text)
        self.assertIn("at least two uninstalled families", closure_text)
        self.assertIn("catalog landing page", closure_text)
        self.assertIn("phase a", phase_text)
        self.assertIn("without penalizing installation state", phase_text)
        self.assertIn("phase b", phase_text)
        self.assertIn("semantic and visual ranking first", selection_text)
        self.assertGreaterEqual(len(external_families), 3)
        self.assertTrue({"Tabler Icons", "Iconoir", "Phosphor", "Remix Icon"}.issubset(candidate_families))
        self.assertIn("a catalog skim or package-name list is not a comparison", skill)
        self.assertIn("exploration closure gate", reference)
        self.assertIn("catalog-only scan cannot stop that search", cli_reference)

    def test_non_universal_icons_are_broad_by_default_with_a_learned_action_exception(self):
        iconography = build_iconography(False, "existing React settings screen uses Lucide")
        gate = iconography["exploration_gate"]

        self.assertTrue(gate["mode"].startswith("BROAD by default"))
        self.assertIn("ROUTINE is allowed only", gate["mode"])
        self.assertIn("confirmed learned universal action", gate["mode"])
        external_families = {
            item["family"] for item in iconography["family_candidates"]
        } - set(iconography["established_sources"])
        self.assertGreaterEqual(len(external_families), 3)

    def test_platform_shortlists_and_universal_actions_preserve_recognition(self):
        apple = build_iconography(True, "native iOS SwiftUI toolbar")
        android = build_iconography(True, "Android Jetpack Compose Material app")
        self.assertEqual("SF Symbols", apple["family_candidates"][0]["family"])
        self.assertEqual("Material Symbols", android["family_candidates"][0]["family"])
        self.assertTrue(all(" or " not in item["family"].casefold() for item in apple["family_candidates"]))
        self.assertTrue(all(" or " not in item["family"].casefold() for item in android["family_candidates"]))
        self.assertIn("search", apple["role_rules"]["universal_actions"])
        self.assertIn("novelty reduces recognition", apple["role_rules"]["universal_actions"])


class VisualIdentityPolicyTests(unittest.TestCase):
    def test_default_style_search_removes_luminous_effect_recipe(self):
        result = search("dark mode OLED operations dashboard", "style", 3)
        self.assertTrue(any("dark mode" in item.get("Style Category", "").casefold() for item in result["results"]))
        combined = " ".join(
            str(value) for item in result["results"] for value in item.values()
        ).casefold()
        self.assertNotIn("minimal glow", combined)
        self.assertNotIn("text-shadow: 0 0", combined)
        self.assertNotIn("box-shadow: 0 0", combined)
        self.assertNotIn("electric blue", combined)
        self.assertNotIn("plasma purple", combined)

    def test_enterprise_mobile_gradient_recipe_is_sanitized(self):
        source = (
            "Indigo→Violet gradient primary CTAs + active tab highlights, "
            "colored card shadows rgba(79,70,229,0.08), gradient active tab icon, "
            "full-width CTA at screen bottom"
        )
        result = sanitize_visual_guidance(source).casefold()
        self.assertNotIn("indigo→violet gradient", result)
        self.assertNotIn("colored card shadows", result)
        self.assertNotIn("gradient active tab icon", result)
        self.assertNotIn("full-width cta at screen bottom", result)
        self.assertIn("solid product-specific accent", result)
        retrieved = search("enterprise SaaS mobile finance app", "style", 3)
        retrieved_text = " ".join(
            str(value) for item in retrieved["results"] for value in item.values()
        ).casefold()
        self.assertNotIn("indigo→violet gradient", retrieved_text)
        self.assertNotIn("colored card shadows", retrieved_text)

    def test_cool_foundation_is_neutralized_unless_explicit(self):
        source = {
            "primary": "#1E40AF",
            "secondary": "#3B82F6",
            "accent": "#06B6D4",
            "background": "#0F172A",
            "foreground": "#F8FAFC",
            "card": "#1E293B",
            "muted": "#334155",
            "muted_foreground": "#94A3B8",
            "border": "#475569",
            "ring": "#60A5FA",
        }
        neutral, adjustments = neutralize_unrequested_cool_foundation(source)
        preserved, explicit_adjustments = neutralize_unrequested_cool_foundation(
            source,
            allow_cool_foundation=explicit_cool_color_request("use the supplied navy brand palette"),
        )
        self.assertTrue(adjustments)
        self.assertEqual("#111110", neutral["background"])
        self.assertEqual("#1E40AF", neutral["primary"])
        self.assertEqual("#1E40AF", neutral["accent"])
        self.assertEqual(source, preserved)
        self.assertFalse(explicit_adjustments)

    def test_functional_blue_accent_on_neutral_surfaces_is_preserved(self):
        source = {
            "primary": "#1E40AF",
            "secondary": "#D6D3D1",
            "accent": "#B45309",
            "background": "#FAFAF9",
            "foreground": "#1C1917",
            "card": "#FFFFFF",
            "muted": "#F5F5F4",
            "muted_foreground": "#57534E",
            "border": "#D6D3D1",
            "ring": "#1E40AF",
        }
        preserved, adjustments = neutralize_unrequested_cool_foundation(source)
        self.assertEqual(source, preserved)
        self.assertFalse(adjustments)

    def test_negative_visual_language_is_not_misread_as_a_request(self):
        self.assertFalse(explicit_luminous_request("No neon or glow; avoid blue-purple gradient"))
        self.assertFalse(explicit_cool_color_request("Avoid blue-purple AI glow"))
        self.assertTrue(explicit_luminous_request("Use a deliberate neon sign motif"))

    def test_dashboard_uses_compact_controls_and_contextual_solid_foundation(self):
        design_system = DesignSystemGenerator().generate(
            "fleet operations dashboard desktop admin dense data tables monitoring",
            "Fleet Ops",
        )
        markdown = format_markdown(design_system)
        self.assertEqual("Compact Desktop", design_system["control_sizing"]["mode"])
        self.assertEqual("32px", design_system["control_sizing"]["css_height"])
        self.assertIn("Fit content by default", design_system["control_sizing"]["width"])
        self.assertIn("### Control Scale", markdown)
        self.assertIn("context-derived solid foundation", markdown.casefold())
        self.assertNotIn("blue data", design_system["colors"]["notes"].casefold())
        self.assertNotIn("minimal glow", design_system["key_effects"].casefold())
        self.assertNotIn("text-shadow: 0 0", design_system["key_effects"].casefold())

    def test_exact_style_priority_beats_exaggerated_name_fragment(self):
        design_system = DesignSystemGenerator().generate(
            "consumer finance mobile dashboard",
            "Finance",
        )
        self.assertEqual("Accessible & Ethical", design_system["style"]["name"])
        self.assertNotIn("oversized typography", design_system["style"]["keywords"].casefold())

    def test_explicit_effect_permission_stays_with_the_named_role(self):
        query = (
            "verified brand requires a blue-to-violet gradient in the campaign hero and "
            "a capsule-shaped primary purchase CTA; no glow on cards, fields, or navigation; "
            "Russian finance dashboard"
        )
        policy = build_visual_treatment_policy(query)
        source = (
            "Blue-to-violet gradient campaign hero. "
            "Indigo→Violet gradient primary CTAs. "
            "Gradient active tab icon. Minimal glow (blue) on cards."
        )
        sanitized = sanitize_visual_guidance(
            source,
            allow_gradient=policy["allow_gradient"],
            allowed_gradient_roles=policy["gradient_roles"],
            allow_luminous=policy["allow_glow"],
            allowed_luminous_roles=policy["glow_roles"],
        ).casefold()

        self.assertTrue(policy["allow_gradient"])
        self.assertEqual({"hero", "brand"}, set(policy["gradient_roles"]))
        self.assertFalse(policy["allow_glow"])
        self.assertFalse(policy["allow_gradient_style"])
        self.assertNotIn("cta", policy["gradient_roles"])
        self.assertNotIn("surface", policy["gradient_roles"])
        self.assertIn("blue-to-violet gradient campaign hero", sanitized)
        self.assertNotIn("indigo→violet gradient", sanitized)
        self.assertNotIn("gradient active tab icon", sanitized)
        self.assertNotIn("minimal glow", sanitized)

        retrieved = search(query, "style", 5)
        self.assertTrue(all(not style_visual_traits(item)["cool_gradient"] for item in retrieved["results"]))

    def test_product_wide_effect_request_can_select_a_matching_style(self):
        policy = build_visual_treatment_policy(
            "Use gradient as the overall visual language across the product"
        )
        self.assertTrue(policy["allow_gradient"])
        self.assertTrue(policy["allow_gradient_style"])

    def test_scoped_brand_exception_does_not_unlock_a_cool_foundation(self):
        query = "verified brand gradient only in the campaign hero on a neutral product canvas"
        self.assertFalse(explicit_cool_color_request(query))
        self.assertFalse(
            explicit_cool_color_request(
                "blue-to-violet gradient only in the campaign hero on a neutral product canvas"
            )
        )
        self.assertTrue(explicit_cool_color_request("use the supplied navy brand palette across the product foundation"))
        self.assertTrue(
            explicit_cool_color_request(
                "используй проверенную фирменную синюю палитру для цветовой основы продукта"
            )
        )
        self.assertFalse(explicit_cool_color_request("не использовать фирменную палитру"))

    def test_positive_and_negative_luminous_clauses_can_coexist(self):
        policy = build_visual_treatment_policy(
            "No glow on cards, fields, or navigation; use a deliberate neon treatment only in the campaign hero"
        )
        self.assertTrue(policy["allow_glow"])
        self.assertEqual(["hero"], policy["glow_roles"])

    def test_explicit_capsule_request_becomes_a_scoped_exception(self):
        design_system = DesignSystemGenerator().generate(
            "capsule-shaped primary purchase CTA; ordinary controls stay compact and component-specific",
            "Storefront",
        )
        exceptions = " ".join(design_system["shape_system"]["approved_exceptions"]).casefold()
        self.assertIn("primary purchase or cta", exceptions)
        self.assertIn("do not propagate", exceptions)

    def test_russian_brief_preserves_the_same_scoped_semantics(self):
        query = (
            "Проверенный бренд требует градиент только в hero; "
            "без свечения на карточках и в навигации; "
            "капсульная кнопка покупки"
        )
        policy = build_visual_treatment_policy(query)
        design_system = DesignSystemGenerator().generate(query, "Магазин")

        self.assertTrue(policy["allow_gradient"])
        self.assertEqual({"hero", "brand"}, set(policy["gradient_roles"]))
        self.assertFalse(policy["allow_glow"])
        self.assertIn("Primary purchase or CTA", design_system["shape_system"]["approved_exceptions"][0])


class DesignDirectionIntelligenceTests(unittest.TestCase):
    def test_typography_director_requires_real_script_and_numeric_evidence(self):
        director = build_typography_director("Russian finance analytics dashboard with dense tables")
        verification = " ".join(director["verification"]).casefold()
        stress = " ".join(director["stress_content"]).casefold()

        self.assertIn("unknown", director["initial_status"].casefold())
        self.assertEqual("Cyrillic", director["script_requirements"])
        self.assertIn("dense numeric and tabular data", director["content_modes"])
        self.assertIn("glyph", verification)
        self.assertIn("fallback", verification)
        self.assertIn("currencies", stress)

        rtl_director = build_typography_director("Hebrew RTL payments עברית")
        self.assertIn("Hebrew", rtl_director["script_requirements"])
        self.assertIn("bidirectional", rtl_director["direction_policy"].casefold())

    def test_creative_distinction_is_product_anchored_without_forced_ornament(self):
        gate = build_creative_distinction_gate(
            "new logistics operations dashboard",
            category="Logistics",
            pattern_name="Operations Workspace",
            style_name="Swiss",
        )
        risks = " ".join(gate["template_risks"]).casefold()

        self.assertIn("unknown", gate["initial_status"].casefold())
        self.assertIn("logistics", gate["product_anchor"].casefold())
        self.assertIn("ornament is optional", gate["ownable_move"].casefold())
        self.assertIn("component-library", risks)
        self.assertIn("generic saas", gate["pass_rule"].casefold())

    def test_rendered_critic_is_evidence_based_and_bounded(self):
        critic = build_rendered_critic("refine an existing product interface")
        workflow = " ".join(critic["workflow"]).casefold()

        self.assertIn("current interface", critic["baseline"].casefold())
        self.assertIn("one critic pass", workflow)
        self.assertIn("rerender", workflow)
        self.assertIn("one full critic pass by default", critic["stop_rule"].casefold())
        self.assertIn("do not perform tweak roulette", critic["anti_loop"].casefold())

    def test_generated_outputs_expose_all_design_decision_modules(self):
        design_system = DesignSystemGenerator().generate(
            "new Russian finance dashboard with dense numeric tables",
            "Ledger",
        )
        markdown = format_markdown(design_system)

        self.assertIn("### Creative Distinction Gate", markdown)
        self.assertIn("#### Typography Director", markdown)
        self.assertIn("### Rendered Critic Loop", markdown)
        self.assertIn("### Project Design Memory", markdown)
        self.assertIn("UNKNOWN — distinctiveness must be demonstrated", markdown)

    def test_project_memory_is_initialized_once_and_never_regenerated(self):
        design_system = DesignSystemGenerator().generate(
            "existing Russian finance dashboard",
            "Ledger",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            first = persist_design_system(design_system, output_dir=temporary_directory)
            memory_path = Path(first["design_system_dir"]) / "PROJECT-MEMORY.md"
            marker = "\nCONFIRMED | Primary data font | Repository font files and rendered Cyrillic proof\n"
            memory_path.write_text(memory_path.read_text(encoding="utf-8") + marker, encoding="utf-8")

            second = persist_design_system(design_system, output_dir=temporary_directory)

            self.assertIn(str(memory_path), first["created_files"])
            self.assertNotIn(str(memory_path), second["created_files"])
            self.assertIn(str(memory_path), second["preserved_files"])
            self.assertIn(marker.strip(), memory_path.read_text(encoding="utf-8"))


class DesignSystemTests(unittest.TestCase):
    def test_explicit_platform_constraint_overrides_retrieved_style_type(self):
        desktop = DesignSystemGenerator().generate(
            "new B2B logistics product visual identity dispatchers high-density desktop",
            "Dispatch Desktop",
        )
        mobile = DesignSystemGenerator().generate(
            "new B2B logistics mobile app for dispatchers",
            "Dispatch Mobile",
        )

        self.assertNotEqual("Mobile", desktop["style"]["type"])
        self.assertNotEqual("Landing Page", desktop["style"]["type"])
        self.assertNotEqual("Touch / Mobile", desktop["control_sizing"]["mode"])
        self.assertEqual("Touch / Mobile", mobile["control_sizing"]["mode"])

    def test_contrast_ratio_reference_values(self):
        self.assertAlmostEqual(21.0, contrast_ratio("#FFFFFF", "#000000"), places=2)
        self.assertAlmostEqual(1.0, contrast_ratio("#123456", "#123456"), places=2)

    def test_semantic_foregrounds_are_repaired_and_disclosed(self):
        colors, adjustments = ensure_accessible_semantic_colors(
            {
                "primary": "#1E40AF",
                "on_primary": "#FFFFFF",
                "secondary": "#3B82F6",
                "on_secondary": "#FFFFFF",
                "accent": "#D97706",
                "on_accent": "#FFFFFF",
                "background": "#F8FAFC",
                "foreground": "#64748B",
                "card": "#FFFFFF",
                "card_foreground": "#64748B",
                "muted": "#E9EEF6",
                "muted_foreground": "#94A3B8",
                "destructive": "#DC2626",
                "on_destructive": "#FFFFFF",
                "ring": "#DBEAFE",
            }
        )
        self.assertTrue(adjustments)
        self.assertNotEqual("#FFFFFF", colors["on_accent"])
        self.assertTrue(all(check["status"] == "PASS" for check in build_contrast_checks(colors)))

    def test_markdown_contains_professional_foundations(self):
        design_system = DesignSystemGenerator().generate(
            "enterprise SaaS mobile dashboard",
            "Enterprise",
            roundness=6,
        )
        markdown = format_markdown(design_system)
        self.assertIn("### Design Direction", markdown)
        self.assertIn("### Layout System", markdown)
        self.assertIn("### Shape and Control Policy", markdown)
        self.assertIn("### Iconography", markdown)
        self.assertIn("#### Contrast Verification", markdown)
        self.assertIn("Avoid a horizontal pill behind a standalone icon", markdown)
        self.assertIn("token spelling alone is not a failure", markdown)
        self.assertNotIn("Use rounded-full", markdown)
        self.assertNotIn("borderRadius: 999", markdown)
        self.assertTrue(all(check["status"] == "PASS" for check in design_system["contrast_checks"]))

    def test_quality_reference_rejects_proxy_only_scoring(self):
        reference = (SKILL_ROOT / "references" / "quality-gates.md").read_text(encoding="utf-8")
        self.assertIn("Evaluation discipline", reference)
        self.assertIn("Fail whenever more than one icon source is installed", reference)
        self.assertNotIn("Only one icon package", reference)
        self.assertIn("package count", reference.casefold())
        self.assertIn("Heuristic or diagnostic signal", reference)
        self.assertIn("rendered effect", reference)

    def test_dark_only_style_receives_a_dark_compatible_palette(self):
        design_system = DesignSystemGenerator().generate(
            "fleet operations dashboard desktop admin dense data tables monitoring",
            "Fleet Ops",
        )
        if "dark" in design_system["style"]["name"].casefold() or "oled" in design_system["style"]["name"].casefold():
            self.assertLess(color_luminance(design_system["colors"]["background"]), 0.18)
        self.assertTrue(all(check["status"] == "PASS" for check in design_system["contrast_checks"]))

    def test_dashboard_uses_product_workspace_not_landing_pattern(self):
        design_system = DesignSystemGenerator().generate(
            "B2B logistics operations dashboard dispatchers dense desktop",
            "Fleet Ops",
            density=8,
        )
        self.assertEqual("Operations Workspace", design_system["pattern"]["name"])
        self.assertNotIn("Hero", design_system["pattern"]["sections"])
        self.assertIn("Compact data-interface", design_system["type_system"]["mode"])

    def test_explicit_landing_request_keeps_marketing_pattern(self):
        design_system = DesignSystemGenerator().generate(
            "analytics dashboard landing page product launch",
            "Launch",
        )
        self.assertNotEqual("Operations Workspace", design_system["pattern"]["name"])

    def test_persistence_slug_cannot_escape_output_directory(self):
        design_system = DesignSystemGenerator().generate(
            "documentation portal",
            "../Unsafe Project",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = persist_design_system(
                design_system,
                page="../../Settings",
                output_dir=temporary_directory,
                page_query="settings form",
            )
            expected_root = (Path(temporary_directory) / "design-system").resolve()
            for created_file in result["created_files"]:
                resolved = Path(created_file).resolve()
                self.assertEqual(
                    os.path.commonpath((str(expected_root), str(resolved))),
                    str(expected_root),
                )
                self.assertTrue(resolved.exists())
            master_text = Path(result["created_files"][0]).read_text(encoding="utf-8")
            self.assertIn("### Project-Wide Decision Policy", master_text)
            self.assertIn("### Art Direction Gate", master_text)
            self.assertIn("UNKNOWN — generated retrieval is a design hypothesis", master_text)
            self.assertIn(".icon-button", master_text)
            self.assertNotIn("border-radius: 999", master_text)
            self.assertNotIn("--radius-pill", master_text)
            self.assertEqual("unsafe-project", slugify_name("../Unsafe Project"))
            self.assertEqual("settings", slugify_name("../../Settings", "page"))

    def test_cli_rejects_page_without_persist(self):
        process = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "search.py"),
                "dashboard",
                "--design-system",
                "--page",
                "overview",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        self.assertNotEqual(0, process.returncode)
        self.assertIn("--page requires --persist", process.stderr)


if __name__ == "__main__":
    unittest.main()
