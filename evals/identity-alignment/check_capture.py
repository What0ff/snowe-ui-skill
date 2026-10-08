"""Check actual browser geometry with the installed product, not a taste score."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

scripts, workspace, receipt_path = map(Path, sys.argv[1:4])
sys.path.insert(0, str(scripts))
from visual_system import inspect_system

plan = json.loads((workspace / "PLAN.json").read_text(encoding="utf-8"))
receipt = json.loads((workspace / receipt_path).read_text(encoding="utf-8"))
system_path = workspace / "SYSTEM.json"
binding = {"path": "SYSTEM.json", "sha256": hashlib.sha256(system_path.read_bytes()).hexdigest()}
baseline = inspect_system(workspace, binding, plan, receipt)
if baseline["issues"]: raise ValueError(f"Corrected control geometry failed: {baseline}")

# Reuse actual measured owners from the deliberately weak neighboring row.
# This is a detector check on bound browser measurements, not a changed render.
bad = deepcopy(receipt)
for row in bad["observations"]:
    if row["id"] == "narrow": continue  # Its input intentionally occupies a different row.
    probes = {probe["selector"]: probe for probe in row["probes"]}
    probes[".good input"]["matches"] = deepcopy(probes[".bad input"]["matches"])
    probes[".good button"]["matches"] = deepcopy(probes[".bad button"]["matches"])
detected = inspect_system(workspace, binding, plan, bad)["issues"]
if len(detected) != 2 or not all(any(case in issue for issue in detected) for case in ("axis-wide", "axis-retina")):
    raise ValueError(f"Measured weak row escaped detection: {detected}")
print(json.dumps({"status": "PASS", "corrected": baseline["issues"], "measured_defects": detected,
                  "boundary": "Geometry evidence and explicit source contracts; visual quality requires inspected renders"}))
