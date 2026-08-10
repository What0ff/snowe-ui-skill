#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Design System Generator - Aggregates search results and applies reasoning
to generate comprehensive design system recommendations.

Usage:
    from design_system import generate_design_system
    result = generate_design_system("SaaS dashboard", "My Project")

    # With persistence (Master + Overrides pattern)
    result = generate_design_system("SaaS dashboard", "My Project", persist=True)
    result = generate_design_system("SaaS dashboard", "My Project", persist=True, page="dashboard")
"""

import csv
import json
import os
import re
import sys
import io
from datetime import datetime
from pathlib import Path
from core import search, DATA_DIR
from design_quality import (
    STANDARDS_BASELINE,
    build_art_direction_gate,
    build_component_guidance,
    build_control_sizing,
    build_contrast_checks,
    build_creative_distinction_gate,
    build_experience_pattern,
    build_iconography,
    build_layout_system,
    build_option_exploration,
    build_project_memory_policy,
    build_quality_gates,
    build_rendered_critic,
    build_typography_director,
    build_type_system,
    build_visual_treatment_policy,
    color_luminance,
    ensure_accessible_semantic_colors,
    explicit_cool_color_request,
    merge_anti_patterns,
    neutralize_unrequested_cool_foundation,
    resolve_shape_system,
    sanitize_visual_guidance,
    split_guidance,
)

# Force UTF-8 for stdout/stderr to handle emojis/box-drawing chars on Windows (cp1252 default)
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


# ============ CONFIGURATION ============
REASONING_FILE = "ui-reasoning.csv"

SEARCH_CONFIG = {
    "product": {"max_results": 1},
    # Keep enough style candidates to apply hard platform/surface filters before
    # preference scoring; a three-result shortlist can contain only incompatible
    # mobile or landing directions for an explicit desktop workspace query.
    "style": {"max_results": 8},
    "color": {"max_results": 2},
    "landing": {"max_results": 2},
    "typography": {"max_results": 2}
}

# ============ DESIGN DIALS (1-10) ============
# Inspired by taste-skill's DESIGN_VARIANCE / MOTION_INTENSITY / VISUAL_DENSITY
# knobs: four optional 1-10 sliders that bias the existing query-based search
# instead of replacing it. Each dial buckets into a low/mid/high tier.
DIAL_TIERS = {
    "variance": [
        (1, 3, {"label": "Centered / Minimal", "style_keywords": ["Minimalism", "Exaggerated Minimalism", "centered", "symmetric", "grid-based"]}),
        (4, 7, {"label": "Balanced / Modern", "style_keywords": ["modern", "structured", "balanced"]}),
        (8, 10, {"label": "Bold / Asymmetric", "style_keywords": ["Brutalism", "Bento Grids", "asymmetric", "experimental"]}),
    ],
    "motion": [
        (1, 3, {"label": "Subtle", "tier": "Subtle"}),
        (4, 7, {"label": "Standard", "tier": "Standard"}),
        (8, 10, {"label": "Complex", "tier": "Complex"}),
    ],
    "density": [
        (1, 3, {"label": "Spacious", "spacing": {"xs": "4px", "sm": "8px", "md": "24px", "lg": "32px", "xl": "48px", "2xl": "64px", "3xl": "96px"}}),
        (4, 7, {"label": "Standard", "spacing": {"xs": "4px", "sm": "8px", "md": "16px", "lg": "24px", "xl": "32px", "2xl": "48px", "3xl": "64px"}}),
        (8, 10, {"label": "Dense / Dashboard", "spacing": {"xs": "2px", "sm": "4px", "md": "8px", "lg": "12px", "xl": "16px", "2xl": "24px", "3xl": "32px"}}),
    ],
    "roundness": [
        (1, 3, {"label": "Sharp / Editorial", "profile": "sharp"}),
        (4, 7, {"label": "Balanced / Professional", "profile": "balanced"}),
        (8, 10, {"label": "Soft / Expressive", "profile": "soft"}),
    ],
}


def _resolve_dial(dial_name: str, value) -> dict:
    """Bucket a 1-10 dial value into its tier config. Returns None if value is None."""
    if value is None:
        return None
    value = max(1, min(10, int(value)))
    for lo, hi, info in DIAL_TIERS[dial_name]:
        if lo <= value <= hi:
            return {**info, "value": value}
    return None


def _style_palette_mode(style: dict) -> str | None:
    """Return a required palette mode when the style clearly declares one."""
    name_and_keywords = " ".join(
        (str(style.get("Style Category", "")), str(style.get("Keywords", "")))
    ).casefold()
    light_support = str(style.get("Light Mode ✓", "")).casefold()
    dark_support = str(style.get("Dark Mode ✓", "")).casefold()
    light_disabled = "✗" in light_support or "no" in light_support
    dark_disabled = "✗" in dark_support or "no" in dark_support

    if "dark mode" in name_and_keywords or "oled" in name_and_keywords:
        return "dark"
    if light_support and light_disabled and dark_support and not dark_disabled:
        return "dark"
    if dark_support and dark_disabled and light_support and not light_disabled:
        return "light"
    return None


def _palette_mode(palette: dict) -> str | None:
    luminance = color_luminance(palette.get("Background", ""))
    if luminance is None:
        return None
    return "dark" if luminance < 0.18 else "light"


def _query_platform_mode(query: str) -> str | None:
    """Resolve an explicit single-platform constraint from the user's query."""
    lowered = str(query or "").casefold()
    mobile_markers = (
        "mobile",
        "ios",
        "android",
        "react native",
        "flutter",
        "swiftui",
        "jetpack compose",
        "touch-first",
    )
    desktop_markers = (
        "desktop",
        "pointer-first",
        "mouse and keyboard",
        "windows app",
        "macos app",
    )
    has_mobile = any(marker in lowered for marker in mobile_markers)
    has_desktop = any(marker in lowered for marker in desktop_markers)
    if has_mobile == has_desktop:
        return None
    return "mobile" if has_mobile else "desktop"


def _query_surface_mode(query: str) -> str | None:
    """Distinguish a product workspace from an explicit marketing surface."""
    lowered = str(query or "").casefold()
    marketing_markers = (
        "landing page",
        "marketing site",
        "marketing page",
        "homepage",
        "campaign page",
        "conversion page",
        "website hero",
    )
    product_markers = (
        "dashboard",
        "admin",
        "workspace",
        "operations",
        "console",
        "control center",
        "data-dense",
        "high-density",
        "dispatcher",
        "internal tool",
        "portal",
    )
    has_marketing = any(marker in lowered for marker in marketing_markers)
    has_product = any(marker in lowered for marker in product_markers)
    if has_marketing == has_product:
        return None
    return "marketing" if has_marketing else "product"


def _select_color_palette(results: list, category: str, required_mode: str | None) -> dict:
    """Prefer a category-matched palette that agrees with the selected style mode."""
    if not results:
        return {}
    candidates = results
    if required_mode:
        compatible = [result for result in results if _palette_mode(result) == required_mode]
        if compatible:
            candidates = compatible

    category_text = category.casefold().strip()
    category_tokens = set(re.findall(r"[a-z0-9]+", category_text))

    def match_score(result: dict) -> tuple[int, int]:
        product_type = str(result.get("Product Type", "")).casefold().strip()
        product_tokens = set(re.findall(r"[a-z0-9]+", product_type))
        exact = 100 if product_type == category_text else 0
        containment = 40 if product_type and (product_type in category_text or category_text in product_type) else 0
        overlap = len(category_tokens & product_tokens)
        # Earlier search results win a tie because ``max`` is stable.
        return exact + containment + overlap, -results.index(result)

    return max(candidates, key=match_score)


# ============ DESIGN SYSTEM GENERATOR ============
class DesignSystemGenerator:
    """Generates design system recommendations from aggregated searches."""

    def __init__(self):
        self.reasoning_data = self._load_reasoning()

    def _load_reasoning(self) -> list:
        """Load reasoning rules from CSV."""
        filepath = DATA_DIR / REASONING_FILE
        if not filepath.exists():
            return []
        with open(filepath, 'r', encoding='utf-8') as f:
            return list(csv.DictReader(f))

    def _multi_domain_search(self, query: str, style_priority: list = None) -> dict:
        """Execute searches across multiple domains."""
        results = {}
        for domain, config in SEARCH_CONFIG.items():
            if domain == "style" and style_priority:
                # For style, also search with priority keywords
                priority_query = " ".join(style_priority[:2]) if style_priority else query
                combined_query = f"{query} {priority_query}"
                results[domain] = search(combined_query, domain, config["max_results"])
            else:
                results[domain] = search(query, domain, config["max_results"])
        return results

    def _find_reasoning_rule(self, category: str) -> dict:
        """Find matching reasoning rule for a category."""
        category_lower = category.lower()

        # Try exact match first
        for rule in self.reasoning_data:
            if rule.get("UI_Category", "").lower() == category_lower:
                return rule

        # Try partial match
        for rule in self.reasoning_data:
            ui_cat = rule.get("UI_Category", "").lower()
            if ui_cat in category_lower or category_lower in ui_cat:
                return rule

        # Try keyword match
        for rule in self.reasoning_data:
            ui_cat = rule.get("UI_Category", "").lower()
            keywords = ui_cat.replace("/", " ").replace("-", " ").split()
            if any(kw in category_lower for kw in keywords):
                return rule

        return {}

    def _apply_reasoning(self, category: str, search_results: dict) -> dict:
        """Apply reasoning rules to search results."""
        rule = self._find_reasoning_rule(category)

        if not rule:
            return {
                "pattern": "Hero + Features + CTA",
                "style_priority": ["Minimalism", "Flat Design"],
                "color_mood": "Professional",
                "typography_mood": "Clean",
                "key_effects": "Subtle hover transitions",
                "anti_patterns": "",
                "decision_rules": {},
                "severity": "MEDIUM"
            }

        # Parse decision rules JSON
        decision_rules = {}
        try:
            decision_rules = json.loads(rule.get("Decision_Rules", "{}"))
        except json.JSONDecodeError:
            pass

        return {
            "pattern": rule.get("Recommended_Pattern", ""),
            "style_priority": [s.strip() for s in rule.get("Style_Priority", "").split("+")],
            "color_mood": rule.get("Color_Mood", ""),
            "typography_mood": rule.get("Typography_Mood", ""),
            "key_effects": rule.get("Key_Effects", ""),
            "anti_patterns": rule.get("Anti_Patterns", ""),
            "decision_rules": decision_rules,
            "severity": rule.get("Severity", "MEDIUM")
        }

    def _select_best_match(self, results: list, priority_keywords: list) -> dict:
        """Select best matching result based on priority keywords."""
        if not results:
            return {}

        if not priority_keywords:
            return results[0]

        # First: try exact style name match
        for priority in priority_keywords:
            priority_lower = priority.lower().strip()
            for result in results:
                style_name = result.get("Style Category", "").lower().strip()
                if priority_lower == style_name:
                    return result

        # Second: score by keyword match in all fields
        scored = []
        for result in results:
            result_str = str(result).lower()
            score = 0
            for kw in priority_keywords:
                kw_lower = kw.lower().strip()
                # Higher score for style name match
                if kw_lower in result.get("Style Category", "").lower():
                    score += 10
                # Lower score for keyword field match
                elif kw_lower in result.get("Keywords", "").lower():
                    score += 3
                # Even lower for other field matches
                elif kw_lower in result_str:
                    score += 1
            scored.append((score, result))

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1] if scored and scored[0][0] > 0 else results[0]

    def _extract_results(self, search_result: dict) -> list:
        """Extract results list from search result dict."""
        return search_result.get("results", [])

    def generate(self, query: str, project_name: str = None,
                 variance: int = None, motion: int = None, density: int = None,
                 roundness: int = None) -> dict:
        """Generate complete design system recommendation.

        variance/motion/density/roundness are optional 1-10 dials (see
        DIAL_TIERS) that bias style selection, pull in a matching motion.csv
        snippet, and tune spacing and shape while keeping generic decorative pills outside the default system.
        """
        variance_info = _resolve_dial("variance", variance)
        motion_info = _resolve_dial("motion", motion)
        density_info = _resolve_dial("density", density)
        roundness_info = _resolve_dial("roundness", roundness)
        treatment_policy = build_visual_treatment_policy(query)
        allow_luminous = treatment_policy["allow_glow"]

        # Step 1: First search product to get category
        product_result = search(query, "product", 1)
        product_results = product_result.get("results", [])
        category = "General"
        if product_results:
            category = product_results[0].get("Product Type", "General")

        # Step 2: Get reasoning rules for this category
        reasoning = self._apply_reasoning(category, {})
        style_priority = reasoning.get("style_priority", [])

        # DESIGN_VARIANCE dial: bias style retrieval/selection toward
        # centered-minimal (low) or bold-asymmetric (high) keywords.
        effective_style_priority = style_priority
        if variance_info:
            effective_style_priority = variance_info["style_keywords"] + style_priority

        # Step 3: Multi-domain search with style priority hints
        search_results = self._multi_domain_search(query, effective_style_priority)
        search_results["product"] = product_result  # Reuse product search

        # Step 4: Select best matches from each domain using priority
        style_results = self._extract_results(search_results.get("style", {}))
        color_results = self._extract_results(search_results.get("color", {}))
        typography_results = self._extract_results(search_results.get("typography", {}))
        landing_results = self._extract_results(search_results.get("landing", {}))

        query_platform = _query_platform_mode(query)
        query_surface = _query_surface_mode(query)
        eligible_style_results = style_results
        if query_platform == "desktop":
            non_mobile_results = [
                result for result in eligible_style_results if result.get("Type", "").casefold() != "mobile"
            ]
            if non_mobile_results:
                eligible_style_results = non_mobile_results
        if query_surface == "product":
            non_landing_results = [
                result
                for result in eligible_style_results
                if result.get("Type", "").casefold() != "landing page"
            ]
            if non_landing_results:
                eligible_style_results = non_landing_results
        best_style = self._select_best_match(eligible_style_results, effective_style_priority)
        required_palette_mode = _style_palette_mode(best_style)
        palette_candidates = list(color_results)
        if required_palette_mode:
            mode_search = search(
                f"{query} {category} {required_palette_mode} theme",
                "color",
                8,
            )
            known_palettes = {
                (item.get("Product Type", ""), item.get("Background", ""))
                for item in palette_candidates
            }
            for item in mode_search.get("results", []):
                identity = (item.get("Product Type", ""), item.get("Background", ""))
                if identity not in known_palettes:
                    palette_candidates.append(item)
                    known_palettes.add(identity)
        best_color = _select_color_palette(
            palette_candidates,
            category,
            required_palette_mode,
        )
        best_typography = typography_results[0] if typography_results else {}
        best_landing = landing_results[0] if landing_results else {}

        # MOTION_INTENSITY dial: pull a matching GSAP skeleton from motion.csv
        # (domain key is "gsap", not "motion" - PR #296 already owns the "motion"
        # domain for Emil Kowalski's motion-design principles, motion-principles.csv).
        motion_snippet = {}
        if motion_info:
            motion_result = search(f"{query} {motion_info['tier']}", "gsap", 5)
            motion_matches = motion_result.get("results", [])
            tiered = [m for m in motion_matches if m.get("Intensity Tier") == motion_info["tier"]]
            if tiered:
                motion_snippet = tiered[0]
            elif motion_matches:
                motion_snippet = motion_matches[0]

        # Step 5: Build final recommendation
        # Combine effects from both reasoning and style search
        style_effects = best_style.get("Effects & Animation", "")
        reasoning_effects = reasoning.get("key_effects", "")
        combined_effects = sanitize_visual_guidance(
            style_effects if style_effects else reasoning_effects,
            allow_luminous=allow_luminous,
            allow_gradient=treatment_policy["allow_gradient"],
            allowed_gradient_roles=treatment_policy["gradient_roles"],
            allowed_luminous_roles=treatment_policy["glow_roles"],
        )

        style = {
            "name": best_style.get("Style Category", "Minimalism"),
            "type": best_style.get("Type", "General"),
            "effects": style_effects,
            "keywords": best_style.get("Keywords", ""),
            "best_for": best_style.get("Best For", ""),
            "performance": best_style.get("Performance", ""),
            "accessibility": best_style.get("Accessibility", ""),
            "light_mode": best_style.get("Light Mode ✓", ""),
            "dark_mode": best_style.get("Dark Mode ✓", ""),
        }
        colors = {
            "primary": best_color.get("Primary", "#2563EB"),
            "on_primary": best_color.get("On Primary", ""),
            "secondary": best_color.get("Secondary", "#3B82F6"),
            "on_secondary": best_color.get("On Secondary", ""),
            "accent": best_color.get("Accent", "#F97316"),
            "on_accent": best_color.get("On Accent", ""),
            "background": best_color.get("Background", "#F8FAFC"),
            "foreground": best_color.get("Foreground", "#1E293B"),
            "card": best_color.get("Card", ""),
            "card_foreground": best_color.get("Card Foreground", ""),
            "muted": best_color.get("Muted", ""),
            "muted_foreground": best_color.get("Muted Foreground", ""),
            "border": best_color.get("Border", ""),
            "destructive": best_color.get("Destructive", ""),
            "on_destructive": best_color.get("On Destructive", ""),
            "ring": best_color.get("Ring", ""),
            "notes": best_color.get("Notes", ""),
            # Keep legacy keys for backward compatibility in MASTER.md.
            "cta": best_color.get("Accent", "#F97316"),
            "text": best_color.get("Foreground", "#1E293B"),
        }
        colors, palette_adjustments = neutralize_unrequested_cool_foundation(
            colors,
            allow_cool_foundation=explicit_cool_color_request(query),
        )
        colors, color_adjustments = ensure_accessible_semantic_colors(colors)
        typography = {
            "heading": best_typography.get("Heading Font", "Inter"),
            "body": best_typography.get("Body Font", "Inter"),
            "mood": best_typography.get("Mood/Style Keywords", reasoning.get("typography_mood", "")),
            "best_for": best_typography.get("Best For", ""),
            "google_fonts_url": best_typography.get("Google Fonts URL", ""),
            "css_import": best_typography.get("CSS Import", ""),
        }

        pattern = build_experience_pattern(
            f"{query} {category}",
            best_landing,
            reasoning.get("pattern", "Hero + Proof + Action"),
        )

        is_mobile = query_platform == "mobile" or (
            query_platform is None and style.get("type", "").casefold() == "mobile"
        )
        shape_system = resolve_shape_system(
            style.get("name", ""),
            style.get("keywords", ""),
            roundness_info.get("profile") if roundness_info else None,
            context=query,
        )
        layout_context = " ".join(
            (
                query,
                category,
                pattern.get("name", ""),
                style.get("name", ""),
            )
        )
        layout_system = build_layout_system(
            layout_context,
            density_info.get("label") if density_info else None,
        )
        art_direction_gate = build_art_direction_gate(query)
        option_exploration = build_option_exploration(query)
        is_compact = bool(density_info and density_info.get("value", 0) >= 8) or any(
            marker in layout_context.casefold()
            for marker in ("dashboard", "admin", "analytics", "operations", "data-dense", "monitoring")
        )
        type_system = build_type_system(is_mobile, compact=is_compact)
        typography_director = build_typography_director(query, typography, type_system)
        creative_distinction_gate = build_creative_distinction_gate(
            query,
            category=category,
            pattern_name=pattern.get("name", ""),
            style_name=style.get("name", ""),
        )
        rendered_critic = build_rendered_critic(query)
        iconography = build_iconography(is_mobile, layout_context)
        control_sizing = build_control_sizing(is_mobile, compact=is_compact)
        component_guidance = build_component_guidance(shape_system, control_sizing)
        contrast_checks = build_contrast_checks(colors)
        anti_patterns = merge_anti_patterns(reasoning.get("anti_patterns", ""))

        return {
            "project_name": project_name or query.upper(),
            "category": category,
            "pattern": pattern,
            "style": style,
            "design_direction": {
                "intent": f"Use {style.get('name', 'the selected style')} to express {category} while keeping task hierarchy explicit",
                "composition": layout_system["composition"],
                "signature": "Choose one product-specific signature device when it adds recognition, or explicitly let content, typography, and composition carry the identity; never force ornament",
                "restraint": "Use a context-derived solid foundation when brand evidence is absent; remove unrequested glow, neon, ambient luminous gradients, inflated controls, and decorative containers without rejecting valid functional color",
            },
            "art_direction_gate": art_direction_gate,
            "option_exploration": option_exploration,
            "creative_distinction_gate": creative_distinction_gate,
            "rendered_critic": rendered_critic,
            "project_memory": build_project_memory_policy(),
            "visual_treatment_policy": treatment_policy,
            "colors": colors,
            "palette_adjustments": palette_adjustments,
            "color_adjustments": color_adjustments,
            "contrast_checks": contrast_checks,
            "typography": typography,
            "type_system": type_system,
            "typography_director": typography_director,
            "layout_system": layout_system,
            "shape_system": shape_system,
            "iconography": iconography,
            "control_sizing": control_sizing,
            "component_guidance": component_guidance,
            "key_effects": combined_effects,
            "anti_patterns": anti_patterns,
            "quality_gates": build_quality_gates(),
            "standards": [dict(item) for item in STANDARDS_BASELINE],
            "decision_rules": reasoning.get("decision_rules", {}),
            "severity": reasoning.get("severity", "MEDIUM"),
            "dials": {
                "variance": variance_info["value"] if variance_info else None,
                "variance_label": variance_info["label"] if variance_info else None,
                "motion": motion_info["value"] if motion_info else None,
                "motion_label": motion_info["label"] if motion_info else None,
                "density": density_info["value"] if density_info else None,
                "density_label": density_info["label"] if density_info else None,
                "roundness": roundness_info["value"] if roundness_info else None,
                "roundness_label": roundness_info["label"] if roundness_info else None,
            },
            "motion_snippet": motion_snippet,
            "spacing_scale": density_info["spacing"] if density_info else None,
        }


# ============ OUTPUT FORMATTERS ============
BOX_WIDTH = 90  # Wider box for more content


def hex_to_ansi(hex_color: str) -> str:
    """Convert hex color to ANSI True Color swatch (██) with fallback."""
    if not hex_color or not hex_color.startswith('#'):
        return ""
    colorterm = os.environ.get('COLORTERM', '')
    if colorterm not in ('truecolor', '24bit'):
        return ""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6:
        return ""
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"\033[38;2;{r};{g};{b}m██\033[0m "


def ansi_ljust(s: str, width: int) -> str:
    """Like str.ljust but accounts for zero-width ANSI escape sequences."""
    import re
    visible_len = len(re.sub(r'\033\[[0-9;]*m', '', s))
    pad = width - visible_len
    return s + (" " * max(0, pad))


def section_header(name: str, width: int) -> str:
    """Create a Unicode section separator: ├─── NAME ───...┤"""
    label = f"─── {name} "
    fill = "─" * (width - len(label) - 1)
    return f"├{label}{fill}┤"


def _append_art_direction_gate_markdown(lines: list[str], gate: dict) -> None:
    """Append the evidence-first art-direction protocol to markdown output."""
    if not gate:
        return
    lines.append("### Art Direction Gate")
    lines.append("")
    lines.append(f"- **Mode:** {gate.get('mode', '')}")
    lines.append(f"- **Initial status:** {gate.get('initial_status', '')}")
    lines.append(f"- **Allowed statuses:** `{gate.get('status_vocabulary', '')}`")
    lines.append(f"- **Concept set:** {gate.get('candidate_policy', '')}")
    lines.append(f"- **Distinctness:** {gate.get('distinctness_rule', '')}")
    lines.append("")
    lines.append("#### Critic dimensions")
    lines.append("")
    for dimension in gate.get("review_dimensions", []):
        lines.append(f"- {dimension}")
    lines.append("")
    lines.append(f"- **Evidence rule:** {gate.get('evidence_rule', '')}")
    lines.append(f"- **Selection rule:** {gate.get('selection_rule', '')}")
    lines.append(f"- **Implementation contract:** {gate.get('implementation_contract', '')}")
    lines.append(f"- **Rendered review:** {gate.get('render_review', '')}")
    lines.append(f"- **Stop rule:** {gate.get('stop_rule', '')}")
    lines.append("")


def _append_option_exploration_markdown(lines: list[str], exploration: dict) -> None:
    """Append the always-on material-decision exploration contract."""
    if not exploration:
        return
    lines.append("### Explore → Compare → Commit")
    lines.append("")
    lines.append(f"- **Mode:** {exploration.get('mode', '')}")
    lines.append(f"- **Principle:** {exploration.get('principle', '')}")
    lines.append(f"- **Scope boundary:** {exploration.get('scope_boundary', '')}")
    lines.append(f"- **Context:** {exploration.get('context_snapshot', '')}")
    lines.append("")
    lines.append("#### Phase order")
    lines.append("")
    for index, step in enumerate(exploration.get("sequence", []), 1):
        lines.append(f"{index}. {step}")
    lines.append("")
    lines.append("#### Domain coverage")
    lines.append("")
    lines.append("| Domain | Relevant-space coverage | Comparison proof |")
    lines.append("|---|---|---|")
    for item in exploration.get("domains", []):
        lines.append(f"| {item.get('domain', '')} | {item.get('coverage', '')} | {item.get('proof', '')} |")
    lines.append("")
    lines.append(f"- **Closure rule:** {exploration.get('closure_rule', '')}")
    lines.append(f"- **Evidence record:** `{exploration.get('record', '')}`")
    for shortcut in exploration.get("anti_shortcuts", []):
        lines.append(f"- **Forbidden shortcut:** {shortcut}")
    lines.append("")


def _append_creative_distinction_markdown(lines: list[str], gate: dict) -> None:
    """Append the product-specific identity gate without forcing ornament."""
    if not gate:
        return
    lines.append("### Creative Distinction Gate")
    lines.append("")
    lines.append(f"- **Mode:** {gate.get('mode', '')}")
    lines.append(f"- **Initial status:** {gate.get('initial_status', '')}")
    lines.append(f"- **Product anchor:** {gate.get('product_anchor', '')}")
    lines.append(f"- **Ownable move:** {gate.get('ownable_move', '')}")
    lines.append(f"- **Context:** {gate.get('context_snapshot', '')}")
    lines.append("")
    if gate.get("candidate_carriers"):
        lines.append("#### Candidate identity carriers")
        lines.append("")
        for carrier in gate.get("candidate_carriers", []):
            lines.append(f"- {carrier}")
        lines.append("")
    if gate.get("template_risks"):
        lines.append("#### Template-resemblance risks")
        lines.append("")
        for risk in gate.get("template_risks", []):
            lines.append(f"- {risk}")
        lines.append("")
    for question in gate.get("proof_questions", []):
        lines.append(f"- **Proof question:** {question}")
    lines.append(f"- **Pass rule:** {gate.get('pass_rule', '')}")
    lines.append(f"- **Subtraction test:** {gate.get('subtraction_test', '')}")
    lines.append("")


def _append_typography_director_markdown(lines: list[str], director: dict) -> None:
    """Append content-, script-, and metric-aware typography guidance."""
    if not director:
        return
    lines.append("#### Typography Director")
    lines.append("")
    lines.append(f"- **Initial status:** {director.get('initial_status', '')}")
    lines.append(f"- **Proposed pair:** {director.get('proposed_pair', '')}")
    lines.append(f"- **Required scripts:** {director.get('script_requirements', '')}")
    lines.append(f"- **Writing direction:** {director.get('direction_policy', '')}")
    lines.append(f"- **Content modes:** {', '.join(director.get('content_modes', []))}")
    lines.append(f"- **Font-count policy:** {director.get('font_count_policy', '')}")
    lines.append(f"- **Fallback policy:** {director.get('fallback_policy', '')}")
    lines.append("")
    for role, guidance in director.get("role_contract", {}).items():
        lines.append(f"- **{role.replace('_', ' ').title()}:** {guidance}")
    if director.get("stress_content"):
        lines.append("")
        lines.append("**Stress content**")
        lines.append("")
        for item in director.get("stress_content", []):
            lines.append(f"- {item}")
    if director.get("verification"):
        lines.append("")
        lines.append("**Verification**")
        lines.append("")
        for item in director.get("verification", []):
            lines.append(f"- {item}")
    lines.append("")


def _append_scoped_treatments_markdown(lines: list[str], policy: dict, shape_system: dict) -> None:
    """Append only explicitly scoped visual-treatment exceptions."""
    explicit_treatment = policy and (policy.get("allow_gradient") or policy.get("allow_glow"))
    shape_exceptions = shape_system.get("approved_exceptions", []) if shape_system else []
    if not explicit_treatment and not shape_exceptions:
        return
    lines.append("### Approved Visual Exceptions")
    lines.append("")
    if policy.get("allow_gradient"):
        lines.append(f"- **Gradient roles:** {', '.join(policy.get('gradient_roles', []))}")
    if policy.get("allow_glow"):
        lines.append(f"- **Glow/neon roles:** {', '.join(policy.get('glow_roles', []))}")
    for exception in shape_exceptions:
        lines.append(f"- **Full-rounding exception:** {exception}")
    if policy:
        lines.append(f"- **Scope rule:** {policy.get('scope_rule', '')}")
    lines.append("")


def _append_rendered_critic_markdown(lines: list[str], critic: dict) -> None:
    """Append the bounded screenshot critic and correction loop."""
    if not critic:
        return
    lines.append("### Rendered Critic Loop")
    lines.append("")
    lines.append(f"- **Initial status:** {critic.get('initial_status', '')}")
    lines.append(f"- **Baseline:** {critic.get('baseline', '')}")
    lines.append(f"- **Finding schema:** `{critic.get('finding_schema', '')}`")
    lines.append(f"- **Severity:** {critic.get('severity_rule', '')}")
    lines.append("")
    lines.append("#### Required evidence")
    lines.append("")
    for item in critic.get("required_evidence", []):
        lines.append(f"- {item}")
    lines.append("")
    lines.append("#### Critic lenses")
    lines.append("")
    for lens in critic.get("lenses", []):
        lines.append(f"- **{lens.get('name', '')}:** {lens.get('inspect', '')}")
    lines.append("")
    lines.append("#### Bounded correction workflow")
    lines.append("")
    for index, item in enumerate(critic.get("workflow", []), 1):
        lines.append(f"{index}. {item}")
    lines.append("")
    lines.append(f"- **Stop rule:** {critic.get('stop_rule', '')}")
    lines.append(f"- **Anti-loop:** {critic.get('anti_loop', '')}")
    lines.append("")


def _append_project_memory_policy_markdown(lines: list[str], memory: dict) -> None:
    """Append the durable project-memory contract."""
    if not memory:
        return
    lines.append("### Project Design Memory")
    lines.append("")
    lines.append(f"- **File:** `{memory.get('file', 'PROJECT-MEMORY.md')}`")
    lines.append(f"- **Statuses:** `{memory.get('statuses', '')}`")
    lines.append(f"- **Read rule:** {memory.get('read_rule', '')}")
    lines.append(f"- **Write rule:** {memory.get('write_rule', '')}")
    lines.append(f"- **Precedence:** {memory.get('precedence', '')}")
    lines.append(f"- **Scope:** {memory.get('scope_rule', '')}")
    lines.append("")


def _append_iconography_markdown(lines: list[str], iconography: dict) -> None:
    """Append the full role-first icon policy to a markdown document."""
    lines.append("### Iconography")
    lines.append("")
    lines.append(f"- **Visual size:** {iconography.get('visual_size', '')}")
    lines.append(f"- **Interaction target:** {iconography.get('target_size', '')}")
    lines.append(f"- **Container:** {iconography.get('container', '')}")
    lines.append(f"- **Source strategy:** {iconography.get('family_strategy', '')}")
    if iconography.get("established_family"):
        lines.append(f"- **Likely primary repository source:** {iconography.get('established_family', '')} (confirm from the source-role map)")
    if iconography.get("established_sources"):
        lines.append(f"- **Observed repository sources:** {', '.join(iconography.get('established_sources', []))}")
    if iconography.get("source_policy"):
        lines.append(f"- **Evaluation policy:** {iconography.get('source_policy', '')}")
    if iconography.get("decision_record"):
        lines.append(f"- **Required product-icon decision record:** {iconography.get('decision_record', '')}")
    lines.append("")

    candidates = iconography.get("family_candidates", [])
    if candidates:
        if iconography.get("established_sources"):
            lines.append("#### Source shortlist — observed sources and installable challengers")
        else:
            lines.append("#### Installable primary-source candidates — choose a drawing language before acquisition")
        lines.append("")
        for candidate in candidates:
            status = candidate.get("status", "candidate")
            lines.append(f"- **{candidate.get('family', '')}** — `{status}`: {candidate.get('reason', '')}")
        lines.append("")

    exploration_gate = iconography.get("exploration_gate", {})
    if exploration_gate:
        lines.append("#### Cross-library exploration closure gate")
        lines.append("")
        lines.append(f"- **Mode:** {exploration_gate.get('mode', '')}")
        lines.append(f"- **Promotion triggers:** {exploration_gate.get('promotion_triggers', '')}")
        lines.append(f"- **Early-stop rule:** {exploration_gate.get('early_stop_rule', '')}")
        lines.append("")
        lines.append("**Required closure evidence**")
        lines.append("")
        for rule in exploration_gate.get("closure_evidence", []):
            lines.append(f"- {rule}")
        lines.append("")
        lines.append("**Decision phases**")
        lines.append("")
        for index, phase in enumerate(exploration_gate.get("decision_phases", []), 1):
            lines.append(f"{index}. {phase}")
        lines.append("")

    role_rules = iconography.get("role_rules", {})
    if role_rules:
        lines.append("#### Role and metaphor policy")
        lines.append("")
        for role, guidance in role_rules.items():
            lines.append(f"- **{role.replace('_', ' ').title()}:** {guidance}")
        lines.append("")

    selection_order = iconography.get("selection_order", [])
    if selection_order:
        lines.append("#### Selection order")
        lines.append("")
        for index, rule in enumerate(selection_order, 1):
            lines.append(f"{index}. {rule}")
        lines.append("")

    dependency_acquisition = iconography.get("dependency_acquisition", {})
    if dependency_acquisition:
        lines.append("#### Dependency acquisition gate")
        lines.append("")
        lines.append(f"- **Authority:** {dependency_acquisition.get('authority', '')}")
        lines.append(f"- **Selection rule:** {dependency_acquisition.get('selection_rule', '')}")
        lines.append("")
        lines.append("**Verify before installation**")
        lines.append("")
        for rule in dependency_acquisition.get("verification", []):
            lines.append(f"- {rule}")
        lines.append("")
        lines.append("**Install, integrate, and verify**")
        lines.append("")
        for index, rule in enumerate(dependency_acquisition.get("installation", []), 1):
            lines.append(f"{index}. {rule}")
        lines.append("")
        lines.append(f"- **Stop conditions:** {dependency_acquisition.get('stop_conditions', '')}")
        lines.append("")

    cliche_guard = iconography.get("cliche_guard", [])
    if cliche_guard:
        lines.append("#### Anti-cliche guard")
        lines.append("")
        for item in cliche_guard:
            guidance = f"- **{item.get('concept', '')}:** avoid as an automatic default: {item.get('avoid', '')}; prefer {item.get('prefer', '')}."
            if item.get("allowed"):
                guidance += f" Allowed when {item.get('allowed', '')}."
            lines.append(guidance)
        lines.append("")

    compatibility_gate = iconography.get("compatibility_gate", [])
    if compatibility_gate:
        lines.append("#### Multi-source compatibility gate")
        lines.append("")
        for rule in compatibility_gate:
            lines.append(f"- {rule}")
        lines.append("")

    custom_icon_gate = iconography.get("custom_icon_gate", [])
    if custom_icon_gate:
        lines.append("#### Missing-glyph and custom-SVG gate")
        lines.append("")
        for rule in custom_icon_gate:
            lines.append(f"- {rule}")
        lines.append("")

    normalization = iconography.get("normalization", {})
    if normalization:
        lines.append("#### Normalization")
        lines.append("")
        for token, guidance in normalization.items():
            lines.append(f"- **{token.title()}:** {guidance}")
        lines.append("")

    for rule in iconography.get("rules", []):
        lines.append(f"- {rule}")
    lines.append("")


def format_ascii_box(design_system: dict) -> str:
    """Format design system as Unicode box with ANSI color swatches."""
    project = design_system.get("project_name", "PROJECT")
    pattern = design_system.get("pattern", {})
    style = design_system.get("style", {})
    colors = design_system.get("colors", {})
    typography = design_system.get("typography", {})
    type_system = design_system.get("type_system", {})
    typography_director = design_system.get("typography_director", {})
    design_direction = design_system.get("design_direction", {})
    option_exploration = design_system.get("option_exploration", {})
    art_direction_gate = design_system.get("art_direction_gate", {})
    creative_distinction_gate = design_system.get("creative_distinction_gate", {})
    rendered_critic = design_system.get("rendered_critic", {})
    project_memory = design_system.get("project_memory", {})
    visual_treatment_policy = design_system.get("visual_treatment_policy", {})
    layout_system = design_system.get("layout_system", {})
    shape_system = design_system.get("shape_system", {})
    iconography = design_system.get("iconography", {})
    control_sizing = design_system.get("control_sizing", {})
    palette_adjustments = design_system.get("palette_adjustments", [])
    color_adjustments = design_system.get("color_adjustments", [])
    contrast_checks = design_system.get("contrast_checks", [])
    effects = design_system.get("key_effects", "")
    anti_patterns = split_guidance(design_system.get("anti_patterns", []))
    dials = design_system.get("dials", {})
    motion_snippet = design_system.get("motion_snippet", {})

    def wrap_text(text: str, prefix: str, width: int) -> list:
        """Wrap long text into multiple lines."""
        if not text:
            return []
        words = text.split()
        lines = []
        current_line = prefix
        for word in words:
            if len(current_line) + len(word) + 1 <= width - 2:
                current_line += (" " if current_line != prefix else "") + word
            else:
                if current_line != prefix:
                    lines.append(current_line)
                current_line = prefix + word
        if current_line != prefix:
            lines.append(current_line)
        return lines

    # Build sections from pattern
    sections = pattern.get("sections", "").split(">")
    sections = [s.strip() for s in sections if s.strip()]

    # Build output lines
    lines = []
    w = BOX_WIDTH - 1

    # Header with double-line box
    lines.append("╔" + "═" * w + "╗")
    lines.append(ansi_ljust(f"║  TARGET: {project} - RECOMMENDED DESIGN SYSTEM", BOX_WIDTH) + "║")
    lines.append("╚" + "═" * w + "╝")
    lines.append("┌" + "─" * w + "┐")

    # Design Dials section (only if at least one dial was set)
    if any(dials.get(k) is not None for k in ("variance", "motion", "density", "roundness")):
        lines.append(section_header("DESIGN DIALS", BOX_WIDTH + 1))
        if dials.get("variance") is not None:
            lines.append(f"│  Variance: {dials['variance']}/10 — {dials['variance_label']}".ljust(BOX_WIDTH) + "│")
        if dials.get("motion") is not None:
            lines.append(f"│  Motion:   {dials['motion']}/10 — {dials['motion_label']}".ljust(BOX_WIDTH) + "│")
        if dials.get("density") is not None:
            lines.append(f"│  Density:  {dials['density']}/10 — {dials['density_label']}".ljust(BOX_WIDTH) + "│")
        if dials.get("roundness") is not None:
            lines.append(f"│  Roundness:{dials['roundness']}/10 — {dials['roundness_label']}".ljust(BOX_WIDTH) + "│")

    # Pattern section
    lines.append(section_header("PATTERN", BOX_WIDTH + 1))
    lines.append(f"│  Name: {pattern.get('name', '')}".ljust(BOX_WIDTH) + "│")
    if pattern.get('conversion'):
        lines.append(f"│     Conversion: {pattern.get('conversion', '')}".ljust(BOX_WIDTH) + "│")
    if pattern.get('cta_placement'):
        lines.append(f"│     CTA: {pattern.get('cta_placement', '')}".ljust(BOX_WIDTH) + "│")
    lines.append("│     Sections:".ljust(BOX_WIDTH) + "│")
    for i, section in enumerate(sections, 1):
        lines.append(f"│       {i}. {section}".ljust(BOX_WIDTH) + "│")

    # Style section
    lines.append(section_header("STYLE", BOX_WIDTH + 1))
    lines.append(f"│  Name: {style.get('name', '')}".ljust(BOX_WIDTH) + "│")
    light = style.get("light_mode", "")
    dark = style.get("dark_mode", "")
    if light or dark:
        lines.append(f"│     Mode Support: Light {light}  Dark {dark}".ljust(BOX_WIDTH) + "│")
    if style.get("keywords"):
        for line in wrap_text(f"Keywords: {style.get('keywords', '')}", "│     ", BOX_WIDTH):
            lines.append(line.ljust(BOX_WIDTH) + "│")
    if style.get("best_for"):
        for line in wrap_text(f"Best For: {style.get('best_for', '')}", "│     ", BOX_WIDTH):
            lines.append(line.ljust(BOX_WIDTH) + "│")
    if style.get("performance") or style.get("accessibility"):
        perf_a11y = f"Performance note: {style.get('performance', '')} | Accessibility note: {style.get('accessibility', '')}"
        lines.append(f"│     {perf_a11y}".ljust(BOX_WIDTH) + "│")

    # Design direction and composition
    lines.append(section_header("DESIGN DIRECTION", BOX_WIDTH + 1))
    for key in ("intent", "composition", "signature", "restraint"):
        if design_direction.get(key):
            label = key.replace("_", " ").title()
            for line in wrap_text(f"{label}: {design_direction[key]}", "│     ", BOX_WIDTH):
                lines.append(line.ljust(BOX_WIDTH) + "│")

    # Art-direction selection protocol
    if option_exploration:
        lines.append(section_header("OPTION EXPLORATION", BOX_WIDTH + 1))
        for label, key in (
            ("Mode", "mode"),
            ("Principle", "principle"),
            ("Scope", "scope_boundary"),
            ("Closure", "closure_rule"),
        ):
            if option_exploration.get(key):
                for line in wrap_text(f"{label}: {option_exploration[key]}", "│     ", BOX_WIDTH):
                    lines.append(line.ljust(BOX_WIDTH) + "│")

    if art_direction_gate:
        lines.append(section_header("ART DIRECTION GATE", BOX_WIDTH + 1))
        for label, key in (
            ("Mode", "mode"),
            ("Initial status", "initial_status"),
            ("Concept set", "candidate_policy"),
            ("Selection", "selection_rule"),
            ("Contract", "implementation_contract"),
        ):
            if art_direction_gate.get(key):
                for line in wrap_text(f"{label}: {art_direction_gate[key]}", "│     ", BOX_WIDTH):
                    lines.append(line.ljust(BOX_WIDTH) + "│")

    if creative_distinction_gate:
        lines.append(section_header("CREATIVE DISTINCTION", BOX_WIDTH + 1))
        for label, key in (
            ("Mode", "mode"),
            ("Initial status", "initial_status"),
            ("Product anchor", "product_anchor"),
            ("Ownable move", "ownable_move"),
            ("Pass rule", "pass_rule"),
        ):
            if creative_distinction_gate.get(key):
                for line in wrap_text(f"{label}: {creative_distinction_gate[key]}", "│     ", BOX_WIDTH):
                    lines.append(line.ljust(BOX_WIDTH) + "│")

    # Layout foundation
    lines.append(section_header("LAYOUT", BOX_WIDTH + 1))
    for label, key in (
        ("Max width", "max_width"),
        ("Grid", "grid"),
        ("Gutters", "gutters"),
        ("Text measure", "content_measure"),
        ("Responsive QA", "breakpoints"),
    ):
        if layout_system.get(key):
            for line in wrap_text(f"{label}: {layout_system[key]}", "│     ", BOX_WIDTH):
                lines.append(line.ljust(BOX_WIDTH) + "│")

    # Shape and icon treatment
    lines.append(section_header("SHAPE & ICONS", BOX_WIDTH + 1))
    if shape_system:
        lines.append(f"│  Shape: {shape_system.get('label', '')}".ljust(BOX_WIDTH) + "│")
        tokens = shape_system.get("tokens", {})
        token_summary = " | ".join(
            f"{key} {tokens.get(key)}" for key in ("control", "card", "overlay", "chip") if tokens.get(key)
        )
        for line in wrap_text(f"Radii: {token_summary}", "│     ", BOX_WIDTH):
            lines.append(line.ljust(BOX_WIDTH) + "│")
        for line in wrap_text(f"Pill policy: {shape_system.get('pill_policy', '')}", "│     ", BOX_WIDTH):
            lines.append(line.ljust(BOX_WIDTH) + "│")
        for exception in shape_system.get("approved_exceptions", []):
            for line in wrap_text(f"Approved full-rounding exception: {exception}", "│     ", BOX_WIDTH):
                lines.append(line.ljust(BOX_WIDTH) + "│")
    if visual_treatment_policy.get("allow_gradient") or visual_treatment_policy.get("allow_glow"):
        scoped = []
        if visual_treatment_policy.get("allow_gradient"):
            scoped.append(f"gradient={','.join(visual_treatment_policy.get('gradient_roles', []))}")
        if visual_treatment_policy.get("allow_glow"):
            scoped.append(f"glow={','.join(visual_treatment_policy.get('glow_roles', []))}")
        for line in wrap_text(f"Scoped visual treatments: {' | '.join(scoped)}", "│     ", BOX_WIDTH):
            lines.append(line.ljust(BOX_WIDTH) + "│")
    if iconography.get("container"):
        for line in wrap_text(f"Icon containers: {iconography['container']}", "│     ", BOX_WIDTH):
            lines.append(line.ljust(BOX_WIDTH) + "│")
    if iconography.get("family_strategy"):
        for line in wrap_text(f"Source decision: {iconography['family_strategy']}", "│     ", BOX_WIDTH):
            lines.append(line.ljust(BOX_WIDTH) + "│")
    if iconography.get("established_family"):
        for line in wrap_text(
            f"Likely primary source: {iconography['established_family']} (confirm repository role map)",
            "│     ",
            BOX_WIDTH,
        ):
            lines.append(line.ljust(BOX_WIDTH) + "│")
    if iconography.get("established_sources"):
        for line in wrap_text(
            f"Observed sources: {', '.join(iconography['established_sources'])}",
            "│     ",
            BOX_WIDTH,
        ):
            lines.append(line.ljust(BOX_WIDTH) + "│")
    if iconography.get("decision_record"):
        for line in wrap_text(f"Product-icon record: {iconography['decision_record']}", "│     ", BOX_WIDTH):
            lines.append(line.ljust(BOX_WIDTH) + "│")
    if iconography.get("family_candidates"):
        family_names = ", ".join(item.get("family", "") for item in iconography["family_candidates"])
        family_label = "Observed sources + installable challengers" if iconography.get("established_sources") else "Installable primary-source candidates"
        for line in wrap_text(f"{family_label}: {family_names}", "│     ", BOX_WIDTH):
            lines.append(line.ljust(BOX_WIDTH) + "│")
    exploration_gate = iconography.get("exploration_gate", {})
    if exploration_gate:
        for line in wrap_text(f"Icon exploration: {exploration_gate.get('mode', '')}", "│     ", BOX_WIDTH):
            lines.append(line.ljust(BOX_WIDTH) + "│")
        for line in wrap_text(f"Exploration stop rule: {exploration_gate.get('early_stop_rule', '')}", "│     ", BOX_WIDTH):
            lines.append(line.ljust(BOX_WIDTH) + "│")
    dependency_acquisition = iconography.get("dependency_acquisition", {})
    if dependency_acquisition:
        for line in wrap_text(
            f"Dependency action: {dependency_acquisition.get('authority', '')}",
            "│     ",
            BOX_WIDTH,
        ):
            lines.append(line.ljust(BOX_WIDTH) + "│")
    if iconography.get("cliche_guard"):
        for line in wrap_text(
            "Metaphor guard: generic AI, rocket, shield, globe, puzzle, cube, chart, trophy, star, and gear shortcuts require literal, learned, branded, or recognition-tested justification",
            "│     ",
            BOX_WIDTH,
        ):
            lines.append(line.ljust(BOX_WIDTH) + "│")
    if control_sizing:
        for label, key in (
            ("Control scale", "mode"),
            ("Visible height", "control_height"),
            ("Icon controls", "icon_control"),
            ("Width", "width"),
        ):
            for line in wrap_text(f"{label}: {control_sizing.get(key, '')}", "│     ", BOX_WIDTH):
                lines.append(line.ljust(BOX_WIDTH) + "│")

    # Colors section (extended palette with ANSI swatches)
    lines.append(section_header("COLORS", BOX_WIDTH + 1))
    color_entries = [
        ("Primary",      "primary",      "--color-primary"),
        ("On Primary",   "on_primary",   "--color-on-primary"),
        ("Secondary",    "secondary",    "--color-secondary"),
        ("On Secondary", "on_secondary", "--color-on-secondary"),
        ("Accent/CTA",   "accent",       "--color-accent"),
        ("On Accent",    "on_accent",    "--color-on-accent"),
        ("Background",   "background",   "--color-background"),
        ("Foreground",   "foreground",   "--color-foreground"),
        ("Card",         "card",         "--color-card"),
        ("Card Text",    "card_foreground", "--color-card-foreground"),
        ("Muted",        "muted",        "--color-muted"),
        ("Muted Text",   "muted_foreground", "--color-muted-foreground"),
        ("Border",       "border",       "--color-border"),
        ("Destructive",  "destructive",  "--color-destructive"),
        ("On Destruct.",  "on_destructive", "--color-on-destructive"),
        ("Ring",         "ring",         "--color-ring"),
    ]
    for label, key, css_var in color_entries:
        hex_val = colors.get(key, "")
        if not hex_val:
            continue
        swatch = hex_to_ansi(hex_val)
        content = f"│     {swatch}{label + ':':14s} {hex_val:10s} ({css_var})"
        lines.append(ansi_ljust(content, BOX_WIDTH) + "│")
    if colors.get("notes"):
        for line in wrap_text(f"Notes: {colors.get('notes', '')}", "│     ", BOX_WIDTH):
            lines.append(line.ljust(BOX_WIDTH) + "│")
    if palette_adjustments:
        lines.append("│     Applied palette de-templating:".ljust(BOX_WIDTH) + "│")
        for adjustment in palette_adjustments:
            summary = f"{adjustment['token']}: {adjustment['from']} → {adjustment['to']} — {adjustment['reason']}"
            for line in wrap_text(summary, "│       ", BOX_WIDTH):
                lines.append(line.ljust(BOX_WIDTH) + "│")
    if color_adjustments:
        lines.append("│     Applied semantic color adjustments:".ljust(BOX_WIDTH) + "│")
        for adjustment in color_adjustments:
            summary = (
                f"{adjustment['token']}: {adjustment['from']} → {adjustment['to']} "
                f"({adjustment['ratio']}:1 against {adjustment['against']}; target {adjustment['target']}:1)"
            )
            for line in wrap_text(summary, "│       ", BOX_WIDTH):
                lines.append(line.ljust(BOX_WIDTH) + "│")
    if contrast_checks:
        lines.append("│     Contrast checks:".ljust(BOX_WIDTH) + "│")
        for check in contrast_checks:
            text = f"{check['status']} {check['pair']}: {check['ratio']}:1 (target {check['threshold']}:1)"
            lines.append(f"│       {text}".ljust(BOX_WIDTH) + "│")
            if check.get("suggestion"):
                for line in wrap_text(f"Action: {check['suggestion']}", "│         ", BOX_WIDTH):
                    lines.append(line.ljust(BOX_WIDTH) + "│")

    # Typography section
    lines.append(section_header("TYPOGRAPHY", BOX_WIDTH + 1))
    lines.append(f"│  {typography.get('heading', '')} / {typography.get('body', '')}".ljust(BOX_WIDTH) + "│")
    if typography.get("mood"):
        for line in wrap_text(f"Mood: {typography.get('mood', '')}", "│     ", BOX_WIDTH):
            lines.append(line.ljust(BOX_WIDTH) + "│")
    if typography.get("best_for"):
        for line in wrap_text(f"Best For: {typography.get('best_for', '')}", "│     ", BOX_WIDTH):
            lines.append(line.ljust(BOX_WIDTH) + "│")
    if typography.get("google_fonts_url"):
        lines.append(f"│     Google Fonts: {typography.get('google_fonts_url', '')}".ljust(BOX_WIDTH) + "│")
    if typography.get("css_import"):
        lines.append(f"│     CSS Import: {typography.get('css_import', '')[:70]}...".ljust(BOX_WIDTH) + "│")
    for role, value in type_system.get("tokens", {}).items():
        lines.append(f"│     {role:8s} {value}".ljust(BOX_WIDTH) + "│")
    if typography_director:
        for label, key in (
            ("Director status", "initial_status"),
            ("Scripts", "script_requirements"),
            ("Direction", "direction_policy"),
            ("Content modes", "content_modes"),
            ("Fallback", "fallback_policy"),
        ):
            value = typography_director.get(key, "")
            if isinstance(value, list):
                value = ", ".join(value)
            if value:
                for line in wrap_text(f"{label}: {value}", "│     ", BOX_WIDTH):
                    lines.append(line.ljust(BOX_WIDTH) + "│")

    # Key Effects section
    if effects:
        lines.append(section_header("KEY EFFECTS", BOX_WIDTH + 1))
        for line in wrap_text(effects, "│     ", BOX_WIDTH):
            lines.append(line.ljust(BOX_WIDTH) + "│")

    # Motion section (GSAP skeleton, only if --motion dial was set)
    if motion_snippet:
        lines.append(section_header("MOTION", BOX_WIDTH + 1))
        lines.append(f"│  {motion_snippet.get('Category', '')} ({motion_snippet.get('Intensity Tier', '')})".ljust(BOX_WIDTH) + "│")
        lines.append(f"│     Trigger: {motion_snippet.get('Trigger', '')} | Duration: {motion_snippet.get('Duration', '')} | Easing: {motion_snippet.get('Easing', '')}".ljust(BOX_WIDTH) + "│")
        for line in wrap_text(f"GSAP: {motion_snippet.get('GSAP Snippet', '')}", "│     ", BOX_WIDTH):
            lines.append(line.ljust(BOX_WIDTH) + "│")
        if motion_snippet.get("Framework Notes"):
            for line in wrap_text(f"Framework: {motion_snippet.get('Framework Notes', '')}", "│     ", BOX_WIDTH):
                lines.append(line.ljust(BOX_WIDTH) + "│")

    # Anti-patterns section
    if anti_patterns:
        lines.append(section_header("AVOID", BOX_WIDTH + 1))
        for anti_pattern in anti_patterns:
            for line in wrap_text(f"- {anti_pattern}", "│     ", BOX_WIDTH):
                lines.append(line.ljust(BOX_WIDTH) + "│")

    if rendered_critic:
        lines.append(section_header("RENDERED CRITIC", BOX_WIDTH + 1))
        for label, key in (
            ("Initial status", "initial_status"),
            ("Baseline", "baseline"),
            ("Stop rule", "stop_rule"),
        ):
            if rendered_critic.get(key):
                for line in wrap_text(f"{label}: {rendered_critic[key]}", "│     ", BOX_WIDTH):
                    lines.append(line.ljust(BOX_WIDTH) + "│")
    if project_memory:
        lines.append(section_header("PROJECT MEMORY", BOX_WIDTH + 1))
        for label, key in (("File", "file"), ("Read", "read_rule"), ("Write", "write_rule")):
            if project_memory.get(key):
                for line in wrap_text(f"{label}: {project_memory[key]}", "│     ", BOX_WIDTH):
                    lines.append(line.ljust(BOX_WIDTH) + "│")

    # Pre-Delivery Checklist section
    lines.append(section_header("PRE-DELIVERY CHECKLIST", BOX_WIDTH + 1))
    checklist_items = [
        "[ ] No decorative pills behind icons or navigation items",
        "[ ] Icon sources have documented roles and render as one coherent drawing language where they appear together",
        "[ ] Product icons describe the real object, mechanism, input, output, or consequence",
        "[ ] Package counts, token spellings, raw hues, and exact pixel values were treated as diagnostic signals rather than automatic failures",
        "[ ] Text contrast checks pass or failing pairs are corrected",
        "[ ] Focus-visible, keyboard order, and accessible names verified",
        "[ ] Reduced motion and text scaling verified",
        "[ ] Real UI inspected at narrow, intermediate, and wide widths",
    ]
    for item in checklist_items:
        lines.append(f"│     {item}".ljust(BOX_WIDTH) + "│")

    lines.append("└" + "─" * w + "┘")

    return "\n".join(lines)


def format_markdown(design_system: dict) -> str:
    """Format design system as markdown."""
    project = design_system.get("project_name", "PROJECT")
    pattern = design_system.get("pattern", {})
    style = design_system.get("style", {})
    colors = design_system.get("colors", {})
    typography = design_system.get("typography", {})
    type_system = design_system.get("type_system", {})
    typography_director = design_system.get("typography_director", {})
    design_direction = design_system.get("design_direction", {})
    option_exploration = design_system.get("option_exploration", {})
    art_direction_gate = design_system.get("art_direction_gate", {})
    creative_distinction_gate = design_system.get("creative_distinction_gate", {})
    rendered_critic = design_system.get("rendered_critic", {})
    project_memory = design_system.get("project_memory", {})
    visual_treatment_policy = design_system.get("visual_treatment_policy", {})
    layout_system = design_system.get("layout_system", {})
    shape_system = design_system.get("shape_system", {})
    iconography = design_system.get("iconography", {})
    component_guidance = design_system.get("component_guidance", {})
    control_sizing = design_system.get("control_sizing", {})
    palette_adjustments = design_system.get("palette_adjustments", [])
    color_adjustments = design_system.get("color_adjustments", [])
    contrast_checks = design_system.get("contrast_checks", [])
    effects = design_system.get("key_effects", "")
    anti_patterns = split_guidance(design_system.get("anti_patterns", []))
    quality_gates = design_system.get("quality_gates", [])
    dials = design_system.get("dials", {})
    motion_snippet = design_system.get("motion_snippet", {})

    lines = []
    lines.append(f"## Design System: {project}")
    lines.append("")

    # Design Dials section (only if at least one dial was set)
    if any(dials.get(k) is not None for k in ("variance", "motion", "density", "roundness")):
        lines.append("### Design Dials")
        if dials.get("variance") is not None:
            lines.append(f"- **Variance:** {dials['variance']}/10 — {dials['variance_label']}")
        if dials.get("motion") is not None:
            lines.append(f"- **Motion:** {dials['motion']}/10 — {dials['motion_label']}")
        if dials.get("density") is not None:
            lines.append(f"- **Density:** {dials['density']}/10 — {dials['density_label']}")
        if dials.get("roundness") is not None:
            lines.append(f"- **Roundness:** {dials['roundness']}/10 — {dials['roundness_label']}")
        lines.append("")

    # Pattern section
    lines.append("### Pattern")
    lines.append(f"- **Name:** {pattern.get('name', '')}")
    if pattern.get('conversion'):
        lines.append(f"- **Conversion Focus:** {pattern.get('conversion', '')}")
    if pattern.get('cta_placement'):
        lines.append(f"- **CTA Placement:** {pattern.get('cta_placement', '')}")
    if pattern.get('color_strategy'):
        lines.append(f"- **Color Strategy:** {pattern.get('color_strategy', '')}")
    lines.append(f"- **Sections:** {pattern.get('sections', '')}")
    lines.append("")

    # Style section
    lines.append("### Style")
    lines.append(f"- **Name:** {style.get('name', '')}")
    light = style.get("light_mode", "")
    dark = style.get("dark_mode", "")
    if light or dark:
        lines.append(f"- **Mode Support:** Light {light} | Dark {dark}")
    if style.get('keywords'):
        lines.append(f"- **Keywords:** {style.get('keywords', '')}")
    if style.get('best_for'):
        lines.append(f"- **Best For:** {style.get('best_for', '')}")
    if style.get('performance') or style.get('accessibility'):
        lines.append(f"- **Performance note:** {style.get('performance', '')} | **Accessibility note:** {style.get('accessibility', '')}")
    lines.append("")

    # Design direction
    lines.append("### Design Direction")
    lines.append(f"- **Intent:** {design_direction.get('intent', '')}")
    lines.append(f"- **Composition:** {design_direction.get('composition', '')}")
    lines.append(f"- **Signature:** {design_direction.get('signature', '')}")
    lines.append(f"- **Restraint:** {design_direction.get('restraint', '')}")
    lines.append("")

    _append_option_exploration_markdown(lines, option_exploration)
    _append_art_direction_gate_markdown(lines, art_direction_gate)
    _append_creative_distinction_markdown(lines, creative_distinction_gate)

    # Layout system
    lines.append("### Layout System")
    lines.append(f"- **Max width:** {layout_system.get('max_width', '')}")
    lines.append(f"- **Grid:** {layout_system.get('grid', '')}")
    lines.append(f"- **Gutters:** {layout_system.get('gutters', '')}")
    lines.append(f"- **Text measure:** {layout_system.get('content_measure', '')}")
    lines.append(f"- **Responsive QA:** {layout_system.get('breakpoints', '')}")
    for rule in layout_system.get("rules", []):
        lines.append(f"- {rule}")
    lines.append("")

    # Shape and control policy
    lines.append("### Shape and Control Policy")
    lines.append(f"- **Profile:** {shape_system.get('label', '')}")
    lines.append(f"- **Rationale:** {shape_system.get('rationale', '')}")
    lines.append(f"- **Pill policy:** {shape_system.get('pill_policy', '')}")
    lines.append("")
    lines.append("| Radius token | Value |")
    lines.append("|--------------|-------|")
    for token, value in shape_system.get("tokens", {}).items():
        lines.append(f"| `--radius-{token.replace('_', '-')}` | `{value}` |")
    lines.append("")
    for rule in shape_system.get("rules", []):
        lines.append(f"- {rule}")
    lines.append("")

    _append_scoped_treatments_markdown(lines, visual_treatment_policy, shape_system)

    # Iconography and component roles
    _append_iconography_markdown(lines, iconography)

    lines.append("### Control Scale")
    lines.append(f"- **Mode:** {control_sizing.get('mode', '')}")
    lines.append(f"- **Primary control height:** {control_sizing.get('control_height', '')}")
    lines.append(f"- **Compact control height:** {control_sizing.get('compact_height', '')}")
    lines.append(f"- **Icon controls:** {control_sizing.get('icon_control', '')}")
    lines.append(f"- **Width:** {control_sizing.get('width', '')}")
    lines.append(f"- **Selects:** {control_sizing.get('select', '')}")
    lines.append(f"- **Segmented controls:** {control_sizing.get('segmented', '')}")
    lines.append(f"- **Hit-area principle:** {control_sizing.get('principle', '')}")
    lines.append(f"- **Measurement policy:** {control_sizing.get('measurement_policy', '')}")
    lines.append("")

    lines.append("### Component Roles")
    for component, guidance in component_guidance.items():
        lines.append(f"- **{component.replace('_', ' ').title()}:** {guidance}")
    lines.append("")

    # Colors section (extended palette)
    lines.append("### Colors")
    lines.append("| Role | Hex | CSS Variable |")
    lines.append("|------|-----|--------------|")
    md_color_entries = [
        ("Primary",      "primary",      "--color-primary"),
        ("On Primary",   "on_primary",   "--color-on-primary"),
        ("Secondary",    "secondary",    "--color-secondary"),
        ("On Secondary", "on_secondary", "--color-on-secondary"),
        ("Accent/CTA",   "accent",       "--color-accent"),
        ("On Accent",    "on_accent",    "--color-on-accent"),
        ("Background",   "background",   "--color-background"),
        ("Foreground",   "foreground",   "--color-foreground"),
        ("Card",         "card",         "--color-card"),
        ("Card Foreground", "card_foreground", "--color-card-foreground"),
        ("Muted",        "muted",        "--color-muted"),
        ("Muted Foreground", "muted_foreground", "--color-muted-foreground"),
        ("Border",       "border",       "--color-border"),
        ("Destructive",  "destructive",  "--color-destructive"),
        ("On Destructive", "on_destructive", "--color-on-destructive"),
        ("Ring",         "ring",         "--color-ring"),
    ]
    for label, key, css_var in md_color_entries:
        hex_val = colors.get(key, "")
        if hex_val:
            lines.append(f"| {label} | `{hex_val}` | `{css_var}` |")
    if colors.get("notes"):
        lines.append(f"\n*Notes: {colors.get('notes', '')}*")
    lines.append("")

    if palette_adjustments:
        lines.append("#### Applied Palette De-templating")
        for adjustment in palette_adjustments:
            lines.append(
                f"- `{adjustment['token']}`: `{adjustment['from']}` → `{adjustment['to']}` — {adjustment['reason']}"
            )
        lines.append("")

    if color_adjustments:
        lines.append("#### Applied Semantic Color Adjustments")
        for adjustment in color_adjustments:
            lines.append(
                f"- `{adjustment['token']}`: `{adjustment['from']}` → `{adjustment['to']}` "
                f"({adjustment['ratio']}:1 against `{adjustment['against']}`; target {adjustment['target']}:1)"
            )
        lines.append("")

    lines.append("#### Contrast Verification")
    if contrast_checks:
        lines.append("| Pair | Ratio | Target | Status | Action |")
        lines.append("|------|-------|--------|--------|--------|")
        for check in contrast_checks:
            lines.append(
                f"| {check['pair']} | {check['ratio']}:1 | {check['threshold']}:1 | {check['status']} | {check.get('suggestion', '')} |"
            )
    else:
        lines.append("No complete solid-color pairs were available; verify contrast in the rendered interface.")
    lines.append("")

    # Typography section
    lines.append("### Typography")
    lines.append(f"- **Heading:** {typography.get('heading', '')}")
    lines.append(f"- **Body:** {typography.get('body', '')}")
    if typography.get("mood"):
        lines.append(f"- **Mood:** {typography.get('mood', '')}")
    if typography.get("best_for"):
        lines.append(f"- **Best For:** {typography.get('best_for', '')}")
    if typography.get("google_fonts_url"):
        lines.append(f"- **Google Fonts:** {typography.get('google_fonts_url', '')}")
    if typography.get("css_import"):
        lines.append(f"- **CSS Import:**")
        lines.append(f"```css")
        lines.append(f"{typography.get('css_import', '')}")
        lines.append(f"```")
    lines.append("")

    lines.append("#### Type Scale")
    lines.append(f"- **Mode:** {type_system.get('mode', '')}")
    lines.append("")
    lines.append("| Role | Size / line-height |")
    lines.append("|------|--------------------|")
    for role, value in type_system.get("tokens", {}).items():
        lines.append(f"| {role} | `{value}` |")
    lines.append("")
    for rule in type_system.get("rules", []):
        lines.append(f"- {rule}")
    lines.append("")

    _append_typography_director_markdown(lines, typography_director)

    # Key Effects section
    if effects:
        lines.append("### Key Effects")
        lines.append(f"{effects}")
        lines.append("")

    # Motion section (GSAP skeleton, only if --motion dial was set)
    if motion_snippet:
        lines.append("### Motion")
        lines.append(f"**{motion_snippet.get('Category', '')}** ({motion_snippet.get('Intensity Tier', '')}) — Trigger: {motion_snippet.get('Trigger', '')} | Duration: {motion_snippet.get('Duration', '')} | Easing: `{motion_snippet.get('Easing', '')}`")
        lines.append("```js")
        lines.append(motion_snippet.get("GSAP Snippet", ""))
        lines.append("```")
        if motion_snippet.get("Framework Notes"):
            lines.append(f"*Framework notes: {motion_snippet.get('Framework Notes', '')}*")
        motion_do = motion_snippet.get("Do", "")
        motion_dont = motion_snippet.get("Don't", "")
        if motion_do:
            lines.append(f"- ✅ {motion_do}")
        if motion_dont:
            lines.append(f"- ❌ {motion_dont}")
        lines.append("")

    # Anti-patterns section
    if anti_patterns:
        lines.append("### Avoid (Anti-patterns)")
        for anti_pattern in anti_patterns:
            lines.append(f"- {anti_pattern}")
        lines.append("")

    _append_rendered_critic_markdown(lines, rendered_critic)
    _append_project_memory_policy_markdown(lines, project_memory)

    # Pre-Delivery Checklist section
    lines.append("### Pre-Delivery Checklist")
    for gate in quality_gates:
        lines.append(f"- [ ] {gate}")
    lines.append("")

    return "\n".join(lines)


# ============ MAIN ENTRY POINT ============
def generate_design_system(query: str, project_name: str = None, output_format: str = "ascii",
                           persist: bool = False, page: str = None, output_dir: str = None,
                           variance: int = None, motion: int = None, density: int = None,
                           roundness: int = None) -> str:
    """
    Main entry point for design system generation.

    Args:
        query: Search query (e.g., "SaaS dashboard", "e-commerce luxury")
        project_name: Optional project name for output header
        output_format: "ascii" (default) or "markdown"
        persist: If True, save design system to design-system/ folder
        page: Optional page name for page-specific override file
        output_dir: Optional output directory (defaults to current working directory)
        variance: Optional 1-10 DESIGN_VARIANCE dial (1=centered/minimal, 10=bold/asymmetric)
        motion: Optional 1-10 MOTION_INTENSITY dial, pulls a matching GSAP snippet from motion.csv
        density: Optional 1-10 VISUAL_DENSITY dial, overrides the spacing scale (1=spacious, 10=dense)
        roundness: Optional 1-10 ROUNDNESS dial; tunes the radius profile while keeping generic decorative pills outside the default system

    Returns:
        Formatted design system string
    """
    generator = DesignSystemGenerator()
    design_system = generator.generate(
        query,
        project_name,
        variance=variance,
        motion=motion,
        density=density,
        roundness=roundness,
    )

    # Persist to files if requested
    if persist:
        persist_design_system(design_system, page, output_dir, query)

    if output_format == "markdown":
        return format_markdown(design_system)
    return format_ascii_box(design_system)


# ============ PERSISTENCE FUNCTIONS ============
def slugify_name(value: str, fallback: str = "default") -> str:
    """Create a filesystem-safe, Unicode-preserving slug from user input."""
    slug = re.sub(r"[^\w]+", "-", str(value or "").casefold(), flags=re.UNICODE)
    slug = re.sub(r"-+", "-", slug.replace("_", "-")).strip("-")
    return slug[:80] or fallback


def _memory_cell(value) -> str:
    """Keep generated project-memory table cells single-line and readable."""
    return re.sub(r"\s+", " ", str(value or "")).replace("|", "\\|").strip()


def format_project_memory_md(design_system: dict) -> str:
    """Create an initialization-only, evidence-aware project design memory."""
    project = design_system.get("project_name", "PROJECT")
    category = design_system.get("category", "General")
    direction = design_system.get("design_direction", {})
    distinction = design_system.get("creative_distinction_gate", {})
    typography = design_system.get("typography_director", {})
    shape = design_system.get("shape_system", {})
    iconography = design_system.get("iconography", {})
    treatment = design_system.get("visual_treatment_policy", {})
    memory = design_system.get("project_memory", {})
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    source_roles = ", ".join(iconography.get("established_sources", [])) or "No repository sources confirmed"
    explicit_treatments = []
    if treatment.get("allow_gradient"):
        explicit_treatments.append(f"gradient: {', '.join(treatment.get('gradient_roles', []))}")
    if treatment.get("allow_glow"):
        explicit_treatments.append(f"glow/neon: {', '.join(treatment.get('glow_roles', []))}")
    explicit_treatments.extend(shape.get("approved_exceptions", []))

    proposed_entries = [
        (
            "PM-001",
            "Project",
            f"{category}; {direction.get('intent', '')}",
            "Generated retrieval and current brief; inspect repository and product evidence",
            "snowe-ui-skill generator",
            "The product, audience, or primary task changes",
        ),
        (
            "PM-002",
            "Identity",
            distinction.get("ownable_move", "No ownable move selected"),
            "Creative-distinction hypothesis; requires rendered comparison",
            "snowe-ui-skill generator",
            "The move fails task clarity, recognition, or repetition review",
        ),
        (
            "PM-003",
            "Typography",
            typography.get("proposed_pair", "No pairing proposed"),
            typography.get("initial_status", "Coverage and metrics unverified"),
            "snowe-ui-skill generator",
            "Content, locale, fallback, licensing, or font metrics conflict",
        ),
        (
            "PM-004",
            "Iconography",
            f"Likely primary: {iconography.get('established_family') or 'unconfirmed'}; observed roles: {source_roles}",
            "Repository context and generated source-role hypothesis",
            "snowe-ui-skill generator",
            "Imports, platform boundary, license, or rendered compatibility changes",
        ),
    ]

    lines = [
        "# Project Design Memory",
        "",
        "> Durable design decisions for this project. Read before material UI work.",
        "> This file is initialized once and is never overwritten by design-system regeneration.",
        "",
        f"**Project:** {project}",
        f"**Initialized:** {timestamp}",
        f"**Statuses:** `{memory.get('statuses', 'PROPOSED | CONFIRMED | SUPERSEDED')}`",
        "",
        "## Decision precedence",
        "",
        memory.get("precedence", "Current explicit requirements and verified repository evidence override generated hypotheses."),
        "",
        "## Decision ledger",
        "",
        "Promote a row to `CONFIRMED` only after repository, brand, user, rendered, or measured evidence supports it. Mark replaced rows `SUPERSEDED`; do not erase the history.",
        "",
        "| ID | Status | Scope | Decision | Evidence | Owner/source | Revisit when |",
        "|----|--------|-------|----------|----------|--------------|--------------|",
    ]
    for entry_id, scope, decision, evidence, owner, revisit in proposed_entries:
        lines.append(
            f"| {entry_id} | PROPOSED | {_memory_cell(scope)} | {_memory_cell(decision)} | {_memory_cell(evidence)} | {_memory_cell(owner)} | {_memory_cell(revisit)} |"
        )

    lines.extend(
        [
            "",
            "## Approved exceptions",
            "",
        ]
    )
    if explicit_treatments:
        lines.append("Treat these as brief-derived proposals until their provenance and scope are confirmed:")
        lines.append("")
        for item in explicit_treatments:
            lines.append(f"- [PROPOSED] {item}")
    else:
        lines.append("- None confirmed. Add exceptions with role, evidence, scope boundary, and revisit trigger.")

    lines.extend(
        [
            "",
            "## Rejected repetitions",
            "",
            "- Do not propagate a signature, gradient, glow, pill, shadow, icon container, or brand geometry from its approved role into routine chrome.",
            "- Do not replace product-specific composition with a generic centered hero, identical icon-card grid, or default component-library demo.",
            "- Do not treat dependency counts, token names, exact pixels, or raw hue names as quality verdicts without rendered evidence.",
            "",
            "## Verification ledger",
            "",
            "| Date | Surface | Evidence inspected | Result | Follow-up |",
            "|------|---------|--------------------|--------|-----------|",
            "| — | — | No rendered evidence recorded yet | UNKNOWN | Run the bounded rendered critic loop |",
            "",
            "## Update protocol",
            "",
            f"- {memory.get('read_rule', '')}",
            f"- {memory.get('write_rule', '')}",
            f"- {memory.get('scope_rule', '')}",
            "- Record public decision rationale and evidence; do not store private chain-of-thought.",
            "",
        ]
    )
    return "\n".join(lines)


def persist_design_system(design_system: dict, page: str = None, output_dir: str = None, page_query: str = None) -> dict:
    """
    Persist design system to design-system/<project>/ folder using Master + Overrides pattern.

    Args:
        design_system: The generated design system dictionary
        page: Optional page name for page-specific override file
        output_dir: Optional output directory (defaults to current working directory)
        page_query: Optional query string for intelligent page override generation

    Returns:
        dict with created file paths and status
    """
    base_dir = Path(output_dir) if output_dir else Path.cwd()

    # Use project name for project-specific folder. Coalesce falsy values
    # (missing key, explicit None, or "") so the .lower() below can't crash.
    project_name = design_system.get("project_name") or "default"
    project_slug = slugify_name(project_name)

    design_system_dir = base_dir / "design-system" / project_slug
    pages_dir = design_system_dir / "pages"

    created_files = []
    preserved_files = []

    # Create directories
    design_system_dir.mkdir(parents=True, exist_ok=True)
    pages_dir.mkdir(parents=True, exist_ok=True)

    master_file = design_system_dir / "MASTER.md"

    # Generate and write MASTER.md
    master_content = format_master_md(design_system)
    with open(master_file, 'w', encoding='utf-8') as f:
        f.write(master_content)
    created_files.append(str(master_file))

    # Initialize durable project memory once. Regeneration may replace MASTER.md
    # hypotheses, but it must never erase confirmed project decisions.
    memory_file = design_system_dir / "PROJECT-MEMORY.md"
    try:
        # Exclusive creation closes the check-then-write race: simultaneous
        # regeneration can never replace already established project memory.
        with open(memory_file, 'x', encoding='utf-8') as f:
            f.write(format_project_memory_md(design_system))
        created_files.append(str(memory_file))
    except FileExistsError:
        preserved_files.append(str(memory_file))

    # If page is specified, create page override file with intelligent content
    if page:
        page_file = pages_dir / f"{slugify_name(page, 'page')}.md"
        page_content = format_page_override_md(design_system, page, page_query)
        with open(page_file, 'w', encoding='utf-8') as f:
            f.write(page_content)
        created_files.append(str(page_file))

    return {
        "status": "success",
        "design_system_dir": str(design_system_dir),
        "created_files": created_files,
        "preserved_files": preserved_files,
    }


def format_master_md(design_system: dict) -> str:
    """Format design system as MASTER.md with hierarchical override logic."""
    project = design_system.get("project_name", "PROJECT")
    pattern = design_system.get("pattern", {})
    style = design_system.get("style", {})
    design_direction = design_system.get("design_direction", {})
    option_exploration = design_system.get("option_exploration", {})
    art_direction_gate = design_system.get("art_direction_gate", {})
    creative_distinction_gate = design_system.get("creative_distinction_gate", {})
    rendered_critic = design_system.get("rendered_critic", {})
    project_memory = design_system.get("project_memory", {})
    visual_treatment_policy = design_system.get("visual_treatment_policy", {})
    colors = design_system.get("colors", {})
    palette_adjustments = design_system.get("palette_adjustments", [])
    color_adjustments = design_system.get("color_adjustments", [])
    contrast_checks = design_system.get("contrast_checks", [])
    typography = design_system.get("typography", {})
    type_system = design_system.get("type_system", {})
    typography_director = design_system.get("typography_director", {})
    layout_system = design_system.get("layout_system", {})
    shape_system = design_system.get("shape_system", {})
    iconography = design_system.get("iconography", {})
    control_sizing = design_system.get("control_sizing", {})
    component_guidance = design_system.get("component_guidance", {})
    effects = design_system.get("key_effects", "")
    anti_patterns = split_guidance(design_system.get("anti_patterns", []))
    quality_gates = design_system.get("quality_gates", [])
    standards = design_system.get("standards", [])
    dials = design_system.get("dials", {})
    motion_snippet = design_system.get("motion_snippet", {})
    spacing_scale = design_system.get("spacing_scale")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = []

    # Logic header
    lines.append("# Design System Master File")
    lines.append("")
    lines.append("> **READ FIRST:** `PROJECT-MEMORY.md` contains durable confirmed decisions and is never overwritten by regeneration.")
    lines.append("> **LOGIC:** Read confirmed project memory, then check this project's `pages/[page-name].md` for scoped overrides.")
    lines.append("> If that file exists, its rules **override** this Master file.")
    lines.append("> If not, strictly follow the rules below.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"**Project:** {project}")
    lines.append(f"**Generated:** {timestamp}")
    lines.append(f"**Category:** {design_system.get('category', 'General')}")
    if any(dials.get(k) is not None for k in ("variance", "motion", "density", "roundness")):
        dial_parts = []
        if dials.get("variance") is not None:
            dial_parts.append(f"Variance {dials['variance']}/10 ({dials['variance_label']})")
        if dials.get("motion") is not None:
            dial_parts.append(f"Motion {dials['motion']}/10 ({dials['motion_label']})")
        if dials.get("density") is not None:
            dial_parts.append(f"Density {dials['density']}/10 ({dials['density_label']})")
        if dials.get("roundness") is not None:
            dial_parts.append(f"Roundness {dials['roundness']}/10 ({dials['roundness_label']})")
        lines.append(f"**Design Dials:** {' | '.join(dial_parts)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Global Rules section
    lines.append("## Global Rules")
    lines.append("")

    lines.append("### Project-Wide Decision Policy")
    lines.append("")
    lines.append("- Treat semantics, accessibility, content integrity, and verified product constraints as invariants; treat counts, token names, pixel ranges, and default visual recipes as contextual heuristics.")
    lines.append("- Do not use pills or capsules as generic decoration, selected-state chrome, or a default container shape.")
    lines.append("- Avoid a horizontal pill behind a standalone icon or every icon-label navigation item when it adds no semantic, state, platform, or brand meaning.")
    lines.append("- Preserve icon hit targets with transparent padding; use a compact rounded square only when visible containment communicates state.")
    lines.append("- Let component role decide full rounding; native or brand controls do not need special permission, but their geometry must not leak into unrelated components.")
    lines.append("- Reject unrequested blue/cyan/violet neon, glow, bloom, or ambient luminous-gradient identity; do not reject a functional cool hue or evidence-backed gradient solely by token or color name.")
    lines.append("- Keep buttons, selects, segmented controls, and icon containers visually compact; satisfy larger hit targets with transparent non-overlapping interaction area.")
    lines.append("- Page overrides inherit project policy, but may document evidence-backed platform, brand, content, or task exceptions without weakening accessibility or semantics.")
    lines.append("")

    lines.append("### Design Direction")
    lines.append("")
    lines.append(f"- **Intent:** {design_direction.get('intent', '')}")
    lines.append(f"- **Composition:** {design_direction.get('composition', '')}")
    lines.append(f"- **Signature:** {design_direction.get('signature', '')}")
    lines.append(f"- **Restraint:** {design_direction.get('restraint', '')}")
    lines.append("")

    _append_option_exploration_markdown(lines, option_exploration)
    _append_art_direction_gate_markdown(lines, art_direction_gate)
    _append_creative_distinction_markdown(lines, creative_distinction_gate)
    _append_scoped_treatments_markdown(lines, visual_treatment_policy, shape_system)

    lines.append("### Layout System")
    lines.append("")
    lines.append(f"- **Max width:** {layout_system.get('max_width', '')}")
    lines.append(f"- **Grid:** {layout_system.get('grid', '')}")
    lines.append(f"- **Gutters:** {layout_system.get('gutters', '')}")
    lines.append(f"- **Text measure:** {layout_system.get('content_measure', '')}")
    lines.append(f"- **Responsive QA:** {layout_system.get('breakpoints', '')}")
    for rule in layout_system.get("rules", []):
        lines.append(f"- {rule}")
    lines.append("")

    # Color Palette
    lines.append("### Color Palette")
    lines.append("")
    lines.append("| Role | Hex | CSS Variable |")
    lines.append("|------|-----|--------------|")
    master_color_entries = [
        ("Primary",      "primary",      "--color-primary"),
        ("On Primary",   "on_primary",   "--color-on-primary"),
        ("Secondary",    "secondary",    "--color-secondary"),
        ("On Secondary", "on_secondary", "--color-on-secondary"),
        ("Accent/CTA",   "accent",       "--color-accent"),
        ("On Accent",    "on_accent",    "--color-on-accent"),
        ("Background",   "background",   "--color-background"),
        ("Foreground",   "foreground",   "--color-foreground"),
        ("Card",         "card",         "--color-card"),
        ("Card Foreground", "card_foreground", "--color-card-foreground"),
        ("Muted",        "muted",        "--color-muted"),
        ("Muted Foreground", "muted_foreground", "--color-muted-foreground"),
        ("Border",       "border",       "--color-border"),
        ("Destructive",  "destructive",  "--color-destructive"),
        ("On Destructive", "on_destructive", "--color-on-destructive"),
        ("Ring",         "ring",         "--color-ring"),
    ]
    for label, key, css_var in master_color_entries:
        hex_val = colors.get(key, "")
        if hex_val:
            lines.append(f"| {label} | `{hex_val}` | `{css_var}` |")
    lines.append("")
    if colors.get("notes"):
        lines.append(f"**Color Notes:** {colors.get('notes', '')}")
        lines.append("")

    if palette_adjustments:
        lines.append("#### Applied Palette De-templating")
        lines.append("")
        for adjustment in palette_adjustments:
            lines.append(
                f"- `{adjustment['token']}`: `{adjustment['from']}` → `{adjustment['to']}` — {adjustment['reason']}"
            )
        lines.append("")

    if color_adjustments:
        lines.append("#### Applied Semantic Color Adjustments")
        lines.append("")
        for adjustment in color_adjustments:
            lines.append(
                f"- `{adjustment['token']}`: `{adjustment['from']}` → `{adjustment['to']}` "
                f"({adjustment['ratio']}:1 against `{adjustment['against']}`; target {adjustment['target']}:1)"
            )
        lines.append("")

    lines.append("#### Contrast Verification")
    lines.append("")
    if contrast_checks:
        lines.append("| Pair | Ratio | Target | Status | Action |")
        lines.append("|------|-------|--------|--------|--------|")
        for check in contrast_checks:
            lines.append(f"| {check['pair']} | {check['ratio']}:1 | {check['threshold']}:1 | {check['status']} | {check.get('suggestion', '')} |")
    else:
        lines.append("No complete solid-color pairs were available. Verify contrast in the rendered interface.")
    lines.append("")

    # Typography
    lines.append("### Typography")
    lines.append("")
    lines.append(f"- **Heading Font:** {typography.get('heading', 'Inter')}")
    lines.append(f"- **Body Font:** {typography.get('body', 'Inter')}")
    if typography.get("mood"):
        lines.append(f"- **Mood:** {typography.get('mood', '')}")
    if typography.get("google_fonts_url"):
        lines.append(f"- **Google Fonts:** [{typography.get('heading', '')} + {typography.get('body', '')}]({typography.get('google_fonts_url', '')})")
    lines.append("")
    if typography.get("css_import"):
        lines.append("**CSS Import:**")
        lines.append("```css")
        lines.append(typography.get("css_import", ""))
        lines.append("```")
        lines.append("")

    lines.append("#### Type Scale")
    lines.append("")
    lines.append(f"**Mode:** {type_system.get('mode', '')}")
    lines.append("")
    lines.append("| Role | Size / line-height |")
    lines.append("|------|--------------------|")
    for role, value in type_system.get("tokens", {}).items():
        lines.append(f"| `{role}` | `{value}` |")
    lines.append("")
    for rule in type_system.get("rules", []):
        lines.append(f"- {rule}")
    lines.append("")

    _append_typography_director_markdown(lines, typography_director)

    # Spacing Variables (overridden by the VISUAL_DENSITY dial when set)
    default_spacing = DIAL_TIERS["density"][1][2]["spacing"]  # mid-tier = the historical defaults
    scale = spacing_scale or default_spacing
    spacing_usage = {
        "xs": "Tight gaps", "sm": "Icon gaps, inline spacing", "md": "Standard padding",
        "lg": "Section padding", "xl": "Large gaps", "2xl": "Section margins", "3xl": "Hero padding",
    }
    lines.append("### Spacing Variables")
    lines.append("")
    if spacing_scale:
        lines.append(f"*Density: {dials.get('density')}/10 — {dials.get('density_label')}*")
        lines.append("")
    lines.append("| Token | Value | Usage |")
    lines.append("|-------|-------|-------|")
    for token in ("xs", "sm", "md", "lg", "xl", "2xl", "3xl"):
        px_value = scale[token]
        rem_value = f"{int(px_value.rstrip('px')) / 16:g}rem"
        lines.append(f"| `--space-{token}` | `{px_value}` / `{rem_value}` | {spacing_usage[token]} |")
    lines.append("")

    # Shape tokens and icon treatment
    lines.append("### Shape Variables")
    lines.append("")
    lines.append(f"**Profile:** {shape_system.get('label', '')} — {shape_system.get('rationale', '')}")
    lines.append("")
    lines.append("| Token | Value |")
    lines.append("|-------|-------|")
    for token, value in shape_system.get("tokens", {}).items():
        lines.append(f"| `--radius-{token.replace('_', '-')}` | `{value}` |")
    lines.append("")
    lines.append(f"**Pill policy:** {shape_system.get('pill_policy', '')}")
    lines.append("")
    for rule in shape_system.get("rules", []):
        lines.append(f"- {rule}")
    lines.append("")

    _append_iconography_markdown(lines, iconography)

    lines.append("### Control Scale")
    lines.append("")
    lines.append(f"- **Mode:** {control_sizing.get('mode', '')}")
    lines.append(f"- **Primary control height:** {control_sizing.get('control_height', '')}")
    lines.append(f"- **Compact control height:** {control_sizing.get('compact_height', '')}")
    lines.append(f"- **Icon controls:** {control_sizing.get('icon_control', '')}")
    lines.append(f"- **Width:** {control_sizing.get('width', '')}")
    lines.append(f"- **Selects:** {control_sizing.get('select', '')}")
    lines.append(f"- **Segmented controls:** {control_sizing.get('segmented', '')}")
    lines.append(f"- **Hit-area principle:** {control_sizing.get('principle', '')}")
    lines.append(f"- **Measurement policy:** {control_sizing.get('measurement_policy', '')}")
    lines.append("")

    # Elevation and separation
    lines.append("### Elevation and Separation")
    lines.append("")
    lines.append("| Level | Value | Usage |")
    lines.append("|-------|-------|-------|")
    lines.append("| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.06)` | Optional lift for interactive surfaces |")
    lines.append("| `--shadow-md` | `0 8px 24px rgba(0,0,0,0.10)` | Menus and floating panels |")
    lines.append("| `--shadow-lg` | `0 20px 48px rgba(0,0,0,0.16)` | Dialogs and high overlays |")
    lines.append("")
    lines.append("Prefer spacing, tonal surfaces, and borders before elevation. Do not put a shadow on every card or button.")
    lines.append("")

    # Component Specs section
    lines.append("---")
    lines.append("")
    lines.append("## Component Specs")
    lines.append("")

    # Buttons
    lines.append("### Buttons")
    lines.append("")
    lines.append(component_guidance.get("buttons", ""))
    lines.append("")
    lines.append("```css")
    lines.append(".button {")
    lines.append(f"  min-block-size: {control_sizing.get('css_height', '36px')};")
    lines.append("  display: inline-flex;")
    lines.append("  align-items: center;")
    lines.append("  justify-content: center;")
    lines.append("  gap: 8px;")
    lines.append(f"  padding-inline: {control_sizing.get('css_padding_inline', '14px')};")
    lines.append("  border-radius: var(--radius-control);")
    lines.append("  font-weight: 600;")
    lines.append("  transition: background-color 180ms ease, color 180ms ease, border-color 180ms ease, box-shadow 180ms ease, transform 120ms ease;")
    lines.append("}")
    lines.append("")
    lines.append(".button-primary {")
    lines.append(f"  background: {colors.get('cta', '#F97316')};")
    lines.append(f"  color: {colors.get('on_accent') or '#FFFFFF'};")
    lines.append("  border: 1px solid transparent;")
    lines.append("}")
    lines.append("")
    lines.append(".button-secondary {")
    lines.append(f"  background: transparent;")
    lines.append(f"  color: {colors.get('primary', '#2563EB')};")
    lines.append(f"  border: 1px solid {colors.get('border') or colors.get('primary', '#2563EB')};")
    lines.append("}")
    lines.append("")
    lines.append("@media (hover: hover) {")
    lines.append("  .button:hover { filter: brightness(0.96); }")
    lines.append("}")
    lines.append("")
    lines.append(".button:active { transform: translateY(1px); }")
    lines.append(".button:focus-visible { outline: 2px solid var(--color-ring); outline-offset: 2px; }")
    lines.append(".button:disabled { opacity: 0.5; cursor: not-allowed; }")
    lines.append("")
    lines.append("@media (prefers-reduced-motion: reduce) {")
    lines.append("  .button { transition-duration: 0.01ms; }")
    lines.append("}")
    lines.append("```")
    lines.append("")

    lines.append("### Icon Buttons and Semantic Chips")
    lines.append("")
    lines.append(f"- **Icon buttons:** {component_guidance.get('icon_buttons', '')}")
    lines.append(f"- **Chips:** {component_guidance.get('chips', '')}")
    lines.append(f"- **Navigation:** {component_guidance.get('navigation', '')}")
    lines.append("")
    lines.append("```css")
    lines.append(".icon-button {")
    lines.append(f"  inline-size: {control_sizing.get('css_icon_size', '36px')};")
    lines.append(f"  block-size: {control_sizing.get('css_icon_size', '36px')};")
    lines.append("  display: grid;")
    lines.append("  place-items: center;")
    lines.append("  padding: 6px;")
    lines.append("  position: relative;")
    lines.append("  border-radius: var(--radius-icon-container);")
    lines.append("  background: transparent;")
    lines.append("}")
    lines.append("")
    lines.append(".icon-button::before {")
    lines.append("  content: '';")
    lines.append("  position: absolute;")
    lines.append("  inset: -6px;")
    lines.append("}")
    lines.append("")
    lines.append("/* Keep adjacent extended hit areas from overlapping. */")
    lines.append(".icon-button + .icon-button { margin-inline-start: 12px; }")
    lines.append("")
    lines.append(".icon-button[aria-pressed='true'],")
    lines.append(".nav-item[aria-current='page'] {")
    lines.append("  color: var(--color-primary);")
    lines.append("  box-shadow: inset 0 -2px 0 var(--color-primary);")
    lines.append("}")
    lines.append("")
    lines.append("/* Use only for real tags, filters, statuses, choices, or entered entities. */")
    lines.append(".chip { border-radius: var(--radius-chip); }")
    lines.append("```")
    lines.append("")

    # Cards
    lines.append("### Cards")
    lines.append("")
    lines.append(component_guidance.get("cards", ""))
    lines.append("")
    lines.append("```css")
    lines.append(".card {")
    lines.append(f"  background: {colors.get('card') or colors.get('background', '#FFFFFF')};")
    lines.append(f"  color: {colors.get('card_foreground') or colors.get('foreground', '#1E293B')};")
    lines.append(f"  border: 1px solid {colors.get('border') or '#E2E8F0'};")
    lines.append("  border-radius: var(--radius-card);")
    lines.append("  padding: 24px;")
    lines.append("}")
    lines.append("")
    lines.append(".card[data-interactive='true'] {")
    lines.append("  transition: border-color 180ms ease, box-shadow 180ms ease, transform 180ms ease;")
    lines.append("  cursor: pointer;")
    lines.append("}")
    lines.append("")
    lines.append("@media (hover: hover) {")
    lines.append("  .card[data-interactive='true']:hover {")
    lines.append("    border-color: var(--color-primary);")
    lines.append("    box-shadow: var(--shadow-sm);")
    lines.append("  }")
    lines.append("}")
    lines.append("```")
    lines.append("")

    # Inputs
    lines.append("### Inputs")
    lines.append("")
    lines.append(component_guidance.get("inputs", ""))
    lines.append("")
    lines.append("```css")
    lines.append(".input {")
    lines.append(f"  min-block-size: {control_sizing.get('css_height', '36px')};")
    lines.append(f"  padding: {control_sizing.get('css_input_padding', '8px 12px')};")
    lines.append(f"  border: 1px solid {colors.get('border') or '#E2E8F0'};")
    lines.append("  border-radius: var(--radius-control);")
    lines.append("  font-size: 16px;")
    lines.append("  transition: border-color 180ms ease, box-shadow 180ms ease;")
    lines.append("}")
    lines.append("")
    lines.append(".input:focus-visible {")
    lines.append("  border-color: var(--color-ring);")
    lines.append("  outline: none;")
    lines.append("  box-shadow: 0 0 0 2px var(--color-ring);")
    lines.append("}")
    lines.append("")
    lines.append("@media (pointer: coarse) {")
    lines.append("  .button, .input { min-block-size: 44px; }")
    lines.append("}")
    lines.append("```")
    lines.append("")

    # Modals
    lines.append("### Modals")
    lines.append("")
    lines.append(component_guidance.get("overlays", ""))
    lines.append("")
    lines.append("```css")
    lines.append(".modal-overlay {")
    lines.append("  background: rgba(0, 0, 0, 0.5);")
    lines.append("}")
    lines.append("")
    lines.append(".modal {")
    lines.append(f"  background: {colors.get('card') or colors.get('background', '#FFFFFF')};")
    lines.append("  border-radius: var(--radius-overlay);")
    lines.append("  padding: 32px;")
    lines.append("  box-shadow: var(--shadow-lg);")
    lines.append("  max-inline-size: 500px;")
    lines.append("  max-block-size: min(90dvh, 800px);")
    lines.append("  inline-size: min(90vw, 500px);")
    lines.append("  overflow: auto;")
    lines.append("}")
    lines.append("```")
    lines.append("")

    # Style section
    lines.append("---")
    lines.append("")
    lines.append("## Style Guidelines")
    lines.append("")
    lines.append(f"**Style:** {style.get('name', 'Minimalism')}")
    lines.append("")
    if style.get("keywords"):
        lines.append(f"**Keywords:** {style.get('keywords', '')}")
        lines.append("")
    if style.get("best_for"):
        lines.append(f"**Best For:** {style.get('best_for', '')}")
        lines.append("")
    if effects:
        lines.append(f"**Key Effects:** {effects}")
        lines.append("")

    # Layout Pattern
    lines.append("### Page Pattern")
    lines.append("")
    lines.append(f"**Pattern Name:** {pattern.get('name', '')}")
    lines.append("")
    if pattern.get('conversion'):
        lines.append(f"- **Conversion Strategy:** {pattern.get('conversion', '')}")
    if pattern.get('cta_placement'):
        lines.append(f"- **CTA Placement:** {pattern.get('cta_placement', '')}")
    lines.append(f"- **Section Order:** {pattern.get('sections', '')}")
    lines.append("")

    # Motion section (GSAP skeleton, only if --motion dial was set)
    if motion_snippet:
        lines.append("---")
        lines.append("")
        lines.append("## Motion")
        lines.append("")
        lines.append(f"**{motion_snippet.get('Category', '')}** ({motion_snippet.get('Intensity Tier', '')}) — Trigger: {motion_snippet.get('Trigger', '')} | Duration: {motion_snippet.get('Duration', '')} | Easing: `{motion_snippet.get('Easing', '')}`")
        lines.append("")
        lines.append("```js")
        lines.append(motion_snippet.get("GSAP Snippet", ""))
        lines.append("```")
        lines.append("")
        if motion_snippet.get("Framework Notes"):
            lines.append(f"**Framework notes:** {motion_snippet.get('Framework Notes', '')}")
            lines.append("")
        motion_do = motion_snippet.get("Do", "")
        motion_dont = motion_snippet.get("Don't", "")
        if motion_do:
            lines.append(f"- ✅ {motion_do}")
        if motion_dont:
            lines.append(f"- ❌ {motion_dont}")
        if motion_snippet.get("Performance Notes"):
            lines.append(f"- ⚡ {motion_snippet.get('Performance Notes', '')}")
        lines.append("")

    # Anti-Patterns section
    lines.append("---")
    lines.append("")
    lines.append("## Anti-Patterns (Do NOT Use)")
    lines.append("")
    for anti_pattern in anti_patterns:
        lines.append(f"- {anti_pattern}")
    lines.append("")

    _append_rendered_critic_markdown(lines, rendered_critic)
    _append_project_memory_policy_markdown(lines, project_memory)

    # Pre-Delivery Checklist
    lines.append("---")
    lines.append("")
    lines.append("## Pre-Delivery Checklist")
    lines.append("")
    lines.append("Before delivering any UI code, verify:")
    lines.append("")
    for gate in quality_gates:
        lines.append(f"- [ ] {gate}")
    lines.append("")

    lines.append("## Standards Baseline")
    lines.append("")
    lines.append("Treat these as the baseline, then follow stricter product or platform requirements when present.")
    lines.append("")
    for standard in standards:
        lines.append(f"- [{standard.get('name', '')}]({standard.get('url', '')}) — {standard.get('applies', '')}")
    lines.append("")

    return "\n".join(lines)


def format_page_override_md(design_system: dict, page_name: str, page_query: str = None) -> str:
    """Format a page-specific override file with intelligent AI-generated content."""
    project = design_system.get("project_name", "PROJECT")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    page_title = page_name.replace("-", " ").replace("_", " ").title()

    # Detect page type and generate intelligent overrides
    page_overrides = _generate_intelligent_overrides(page_name, page_query, design_system)

    lines = []

    lines.append(f"# {page_title} Page Overrides")
    lines.append("")
    lines.append(f"> **PROJECT:** {project}")
    lines.append(f"> **Generated:** {timestamp}")
    lines.append(f"> **Page Type:** {page_overrides.get('page_type', 'General')}")
    lines.append("")
    lines.append("> **IMPORTANT:** Rules in this file override page-level details in the Master file.")
    lines.append("> Confirmed entries in `../PROJECT-MEMORY.md` and current explicit requirements take precedence over this override.")
    lines.append("> Accessibility, semantics, and content integrity remain invariant. Visual defaults inherit from Master but may be overridden by documented page, platform, brand, or task evidence.")
    lines.append("> Only deviations from the Master are documented here. For all other rules, refer to the Master.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Page-specific rules with actual content
    lines.append("## Page-Specific Rules")
    lines.append("")

    # Layout Overrides
    lines.append("### Layout Overrides")
    lines.append("")
    layout = page_overrides.get("layout", {})
    if layout:
        for key, value in layout.items():
            lines.append(f"- **{key}:** {value}")
    else:
        lines.append("- No overrides — use Master layout")
    lines.append("")

    # Spacing Overrides
    lines.append("### Spacing Overrides")
    lines.append("")
    spacing = page_overrides.get("spacing", {})
    if spacing:
        for key, value in spacing.items():
            lines.append(f"- **{key}:** {value}")
    else:
        lines.append("- No overrides — use Master spacing")
    lines.append("")

    # Typography Overrides
    lines.append("### Typography Overrides")
    lines.append("")
    typography = page_overrides.get("typography", {})
    if typography:
        for key, value in typography.items():
            lines.append(f"- **{key}:** {value}")
    else:
        lines.append("- No overrides — use Master typography")
    lines.append("")

    # Color Overrides
    lines.append("### Color Overrides")
    lines.append("")
    colors = page_overrides.get("colors", {})
    if colors:
        for key, value in colors.items():
            lines.append(f"- **{key}:** {value}")
    else:
        lines.append("- No overrides — use Master colors")
    lines.append("")

    # Component Overrides
    lines.append("### Component Overrides")
    lines.append("")
    components = page_overrides.get("components", [])
    if components:
        for comp in components:
            lines.append(f"- {comp}")
    else:
        lines.append("- No overrides — use Master component specs")
    lines.append("")

    # Page-Specific Components
    lines.append("---")
    lines.append("")
    lines.append("## Page-Specific Components")
    lines.append("")
    unique_components = page_overrides.get("unique_components", [])
    if unique_components:
        for comp in unique_components:
            lines.append(f"- {comp}")
    else:
        lines.append("- No unique components for this page")
    lines.append("")

    # Recommendations
    lines.append("---")
    lines.append("")
    lines.append("## Recommendations")
    lines.append("")
    recommendations = page_overrides.get("recommendations", [])
    if recommendations:
        for rec in recommendations:
            lines.append(f"- {rec}")
    lines.append("")

    return "\n".join(lines)


def _generate_intelligent_overrides(page_name: str, page_query: str, design_system: dict) -> dict:
    """
    Generate intelligent overrides based on page type using layered search.

    Uses the existing search infrastructure to find relevant style, UX, and layout
    data instead of hardcoded page types.
    """
    from core import search

    page_lower = page_name.lower()
    query_lower = (page_query or "").lower()
    combined_context = f"{page_lower} {query_lower}"

    # Search across multiple domains for page-specific guidance
    style_search = search(combined_context, "style", max_results=1)
    ux_search = search(combined_context, "ux", max_results=3)
    landing_search = search(combined_context, "landing", max_results=1)

    # Extract results from search response
    style_results = style_search.get("results", [])
    ux_results = ux_search.get("results", [])
    landing_results = landing_search.get("results", [])

    # Detect page type from search results or context
    page_type = _detect_page_type(combined_context, style_results)

    # Build overrides from search results
    layout = {}
    spacing = {}
    typography = {}
    colors = {}
    components = []
    unique_components = []
    recommendations = []

    # Extract style-based overrides
    if style_results:
        style = style_results[0]
        style_name = style.get("Style Category", "")
        keywords = style.get("Keywords", "")
        best_for = style.get("Best For", "")
        effects = style.get("Effects & Animation", "")

        # Infer layout from style keywords
        if any(kw in keywords.lower() for kw in ["data", "dense", "dashboard", "grid"]):
            layout["Max Width"] = "1400px or full-width"
            layout["Grid"] = "12-column grid for data flexibility"
            spacing["Content Density"] = "High — optimize for information display"
        elif any(kw in keywords.lower() for kw in ["minimal", "simple", "clean", "single"]):
            layout["Max Width"] = "800px (narrow, focused)"
            layout["Layout"] = "Single column, centered"
            spacing["Content Density"] = "Low — focus on clarity"
        else:
            layout["Max Width"] = "1200px (standard)"
            layout["Layout"] = "Full-width sections, centered content"

        if effects:
            recommendations.append(f"Effects: {effects}")

    # Extract UX guidelines as recommendations
    for ux in ux_results:
        category = ux.get("Category", "")
        do_text = ux.get("Do", "")
        dont_text = ux.get("Don't", "")
        if do_text:
            recommendations.append(f"{category}: {do_text}")
        if dont_text:
            components.append(f"Avoid: {dont_text}")

    # Extract landing pattern info for section structure
    if landing_results:
        landing = landing_results[0]
        sections = landing.get("Section Order", "")
        cta_placement = landing.get("Primary CTA Placement", "")
        color_strategy = landing.get("Color Strategy", "")

        if sections:
            layout["Sections"] = sections
        if cta_placement:
            recommendations.append(f"CTA Placement: {cta_placement}")
        if color_strategy:
            colors["Strategy"] = color_strategy

    # Add page-type specific defaults if no search results
    if not layout:
        layout["Max Width"] = "1200px"
        layout["Layout"] = "Responsive grid"

    if not recommendations:
        recommendations = [
            "Refer to MASTER.md for all design rules",
            "Add specific overrides as needed for this page"
        ]

    return {
        "page_type": page_type,
        "layout": layout,
        "spacing": spacing,
        "typography": typography,
        "colors": colors,
        "components": components,
        "unique_components": unique_components,
        "recommendations": recommendations
    }


def _detect_page_type(context: str, style_results: list) -> str:
    """Detect page type from context and search results."""
    context_lower = context.lower()

    # Check for common page type patterns
    page_patterns = [
        (["dashboard", "admin", "analytics", "data", "metrics", "stats", "monitor", "overview"], "Dashboard / Data View"),
        (["checkout", "payment", "cart", "purchase", "order", "billing"], "Checkout / Payment"),
        (["settings", "profile", "account", "preferences", "config"], "Settings / Profile"),
        (["landing", "marketing", "homepage", "hero", "home", "promo"], "Landing / Marketing"),
        (["login", "signin", "signup", "register", "auth", "password"], "Authentication"),
        (["pricing", "plans", "subscription", "tiers", "packages"], "Pricing / Plans"),
        (["blog", "article", "post", "news", "content", "story"], "Blog / Article"),
        (["product", "item", "detail", "pdp", "shop", "store"], "Product Detail"),
        (["search", "results", "browse", "filter", "catalog", "list"], "Search Results"),
        (["empty", "404", "error", "not found", "zero"], "Empty State"),
    ]

    for keywords, page_type in page_patterns:
        if any(kw in context_lower for kw in keywords):
            return page_type

    # Fallback: try to infer from style results
    if style_results:
        style_name = style_results[0].get("Style Category", "").lower()
        best_for = style_results[0].get("Best For", "").lower()

        if "dashboard" in best_for or "data" in best_for:
            return "Dashboard / Data View"
        elif "landing" in best_for or "marketing" in best_for:
            return "Landing / Marketing"

    return "General"


# ============ CLI SUPPORT ============
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate Design System")
    parser.add_argument("query", help="Search query (e.g., 'SaaS dashboard')")
    parser.add_argument("--project-name", "-p", type=str, default=None, help="Project name")
    parser.add_argument("--format", "-f", choices=["ascii", "markdown"], default="ascii", help="Output format")
    parser.add_argument("--variance", type=int, choices=range(1, 11), metavar="1-10")
    parser.add_argument("--motion", type=int, choices=range(1, 11), metavar="1-10")
    parser.add_argument("--density", type=int, choices=range(1, 11), metavar="1-10")
    parser.add_argument("--roundness", type=int, choices=range(1, 11), metavar="1-10")

    args = parser.parse_args()

    result = generate_design_system(
        args.query,
        args.project_name,
        args.format,
        variance=args.variance,
        motion=args.motion,
        density=args.density,
        roundness=args.roundness,
    )
    print(result)
