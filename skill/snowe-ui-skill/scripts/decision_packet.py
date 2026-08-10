#!/usr/bin/env python3
"""Architecture-first decision support for Snowe UI Skill.

The packet deliberately does not choose a site recipe, visual style, font,
palette, image source, or motion intensity.  It turns a brief into a causal
design workbench: facts and unknowns, design pressures, evidence needs,
candidate contracts, and proof obligations.  A capable agent performs the
actual synthesis and records the decision after comparing real candidates.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from core import search


SCHEMA_VERSION = "3.0"


def _as_string_list(value: Any, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise TypeError(f"declared_context.{field} must be a list of strings")
    items = [str(item).strip() for item in value if str(item).strip()]
    return items


def _normalize_declared_context(value: dict[str, Any] | None) -> dict[str, Any]:
    """Pass through explicit caller declarations without interpreting the brief."""
    context = dict(value or {})
    work_mode = str(context.pop("work_mode", "")).strip()
    platforms = _as_string_list(context.pop("platforms", None), "platforms")
    facts = _as_string_list(context.pop("facts", None), "facts")
    pressures = _as_string_list(context.pop("pressures", None), "pressures")
    other = {str(key): child for key, child in context.items()}
    declared = bool(work_mode or platforms or facts or pressures or other)
    return {
        "status": "CALLER_DECLARED" if declared else "NOT_PROVIDED",
        "work_mode": work_mode or "UNRESOLVED — determine from the requested change and verified repository state",
        "platforms": platforms or ["UNRESOLVED — verify target surfaces, environments, and input modes"],
        "facts": facts,
        "pressures": pressures,
        "other": other,
        "provenance": "Values in this block come only from the caller; the runtime never derives them from brief vocabulary.",
    }


def _pressure_inquiry() -> list[dict[str, str]]:
    return [
        {
            "dimension": "user outcome and context",
            "question": "What outcome is each primary actor trying to reach, in what situation, frequency, environment, and level of consequence?",
        },
        {
            "dimension": "business or organizational outcome",
            "question": "Which outcome, transaction, adoption, efficiency, trust, learning, or relationship matters—and what evidence would show progress without harming the user outcome?",
        },
        {
            "dimension": "objects, content, and state",
            "question": "Which real objects, attributes, relationships, content types, lifecycle states, exceptions, and provenance shape the experience?",
        },
        {
            "dimension": "journey and decision structure",
            "question": "Which decisions, dependencies, entry points, return visits, recovery paths, assisted routes, and cross-channel steps determine the architecture?",
        },
        {
            "dimension": "risk and exclusion",
            "question": "Which errors, ambiguity, language needs, access barriers, performance limits, or policy constraints could cause material harm or failure?",
        },
        {
            "dimension": "identity and perception",
            "question": "Which verified product, brand, audience, place, material, content, or behavioral truths should the experience make perceptible?",
        },
    ]


def _research_plan() -> dict[str, Any]:
    return {
        "posture": "targeted, decision-led research; never a mandatory moodboard",
        "triggers": [
            {
                "activate_when": "Current standards, law, policy, safety, accessibility, localization, or platform behavior could change a material constraint.",
                "question": "What current primary guidance or verified policy governs the unresolved decision?",
                "sources": "Official standards, regulator or organizational policy, primary platform documentation, and current accessibility guidance",
                "stop": "The constraint is verified, safely bounded, or explicitly left UNKNOWN with a recovery path.",
            },
            {
                "activate_when": "Real products, category behavior, culture, or audience expectations could reveal a material alternative or risk.",
                "question": "Which current examples widen the architecture, content, interaction, or identity space without becoming a template?",
                "sources": "Real current products, first-party product material, credible domain research, and direct observation",
                "stop": "New examples repeat known approaches and no longer change a candidate or risk.",
            },
            {
                "activate_when": "A font, icon family, package, browser technique, image generator, or other dependency is a live candidate.",
                "question": "Which current official asset, capability, license, version, and integration constraints affect the choice?",
                "sources": "Official documentation, authoritative registries, licenses, release notes, and real target-platform renders",
                "stop": "Viable candidates and their constraints are verified; speculative dependencies are not installed.",
            },
        ],
        "activation_rule": "The agent activates only checks that can change a material decision. Brief vocabulary never activates research automatically.",
        "synthesis_rule": "Extract transferable principles, tensions, and counterexamples. Do not copy a competitor's composition, brand codes, imagery, or interaction signature.",
        "evidence_record": "decision | source | observed fact | implication | confidence | freshness | candidate changed?",
    }


def _local_analogs(analog_query: str | None) -> dict[str, Any]:
    query = str(analog_query or "").strip()
    if not query:
        return {
            "status": "NOT_REQUESTED",
            "query": None,
            "product_analogs": [],
        }

    result = search(query, "product", 3)
    analogs = [
        {
            "status": "UNVERIFIED_ANALOG",
            "label": item.get("Product Type", "Unlabelled analog"),
            "catalog_terms": item.get("Keywords", ""),
            "warning": "The caller chose this lexical query. BM25 rank is not semantic confidence; use the row only to widen questions or alternatives.",
        }
        for item in result.get("results", [])
    ]
    return {
        "status": "REQUESTED_BY_CALLER",
        "query": query,
        "product_analogs": analogs,
    }


def _unknowns() -> list[str]:
    return [
        "What in the brief is verified fact, what is a stakeholder claim, what is an assumption, and what evidence is missing?",
        "What would make the current framing wrong, incomplete, or too narrow?",
        "Which important pressure may be absent from every bundled vocabulary or familiar product category?",
        "Which parts of the problem require domain, language, cultural, legal, or operational expertise the runtime does not possess?",
    ]


def _identity_sources() -> list[str]:
    return [
        "The product's real objects, construction, workflow, state transitions, or information relationships",
        "Audience language, culture, habits, access needs, and context of use",
        "Verified brand history, voice, assets, materials, place, and behavior",
        "The form, authorship, provenance, and quality of real content—not placeholder volume or trend labels",
        "Physical, service, operational, editorial, commercial, or community realities discovered in the project",
    ]


class DecisionPacketGenerator:
    """Generate an open design workbench without selecting the design."""

    def generate(
        self,
        brief: str,
        project_name: str | None = None,
        *,
        declared_context: dict[str, Any] | None = None,
        analog_query: str | None = None,
    ) -> dict[str, Any]:
        context = _normalize_declared_context(declared_context)
        pressure_status = (
            "CALLER_DECLARED — verify provenance and causal relevance"
            if context["pressures"]
            else "UNRESOLVED — derive from verified project evidence; do not classify from brief keywords"
        )
        evidence = _local_analogs(analog_query)

        return {
            "schema_version": SCHEMA_VERSION,
            "project_name": project_name or "Untitled design inquiry",
            "brief": brief,
            "situation": {
                "framing_status": "UNRESOLVED" if context["status"] == "NOT_PROVIDED" else "PARTIALLY_DECLARED",
                "mode": context["work_mode"],
                "platforms": context["platforms"],
                "declared_facts": context["facts"],
                "other_declared_context": context["other"],
                "declaration_provenance": context["provenance"],
                "pressure_status": pressure_status,
                "design_pressures": context["pressures"],
                "pressure_inquiry": _pressure_inquiry(),
                "extension_rule": "Add any evidence-backed pressure the project reveals, even when it has no name or precedent in Snowe's local vocabulary.",
                "unknowns": _unknowns(),
                "language_policy": "The runtime preserves the brief verbatim and does not detect language, translate, classify intent, or privilege English vocabulary.",
                "ambiguity_policy": "Ambiguous terms such as service, platform, audit, history, store, and application remain unresolved until surrounding evidence establishes their role.",
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
            "research": _research_plan(),
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
                "identity_sources": _identity_sources(),
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
                "eligible_outcomes": [
                    "No animation",
                    "State feedback only",
                    "Continuity or explanatory motion",
                    "Expressive motion with an earned narrative or identity role",
                ],
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
                "status": evidence["status"],
                "role": "caller-requested lexical analogs only—never classification, pressure inference, direction, or architecture",
                "query": evidence["query"],
                "product_analogs": evidence["product_analogs"],
                "absence_rule": "NOT_REQUESTED, no match, or removal of the local dataset changes no framing or design obligation.",
                "limitations": "Bundled catalogs are optional English-oriented snapshots. They may widen vocabulary after the question is known; they cannot establish current truth or bound synthesis.",
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
        f"- **Framing:** {situation['framing_status']}",
        f"- **Mode:** {situation['mode']}",
        f"- **Platforms:** {', '.join(situation['platforms'])}",
        f"- **Pressure status:** {situation['pressure_status']}",
        f"- **Language policy:** {situation['language_policy']}",
        f"- **Ambiguity policy:** {situation['ambiguity_policy']}",
        f"- **Fact policy:** {situation['fact_policy']}",
        "",
        "### Caller-declared facts",
        "",
    ]
    _append_list(lines, situation["declared_facts"] or ["UNKNOWN — no structured facts were supplied"])
    lines.extend(
        (
            "",
        "### Design pressures",
        "",
        )
    )
    _append_list(lines, situation["design_pressures"] or ["UNRESOLVED — establish from evidence before architecture"])
    lines.extend(("", "### Pressure inquiry", ""))
    for item in situation["pressure_inquiry"]:
        lines.append(f"- **{item['dimension'].title()}:** {item['question']}")
    lines.append(f"- **Extension rule:** {situation['extension_rule']}")
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
    lines.extend(("", "## External research", "", f"- **Posture:** {research['posture']}", f"- **Activation:** {research['activation_rule']}", f"- **Synthesis:** {research['synthesis_rule']}", ""))
    for trigger in research["triggers"]:
        lines.append(f"- **Activate when:** {trigger['activate_when']}")
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
    lines.extend(("", "## Motion", "", f"- **Status:** {motion['status']}", f"- **Decision:** {motion['decision_question']}", f"- **Record:** `{motion['record']}`", "", "### Eligible outcomes", ""))
    _append_list(lines, motion["eligible_outcomes"])
    lines.extend(("", "### Rules", ""))
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
    lines.extend(("", "## Local evidence", "", f"- **Status:** {evidence['status']}", f"- **Role:** {evidence['role']}", f"- **Query:** {evidence['query'] or 'none'}", f"- **Absence rule:** {evidence['absence_rule']}", f"- **Limitations:** {evidence['limitations']}", ""))
    for analog in evidence["product_analogs"]:
        lines.append(f"- **{analog['label']}** — `{analog['status']}`")
        if analog["catalog_terms"]:
            lines.append(f"  - Catalog terms: {analog['catalog_terms']}")
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
    declared_context: dict[str, Any] | None = None,
    analog_query: str | None = None,
) -> str:
    packet = DecisionPacketGenerator().generate(
        brief,
        project_name,
        declared_context=declared_context,
        analog_query=analog_query,
    )
    if persist:
        persist_decision_packet(packet, page=page, output_dir=output_dir, page_brief=page_brief)
    if output_format == "json":
        return format_packet_json(packet)
    return format_packet_markdown(packet)
