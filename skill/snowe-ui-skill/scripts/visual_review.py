#!/usr/bin/env python3
"""Check recorded visual verdicts and evidence, not automated visual quality."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import sys
import json

from checked_evidence import file_digest, object_fields, read_json, text
from decision_packet import _normalize_lexical_aliases, _reject_reparse_chain

VERDICTS = {"KEEP", "REVISE", "REJECT", "UNKNOWN"}
METHODS = {"self-review", "peer-review", "user-review"}
USER_DISPOSITIONS = {"UNCONFIRMED", "ACCEPTED", "REJECTED"}
BOUNDARY = "Recorded verdict and evidence integrity; not automated visual quality or user acceptance"


def relative_path(value):
    text(value, "path")
    path = Path(value)
    if path.is_absolute() or path.drive or ".." in path.parts or ":" in value or "\\" in value:
        raise ValueError("Use a workspace-relative path with forward slashes")
    return value


def strings(value, field, allow_empty=False):
    if not isinstance(value, list) or (not value and not allow_empty):
        raise ValueError(f"{field} must be an array of text")
    for item in value: text(item, field)
    if len(value) != len(set(value)): raise ValueError(f"Duplicate {field}")
    return value


def binding(value, render=False):
    object_fields(value, {"path", "sha256"} | ({"state", "viewport"} if render else set()))
    relative_path(value["path"])
    if not isinstance(value["sha256"], str) or not re.fullmatch(r"[a-f0-9]{64}", value["sha256"]):
        raise ValueError("Expected SHA-256 evidence binding")
    if render:
        text(value["state"], "render state")
        if not isinstance(value["viewport"], str) or not re.fullmatch(r"[1-9]\d{1,4}x[1-9]\d{1,4}@[1-4](?:\.\d{1,2})?", value["viewport"]):
            raise ValueError("Viewport must identify width x height @ pixel ratio")


def verdict(value):
    if not isinstance(value, str) or value not in VERDICTS: raise ValueError("Visual verdict must be KEEP, REVISE, REJECT or UNKNOWN")
    return value


def inspect_review(workspace, report_path):
    """Read-only check; a PASS accepts the recorded judgment, not the pixels."""
    root = _normalize_lexical_aliases(Path(os.path.abspath(workspace)), "Review workspace")
    _reject_reparse_chain(root, "Review workspace")
    report_path = relative_path(str(report_path))
    report = read_json(root / report_path)
    if not isinstance(report, dict): raise ValueError("Expected a review object")
    if report.get("schema") == "1.0":
        return {"status": "REVIEW_REQUIRED", "integrity": "UNCONFIRMED", "visual_verdict": "UNKNOWN",
                "user_acceptance": "UNCONFIRMED", "issues": ["Legacy report has no checked explicit verdict; review it again without rewriting its history"], "boundary": BOUNDARY}
    object_fields(report, {"schema", "scope", "method", "reviewer", "contract", "sources", "renders", "visualAssessment", "userAcceptance"},
                  {"date", "evidence", "inspectedCaptures", "notes"})
    if report["schema"] != "2.0": raise ValueError("Unsupported visual review schema")
    for field in ("scope", "reviewer"): text(report[field], field)
    if not isinstance(report["method"], str) or report["method"] not in METHODS: raise ValueError("Unknown review method")
    if not isinstance(report["userAcceptance"], str) or report["userAcceptance"] not in USER_DISPOSITIONS: raise ValueError("Unknown user disposition")
    binding(report["contract"])
    for field in ("sources", "renders"):
        if not isinstance(report[field], list) or not report[field]: raise ValueError(f"Review needs {field}")
        for item in report[field]: binding(item, field == "renders")
    bindings = [report["contract"], *report["sources"], *report["renders"]]
    if len({item["path"] for item in bindings}) != len(bindings): raise ValueError("Duplicate evidence path")
    assessment = report["visualAssessment"]
    object_fields(assessment, {"finding", "assessments", "findings"}, {"verdict"})
    text(assessment["finding"], "visual finding")
    overall = verdict(assessment["verdict"]) if "verdict" in assessment else "UNKNOWN"
    issues = []
    if "verdict" not in assessment: issues.append("Missing explicit visual verdict")
    renders = {item["path"]: item for item in report["renders"]}
    if not isinstance(assessment["assessments"], list) or not assessment["assessments"]:
        raise ValueError("Review needs state assessments")
    covered = set()
    negative = set()
    unknown = set()
    for item in assessment["assessments"]:
        object_fields(item, {"state", "renders", "observedAttention", "finding", "verdict"})
        text(item["state"], "assessment state"); text(item["finding"], "state finding")
        value = verdict(item["verdict"])
        strings(item["observedAttention"], "observed attention", allow_empty=value == "UNKNOWN")
        strings(item["renders"], "assessed renders")
        for name in item["renders"]:
            if name not in renders or renders[name]["state"] != item["state"]:
                raise ValueError("Assessment must reference a bound render of its own state")
            if name in covered: raise ValueError("A render was assessed more than once")
            covered.add(name)
        if value in {"REVISE", "REJECT"}: negative.add(item["state"])
        if value == "UNKNOWN": unknown.add(item["state"])
    if covered != set(renders): issues.append("Some bound renders have no assessment")
    if not isinstance(assessment["findings"], list): raise ValueError("Findings must be an array")
    ids, blocking, explained = set(), [], set()
    for item in assessment["findings"]:
        object_fields(item, {"id", "states", "owner", "observation", "consequence", "blocking", "status", "renders"}, {"resolution"})
        for field in ("id", "owner", "observation", "consequence"): text(item[field], field)
        if item["id"] in ids: raise ValueError("Duplicate finding ID")
        ids.add(item["id"])
        strings(item["states"], "finding states"); strings(item["renders"], "finding renders")
        if type(item["blocking"]) is not bool or item["status"] not in {"open", "resolved", "accepted"}:
            raise ValueError("Invalid finding disposition")
        if not set(item["renders"]) <= set(renders): raise ValueError("Finding references an unbound render")
        if set(item["states"]) != {renders[name]["state"] for name in item["renders"]}:
            raise ValueError("Finding evidence does not cover its stated scope")
        if item["status"] != "open": text(item.get("resolution"), "resolution or acceptance reason")
        if item["status"] == "accepted" and item["blocking"]: raise ValueError("A blocking finding cannot be accepted away")
        if item["status"] == "open" and item["blocking"]:
            blocking.append(item["id"])
            explained.update(item["states"])
    if negative - explained: issues.append("Negative state verdict lacks an open causal finding")
    freshness = []
    for item in bindings:
        try:
            if file_digest(root, item["path"]) != item["sha256"]: freshness.append(f"Changed: {item['path']}")
        except (OSError, ValueError) as error:
            freshness.append(f"Unavailable: {item['path']}: {error}")
    expected_states = set()
    if not freshness:
        contract = read_json(root / report["contract"]["path"])
        object_fields(contract, {"schema", "scope", "states"})
        if contract["schema"] != "1.0" or contract["scope"] != report["scope"]:
            raise ValueError("Review and attention contract disagree on scope/version")
        if not isinstance(contract["states"], list) or not contract["states"]: raise ValueError("Attention contract needs states")
        for item in contract["states"]:
            object_fields(item, {"id", "question", "priority", "cues", "competing"})
            text(item["id"], "state"); text(item["question"], "state question")
            strings(item["priority"], "expected attention"); strings(item["cues"], "intended cues")
            strings(item["competing"], "competing elements", allow_empty=True)
            if item["id"] in expected_states: raise ValueError("Duplicate contract state")
            expected_states.add(item["id"])
        if {item["state"] for item in renders.values()} != expected_states:
            issues.append("Rendered states do not cover the declared attention contract")
    if overall == "KEEP" and (negative or blocking): issues.append("KEEP contradicts unresolved visual findings")
    if overall == "KEEP" and unknown: issues.append("KEEP contradicts an unknown state assessment")
    if report["userAcceptance"] == "REJECTED": blocking.append("user-rejection")
    status = "PASS"
    if freshness or issues or overall == "UNKNOWN" or unknown: status = "REVIEW_REQUIRED"
    if not freshness and (blocking or negative or overall in {"REVISE", "REJECT"}): status = "BLOCKED"
    return {"status": status, "integrity": "STALE" if freshness else "PASS", "visual_verdict": overall,
            "method": report["method"], "user_acceptance": report["userAcceptance"], "blocking_findings": blocking,
            "issues": [*freshness, *issues], "states": sorted(expected_states),
            "source_paths": [item["path"] for item in report["sources"]], "boundary": BOUNDARY}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", help="Workspace-relative review JSON")
    parser.add_argument("--workspace", required=True)
    args = parser.parse_args()
    try:
        result = inspect_review(args.workspace, args.report)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return {"PASS": 0, "BLOCKED": 2, "REVIEW_REQUIRED": 3}[result["status"]]
    except (ValueError, OSError, RuntimeError, TypeError, KeyError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"): sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
