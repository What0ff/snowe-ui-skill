#!/usr/bin/env python3
"""Scoped correction journal. Evidence integrity is not automated visual judgment."""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

from decision_packet import (
    locked_project_state, _atomic_write_text, _reject_reparse_chain,
    _normalize_lexical_aliases, _shared_regular_file,
)

VERSION = "1.0"
STATUSES = {"requested", "implemented", "verified", "superseded"}
BASE_FIELDS = {"id", "source", "requirement", "scope", "criteria"}


def text(value, field):
    if not isinstance(value, str) or not value.strip() or len(value) > 8000 or not value.isprintable():
        raise ValueError(f"{field} must be nonempty printable text")
    return value


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,99}", value):
        raise ValueError("Invalid correction or criterion ID")
    return value


def object_fields(value, required, optional=()):
    if not isinstance(value, dict) or not set(required) <= value.keys() or set(value) - set(required) - set(optional):
        raise ValueError(f"Expected fields {sorted(required)} with optional {sorted(optional)}")


def read_json(path):
    path = Path(path)
    _reject_reparse_chain(path, "JSON input")
    if not path.is_file() or path.stat().st_size > 1_000_000:
        raise ValueError("JSON input must be a regular file of at most 1 MB")
    try:
        value = json.loads(path.read_text(encoding="utf-8"), parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))
    except (RecursionError, UnicodeError) as error:
        raise ValueError("Invalid or excessive JSON") from error
    def bounded(node, depth=0):
        if depth > 32:
            raise ValueError("JSON nesting exceeds 32")
        if isinstance(node, dict):
            for child in node.values(): bounded(child, depth + 1)
        elif isinstance(node, list):
            for child in node: bounded(child, depth + 1)
    bounded(value)
    return value


def scope(value):
    object_fields(value, {"owners", "routes", "states"})
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
        object_fields(item, {"id", "kind", "requirement"})
        ids.append(identifier(item["id"]))
        if item["kind"] not in {"technical", "behavior", "visual"}: raise ValueError("Unknown criterion kind")
        text(item["requirement"], "criterion requirement")
    if len(ids) != len(set(ids)): raise ValueError("Duplicate criterion ID")


def base_record(value):
    object_fields(value, BASE_FIELDS)
    identifier(value["id"])
    text(value["source"], "source")
    text(value["requirement"], "requirement")
    scope(value["scope"])
    criteria(value["criteria"])


def event(entry, status, note):
    entry["status"] = status
    snapshot = {key: deepcopy(value) for key, value in entry.items() if key != "history"}
    entry["history"].append({"at": datetime.now(timezone.utc).isoformat(), "status": status, "note": text(note, "note"), "snapshot": snapshot})


def file_digest(root, relative):
    text(relative, "evidence path")
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or path.drive or ":" in relative:
        raise ValueError("Evidence paths must remain relative to the workspace")
    path = root / path
    _reject_reparse_chain(path, "Evidence")
    before = path.stat()
    if not stat.S_ISREG(before.st_mode): raise ValueError("Evidence must be a regular file")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        opened = os.fstat(handle.fileno())
        if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino): raise ValueError("Evidence changed before reading")
        for chunk in iter(lambda: handle.read(65536), b""): digest.update(chunk)
        after = os.fstat(handle.fileno())
    _reject_reparse_chain(path, "Evidence")
    current = path.stat()
    if (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) != (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns) or opened.st_mtime_ns != after.st_mtime_ns:
        raise ValueError("Evidence changed during reading")
    return digest.hexdigest()


def validate_proof_shape(proof):
    """Validate receipt structure without treating it as confirmation of a definition."""
    object_fields(proof, {"sources", "artifacts", "results"})
    paths = set()
    for key in ("sources", "artifacts"):
        if not isinstance(proof[key], list) or not proof[key]: raise ValueError(f"Proof needs {key}")
        for item in proof[key]:
            object_fields(item, {"path", "sha256"})
            text(item["path"], "path")
            if not isinstance(item["sha256"], str) or not re.fullmatch(r"[a-f0-9]{64}", item["sha256"]): raise ValueError("Expected SHA-256")
            if item["path"] in paths: raise ValueError("Duplicate source/artifact path")
            paths.add(item["path"])
    if not isinstance(proof["results"], list) or not proof["results"]:
        raise ValueError("Proof needs criterion results")
    for result in proof["results"]:
        object_fields(result, {"criterion", "status", "artifacts"}, {"review"})
        identifier(result["criterion"])
        if result["status"] != "PASS": raise ValueError("Only passing results can be submitted for verification")
        if not isinstance(result["artifacts"], list) or not result["artifacts"]: raise ValueError("Result needs artifact paths")
        for path in result["artifacts"]: text(path, "result artifact")
        if "review" in result:
            object_fields(result["review"], {"reviewer", "finding", "viewport", "state"})
            for field, value in result["review"].items(): text(value, field)


def confirmation_issues(entry):
    """History is a binding to the recorded definition, not a tamper-proof signature."""
    snapshot = entry["history"][-1].get("snapshot")
    if snapshot is None:
        return ["Legacy verification has no definition snapshot; explicit verification is required"] if entry["status"] == "verified" else []
    current = {key: value for key, value in entry.items() if key != "history"}
    return [] if current == snapshot else ["Current definition or proof differs from the last recorded snapshot"]


def validate_proof(entry, proof):
    validate_proof_shape(proof)
    expected = {item["id"]: item for item in entry["criteria"]}
    if not set(entry["scope"]["owners"]) <= {item["path"] for item in proof["sources"]}:
        raise ValueError("Proof must bind every declared source owner")
    if not isinstance(proof["results"], list) or len(proof["results"]) != len(expected): raise ValueError("Incomplete criterion results")
    seen = set()
    reviewed_states = set()
    artifacts = {item["path"] for item in proof["artifacts"]}
    for result in proof["results"]:
        object_fields(result, {"criterion", "status", "artifacts"}, {"review"})
        key = result["criterion"]
        if key not in expected or key in seen or result["status"] != "PASS": raise ValueError("Each criterion needs one passing result")
        seen.add(key)
        if not isinstance(result["artifacts"], list) or not result["artifacts"] or not set(result["artifacts"]) <= artifacts: raise ValueError("Results must reference bound artifacts")
        if expected[key]["kind"] == "visual":
            review = result.get("review")
            object_fields(review, {"reviewer", "finding", "viewport", "state"})
            for field, value in review.items(): text(value, field)
            if entry["scope"]["states"] and review["state"] not in entry["scope"]["states"]: raise ValueError("Review state is outside correction scope")
            reviewed_states.add(review["state"])
    if any(item["kind"] == "visual" for item in entry["criteria"]) and not set(entry["scope"]["states"]) <= reviewed_states:
        raise ValueError("Each required visual state needs its own reviewed criterion")


def proof_current(root, proof):
    issues = []
    for item in proof["sources"] + proof["artifacts"]:
        try:
            if file_digest(root, item["path"]) != item["sha256"]: issues.append(f"Changed: {item['path']}")
        except (OSError, ValueError) as error: issues.append(f"Unavailable: {item['path']}: {error}")
    return issues


def load_journal(path, identity):
    _reject_reparse_chain(path, "Correction journal")
    if not path.exists(): return {"schema_version": VERSION, "project_identity": identity, "records": []}
    if _shared_regular_file(path): raise ValueError("Correction journal must not be a shared hardlink")
    journal = read_json(path)
    object_fields(journal, {"schema_version", "project_identity", "records"})
    if journal["schema_version"] != VERSION or journal["project_identity"] != identity: raise ValueError("Journal schema/project mismatch")
    if not isinstance(journal["records"], list): raise ValueError("Records must be an array")
    ids = set()
    for entry in journal["records"]:
        object_fields(entry, BASE_FIELDS | {"status", "history"}, {"proof", "replacement"})
        base_record({key: entry[key] for key in BASE_FIELDS})
        if entry["id"] in ids: raise ValueError("Duplicate correction ID")
        ids.add(entry["id"])
        if entry["status"] not in STATUSES or not isinstance(entry["history"], list) or not entry["history"]: raise ValueError("Invalid record state/history")
        for item in entry["history"]:
            object_fields(item, {"at", "status", "note"}, {"snapshot"})
            text(item["at"], "timestamp"); text(item["note"], "note")
            if item["status"] not in STATUSES: raise ValueError("Invalid history status")
            if "snapshot" in item:
                snapshot = item["snapshot"]
                object_fields(snapshot, BASE_FIELDS | {"status"}, {"proof", "replacement"})
                base_record({key: snapshot[key] for key in BASE_FIELDS})
                if snapshot["id"] != entry["id"] or snapshot["status"] != item["status"]: raise ValueError("History snapshot mismatch")
                if snapshot["status"] == "verified": validate_proof(snapshot, snapshot.get("proof"))
        if entry["history"][-1]["status"] != entry["status"]: raise ValueError("History/state mismatch")
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


def applies(entry, active):
    if active is None: return True
    own = entry["scope"]
    overlap = any(set(own[key]) & set(active[key]) for key in ("owners", "routes"))
    return overlap and (not own["states"] or not active["states"] or bool(set(own["states"]) & set(active["states"])))


def execute(command, *, workspace, project, payload=None):
    root = _normalize_lexical_aliases(Path(os.path.abspath(workspace)), "Workspace")
    _reject_reparse_chain(root, "Workspace")
    identity = text(project, "project").strip()
    data = deepcopy(payload)
    readonly = command in {"list", "check"}
    if command not in {"record", "list", "update", "verify", "supersede", "check"}: raise ValueError("Unknown command")
    if command == "record": base_record(data)
    with locked_project_state(root, identity, create=command == "record") as directory:
        path = directory / "CORRECTIONS.json" if directory else None
        journal = load_journal(path, identity) if path else {"schema_version": VERSION, "project_identity": identity, "records": []}
        entries = journal["records"]
        if readonly:
            if data is not None: scope(data)
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
            if command == "list": return {"project_identity": identity, "records": selected,
                "review_required": [{"id": e["id"], "issues": integrity[e["id"]]} for e in selected if integrity[e["id"]]]}
            blocked, stale = [], []
            for entry in selected:
                if entry["status"] in {"requested", "implemented"}: blocked.append(entry["id"])
                issues = list(integrity[entry["id"]])
                if entry["status"] == "verified": issues.extend(proof_current(root, entry["proof"]))
                if issues: stale.append({"id": entry["id"], "issues": issues})
            return {"status": "BLOCKED" if blocked else "REVIEW_REQUIRED" if stale else "PASS", "project_identity": identity, "applicable": [e["id"] for e in selected], "blocked": blocked, "stale": stale, "boundary": "Recorded proof integrity; not independent visual certification"}
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
            object_fields(data, {"id"}, {"status", "note", "requirement", "scope", "criteria", "proof", "replacement"})
            entry = next((e for e in entries if e["id"] == data["id"]), None)
            if entry is None: raise ValueError("Unknown correction ID")
            if entry["status"] == "superseded": raise ValueError("A superseded record is immutable")
            if command == "update":
                object_fields(data, {"id", "note"}, {"status", "requirement", "scope", "criteria"})
                changed = any(k in data and data[k] != entry[k] for k in ("requirement", "scope", "criteria"))
                for k in ("requirement", "scope", "criteria"):
                    if k in data: entry[k] = data[k]
                base_record({k: entry[k] for k in BASE_FIELDS})
                target = "requested" if changed else data.get("status", "implemented")
                if target not in {"requested", "implemented"}: raise ValueError("Use verify/supersede for final transitions")
                entry.pop("proof", None)
                event(entry, target, data["note"])
            elif command == "verify":
                object_fields(data, {"id", "proof"})
                if entry["status"] not in {"implemented", "verified"}: raise ValueError("Implement before verification")
                validate_proof(entry, data["proof"])
                issues = proof_current(root, data["proof"])
                if issues: raise ValueError("; ".join(issues))
                entry["proof"] = data["proof"]
                event(entry, "verified", "Bound criterion results and current evidence verified")
            else:
                object_fields(data, {"id", "replacement", "note"})
                replacement = next((e for e in entries if e["id"] == data["replacement"]), None)
                if replacement is None or replacement is entry or replacement["status"] == "superseded": raise ValueError("Replacement must be a different active correction")
                if any(not set(entry["scope"][k]) <= set(replacement["scope"][k]) for k in ("owners", "routes")) or (not entry["scope"]["states"] and replacement["scope"]["states"]) or (entry["scope"]["states"] and replacement["scope"]["states"] and not set(entry["scope"]["states"]) <= set(replacement["scope"]["states"])):
                    raise ValueError("Replacement must cover the original scope")
                entry["replacement"] = replacement["id"]
                event(entry, "superseded", data["note"])
        _reject_reparse_chain(path, "Correction journal")
        if path.exists() and _shared_regular_file(path): raise ValueError("Correction journal must not be a shared hardlink")
        encoded = json.dumps(journal, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if len(encoded.encode("utf-8")) > 1_000_000: raise ValueError("Correction journal exceeds 1 MB")
        _atomic_write_text(path, encoded)
        return {"record": entry, "changed": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["record", "list", "update", "verify", "supersede", "check"])
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--input", help="JSON record, transition, proof, or active scope")
    args = parser.parse_args()
    try:
        if args.command not in {"list", "check"} and not args.input: raise ValueError("This command requires --input")
        result = execute(args.command, workspace=args.workspace, project=args.project, payload=read_json(args.input) if args.input else None)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return {"PASS": 0, "BLOCKED": 2, "REVIEW_REQUIRED": 3}.get(result.get("status"), 0)
    except (ValueError, OSError, RuntimeError, TypeError, KeyError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"): sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
