"""Synthetic schema fixtures. No browser execution or aesthetic claim is implied."""
import hashlib
import json
from pathlib import Path
import struct
import zlib
import subprocess
from functools import lru_cache

PRODUCT = Path(__file__).resolve().parents[1] / "skill/snowe-ui-skill/scripts"
HISTORICAL_REVISION = "92eeb724fcfa889cafe8cb47c219b7e80a8e2635"


@lru_cache(maxsize=1)
def historical_browser_digest(root):
    raw = subprocess.check_output(["git", "show", HISTORICAL_REVISION+":scripts/browser-smoke.mjs"], cwd=root)
    return hashlib.sha256(raw).hexdigest()


def write(root, name, value):
    (root / name).write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def binding(root, name):
    return {"path": name, "sha256": hashlib.sha256((root / name).read_bytes()).hexdigest()}


def make_review(root, owner="page.css", state="running", viewport="900x700@1", image="render.png"):
    width, tail = viewport.split("x"); height, dpr = tail.split("@")
    width, height, dpr = int(width), int(height), float(dpr)
    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))
    pixels = (b"\0" + b"\xff\xff\xff" * round(width*dpr)) * round(height*dpr)
    (root / image).write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", round(width*dpr), round(height*dpr), 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(pixels)) + chunk(b"IEND", b""))
    (root / "detail.png").write_bytes((root / image).read_bytes())
    (root / "viewport.png").write_bytes((root / image).read_bytes())
    case = {"id": "main", "state": state, "viewport": viewport, "theme": "light", "input": "pointer", "motion": "normal", "context": "page", "route": "/page", "steps": [], "probes": [{"selector": "main", "pseudo": ""}]}
    plan = {"schema": "1.0", "scope": "Run monitoring", "sourceRoots": [owner], "cases": [case]}
    case["details"] = [{"id":"owner", "selector":"main", "padding":0, "scale":1}]
    case["expect"] = [{"selector":"main", "property":"css:fontWeight", "equals":"400"}]
    write(root, "plan.json", plan)
    system = {"schema": "1.0", "revision": 1, "scope": plan["scope"], "depth": "Direct", "direction": {"status": "selected", "thesis": "Preserve a coherent reading role", "axes": {"typography": "Body role remains regular"}, "revisit": ["New type role"]},
        "tokens": [], "components": [{"id": "page", "role": "Reading content", "owner": owner, "selector": "main", "tokens": [], "states": [state], "consumers": [{"case": "main", "selector": "main"}], "layers": [{"kind": "element", "selector": "main", "pseudo": "", "sources": [owner], "cases": ["main"]}]}], "relations": [], "exceptions": [], "hypotheses": []}
    write(root, "visual-system.json", system)
    contract = {"schema": "2.0", "scope": plan["scope"], "plan": binding(root, "plan.json"), "system": binding(root, "visual-system.json"), "states": [{"id": state, "question": "How is the current run progressing?", "priority": ["Run progress", "Kingdom status"], "cues": ["Progress and related data form a group"], "competing": ["Create new"]}]}
    write(root, "attention.json", contract)
    receipt = {"schema": "1.0", "plan": binding(root, "plan.json"), "observer": hashlib.sha256((PRODUCT / "observe.mjs").read_bytes()).hexdigest(), "browser": {"product": "Synthetic test", "userAgent": "Synthetic", "jsVersion": "test", "protocolVersion": "test"}, "sources": [binding(root, owner)],
        "observations": [{**{k:case[k] for k in ("id", "state", "viewport", "theme", "input", "motion", "context")}, "render": binding(root, image), "actual": {"width": width, "height": height, "dpr": dpr, "theme": "light", "touch": False, "motion": "normal", "route": "/page", "fonts": "loaded", "settled": True}, "image": {"width": round(width*dpr), "height": round(height*dpr)}, "resources": [binding(root, owner)], "probes": [{"selector": "main", "pseudo": "", "matches": [{"fontWeight": "400", "color": "rgb(0, 0, 0)"}]}], "diagnostics": []}]}
    write(root, "receipt.json", receipt)
    receipt["observations"][0]["details"] = [{"id":"owner", "selector":"main", "render":binding(root,"detail.png"), "clip":{"x":0,"y":0,"width":width,"height":height,"scale":1}, "image":{"width":round(width*dpr),"height":round(height*dpr)}}]
    receipt["observations"][0]["actual"].update(scrollX=0,scrollY=0)
    receipt["observations"][0]["stateProof"] = [{**case["expect"][0], "actual":"400"}]
    receipt["observations"][0]["viewportRender"] = binding(root,"viewport.png")
    receipt["observations"][0]["probes"][0]["matches"][0]["bounds"]={"x":0,"y":0,"width":width,"height":height}
    write(root, "receipt.json", receipt)
    report = {"schema": "3.0", "scope": plan["scope"], "method": "self-review", "reviewer": "Synthetic unit test; not a visual claim", "contract": binding(root, "attention.json"), "capture": binding(root, "receipt.json"), "sources": receipt["sources"],
        "renders": [{**binding(root, image), **{k:case[k] for k in ("id", "state", "viewport", "theme", "input", "motion", "context")}}], "visualAssessment": {"verdict": "KEEP", "finding": "Authored contract record", "assessments": [{"state": state, "renders": [image], "observedAttention": ["Run progress", "Kingdom status"], "finding": "Authored comparison", "verdict": "KEEP"}], "findings": []}, "userAcceptance": "UNCONFIRMED"}
    write(root, "review.json", report)
    report["renders"].append({**report["renders"][0], **binding(root,"detail.png"), "id":"main:owner"})
    report["renders"].append({**report["renders"][0], **binding(root,"viewport.png"), "id":"main:viewport"})
    report["visualAssessment"]["assessments"][0]["renders"].append("detail.png")
    report["visualAssessment"]["assessments"][0]["renders"].append("viewport.png")
    write(root, "review.json", report)
    return report
