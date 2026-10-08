"""Deterministic, repository-only declarations for the identity/alignment proof."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def bind(path):
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def write(path, value):
    (ROOT / path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def build():
    for name in ("span", "span-before", "bluesky-black"):
        brand = name == "bluesky-black"
        value = {"name": name, "asset_type": "brand-mark" if brand else "interface-icon",
                 "role": "External Bluesky identity" if brand else "Distance between mounting boundaries",
                 "grid": "568 x 501" if brand else 24,
                 "live_area": {"min_x": 0, "min_y": 0, "max_x": 568 if brand else 24, "max_y": 501 if brand else 24},
                 "drawing_language": {"mode": "fill" if brand else "stroke", "stroke_width": 0 if brand else 1.5,
                                      "linecap": "not applicable" if brand else "round", "linejoin": "not applicable" if brand else "round",
                                      "corner_language": "Unchanged supplied butterfly" if brand else "Open measurement termini",
                                      "detail_budget": "Supplied silhouette" if brand else "Two boundaries and one dimension relationship"},
                 "target_sizes": [24] if brand else [16, 20, 24],
                 "source": "Official Bluesky black butterfly download" if brand else "Original repository evaluation drawing",
                 "license": "Owner trademark policy; see SOURCES.md" if brand else "Repository MIT; see SOURCES.md",
                 "accessibility_owner": "Owning labeled link/button; image decorative",
                 "provenance": {"kind": "external" if brand else "original", "creator": "Bluesky Social PBC" if brand else "Snowe evaluation author",
                                "source_ref": "https://bsky.social/about/brand-assets/butterfly/bluesky_media_kit_logo_transparent_4.svg" if brand else "SOURCES.md#original-interface-glyphs",
                                "reviewed": "2026-10-08", "sha256": bind(f"assets/{name}.svg")["sha256"]},
                 "evidence": {"source": {"kind": "external", "verification": "unverified"} if brand else {"kind": "local", **bind("SOURCES.md")},
                              "license": bind("SOURCES.md")}}
        if brand:
            value["brand"] = {"schema": "1.0", "identity": "Bluesky", "variant": "Official black butterfly",
                              "artwork": {"path": "../upstream/bluesky-black.svg", "sha256": bind("upstream/bluesky-black.svg")["sha256"]},
                              "usage": {"path": "../SOURCES.md", "sha256": bind("SOURCES.md")["sha256"]}}
        # Evidence paths resolve from the metadata's assets directory.
        for key in ("source", "license"):
            if "path" in value["evidence"][key]: value["evidence"][key]["path"] = "../SOURCES.md"
        write(f"assets/{name}.metadata.json", value)

    cases = []
    for name, viewport in (("wide", "900x900@1"), ("narrow", "390x844@1"), ("retina", "900x900@2")):
        selectors = ["main", ".good", ".bad", ".good input", ".good button", ".good .filter", ".good .primary", ".bad input", ".bad button", ".brand img", ".samples img", "#custom"]
        cases.append({"id": name, "state": "default", "viewport": viewport, "theme": "light", "input": "pointer", "motion": "reduced", "context": "page", "route": "/index.html", "steps": [],
                      "expect": [{"selector": ".good .filter", "property": "attribute:aria-pressed", "equals": "false"}],
                      "probes": [{"selector": selector, "pseudo": ""} for selector in selectors],
                      "details": [{"id": "good-toolbar", "selector": ".good", "padding": 10, "scale": 1},
                                  {"id": "bad-toolbar", "selector": ".bad", "padding": 10, "scale": 1},
                                  {"id": "icons-native", "selector": "#custom", "padding": 0, "scale": 1},
                                  {"id": "icons-detail", "selector": "#custom", "padding": 0, "scale": 2}]})
    write("PLAN.json", {"schema": "1.0", "scope": "Identity and mixed control relationships", "sourceRoots": ["index.html", "assets", "upstream", "SOURCES.md"], "cases": cases})
    checks = []
    for case in cases:
        narrow = case["id"] == "narrow"
        checks.append({"id": f"axis-{case['id']}", "case": case["id"], "selector": ".good .primary" if narrow else ".good button", "pseudo": "", "property": "bounds.bottom",
                       "sameAs": {"selector": ".good .filter" if narrow else ".good input", "pseudo": ""},
                       "tolerance": {"cssPixels": 0.25, "reason": "Declared bottom axis; permit fractional layout rounding, retain unequal control heights"}})
    write("SYSTEM.json", {"schema": "1.1", "revision": 1, "scope": "Identity and mixed control relationships", "depth": "Focused",
                          "direction": {"status": "selected", "thesis": "Separate identity, drawing and control geometry", "axes": {"composition": "Actual controls share the operational row; captions/help have their own rows"}, "revisit": ["Changed toolbar or identity usage"]},
                          "tokens": [], "components": [{"id": "toolbar", "role": "Mixed field and peer actions", "owner": "index.html", "selector": ".good", "tokens": [], "states": ["default"],
                                                        "consumers": [{"case": c["id"], "selector": ".good"} for c in cases],
                                                        "layers": [{"kind": "element", "selector": ".good", "pseudo": "", "sources": ["index.html"], "cases": [c["id"] for c in cases]}]}],
                          "relations": [{"id": "operational-axis", "members": ["toolbar"], "intent": "Align visible controls independently of captions and help", "checks": checks}], "exceptions": [], "hypotheses": []})
    contexts = []
    for brand in (True, False):
        name = "bluesky-black" if brand else "span"
        contexts.append({"id": name, "symbol_role": "brand-mark" if brand else "interface-icon", **({"brand_identity": "Bluesky"} if brand else {}),
                         "role": "Link to an external profile" if brand else "Identify the span measurement control", "lang": "ru", "dir": "ltr", "component": "labeled-button",
                         "label": "Bluesky" if brand else "Расстояние между креплениями", "sizes": [24] if brand else [16, 20, 24], "states": ["default"],
                         "selected": name, "verdict": "KEEP", "decision_evidence": "Implementer self-review; see REVIEW.md; no recognition-study claim",
                         "context_evidence": {"basis": "representative", "source": "index.html", "selector": ".brand" if brand else ".measure", "viewport": "900x900@1 and 390x844@1"},
                         "candidates": []})
        for asset_name in ([name] if brand else [name, "span-before"]):
            metadata = json.loads((ROOT / f"assets/{asset_name}.metadata.json").read_text(encoding="utf-8"))
            contexts[-1]["candidates"].append({"id": asset_name, "name": asset_name, "kind": "existing" if brand else "custom", "asset": f"assets/{asset_name}.svg", "metadata": f"assets/{asset_name}.metadata.json",
                                             "asset_sha256": bind(f"assets/{asset_name}.svg")["sha256"], "source": metadata["source"], "license": metadata["license"],
                                             "rationale": "Retain supplied identity" if brand else "Two boundary cues survive at native size" if asset_name == name else "REVISE: inner ticks crowd the dimension cue"})
        if not brand:
            contexts[-1]["candidates"].append({"id": "span-text", "name": "Visible wording", "kind": "none", "visible_label": "Расстояние между креплениями", "source": "No artwork", "license": "No artwork", "rationale": "Truthful alternative; optional pictogram supports repeated scanning"})
    write("manifest.json", {"schema_version": "1.2", "title": "Identity and custom drawing role proof", "contexts": contexts})


if __name__ == "__main__":
    build()
