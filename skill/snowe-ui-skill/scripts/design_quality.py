#!/usr/bin/env python3
"""Deterministic design-quality rules shared by search and system generation."""

from __future__ import annotations

import colorsys
import re
from typing import Any, Iterable


GLOBAL_ANTI_PATTERNS = (
    "Decorative pill or capsule backgrounds behind standalone icons",
    "rounded-full as the default shape for buttons, navigation items, fields, cards, or toolbars",
    "A separate card around every content group when whitespace or a divider would create clearer hierarchy",
    "Multiple visually equal primary actions without a workflow reason or a clear action hierarchy",
    "Arbitrary radii, shadows, gradients, or icon styles that are not tied to design tokens",
    "Color-only state communication, low-contrast text, or invisible keyboard focus",
    "Generic AI-blue, cyan, or violet neon; luminous gradients; bloom; or glow used as the default visual identity",
    "Oversized buttons, selects, segmented controls, or icon containers whose visible geometry is larger than the task requires",
    "Sparkles, magic wands, brains, rockets, shields, lightning, globes, puzzle pieces, cubes, or generic chart-up symbols used as automatic shortcuts for product value",
    "Uncontrolled icon-source mixing that creates inconsistent stroke, fill, corner, detail, baseline, or optical-weight behavior",
)


ICON_CLICHE_GUARD = (
    {
        "concept": "AI and automation",
        "avoid": "sparkles, magic wand, brain, or generic robot head",
        "prefer": "the actual capability or output: compose, extract, classify, translate, route, schedule, or connect a trigger to an action",
        "allowed": "a learned enhance or generative action, a literal bot character, or a verified brand motif when context and labels keep the action clear",
    },
    {
        "concept": "Launch, growth, and performance",
        "avoid": "rocket, confetti, plant sprout, generic chart-up, lightning, or flame",
        "prefer": "the release artifact, measured KPI, retention or acquisition path, latency trace, stopwatch, gauge, or throughput model",
        "allowed": "a literal subject, an established campaign motif, or a conventional symbol whose exact meaning is clear in context",
    },
    {
        "concept": "Security and trust",
        "avoid": "a shield or shield-check applied to every assurance claim",
        "prefer": "the real mechanism or evidence: key, lock, identity, firewall, credential, signed record, audit trail, or provenance",
        "allowed": "a top-level protection boundary, verified certification, or established security destination rather than every individual feature",
    },
    {
        "concept": "Global, integrations, and platform",
        "avoid": "generic globe, puzzle piece, stacked layers, or floating cubes",
        "prefer": "translation, time zone, route, region nodes, connector, webhook, provider mark, runtime boundary, or component graph",
        "allowed": "a learned worldwide-scope, extension, layer, or 3D-object meaning that the product actually uses",
    },
    {
        "concept": "Analytics and data",
        "avoid": "the same rising chart or database cylinder for every data feature",
        "prefer": "the exact view or object: line, bars, funnel, scatter, table, records, schema, event stream, or warehouse",
        "allowed": "the icon depicts the actual selected visualization, database, or storage administration task",
    },
    {
        "concept": "Community, achievement, and settings",
        "avoid": "generic user group, trophy, star, crown, or gear",
        "prefer": "discussion, event, directory, collaboration, certificate, checkpoint, sliders, access key, or the specific setup tool",
        "allowed": "a literal group, award, rating, favorite, or established general-settings destination",
    },
)


STANDARDS_BASELINE = (
    {
        "name": "WCAG 2.2",
        "url": "https://www.w3.org/TR/WCAG22/",
        "applies": "Web accessibility, contrast, focus, reflow, input, and target-size conformance",
    },
    {
        "name": "Apple UI Design Dos and Don'ts",
        "url": "https://developer.apple.com/design/tips/",
        "applies": "Apple-platform hit targets, readability, layout, and alignment",
    },
    {
        "name": "Android accessibility guidance",
        "url": "https://developer.android.com/design/ui/mobile/guides/foundations/accessibility",
        "applies": "Android touch targets, semantics, and accessible alternatives",
    },
    {
        "name": "Android Material components",
        "url": "https://developer.android.com/develop/ui/compose/components",
        "applies": "Component roles such as buttons, icon buttons, chips, navigation, and selection controls",
    },
)


SHAPE_PROFILES = {
    "sharp": {
        "label": "Sharp / Editorial",
        "tokens": {
            "xs": "0px",
            "sm": "2px",
            "control": "4px",
            "card": "6px",
            "overlay": "10px",
            "chip": "6px",
            "icon_container": "6px",
        },
    },
    "balanced": {
        "label": "Balanced / Professional",
        "tokens": {
            "xs": "2px",
            "sm": "6px",
            "control": "8px",
            "card": "12px",
            "overlay": "16px",
            "chip": "8px",
            "icon_container": "10px",
        },
    },
    "soft": {
        "label": "Soft / Expressive",
        "tokens": {
            "xs": "4px",
            "sm": "8px",
            "control": "12px",
            "card": "18px",
            "overlay": "24px",
            "chip": "10px",
            "icon_container": "12px",
        },
    },
}


_SHARP_STYLE_MARKERS = (
    "brutal",
    "bauhaus",
    "swiss",
    "cyberpunk",
    "flat design",
    "editorial",
    "monochrome",
)
_SOFT_STYLE_MARKERS = (
    "clay",
    "organic",
    "biophilic",
    "bento",
    "neumorph",
    "glass",
    "playful",
    "soft ui",
)


_PILL_REPLACEMENTS = (
    (
        re.compile(
            r"all interactive elements are pill-shaped\s*\(borderRadius\s*:\s*9999?\)",
            re.IGNORECASE,
        ),
        "Use component-specific radii: 8-12px controls, 12-20px cards, and full rounding only for semantic chips or tags",
    ),
    (
        re.compile(
            r"everything interactive is pill-shaped or heavily rounded",
            re.IGNORECASE,
        ),
        "Use a restrained component-specific shape hierarchy",
    ),
    (
        re.compile(
            r"pill-shaped buttons and chips\s*\(borderRadius\s*:?\s*9999?\)",
            re.IGNORECASE,
        ),
        "moderately rounded buttons and compact semantic chips",
    ),
    (
        re.compile(r"all\s+(?:CTAs?|buttons?|actions?)\s+are\s+pill-shaped", re.IGNORECASE),
        "CTA and action shape follows component role and hierarchy",
    ),
    (
        re.compile(r"borderRadius\s*:\s*9999?\s*\(buttons/chips\)", re.IGNORECASE),
        "buttonRadius: component-specific; chipRadius: semantic compact token",
    ),
    (re.compile(r"pill buttons?\s+or\s+12pt radius", re.IGNORECASE), "12pt-radius buttons"),
    (re.compile(r"pill-shaped\s+or\s+radius\s+12", re.IGNORECASE), "radius 12"),
    (re.compile(r"pill buttons?", re.IGNORECASE), "12px-radius buttons"),
    (re.compile(r"rounded pill", re.IGNORECASE), "compact rounded tag"),
    (
        re.compile(
            r"\brounded-full\s+(buttons?|fields?|inputs?|cards?|toolbars?|navigation(?:\s+items?)?|nav(?:\s+items?)?|tabs?)\b",
            re.IGNORECASE,
        ),
        r"component-specific-radius \1",
    ),
    (
        re.compile(
            r"\b(buttons?|fields?|inputs?|cards?|toolbars?|navigation(?:\s+items?)?|nav(?:\s+items?)?|tabs?)\s+(?:use|are|with)?\s*rounded-full\b",
            re.IGNORECASE,
        ),
        r"\1 use a component-specific radius",
    ),
    (
        re.compile(
            r"border-radius\s*:\s*0px\s*\(cards/inputs\)\s*or\s*9999?px\s*\(buttons/FAB\)",
            re.IGNORECASE,
        ),
        "use component-specific radii for cards, inputs, and buttons; use a circle only for a true FAB",
    ),
    (
        re.compile(r"9999?px\s*\(buttons(?:/FAB)?\)", re.IGNORECASE),
        "a component-specific button radius; use a circle only for a true FAB",
    ),
    (re.compile(r"--radius-pill\s*:\s*9999?px", re.IGNORECASE), "--radius-chip: var(--radius-control)"),
    (re.compile(r"radiusPill\s*:\s*9999?", re.IGNORECASE), "radiusChip: radiusControl"),
    (re.compile(r"Pill/Search Bar", re.IGNORECASE), "Search field"),
    (re.compile(r"Power Pill", re.IGNORECASE), "Primary action"),
)


_GLOW_REPLACEMENTS = (
    (
        re.compile(r"minimal\s+glow\s*\([^)]*\)", re.IGNORECASE),
        "solid tonal contrast; avoid ambient light effects",
    ),
    (re.compile(r"\bneon(?:-lit)?\b", re.IGNORECASE), "solid high-contrast"),
    (re.compile(r"\belectric\s+(?:blue|cyan|purple|violet)\b", re.IGNORECASE), "restrained solid accent"),
    (re.compile(r"\bplasma\s+(?:purple|violet|blue)\b", re.IGNORECASE), "restrained solid accent"),
    (
        re.compile(r"\bmidnight\s+blue(?:\s+accents?)?(?:\s+#[0-9a-fA-F]{6})?", re.IGNORECASE),
        "neutral charcoal with a deliberate solid accent",
    ),
    (re.compile(r"\bvibrant\s+accents?\b", re.IGNORECASE), "restrained accents"),
    (re.compile(r"\bluminous\b", re.IGNORECASE), "high-contrast"),
    (re.compile(r"\bglowing\b", re.IGNORECASE), "high-contrast"),
    (re.compile(r"\bglows?\b", re.IGNORECASE), "tonal emphasis"),
    (re.compile(r"\bbloom\b", re.IGNORECASE), "tonal contrast"),
    (re.compile(r"\baura(?:\s+blobs?)?\b", re.IGNORECASE), "restrained tonal field"),
    (
        re.compile(r"\b(?:colored|tinted)\s+card\s+shadows?(?:\s+rgba\([^)]*\))?", re.IGNORECASE),
        "neutral border or overlay-only shadow",
    ),
    (re.compile(r"\btinted\s+shadows?\b", re.IGNORECASE), "neutral overlay-only shadows"),
    (
        re.compile(r"\bfull-width\s+CTA\s+at\s+(?:the\s+)?screen\s+bottom\b", re.IGNORECASE),
        "contextual primary action; full width only when a narrow linear task justifies it",
    ),
    (re.compile(r"text-shadow\s*:\s*0\s+0\s+[^,;]*", re.IGNORECASE), "text-shadow: none"),
    (re.compile(r"box-shadow\s*:\s*0\s+0\s+[^,;]*", re.IGNORECASE), "box-shadow: none"),
)


_GRADIENT_REPLACEMENTS = (
    (
        re.compile(
            r"\b(?:blue|cyan|indigo)\s*(?:→|->|to|-)\s*(?:cyan|violet|purple)\s+gradient\b",
            re.IGNORECASE,
        ),
        "solid product-specific accent",
    ),
    (re.compile(r"\bgradient\s+active\s+tab\s+icons?\b", re.IGNORECASE), "solid active-tab icon"),
    (
        re.compile(r"gradientPrimary\s*:\s*\[[^\]]+\]", re.IGNORECASE),
        "primary: 'product-specific solid accent'",
    ),
)


_LUMINOUS_MARKERS = (
    "neon",
    "glow",
    "glowing",
    "luminous",
    "cyberpunk",
    "aurora",
    "holographic",
    "electric blue",
    "electric cyan",
    "неон",
    "свечение",
    "светящийся",
    "светящаяся",
    "люминесцент",
)


_GRADIENT_MARKERS = ("gradient", "градиент")


_SYSTEM_TREATMENT_SCOPE_MARKERS = (
    "overall visual language",
    "visual identity",
    "design language",
    "product-wide",
    "across the product",
    "throughout the product",
    "system-wide",
    "overall theme",
    "визуальный язык",
    "визуальная айдентика",
    "дизайн-язык",
    "по всему продукту",
    "во всем продукте",
    "во всём продукте",
    "системно",
    "общая тема",
)


_VISUAL_ROLE_MARKERS = {
    "hero": ("hero", "campaign masthead", "masthead", "хиро", "первый экран", "обложк"),
    "brand": ("brand", "logo", "identity", "бренд", "логотип", "айдентик"),
    "illustration": ("illustration", "artwork", "poster", "image", "иллюстрац", "постер", "изображен"),
    "data": ("chart", "data", "visualization", "heatmap", "график", "данн", "визуализац", "теплов"),
    "cta": (
        "cta",
        "call to action",
        "purchase button",
        "buy button",
        "primary button",
        "primary action",
        "призыв к действию",
        "кнопк покупки",
        "кнопк купить",
        "основн действ",
    ),
    "navigation": (
        "navigation",
        "nav",
        "tab",
        "sidebar",
        "toolbar",
        "навигац",
        "вкладк",
        "таб",
        "сайдбар",
        "тулбар",
    ),
    "surface": (
        "background",
        "canvas",
        "surface",
        "card",
        "panel",
        "field",
        "input",
        "фон",
        "холст",
        "поверхност",
        "карточк",
        "панел",
        "поле",
        "поля",
        "инпут",
    ),
}


_VISUAL_NEGATION_PREFIX = re.compile(
    r"(?:\bno\b|\bnot\b|\bwithout\b|\bavoid(?:ing)?\b|\breject\b|\bremove\b|\bdisable\b|\bdo\s+not\s+use\b|\bdon['’]?t\s+use\b|\bбез\b|\bнет\b|\bне\b|\bникак(?:ого|ой|их)\b|\bизбег(?:ать|ай|айте)\b|\bубер(?:и|ите|ать)\b)[^.;:\n]{0,48}$",
    re.IGNORECASE,
)


def _position_is_negated(context: str, start: int) -> bool:
    lowered = str(context or "").casefold()
    prefix = lowered[max(0, start - 64) : start]
    return bool(_VISUAL_NEGATION_PREFIX.search(prefix))


def _term_is_negated(context: str, term: str) -> bool:
    """Return true only when every occurrence is locally rejected."""
    lowered = str(context or "").casefold()
    matches = list(re.finditer(re.escape(term.casefold()), lowered))
    return bool(matches) and all(_position_is_negated(lowered, match.start()) for match in matches)


def explicit_luminous_request(context: str) -> bool:
    """Return whether glow, neon, or another luminous effect was requested."""
    lowered = str(context or "").casefold()
    return bool(
        [
        marker
        for marker in _LUMINOUS_MARKERS
        if marker in lowered and not _term_is_negated(lowered, marker)
        ]
    )


def explicit_gradient_request(context: str) -> bool:
    """Return whether a gradient was positively requested rather than rejected."""
    lowered = str(context or "").casefold()
    return any(marker in lowered and not _term_is_negated(lowered, marker) for marker in _GRADIENT_MARKERS)


def _local_treatment_window(context: str, start: int, end: int, radius: int = 40) -> str:
    """Return a punctuation-bounded phrase around one visual-treatment mention."""
    lowered = str(context or "").casefold()
    left = max(0, start - radius)
    right = min(len(lowered), end + radius)
    for boundary in (";", ".", "\n"):
        prior = lowered.rfind(boundary, left, start)
        if prior >= 0:
            left = max(left, prior + 1)
        following = lowered.find(boundary, end, right)
        if following >= 0:
            right = min(right, following)
    return lowered[left:right]


def _roles_near_term(context: str, term: str) -> list[str]:
    """Return visual roles named near an unnegated treatment term."""
    lowered = str(context or "").casefold()
    roles: list[str] = []
    for match in re.finditer(re.escape(term.casefold()), lowered):
        if _position_is_negated(lowered, match.start()):
            continue
        window = _local_treatment_window(lowered, match.start(), match.end())
        for role, markers in _VISUAL_ROLE_MARKERS.items():
            if any(marker in window for marker in markers) and role not in roles:
                roles.append(role)
    return roles


def _system_scope_requested(context: str, terms: Iterable[str]) -> bool:
    """Return whether a treatment is explicitly part of the overall visual system."""
    lowered = str(context or "").casefold()
    if not any(marker in lowered for marker in _SYSTEM_TREATMENT_SCOPE_MARKERS):
        return False
    for term in terms:
        for match in re.finditer(re.escape(term.casefold()), lowered):
            if _position_is_negated(lowered, match.start()):
                continue
            window = _local_treatment_window(lowered, match.start(), match.end(), radius=72)
            if any(marker in window for marker in _SYSTEM_TREATMENT_SCOPE_MARKERS):
                return True
    return False


def build_visual_treatment_policy(context: str) -> dict[str, Any]:
    """Resolve explicit visual effects and keep permission scoped to named roles."""
    allow_gradient = explicit_gradient_request(context)
    allow_glow = explicit_luminous_request(context)
    gradient_roles: list[str] = []
    if allow_gradient:
        for marker in _GRADIENT_MARKERS:
            if marker in str(context or "").casefold() and not _term_is_negated(context, marker):
                for role in _roles_near_term(context, marker):
                    if role not in gradient_roles:
                        gradient_roles.append(role)
    glow_roles: list[str] = []
    if allow_glow:
        for marker in _LUMINOUS_MARKERS:
            if marker in str(context or "").casefold() and not _term_is_negated(context, marker):
                for role in _roles_near_term(context, marker):
                    if role not in glow_roles:
                        glow_roles.append(role)
    if allow_gradient and not gradient_roles:
        gradient_roles = ["unspecified"]
    if allow_glow and not glow_roles:
        glow_roles = ["unspecified"]
    gradient_system_scope = allow_gradient and _system_scope_requested(context, _GRADIENT_MARKERS)
    glow_system_scope = allow_glow and _system_scope_requested(context, _LUMINOUS_MARKERS)
    return {
        "allow_gradient": allow_gradient,
        "gradient_roles": gradient_roles,
        "allow_gradient_style": bool(
            allow_gradient and (gradient_system_scope or gradient_roles == ["unspecified"])
        ),
        "allow_glow": allow_glow,
        "glow_roles": glow_roles,
        "allow_glow_style": bool(allow_glow and (glow_system_scope or glow_roles == ["unspecified"])),
        "scope_rule": (
            "Permission follows the named component or content role; an approved hero, brand, data, illustration, or CTA treatment does not authorize the same effect on routine navigation, fields, cards, or page chrome"
        ),
    }


def _treatment_match_allowed(value: str, match: re.Match[str], allowed_roles: Iterable[str]) -> bool:
    roles = tuple(allowed_roles or ())
    if not roles:
        return False
    if "unspecified" in roles:
        return True
    window = _local_treatment_window(value, match.start(), match.end())
    matched_roles = {
        role
        for role, markers in _VISUAL_ROLE_MARKERS.items()
        if any(marker in window for marker in markers)
    }
    return bool(matched_roles.intersection(roles))


def is_luminous_style(result: dict[str, Any]) -> bool:
    """Identify a style whose identity depends on neon, glow, or related effects."""
    category = str(result.get("Style Category", "")).casefold()
    context = " ".join(
        str(result.get(key, ""))
        for key in ("Style Category", "Keywords", "AI Prompt Keywords")
    ).casefold()
    # Dark mode itself is not a luminous style; its historical neon details are
    # sanitized into a solid low-chroma direction when glow was not requested.
    if "dark mode" in category and "neon" not in category:
        return False
    templated_cool_gradient = "gradient" in context and sum(
        color in context for color in ("blue", "cyan", "indigo", "violet", "purple")
    ) >= 2
    return (
        templated_cool_gradient
        or "colored card shadow" in context
        or "tinted shadow" in context
        or any(marker in context for marker in _LUMINOUS_MARKERS)
    )


def style_visual_traits(result: dict[str, Any]) -> dict[str, bool]:
    """Classify glow and cool-gradient identity separately for scoped filtering."""
    category = str(result.get("Style Category", "")).casefold()
    context = " ".join(
        str(result.get(key, ""))
        for key in ("Style Category", "Keywords", "AI Prompt Keywords")
    ).casefold()
    glow = any(marker in context for marker in _LUMINOUS_MARKERS)
    if "dark mode" in category and "neon" not in category:
        glow = False
    cool_gradient = "gradient" in context and sum(
        color in context for color in ("blue", "cyan", "indigo", "violet", "purple")
    ) >= 2
    return {"glow": glow, "cool_gradient": cool_gradient}


def sanitize_visual_guidance(
    value: Any,
    allow_luminous: bool = False,
    allow_gradient: bool = False,
    allowed_gradient_roles: Iterable[str] = (),
    allowed_luminous_roles: Iterable[str] = (),
) -> Any:
    """Remove generic pills and unrequested luminous styling from guidance.

    Apply this only to visual-style fields. Product names such as "pill reminder"
    and geometry APIs such as CapsuleGeometry must remain untouched.
    """
    if not isinstance(value, str) or not value:
        return value

    sanitized = value
    for pattern, replacement in _PILL_REPLACEMENTS:
        sanitized = pattern.sub(replacement, sanitized)
    if not allow_luminous:
        for pattern, replacement in _GLOW_REPLACEMENTS:
            sanitized = pattern.sub(replacement, sanitized)
    else:
        for pattern, replacement in _GLOW_REPLACEMENTS:
            sanitized = pattern.sub(
                lambda match: match.group(0)
                if _treatment_match_allowed(sanitized, match, allowed_luminous_roles)
                else replacement,
                sanitized,
            )
    if not allow_gradient:
        for pattern, replacement in _GRADIENT_REPLACEMENTS:
            sanitized = pattern.sub(replacement, sanitized)
    else:
        for pattern, replacement in _GRADIENT_REPLACEMENTS:
            sanitized = pattern.sub(
                lambda match: match.group(0)
                if _treatment_match_allowed(sanitized, match, allowed_gradient_roles)
                else replacement,
                sanitized,
            )
    return sanitized


def sanitize_style_result(
    result: dict[str, Any],
    allow_luminous: bool = False,
    allow_gradient: bool = False,
    allowed_gradient_roles: Iterable[str] = (),
    allowed_luminous_roles: Iterable[str] = (),
) -> dict[str, Any]:
    """Return a style result with the global shape policy applied."""
    visual_fields = {
        "Keywords",
        "Primary Colors",
        "Effects & Animation",
        "AI Prompt Keywords",
        "CSS/Technical Keywords",
        "Implementation Checklist",
        "Design System Variables",
    }
    sanitized = {
        key: sanitize_visual_guidance(
            value,
            allow_luminous,
            allow_gradient,
            allowed_gradient_roles,
            allowed_luminous_roles,
        ) if key in visual_fields else value
        for key, value in result.items()
    }
    for key, qualifier in (
        ("Performance", "style-level estimate; measure the implementation"),
        ("Accessibility", "style-level note; not a conformance result"),
    ):
        value = sanitized.get(key)
        if isinstance(value, str) and value and qualifier not in value:
            sanitized[key] = f"{value} ({qualifier})"
    return sanitized


def split_guidance(value: Any) -> list[str]:
    """Normalize a guidance string or sequence into clean list items."""
    if not value:
        return []
    if isinstance(value, str):
        return [item.strip() for item in re.split(r"\s+\+\s+|\r?\n", value) if item.strip()]
    if isinstance(value, Iterable):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def merge_anti_patterns(*values: Any) -> list[str]:
    """Merge project and global anti-patterns while preserving stable order."""
    merged: list[str] = []
    seen: set[str] = set()
    for value in (*values, GLOBAL_ANTI_PATTERNS):
        for item in split_guidance(value):
            key = item.casefold()
            if key not in seen:
                seen.add(key)
                merged.append(item)
    return merged


def _explicit_full_rounding_exceptions(context: str) -> list[str]:
    """Extract scoped, positively requested capsule roles from the brief."""
    lowered = str(context or "").casefold()
    exceptions: list[str] = []
    shape_terms = (
        "capsule-shaped",
        "capsule shaped",
        "capsule",
        "pill-shaped",
        "pill shaped",
        "капсулообразн",
        "капсульн",
        "в виде капсулы",
        "пилюлеобразн",
    )
    for term in shape_terms:
        for match in re.finditer(re.escape(term), lowered):
            if _position_is_negated(lowered, match.start()):
                continue
            window = lowered[max(0, match.start() - 100) : min(len(lowered), match.end() + 120)]
            if any(
                marker in window
                for marker in (
                    "cta",
                    "purchase",
                    "buy button",
                    "primary action",
                    "покупк",
                    "купить",
                    "призыв",
                    "основн действ",
                )
            ):
                rule = "Primary purchase or CTA variant: retain the explicitly requested full rounding only for that role; do not propagate it to routine controls or navigation"
            elif any(marker in window for marker in ("chip", "tag", "filter", "status", "token", "чип", "тег", "фильтр", "статус")):
                rule = "Named semantic chip, tag, filter, or status: full rounding is role-appropriate while repetition and label length remain controlled"
            elif any(
                marker in window
                for marker in (
                    "native",
                    "platform",
                    "brand",
                    "verified",
                    "design system",
                    "нативн",
                    "платформ",
                    "бренд",
                    "проверенн",
                    "дизайн-систем",
                )
            ):
                rule = "Verified native or brand component: preserve its full rounding inside the documented component boundary"
            else:
                rule = "Explicitly named capsule component: confirm its role and scope before implementation; the request does not authorize a global pill treatment"
            if rule not in exceptions:
                exceptions.append(rule)
    return exceptions


def resolve_shape_system(
    style_name: str,
    style_keywords: str = "",
    profile_override: str | None = None,
    context: str = "",
) -> dict[str, Any]:
    """Select a component-specific radius scale without generic capsules."""
    style_context = f"{style_name} {style_keywords}".casefold()
    if profile_override in SHAPE_PROFILES:
        profile = profile_override
        rationale = "Explicit roundness dial"
    elif any(marker in style_context for marker in _SHARP_STYLE_MARKERS):
        profile = "sharp"
        rationale = f"Style-driven geometry for {style_name or 'the selected direction'}"
    elif any(marker in style_context for marker in _SOFT_STYLE_MARKERS):
        profile = "soft"
        rationale = f"Style-driven geometry for {style_name or 'the selected direction'}"
    else:
        profile = "balanced"
        rationale = "Professional default with distinct component roles"

    resolved = SHAPE_PROFILES[profile]
    return {
        "profile": profile,
        "label": resolved["label"],
        "rationale": rationale,
        "tokens": dict(resolved["tokens"]),
        "pill_policy": "Role-driven: full rounding is valid for compact semantic objects, established native or brand controls, and genuinely circular interactions; token spelling alone is not a failure",
        "approved_exceptions": _explicit_full_rounding_exceptions(context),
        "rules": [
            "Do not use a pill or capsule as generic decoration or as a default selected-state background",
            "Keep icon-only controls visually bare or use a compact rounded-square container; preserve the hit target with invisible padding",
            "Avoid a horizontal pill behind a standalone icon when it adds decoration but no state, grouping, platform, or brand meaning",
            "Use circles for avatars, FABs, record and media controls, swatches, or established compact icon controls when the silhouette communicates a real role; do not repeat them as generic chrome",
            "Use one radius scale consistently; nested surfaces must not all have the same exaggerated rounding",
            "Judge full rounding by component role and rendered repetition, not by the mere presence of rounded-full, 999px, Capsule, or an equivalent token",
        ],
    }


def build_layout_system(context: str, density_label: str | None = None) -> dict[str, Any]:
    """Build a restrained responsive layout foundation from product context."""
    lowered = context.casefold()
    if any(word in lowered for word in ("dashboard", "admin", "analytics", "monitor", "data", "erp", "crm")):
        max_width = "1440px"
        composition = "Persistent navigation plus a flexible data canvas; prioritize scan paths over card count"
    elif any(word in lowered for word in ("landing", "marketing", "portfolio", "conference", "campaign")):
        max_width = "1280px"
        composition = "Editorial section rhythm with one dominant focal point and intentional visual breaks"
    elif any(word in lowered for word in ("article", "docs", "reading", "editor", "form", "checkout")):
        max_width = "760px primary reading column"
        composition = "Focused single-column flow; introduce side content only when it supports the current task"
    else:
        max_width = "1200px"
        composition = "Responsive content grid with a clear primary region and restrained secondary surfaces"

    return {
        "max_width": max_width,
        "grid": "4 columns mobile / 8 tablet / 12 desktop; collapse by content pressure, not device labels alone",
        "gutters": "16px compact / 24px tablet / 32px desktop",
        "content_measure": "45-75 characters for long-form text",
        "breakpoints": "Use content-driven breakpoints; verify at 320, 375, 768, 1024, and 1440px",
        "density": density_label or "Balanced",
        "composition": composition,
        "rules": [
            "Create hierarchy with scale, spacing, alignment, and contrast before adding containers",
            "Use cards only for independent or actionable groups; prefer whitespace, headings, and dividers for ordinary grouping",
            "Make task priority legible; use one dominant action by default, or visually coordinate peer actions when the workflow genuinely gives them equal priority",
            "Preserve reading order and task priority when the layout collapses",
        ],
    }


def build_experience_pattern(
    context: str,
    landing_result: dict[str, Any],
    fallback_pattern: str,
) -> dict[str, str]:
    """Choose a product-flow pattern before falling back to landing-page data."""
    lowered = context.casefold()
    explicitly_marketing = any(
        marker in lowered
        for marker in ("landing page", "marketing site", "campaign", "homepage", "product launch", "waitlist")
    )

    if not explicitly_marketing and any(
        marker in lowered
        for marker in ("dashboard", "admin", "console", "operations", "analytics", "monitoring", "control center")
    ):
        return {
            "name": "Operations Workspace",
            "sections": "Persistent navigation > Context header and global status > Primary workspace > Secondary detail > Alerts and action feedback",
            "cta_placement": "Place the primary task action in the context header; keep object actions beside the affected object",
            "color_strategy": "Use neutral work surfaces, a restrained action accent, and semantic status colors with text or icons",
            "conversion": "Optimize time-to-detect, time-to-understand, and time-to-action rather than marketing conversion",
        }

    if not explicitly_marketing and any(
        marker in lowered
        for marker in ("mobile app", "ios app", "android app", "react native", "flutter", "swiftui", "jetpack compose")
    ):
        return {
            "name": "Task-First Mobile Shell",
            "sections": "Context header > Primary task or summary > Supporting content and actions > Persistent top-level navigation",
            "cta_placement": "Keep the task's dominant action in context and within a comfortable touch region; coordinate peer actions when the workflow gives them equal priority",
            "color_strategy": "Use semantic surfaces and one action accent; preserve status clarity in both themes",
            "conversion": "Optimize task completion, confidence, and return use",
        }

    if not explicitly_marketing and any(
        marker in lowered
        for marker in ("settings", "form", "checkout", "onboarding", "wizard", "application flow")
    ):
        return {
            "name": "Focused Task Flow",
            "sections": "Context and progress > Primary form or task > Inline help and validation > Review or confirmation",
            "cta_placement": "Place the primary action after the required task content; keep back or cancel visibly subordinate",
            "color_strategy": "Reserve accent for progress, focus, validation, and the primary completion action",
            "conversion": "Reduce errors, preserve entered work, and make recovery explicit",
        }

    return {
        "name": landing_result.get("Pattern Name", fallback_pattern or "Hero + Proof + Action"),
        "sections": landing_result.get("Section Order", "Hero > Value > Proof > Action"),
        "cta_placement": landing_result.get("Primary CTA Placement", "In the primary decision context"),
        "color_strategy": landing_result.get("Color Strategy", ""),
        "conversion": landing_result.get("Conversion Optimization", ""),
    }


def build_type_system(is_mobile: bool = False, compact: bool = False) -> dict[str, Any]:
    """Return a practical, role-based typography scale."""
    if compact and not is_mobile:
        tokens = {
            "display": "2rem / 2.5rem",
            "h1": "clamp(1.75rem, 2.5vw, 2.5rem) / 1.1",
            "h2": "1.5rem / 1.9rem",
            "h3": "1.125rem / 1.5rem",
            "body": "0.9375rem / 1.5",
            "label": "0.8125rem / 1.35",
            "caption": "0.75rem / 1.35",
        }
        mode = "Compact data-interface roles with a readable 15px body baseline"
    elif is_mobile:
        tokens = {
            "display": "36px / 40px",
            "h1": "32px / 38px",
            "h2": "24px / 30px",
            "h3": "20px / 26px",
            "body": "16px / 24px",
            "label": "14px / 20px",
            "caption": "12px / 16px",
        }
        mode = "Mobile-first fixed roles with system text scaling"
    else:
        tokens = {
            "display": "clamp(3rem, 7vw, 6rem) / 0.95",
            "h1": "clamp(2.25rem, 5vw, 4.5rem) / 1.0",
            "h2": "clamp(1.75rem, 3vw, 3rem) / 1.1",
            "h3": "clamp(1.25rem, 2vw, 1.75rem) / 1.25",
            "body": "1rem / 1.5",
            "label": "0.875rem / 1.35",
            "caption": "0.75rem / 1.4",
        }
        mode = "Fluid display roles plus stable reading sizes"

    return {
        "mode": mode,
        "tokens": tokens,
        "rules": [
            "Minimize font families and loaded styles; give every additional family a specific semantic, brand, script-coverage, numeric, or editorial role and verify its performance and fallback cost",
            "Build hierarchy through size, weight, line height, and space; do not rely on color alone",
            "Keep body copy at a readable base size and allow zoom or system text scaling without truncation",
            "Use tabular figures for aligned metrics, prices, timers, and dense numeric tables",
        ],
    }


def build_typography_director(
    context: str,
    typography: dict[str, Any] | None = None,
    type_system: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a content- and script-aware typography decision contract."""
    lowered = str(context or "").casefold()
    typography = typography or {}
    type_system = type_system or {}
    scripts: list[str] = []
    script_markers = (
        ("Cyrillic", ("cyrillic", "russian", "ukrainian", "bulgarian", "русский", "україн")),
        ("Arabic", ("arabic", "العربية")),
        ("Hebrew", ("hebrew", "עברית")),
        ("CJK", ("chinese", "japanese", "korean", "cjk", "中文", "日本語", "한국어")),
        ("Devanagari", ("devanagari", "hindi", "हिन्दी")),
        ("Greek", ("greek", "ελλην")),
        ("Thai", ("thai", "ไทย")),
        (
            "Latin Extended",
            (
                "vietnamese",
                "polish",
                "czech",
                "slovak",
                "turkish",
                "romanian",
                "hungarian",
                "tiếng việt",
            ),
        ),
    )
    for script, markers in script_markers:
        if any(marker in lowered for marker in markers):
            scripts.append(script)
    unicode_scripts = (
        ("Cyrillic", r"[\u0400-\u052f]"),
        ("Arabic", r"[\u0600-\u06ff\u0750-\u077f]"),
        ("Hebrew", r"[\u0590-\u05ff]"),
        ("Devanagari", r"[\u0900-\u097f]"),
        ("Greek", r"[\u0370-\u03ff]"),
        ("Thai", r"[\u0e00-\u0e7f]"),
        ("CJK", r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]"),
    )
    for script, pattern in unicode_scripts:
        if re.search(pattern, str(context or "")) and script not in scripts:
            scripts.append(script)
    if "rtl" in lowered and not any(script in scripts for script in ("Arabic", "Hebrew")):
        scripts.append("RTL script — confirm language")

    content_modes: list[str] = []
    mode_markers = (
        ("dense numeric and tabular data", ("dashboard", "analytics", "finance", "metrics", "table", "operations")),
        ("long-form reading", ("editorial", "article", "documentation", "knowledge", "reading", "report")),
        ("transactional forms and validation", ("form", "checkout", "onboarding", "application", "settings")),
        ("short expressive display copy", ("campaign", "landing", "marketing", "brand", "hero")),
        ("multilingual and localization stress", ("multilingual", "localization", "international", "locale", "translation")),
    )
    for mode, markers in mode_markers:
        if any(marker in lowered for marker in markers):
            content_modes.append(mode)
    if not content_modes:
        content_modes.append("general product UI with representative labels, values, and messages")

    heading = typography.get("heading", "the proposed heading family")
    body = typography.get("body", "the proposed body family")
    script_text = ", ".join(scripts) if scripts else "UNKNOWN — confirm every supported locale and script"
    requires_bidi = "rtl" in lowered or any(script in scripts for script in ("Arabic", "Hebrew"))
    return {
        "initial_status": "UNKNOWN — the retrieved pairing is a hypothesis until real content, glyph coverage, font files, and rendered metrics are inspected",
        "proposed_pair": f"{heading} for heading roles; {body} for body and interface roles, subject to repository and coverage evidence",
        "script_requirements": script_text,
        "direction_policy": (
            "Verify bidirectional text, mirrored directional controls, logical spacing, mixed-script values, numerals, and focus or reading order in the real platform"
            if requires_bidi
            else "Use logical layout properties and confirm direction per supported locale; do not hard-code left/right assumptions into reusable components"
        ),
        "content_modes": content_modes,
        "role_contract": {
            "interface_and_body": "Optimize legibility, label fit, punctuation, diacritics, and stable wrapping before personality",
            "display_and_heading": "Earn contrast through proportion, weight, width, or editorial treatment; do not rely on an oversized generic headline",
            "data_and_code": "Use tabular figures for aligned values and introduce monospace only for identifiers, code, logs, or another explicit semantic role",
        },
        "font_count_policy": "Minimize families and loaded styles, but judge each additional family by semantic role, script coverage, metrics, performance, and fallback behavior rather than count alone",
        "fallback_policy": "Choose fallbacks with compatible x-height, width, weight, numeral behavior, and script coverage; test the actual fallback instead of listing system-ui as decoration",
        "stress_content": [
            "Longest realistic heading, navigation label, button label, validation message, and localized expansion",
            "Dense rows with large values, decimals, percentages, dates, times, currencies, and identifiers when applicable",
            "Mixed case, punctuation, diacritics, missing glyphs, synthetic bold or italic, and font-loading failure",
        ],
        "verification": [
            "Confirm licensed files or installed dependencies, required weights, variable axes, subsets, required glyph coverage, and loading strategy",
            "Render representative content at compact, intermediate, and wide widths plus zoom or system text scaling",
            "Inspect x-height, character width, line breaks, line height, baseline alignment, numeral alignment, and focus or validation text",
            "Reject the pairing if fallback, localization, or real content changes hierarchy or causes clipping; record the replacement and evidence",
        ],
        "type_scale_reference": type_system.get("mode", "Use the role-based scale as a starting hypothesis"),
    }


def build_creative_distinction_gate(
    context: str,
    category: str = "General",
    pattern_name: str = "",
    style_name: str = "",
) -> dict[str, Any]:
    """Require product-specific identity without forcing decorative novelty."""
    lowered = str(context or "").casefold()
    established = any(
        marker in lowered
        for marker in ("existing", "current interface", "polish", "refine", "established", "repository")
    )
    carriers: list[str] = []
    if any(marker in lowered for marker in ("dashboard", "analytics", "data", "monitor", "operations")):
        carriers.extend(("information composition and scan path", "domain data treatment"))
    if any(marker in lowered for marker in ("editorial", "documentation", "article", "knowledge", "report")):
        carriers.extend(("typographic hierarchy and reading rhythm", "content structure"))
    if any(marker in lowered for marker in ("creator", "media", "gallery", "portfolio", "campaign", "commerce", "shop")):
        carriers.extend(("imagery or content framing", "interaction and transition model"))
    for fallback in ("composition", "typography", "product language and real content"):
        if fallback not in carriers:
            carriers.append(fallback)
    return {
        "mode": "Preserve and sharpen established identity" if established else "Establish product-specific identity",
        "initial_status": "UNKNOWN — distinctiveness must be demonstrated in a rendered comparison, not asserted from style labels",
        "product_anchor": f"Derive the identity from {category}'s real objects, workflow, data, language, or audience rather than from {style_name or 'a trend name'} alone",
        "candidate_carriers": carriers[:4],
        "ownable_move": "Choose one repeatable composition, typographic, content, imagery, data, or interaction decision that improves the task; an added ornament is optional and must have a repetition boundary",
        "template_risks": [
            "Generic centered headline plus gradient word, floating mockup, and identical icon-card grid",
            "Default component-library composition with only palette, radius, and font substitutions",
            "Uniform card sizing, equal visual weight, stock value icons, and one accent treatment repeated on every surface",
            "A signature motif that appears so often it becomes another decorative texture",
        ],
        "proof_questions": [
            "Can the direction be described through a product-specific noun, workflow, data shape, or content behavior rather than only aesthetic adjectives?",
            "Would the composition and hierarchy still feel intentional with the logo, gradient, and decorative effects temporarily removed?",
            "Does the ownable move improve recognition, comprehension, or task flow, and is its repetition explicitly bounded?",
            "For an established product, does the refinement sharpen recognizable equity instead of replacing it for novelty?",
        ],
        "pass_rule": "Pass only when the rendered interface has a coherent product-specific identity, the primary task remains clearer than the signature, and the result cannot be reduced to a component-library demo or generic SaaS recipe",
        "subtraction_test": "Remove one decorative layer at a time; keep only treatments whose removal materially weakens hierarchy, meaning, brand recognition, or feedback",
        "context_snapshot": f"Pattern: {pattern_name or 'unresolved'} | Style hypothesis: {style_name or 'unresolved'}",
    }


def build_rendered_critic(context: str = "") -> dict[str, Any]:
    """Return a bounded render-review and targeted-correction loop."""
    lowered = str(context or "").casefold()
    refinement = any(marker in lowered for marker in ("existing", "polish", "refine", "current interface"))
    return {
        "initial_status": "UNKNOWN — no visual-quality claim is valid until the real interface is rendered and inspected",
        "baseline": (
            "Capture the current interface beside the refinement at identical content, state, viewport, and theme"
            if refinement
            else "Use the selected implementation contract and direction card as the comparison baseline"
        ),
        "required_evidence": [
            "Representative real content at compact, intermediate, and wide sizes",
            "Default plus applicable focus, selected, disabled, loading, empty, error, success, and overflow states",
            "Every supported theme and relevant zoom, text-scaling, reduced-motion, high-contrast, pointer, and touch mode",
        ],
        "lenses": [
            {"name": "Composition", "inspect": "focal order, reading path, alignment axes, grouping, balance, and responsive reflow"},
            {"name": "Typography", "inspect": "hierarchy, measure, wrapping, x-height, weight, numeral behavior, labels, and localization stress"},
            {"name": "Density", "inspect": "visible control geometry, whitespace rhythm, scan efficiency, hit areas, and information compression"},
            {"name": "Noise and identity", "inspect": "card nesting, pills, icon containers, shadows, gradients, glow, repeated motifs, source coherence, and template resemblance"},
        ],
        "workflow": [
            "Capture the functionally correct render before polishing and compare it with the selected contract or prior baseline",
            "Run one critic pass across all lenses; record only evidence-visible findings with severity, consequence, and a concrete correction",
            "Apply the smallest coherent correction set that resolves blockers and majors without reopening the whole art direction",
            "Rerender the same evidence set and verify the corrected findings; treat this as verification, not a new taste pass",
        ],
        "finding_schema": "Severity | viewport/state | visible evidence | task or system consequence | correction | verification",
        "severity_rule": "Use BLOCKER for requirement, accessibility, content, or task failure; MAJOR for clear hierarchy, coherence, responsive, or identity harm; MINOR for local polish that does not impede the task; UNKNOWN when the required render or state is missing",
        "stop_rule": "Use one full critic pass by default. Run another full pass only when a correction materially changes composition or a blocker or major remains; otherwise stop after targeted verification and disclose untested evidence",
        "anti_loop": "Do not perform tweak roulette, pixel-delta scoring, or endless screenshot churn; every change must answer a recorded finding",
    }


def build_project_memory_policy() -> dict[str, Any]:
    """Describe the durable, evidence-aware project design memory contract."""
    return {
        "file": "PROJECT-MEMORY.md",
        "statuses": "PROPOSED | CONFIRMED | SUPERSEDED",
        "read_rule": "Read confirmed memory before material UI decisions, then verify it against the current repository, brief, and brand assets",
        "write_rule": "Initialize once; never overwrite confirmed human or repository-backed decisions during regeneration. Add or supersede entries only with evidence, scope, owner, and revisit trigger",
        "precedence": "Current explicit requirements and verified repository or brand evidence > confirmed project memory > scoped page overrides > MASTER defaults > generated hypotheses",
        "scope_rule": "Record project-wide decisions, stable source roles, approved exceptions, rejected repetitions, and verification evidence; keep temporary experiments and private reasoning out of memory",
    }


def build_option_exploration(context: str = "") -> dict[str, Any]:
    """Return the always-on Explore → Compare → Commit contract for material decisions."""
    return {
        "mode": "ALWAYS ON for material design decisions",
        "principle": "Search the full relevant option space after hard product, platform, script, accessibility, brand, license, performance, and scope constraints; treat repository, native, installed, and current-token choices as the baseline rather than the outer boundary",
        "scope_boundary": "Do not enumerate an infinite catalog or reopen confirmed invariants, learned platform conventions, unchanged routine tokens, or narrow bug-fix choices. Promote any unclear, weak, rejected, or materially challenged baseline to full exploration and stop at documented evidence saturation.",
        "context_snapshot": context.strip() or "No context supplied; derive the relevant universe from repository and brief evidence",
        "sequence": [
            "Declare the material decision, real user consequence, hard constraints, current baseline, relevant candidate classes, authoritative sources, and evidence-backed exclusions",
            "Explore concrete repository and external options for semantic and visual quality without dependency, migration, lockfile, procurement, familiarity, or maintenance penalties; only proven legal, platform, or hard-delivery incompatibility may pre-eliminate a candidate",
            "Compare finalists on identical real content, viewport, state, theme, size, script, and task; catalog pages, package names, font names, trend labels, moodboards, and demo clips are discovery evidence rather than comparison proof",
            "Record the semantic and visual ranking before applying license, bundle or loading, implementation, migration, maintenance, ownership, and lockfile cost",
            "Commit one coherent winner, document why the strongest alternative lost, integrate only the winner when authorized, and remove or avoid speculative comparison dependencies and assets",
        ],
        "domains": [
            {
                "domain": "Visual direction and composition",
                "coverage": "Current baseline plus every structurally distinct direction that represents a material product trade-off",
                "proof": "Same real content and requirements through the direct, refinement, or full art-direction gate; palette-only variants do not count",
            },
            {
                "domain": "Typography",
                "coverage": "Applicable repository, platform, open, and licensed foundry or catalog candidates filtered by scripts, weights, axes, numerals, tone, license, loading, and platform constraints",
                "proof": "Render the baseline and at least three strongest external finalists when available with real headings, body, labels, localization stress, numerals, and fallback behavior; a font-name list or specimen page does not count",
            },
            {
                "domain": "Iconography",
                "coverage": "Concrete glyphs from every relevant family class, including at least three uninstalled sources in broad cases when available",
                "proof": "Render at least two external finalists beside the installed baseline at the exact UI size, state, label, and surface",
            },
            {
                "domain": "Color and material",
                "coverage": "Complete semantic role systems and material treatments appropriate to product, brand, themes, content, and states rather than isolated swatches",
                "proof": "Apply finalists to the same hierarchy, controls, data, states, and themes; measure applicable contrast and inspect repetition",
            },
            {
                "domain": "Shape, surfaces, controls, and components",
                "coverage": "Coherent geometry and density systems plus behaviorally viable native, repository, and stack-appropriate primitives",
                "proof": "Render representative controls with focus, selected, disabled, error, content expansion, keyboard behavior, and target behavior; component-gallery aesthetics do not decide",
            },
            {
                "domain": "Imagery and illustration",
                "coverage": "Verified brand or repository assets plus relevant licensed, commissioned, generated, diagrammatic, or data-led directions",
                "proof": "Compare finalists in the real crop and layout with provenance, rights, responsive behavior, loading, and text contrast",
            },
            {
                "domain": "Motion",
                "coverage": "Static or reduced-motion baseline plus every materially relevant functional transition model",
                "proof": "Exercise the real interaction, interruption, repeated use, reduced motion, and runtime behavior rather than approving a demo clip",
            },
            {
                "domain": "Data visualization",
                "coverage": "Every chart family capable of answering the real analytical question after incompatible encodings are rejected with evidence",
                "proof": "Render strongest encodings with representative data, labels, extremes, empty or error states, and accessible text or table support",
            },
        ],
        "closure_rule": "Close only after the relevant universe and exclusions are declared, every applicable candidate class has concrete evidence, external challengers and same-context finalist renders exist, quality ranking precedes integration economics, the strongest rejected option is recorded, and no unsearched relevant class is reasonably likely to change the winner; otherwise keep the decision UNKNOWN",
        "record": "decision | candidate class | exact candidate/source | baseline or external | constraints passed | same-context render | semantic/visual finding | integration finding | advance/reject reason",
        "anti_shortcuts": [
            "Do not stop at the first acceptable installed, familiar, or easy-to-integrate option",
            "Do not call a search-result list, catalog skim, moodboard, font-name list, package comparison, or isolated demo a finalist comparison",
            "Do not apply dependency, bundle, migration, procurement, or maintenance cost before semantic and visual ranking",
            "Do not continue through near-duplicates after every relevant class is covered and evidence saturation is documented",
        ],
    }


def _established_icon_sources(context: str) -> list[str]:
    """Detect repository-established icon sources in textual order."""
    query = context.casefold()
    aliases = (
        ("material symbols", "Material Symbols"),
        ("fluent ui system icons", "Fluent UI System Icons"),
        ("bootstrap icons", "Bootstrap Icons"),
        ("font awesome", "Font Awesome"),
        ("simple icons", "Simple Icons"),
        ("carbon icons", "Carbon Icons"),
        ("custom svg", "Repository custom SVG"),
        ("sf symbols", "SF Symbols"),
        ("radix icons", "Radix Icons"),
        ("remix icon", "Remix Icon"),
        ("tabler icons", "Tabler Icons"),
        ("hugeicons", "Hugeicons Free"),
        ("heroicons", "Heroicons"),
        ("phosphor", "Phosphor"),
        ("iconoir", "Iconoir"),
        ("lucide", "Lucide"),
        ("tabler", "Tabler Icons"),
    )
    repository_markers = (
        "already uses",
        "currently uses",
        "uses ",
        "existing",
        "installed",
        "established",
        "repository",
        "repo uses",
        "using lucide",
        "using phosphor",
        "using tabler",
        "using iconoir",
        "using heroicons",
        "using hugeicons",
        "установлен",
        "использует",
        "используются",
        "уже есть",
        "в проекте стоят",
        "в проекте есть",
        "проекте стоят",
        "проекте используются",
        "проекте установлен",
        "репозитор",
    )
    if not any(marker in query for marker in repository_markers):
        return []
    hits: list[tuple[int, str]] = []
    for alias, family in aliases:
        position = query.find(alias)
        if position >= 0:
            hits.append((position, family))
    ordered: list[str] = []
    for _, family in sorted(hits):
        if family not in ordered:
            ordered.append(family)
    return ordered


def _established_icon_family(context: str) -> str | None:
    """Return the likely primary repository family while retaining source inventory elsewhere."""
    sources = _established_icon_sources(context)
    return sources[0] if sources else None


def _contextual_icon_family_candidates(context: str, is_mobile: bool) -> list[dict[str, str]]:
    """Return product- and platform-relevant source challengers."""
    query = context.casefold()
    if any(marker in query for marker in ("ios", "ipados", "macos", "swiftui", "apple")):
        return [
            {"family": "SF Symbols", "reason": "Native Apple surfaces, text alignment, localization, weights, and platform behavior"},
            {"family": "Iconoir", "reason": "Alternative primary interface source when a shared cross-platform implementation needs one portable drawing language"},
            {"family": "Phosphor", "reason": "Alternative primary interface source for a shared app that needs broader weights and coverage"},
        ]
    if any(marker in query for marker in ("android", "jetpack compose", "material")):
        return [
            {"family": "Material Symbols", "reason": "Native Material states, optical sizes, and Android implementation"},
            {"family": "Phosphor", "reason": "Alternative primary interface source when a shared cross-platform implementation needs one portable drawing language"},
            {"family": "Iconoir", "reason": "Alternative primary source for a non-Material cross-platform product voice"},
        ]
    if any(marker in query for marker in ("dashboard", "admin", "operations", "analytics", "monitoring", "data-dense", "inspector")):
        return [
            {"family": "Tabler Icons", "reason": "Broad technical coverage and a precise 24px system for dense products"},
            {"family": "Radix Icons", "reason": "Crisp 15px controls for compact web toolbars and inspectors"},
            {"family": "Iconoir", "reason": "A more distinctive monoline alternative for navigation and product concepts"},
        ]
    if is_mobile or any(marker in query for marker in ("consumer", "lifestyle", "creator", "social", "media", "education")):
        return [
            {"family": "Phosphor", "reason": "Flexible weights and broad cross-platform coverage without changing families"},
            {"family": "Hugeicons Free", "reason": "Broad domain coverage when a basic utility set lacks the literal object or activity"},
            {"family": "Remix Icon", "reason": "Paired outline and fill variants for navigation and selected states"},
        ]
    return [
        {"family": "Lucide", "reason": "Disciplined general-purpose system actions and broad framework support"},
        {"family": "Iconoir", "reason": "Distinctive monoline product and navigation vocabulary"},
        {"family": "Phosphor", "reason": "Flexible weights and richer domain coverage within one coherent family"},
    ]


def _icon_family_candidates(context: str, is_mobile: bool) -> list[dict[str, str]]:
    """Return installed sources plus installable challengers; inventory is not an allowlist."""
    established_sources = _established_icon_sources(context)
    challengers = _contextual_icon_family_candidates(context, is_mobile)
    broad_pool = [
        {"family": "Tabler Icons", "reason": "Broad specialist catalog for literal technical, transport, and operational subjects"},
        {"family": "Iconoir", "reason": "Distinctive monoline vocabulary for product navigation and domain objects"},
        {"family": "Phosphor", "reason": "Multiple coherent weights and broad object coverage for optical comparison"},
        {"family": "Remix Icon", "reason": "Paired outline and fill catalog for content-rich web products and selected states"},
        {"family": "Heroicons", "reason": "Conventional 16px, 20px, and 24px web variants for a restrained baseline"},
        {"family": "Radix Icons", "reason": "Compact 15px source to test whether the role belongs in a dense control surface"},
        {"family": "Material Symbols", "reason": "Large optical-size-aware catalog when a Material drawing language or exact domain glyph is relevant"},
        {"family": "Lucide", "reason": "Disciplined geometric baseline for familiar product UI"},
        {"family": "Hugeicons Free", "reason": "Broad rounded-stroke catalog for literal domain objects and activities"},
    ]
    seen_challengers = {candidate["family"] for candidate in challengers}
    challengers.extend(
        candidate for candidate in broad_pool if candidate["family"] not in seen_challengers
    )
    candidates: list[dict[str, str]] = []
    for index, family in enumerate(established_sources):
        candidates.append(
            {
                "family": family,
                "status": "observed repository source",
                "reason": (
                    "Observed first and treated as the likely primary interface source; keep it when coverage and rendered fit are strong"
                    if index == 0
                    else "Observed as an auxiliary source; retain it inside a documented role boundary when compatibility remains coherent"
                ),
            }
        )
    for challenger in challengers:
        if challenger["family"] in established_sources:
            continue
        candidates.append(
            {
                **challenger,
                "status": "installable candidate — acquire only if selected by the dependency gate",
            }
        )
    return candidates


def _requires_broad_icon_exploration(context: str) -> bool:
    """Detect an explicit request to look beyond the current icon-source inventory."""
    query = context.casefold()
    markers = (
        "other icon librar",
        "different icon librar",
        "new icon librar",
        "external icon",
        "cross-library",
        "expand the icon",
        "broader icon",
        "best available icon",
        "compare icon libraries",
        "look beyond",
        "none of these icons",
        "другие библиотек",
        "новые библиотек",
        "сторонние икон",
        "расширить пул",
        "расшири пул",
        "сравни библиотек",
        "посмотри другие",
        "поищи другие",
        "не только lucide",
        "не только hugeicons",
        "лучшие иконк",
        "банальные иконк",
    )
    return any(marker in query for marker in markers)


def build_iconography(is_mobile: bool = False, context: str = "") -> dict[str, Any]:
    """Return a role-first icon system with anti-cliche metaphor guidance."""
    context_lower = context.casefold()
    is_dense = any(
        marker in context_lower
        for marker in ("dashboard", "admin", "operations", "analytics", "monitoring", "data-dense", "inspector")
    )
    target = (
        "44pt minimum on Apple touch platforms; 48dp recommended on Android"
        if is_mobile
        else "Aim for at least 24x24 CSS px or meet WCAG 2.2 AA spacing exceptions; prefer 44x44 CSS px for primary touch controls"
    )
    established_family = _established_icon_family(context)
    established_sources = _established_icon_sources(context)
    broad_exploration = _requires_broad_icon_exploration(context)
    return {
        "visual_size": (
            "16-20px for dense desktop controls and 20-24px for primary navigation; compare optical weight at the rendered size"
            if is_dense and not is_mobile
            else "20-24px/pt/dp for common controls; adjust optical weight at the rendered size instead of scaling arbitrarily"
        ),
        "target_size": target,
        "container": "Transparent hit area by default; compact rounded square only when containment communicates state or grouping",
        "family_strategy": (
            "Repository evidence first, but installed packages are a baseline rather than a closed allowlist. Define a primary interface drawing language and map every source to a stable role. Complete semantic and visual discovery before applying dependency economics: in broad cross-library mode, a strong installed glyph cannot end the search before concrete external candidates are rendered. For authorized implementation work, install the single selected official adapter when package-based, or integrate the selected official native or asset source through its platform mechanism, after the dependency gate passes; do not use package count as a quality metric or acquire every evaluated candidate."
        ),
        "established_family": established_family,
        "established_sources": established_sources,
        "source_policy": (
            "Judge the rendered icon language, not installation state or dependency count: an uninstalled source may be the correct choice, multiple sources can be coherent when roles are intentional, and one package can still be incoherent when weights, fills, sizes, or metaphors are inconsistent"
        ),
        "family_candidates": _icon_family_candidates(context, is_mobile),
        "exploration_gate": {
            "mode": (
                "BROAD cross-library exploration — explicitly requested; closure evidence is mandatory before selection"
                if broad_exploration
                else "BROAD by default for every non-universal product, domain, navigation, status, or signature icon; ROUTINE is allowed only for a confirmed learned universal action with coherent primary-source coverage"
            ),
            "promotion_triggers": "Other or new libraries, wider icon pool, best available glyph, rejected current candidates, weak primary coverage, a high-cliche shortcut, or an unresolved product metaphor",
            "early_stop_rule": "A strong installed candidate, lower dependency cost, or a catalog skim never closes BROAD exploration; those factors may influence the final decision only after closure evidence exists",
            "closure_evidence": [
                "Declare every platform- and role-relevant family in the bundled registry and expand to current official catalogs or authoritative registries when the local snapshot lacks the subject",
                "Inspect concrete named glyphs from at least three relevant uninstalled families when available, plus the installed baseline; if fewer exist, record the official source, exact search terms, and no-result or incompatibility evidence for every missing slot",
                "Render the strongest candidate from at least two uninstalled families beside the installed baseline with identical visible size, color, label, state, and surface; a package name, catalog landing page, or text-only description does not count as comparison",
                "Record family, exact glyph or export, official source, metaphor, target-size render status, semantic and visual finding, and advance or reject reason",
            ],
            "decision_phases": [
                "Phase A — rank semantic specificity, recognition, silhouette, detail, optical balance, and drawing-language fit without penalizing installation state, lockfile change, bundle, migration, or maintenance cost; only a proven legal or platform incompatibility may pre-eliminate a source",
                "Phase B — after exploration closes and Phase A is recorded, apply compatibility, license, bundle or asset loading, migration, maintenance, and dependency cost; the installed source may win here, but not by truncating Phase A",
            ],
        },
        "role_rules": {
            "universal_actions": "Keep learned platform symbols for search, close, back, delete, disclosure, upload, and download; novelty reduces recognition here",
            "product_and_domain": "Write `real subject → mechanism/output`, explore enough plausible candidates to make a real decision, starting with the primary source; map the actual object, input, output, mechanism, or consequence instead of reusing one generic value symbol",
            "status": "Use a familiar state shape plus text when consequence matters; never rely on icon color alone",
            "brand": "Use only current official assets and record provenance and license constraints",
        },
        "selection_order": [
            "Inventory existing icon imports, wrappers, custom SVGs, native symbols, and licenses before selecting anything",
            "Classify the need as universal action, navigation, status, data view, product/domain concept, brand, or decoration",
            "For universal actions keep the familiar symbol; for every product concept write `real subject → mechanism/output` before searching glyphs",
            "Choose ROUTINE or BROAD exploration before searching; every non-universal product, domain, navigation, status, or signature icon and every explicit request for other libraries, a wider pool, or the best available glyph selects BROAD",
            "Search verified named candidates one source at a time with the real subject and mechanism/output; in BROAD mode complete the external-source and render evidence instead of stopping at an acceptable installed result",
            "Produce the semantic and visual ranking first, then apply compatibility and dependency economics; select a challenger when it remains stronger after both phases",
            "For an authorized build or change task, install the selected official stack adapter with the repository package manager when it is not present; for review-only work, record the recommendation without mutating dependencies",
            "If no clear symbol survives, choose between visible text, a compatible auxiliary source, or a repository-owned SVG based on recognition, ownership, bundle, and maintenance evidence; do not force an abstract icon",
        ],
        "decision_record": "`real subject → mechanism/output` | role | primary drawing language | candidates considered | chosen metaphor and why | source and exception role if any | installed/reused/acquired | package and verified version | license/provenance | compatibility evidence | label requirement",
        "cliche_guard": [dict(item) for item in ICON_CLICHE_GUARD],
        "dependency_acquisition": {
            "authority": "In an authorized implementation, build, refactor, or change task, adding the selected package-based icon dependency or official platform integration is a normal scoped implementation step; do not stop merely because the strongest source is not already present. In review, audit, or direction-only work, recommend it without changing the repository.",
            "selection_rule": "In BROAD mode, begin this gate only after exploration closure and semantic or visual ranking. Then install one selected source at a time only after it wins on role coverage, recognition, drawing-language fit, platform support, accessibility, license, bundle behavior, and maintenance; never install the whole comparison set speculatively.",
            "verification": [
                "Use current official documentation and the authoritative package registry to confirm the exact stack adapter, latest compatible version, license or usage terms, supported exports, maintenance state, and framework or platform requirements; do not rely on remembered package names or the local snapshot alone",
                "Detect the repository package manager from packageManager metadata and lockfiles; preserve its existing version and workspace conventions",
                "Check tree shaking or asset loading, ESM/CJS and SSR or native compatibility where relevant, type support, bundle or binary cost, and whether the candidate requires fonts, global CSS, raw SVG redistribution, or paid assets",
            ],
            "installation": [
                "For a package-based source, install the selected official adapter as a runtime dependency with the repository package manager so the manifest and lockfile update together; do not hand-edit a version when the package manager is available. For native symbols, fonts, or official assets, use the platform-supported integration and availability checks instead of inventing a package",
                "Add or extend a shared icon wrapper and document the new source role; migrate only the approved role instead of replacing unrelated icons opportunistically",
                "Run dependency, build, type or static, test, and bundle checks supported by the repository, then render the icon beside neighboring sources at actual sizes and states",
                "If compatibility, licensing, build, or footprint evidence fails, remove the dependency with the same package manager and use the next qualified option or a repository-owned SVG",
            ],
            "stop_conditions": "Do not install when the task is read-only, the repository explicitly forbids new dependencies, the official package or license cannot be verified, the source requires unauthorized paid terms, or the role boundary and maintenance owner cannot be stated",
        },
        "compatibility_gate": [
            "Assign each source a stable role such as interface actions, native controls, brands/providers, specialized domain objects, illustration, or migration legacy; do not alternate sources by personal preference",
            "Compare grid, stroke or fill behavior, caps, joins, corner language, negative space, detail level, baseline, and optical weight in the rendered surface",
            "Normalize size, color, alignment, accessible naming, and state behavior through one wrapper; do not distort internal geometry merely to fake sameness",
            "Check license, provenance, current package-version support, tree shaking or asset cost, and long-term maintenance before installing, adding, or retaining a source",
            "Document intentional exceptions and remove accidental duplicates; package count alone is neither a pass nor a failure",
        ],
        "custom_icon_gate": [
            "Treat a missing glyph as a design decision: compare visible text, a compatible auxiliary source, and a repository-owned SVG rather than defaulting automatically to any one option",
            "Create a repository-owned SVG for a recurring domain concept or signature navigation role only when the team can own its source, provenance, maintenance, and accessibility",
            "Do not replace learned universal actions with custom glyphs and do not use an unfamiliar one-off icon without visible text",
            "Match the declared drawing language or document why a deliberate role boundary uses a different one",
            "Review at 16px, 20px, and 24px plus disabled, selected, light, and dark states; simplify paths that collapse or blur",
            "Store source and license provenance, use currentColor where appropriate, and provide an accessible name through the control",
        ],
        "normalization": {
            "grid": "Preserve each source's internal geometry; normalize visible size and alignment through the wrapper, and redraw only repository-owned assets when a shared grid is an explicit design requirement",
            "stroke": "Choose one default weight and explicit selected/filled exceptions; do not globally override stroke width if it breaks supplied artwork",
            "alignment": "Align by optical center and baseline, not only by SVG bounds",
            "color": "Use currentColor and semantic foreground roles; reserve multicolor artwork for verified brand or meaningful data",
        },
        "rules": [
            "Prefer an established primary source when it already covers the role clearly, but install a documented role-specific source when it materially improves recognition, domain coverage, or platform fidelity without visual fragmentation",
            "Never use an acceptable installed glyph or dependency cost as an early-stop rule when broad cross-library exploration was requested; close discovery with exact external candidates and same-context renders first",
            "Keep one coherent drawing language per role and surface; consistency is evaluated from rendered geometry and behavior rather than dependency count",
            "Do not add or reject a source solely because one glyph is missing; compare recognition, compatibility, ownership, bundle, license, and maintenance trade-offs",
            "Label unfamiliar icon-only actions with accessible names and visible text when ambiguity remains",
            "Do not use emoji as structural navigation, toolbar, or system-control icons",
            "Indicate selected navigation with color, weight, underline, side marker, or tonal surface—not a decorative pill behind every icon",
            "Treat sparkles, wands, brains, rockets, shields, lightning, globes, puzzle pieces, cubes, generic charts, trophies, stars, and gears as high-cliche-risk symbols: use them when literal, learned, branded, or demonstrably clearest—not as automatic shorthand for product value",
        ],
    }


def build_control_sizing(is_mobile: bool = False, compact: bool = False) -> dict[str, Any]:
    """Return restrained visible control sizes separated from hit-target size."""
    if is_mobile:
        mode = "Touch / Mobile"
        control_height = "40-44px/pt visible starting range; use the native 48dp geometry where the Android component or task calls for it"
        compact_height = "36-40px/pt visible geometry for secondary controls when the platform, content, and non-overlapping target permit"
        icon_control = "32-40px/pt visible geometry with a 44pt or 48dp non-overlapping interaction target"
        css_height = "44px"
        css_icon_size = "40px"
        css_padding_inline = "16px"
        css_input_padding = "10px 14px"
    elif compact:
        mode = "Compact Desktop"
        control_height = "32-36px visible default"
        compact_height = "28-32px only for expert dense toolbars with verified target spacing"
        icon_control = "28-32px visible container; preserve at least a 24x24 CSS px target and enlarge for coarse pointers"
        css_height = "32px"
        css_icon_size = "32px"
        css_padding_inline = "12px"
        css_input_padding = "6px 10px"
    else:
        mode = "Standard Desktop"
        control_height = "36-40px visible default"
        compact_height = "32-36px for secondary and toolbar controls"
        icon_control = "32-36px visible container; preserve at least a 24x24 CSS px target and enlarge for coarse pointers"
        css_height = "36px"
        css_icon_size = "36px"
        css_padding_inline = "14px"
        css_input_padding = "8px 12px"

    return {
        "mode": mode,
        "control_height": control_height,
        "compact_height": compact_height,
        "icon_control": icon_control,
        "width": "Fit content by default; full width only when the task flow, narrow layout, or primary form action benefits from it",
        "select": "Match adjacent field height; keep a persistent label, compact chevron, and content-driven width instead of an oversized capsule",
        "segmented": "Size to its short labels and available width; do not stretch a small choice set into a dominant full-width control without a layout reason",
        "principle": "Separate visible surface size from interaction target size; use transparent non-overlapping padding instead of inflated backgrounds",
        "measurement_policy": "Treat these ranges as starter tokens, not pass/fail thresholds; preserve native component geometry or depart from the range when content, density, input mode, brand, or measured usability provides a better reason",
        "css_height": css_height,
        "css_icon_size": css_icon_size,
        "css_padding_inline": css_padding_inline,
        "css_input_padding": css_input_padding,
    }


def build_component_guidance(
    shape_system: dict[str, Any],
    control_sizing: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Create component rules that consume the resolved radius tokens."""
    tokens = shape_system["tokens"]
    sizing = control_sizing or build_control_sizing()
    return {
        "buttons": f"Use a clear text label, make task priority visible, apply {tokens['control']} radius, and start from {sizing['control_height']}; size to content instead of defaulting to a huge or full-width control, while allowing coordinated peer actions when the workflow calls for them",
        "icon_buttons": f"Use {sizing['icon_control']} with {tokens['icon_container']} radius and no visible background until hover, press, focus, or selection requires one",
        "chips": f"Use only for tags, filters, statuses, compact choices, or entered entities; default to {tokens['chip']} radius and avoid wrapping labels",
        "navigation": "Keep placement stable and show selection without a capsule behind each icon or icon-label pair",
        "cards": f"Use {tokens['card']} radius only for independent grouped content; ordinary sections should remain uncarded",
        "inputs": f"Use persistent labels, clear help/error text, {tokens['control']} radius, and {sizing['control_height']}; never inflate fields to create visual importance",
        "selects": sizing["select"],
        "segmented_controls": sizing["segmented"],
        "overlays": f"Use {tokens['overlay']} radius, a clear escape path, focus management, and a scrim only when it improves separation",
    }


_HEX_RE = re.compile(r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?\b")


def _first_hex(value: Any) -> str | None:
    match = _HEX_RE.search(str(value or ""))
    if not match:
        return None
    value = match.group(0)
    if len(value) == 4:
        value = "#" + "".join(character * 2 for character in value[1:])
    return value.upper()


def _relative_luminance(hex_color: str) -> float:
    channels = [int(hex_color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def color_luminance(value: Any) -> float | None:
    """Return relative luminance for the first solid hex color in ``value``."""
    color = _first_hex(value)
    return _relative_luminance(color) if color else None


def explicit_cool_color_request(context: str) -> bool:
    """Return whether a cool chromatic *foundation* or supplied palette is explicit.

    A blue accent, hero gradient, or focus color does not authorize blue-washed
    structural surfaces. Foundation permission needs palette, theme, canvas, or
    surface language near the requested color.
    """
    lowered = str(context or "").casefold()
    color_terms = (
        "blue",
        "cyan",
        "indigo",
        "navy",
        "violet",
        "purple",
        "син",
        "голуб",
        "циан",
        "индиго",
        "фиолет",
        "пурпур",
    )
    foundation_terms = (
        "palette",
        "theme",
        "foundation",
        "canvas",
        "background",
        "surface system",
        "surface palette",
        "brand tokens",
        "provided colors",
        "overall visual language",
        "visual identity",
        "палитр",
        "цветовая система",
        "цветовая основа",
        "холст",
        "фон",
        "поверхност",
        "бренд-токен",
        "фирменн цвет",
        "предоставленн цвет",
        "визуальный язык",
        "визуальная айдентика",
    )
    explicit_palette = any(
        term in lowered and not _term_is_negated(lowered, term)
        for term in (
            "brand palette",
            "provided palette",
            "supplied palette",
            "existing palette",
            "фирменная палитра",
            "фирменную палитру",
            "брендовая палитра",
            "брендовую палитру",
            "предоставленная палитра",
            "предоставленную палитру",
            "существующая палитра",
            "существующую палитру",
        )
    )
    if not explicit_palette and "палитр" in lowered:
        palette_match = next(re.finditer("палитр", lowered), None)
        explicit_palette = bool(
            palette_match
            and not _position_is_negated(lowered, palette_match.start())
            and any(marker in lowered for marker in ("фирменн", "брендов", "предоставленн", "существующ"))
        )
    if explicit_palette:
        return True

    treatment_policy = build_visual_treatment_policy(lowered)
    scoped_gradient = bool(
        treatment_policy.get("allow_gradient") and not treatment_policy.get("allow_gradient_style")
    )
    neutral_markers = ("neutral", "neutralized", "нейтраль", "ахромат")
    for color_term in color_terms:
        for match in re.finditer(re.escape(color_term), lowered):
            if _position_is_negated(lowered, match.start()):
                continue
            window = _local_treatment_window(lowered, match.start(), match.end(), radius=56)
            if not any(term in window for term in foundation_terms):
                continue
            if any(marker in window for marker in neutral_markers):
                continue
            if scoped_gradient and any(marker in window for marker in _GRADIENT_MARKERS):
                continue
            return True

    hex_colors = _HEX_RE.findall(lowered)
    return len(hex_colors) >= 2 and any(term in lowered for term in foundation_terms)


def _is_cool_chromatic(value: Any) -> bool:
    color = _first_hex(value)
    if not color:
        return False
    red, green, blue = (int(color[index : index + 2], 16) / 255 for index in (1, 3, 5))
    hue, lightness, saturation = colorsys.rgb_to_hls(red, green, blue)
    hue_degrees = hue * 360
    return 185 <= hue_degrees <= 285 and saturation >= 0.22 and 0.08 <= lightness <= 0.92


def neutralize_unrequested_cool_foundation(
    colors: dict[str, Any],
    allow_cool_foundation: bool = False,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Remove an unrequested cool color wash while preserving a functional accent.

    A blue primary or focus ring alone is not a failure. Neutralization applies
    only when cool chroma dominates structural surfaces or several identity
    roles at once, which is the recurring generic AI-template failure mode.
    """
    resolved = dict(colors)
    if allow_cool_foundation:
        return resolved, []

    foundation_keys = (
        "background",
        "card",
        "muted",
        "border",
    )
    identity_keys = ("primary", "secondary", "accent", "ring")
    cool_foundation_count = sum(
        _is_cool_chromatic(resolved.get(key)) for key in foundation_keys
    )
    cool_identity_count = sum(
        _is_cool_chromatic(resolved.get(key)) for key in identity_keys
    )
    dominated_by_cool_wash = cool_foundation_count >= 2 or (
        cool_foundation_count >= 1 and cool_identity_count >= 3
    )
    if not dominated_by_cool_wash:
        return resolved, []

    background_luminance = color_luminance(resolved.get("background"))
    dark_theme = background_luminance is not None and background_luminance < 0.18
    neutral_tokens = (
        {
            "secondary": "#44403C",
            "background": "#111110",
            "foreground": "#F5F5F4",
            "card": "#1C1917",
            "card_foreground": "#F5F5F4",
            "muted": "#292524",
            "muted_foreground": "#A8A29E",
            "border": "#44403C",
            "ring": "#D6D3D1",
        }
        if dark_theme
        else {
            "secondary": "#57534E",
            "background": "#F7F7F5",
            "foreground": "#1C1917",
            "card": "#FFFFFF",
            "card_foreground": "#1C1917",
            "muted": "#ECEAE6",
            "muted_foreground": "#57534E",
            "border": "#D6D3D1",
            "ring": "#57534E",
        }
    )
    primary = _first_hex(resolved.get("primary"))
    if primary and _is_cool_chromatic(primary):
        if _is_cool_chromatic(resolved.get("accent")):
            neutral_tokens["accent"] = primary
        if _is_cool_chromatic(resolved.get("ring")):
            neutral_tokens["ring"] = primary
    reason = "Removed an unrequested cool-chromatic wash from structural surfaces while preserving one restrained functional accent"
    adjustments: list[dict[str, str]] = []
    for key, replacement in neutral_tokens.items():
        current = _first_hex(resolved.get(key)) or "unset"
        if current == replacement:
            continue
        resolved[key] = replacement
        adjustments.append(
            {
                "token": f"--color-{key.replace('_', '-')}",
                "from": current,
                "to": replacement,
                "reason": reason,
            }
        )
    resolved["notes"] = "Context-neutral structural surfaces with chromatic color reserved for deliberate functional, brand, or domain emphasis"
    return resolved, adjustments


def contrast_ratio(foreground: str, background: str) -> float:
    """Calculate the WCAG contrast ratio for two six-digit hex colors."""
    lighter, darker = sorted(
        (_relative_luminance(foreground), _relative_luminance(background)),
        reverse=True,
    )
    return (lighter + 0.05) / (darker + 0.05)


def ensure_accessible_semantic_colors(colors: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Repair semantic foreground tokens while preserving brand surface colors.

    Search data can contain a useful brand palette with an unsuitable ``on-*``
    token. This function keeps primary, accent, background, and surface colors
    intact, then chooses an explicit neutral foreground or visible focus-ring
    token when the declared pair misses its target. Every change is returned so
    output formatters can disclose it instead of silently rewriting the palette.
    """
    resolved = dict(colors)
    adjustments: list[dict[str, Any]] = []
    pairs = (
        ("foreground", "background", 4.5, "content"),
        ("on_primary", "primary", 4.5, "on_color"),
        ("on_secondary", "secondary", 4.5, "on_color"),
        ("on_accent", "accent", 4.5, "on_color"),
        ("card_foreground", "card", 4.5, "content"),
        ("muted_foreground", "muted", 4.5, "muted"),
        ("on_destructive", "destructive", 4.5, "on_color"),
        ("ring", "background", 3.0, "ring"),
    )

    for foreground_key, background_key, threshold, role in pairs:
        background = _first_hex(resolved.get(background_key))
        current = _first_hex(resolved.get(foreground_key))
        if not background:
            continue
        if current and contrast_ratio(current, background) >= threshold:
            continue

        is_dark_surface = _relative_luminance(background) < 0.18
        if role == "on_color":
            candidates = (
                ("#FFFFFF", "#0F172A", "#000000")
                if is_dark_surface
                else ("#0F172A", "#000000", "#FFFFFF")
            )
        elif role == "muted":
            candidates = (
                ("#CBD5E1", "#E2E8F0", "#FFFFFF")
                if is_dark_surface
                else ("#475569", "#334155", "#0F172A", "#000000")
            )
        elif role == "ring":
            candidates = tuple(
                candidate
                for candidate in (
                    _first_hex(resolved.get("accent")),
                    _first_hex(resolved.get("secondary")),
                    _first_hex(resolved.get("primary")),
                    "#60A5FA" if is_dark_surface else "#2563EB",
                    "#FFFFFF" if is_dark_surface else "#000000",
                )
                if candidate
            )
        else:
            candidates = (
                ("#F8FAFC", "#E2E8F0", "#FFFFFF")
                if is_dark_surface
                else ("#0F172A", "#1E293B", "#000000")
            )

        replacement = next(
            (candidate for candidate in candidates if contrast_ratio(candidate, background) >= threshold),
            None,
        )
        if not replacement:
            fallback_candidates = ("#000000", "#FFFFFF")
            replacement = max(
                fallback_candidates,
                key=lambda candidate: contrast_ratio(candidate, background),
            )

        resolved[foreground_key] = replacement
        adjustments.append(
            {
                "token": f"--color-{foreground_key.replace('_', '-')}",
                "from": current or "unset",
                "to": replacement,
                "ratio": round(contrast_ratio(replacement, background), 2),
                "target": threshold,
                "against": f"--color-{background_key.replace('_', '-')}",
            }
        )

    # Synchronize legacy aliases after semantic repair.
    resolved["text"] = resolved.get("foreground", resolved.get("text", ""))
    resolved["cta"] = resolved.get("accent", resolved.get("cta", ""))
    return resolved, adjustments


def build_contrast_checks(colors: dict[str, Any]) -> list[dict[str, Any]]:
    """Check text/surface pairs without silently changing brand colors."""
    pairs = (
        ("Foreground / Background", "foreground", "background", 4.5),
        ("On Primary / Primary", "on_primary", "primary", 4.5),
        ("On Secondary / Secondary", "on_secondary", "secondary", 4.5),
        ("On Accent / Accent", "on_accent", "accent", 4.5),
        ("Card Foreground / Card", "card_foreground", "card", 4.5),
        ("Muted Foreground / Muted", "muted_foreground", "muted", 4.5),
        ("On Destructive / Destructive", "on_destructive", "destructive", 4.5),
        ("Focus Ring / Background", "ring", "background", 3.0),
    )
    checks = []
    for label, foreground_key, background_key, threshold in pairs:
        foreground = _first_hex(colors.get(foreground_key))
        background = _first_hex(colors.get(background_key))
        if not foreground or not background:
            continue
        ratio = contrast_ratio(foreground, background)
        suggestion = ""
        if ratio < threshold:
            candidates = ((contrast_ratio("#000000", background), "#000000"), (contrast_ratio("#FFFFFF", background), "#FFFFFF"))
            best_ratio, best_color = max(candidates)
            if best_ratio >= threshold:
                suggestion = f"Use {best_color} or choose a brand-aligned foreground/background pair that reaches {threshold}:1"
            else:
                suggestion = f"Adjust both tokens until the rendered pair reaches {threshold}:1"
        checks.append(
            {
                "pair": label,
                "foreground": foreground,
                "background": background,
                "ratio": round(ratio, 2),
                "threshold": threshold,
                "status": "PASS" if ratio >= threshold else "ADJUST",
                "suggestion": suggestion,
            }
        )
    return checks


def build_art_direction_gate(context: str = "") -> dict[str, Any]:
    """Return an evidence-first concept-selection protocol for the requested scope.

    The generator can propose a direction, but it cannot honestly certify its own
    aesthetic choice without comparison and rendered evidence. The initial state
    therefore remains UNKNOWN until the appropriate gate is executed.
    """
    lowered = str(context or "").casefold()
    direct_markers = (
        "bug fix",
        "state addition",
        "small component",
        "narrow component",
        "contained change",
        "local fix",
    )
    refinement_markers = (
        "existing interface",
        "existing app",
        "existing product",
        "current interface",
        "polish",
        "refine",
        "extend the design system",
    )
    full_markers = (
        "new product",
        "new app",
        "from scratch",
        "redesign",
        "visual identity",
        "art direction",
        "rebrand",
    )

    if any(marker in lowered for marker in direct_markers):
        mode = "Direct execution fit check"
        candidate_policy = (
            "Keep the established system and test the proposed change against the current task, tokens, component roles, and states"
        )
    elif any(marker in lowered for marker in refinement_markers) and not any(
        marker in lowered for marker in full_markers
    ):
        mode = "Refinement gate"
        candidate_policy = (
            "Compare the current rendered baseline with one focused refinement hypothesis; preserve the established system unless scope authorizes a redesign"
        )
    else:
        mode = "Full concept gate"
        candidate_policy = (
            "Compare two direction cards, or a third only when it represents another material product trade-off, on the same product truth, real content, functional requirements, and platform constraints"
        )

    return {
        "mode": mode,
        "initial_status": (
            "UNKNOWN — generated retrieval is a design hypothesis until the required comparison, critic pass, and rendered review are completed"
        ),
        "status_vocabulary": "PASS | BLOCKER | UNKNOWN | N/A",
        "candidate_policy": candidate_policy,
        "distinctness_rule": (
            "For a full gate, each candidate must represent a material design trade-off visible in composition, hierarchy, density, content model, interaction, imagery, or motion; cosmetic token swaps do not count, but do not force an arbitrary number of differences unrelated to the brief"
        ),
        "review_dimensions": [
            "Product and audience fit; primary-task clarity and action hierarchy",
            "Information architecture and resilience with real, long, empty, loading, error, and localized content",
            "System coherence and product-specific distinctiveness rather than trend mimicry",
            "Verified brand provenance, official assets, and explicit assumptions",
            "Accessibility, platform conventions, input modes, and responsive feasibility",
            "Stack, component-library, dependency, asset, performance, and delivery feasibility",
            "Guardrail integrity: no decorative pill field, inflated controls, card soup, uncontrolled icon-source mixing, vague stock metaphors, or unrequested blue-purple neon/glow",
        ],
        "evidence_rule": (
            "Use exactly one PASS, BLOCKER, UNKNOWN, or N/A token in each status field; put evidence, caveats, risk, and corrective action in separate fields, reserve BLOCKER for violated requirements or outcome-level harm rather than heuristic counts, never invent PASS with risk, and never use numeric taste scores"
        ),
        "selection_rule": (
            "Eliminate unresolved blockers, treat unknowns as risk, and choose the direction that best serves the primary task and product identity; synthesize only compatible ideas that restate as one thesis"
        ),
        "implementation_contract": (
            "Freeze the selected thesis, dominant composition, optional signature device, preserved repository conventions, approved deviations, non-negotiables, forbidden defaults, representative states, and target viewports before implementation"
        ),
        "render_review": (
            "Compare the real render with the contract at compact, intermediate, and wide sizes and across applicable states, themes, zoom or text scaling, focus, and reduced motion; include the prior baseline for refinement work"
        ),
        "stop_rule": (
            "Resolve blockers and major findings, rerender after material changes, then stop when the task, contract, and quality gates are satisfied; disclose untested modes and external limitations"
        ),
    }


def build_quality_gates() -> list[str]:
    """Return implementation-neutral design QA gates."""
    return [
        "Complete the appropriate direct, refinement, or full art-direction gate and compare the render with the selected implementation contract",
        "Pass the creative-distinction gate: tie identity to product content, workflow, data, typography, imagery, or interaction and reject template resemblance without forcing ornament",
        "Judge outcome evidence before proxies: package count, class names, exact pixel values, raw hue names, and element counts are review signals rather than automatic failures",
        "Render and inspect the real interface at narrow, intermediate, and wide widths; do not approve from code alone",
        "Run one bounded rendered-critic pass across composition, typography, density, and visual noise; correct blockers and majors, then rerender the same evidence set",
        "Verify default, hover where supported, pressed, focus-visible, selected, disabled, loading, empty, error, and success states",
        "Test keyboard order, screen-reader names, zoom or system text scaling, reduced motion, and high-contrast or forced-colors behavior where supported",
        "Check every supported theme independently; never infer one theme's contrast from another",
        "Confirm that async content reserves space and that fixed UI does not cover content or focused controls",
        "Remove decorative containers, pills, shadows, gradients, and animations that do not improve hierarchy or feedback",
        "Reject unrequested blue/cyan/violet glow, neon, bloom, or luminous-gradient identity; do not reject a restrained functional hue or evidence-backed brand treatment merely because it is cool or uses a gradient",
        "Check that buttons, selects, segmented controls, and icon containers are visually compact while their non-overlapping hit targets remain accessible",
        "Audit icon roles and metaphors: preserve learned universal actions, reject vague stock-value symbols, and verify coherent rendered geometry plus documented source roles rather than counting icon packages",
        "When a new icon source wins, verify its current official adapter, version, license, compatibility, bundle behavior, and maintenance; install only that winner with the repository package manager, preserve the lockfile, run repository checks, and remove rejected acquisitions",
        "Verify typography with real content, supported scripts, localization, font-loading failure, fallback metrics, numeral behavior, zoom or text scaling, and the actual loaded weights",
        "Update PROJECT-MEMORY.md only with evidence-backed project decisions; preserve confirmed entries during regeneration and supersede rather than erase history",
    ]
