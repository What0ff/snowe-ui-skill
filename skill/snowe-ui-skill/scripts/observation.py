"""Portable observation contracts; deterministic integrity, never aesthetic grading."""
from __future__ import annotations

import hashlib
import math
from pathlib import Path
import re
import struct

from checked_evidence import file_digest, object_fields, read_json, text
from decision_packet import _reject_reparse_chain

DIMENSIONS = ("state", "viewport", "theme", "input", "motion", "context")


def pixel_round(value):
    """Positive device coordinates use the browser's half-up rounding."""
    return math.floor(value + .5)


def relative(value):
    text(value, "path")
    p = Path(value)
    if p.is_absolute() or p.drive or ".." in p.parts or ":" in value or "\\" in value or value in {".", ""}:
        raise ValueError("Use a workspace-relative path with forward slashes")
    return value


def bound(value):
    object_fields(value, {"path", "sha256"})
    relative(value["path"])
    if not isinstance(value["sha256"], str) or not re.fullmatch("[a-f0-9]{64}", value["sha256"]):
        raise ValueError("Expected SHA-256 binding")
    return value


def current(root, value, *, max_bytes=1_000_000):
    bound(value)
    if file_digest(root, value["path"]) != value["sha256"]:
        raise ValueError(f"Changed: {value['path']}")
    return read_json(root / value["path"], max_bytes=max_bytes)


def combination(case):
    for field in DIMENSIONS: text(case.get(field), field)
    if not re.fullmatch(r"[1-9]\d{1,4}x[1-9]\d{1,4}@[1-4](?:\.\d{1,2})?", case["viewport"]):
        raise ValueError("Viewport must identify width x height @ pixel ratio")
    if case["theme"] not in {"light", "dark"} or case["input"] not in {"pointer", "touch", "keyboard"} or case["motion"] not in {"normal", "reduced"}:
        raise ValueError("Unsupported browser emulation")
    return tuple(case[field] for field in DIMENSIONS)


def inventory(root, roots):
    """Complete bounded source scopes: include assets/imports; exclude nothing implicitly."""
    if not isinstance(roots, list) or not roots: raise ValueError("Declare affected source roots")
    paths = set()
    for name in roots:
        relative(name)
        target = root / name
        _reject_reparse_chain(target, "Source root")
        if not target.exists(): raise ValueError(f"Unavailable source root: {name}")
        pending = [target]
        visited = 0
        while pending:
            path = pending.pop()
            visited += 1
            if visited > 10000: raise ValueError("Source scope exceeds 10000 entries; narrow the roots")
            _reject_reparse_chain(path, "Source inventory")
            if path.is_dir(): pending.extend(path.iterdir())
            elif path.is_file(): paths.add(path.relative_to(root).as_posix())
            else: raise ValueError("Source scopes need regular files/directories")
    return [{"path": name, "sha256": file_digest(root, name)} for name in sorted(paths)]


def validate_plan(plan):
    object_fields(plan, {"schema", "scope", "sourceRoots", "cases"})
    if plan["schema"] != "1.0": raise ValueError("Unsupported observation plan")
    text(plan["scope"], "scope")
    if not isinstance(plan["sourceRoots"], list) or not plan["sourceRoots"]: raise ValueError("Missing source roots")
    for name in plan["sourceRoots"]: relative(name)
    if not isinstance(plan["cases"], list) or not plan["cases"]: raise ValueError("Missing observation cases")
    ids, combinations = set(), set()
    for case in plan["cases"]:
        object_fields(case, {"id", *DIMENSIONS, "route", "steps", "probes", "details", "expect"}, {"sequence"})
        text(case["id"], "case ID")
        key = combination(case)
        if case["id"] in ids or key in combinations: raise ValueError("Duplicate observation ID or combination")
        ids.add(case["id"]); combinations.add(key)
        if not isinstance(case["expect"], list) or not case["expect"]: raise ValueError("Plan observable state postconditions")
        for condition in case["expect"]:
            object_fields(condition, {"selector", "property"}, {"equals", "includes"})
            text(condition["selector"], "state selector"); text(condition["property"], "state property")
            if ("equals" in condition) == ("includes" in condition): raise ValueError("State condition needs one expected result")
            if "includes" in condition: text(condition["includes"], "expected state text")
        if not isinstance(case["route"], str) or not case["route"].startswith("/") or case["route"].startswith("//"):
            raise ValueError("Observation route must be local")
        if not isinstance(case["steps"], list) or not isinstance(case["probes"], list) or not case["probes"]:
            raise ValueError("Cases need steps and affected-layer probes")
        for step in case["steps"]:
            object_fields(step, {"action"}, {"selector", "value", "key"})
            if step["action"] not in {"click", "fill", "key", "wait", "scroll", "script"}: raise ValueError("Unknown replay action")
            for field, value in step.items(): text(value, field)
        seen = set()
        for probe in case["probes"]:
            object_fields(probe, {"selector", "pseudo"})
            text(probe["selector"], "probe selector")
            if probe["pseudo"] not in {"", "::before", "::after", "::backdrop"}: raise ValueError("Unknown pseudo layer")
            key = (probe["selector"], probe["pseudo"])
            if key in seen: raise ValueError("Duplicate probe")
            seen.add(key)
        if not isinstance(case["details"], list) or not case["details"]: raise ValueError("Plan native-size detail evidence for the affected owner")
        detail_ids = set()
        for detail in case["details"]:
            object_fields(detail, {"id", "selector", "padding", "scale"}, {"space"})
            text(detail["id"], "detail ID")
            if detail["id"] in detail_ids or (detail["selector"], "") not in seen: raise ValueError("Detail must name a unique ID and measured owner")
            detail_ids.add(detail["id"])
            if type(detail["padding"]) is not int or not 0 <= detail["padding"] <= 100 or detail["scale"] not in {1, 2}: raise ValueError("Invalid detail scale/padding")
            if detail.get("space","document") not in {"document","viewport"}: raise ValueError("Unknown detail coordinate space")
        if "sequence" in case:
            sequence = case["sequence"]
            object_fields(sequence, {"fps", "durationMs", "start", "events"})
            if type(sequence["fps"]) is not int or not 1 <= sequence["fps"] <= 30 or type(sequence["durationMs"]) is not int or not 1 <= sequence["durationMs"] <= 10000:
                raise ValueError("Sequence needs bounded fps/duration")
            if not isinstance(sequence["start"], list) or not isinstance(sequence["events"], list): raise ValueError("Sequence needs replay steps/events")
            last = -1
            for event in sequence["events"]:
                object_fields(event, {"atMs", "steps"})
                if type(event["atMs"]) is not int or not last < event["atMs"] < sequence["durationMs"] or not isinstance(event["steps"], list): raise ValueError("Invalid sequence event")
                last = event["atMs"]
            # Reuse the same strict replay shape for temporal actions.
            replay_case = {**case, "steps": sequence["start"] + [step for event in sequence["events"] for step in event["steps"]]}
            replay_case.pop("sequence")
            validate_plan({**plan, "cases": [replay_case]})
    return plan


def inspect_capture(root, receipt_binding, plan_binding):
    """Receipt is an audit trail, not a trusted attestation against its author."""
    # Measured families and temporal/detail matrices legitimately exceed a tiny manifest.
    receipt = current(root, receipt_binding, max_bytes=8_000_000)
    plan = validate_plan(current(root, plan_binding))
    object_fields(receipt, {"schema", "plan", "observer", "browser", "sources", "observations"})
    if receipt["schema"] != "1.0" or receipt["plan"] != plan_binding: raise ValueError("Capture plan binding mismatch")
    observer = Path(__file__).with_name("observe.mjs")
    if receipt["observer"] != hashlib.sha256(observer.read_bytes()).hexdigest(): raise ValueError("Observer revision changed")
    object_fields(receipt["browser"], {"product", "userAgent", "jsVersion", "protocolVersion"})
    for field, value in receipt["browser"].items(): text(value, field)
    expected_sources = inventory(root, plan["sourceRoots"])
    if receipt["sources"] != expected_sources: raise ValueError("Source inventory changed or is incomplete")
    sources = {item["path"]: item["sha256"] for item in expected_sources}
    if not isinstance(receipt["observations"], list): raise ValueError("Missing observations")
    cases = {item["id"]: item for item in plan["cases"]}
    observed = {}
    for row in receipt["observations"]:
        object_fields(row, {"id", *DIMENSIONS, "render", "viewportRender", "actual", "image", "resources", "probes", "diagnostics", "details", "stateProof"}, {"sequence"})
        if row["id"] not in cases or row["id"] in observed: raise ValueError("Unplanned or duplicate capture")
        case = cases[row["id"]]
        if combination(row) != combination(case): raise ValueError("Capture does not match planned combination")
        if not isinstance(row["stateProof"], list) or len(row["stateProof"]) != len(case["expect"]): raise ValueError("State postconditions are unobserved")
        for expected, proof in zip(case["expect"], row["stateProof"]):
            if not isinstance(proof, dict) or {k:v for k,v in proof.items() if k != "actual"} != expected or "actual" not in proof: raise ValueError("State proof differs from independent plan")
            if "equals" in expected and proof["actual"] != expected["equals"]: raise ValueError("Claimed application state was not reproduced")
            if "includes" in expected and (not isinstance(proof["actual"], str) or expected["includes"] not in proof["actual"]): raise ValueError("Required state result is missing")
        actual = row["actual"]
        object_fields(actual, {"width", "height", "dpr", "theme", "touch", "motion", "route", "fonts", "settled", "scrollX", "scrollY"})
        if any(type(actual[k]) is not int or not 0<actual[k]<=99999 for k in ("width","height")) or type(actual["dpr"]) not in {int,float} or not math.isfinite(actual["dpr"]) or not 1<=actual["dpr"]<=4:
            raise ValueError("Browser dimensions/DPR must be bounded real numbers, not flags")
        if type(actual["touch"]) is not bool or any(type(actual[k]) not in {int,float} or not math.isfinite(actual[k]) for k in ("scrollX","scrollY")):
            raise ValueError("Invalid browser input or scroll metadata")
        viewport = f"{actual['width']}x{actual['height']}@{actual['dpr']:g}"
        if viewport != row["viewport"] or actual["theme"] != row["theme"] or actual["touch"] != (row["input"] == "touch") or actual["motion"] != row["motion"] or actual["route"] != case["route"]:
            raise ValueError("Actual browser environment disagrees with capture metadata")
        if actual["fonts"] != "loaded" or actual["settled"] is not True: raise ValueError("Unsettled fonts/layout capture")
        bound(row["viewportRender"])
        if row["viewportRender"]["path"] in sources or file_digest(root,row["viewportRender"]["path"]) != row["viewportRender"]["sha256"]: raise ValueError("Viewport render changed or aliases source")
        with (root / row["viewportRender"]["path"]).open("rb") as handle: view_header = handle.read(24)
        if len(view_header)<24 or view_header[:8] != b"\x89PNG\r\n\x1a\n": raise ValueError("Expected native viewport PNG")
        view_width,view_height=struct.unpack(">II",view_header[16:24])
        if abs(view_width-actual["width"]*actual["dpr"])>1 or abs(view_height-actual["height"]*actual["dpr"])>1:
            raise ValueError("Native viewport image does not match browser environment")
        bound(row["render"])
        if row["render"]["path"] in sources: raise ValueError("Outputs must be outside source roots")
        if file_digest(root, row["render"]["path"]) != row["render"]["sha256"]: raise ValueError("Render bytes changed")
        with (root / row["render"]["path"]).open("rb") as handle: header = handle.read(24)
        if header[:8] != b"\x89PNG\r\n\x1a\n" or len(header) < 24: raise ValueError("Expected lossless PNG capture")
        width, height = struct.unpack(">II", header[16:24])
        if row["image"] != {"width": width, "height": height} or width < actual["width"] * actual["dpr"]-1 or height < actual["height"] * actual["dpr"]-1:
            raise ValueError("PNG geometry disagrees with browser capture")
        if row["diagnostics"] != []: raise ValueError("Capture has browser/network diagnostics")
        if not isinstance(row["resources"], list) or not row["resources"]: raise ValueError("Missing browser resource closure")
        for resource in row["resources"]:
            object_fields(resource, {"path", "sha256"})
            if sources.get(resource["path"]) != resource["sha256"]: raise ValueError("Loaded dependency is outside bound source inventory")
        requested = {(p["selector"], p["pseudo"]) for p in case["probes"]}
        if not isinstance(row["probes"], list): raise ValueError("Missing layer measurements")
        found = set()
        for probe in row["probes"]:
            object_fields(probe, {"selector", "pseudo", "matches"})
            key = (probe["selector"], probe["pseudo"])
            if key in found or not isinstance(probe["matches"], list) or not probe["matches"]: raise ValueError("Missing or duplicate measured layer")
            found.add(key)
        if found != requested: raise ValueError("Measured layers differ from plan")
        if not isinstance(row["details"], list) or len(row["details"]) != len(case["details"]): raise ValueError("Missing required detail crops")
        detail_ids = set()
        for detail in row["details"]:
            object_fields(detail, {"id", "selector", "render", "clip", "image"}, {"space","parent","pixels"})
            expected = next((d for d in case["details"] if d["id"] == detail["id"]), None)
            if expected is None or detail["id"] in detail_ids or expected["selector"] != detail["selector"]: raise ValueError("Unplanned or duplicate detail")
            detail_ids.add(detail["id"])
            clip = detail["clip"]
            object_fields(clip, {"x", "y", "width", "height", "scale"})
            if clip["scale"] != expected["scale"] or any(type(clip[k]) not in {int,float} or not math.isfinite(clip[k]) or clip[k] < 0 for k in ("x", "y", "width", "height")):
                raise ValueError("Invalid detail clip")
            owner = next(p for p in row["probes"] if p["selector"] == detail["selector"] and not p["pseudo"])["matches"][0]
            box = owner.get("bounds")
            object_fields(box, {"x", "y", "width", "height"})
            space=expected.get("space","document")
            if detail.get("space","document") != space: raise ValueError("Detail coordinate space differs from plan")
            offset_x,offset_y=(0,0) if space=="viewport" else (actual["scrollX"],actual["scrollY"])
            x = max(0, math.floor(box["x"] + offset_x - expected["padding"]))
            y = max(0, math.floor(box["y"] + offset_y - expected["padding"]))
            right=math.ceil(box["x"]+offset_x+box["width"]+expected["padding"])
            bottom=math.ceil(box["y"]+offset_y+box["height"]+expected["padding"])
            if space=="viewport": right,bottom=min(actual["width"],right),min(actual["height"],bottom)
            wanted = {"x":x,"y":y,"width":right-x,"height":bottom-y,"scale":expected["scale"]}
            if clip != wanted: raise ValueError(f"Detail {row['id']}:{detail['id']} clip is not the measured owner: {clip} != {wanted}")
            bound(detail["render"])
            if detail["render"]["path"] in sources or file_digest(root, detail["render"]["path"]) != detail["render"]["sha256"]: raise ValueError("Detail bytes changed or alias a source")
            with (root / detail["render"]["path"]).open("rb") as handle: header = handle.read(24)
            if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n": raise ValueError("Expected lossless detail PNG")
            dw, dh = struct.unpack(">II", header[16:24])
            if space=="viewport":
                if detail.get("parent") != row["viewportRender"]: raise ValueError("Viewport crop must bind its exact parent frame")
                px,py=pixel_round(x*actual["dpr"]),pixel_round(y*actual["dpr"])
                pixels={"x":px,"y":py,"width":min(pixel_round(clip["width"]*actual["dpr"]),view_width-px),"height":min(pixel_round(clip["height"]*actual["dpr"]),view_height-py)}
                if detail.get("pixels") != pixels: raise ValueError("Viewport pixel crop differs from measured owner")
                expected_w,expected_h=pixels["width"]*clip["scale"],pixels["height"]*clip["scale"]
            else: expected_w,expected_h=clip["width"]*clip["scale"]*actual["dpr"],clip["height"]*clip["scale"]*actual["dpr"]
            if detail["image"] != {"width":dw,"height":dh} or abs(dw-expected_w) > 1 or abs(dh-expected_h) > 1:
                raise ValueError("Detail PNG dimensions disagree with clip/environment")
        if "sequence" in case:
            frames = row.get("sequence")
            spec = case["sequence"]
            count = (spec["durationMs"] * spec["fps"] + 999) // 1000
            if not isinstance(frames, list) or len(frames) != count: raise ValueError("Incomplete temporal evidence")
            last = -1
            for frame in frames:
                object_fields(frame, {"atMs", "render", "environment"})
                if type(frame["atMs"]) not in {int, float} or not math.isfinite(frame["atMs"]) or frame["atMs"] <= last: raise ValueError("Frame times must increase")
                last = frame["atMs"]
                bound(frame["render"])
                if frame["render"]["path"] in sources or file_digest(root, frame["render"]["path"]) != frame["render"]["sha256"]: raise ValueError("Temporal render changed or aliases a source")
                if frame["environment"] != {key: actual[key] for key in ("width", "height", "dpr", "theme", "touch", "motion", "route")}:
                    raise ValueError("Browser environment changed during sequence")
                with (root / frame["render"]["path"]).open("rb") as handle: header = handle.read(24)
                if len(header)<24 or header[:8] != b"\x89PNG\r\n\x1a\n" or struct.unpack(">II", header[16:24]) != (round(actual["width"]*actual["dpr"]), round(actual["height"]*actual["dpr"])):
                    raise ValueError("Temporal frame dimensions disagree with browser environment")
            if frames[-1]["atMs"] < spec["durationMs"] - 2000 / spec["fps"]: raise ValueError("Temporal coverage is too short")
        elif "sequence" in row: raise ValueError("Unplanned temporal evidence")
        observed[row["id"]] = row
    if observed.keys() != cases.keys(): raise ValueError("Required browser combinations are missing")
    return plan, receipt
