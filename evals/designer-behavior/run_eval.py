#!/usr/bin/env python3
"""Deterministic contracts for Snowe's open design practice.

The runner checks packet/repository epistemic boundaries and metamorphic
invariants. It never invokes a model or skill host and never scores creativity,
taste, or a preferred layout. Rendered/browser regressions and observed-agent
behavior are separate evidence surfaces.
"""

from __future__ import annotations

import json
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


def evaluate() -> dict[str, Any]:
    data = json.loads((Path(__file__).with_name("scenarios.json")).read_text(encoding="utf-8"))
    generator = DecisionPacketGenerator()
    findings: list[dict[str, Any]] = []

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

    route_failures: list[str] = []
    route_evidence: list[str] = []
    for trace in data["progressive_disclosure"]:
        overlap = sorted(set(trace["needed"]) & set(trace["not_needed"]))
        if overlap:
            route_failures.append(f"{trace['id']}: contradictory routes {', '.join(overlap)}")
        for reference in trace["needed"] + trace["not_needed"]:
            if not (SKILL_ROOT / "references" / reference).is_file():
                route_failures.append(f"{trace['id']}: missing reference {reference}")
        for reference in trace["needed"]:
            if f"references/{reference}" not in skill_text:
                route_failures.append(f"{trace['id']}: router omits {reference}")
        if not trace["reason"].strip():
            route_failures.append(f"{trace['id']}: missing causal reason")
        route_evidence.append(
            f"{trace['id']}: {', '.join(trace['needed'])}; excludes {', '.join(trace['not_needed'])}"
        )
    if "Do not preload the library" not in skill_text:
        route_failures.append("router lacks an explicit no-preload boundary")
    findings.append(finding("progressive-disclosure", route_failures, route_evidence))

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
        "method": "deterministic contract and metamorphic checks; no model or skill-host invocation and no creativity, taste, layout, or style score",
        "evidence_scope": {
            "deterministic_contracts": {
                "status": "MEASURED",
                "covers": "packet output, repository boundaries, and authored progressive-disclosure fixtures",
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
