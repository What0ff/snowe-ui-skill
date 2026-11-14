#!/usr/bin/env python3
"""Scoped correction journal. Evidence integrity is not automated visual judgment."""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys

# Isolated interpreters (python -I, PYTHONSAFEPATH) drop the script directory
# from sys.path; the sibling modules below belong to this skill.
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from decision_packet import (
    locked_project_state, _atomic_write_text, _reject_reparse_chain,
    _resolve_selected_root, _shared_regular_file,
)

from checked_evidence import file_digest, object_fields, read_json, read_selected_json, text
from observation import relative, viewport_metrics
from visual_review import inspect_review, METHODS, VERDICTS


VERSION = "1.0"
COMMANDS = ("record", "list", "update", "unavailable", "verify", "supersede", "check")
STATUSES = {"requested", "implemented", "verified", "superseded"}
BASE_FIELDS = {"id", "source", "requirement", "scope", "criteria"}
# Optional record fields beside the base definition and lifecycle state.
RECORD_OPTIONAL = {"proof", "replacement", "unavailable"}
CAPTURE_FIELDS = {"origin", "tool", "url", "date", "image"}
# Signatures of the screenshot formats host browser tools write (WebP is checked separately).
IMAGE_SIGNATURES = ((b"\x89PNG\r\n\x1a\n", "PNG"), (b"\xff\xd8\xff", "JPEG"))


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,99}", value):
        raise ValueError("Invalid correction or criterion ID")
    return value


def scope(value):
    object_fields(value, {"owners", "routes", "states"}, name="scope")
    for key, items in value.items():
        if not isinstance(items, list) or len(items) != len(set(map(str, items))):
            raise ValueError("Scope values must be distinct arrays")
        for item in items: text(item, key)
    if not value["owners"] and not value["routes"]:
        raise ValueError("A scope needs an explicit owner or route")
    for owner in value["owners"]:
        path = Path(owner)
        if path.is_absolute() or path.drive or ".." in path.parts or ":" in owner or "\\" in owner:
            raise ValueError("Owners must be workspace-relative source paths using forward slashes")
    return value


def criteria(value):
    if not isinstance(value, list) or not value:
        raise ValueError("At least one criterion is required")
    ids = []
    for item in value:
        object_fields(item, {"id", "kind", "requirement"}, name="criterion")
        ids.append(identifier(item["id"]))
        if item["kind"] not in {"technical", "behavior", "visual"}: raise ValueError("Unknown criterion kind")
        text(item["requirement"], "criterion requirement")
    if len(ids) != len(set(ids)): raise ValueError("Duplicate criterion ID")


def base_record(value):
    object_fields(value, BASE_FIELDS, name="correction record")
    identifier(value["id"])
    text(value["source"], "source")
    text(value["requirement"], "requirement")
    scope(value["scope"])
    criteria(value["criteria"])


def event(entry, status, note):
    entry["status"] = status
    snapshot = {key: deepcopy(value) for key, value in entry.items() if key != "history"}
    entry["history"].append({"at": datetime.now(timezone.utc).isoformat(), "status": status, "note": text(note, "note"), "snapshot": snapshot})


def host_capture(capture):
    """Provenance of a screenshot taken with the host's own browser tooling; not an observer receipt."""
    object_fields(capture, CAPTURE_FIELDS, name="host capture")
    for field, value in capture.items(): text(value, f"host capture {field}")
    if capture["origin"] != "host": raise ValueError("Host capture origin must be host")
    if len(capture["tool"]) > 200: raise ValueError("Host capture tool must be named in at most 200 characters")
    url = capture["url"]
    if len(url) > 2000 or not (re.fullmatch(r"/\S*", url) or re.fullmatch(r"[a-zA-Z][a-zA-Z0-9+.-]*://\S+", url)):
        raise ValueError("Host capture url must be an absolute URL or a route beginning with /")
    try:
        datetime.fromisoformat(capture["date"])
    except ValueError:
        raise ValueError("Host capture date must be an ISO 8601 date or date-time") from None
    relative(capture["image"])


def review_fields(review):
    object_fields(review, {"reviewer", "finding", "viewport", "state"}, {"method", "verdict", "report", "capture"}, name="criterion review")
    for field, value in review.items():
        if field != "capture": text(value, field)
    if "method" in review and review["method"] not in METHODS: raise ValueError("Unknown visual review method")
    if "verdict" in review and review["verdict"] not in VERDICTS: raise ValueError("Unknown visual verdict")
    if "report" in review and "capture" in review:
        raise ValueError("A visual review links either a checked report or a host capture, not both")
    if ("report" in review or "capture" in review) and not {"method", "verdict"} <= review.keys():
        raise ValueError("A linked report or host capture requires its method and explicit verdict")
    if "capture" in review:
        host_capture(review["capture"])
        viewport_metrics(review["viewport"])


def closing_review(review):
    """A current closure names its method, an explicit verdict and either a checked report or a host capture."""
    return {"method", "verdict"} <= review.keys() and ("report" in review or "capture" in review)


def unavailable_reason(value):
    text(value, "unavailable evidence reason")
    if len(value) > 2000: raise ValueError("Unavailable evidence reason must be at most 2000 characters")
    return value


def validate_unavailable(record):
    """Statements that a criterion's evidence cannot be produced keep the record open; they never close it."""
    if "unavailable" not in record: return
    if record["status"] != "implemented": raise ValueError("Unavailable evidence belongs to an implemented, unverified record")
    statements = record["unavailable"]
    if not isinstance(statements, list) or not statements: raise ValueError("Unavailable evidence must be a nonempty array")
    known = {item["id"] for item in record["criteria"]}
    seen = set()
    for item in statements:
        object_fields(item, {"criterion", "reason"}, name="unavailable evidence")
        if item["criterion"] not in known or item["criterion"] in seen:
            raise ValueError("Unavailable evidence must name each recorded criterion at most once")
        seen.add(item["criterion"])
        unavailable_reason(item["reason"])


def validate_proof_shape(proof):
    """Validate receipt structure without treating it as confirmation of a definition."""
    object_fields(proof, {"sources", "artifacts", "results"}, name="proof")
    paths = set()
    for key in ("sources", "artifacts"):
        if not isinstance(proof[key], list) or not proof[key]: raise ValueError(f"Proof needs {key}")
        for item in proof[key]:
            object_fields(item, {"path", "sha256"}, name="proof binding")
            text(item["path"], "path")
            if not isinstance(item["sha256"], str) or not re.fullmatch(r"[a-f0-9]{64}", item["sha256"]): raise ValueError("Expected SHA-256")
            if item["path"] in paths: raise ValueError("Duplicate source/artifact path")
            paths.add(item["path"])
    if not isinstance(proof["results"], list) or not proof["results"]:
        raise ValueError("Proof needs criterion results")
    for result in proof["results"]:
        object_fields(result, {"criterion", "status", "artifacts"}, {"review"}, name="criterion result")
        identifier(result["criterion"])
        if result["status"] != "PASS": raise ValueError("Only passing results can be submitted for verification")
        if not isinstance(result["artifacts"], list) or not result["artifacts"]: raise ValueError("Result needs artifact paths")
        for path in result["artifacts"]: text(path, "result artifact")
        if "review" in result:
            review_fields(result["review"])


def confirmation_issues(entry):
    """History is a binding to the recorded definition, not a tamper-proof signature."""
    snapshot = entry["history"][-1].get("snapshot")
    if snapshot is None:
        return ["Legacy verification has no definition snapshot; explicit verification is required"] if entry["status"] == "verified" else []
    current = {key: value for key, value in entry.items() if key != "history"}
    return [] if current == snapshot else ["Current definition or proof differs from the last recorded snapshot"]


def validate_proof(entry, proof, *, new=False):
    validate_proof_shape(proof)
    expected = {item["id"]: item for item in entry["criteria"]}
    if not set(entry["scope"]["owners"]) <= {item["path"] for item in proof["sources"]}:
        raise ValueError("Proof must bind every declared source owner")
    if not isinstance(proof["results"], list) or len(proof["results"]) != len(expected): raise ValueError("Incomplete criterion results")
    seen = set()
    reviewed_states = set()
    artifacts = {item["path"] for item in proof["artifacts"]}
    for result in proof["results"]:
        object_fields(result, {"criterion", "status", "artifacts"}, {"review"}, name="criterion result")
        key = result["criterion"]
        if key not in expected or key in seen or result["status"] != "PASS": raise ValueError("Each criterion needs one passing result")
        seen.add(key)
        if not isinstance(result["artifacts"], list) or not result["artifacts"] or not set(result["artifacts"]) <= artifacts: raise ValueError("Results must reference bound artifacts")
        # validate_proof_shape has already checked any review's fields.
        if "capture" in result.get("review", {}):
            image = result["review"]["capture"]["image"]
            if image not in artifacts: raise ValueError("The host capture image must be a bound proof artifact")
            if image not in result["artifacts"]: raise ValueError("The host capture image must be one of its result's artifacts")
        if expected[key]["kind"] == "visual":
            review = result.get("review")
            review_fields(review)
            if new and not closing_review(review):
                raise ValueError("New visual verification requires method, explicit KEEP and either a current checked report or a bound host capture")
            if "verdict" in review and review["verdict"] != "KEEP": raise ValueError("Only KEEP can close visual proof")
            if "report" in review and review["report"] not in artifacts:
                raise ValueError("The visual report must be a bound proof artifact")
            if entry["scope"]["states"] and review["state"] not in entry["scope"]["states"]: raise ValueError("Review state is outside correction scope")
            reviewed_states.add(review["state"])
    if any(item["kind"] == "visual" for item in entry["criteria"]) and not set(entry["scope"]["states"]) <= reviewed_states:
        raise ValueError("Each required visual state needs its own reviewed criterion")


def image_format(root, path):
    """Name a bound screenshot's format from its signature; its pixels are never judged."""
    target = root / path
    _reject_reparse_chain(target, "Host capture")
    with target.open("rb") as handle: header = handle.read(12)
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP": return "WebP"
    return next((name for signature, name in IMAGE_SIGNATURES if header.startswith(signature)), None)


def proof_current(root, proof, entry=None):
    issues = []
    for item in proof["sources"] + proof["artifacts"]:
        try:
            if file_digest(root, item["path"]) != item["sha256"]: issues.append(f"Changed: {item['path']}")
        except (OSError, ValueError) as error: issues.append(f"Unavailable: {item['path']}: {error}")
    for result in proof["results"]:
        review = result.get("review", {})
        if review and not closing_review(review):
            issues.append("Historical inline visual receipt needs new explicit checked verification")
        if "capture" in review:
            image = review["capture"]["image"]
            try:
                if image_format(root, image) is None: issues.append(f"Host capture is not a PNG, JPEG or WebP image: {image}")
            except (OSError, ValueError) as error: issues.append(f"Host capture unavailable: {image}: {error}")
            continue
        if "report" not in review: continue
        try:
            checked = inspect_review(root, review["report"])
            if checked["status"] != "PASS": issues.append(f"Visual report {checked['status']}: {review['report']}")
            if checked.get("visual_verdict") != review["verdict"] or checked.get("method") != review["method"]:
                issues.append("Visual receipt disagrees with its linked report")
            if review["state"] not in checked.get("states", []): issues.append("Visual report does not cover the receipt state")
            if not any(row["state"] == review["state"] and row["viewport"] == review["viewport"] for row in checked.get("combinations", [])):
                issues.append("Visual report does not cover the receipt viewport/state")
            if entry and not set(entry["scope"]["owners"]) <= set(checked.get("source_paths", [])):
                issues.append("Visual report does not bind every correction owner")
        except (OSError, ValueError, TypeError, KeyError) as error:
            issues.append(f"Visual report unavailable: {error}")
    return issues


def load_journal(path, identity):
    _reject_reparse_chain(path, "Correction journal")
    if not path.exists(): return {"schema_version": VERSION, "project_identity": identity, "records": []}
    if _shared_regular_file(path): raise ValueError("Correction journal must not be a shared hardlink")
    journal = read_json(path)
    object_fields(journal, {"schema_version", "project_identity", "records"}, name="correction journal")
    if journal["schema_version"] != VERSION or journal["project_identity"] != identity: raise ValueError("Journal schema/project mismatch")
    if not isinstance(journal["records"], list): raise ValueError("Records must be an array")
    ids = set()
    for entry in journal["records"]:
        object_fields(entry, BASE_FIELDS | {"status", "history"}, RECORD_OPTIONAL, name="journal record")
        base_record({key: entry[key] for key in BASE_FIELDS})
        if entry["id"] in ids: raise ValueError("Duplicate correction ID")
        ids.add(entry["id"])
        if entry["status"] not in STATUSES or not isinstance(entry["history"], list) or not entry["history"]: raise ValueError("Invalid record state/history")
        for item in entry["history"]:
            object_fields(item, {"at", "status", "note"}, {"snapshot"}, name="history event")
            text(item["at"], "timestamp"); text(item["note"], "note")
            if item["status"] not in STATUSES: raise ValueError("Invalid history status")
            if "snapshot" in item:
                snapshot = item["snapshot"]
                object_fields(snapshot, BASE_FIELDS | {"status"}, RECORD_OPTIONAL, name="history snapshot")
                base_record({key: snapshot[key] for key in BASE_FIELDS})
                if snapshot["id"] != entry["id"] or snapshot["status"] != item["status"]: raise ValueError("History snapshot mismatch")
                if snapshot["status"] == "verified": validate_proof(snapshot, snapshot.get("proof"))
                validate_unavailable(snapshot)
        if entry["history"][-1]["status"] != entry["status"]: raise ValueError("History/state mismatch")
        validate_unavailable(entry)
        if entry["status"] == "verified":
            validate_proof_shape(entry.get("proof"))
            if not confirmation_issues(entry): validate_proof(entry, entry["proof"])
        if entry["status"] == "superseded": identifier(entry.get("replacement"))
    by_id = {entry["id"]: entry for entry in journal["records"]}
    for entry in journal["records"]:
        seen = set()
        while entry["status"] == "superseded":
            if entry["id"] in seen or entry["replacement"] not in by_id: raise ValueError("Invalid supersession chain")
            seen.add(entry["id"]); entry = by_id[entry["replacement"]]
    return journal


def _owner_set(owners):
    # "./src/a.css" and "src/a.css" name the same workspace file.
    return {PurePosixPath(owner).as_posix() for owner in owners}


def applies(entry, active):
    if active is None: return True
    own = entry["scope"]
    overlap = bool(_owner_set(own["owners"]) & _owner_set(active["owners"])) or bool(set(own["routes"]) & set(active["routes"]))
    return overlap and (not own["states"] or not active["states"] or bool(set(own["states"]) & set(active["states"])))


def visual_closures(entry):
    """How each visual criterion of a current verified record was closed, so delivery can name the review method."""
    kinds = {item["id"]: item["kind"] for item in entry["criteria"]}
    closures = []
    for result in entry["proof"]["results"]:
        review = result.get("review")
        if kinds.get(result["criterion"]) != "visual" or not review: continue
        closure = {"id": entry["id"], "criterion": result["criterion"], "method": review.get("method"),
                   "evidence": "host-capture" if "capture" in review else "checked-report",
                   "state": review["state"], "viewport": review["viewport"]}
        if "capture" in review: closure.update({key: review["capture"][key] for key in ("tool", "url", "date", "image")})
        else: closure["report"] = review.get("report")
        closures.append(closure)
    return closures


def known_journal_identities(root):
    """Project identities that already have a correction journal in this workspace."""
    names = []
    base = root / "design-intelligence"
    if not base.is_dir(): return names
    for journal in sorted(base.glob("*/CORRECTIONS.json")):
        try:
            identity = read_json(journal).get("project_identity")
        except (ValueError, OSError, AttributeError):
            continue
        if isinstance(identity, str) and identity.strip(): names.append(identity)
    return names


def execute(command, *, workspace, project, payload=None):
    root = _resolve_selected_root(workspace, "Workspace")
    if not root.is_dir(): raise ValueError(f"Workspace is not an existing directory: {root}")
    identity = text(project, "project").strip()
    data = deepcopy(payload)
    readonly = command in {"list", "check"}
    if command not in COMMANDS: raise ValueError("Unknown command")
    if command == "record": base_record(data)
    with locked_project_state(root, identity, create=command == "record") as directory:
        path = directory / "CORRECTIONS.json" if directory else None
        journal = load_journal(path, identity) if path else {"schema_version": VERSION, "project_identity": identity, "records": []}
        entries = journal["records"]
        if readonly:
            if data is not None: scope(data)
            present = bool(path and path.exists())
            others = [] if present else [name for name in known_journal_identities(root) if name != identity]
            if others:
                # A mistyped identity must not look like a project without corrections.
                if command == "list": return {"project_identity": identity, "journal": "absent", "known_projects": others, "records": [], "review_required": []}
                return {"status": "NO_JOURNAL", "project_identity": identity, "journal": "absent", "known_projects": others,
                    "applicable": [], "blocked": [], "stale": [], "evidence_unavailable": [], "visual_closures": [],
                    "boundary": "No journal for this identity; check --project against known_projects"}
            integrity = {entry["id"]: confirmation_issues(entry) for entry in entries}
            def applicable(entry):
                if applies(entry, data): return True
                if integrity[entry["id"]]:
                    # A direct edit must not move an obligation out of its recorded scope.
                    prior = [item["snapshot"] for item in entry["history"] if "snapshot" in item]
                    confirmed = next((snapshot for snapshot in reversed(prior) if snapshot["status"] == "verified"), None)
                    return any(applies(snapshot, data) for snapshot in prior[-1:]) or (
                        confirmed is not None and applies(confirmed, data)
                    )
                return False
            selected = [entry for entry in entries if applicable(entry)]
            # Supersession cannot hide an original obligation if its replacement scope changes.
            by_id = {entry["id"]: entry for entry in entries}
            included = {entry["id"] for entry in selected}
            for entry in selected:
                if entry["status"] == "superseded" and entry["replacement"] not in included:
                    selected.append(by_id[entry["replacement"]])
                    included.add(entry["replacement"])
            if command == "list": return {"project_identity": identity, "journal": "present" if present else "absent", "records": selected,
                "review_required": [{"id": e["id"], "issues": integrity[e["id"]]} for e in selected if integrity[e["id"]]]}
            blocked, stale, unavailable, closures = [], [], [], []
            for entry in selected:
                if entry["status"] in {"requested", "implemented"}: blocked.append(entry["id"])
                kinds = {item["id"]: item["kind"] for item in entry["criteria"]}
                for statement in entry.get("unavailable", []):
                    unavailable.append({"id": entry["id"], "criterion": statement["criterion"],
                                        "kind": kinds[statement["criterion"]], "reason": statement["reason"]})
                issues = list(integrity[entry["id"]])
                if entry["status"] == "verified": issues.extend(proof_current(root, entry["proof"], entry))
                if issues: stale.append({"id": entry["id"], "issues": issues})
                elif entry["status"] == "verified": closures.extend(visual_closures(entry))
            # Unavailable evidence explains a BLOCKED record; it never turns the result into PASS.
            return {"status": "BLOCKED" if blocked else "REVIEW_REQUIRED" if stale else "PASS", "project_identity": identity,
                    "journal": "present" if present else "absent", "applicable": [e["id"] for e in selected], "blocked": blocked,
                    "stale": stale, "evidence_unavailable": unavailable, "visual_closures": closures,
                    "boundary": "Recorded proof integrity; not independent visual certification"}
        if command == "record":
            base_record(data)
            existing = next((e for e in entries if e["id"] == data["id"]), None)
            if existing:
                if any(existing[k] != data[k] for k in BASE_FIELDS): raise ValueError("ID already records a different correction")
                return {"record": existing, "changed": False}
            entry = {**data, "history": []}
            event(entry, "requested", "Correction recorded")
            entries.append(entry)
        else:
            object_fields(data, {"id"}, {"status", "note", "requirement", "scope", "criteria", "proof", "replacement", "criterion", "reason"}, name="transition input")
            entry = next((e for e in entries if e["id"] == data["id"]), None)
            if entry is None: raise ValueError("Unknown correction ID")
            if entry["status"] == "superseded": raise ValueError("A superseded record is immutable")
            if command == "update":
                object_fields(data, {"id", "note"}, {"status", "requirement", "scope", "criteria"}, name="update input")
                changed = any(k in data and data[k] != entry[k] for k in ("requirement", "scope", "criteria"))
                for k in ("requirement", "scope", "criteria"):
                    if k in data: entry[k] = data[k]
                base_record({k: entry[k] for k in BASE_FIELDS})
                target = "requested" if changed else data.get("status", "implemented")
                if target not in {"requested", "implemented"}: raise ValueError("Use verify/supersede for final transitions")
                # A new implementation or definition outdates earlier proof and unavailability statements.
                entry.pop("proof", None)
                entry.pop("unavailable", None)
                event(entry, target, data["note"])
            elif command == "unavailable":
                object_fields(data, {"id", "criterion", "reason"}, name="unavailable input")
                if entry["status"] != "implemented":
                    raise ValueError("Record unavailable evidence for an implemented record; implement it first, and update a verified record to implemented")
                order = [item["id"] for item in entry["criteria"]]
                if data["criterion"] not in order: raise ValueError("Unknown criterion for this correction")
                statement = {"criterion": data["criterion"], "reason": unavailable_reason(data["reason"])}
                statements = entry.get("unavailable", [])
                if statement in statements: return {"record": entry, "changed": False}
                statements = [item for item in statements if item["criterion"] != statement["criterion"]] + [statement]
                entry["unavailable"] = sorted(statements, key=lambda item: order.index(item["criterion"]))
                event(entry, "implemented", f"Evidence unavailable for criterion {statement['criterion']}: {statement['reason']}")
            elif command == "verify":
                object_fields(data, {"id", "proof"}, name="verify input")
                if entry["status"] not in {"implemented", "verified"}: raise ValueError("Implement before verification")
                validate_proof(entry, data["proof"], new=True)
                issues = proof_current(root, data["proof"], entry)
                if issues: raise ValueError("; ".join(issues))
                entry["proof"] = data["proof"]
                entry.pop("unavailable", None)
                event(entry, "verified", "Bound criterion results and current evidence verified")
            else:
                object_fields(data, {"id", "replacement", "note"}, name="supersede input")
                replacement = next((e for e in entries if e["id"] == data["replacement"]), None)
                if replacement is None or replacement is entry or replacement["status"] == "superseded": raise ValueError("Replacement must be a different active correction")
                if any(not set(entry["scope"][k]) <= set(replacement["scope"][k]) for k in ("owners", "routes")) or (not entry["scope"]["states"] and replacement["scope"]["states"]) or (entry["scope"]["states"] and replacement["scope"]["states"] and not set(entry["scope"]["states"]) <= set(replacement["scope"]["states"])):
                    raise ValueError("Replacement must cover the original scope")
                entry["replacement"] = replacement["id"]
                # Unavailability statements stay in history; the replacement carries the obligation.
                entry.pop("unavailable", None)
                event(entry, "superseded", data["note"])
        _reject_reparse_chain(path, "Correction journal")
        if path.exists() and _shared_regular_file(path): raise ValueError("Correction journal must not be a shared hardlink")
        encoded = json.dumps(journal, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if len(encoded.encode("utf-8")) > 1_000_000: raise ValueError("Correction journal exceeds 1 MB")
        _atomic_write_text(path, encoded)
        return {"record": entry, "changed": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=COMMANDS)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--input", help="JSON record, transition, proof, unavailable-evidence statement, or active scope")
    args = parser.parse_args()
    try:
        if args.command not in {"list", "check"} and not args.input: raise ValueError("This command requires --input")
        result = execute(args.command, workspace=args.workspace, project=args.project, payload=read_selected_json(args.input) if args.input else None)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return {"PASS": 0, "BLOCKED": 2, "REVIEW_REQUIRED": 3, "NO_JOURNAL": 4}.get(result.get("status"), 0)
    except (ValueError, OSError, RuntimeError, TypeError, KeyError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"): sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
