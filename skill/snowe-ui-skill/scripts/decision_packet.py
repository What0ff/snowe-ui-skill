#!/usr/bin/env python3
"""Architecture-first decision support for Snowe UI Skill.

The packet deliberately does not choose a site recipe, visual style, font,
palette, image source, or motion intensity.  It turns a brief into a causal
design workbench: facts and unknowns, design pressures, evidence needs,
candidate contracts, and proof obligations.  A capable agent performs the
actual synthesis and records the decision after comparing real candidates.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

from core import DATA_DIR, search


SCHEMA_VERSION = "2.0"

_TOKEN_RE = re.compile(r"[^\W_]+(?:[-’'][^\W_]+)*", re.UNICODE)

_ANALOG_GENERIC_TERMS = {
    "app",
    "application",
    "audit",
    "before",
    "brand",
    "care",
    "clear",
    "desktop",
    "direct",
    "existing",
    "first",
    "high",
    "history",
    "independent",
    "live",
    "local",
    "mobile",
    "music",
    "need",
    "online",
    "platform",
    "product",
    "real",
    "responsive",
    "service",
    "show",
    "shop",
    "site",
    "track",
    "price",
    "prices",
    "purchase",
    "public",
    "reminder",
    "reminders",
    "upload",
    "user",
    "web",
    "website",
}

_STOPWORDS = {
    "a",
    "an",
    "and",
    "app",
    "application",
    "build",
    "create",
    "design",
    "for",
    "from",
    "in",
    "new",
    "of",
    "on",
    "or",
    "product",
    "site",
    "the",
    "to",
    "ui",
    "ux",
    "web",
    "website",
    "with",
}

_QUERY_EXPANSIONS = {
    "bicycle": ("bike", "cycling"),
    "bicycles": ("bike", "cycling"),
    "bike": ("bicycle", "cycling"),
    "medication": ("health", "healthcare", "medical", "prescription"),
    "municipal": ("civic", "government", "public service"),
    "municipality": ("civic", "government", "public service"),
    "musician": ("music", "artist", "album", "record"),
    "magazine": ("editorial", "publication", "articles"),
    "journal": ("editorial", "publication", "articles"),
    "pediatric": ("health", "healthcare", "medical", "child", "parent"),
    "performances": ("concert", "tour", "music"),
    "releases": ("music", "album", "record"),
    "store": ("retail", "shop", "ecommerce"),
    "retailer": ("retail", "shop", "ecommerce"),
    "symptoms": ("health", "medical", "triage"),
    "warehouse": ("inventory", "stock", "operations"),
}

_SIGNAL_RULES: dict[str, tuple[str, ...]] = {
    "commerce": (
        "buy",
        "cart",
        "catalog",
        "commerce",
        "ecommerce",
        "e-commerce",
        "price",
        "pricing",
        "purchase",
        "retail",
        "retailer",
        "shop",
        "store",
        "subscription",
    ),
    "service_transaction": (
        "application status",
        "appointment",
        "apply",
        "booking",
        "document upload",
        "eligibility",
        "permit",
        "registration",
        "status tracker",
        "triage",
    ),
    "editorial_content": (
        "article",
        "articles",
        "editorial",
        "issue",
        "journal",
        "literary",
        "long-form",
        "magazine",
        "news",
        "publication",
        "reading",
        "story",
    ),
    "operations": (
        "admin",
        "analytics",
        "console",
        "dashboard",
        "dispatcher",
        "exceptions",
        "inventory",
        "monitoring",
        "operations",
        "stock",
        "warehouse",
        "workspace",
    ),
    "event_or_community": (
        "agenda",
        "community",
        "event",
        "events",
        "live dates",
        "membership",
        "schedule",
        "ticket",
        "tickets",
    ),
    "brand_expression": (
        "art direction",
        "brand",
        "campaign",
        "experimental",
        "expressive",
        "immersive",
        "portfolio",
        "rebrand",
        "storytelling",
        "visual identity",
    ),
    "comparison": (
        "compare",
        "comparison",
        "decision support",
        "fit guide",
        "selector",
    ),
    "location_or_route": (
        "city",
        "location",
        "map",
        "nearby",
        "route",
        "store locator",
    ),
    "media_rich": (
        "album",
        "gallery",
        "image",
        "imagery",
        "photo",
        "photography",
        "video",
        "visual",
    ),
    "high_stakes": (
        "civic",
        "financial",
        "government",
        "health",
        "healthcare",
        "medical",
        "municipal",
        "pediatric",
        "public service",
        "safety",
    ),
    "multilingual": (
        "bilingual",
        "internationalization",
        "localization",
        "multilingual",
        "rtl",
    ),
    "dense_information": (
        "data-dense",
        "dense",
        "high-density",
        "inventory",
        "metrics",
        "table",
        "tables",
    ),
    "keyboard_first": (
        "keyboard-first",
        "keyboard first",
        "power user",
        "shortcut",
    ),
}

_PRESSURES = {
    "commerce": "Make the offer concrete, support confident selection, expose price and fulfilment evidence, and place conversion where the decision becomes ready.",
    "service_transaction": "Join eligibility, evidence, submission, recovery, and status into one understandable journey instead of mirroring organizational structure.",
    "editorial_content": "Balance discovery with sustained reading, preserve issue/article relationships, and make subscription or attendance a consequence of editorial value rather than an interruption.",
    "operations": "Reduce time to detect, understand, and act; preserve scan paths, object context, state history, and frequent keyboard loops.",
    "event_or_community": "Make time, place, availability, participation, and social proof legible without turning urgency into noise.",
    "brand_expression": "Create a recognizable point of view from the product, audience, content, material, or behavior rather than selecting a trend label.",
    "comparison": "Keep criteria commensurable and visible at the decision moment; avoid forcing memory-based comparison across pages.",
    "location_or_route": "Preserve orientation, distance, sequence, and a non-map alternative when spatial context matters.",
    "media_rich": "Give every visual a job—desire, proof, explanation, orientation, detail, or atmosphere—and budget crop, loading, and fallback behavior.",
    "high_stakes": "Prioritize comprehension, error prevention, recovery, provenance, accessibility, and calm confidence over novelty.",
    "multilingual": "Treat script coverage, expansion, bidirectionality, content parity, and locale switching as architecture inputs rather than final QA.",
    "dense_information": "Use density to support expert scanning and comparison; prevent compression from hiding priority, state, or action.",
    "keyboard_first": "Model repeated command paths, focus movement, shortcuts, undo, and state continuity as first-class interaction architecture.",
}


def _tokens(value: str) -> list[str]:
    return [token.casefold() for token in _TOKEN_RE.findall(str(value or ""))]


def _contains_phrase(tokens: list[str], phrase: str) -> bool:
    phrase_tokens = _tokens(phrase)
    if not phrase_tokens:
        return False
    width = len(phrase_tokens)
    return any(tokens[index : index + width] == phrase_tokens for index in range(len(tokens) - width + 1))


def _detect_signals(brief: str) -> list[str]:
    tokens = _tokens(brief)
    return [
        signal
        for signal, markers in _SIGNAL_RULES.items()
        if any(_contains_phrase(tokens, marker) for marker in markers)
    ]


def _work_mode(brief: str) -> str:
    tokens = _tokens(brief)
    if any(
        _contains_phrase(tokens, phrase)
        for phrase in (
            "design audit",
            "ui audit",
            "ux audit",
            "usability audit",
            "usability review",
            "design review",
            "review this",
            "review the",
            "review existing",
            "critique this",
            "critique the",
            "diagnose this",
            "diagnose the",
            "audit this",
            "audit the",
            "audit existing",
        )
    ):
        return "review"
    if any(
        _contains_phrase(tokens, phrase)
        for phrase in ("existing", "polish", "refine", "redesign", "rework", "improve")
    ):
        return "evolution"
    return "new_direction"


def _platforms(brief: str) -> list[str]:
    tokens = _tokens(brief)
    platforms: list[str] = []
    groups = (
        ("responsive_web", ("responsive web", "website", "web")),
        ("mobile", ("mobile", "ios", "android", "touch-first")),
        ("desktop", ("desktop", "keyboard-first", "pointer-first")),
    )
    for platform, markers in groups:
        if any(_contains_phrase(tokens, marker) for marker in markers):
            platforms.append(platform)
    return platforms or ["UNKNOWN — verify target surfaces and input modes"]


def _research_plan(mode: str, signals: list[str], brief: str) -> dict[str, Any]:
    tokens = _tokens(brief)
    triggers: list[dict[str, str]] = []
    if mode == "new_direction" or "brand_expression" in signals:
        triggers.append(
            {
                "question": "What does the current product, market, cultural, and visual landscape make familiar—and where is there room to be meaningfully distinct?",
                "sources": "Real current products, official brand assets, primary platform guidance, and credible domain research",
                "stop": "Stop when new sources repeat known approaches and no longer introduce a material architecture, content, or art-direction challenger.",
            }
        )
    if "commerce" in signals:
        triggers.append(
            {
                "question": "What information and interaction evidence do buyers currently need to compare, trust, and purchase this category?",
                "sources": "Current category retailers and manufacturers plus evidence-based ecommerce UX research",
                "stop": "Stop after the main decision anxieties, content conventions, and strongest counterexamples are represented.",
            }
        )
    if "high_stakes" in signals or "multilingual" in signals:
        triggers.append(
            {
                "question": "Which current standards, service guidance, legal constraints, language requirements, and failure modes shape the experience?",
                "sources": "Official standards, regulator or service guidance, platform accessibility documentation, and verified organizational policy",
                "stop": "Standards and hard constraints are resolved or explicitly left UNKNOWN with a safe fallback.",
            }
        )
    if any(_contains_phrase(tokens, marker) for marker in ("icon", "font", "library", "framework", "image generator", "gpt image")):
        triggers.append(
            {
                "question": "Which current official assets, packages, licenses, capabilities, and platform constraints can materially change the decision?",
                "sources": "Official documentation, authoritative registries, licenses, and current release information",
                "stop": "The viable candidates and their current integration constraints are verified; no speculative dependency set is installed.",
            }
        )
    if not triggers:
        triggers.append(
            {
                "question": "Could current external evidence reveal a materially different architecture, interaction, visual language, or risk than repository evidence alone?",
                "sources": "Use targeted primary or real-product sources only if the answer is plausibly yes.",
                "stop": "Skip or stop when external exploration cannot reasonably change a high-leverage decision.",
            }
        )
    return {
        "posture": "targeted, decision-led research; never a mandatory moodboard",
        "triggers": triggers,
        "synthesis_rule": "Extract transferable principles, tensions, and counterexamples. Do not copy a competitor's composition, brand codes, imagery, or interaction signature.",
        "evidence_record": "decision | source | observed fact | implication | confidence | freshness | candidate changed?",
    }


def _expanded_query(brief: str) -> str:
    query_tokens = _tokens(brief)
    additions: list[str] = []
    for token in query_tokens:
        for expansion in _QUERY_EXPANSIONS.get(token, ()):
            if expansion not in additions:
                additions.append(expansion)
    return " ".join((brief, *additions))


def _matched_terms(brief: str, values: Iterable[Any]) -> list[str]:
    query_terms = {token for token in _tokens(brief) if token not in _STOPWORDS and len(token) > 2}
    evidence_terms = set(_tokens(" ".join(str(value) for value in values)))
    return sorted(query_terms & evidence_terms)


@lru_cache(maxsize=1)
def _product_term_frequency() -> tuple[int, dict[str, int]]:
    """Return product-vocabulary document frequency for weak-analog rejection."""
    filepath = DATA_DIR / "products.csv"
    counts: Counter[str] = Counter()
    total = 0
    with filepath.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            total += 1
            values = (
                row.get("Product Type", ""),
                row.get("Keywords", ""),
                row.get("Key Considerations", ""),
            )
            counts.update(set(_tokens(" ".join(values))))
    return total, dict(counts)


def _meaningful_analog_terms(terms: Iterable[str]) -> list[str]:
    total, frequency = _product_term_frequency()
    rare_limit = max(5, round(total * 0.05))
    meaningful = [term for term in terms if term not in _ANALOG_GENERIC_TERMS]
    if len(meaningful) >= 2:
        return meaningful
    return [term for term in meaningful if frequency.get(term, total) <= rare_limit]


def _non_generic_terms(terms: Iterable[str]) -> list[str]:
    return [term for term in terms if term not in _ANALOG_GENERIC_TERMS]


def _local_analogs(brief: str) -> list[dict[str, Any]]:
    expanded = _expanded_query(brief)
    specific_terms = [
        token
        for token in _tokens(expanded)
        if token not in _STOPWORDS and token not in _ANALOG_GENERIC_TERMS and len(token) > 2
    ]
    candidates: list[dict[str, Any]] = []
    seen_labels: set[str] = set()
    for query in (" ".join(specific_terms), expanded):
        if not query.strip():
            continue
        result = search(query, "product", 16)
        for item in result.get("results", []):
            label = item.get("Product Type", "Unlabelled analog")
            if label in seen_labels:
                continue
            seen_labels.add(label)
            candidates.append(item)

    ranked: list[tuple[int, dict[str, Any], list[str]]] = []
    for item in candidates:
        matches = _meaningful_analog_terms(_matched_terms(expanded, item.values()))
        if not matches:
            continue
        label_matches = _non_generic_terms(
            _matched_terms(expanded, (item.get("Product Type", ""),))
        )
        keyword_matches = _non_generic_terms(
            _matched_terms(expanded, (item.get("Keywords", ""),))
        )
        consideration_matches = _non_generic_terms(
            _matched_terms(expanded, (item.get("Key Considerations", ""),))
        )
        if not label_matches and not keyword_matches and len(matches) < 2:
            continue
        score = 5 * len(label_matches) + 3 * len(keyword_matches) + len(consideration_matches)
        ranked.append((score, item, matches))

    analogs: list[dict[str, Any]] = []
    for _score, item, matches in sorted(ranked, key=lambda entry: entry[0], reverse=True):
        analogs.append(
            {
                "status": "UNVERIFIED_ANALOG",
                "label": item.get("Product Type", "Unlabelled analog"),
                "matched_terms": matches,
                "possibly_useful_evidence": item.get("Key Considerations", ""),
                "warning": "Use only the relevant concern or content clue. Do not inherit this row's product identity, layout, style, palette, or landing recipe.",
            }
        )
        if len(analogs) == 3:
            break
    return analogs


def _unknowns(signals: list[str]) -> list[str]:
    questions = [
        "What outcome is the primary user trying to reach, in what context, and what currently makes it difficult?",
        "What business outcome and conversion event matter, and what evidence would show success without harming the user outcome?",
        "Which actors, objects, content, states, entry points, return visits, and offline or cross-channel steps belong to the whole journey?",
        "Which requirements are facts, which are reversible assumptions, and which unknowns could change the architecture or brand position?",
    ]
    if "commerce" in signals:
        questions.append("What is sold, how does the assortment differ, which criteria drive selection, and which fulfilment, service, warranty, availability, or price facts remove purchase anxiety?")
    if "service_transaction" in signals:
        questions.append("What must users understand before starting, what evidence must they provide, how can they save or recover work, and how is progress or status explained?")
    if "editorial_content" in signals:
        questions.append("How do issues, articles, authors, topics, archives, events, and paid offerings relate, and which reading/discovery loops should the architecture preserve?")
    if "operations" in signals:
        questions.append("Which objects change state, which exceptions demand action, what decisions repeat, and what context or history must remain visible while acting?")
    if "high_stakes" in signals:
        questions.append("Which errors create real harm, what provenance or reassurance is required, and what assisted or alternative path exists when the digital journey fails?")
    return questions


def _identity_sources(signals: list[str]) -> list[str]:
    sources = [
        "The product's real objects, construction, workflow, or information relationships",
        "Audience language, culture, habits, and context of use",
        "Verified brand history, voice, assets, materials, place, and behavior",
        "The form and quality of real content—not placeholder volume or trend labels",
    ]
    if "commerce" in signals:
        sources.append("Product engineering, materials, fit, use environments, service expertise, and the rituals of selection and ownership")
    if "editorial_content" in signals:
        sources.append("Editorial voice, issue structure, pacing, authorship, annotation, and the physical or archival qualities of publication")
    if "operations" in signals:
        sources.append("Domain states, transitions, signals, physical environment, and the cadence of expert decisions")
    return sources


class DecisionPacketGenerator:
    """Generate an open design workbench without selecting the design."""

    def generate(self, brief: str, project_name: str | None = None) -> dict[str, Any]:
        signals = _detect_signals(brief)
        mode = _work_mode(brief)
        pressures = [_PRESSURES[signal] for signal in signals if signal in _PRESSURES]
        if not pressures:
            pressures = [
                "The brief does not yet expose a dominant experience pressure. Resolve the user outcome, business outcome, content, and usage context before proposing architecture."
            ]

        return {
            "schema_version": SCHEMA_VERSION,
            "project_name": project_name or "Untitled design inquiry",
            "brief": brief,
            "situation": {
                "mode": mode,
                "platforms": _platforms(brief),
                "signals": signals or ["unresolved"],
                "design_pressures": pressures,
                "unknowns": _unknowns(signals),
                "fact_policy": "The original brief and verified repository or external evidence are facts. Retrieved analogs, inferred audiences, market assumptions, and generated directions remain hypotheses until verified.",
            },
            "decision_graph": {
                "purpose": "Keep freedom causal: every material move traces back to a real driver and forward to an observable consequence.",
                "record": "driver → design move → expected user/business consequence → evidence → risk → revisit trigger",
                "layers": [
                    "Outcomes and constraints",
                    "Whole journey, actors, objects, content, decisions, and states",
                    "Site/service topology, navigation, page jobs, and conversion paths",
                    "Art direction, type, color/material, imagery, graphics, and motion language",
                    "Components, interactions, responsive transformations, and implementation",
                    "Rendered evidence, behavioral evidence, learning, and accepted decisions",
                ],
                "rule": "A downstream choice may be novel or absent from every local catalog. Keep it when its causal chain is stronger than the alternatives and it survives real-content and rendered tests.",
            },
            "research": _research_plan(mode, signals, brief),
            "architecture": {
                "status": "OPEN — synthesize after the whole journey and content model are understood",
                "inputs": [
                    "Actors, contexts, frequency, stakes, and input modes",
                    "User jobs, decision moments, dependencies, failure/recovery, and re-entry",
                    "Business model, conversion, trust obligations, and success evidence",
                    "Content and product objects, attributes, relationships, quantities, lifecycle, and ownership",
                    "Entry points, search/discovery behavior, navigation depth, and cross-channel steps",
                ],
                "synthesis": [
                    "Map the whole journey and object/content relationships before naming pages or sections.",
                    "Define the site or product boundary around outcomes; do not mirror the organization, database, or a familiar template.",
                    "Generate enough structurally different candidates to cover the live trade-offs. Change the organizing principle, sequence, navigation, disclosure, or conversion model—not only visual styling.",
                    "Include a synthesized candidate when the strongest answer is not represented by retrieved patterns. Local data is evidence and analogy, never the candidate boundary.",
                    "Prototype the riskiest page slice or journey transition with real content before selecting the complete architecture.",
                ],
                "candidate_record": {
                    "thesis": "How this architecture organizes the user's world",
                    "site_scope": "What belongs, what does not, and how cross-channel steps join up",
                    "topology": "Destinations or product areas and the relationships that justify them",
                    "navigation": "How users orient, move, search, compare, return, and recover",
                    "page_jobs": "For every key page: what the user should understand, decide, or do",
                    "content_sequence": "Questions and dependencies that determine order; no hero or section type is mandatory",
                    "conversion_path": "Where intent becomes ready and what proof precedes the action",
                    "responsive_transformation": "What stays invariant and what reorders, collapses, changes control, or changes medium",
                    "risk": "The assumption most likely to invalidate this candidate",
                },
                "selection_rule": "Select by causal fit, clarity, content resilience, identity potential, accessibility, and feasibility. Hybridize only compatible moves that form one coherent organizing logic.",
            },
            "art_direction": {
                "status": "OPEN — architecture and real content constrain the visual language before styling begins",
                "identity_sources": _identity_sources(signals),
                "direction_method": [
                    "Frame directions as perceptual and behavioral theses, not style labels or mood adjectives.",
                    "Make finalists differ in composition, typographic voice, image/graphic logic, material behavior, or interaction character where those differences express a real product trade-off.",
                    "Choose one primary identity carrier and define its repetition boundary. The carrier may be architecture, type, content behavior, imagery, graphics, data, or motion; decoration is optional.",
                    "Use typography, color, shape, and material as a coherent system derived from content, scripts, platform, and desired perception. A dataset pairing or palette is only a candidate.",
                ],
                "direction_record": "thesis | perception | product-specific source | dominant composition | type voice | color/material logic | imagery/graphic logic | interaction/motion character | signature boundary | strongest risk",
            },
            "assets": {
                "visual_need_decision": {
                    "status": "OPEN",
                    "question": "What must a visual explain, prove, orient, reveal, or make desirable that type, layout, real product UI, or no image cannot do better?",
                    "eligible_outcomes": [
                        "No image",
                        "Verified existing or brand asset",
                        "Product photography or commissioned photography",
                        "Illustration",
                        "Diagram or data-led graphic",
                        "3D/product composition",
                        "Generated artwork or photography",
                        "Repository-owned custom graphic",
                    ],
                    "selection_rule": "Choose by communicative job, truthfulness, provenance, art-direction fit, responsive crop, performance, and maintenance—not by novelty or tool availability.",
                },
                "image_generation": {
                    "use_when": "Generation can produce a needed, truthful, ownable composition that is unavailable from real product, brand, licensed, commissioned, or diagrammatic sources inside scope.",
                    "brief": "page role | communicative job | exact aspect/crop | subject and action | camera/perspective | subject placement and negative space | light/material/palette | continuity with type and surfaces | required truth | prohibited artifacts/cliches | responsive variants",
                    "loop": [
                        "Generate a small set of meaningfully different compositions, not prompt paraphrases.",
                        "Place finalists in the actual layout at target crops and widths before judging them.",
                        "Inspect anatomy, product truth, text-like artifacts, edge quality, focal competition, crop resilience, loading cost, and provenance disclosure.",
                        "Regenerate, edit, or reject the asset when the real layout is weaker than the no-image or non-generated alternative.",
                    ],
                },
                "custom_graphics": {
                    "family_spec": "role | grid/viewBox | live area/keylines | stroke or fill model | caps/joins/corners | curvature | optical overshoot | counter/negative-space minimum | detail budget by size | color modes | source/provenance",
                    "workflow": [
                        "Decide whether visible text, an existing symbol, a compatible external family, or a custom graphic gives the clearest and most ownable result.",
                        "Sketch materially different silhouettes and compound constructions before polishing paths.",
                        "Draw to the family specification; use optical compensation rather than mechanically identical bounds.",
                        "Run structural SVG/provenance validation, then render at 16, 20, and 24px and at every actual interface size beside neighboring icons.",
                        "Test default, selected, disabled, dark, high-contrast, and labelled contexts where applicable.",
                    ],
                    "reject_when": "Reject or redraw when recognition depends on explanation, counters close, stroke/area feels heavier than neighbors, the metaphor conflicts with the action, the silhouette collapses, or an existing asset is visibly stronger.",
                },
            },
            "motion": {
                "status": "OPEN — the static and reduced-motion experience is the baseline",
                "decision_question": "Does motion clarify cause, continuity, hierarchy, spatial relationship, progress, feedback, or story—and is that benefit worth its repetition and runtime cost?",
                "record": "trigger/state change | information motion carries | affected hierarchy | frequency | choreography | interruption | performance budget | reduced/static equivalent | reject condition",
                "rules": [
                    "Use immediate restrained feedback for frequent controls; reserve expressive choreography for low-frequency moments whose narrative or spatial role earns it.",
                    "Motion must be interruptible and must not delay task completion, hide required state, or create a gesture-only path.",
                    "Test repeated use and `prefers-reduced-motion`; reduction may preserve a short opacity/state transition when removing all feedback would weaken comprehension.",
                    "Choose no animation when the static state change is clearer, faster, calmer, or more accessible.",
                ],
            },
            "responsive": {
                "principle": "Design transformations, not three screenshots. Preserve outcome, priority, reading order, state, and conversion while changing composition and controls when space or input mode changes.",
                "contract": "invariants | reorder/collapse rules | navigation transition | content disclosure | media crop/substitution | comparison behavior | sticky/fixed behavior | pointer/touch/keyboard differences | long-content and localization stress",
                "proof": "Render narrow, at least one pressure width between planned breakpoints, and wide; include zoom/text scaling, long real content, focus, open overlays, selected/disabled/error states, and reduced motion.",
            },
            "evaluation": {
                "verdicts": "KEEP | REVISE | REJECT | UNKNOWN",
                "criteria": [
                    "Causal fit: important moves trace to real user, business, content, brand, or platform drivers.",
                    "Structural range: candidates change organizing logic where the brief contains a real trade-off; cosmetic variants do not count.",
                    "Synthesis: the chosen answer may exceed every local recipe and does not inherit an analog's identity by accident.",
                    "Coherence: architecture, visual language, assets, interactions, and motion reinforce one thesis without uniformity for its own sake.",
                    "Discretion: imagery, generation, custom graphics, and animation appear only when they outperform simpler alternatives.",
                    "UX resilience: task clarity, accessibility, localization, content variation, performance, and responsive behavior survive the direction.",
                    "Rendered proof: visible hierarchy and interaction quality are evaluated in the real product, not certified by policy prose or code tokens.",
                ],
                "finding_record": "verdict | viewport/state | visible or behavioral evidence | consequence | correction or acceptance reason | rerender/retest",
                "stop": "Resolve every REJECT and material REVISE finding, rerender the affected evidence, and stop when further change no longer improves a stated driver. Preserve UNKNOWN where evidence genuinely cannot be obtained.",
            },
            "local_evidence": {
                "role": "lexical analogs and prompts for investigation—not classification, direction, or architecture",
                "product_analogs": _local_analogs(brief),
                "limitations": "Bundled CSVs are snapshots, mainly English, and contain historical recipes and unverified claims. Confirm current facts externally and synthesize beyond them.",
            },
        }


def _append_list(lines: list[str], items: Iterable[Any]) -> None:
    for item in items:
        lines.append(f"- {item}")


def format_packet_markdown(packet: dict[str, Any]) -> str:
    """Format a decision packet as a compact working document."""
    situation = packet["situation"]
    lines = [
        "# Snowe Design Decision Packet",
        "",
        f"**Project:** {packet['project_name']}",
        f"**Schema:** {packet['schema_version']}",
        f"**Brief:** {packet['brief']}",
        "",
        "> This packet opens decisions; it does not select a layout, style, palette, font, image, icon family, or motion recipe.",
        "",
        "## Design situation",
        "",
        f"- **Mode:** {situation['mode']}",
        f"- **Platforms:** {', '.join(situation['platforms'])}",
        f"- **Signals:** {', '.join(situation['signals'])}",
        f"- **Fact policy:** {situation['fact_policy']}",
        "",
        "### Design pressures",
        "",
    ]
    _append_list(lines, situation["design_pressures"])
    lines.extend(("", "### Resolve before architecture", ""))
    _append_list(lines, situation["unknowns"])

    graph = packet["decision_graph"]
    lines.extend(
        (
            "",
            "## Decision graph",
            "",
            f"- **Purpose:** {graph['purpose']}",
            f"- **Record:** `{graph['record']}`",
            f"- **Freedom rule:** {graph['rule']}",
            "",
        )
    )
    _append_list(lines, graph["layers"])

    research = packet["research"]
    lines.extend(("", "## External research", "", f"- **Posture:** {research['posture']}", f"- **Synthesis:** {research['synthesis_rule']}", ""))
    for trigger in research["triggers"]:
        lines.append(f"- **Question:** {trigger['question']}")
        lines.append(f"  - Sources: {trigger['sources']}")
        lines.append(f"  - Stop: {trigger['stop']}")
    lines.append(f"- **Record:** `{research['evidence_record']}`")

    architecture = packet["architecture"]
    lines.extend(("", "## Experience architecture", "", f"- **Status:** {architecture['status']}", "", "### Inputs", ""))
    _append_list(lines, architecture["inputs"])
    lines.extend(("", "### Synthesis", ""))
    _append_list(lines, architecture["synthesis"])
    lines.extend(("", "### Candidate record", ""))
    for key, value in architecture["candidate_record"].items():
        lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
    lines.append(f"- **Selection:** {architecture['selection_rule']}")

    art = packet["art_direction"]
    lines.extend(("", "## Art direction", "", f"- **Status:** {art['status']}", "", "### Identity sources", ""))
    _append_list(lines, art["identity_sources"])
    lines.extend(("", "### Direction method", ""))
    _append_list(lines, art["direction_method"])
    lines.append(f"- **Record:** `{art['direction_record']}`")

    assets = packet["assets"]
    visual = assets["visual_need_decision"]
    lines.extend(("", "## Imagery and custom assets", "", f"- **Visual decision:** {visual['status']} — {visual['question']}", f"- **Selection:** {visual['selection_rule']}", "", "### Eligible outcomes", ""))
    _append_list(lines, visual["eligible_outcomes"])
    generation = assets["image_generation"]
    lines.extend(("", "### Generated imagery", "", f"- **Use when:** {generation['use_when']}", f"- **Art-direction brief:** `{generation['brief']}`", ""))
    _append_list(lines, generation["loop"])
    custom = assets["custom_graphics"]
    lines.extend(("", "### Custom graphics and icons", "", f"- **Family specification:** `{custom['family_spec']}`", ""))
    _append_list(lines, custom["workflow"])
    lines.append(f"- **Reject when:** {custom['reject_when']}")

    motion = packet["motion"]
    lines.extend(("", "## Motion", "", f"- **Status:** {motion['status']}", f"- **Decision:** {motion['decision_question']}", f"- **Record:** `{motion['record']}`", ""))
    _append_list(lines, motion["rules"])

    responsive = packet["responsive"]
    lines.extend(
        (
            "",
            "## Responsive behavior",
            "",
            f"- **Principle:** {responsive['principle']}",
            f"- **Contract:** `{responsive['contract']}`",
            f"- **Proof:** {responsive['proof']}",
        )
    )

    evaluation = packet["evaluation"]
    lines.extend(("", "## Evaluation", "", f"- **Verdicts:** `{evaluation['verdicts']}`", ""))
    _append_list(lines, evaluation["criteria"])
    lines.append(f"- **Finding record:** `{evaluation['finding_record']}`")
    lines.append(f"- **Stop:** {evaluation['stop']}")

    evidence = packet["local_evidence"]
    lines.extend(("", "## Local evidence", "", f"- **Role:** {evidence['role']}", f"- **Limitations:** {evidence['limitations']}", ""))
    for analog in evidence["product_analogs"]:
        matches = ", ".join(analog["matched_terms"]) or "weak lexical overlap"
        lines.append(f"- **{analog['label']}** — `{analog['status']}`; matched: {matches}")
        if analog["possibly_useful_evidence"]:
            lines.append(f"  - Possible evidence: {analog['possibly_useful_evidence']}")
        lines.append(f"  - Warning: {analog['warning']}")
    return "\n".join(lines) + "\n"


def format_packet_json(packet: dict[str, Any]) -> str:
    return json.dumps(packet, indent=2, ensure_ascii=False) + "\n"


def slugify_name(value: str, fallback: str = "default") -> str:
    normalized = re.sub(r"[^\w]+", "-", str(value or "").casefold(), flags=re.UNICODE)
    normalized = re.sub(r"_+", "-", normalized)
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized[:80] or fallback


def format_decision_journal(project_name: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return (
        "# Accepted Design Decisions\n\n"
        f"Project: {project_name}\n"
        f"Initialized: {timestamp} UTC\n\n"
        "This file is durable and is never overwritten by packet regeneration.\n"
        "Record only evidence-backed decisions; keep experiments in disposable working notes.\n\n"
        "## Decision record\n\n"
        "| Status | Scope | Driver | Decision | Expected consequence | Evidence | Revisit trigger |\n"
        "|---|---|---|---|---|---|---|\n"
        "| PROPOSED | project |  |  |  |  |  |\n\n"
        "Allowed statuses: `PROPOSED`, `ACCEPTED`, `SUPERSEDED`.\n"
    )


def format_page_inquiry(page_name: str, page_brief: str | None = None) -> str:
    title = page_name.replace("-", " ").replace("_", " ").strip().title() or "Page"
    brief = page_brief or "UNKNOWN — derive from the verified project brief and journey"
    return (
        f"# {title} — Page Inquiry\n\n"
        f"**Page brief:** {brief}\n\n"
        "> This file does not prescribe a page type or section order. Resolve the page job from the journey and real content.\n\n"
        "## Page job\n\n"
        "- What must the user understand, decide, or do here?\n"
        "- Which entry states and prior knowledge must the page support?\n"
        "- What is the next useful outcome, and what evidence must precede it?\n\n"
        "## Content and interaction dependencies\n\n"
        "- Required objects, attributes, relationships, states, and real content:\n"
        "- Search, comparison, navigation, recovery, and re-entry behavior:\n"
        "- Loading, empty, partial, error, success, and permission states:\n\n"
        "## Architecture candidates\n\n"
        "Create enough structurally different candidates to cover the live trade-offs. For each, record the organizing principle, content sequence, focal hierarchy, conversion or task action, responsive transformation, and main invalidating risk.\n\n"
        "## Rendered proof\n\n"
        "Test real content at narrow, pressure/intermediate, and wide widths plus applicable focus, open, selected, disabled, loading, error, and reduced-motion states.\n"
    )


def persist_decision_packet(
    packet: dict[str, Any],
    page: str | None = None,
    output_dir: str | None = None,
    page_brief: str | None = None,
) -> dict[str, Any]:
    root = Path(output_dir or ".").resolve()
    project_slug = slugify_name(packet.get("project_name") or packet.get("brief") or "project")
    project_dir = root / "design-intelligence" / project_slug
    project_dir.mkdir(parents=True, exist_ok=True)

    created_or_updated: list[str] = []
    preserved: list[str] = []

    brief_path = project_dir / "BRIEF.md"
    brief_path.write_text(format_packet_markdown(packet), encoding="utf-8")
    created_or_updated.append(str(brief_path))

    decisions_path = project_dir / "DECISIONS.md"
    try:
        with decisions_path.open("x", encoding="utf-8") as handle:
            handle.write(format_decision_journal(packet.get("project_name", "Project")))
        created_or_updated.append(str(decisions_path))
    except FileExistsError:
        preserved.append(str(decisions_path))

    if page:
        pages_dir = project_dir / "pages"
        pages_dir.mkdir(parents=True, exist_ok=True)
        page_path = pages_dir / f"{slugify_name(page, 'page')}.md"
        page_path.write_text(format_page_inquiry(page, page_brief), encoding="utf-8")
        created_or_updated.append(str(page_path))

    return {
        "design_intelligence_dir": str(project_dir),
        "created_or_updated_files": created_or_updated,
        "preserved_files": preserved,
    }


def generate_decision_packet(
    brief: str,
    project_name: str | None = None,
    output_format: str = "markdown",
    persist: bool = False,
    page: str | None = None,
    output_dir: str | None = None,
    page_brief: str | None = None,
) -> str:
    packet = DecisionPacketGenerator().generate(brief, project_name)
    if persist:
        persist_decision_packet(packet, page=page, output_dir=output_dir, page_brief=page_brief)
    if output_format == "json":
        return format_packet_json(packet)
    return format_packet_markdown(packet)
