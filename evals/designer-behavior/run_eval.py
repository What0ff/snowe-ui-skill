#!/usr/bin/env python3
"""Contract evaluation for Snowe's open design-inquiry behavior.

This runner intentionally does not score creativity or visual quality. It
detects recipe selection, signal collisions, automatic asset/motion choices,
and epistemic-boundary regressions. Rendered artifacts still need the manual
comparative evaluation described in README.md and the skill reference.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SKILL_SCRIPTS = ROOT / "skill" / "snowe-ui-skill" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

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


def evaluate() -> dict[str, Any]:
    scenarios = json.loads((Path(__file__).with_name("scenarios.json")).read_text(encoding="utf-8"))
    generator = DecisionPacketGenerator()
    findings: list[dict[str, Any]] = []
    profiles: dict[str, tuple[str, ...]] = {}

    for scenario in scenarios:
        packet = generator.generate(scenario["brief"], scenario["id"])
        signals = set(packet["situation"]["signals"])
        profiles[scenario["id"]] = tuple(packet["situation"]["signals"])
        failures: list[str] = []

        unexpected_keys = sorted(FORBIDDEN_SELECTION_KEYS & nested_keys(packet))
        if unexpected_keys:
            failures.append("selected recipe keys: " + ", ".join(unexpected_keys))
        missing = sorted(set(scenario["expected_signals"]) - signals)
        forbidden = sorted(set(scenario["forbidden_signals"]) & signals)
        if missing:
            failures.append("missing contextual signals: " + ", ".join(missing))
        if forbidden:
            failures.append("context collision signals: " + ", ".join(forbidden))
        if not packet["architecture"]["status"].startswith("OPEN"):
            failures.append("architecture was prematurely committed")
        if packet["assets"]["visual_need_decision"]["status"] != "OPEN":
            failures.append("visual asset was automatically selected")
        if not packet["motion"]["status"].startswith("OPEN"):
            failures.append("motion was automatically selected")
        if any(
            analog.get("status") != "UNVERIFIED_ANALOG"
            for analog in packet["local_evidence"]["product_analogs"]
        ):
            failures.append("a local analog escaped its unverified evidence role")

        findings.append(
            {
                "verdict": "REJECT" if failures else "KEEP",
                "scenario": scenario["id"],
                "signals": list(packet["situation"]["signals"]),
                "design_pressures": packet["situation"]["design_pressures"],
                "local_analogs": [
                    {"label": item["label"], "matched_terms": item["matched_terms"]}
                    for item in packet["local_evidence"]["product_analogs"]
                ],
                "evidence": failures or [
                    "Architecture, imagery, and motion remain open; contextual signals and evidence roles match the scenario."
                ],
            }
        )

    duplicate_profiles: dict[tuple[str, ...], list[str]] = {}
    for scenario_id, profile in profiles.items():
        duplicate_profiles.setdefault(profile, []).append(scenario_id)
    collisions = [ids for ids in duplicate_profiles.values() if len(ids) > 1]
    if collisions:
        findings.append(
            {
                "verdict": "REVISE",
                "scenario": "cross-scenario-pressure-profile",
                "evidence": [
                    "Identical signal profiles require manual causal review: " + ", ".join(ids)
                    for ids in collisions
                ],
            }
        )

    return {
        "method": "behavioral contract findings; no creativity or taste score",
        "findings": findings,
        "manual_proof_still_required": [
            "structurally different architecture candidates from the real trade-offs",
            "product-specific art direction and coherent implemented visual language",
            "optional imagery, custom assets, and motion compared inside the real layout",
            "wide, pressure, narrow, interaction, accessibility, and reduced-motion renders",
        ],
    }


def main() -> int:
    result = evaluate()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 1 if any(item["verdict"] == "REJECT" for item in result["findings"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
