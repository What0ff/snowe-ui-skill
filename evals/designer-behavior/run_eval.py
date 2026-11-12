#!/usr/bin/env python3
"""Deterministic contracts for Snowe's open design practice.

The runner checks packet/repository epistemic boundaries and metamorphic
invariants. It never invokes a model or skill host and never scores creativity,
taste, or a preferred layout. Rendered/browser regressions and observed-agent
behavior are separate evidence surfaces.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = ROOT / "skill" / "snowe-ui-skill"
SKILL_SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

import decision_packet as packet_module  # noqa: E402
from decision_packet import DecisionPacketGenerator  # noqa: E402


FORBIDDEN_SELECTION_KEYS = {
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
    "signals",
}


def nested_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            keys.add(key)
            keys.update(nested_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(nested_keys(child))
    return keys


def framing_signature(packet: dict[str, Any]) -> dict[str, Any]:
    situation = packet["situation"]
    return {
        "framing_status": situation["framing_status"],
        "mode": situation["mode"],
        "platforms": situation["platforms"],
        "pressure_status": situation["pressure_status"],
        "design_pressures": situation["design_pressures"],
        "pressure_inquiry": situation["pressure_inquiry"],
        "unknowns": situation["unknowns"],
        "language_policy": situation["language_policy"],
        "architecture_status": packet["architecture"]["status"],
        "asset_status": packet["assets"]["visual_need_decision"]["status"],
        "motion_status": packet["motion"]["status"],
        "local_evidence_status": packet["local_evidence"]["status"],
    }


def open_contract_failures(packet: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    unexpected = sorted(FORBIDDEN_SELECTION_KEYS & nested_keys(packet))
    if unexpected:
        failures.append("selected or classified keys: " + ", ".join(unexpected))
    if not packet["architecture"]["status"].startswith("OPEN"):
        failures.append("architecture was prematurely committed")
    if packet["assets"]["visual_need_decision"]["status"] != "OPEN":
        failures.append("visual asset was automatically selected")
    if not packet["motion"]["status"].startswith("OPEN"):
        failures.append("motion was automatically selected")
    if packet["local_evidence"]["status"] != "NOT_REQUESTED":
        failures.append("local evidence was retrieved without caller opt-in")
    if packet["local_evidence"]["product_analogs"]:
        failures.append("default packet contains analogs")
    return failures


def finding(scenario: str, failures: list[str], evidence: list[str]) -> dict[str, Any]:
    return {
        "verdict": "REJECT" if failures else "KEEP",
        "scenario": scenario,
        "evidence": failures or evidence,
    }


SCOPE_MARKERS = (
    "calibrate consequence and change surface",
    "high-salience consequence",
    "actual owner(s)",
    "dependencies and sibling consumers",
    "shared-system proof",
    "material uncertainty in user goals",
    "do not infer depth from the request's wording",
    "decision packet",
    "references loaded",
    "stop condition",
    "escalation trigger",
    "the loop is conditional",
    "proof intensity independently of process breadth",
)


ARTIFACT_MARKERS = {
    "depth record": ("depth record",),
    "affected invariant": ("affected invariant",),
    "rendered state": ("affected state", "rendered state"),
    "shared-system proof": ("shared-system proof",),
    "baseline and challenger": ("baseline/challenger", "baseline and challenger"),
    "sibling-context render": ("sibling contexts",),
    "causal decision record": ("causal decision record", "causal record"),
    "affected responsive render": ("responsive",),
    "whole-journey model": ("whole journey",),
    "structurally different candidates": ("structurally different candidates",),
    "proof slice": ("proof slices", "proof slice"),
    "strongest rejected alternative": ("strongest rejected alternative",),
    "implementation contract": ("implementation contract",),
    "high-consequence proof": ("failure/recovery path", "adverse states"),
}

UNCERTAINTY_SURFACE_FIELDS = {
    "user_goals",
    "topology",
    "journey",
    "content_object_relationships",
    "interaction_contracts",
    "responsive_transformations",
    "system_contracts",
}

DIRECT_BROAD_REFERENCES = {
    "page-hierarchy.md",
    "exploration-protocol.md",
    "experience-architecture.md",
    "art-direction-gate.md",
    "design-foundations.md",
    "imagery-and-assets.md",
    "motion-and-interaction.md",
    "research-and-evidence.md",
    "designer-evaluation.md",
    "cli-reference.md",
}

SCOPE_REFERENCE_UNIVERSE = {
    "page-hierarchy.md",
    "exploration-protocol.md",
    "experience-architecture.md",
    "art-direction-gate.md",
    "design-foundations.md",
    "imagery-and-assets.md",
    "iconography-system.md",
    "motion-and-interaction.md",
    "research-and-evidence.md",
    "designer-evaluation.md",
    "cli-reference.md",
    "quality-gates.md",
}

SCOPE_LOADED_REFERENCES = {
    "trivial-visual-correction": {"quality-gates.md"},
    "narrow-accessibility-defect": {"quality-gates.md"},
    "shared-owner-component-symptom": {"exploration-protocol.md", "quality-gates.md"},
    "medium-established-feature": {"exploration-protocol.md", "quality-gates.md"},
    "open-journey-architecture": {
        "exploration-protocol.md",
        "experience-architecture.md",
        "designer-evaluation.md",
        "quality-gates.md",
    },
    "narrow-high-consequence-correction": {"quality-gates.md"},
}

SCOPE_SKIPPED_PROCESS = {
    "Direct": {
        "decision packet",
        "broad research",
        "candidate generation",
        "architecture work",
        "asset exploration",
        "motion exploration",
        "designer evaluation",
    },
    "Focused": {
        "decision packet",
        "broad research",
        "whole-journey framing",
        "Portfolio candidate set",
        "unrelated asset exploration",
        "unrelated motion exploration",
        "designer evaluation",
    },
    "Portfolio": {
        "broad research",
        "unrelated imagery exploration",
        "unrelated custom icon work",
        "unrelated motion exploration",
    },
}

SCOPE_TRACE_CONTRACTS = {
    "trivial-visual-correction": {
        "artifacts": (
            "depth record",
            "affected invariant",
            "rendered state",
        ),
        "stop_evidence": "rendered affected state confirms the invariant",
        "escalation_evidence": "new owner, sibling consumer, or material contract uncertainty",
    },
    "narrow-accessibility-defect": {
        "artifacts": (
            "depth record",
            "affected invariant",
            "rendered state",
        ),
        "stop_evidence": "keyboard and rendered focus proof closes the invariant",
        "escalation_evidence": "the focus controller is shared by sibling dialogs or the contract remains unknown",
    },
    "shared-owner-component-symptom": {
        "artifacts": (
            "depth record",
            "shared-system proof",
            "baseline and challenger",
            "sibling-context render",
        ),
        "stop_evidence": "baseline/challenger renders preserve the shared contract in representative sibling contexts",
        "escalation_evidence": "proof exposes material uncertainty in goals, topology, journey, content, interaction, responsive, or system contracts",
    },
    "medium-established-feature": {
        "artifacts": (
            "depth record",
            "causal decision record",
            "baseline and challenger",
            "affected responsive render",
        ),
        "stop_evidence": "the affected workflow and responsive proof close the placement/disclosure choice",
        "escalation_evidence": "the feature changes the accepted object model, journey, interaction contract, or responsive transformation",
    },
    "open-journey-architecture": {
        "artifacts": (
            "depth record",
            "whole-journey model",
            "structurally different candidates",
            "proof slice",
            "strongest rejected alternative",
        ),
        "stop_evidence": "whole-journey proof and implementation contract close the material uncertainties",
        "escalation_evidence": "new material uncertainty or failed proof slice reopens the relevant decision",
    },
    "narrow-high-consequence-correction": {
        "artifacts": (
            "depth record",
            "affected invariant",
            "rendered state",
            "high-consequence proof",
        ),
        "stop_evidence": "keyboard, zoom, high-contrast, adverse-state, and rollback checks close the exact confirmation-control invariant",
        "escalation_evidence": "the repair exposes a shared owner or uncertainty in medication action semantics, recovery, or system contracts",
    },
}

PROGRESSIVE_DISCLOSURE_CONTRACTS = {
    "narrow-focus-fix": (
        {"quality-gates.md"},
        {"experience-architecture.md", "imagery-and-assets.md", "motion-and-interaction.md", "designer-evaluation.md"},
    ),
    "journey-architecture": (
        {"exploration-protocol.md", "experience-architecture.md"},
        {"iconography-system.md", "imagery-and-assets.md", "motion-and-interaction.md"},
    ),
    "no-image-decision": (
        {"imagery-and-assets.md"},
        {"iconography-system.md", "motion-and-interaction.md", "designer-evaluation.md"},
    ),
    "routine-icon": (
        {"iconography-system.md"},
        {"imagery-and-assets.md", "art-direction-gate.md", "experience-architecture.md"},
    ),
    "benchmark-comparison": (
        {"designer-evaluation.md"},
        {"cli-reference.md", "iconography-system.md"},
    ),
}

PROGRESSIVE_DISCLOSURE_REASONS = {
    "narrow-focus-fix": "The product structure and visual language are accepted; only an interaction/accessibility defect is open.",
    "journey-architecture": "The organizing logic and whole journey are open; visual assets and motion are not yet decisions.",
    "no-image-decision": "The active comparison is image versus no image; generation workflow ends when no image wins.",
    "routine-icon": "A known system action in an accepted family does not justify custom drawing or broader art direction.",
    "benchmark-comparison": "The active work is cross-scenario evidence, not asset production or local retrieval.",
}

# Short concept anchors guard the scoped-process invariants. Each anchor is a
# few words that must survive any rewrite; the prose around it may change
# freely. Verbatim section copies used to live here and froze SKILL.md wording.
SKILL_REQUIRED_CONCEPTS = {
    "depth vocabulary": ("**Direct**", "**Focused**", "**Portfolio**"),
    "progressive disclosure without preloading": ("Do not preload",),
    "provisional depth escalates and de-escalates": ("Escalate", "De-escalate"),
    "consequence raises proof, not process breadth": ("proof intensity",),
    "missing evidence stays unknown": ("`UNKNOWN`",),
    "correction check gates completion": ("`BLOCKED`", "`REVIEW_REQUIRED`"),
    "decision packet optional, analogs opt-in": ("--decision-packet", "--analog-query"),
}
EXPLORATION_REQUIRED_CONCEPTS = {
    "direct work opens no packet or workshop": ("do not open a packet",),
}
# Deliberate negative fixtures; this is not a general contradiction detector.
FORBIDDEN_GLOBAL_OBLIGATIONS = (
    "every task must run architecture",
    "preload the entire library for every task",
    "preload all references",
)
DELIVERY_DEPTH_MARKERS = ("**Direct:**", "**Focused:**", "**Portfolio:**")
UNSCOPED_DELIVERY = re.compile(r"\b(?:every|all) tasks?\b", re.IGNORECASE)


def reference_route_failures(skill_text: str) -> list[str]:
    """Every installed reference must be reachable from the root router."""
    return [
        f"Scoped contract route missing for references/{path.name}"
        for path in sorted((SKILL_ROOT / "references").glob("*.md"))
        if f"references/{path.name}" not in skill_text
    ]


def scope_document_contract_failures(skill_text: str, exploration_text: str) -> list[str]:
    """Guard scoped-process invariants by concept anchors, routes and negative fixtures."""
    failures: list[str] = []
    for label, anchors in SKILL_REQUIRED_CONCEPTS.items():
        missing = [anchor for anchor in anchors if anchor not in skill_text]
        if missing:
            failures.append(f"Required scoped contract concept missing ({label}): {', '.join(missing)}")
    lowered_exploration = exploration_text.lower()
    for label, anchors in EXPLORATION_REQUIRED_CONCEPTS.items():
        missing = [anchor for anchor in anchors if anchor not in lowered_exploration]
        if missing:
            failures.append(f"Required scoped contract concept missing ({label}): {', '.join(missing)}")
    for line in (skill_text + "\n" + exploration_text).splitlines():
        if line.strip().lower().startswith(FORBIDDEN_GLOBAL_OBLIGATIONS):
            failures.append("Contradictory global scoped contract obligation")
    failures.extend(reference_route_failures(skill_text))
    return failures


PAGE_HIERARCHY_CLAUSES = (
    "A specified local property correction stays Direct.",
    "This is a Focused route when the objects and surrounding product flow are known.",
    "Only then choose grouping, composition, components and visual emphasis.",
    "Never use a global forbidden-word list.",
    "Identical row buttons for different objects are legitimate distinct actions.",
    "verify it against the handler/destination",
    "Record four separate outcomes: technical contract, evidence integrity, visual assessment and user acceptance.",
    "Equally, approved quiet or native-looking controls are valid",
)


def page_hierarchy_contract_failures(documents: dict[str, str]) -> list[str]:
    """Critical authored clauses/routes only; no semantic or aesthetic certification."""
    guide = documents.get("page-hierarchy.md", "")
    failures = [f"Page hierarchy clause missing: {clause}" for clause in PAGE_HIERARCHY_CLAUSES if clause not in guide]
    for owner in ("SKILL.md", "experience-architecture.md", "exploration-protocol.md", "quality-gates.md"):
        if "page-hierarchy.md" not in documents.get(owner, ""):
            failures.append(f"Page hierarchy route missing: {owner}")
    return failures


DIRECT_DELIVERY = {
    "calibrated depth and loaded/skipped routes",
    "owner and affected invariant",
    "implementation scope",
    "affected states and proof",
    "corrections after review",
    "remaining unknowns",
    "executed evidence versus inference",
}
FOCUSED_DELIVERY = {
    "calibrated depth and loaded/skipped routes",
    "affected causal decision",
    "baseline and closest challenger",
    "representative sibling contexts when shared",
    "implementation scope",
    "affected states and proof",
    "corrections after review",
    "remaining unknowns",
    "executed evidence versus inference",
}
PORTFOLIO_DELIVERY = {
    "calibrated depth and loaded/skipped routes",
    "chosen architecture and thesis",
    "material causal decisions",
    "strongest rejected alternative",
    "external evidence that changed the outcome, if any",
    "asset and motion decisions when live",
    "implementation scope",
    "rendered proof slices",
    "accessibility and performance checks",
    "corrections after review",
    "remaining unknowns",
    "executed evidence versus inference",
}


def scope_calibration_contract(
    data: dict[str, Any], skill_text: str, exploration_text: str
) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    """Check authored process traces without pretending to run a host/model.

    These fixtures record the evidence a host should observe and the route it
    should take. They are deterministic contract probes, not an automatic
    task classifier and not causal evidence about an agent's behavior.
    """

    failures: list[str] = []
    evidence: list[str] = []
    traces: list[dict[str, Any]] = []
    combined = (skill_text + "\n" + exploration_text).lower()

    failures.extend(scope_document_contract_failures(skill_text, exploration_text))
    hierarchy_documents = {name: (SKILL_ROOT / "references" / name).read_text(encoding="utf-8")
                           for name in ("page-hierarchy.md", "experience-architecture.md", "quality-gates.md")}
    hierarchy_documents.update({"SKILL.md": skill_text, "exploration-protocol.md": exploration_text})
    failures.extend(page_hierarchy_contract_failures(hierarchy_documents))

    missing_markers = [marker for marker in SCOPE_MARKERS if marker not in combined]
    if missing_markers:
        failures.append("scope calibration mechanism missing: " + ", ".join(missing_markers))

    # Delivery is structurally closed: one depth-proportional preface and one
    # obligation per depth. This rejects a later global workshop obligation
    # without interpreting task vocabulary or classifying a brief.
    if "## Delivery" not in skill_text:
        failures.append("depth-proportional delivery section is missing")
    else:
        delivery_section = skill_text.split("## Delivery", 1)[1]
        if any(marker not in delivery_section for marker in DELIVERY_DEPTH_MARKERS) or UNSCOPED_DELIVERY.search(delivery_section):
            failures.append(
                "delivery section contains an unscoped or missing process obligation"
            )

    cases = data.get("scope_calibration", [])
    expected_ids = {
        "trivial-visual-correction",
        "narrow-accessibility-defect",
        "shared-owner-component-symptom",
        "medium-established-feature",
        "open-journey-architecture",
        "narrow-high-consequence-correction",
    }
    actual_ids = {case.get("id") for case in cases}
    if (
        len(cases) != len(expected_ids)
        or len(actual_ids) != len(cases)
        or actual_ids != expected_ids
    ):
        failures.append(
            "scope probes must cover exactly the six calibrated cases; got "
            + ", ".join(sorted(str(value) for value in actual_ids))
        )

    for case in cases:
        case_id = case.get("id", "<missing-id>")
        observed = case.get("observed", {})
        expected = case.get("expected", {})
        depth = expected.get("depth")
        loaded = expected.get("loaded_references", [])
        skipped = expected.get("skipped_references", [])
        if depth not in {"Direct", "Focused", "Portfolio"}:
            failures.append(f"{case_id}: invalid expected depth {depth!r}")
        if set(loaded) & set(skipped):
            failures.append(f"{case_id}: loaded and skipped reference routes overlap")
        expected_loaded = SCOPE_LOADED_REFERENCES.get(case_id, set())
        expected_skipped = SCOPE_REFERENCE_UNIVERSE - expected_loaded
        if set(loaded) != expected_loaded or set(skipped) != expected_skipped:
            failures.append(
                f"{case_id}: reference route diverges from the authored calibrated surface"
            )
        trace_contract = SCOPE_TRACE_CONTRACTS.get(case_id)
        if trace_contract is None:
            failures.append(f"{case_id}: authored trace contract is missing")
        else:
            if tuple(expected.get("artifacts", [])) != trace_contract["artifacts"]:
                failures.append(f"{case_id}: artifact contract diverges from the authored calibrated surface")
            if expected.get("stop_evidence") != trace_contract["stop_evidence"]:
                failures.append(f"{case_id}: stop evidence contract diverges from the authored calibrated surface")
            if expected.get("escalation_evidence") != trace_contract["escalation_evidence"]:
                failures.append(
                    f"{case_id}: escalation evidence contract diverges from the authored calibrated surface"
                )
        if not expected.get("artifacts"):
            failures.append(f"{case_id}: no process artifacts recorded")
        if not expected.get("stop_evidence"):
            failures.append(f"{case_id}: no stop evidence recorded")
        if not expected.get("escalation_evidence"):
            failures.append(f"{case_id}: no escalation evidence recorded")
        delivery = expected.get("delivery", [])
        if len(delivery) != len(set(delivery)):
            failures.append(f"{case_id}: duplicate delivery fields")
        if not observed.get("consequence"):
            failures.append(f"{case_id}: high-salience consequence is missing")
        if not observed.get("affected_invariant"):
            failures.append(f"{case_id}: affected invariant is missing")
        if not observed.get("owner") or "shared_consumers" not in observed:
            failures.append(f"{case_id}: owner/shared-consumer inspection is missing")
        if "material_uncertainty" not in observed:
            failures.append(f"{case_id}: material-uncertainty inspection is missing")
        uncertainty_surface = observed.get("uncertainty_surface")
        valid_uncertainty_surface = (
            isinstance(uncertainty_surface, dict)
            and set(uncertainty_surface) == UNCERTAINTY_SURFACE_FIELDS
            and all(isinstance(value, bool) for value in uncertainty_surface.values())
        )
        if not valid_uncertainty_surface:
            failures.append(
                f"{case_id}: authored uncertainty surface must declare every documented contract as boolean"
            )
        consequence_class = observed.get("consequence_class")
        if consequence_class not in {"bounded", "high-consequence", "open-system"}:
            failures.append(f"{case_id}: consequence_class must be bounded, high-consequence, or open-system")

        # This is an authored trace field, not text classification. No task or
        # free-form uncertainty phrase is matched against a vocabulary.
        portfolio_uncertainty = bool(
            valid_uncertainty_surface and any(uncertainty_surface.values())
        )
        shared_consumers = observed.get("shared_consumers") is True
        focused_choice = observed.get("focused_choice") is True
        if depth == "Direct" and (shared_consumers or focused_choice or portfolio_uncertainty):
            failures.append(f"{case_id}: Direct route contradicts the observed owner/uncertainty surface")
        if depth == "Focused" and not (shared_consumers or focused_choice):
            failures.append(f"{case_id}: Focused route has no observed shared owner or unresolved material choice")
        if depth == "Portfolio" and not portfolio_uncertainty:
            failures.append(f"{case_id}: Portfolio route has no observed whole-system uncertainty")
        if portfolio_uncertainty and depth != "Portfolio":
            failures.append(f"{case_id}: whole-system uncertainty was flattened below Portfolio")
        if consequence_class == "high-consequence":
            if "high-consequence proof" not in expected.get("artifacts", []):
                failures.append(f"{case_id}: high-consequence bounded work lacks its proof floor")
            proof_record = " ".join(
                [
                    *[str(item) for item in expected.get("artifacts", [])],
                    str(expected.get("stop_evidence", "")),
                ]
            ).casefold()
            proof_dimensions = ("keyboard", "zoom", "high-contrast", "adverse-state", "rollback")
            missing_dimensions = [item for item in proof_dimensions if item not in proof_record]
            if missing_dimensions:
                failures.append(
                    f"{case_id}: high-consequence proof omits required dimensions: "
                    + ", ".join(missing_dimensions)
                )

        for reference in loaded + skipped:
            if not (SKILL_ROOT / "references" / reference).is_file():
                failures.append(f"{case_id}: missing reference {reference}")
            if f"references/{reference}" not in skill_text:
                failures.append(f"{case_id}: router has no route for {reference}")

        for artifact in expected.get("artifacts", []):
            markers = ARTIFACT_MARKERS.get(artifact)
            if markers and not any(marker.lower() in combined for marker in markers):
                failures.append(f"{case_id}: mechanism does not document artifact {artifact}")

        if depth == "Direct":
            required_skips = SCOPE_SKIPPED_PROCESS["Direct"]
            if not required_skips.issubset(set(expected.get("skipped_process", []))):
                failures.append(f"{case_id}: Direct route does not record all broad-process skips")
            broad_loaded = sorted(DIRECT_BROAD_REFERENCES.intersection(loaded))
            if broad_loaded:
                failures.append(
                    f"{case_id}: Direct route loaded broad references: "
                    + ", ".join(broad_loaded)
                )
            if set(expected.get("skipped_process", [])) != required_skips:
                failures.append(
                    f"{case_id}: Direct route records an undeclared process activation or omission"
                )
            if set(delivery) != DIRECT_DELIVERY:
                failures.append(
                    f"{case_id}: Direct delivery is not bounded to owner/invariant/proof"
                )
        elif depth == "Focused":
            if "exploration-protocol.md" not in loaded:
                failures.append(f"{case_id}: Focused route omitted exploration protocol")
            if "whole-journey framing" not in expected.get("skipped_process", []):
                failures.append(f"{case_id}: Focused route lacks a whole-journey stop boundary")
            if set(expected.get("skipped_process", [])) != SCOPE_SKIPPED_PROCESS["Focused"]:
                failures.append(
                    f"{case_id}: Focused route records an undeclared process activation or omission"
                )
            if set(delivery) != FOCUSED_DELIVERY:
                failures.append(
                    f"{case_id}: Focused delivery does not match the affected-decision proof"
                )
        elif depth == "Portfolio":
            if "experience-architecture.md" not in loaded:
                failures.append(f"{case_id}: Portfolio route omitted architecture reference")
            if not observed.get("material_uncertainty"):
                failures.append(f"{case_id}: Portfolio route has no material uncertainty")
            if set(expected.get("skipped_process", [])) != SCOPE_SKIPPED_PROCESS["Portfolio"]:
                failures.append(
                    f"{case_id}: Portfolio route records an unrelated process activation or omission"
                )
            if set(delivery) != PORTFOLIO_DELIVERY:
                failures.append(
                    f"{case_id}: Portfolio delivery omits the whole-problem decision record"
                )

        evidence.append(
            f"{case_id}: {depth}; loaded {', '.join(loaded) or 'none'}; "
            f"skipped {', '.join(skipped) or 'none'}; "
            f"proof {expected.get('stop_evidence', '')}"
        )
        traces.append(
            {
                "id": case_id,
                "evidence_category": "deterministic_contracts",
                "evidence_type": "authored deterministic process trace",
                "host_causation": "NOT_MEASURED",
                "overhead": {"tokens": "NOT_OBSERVABLE", "time": "NOT_OBSERVABLE"},
                "task": case.get("task"),
                "observed": observed,
                "route": {
                    "depth": depth,
                    "references_loaded": loaded,
                    "references_not_loaded": skipped,
                    "process_not_activated": expected.get("skipped_process", []),
                    "artifacts": expected.get("artifacts", []),
                    "delivery": delivery,
                    "stop_evidence": expected.get("stop_evidence"),
                    "escalation_evidence": expected.get("escalation_evidence"),
                },
            }
        )

    return failures, evidence, traces


def progressive_disclosure_contract(
    data: dict[str, Any], skill_text: str
) -> tuple[list[str], list[str]]:
    """Validate authored route fixtures without classifying a task brief."""
    failures: list[str] = []
    evidence: list[str] = []
    traces = data.get("progressive_disclosure", [])
    actual_ids = {trace.get("id") for trace in traces}
    if actual_ids != set(PROGRESSIVE_DISCLOSURE_CONTRACTS) or len(traces) != len(actual_ids):
        failures.append("progressive-disclosure fixtures do not match the canonical route set")
    for trace in traces:
        trace_id = trace.get("id", "<missing-id>")
        needed = set(trace.get("needed", []))
        not_needed = set(trace.get("not_needed", []))
        expected = PROGRESSIVE_DISCLOSURE_CONTRACTS.get(trace_id)
        if expected is None or (needed, not_needed) != expected:
            failures.append(f"{trace_id}: progressive route diverges from its authored surface")
        expected_reason = PROGRESSIVE_DISCLOSURE_REASONS.get(trace_id)
        if expected_reason is None or trace.get("reason") != expected_reason:
            failures.append(f"{trace_id}: progressive route reason diverges from its authored surface")
        overlap = sorted(needed & not_needed)
        if overlap:
            failures.append(f"{trace_id}: contradictory routes {', '.join(overlap)}")
        for reference in needed | not_needed:
            if not (SKILL_ROOT / "references" / reference).is_file():
                failures.append(f"{trace_id}: missing reference {reference}")
        for reference in needed:
            if f"references/{reference}" not in skill_text:
                failures.append(f"{trace_id}: router omits {reference}")
        if not str(trace.get("reason", "")).strip():
            failures.append(f"{trace_id}: missing causal reason")
        evidence.append(
            f"{trace_id}: {', '.join(trace.get('needed', []))}; "
            f"excludes {', '.join(trace.get('not_needed', []))}"
        )
    if "Do not preload the library" not in skill_text:
        failures.append("router lacks an explicit no-preload boundary")
    return failures, evidence


def evaluate() -> dict[str, Any]:
    data = json.loads((Path(__file__).with_name("scenarios.json")).read_text(encoding="utf-8"))
    generator = DecisionPacketGenerator()
    findings: list[dict[str, Any]] = []
    scope_traces: list[dict[str, Any]] = []

    for scenario in data["core_scenarios"]:
        packet = generator.generate(
            scenario["brief"],
            scenario["id"],
            declared_context=scenario["declared_context"],
        )
        failures = open_contract_failures(packet)
        expected_pressures = scenario["declared_context"]["pressures"]
        if packet["situation"]["design_pressures"] != expected_pressures:
            failures.append("caller-declared pressure was changed")
        findings.append(
            finding(
                scenario["id"],
                failures,
                ["Caller facts and pressures pass through; architecture, imagery, motion, and local evidence remain open."],
            )
        )

    for pair in data["equivalence_pairs"]:
        left = generator.generate(pair["left"])
        right = generator.generate(pair["right"])
        failures = open_contract_failures(left) + open_contract_failures(right)
        if framing_signature(left) != framing_signature(right):
            failures.append("language or paraphrase changed unresolved framing")
        findings.append(
            finding(
                pair["id"],
                failures,
                ["Equivalent English, Russian, or mixed-language briefs retain the same unresolved framing contract."],
            )
        )

    ambiguity_failures: list[str] = []
    for case in data["ambiguity_cases"]:
        packet = generator.generate(case["brief"])
        situation = packet["situation"]
        if situation["design_pressures"]:
            ambiguity_failures.append(f"{case['id']}: inferred a pressure")
        if not situation["mode"].startswith("UNRESOLVED"):
            ambiguity_failures.append(f"{case['id']}: inferred work mode")
        if "signals" in situation:
            ambiguity_failures.append(f"{case['id']}: emitted signals")
    findings.append(
        finding(
            "ambiguous-and-unknown-language",
            ambiguity_failures,
            ["Ambiguous roles, an unknown domain, and an under-specified brief remain unresolved."],
        )
    )

    metamorphic = data["metamorphic_cases"]
    stable = metamorphic["stable_paraphrase"]
    stable_left = generator.generate(stable["left"])
    stable_right = generator.generate(stable["right"])
    stable_failures = []
    if framing_signature(stable_left) != framing_signature(stable_right):
        stable_failures.append("small paraphrase caused framing churn")
    findings.append(
        finding(
            "small-change-stability",
            stable_failures,
            ["A small wording change does not change the unresolved contract."],
        )
    )

    changed = metamorphic["meaningful_business_change"]
    changed_left = generator.generate(changed["brief"], declared_context=changed["left_context"])
    changed_right = generator.generate(changed["brief"], declared_context=changed["right_context"])
    change_failures = []
    if changed_left["situation"]["design_pressures"] == changed_right["situation"]["design_pressures"]:
        change_failures.append("meaningful caller-declared business change did not change pressures")
    if changed_left["architecture"] != changed_right["architecture"]:
        change_failures.append("shared architecture workbench changed before synthesis")
    findings.append(
        finding(
            "meaningful-business-change",
            change_failures,
            ["Explicit business differences change pressures without selecting a layout or style."],
        )
    )

    preservation = metamorphic["preservation"]
    preserved = generator.generate(
        preservation["brief"],
        declared_context=preservation["declared_context"],
    )
    skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    preserve_failures = []
    if preserved["situation"]["mode"] != "evolution":
        preserve_failures.append("explicit evolution mode was not preserved")
    if preservation["declared_context"]["facts"] != preserved["situation"]["declared_facts"]:
        preserve_failures.append("coherent-system preservation fact was lost")
    if "Preserve a coherent existing system" not in skill_text:
        preserve_failures.append("router does not protect accepted coherent systems")
    findings.append(
        finding(
            "coherent-system-preservation",
            preserve_failures,
            ["A bounded defect can preserve accepted architecture and visual-system facts."],
        )
    )

    discretion = generator.generate("Unresolved product")
    outcomes = discretion["assets"]["visual_need_decision"]["eligible_outcomes"]
    discretion_failures = []
    if "No image" not in outcomes:
        discretion_failures.append("no-image outcome disappeared")
    if "No animation" not in discretion["motion"]["eligible_outcomes"]:
        discretion_failures.append("no-animation outcome disappeared")
    if discretion["assets"]["custom_graphics"].get("reject_when") is None:
        discretion_failures.append("custom asset rejection path disappeared")
    findings.append(
        finding(
            "asset-and-motion-discretion",
            discretion_failures,
            ["No image, rejected custom work, and no animation remain first-class outcomes."],
        )
    )

    baseline = generator.generate("Unknown domain")
    with patch.object(packet_module, "search", return_value={"results": []}):
        absent = generator.generate("Unknown domain", analog_query="catalog term with no rows")
    absence_failures = []
    for key in ("situation", "architecture", "art_direction", "assets", "motion", "responsive"):
        if baseline[key] != absent[key]:
            absence_failures.append(f"missing dataset changed {key}")
    if absent["local_evidence"]["product_analogs"]:
        absence_failures.append("empty dataset produced analogs")
    findings.append(
        finding(
            "dataset-absence",
            absence_failures,
            ["An absent or unmatched local catalog changes no framing or design obligation."],
        )
    )

    route_failures, route_evidence = progressive_disclosure_contract(data, skill_text)
    findings.append(finding("progressive-disclosure", route_failures, route_evidence))

    skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    exploration_text = (SKILL_ROOT / "references" / "exploration-protocol.md").read_text(
        encoding="utf-8"
    )
    scope_failures, scope_evidence, scope_traces = scope_calibration_contract(
        data, skill_text, exploration_text
    )
    findings.append(finding("scope-proportionality", scope_failures, scope_evidence))

    packet_source = (SKILL_SCRIPTS / "decision_packet.py").read_text(encoding="utf-8")
    boundary_failures = []
    for symbol in ("_SIGNAL_RULES", "_QUERY_EXPANSIONS", "_PRESSURES", "_detect_signals"):
        if symbol in packet_source:
            boundary_failures.append(f"semantic classifier table returned: {symbol}")
    for filename in ("landing.csv", "styles.csv", "colors.csv", "typography.csv", "motion.csv"):
        if (SKILL_ROOT / "data" / filename).exists():
            boundary_failures.append(f"obsolete recipe dataset returned: {filename}")
    findings.append(
        finding(
            "semantic-and-evidence-boundary",
            boundary_failures,
            ["No keyword classifier tables or default architecture/style/palette/font/motion recipe catalogs remain."],
        )
    )

    return {
        "skill_fingerprint": hashlib.sha256(skill_text.encode("utf-8")).hexdigest(),
        "method": "deterministic contract and metamorphic checks; no model or skill-host invocation and no creativity, taste, layout, or style score",
        "evidence_scope": {
            "deterministic_contracts": {
                "status": "MEASURED",
                "covers": "packet output, repository boundaries, authored progressive-disclosure fixtures, and authored scope-calibration traces",
            },
            "rendered_browser_regressions": {
                "status": "SEPARATE",
                "covers": "checked-in implementations and known browser states outside this runner",
            },
            "observed_real_agent_behavior": {
                "status": "NOT_MEASURED",
                "requires": "reproducible host/model runs, actual reference-load traces, repeated runs, and a control",
            },
        },
        "findings": findings,
        "scope_traces": scope_traces,
        "manual_proof_still_required": [
            "causally different rendered architectures across real scenario classes",
            "product-specific visual languages and responsive transformations",
            "interaction, focus, overflow, asset, error, and reduced-motion browser evidence",
            "cross-benchmark review of repeated topology, carriers, cards, CTAs, imagery, and motion",
        ],
    }


def main() -> int:
    result = evaluate()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 1 if any(item["verdict"] != "KEEP" for item in result["findings"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
