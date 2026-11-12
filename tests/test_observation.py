"""Adversarial evidence and relational contracts; synthetic bytes never prove taste."""
from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from tests.evidence_factory import binding, make_review, write

ROOT = Path(__file__).resolve().parents[1]
OBSERVER = ROOT / "skill/snowe-ui-skill/scripts/observe.mjs"
sys.path.insert(0, str(ROOT / "skill/snowe-ui-skill/scripts"))
from observation import inspect_capture, validate_plan
from visual_review import inspect_review


@lru_cache(maxsize=1)
def node_executable():
    """Node 22+ for the optional observer, or None when this host cannot run it."""
    node = shutil.which("node")
    if not node: return None
    version = subprocess.run([node, "--version"], capture_output=True, text=True, timeout=30).stdout.strip()
    try:
        major = int(version.lstrip("v").split(".")[0])
    except ValueError:
        return None
    return node if major >= 22 else None


@lru_cache(maxsize=1)
def browser_observation_available():
    node = node_executable()
    if not node: return False
    result = subprocess.run([node, str(OBSERVER), "capabilities"], capture_output=True, text=True, timeout=60)
    return result.returncode == 0 and json.loads(result.stdout)["available"]


class ObservationIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "page.css").write_text("main{font-weight:400}")
        self.report = make_review(self.root)

    def check(self):
        write(self.root, "review.json", self.report)
        return inspect_review(self.root, "review.json")

    def edit(self, name, edit):
        value = json.loads((self.root / name).read_text(encoding="utf-8")); edit(value); write(self.root, name, value)

    def rebind(self, *, plan=False, system=False, receipt=False):
        if plan or system:
            self.edit("attention.json", lambda c:c.update(**({"plan": binding(self.root, "plan.json")} if plan else {}), **({"system": binding(self.root, "visual-system.json")} if system else {})))
            self.report["contract"] = binding(self.root, "attention.json")
        if receipt: self.report["capture"] = binding(self.root, "receipt.json")

    def test_required_mobile_theme_input_and_context_cannot_be_removed(self):
        for field, value in (("viewport", "390x844@1"), ("theme", "dark"), ("input", "keyboard"), ("context", "overlay"), ("motion", "reduced")):
            original = (self.root / "plan.json").read_bytes()
            with self.subTest(field=field):
                def add(plan):
                    extra = deepcopy(plan["cases"][0]); extra.update(id="required", **{field: value}); plan["cases"].append(extra)
                self.edit("plan.json", add); self.rebind(plan=True)
                self.edit("receipt.json", lambda receipt:receipt.update(plan=binding(self.root, "plan.json"))); self.rebind(receipt=True)
                self.assertEqual("REVIEW_REQUIRED", self.check()["status"])
            (self.root / "plan.json").write_bytes(original)

    def test_viewport_relabel_with_and_without_receipt_edit_needs_real_recapture(self):
        self.report["renders"][0]["viewport"] = "390x844@1"
        self.assertEqual("REVIEW_REQUIRED", self.check()["status"])
        self.edit("receipt.json", lambda receipt:receipt["observations"][0].update(viewport="390x844@1"))
        self.edit("plan.json", lambda plan:plan["cases"][0].update(viewport="390x844@1")); self.rebind(plan=True)
        self.edit("receipt.json", lambda receipt:receipt.update(plan=binding(self.root, "plan.json"))); self.rebind(receipt=True)
        self.assertEqual("REVIEW_REQUIRED", self.check()["status"])

    def test_changed_css_cannot_be_hidden_by_omitting_sources(self):
        (self.root / "second.css").write_text("body{color:red}")
        self.report["sources"] = [binding(self.root, "second.css")]
        (self.root / "page.css").write_text("main{font-weight:900}")
        self.assertEqual("REVIEW_REQUIRED", self.check()["status"])

    def test_dependency_closure_detects_new_files_and_out_of_scope_resources(self):
        (self.root / "source").mkdir(); (self.root / "source/page.css").write_text("body{}")
        self.edit("plan.json", lambda p:p.update(sourceRoots=["source"])); self.rebind(plan=True)
        self.edit("receipt.json", lambda r:r.update(plan=binding(self.root, "plan.json"), sources=[binding(self.root, "source/page.css")]))
        (self.root / "source/new.css").write_text("body{background:red}")
        self.rebind(receipt=True)
        self.assertEqual("REVIEW_REQUIRED", self.check()["status"])
        # Even a current inventory cannot bind a loaded dependency outside it.
        self.edit("receipt.json", lambda r:r.update(sources=[binding(self.root, "source/new.css"), binding(self.root, "source/page.css")]))
        self.rebind(receipt=True)
        self.assertEqual("REVIEW_REQUIRED", self.check()["status"])

    def test_actual_png_dimensions_and_browser_emulation_are_checked(self):
        original = (self.root / "receipt.json").read_bytes()
        for field, value in (("theme", "dark"), ("touch", True), ("motion", "reduced"), ("dpr", 2), ("dpr", True), ("fonts", "loading"), ("route", "/wrong"), ("settled", False)):
            with self.subTest(field=field):
                (self.root / "receipt.json").write_bytes(original)
                self.edit("receipt.json", lambda r:r["observations"][0]["actual"].update(**{field:value})); self.rebind(receipt=True)
                self.assertEqual("REVIEW_REQUIRED", self.check()["status"])

    def test_device_pixel_ratio_is_compared_as_a_number_not_its_spelling(self):
        # Browsers report devicePixelRatio as a number: a planned "@1.0" captures as 1.
        for planned, reported, status in (("390x844@1.0", 1, "PASS"), ("390x844@1.50", 1.5, "PASS"),
                                          ("390x844@1.1", 1.100000023841858, "PASS"), ("390x844@1.0", 1.25, "REVIEW_REQUIRED")):
            with self.subTest(planned=planned, reported=reported):
                with tempfile.TemporaryDirectory() as directory:
                    self.root = Path(directory)
                    (self.root / "page.css").write_text("main{font-weight:400}")
                    self.report = make_review(self.root, viewport=planned)
                    self.edit("receipt.json", lambda r:r["observations"][0]["actual"].update(dpr=reported)); self.rebind(receipt=True)
                    result = self.check()
                    self.assertEqual(status, result["status"], result["issues"])

    def test_detail_evidence_cannot_be_dropped_unassessed_or_rescaled(self):
        self.edit("receipt.json", lambda r:r["observations"][0].update(details=[])); self.rebind(receipt=True)
        self.assertEqual("REVIEW_REQUIRED", self.check()["status"])
        self.report = make_review(self.root)
        self.report["renders"] = self.report["renders"][:1]
        self.report["visualAssessment"]["assessments"][0]["renders"] = ["render.png"]
        self.assertEqual("REVIEW_REQUIRED", self.check()["status"])
        self.report = make_review(self.root)
        self.edit("receipt.json", lambda r:r["observations"][0]["details"][0]["clip"].update(scale=2)); self.rebind(receipt=True)
        self.assertEqual("REVIEW_REQUIRED", self.check()["status"])

    def test_duplicate_or_empty_temporal_evidence_cannot_pass(self):
        sequence={"fps":12,"durationMs":1000,"start":[],"events":[]}
        self.edit("plan.json", lambda p:p["cases"][0].update(sequence=sequence)); self.rebind(plan=True)
        self.edit("receipt.json", lambda r:r.update(plan=binding(self.root,"plan.json"))); self.rebind(receipt=True)
        self.assertEqual("REVIEW_REQUIRED", self.check()["status"])

    def test_capture_reader_budget_does_not_expand_ordinary_json_inputs(self):
        from checked_evidence import read_json
        (self.root / "large.json").write_text(json.dumps(["bounded measurement"] * 60000), encoding="utf-8")
        with self.assertRaises(ValueError): read_json(self.root / "large.json")
        self.assertEqual(60000, len(read_json(self.root / "large.json", max_bytes=8_000_000)))

    def test_failed_replay_cannot_be_relabelled_as_the_requested_state(self):
        self.edit("receipt.json", lambda r:r["observations"][0]["stateProof"][0].update(actual="900"));self.rebind(receipt=True)
        self.assertEqual("REVIEW_REQUIRED", self.check()["status"])

    def test_fixed_layer_crop_binds_the_original_viewport_frame(self):
        self.edit("plan.json",lambda p:p['cases'][0]['details'][0].update(space='viewport'));self.rebind(plan=True)
        self.edit("receipt.json",lambda r:(r.update(plan=binding(self.root,'plan.json')),r['observations'][0]['details'][0].update(space='viewport',parent=binding(self.root,'viewport.png'),pixels={'x':0,'y':0,'width':900,'height':700})));self.rebind(receipt=True)
        self.assertEqual('PASS',self.check()['status'])
        self.edit("receipt.json",lambda r:r['observations'][0]['details'][0].update(parent=binding(self.root,'render.png')));self.rebind(receipt=True)
        self.assertEqual('REVIEW_REQUIRED',self.check()['status'])

    def test_missing_layer_or_owner_is_unknown_not_pass(self):
        self.edit("visual-system.json", lambda s:s["components"][0]["layers"].append({"kind":"pseudo", "selector":"main", "pseudo":"::before", "sources":["page.css"], "cases":["main"]}))
        self.rebind(system=True)
        self.assertEqual("REVIEW_REQUIRED", self.check()["status"])

    def test_relationship_drift_and_scoped_exception(self):
        check = {"id":"body-weight", "case":"main", "selector":"main", "pseudo":"", "property":"fontWeight", "equals":"500"}
        self.edit("visual-system.json", lambda s:s["relations"].append({"id":"body", "members":["page"], "intent":"Body role remains coherent with other labels", "checks":[check]})); self.rebind(system=True)
        self.assertEqual("REVIEW_REQUIRED", self.check()["status"])
        self.edit("visual-system.json", lambda s:s["exceptions"].append({"check":"body-weight", "reason":"User-specified regular text in this context", "revisit":"If the user reopens typography"})); self.rebind(system=True)
        self.assertEqual("PASS", self.check()["status"])

    def test_selected_direction_is_not_implementation_or_user_acceptance(self):
        self.edit("visual-system.json", lambda s:s["direction"].update(status="proposed")); self.rebind(system=True)
        self.assertEqual("REVIEW_REQUIRED", self.check()["status"])
        self.edit("visual-system.json", lambda s:s["direction"].update(status="user-specified")); self.rebind(system=True)
        result = self.check()
        self.assertEqual("PASS", result["status"])
        self.assertEqual("UNCONFIRMED", result["user_acceptance"])

    def test_supported_memory_requires_current_evidence_and_counterexample(self):
        hypothesis = {"id":"regular", "observation":"Labels compete", "cause":"Equal weight", "change":"Lower secondary weight", "prediction":"Primary remains first", "outcome":"supported", "evidence":[binding(self.root,"render.png")], "applicability":"Secondary reading labels", "counterexamples":["Critical alarms need stronger emphasis"], "reason":"Compared identical content"}
        self.edit("visual-system.json", lambda s:s["hypotheses"].append(hypothesis)); self.rebind(system=True)
        self.assertEqual("PASS", self.check()["status"])
        hypothesis["evidence"] = []
        self.edit("visual-system.json", lambda s:s.update(hypotheses=[hypothesis])); self.rebind(system=True)
        self.assertEqual("REVIEW_REQUIRED", self.check()["status"])

    def test_history_remains_readable_but_cannot_close_new_proof(self):
        self.report["schema"] = "2.0"; self.report.pop("capture")
        self.edit("attention.json", lambda c:(c.update(schema="1.0"), c.pop("plan"), c.pop("system")))
        self.report["contract"] = binding(self.root,"attention.json")
        self.assertEqual("REVIEW_REQUIRED", self.check()["status"])
        self.assertEqual("HISTORICAL", self.check()["integrity"])


TOGGLE_PAGE = """<!doctype html><meta charset="utf-8"><title>Toggle</title>
<main><button id="toggle" type="button" aria-pressed="false">Toggle</button></main>
<script>
const toggle = document.querySelector('#toggle');
toggle.addEventListener('click', () => toggle.setAttribute('aria-pressed', String(toggle.getAttribute('aria-pressed') !== 'true')));
</script>
"""


class ReplayKeyTests(unittest.TestCase):
    """Keyboard replay names keys; the documented `space` must survive plan checks and capture."""

    def plan(self, steps):
        case = {"id": "space", "state": "pressed", "viewport": "390x844@1", "theme": "light", "input": "keyboard",
                "motion": "reduced", "context": "control", "route": "/page/index.html", "steps": steps,
                "probes": [{"selector": "#toggle", "pseudo": ""}],
                "details": [{"id": "toggle", "selector": "#toggle", "padding": 4, "scale": 1}],
                "expect": [{"selector": "#toggle", "property": "attribute:aria-pressed", "equals": "true"},
                           {"selector": "#toggle", "property": "focused", "equals": True}]}
        return {"schema": "1.0", "scope": "Keyboard toggle", "sourceRoots": ["page"], "cases": [case]}

    def test_space_is_a_supported_key_name(self):
        for key in ("Space", "space", "Tab", "Enter", "Escape", "ArrowDown", "ArrowUp"):
            with self.subTest(key=key):
                validate_plan(self.plan([{"action": "key", "key": key}]))

    def test_unsupported_or_missing_keys_fail_plan_validation(self):
        # A literal " " is not printable text in JSON plans; name the key instead.
        for step in ({"action": "key", "key": " "}, {"action": "key", "key": "F5"}, {"action": "key"}):
            with self.subTest(step=step):
                with self.assertRaisesRegex(ValueError, "key"):
                    validate_plan(self.plan([step]))

    def test_space_activation_passes_capture_and_receipt_check(self):
        if not browser_observation_available():
            self.skipTest("Node 22+ and a system Chrome/Chromium/Edge are unavailable")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "page").mkdir()
            (root / "page/index.html").write_text(TOGGLE_PAGE, encoding="utf-8")
            plan = self.plan([{"action": "key", "key": "Tab"}, {"action": "key", "key": "Space"}])
            validate_plan(plan)
            write(root, "plan.json", plan)
            result = subprocess.run([node_executable(), str(OBSERVER), "capture", str(root), "plan.json", "captures"],
                                    capture_output=True, text=True, timeout=180)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            receipt = json.loads((root / "captures/receipt.json").read_text(encoding="utf-8"))
            proof = receipt["observations"][0]["stateProof"]
            self.assertEqual(["true", True], [item["actual"] for item in proof])
            inspect_capture(root, binding(root, "captures/receipt.json"), binding(root, "plan.json"))


if __name__ == "__main__": unittest.main()
