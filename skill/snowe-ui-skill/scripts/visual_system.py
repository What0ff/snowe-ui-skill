#!/usr/bin/env python3
"""Validate scoped visual ownership and declared relationships, not taste."""
from __future__ import annotations

import math

from checked_evidence import object_fields, text, file_digest
from observation import bound, current, relative

AXES = {"composition", "typography", "color", "surfaces", "shape", "imagery", "motion", "responsive"}
LAYERS = {"element", "pseudo", "backdrop", "portal", "font", "image", "svg", "canvas", "video"}
GEOMETRY = {"x", "y", "width", "height", "right", "bottom", "centerX", "centerY"}


def finite_number(value, field):
    try:
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError(f"{field} must be a finite number")
    except OverflowError as error:
        raise ValueError(f"{field} exceeds numeric limits") from error
    return value


def geometry_value(match, property_name):
    bounds = match.get("bounds")
    object_fields(bounds, {"x", "y", "width", "height"})
    for name, value in bounds.items():
        finite_number(value, f"bounds.{name}")
    if bounds["width"] <= 0 or bounds["height"] <= 0:
        raise ValueError("Geometry needs a visible positive owner box")
    x, y, width, height = (bounds[name] for name in ("x", "y", "width", "height"))
    values = {**bounds, "right": x + width, "bottom": y + height,
              "centerX": x + width / 2, "centerY": y + height / 2}
    return finite_number(values[property_name], property_name)


def texts(values, field, empty=False):
    if not isinstance(values, list) or (not values and not empty): raise ValueError(f"Missing {field}")
    for value in values: text(value, field)
    if len(set(values)) != len(values): raise ValueError(f"Duplicate {field}")


def inspect_system(root, binding, plan, receipt):
    system = current(root, binding)
    object_fields(system, {"schema", "revision", "scope", "depth", "direction", "tokens", "components", "relations", "exceptions", "hypotheses"}, {"previous"})
    if system["schema"] not in ("1.0", "1.1") or type(system["revision"]) is not int or system["revision"] < 1 or system["scope"] != plan["scope"]:
        raise ValueError("Invalid visual system revision/scope")
    if system["depth"] not in {"Direct", "Focused", "Portfolio"}: raise ValueError("Unknown system scope depth")
    if system["revision"] > 1:
        previous = current(root, system.get("previous"))
        if previous["revision"] != system["revision"] - 1 or previous["scope"] != system["scope"]: raise ValueError("Broken visual contract history")
    direction = system["direction"]
    object_fields(direction, {"status", "thesis", "axes", "revisit"})
    if direction["status"] not in {"proposed", "selected", "user-specified"}: raise ValueError("Direction is separate from implementation and user acceptance")
    text(direction["thesis"], "visual thesis"); texts(direction["revisit"], "revisit conditions")
    if not isinstance(direction["axes"], dict) or not direction["axes"] or not direction["axes"].keys() <= AXES: raise ValueError("Unknown/missing direction axes")
    if system["depth"] == "Portfolio" and direction["axes"].keys() != AXES: raise ValueError("Whole-system direction needs all axes; record justified absence explicitly")
    for value in direction["axes"].values(): text(value, "axis decision")
    sources = {item["path"] for item in receipt["sources"]}
    cases = {case["id"]: case for case in plan["cases"]}
    tokens, components = {}, {}
    for token in system["tokens"]:
        object_fields(token, {"id", "owner", "property", "value"})
        for field in token: text(token[field], field)
        if token["id"] in tokens or relative(token["owner"]) not in sources: raise ValueError("Duplicate token or unbound token owner")
        tokens[token["id"]] = token
    for component in system["components"]:
        object_fields(component, {"id", "role", "owner", "selector", "tokens", "states", "consumers", "layers"})
        for field in ("id", "role", "owner", "selector"): text(component[field], field)
        if component["id"] in components or relative(component["owner"]) not in sources: raise ValueError("Duplicate component or unbound owner")
        texts(component["tokens"], "component tokens", empty=True)
        if not set(component["tokens"]) <= tokens.keys(): raise ValueError("Unmapped component token")
        texts(component["states"], "component states")
        if not isinstance(component["consumers"], list) or not component["consumers"] or not isinstance(component["layers"], list) or not component["layers"]:
            raise ValueError("Components need consumers and real layers")
        for consumer in component["consumers"]:
            object_fields(consumer, {"case", "selector"})
            case = cases.get(consumer["case"])
            if case is None or case["state"] not in component["states"]: raise ValueError("Consumer missing from state plan")
            if {"selector": consumer["selector"], "pseudo": ""} not in case["probes"]: raise ValueError("Consumer is not measured")
        for layer in component["layers"]:
            object_fields(layer, {"kind", "selector", "pseudo", "sources", "cases"})
            if layer["kind"] not in LAYERS: raise ValueError("Unknown visual layer")
            texts(layer["sources"], "layer sources", empty=True); texts(layer["cases"], "layer cases")
            if not set(layer["sources"]) <= sources: raise ValueError("Unbound visual dependency")
            for case_id in layer["cases"]:
                if case_id not in cases or {"selector": layer["selector"], "pseudo": layer["pseudo"]} not in cases[case_id]["probes"]: raise ValueError("Unmeasured visual layer")
        components[component["id"]] = component
    if not components: raise ValueError("Visual map has no affected owner")
    observations = {row["id"]: row for row in receipt["observations"]}
    issues, check_ids, exception_ids = [], set(), set()
    if not isinstance(system["exceptions"], list) or not isinstance(system["relations"], list): raise ValueError("Relations/exceptions must be arrays")
    for exception in system["exceptions"]:
        object_fields(exception, {"check", "reason", "revisit"})
        for value in exception.values(): text(value, "exception")
        if exception["check"] in exception_ids: raise ValueError("Duplicate exception")
        exception_ids.add(exception["check"])
    for relation in system["relations"]:
        object_fields(relation, {"id", "members", "intent", "checks"})
        text(relation["id"], "relation ID"); text(relation["intent"], "relationship intent")
        texts(relation["members"], "related components")
        if not set(relation["members"]) <= components.keys(): raise ValueError("Unknown relationship member")
        if not isinstance(relation["checks"], list) or not relation["checks"]: raise ValueError("Relationship needs observable checks")
        for check in relation["checks"]:
            optional = {"equals", "sameAs", "tolerance"} if system["schema"] == "1.1" else {"equals", "sameAs"}
            object_fields(check, {"id", "case", "selector", "pseudo", "property"}, optional)
            if check["id"] in check_ids or ("equals" in check) == ("sameAs" in check): raise ValueError("Duplicate or ambiguous relationship check")
            check_ids.add(check["id"])
            text(check["property"], "relationship property")
            geometry = check["property"].startswith("bounds.")
            tolerance = 0
            if geometry:
                if system["schema"] != "1.1" or check["property"][7:] not in GEOMETRY or check["pseudo"]:
                    raise ValueError("Geometry requires schema 1.1 and a measured element axis, not pseudo-element bounds")
                object_fields(check.get("tolerance"), {"cssPixels", "reason"})
                tolerance = finite_number(check["tolerance"]["cssPixels"], "geometry tolerance")
                if tolerance < 0: raise ValueError("Geometry tolerance cannot be negative")
                text(check["tolerance"]["reason"], "tolerance reason")
            elif "tolerance" in check:
                raise ValueError("Tolerance applies only to declared geometry checks")
            def values(selector, pseudo):
                if geometry and pseudo: raise ValueError("A pseudo-element has no independently measured box")
                row = observations.get(check["case"])
                if row is None: raise ValueError("Relationship case is unobserved")
                probes = [p for p in row["probes"] if p["selector"] == selector and p["pseudo"] == pseudo]
                if len(probes) != 1: raise ValueError("Relationship layer is unobserved")
                result = []
                for match in probes[0]["matches"]:
                    if geometry:
                        result.append(geometry_value(match, check["property"][7:]))
                    else:
                        if check["property"] not in match: raise ValueError("Relationship property is unmeasured")
                        result.append(match[check["property"]])
                if not result: raise ValueError("Relationship has no measured matches")
                return result
            actual = values(check["selector"], check["pseudo"])
            if "sameAs" in check:
                object_fields(check["sameAs"], {"selector", "pseudo"})
                expected = values(check["sameAs"]["selector"], check["sameAs"]["pseudo"])
            else: expected = [check["equals"]]
            if geometry:
                if len(expected) != 1: raise ValueError("Geometry requires one unambiguous reference owner")
                target = finite_number(expected[0], "geometry reference")
                drift = any(abs(value - target) > tolerance for value in actual)
            else:
                drift = len(set(map(str, expected))) != 1 or any(value != expected[0] for value in actual)
            if drift and check["id"] not in exception_ids:
                issues.append(f"Visual relationship drift: {check['id']}")
    if not exception_ids <= check_ids: raise ValueError("Exception does not name a real check")
    if not isinstance(system["hypotheses"], list): raise ValueError("Hypotheses must be an array")
    for hypothesis in system["hypotheses"]:
        object_fields(hypothesis, {"id", "observation", "cause", "change", "prediction", "outcome", "evidence", "applicability", "counterexamples", "reason"})
        for field in ("id", "observation", "cause", "change", "prediction", "applicability", "reason"): text(hypothesis[field], field)
        if hypothesis["outcome"] not in {"untested", "supported", "rejected", "inconclusive"}: raise ValueError("Unknown hypothesis outcome")
        texts(hypothesis["counterexamples"], "counterexamples")
        if not isinstance(hypothesis["evidence"], list) or (hypothesis["outcome"] == "supported" and not hypothesis["evidence"]): raise ValueError("Supported hypothesis needs evidence")
        for evidence in hypothesis["evidence"]:
            bound(evidence)
            if file_digest(root, evidence["path"]) != evidence["sha256"]: issues.append(f"Stale hypothesis: {hypothesis['id']}")
    return {"revision": system["revision"], "direction": direction["status"], "components": sorted(components), "issues": issues}
