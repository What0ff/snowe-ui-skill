from __future__ import annotations

import importlib.util
import copy
import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "evals" / "designer-behavior" / "run_eval.py"
SCENARIOS = REPO_ROOT / "evals" / "designer-behavior" / "scenarios.json"
SKILL = REPO_ROOT / "skill" / "snowe-ui-skill" / "SKILL.md"
EXPLORATION = REPO_ROOT / "skill" / "snowe-ui-skill" / "references" / "exploration-protocol.md"
EXPECTED_UNCERTAINTY_SURFACE_FIELDS = {
    "user_goals",
    "topology",
    "journey",
    "content_object_relationships",
    "interaction_contracts",
    "responsive_transformations",
    "system_contracts",
}


def load_runner():
    spec = importlib.util.spec_from_file_location("snowe_designer_behavior_scope", RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load designer behavior runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ScopeContractTests(unittest.TestCase):
    def test_calibration_probes_cover_bounded_shared_medium_and_open_work(self):
        result = load_runner().evaluate()
        finding = next(item for item in result["findings"] if item["scenario"] == "scope-proportionality")

        self.assertEqual(finding["verdict"], "KEEP", finding["evidence"])
        traces = {trace["id"]: trace for trace in result["scope_traces"]}
        self.assertEqual(
            set(traces),
            {
                "trivial-visual-correction",
                "narrow-accessibility-defect",
                "shared-owner-component-symptom",
                "medium-established-feature",
                "open-journey-architecture",
                "narrow-high-consequence-correction",
            },
        )
        self.assertEqual(traces["trivial-visual-correction"]["route"]["depth"], "Direct")
        self.assertEqual(traces["narrow-accessibility-defect"]["route"]["depth"], "Direct")
        self.assertEqual(traces["shared-owner-component-symptom"]["route"]["depth"], "Focused")
        self.assertEqual(traces["medium-established-feature"]["route"]["depth"], "Focused")
        self.assertEqual(traces["open-journey-architecture"]["route"]["depth"], "Portfolio")
        self.assertEqual(traces["narrow-high-consequence-correction"]["route"]["depth"], "Direct")
        self.assertIn(
            "high-consequence proof",
            traces["narrow-high-consequence-correction"]["route"]["artifacts"],
        )

        for trace in traces.values():
            route = trace["route"]
            self.assertTrue(
                set(route["references_loaded"]).isdisjoint(route["references_not_loaded"]),
                trace["id"],
            )
            self.assertEqual(trace["evidence_type"], "authored deterministic process trace")
            self.assertEqual(trace["evidence_category"], "deterministic_contracts")
            self.assertEqual(trace["host_causation"], "NOT_MEASURED")
            self.assertEqual(
                trace["overhead"], {"tokens": "NOT_OBSERVABLE", "time": "NOT_OBSERVABLE"}
            )
            self.assertTrue(route["artifacts"], trace["id"])
            self.assertTrue(route["delivery"], trace["id"])
            self.assertTrue(route["stop_evidence"], trace["id"])
            self.assertTrue(route["escalation_evidence"], trace["id"])

    def test_contract_rejects_flattened_and_unjustifiably_widened_routes(self):
        runner = load_runner()
        original = json.loads(SCENARIOS.read_text(encoding="utf-8"))
        skill_text = SKILL.read_text(encoding="utf-8")
        exploration_text = EXPLORATION.read_text(encoding="utf-8")

        widened = copy.deepcopy(original)
        shared = next(case for case in widened["scope_calibration"] if case["id"] == "shared-owner-component-symptom")
        shared["observed"]["shared_consumers"] = False
        shared["observed"]["focused_choice"] = False
        shared["observed"]["material_uncertainty"] = []
        shared["observed"]["uncertainty_surface"] = {
            field: False for field in runner.UNCERTAINTY_SURFACE_FIELDS
        }
        failures, _, _ = runner.scope_calibration_contract(widened, skill_text, exploration_text)
        self.assertTrue(any("Focused route has no observed" in failure for failure in failures), failures)

        flattened = copy.deepcopy(original)
        architecture = next(case for case in flattened["scope_calibration"] if case["id"] == "open-journey-architecture")
        architecture["expected"]["depth"] = "Focused"
        failures, _, _ = runner.scope_calibration_contract(flattened, skill_text, exploration_text)
        self.assertTrue(any("flattened below Portfolio" in failure for failure in failures), failures)

        underproved = copy.deepcopy(original)
        critical = next(case for case in underproved["scope_calibration"] if case["id"] == "narrow-high-consequence-correction")
        critical["expected"]["artifacts"].remove("high-consequence proof")
        failures, _, _ = runner.scope_calibration_contract(underproved, skill_text, exploration_text)
        self.assertTrue(any("lacks its proof floor" in failure for failure in failures), failures)

        vague = copy.deepcopy(original)
        critical = next(case for case in vague["scope_calibration"] if case["id"] == "narrow-high-consequence-correction")
        critical["expected"]["stop_evidence"] = "a high-consequence proof was recorded"
        failures, _, _ = runner.scope_calibration_contract(vague, skill_text, exploration_text)
        self.assertTrue(any("omits required dimensions" in failure for failure in failures), failures)

        self.assertEqual(runner.UNCERTAINTY_SURFACE_FIELDS, EXPECTED_UNCERTAINTY_SURFACE_FIELDS)
        for dimension in EXPECTED_UNCERTAINTY_SURFACE_FIELDS:
            consequential = copy.deepcopy(original)
            direct = next(
                case for case in consequential["scope_calibration"]
                if case["id"] == "trivial-visual-correction"
            )
            direct["observed"]["uncertainty_surface"][dimension] = True
            direct["observed"]["material_uncertainty"] = [
                f"authored uncertainty in {dimension}"
            ]
            failures, _, _ = runner.scope_calibration_contract(
                consequential, skill_text, exploration_text
            )
            self.assertTrue(
                any("flattened below Portfolio" in failure for failure in failures),
                (dimension, failures),
            )

        for reference in runner.DIRECT_BROAD_REFERENCES:
            broadened = copy.deepcopy(original)
            direct = next(
                case for case in broadened["scope_calibration"]
                if case["id"] == "trivial-visual-correction"
            )
            direct["expected"]["skipped_references"].remove(reference)
            direct["expected"]["loaded_references"].append(reference)
            failures, _, _ = runner.scope_calibration_contract(
                broadened, skill_text, exploration_text
            )
            self.assertTrue(
                any("Direct route loaded broad references" in failure for failure in failures),
                (reference, failures),
            )

        for case in original["scope_calibration"]:
            if case["expected"]["skipped_references"]:
                widened_route = copy.deepcopy(original)
                mutated = next(
                    item for item in widened_route["scope_calibration"]
                    if item["id"] == case["id"]
                )
                reference = mutated["expected"]["skipped_references"].pop(0)
                mutated["expected"]["loaded_references"].append(reference)
                failures, _, _ = runner.scope_calibration_contract(
                    widened_route, skill_text, exploration_text
                )
                self.assertTrue(
                    any("reference route diverges" in failure for failure in failures),
                    (case["id"], reference, failures),
                )
            for skipped_process in case["expected"]["skipped_process"]:
                activated = copy.deepcopy(original)
                mutated = next(
                    item for item in activated["scope_calibration"]
                    if item["id"] == case["id"]
                )
                mutated["expected"]["skipped_process"].remove(skipped_process)
                failures, _, _ = runner.scope_calibration_contract(
                    activated, skill_text, exploration_text
                )
                self.assertTrue(
                    any(
                        "process activation or omission" in failure
                        for failure in failures
                    ),
                    (case["id"], skipped_process, failures),
                )

            for artifact in case["expected"]["artifacts"]:
                weakened = copy.deepcopy(original)
                mutated = next(
                    item for item in weakened["scope_calibration"]
                    if item["id"] == case["id"]
                )
                mutated["expected"]["artifacts"].remove(artifact)
                failures, _, _ = runner.scope_calibration_contract(
                    weakened, skill_text, exploration_text
                )
                self.assertTrue(
                    any("artifact contract diverges" in failure for failure in failures),
                    (case["id"], artifact, failures),
                )

            global_ceremony = (
                "Every task must run architecture, research, candidates, assets, and motion."
            )
            contract_labels = {
                "artifacts": "artifact",
                "stop_evidence": "stop evidence",
                "escalation_evidence": "escalation evidence",
            }
            for field in ("artifacts", "stop_evidence", "escalation_evidence"):
                contradicted = copy.deepcopy(original)
                mutated = next(
                    item for item in contradicted["scope_calibration"]
                    if item["id"] == case["id"]
                )
                if field == "artifacts":
                    mutated["expected"][field] = [global_ceremony]
                else:
                    mutated["expected"][field] = global_ceremony
                failures, _, _ = runner.scope_calibration_contract(
                    contradicted, skill_text, exploration_text
                )
                self.assertTrue(
                    any(
                        f"{contract_labels[field]} contract diverges" in failure
                        for failure in failures
                    ),
                    (case["id"], field, failures),
                )

        for trace in original["progressive_disclosure"]:
            changed_routes = copy.deepcopy(original)
            mutated = next(
                item for item in changed_routes["progressive_disclosure"]
                if item["id"] == trace["id"]
            )
            reference = mutated["not_needed"].pop(0)
            mutated["needed"].append(reference)
            failures, _ = runner.progressive_disclosure_contract(
                changed_routes, skill_text
            )
            self.assertTrue(
                any("progressive route diverges" in failure for failure in failures),
                (trace["id"], reference, failures),
            )

            contradicted_reason = copy.deepcopy(original)
            mutated = next(
                item for item in contradicted_reason["progressive_disclosure"]
                if item["id"] == trace["id"]
            )
            mutated["reason"] = (
                "Every task must preload the entire reference library and run every workflow."
            )
            failures, _ = runner.progressive_disclosure_contract(
                contradicted_reason, skill_text
            )
            self.assertTrue(
                any("progressive route reason diverges" in failure for failure in failures),
                (trace["id"], failures),
            )

    def test_target_discovery_cannot_treat_filename_miss_as_absence(self):
        for path in (SKILL, EXPLORATION):
            text = path.read_text(encoding="utf-8").lower()
            with self.subTest(path=path):
                self.assertIn("user-supplied", text)
                self.assertIn("file content", text)
                self.assertIn("manifest", text)
                self.assertIn("filename miss", text)
                self.assertIn("not absence evidence", text)

    def test_delivery_contract_is_depth_proportional(self):
        result = load_runner().evaluate()
        traces = {trace["id"]: trace for trace in result["scope_traces"]}
        direct = set(traces["trivial-visual-correction"]["route"]["delivery"])
        self.assertEqual(direct, load_runner().DIRECT_DELIVERY)
        self.assertTrue(
            direct.isdisjoint(
                {
                    "chosen architecture and thesis",
                    "strongest rejected alternative",
                    "external evidence that changed the outcome, if any",
                    "asset and motion decisions when live",
                }
            )
        )
        self.assertEqual(
            set(traces["shared-owner-component-symptom"]["route"]["delivery"]),
            load_runner().FOCUSED_DELIVERY,
        )
        self.assertEqual(
            set(traces["open-journey-architecture"]["route"]["delivery"]),
            load_runner().PORTFOLIO_DELIVERY,
        )

        delivery = SKILL.read_text(encoding="utf-8").split("## Delivery", 1)[1]
        for marker in ("**Direct:**", "**Focused:**", "**Portfolio:**"):
            self.assertIn(marker, delivery)
        self.assertIn("do not invent fields for work that was responsibly skipped", delivery)

        runner = load_runner()
        original = json.loads(SCENARIOS.read_text(encoding="utf-8"))
        injected = SKILL.read_text(encoding="utf-8") + (
            "\nReport architecture, rejected alternatives, research, assets, and motion for every task.\n"
        )
        failures, _, _ = runner.scope_calibration_contract(
            original, injected, EXPLORATION.read_text(encoding="utf-8")
        )
        self.assertTrue(
            any("unscoped or missing process obligation" in failure for failure in failures),
            failures,
        )

        extra_heading = SKILL.read_text(encoding="utf-8") + (
            "\n## Global delivery obligations\n\nReport Portfolio ceremony for every task.\n"
        )
        failures, _, _ = runner.scope_calibration_contract(
            original, extra_heading, EXPLORATION.read_text(encoding="utf-8")
        )
        self.assertTrue(
            any("unscoped or missing process obligation" in failure for failure in failures),
            failures,
        )

        expanded_portfolio = SKILL.read_text(encoding="utf-8").replace(
            "and remaining unknowns.\n",
            "and remaining unknowns. Report this complete record for every task.\n",
        )
        failures, _, _ = runner.scope_calibration_contract(
            original, expanded_portfolio, EXPLORATION.read_text(encoding="utf-8")
        )
        self.assertTrue(
            any("unscoped or missing process obligation" in failure for failure in failures),
            failures,
        )

    def test_operative_route_documents_reject_contradictory_ceremony(self):
        runner = load_runner()
        original = json.loads(SCENARIOS.read_text(encoding="utf-8"))
        skill_text = SKILL.read_text(encoding="utf-8")
        exploration_text = EXPLORATION.read_text(encoding="utf-8")

        mutations = (
            (
                "exploration direct route",
                skill_text,
                exploration_text.replace(
                    "Do not open a packet, broad research, candidate set, architecture exercise, asset/motion exploration, or evaluation route.",
                    "Open a packet, broad research, candidate set, architecture exercise, asset/motion exploration, and evaluation route for every Direct task.",
                    1,
                ),
            ),
            (
                "skill no-preload route",
                skill_text.replace(
                    "Load only the references whose decision is active. Do not preload the library, and do not follow a nested link merely because another reference mentions that domain.",
                    "Preload the entire library for every task.",
                    1,
                ),
                exploration_text,
            ),
            (
                "global ceremony before delivery",
                skill_text.replace(
                    "## Delivery",
                    "Every task must run architecture, broad research, candidates, assets, and motion.\n\n## Delivery",
                    1,
                ),
                exploration_text,
            ),
            (
                "global ceremony before calibration",
                skill_text.replace(
                    "## Calibrate Consequence and Change Surface",
                    "Every task must run architecture, broad research, candidates, assets, and motion.\n\n## Calibrate Consequence and Change Surface",
                    1,
                ),
                exploration_text,
            ),
            (
                "exploration inquiry depth",
                skill_text,
                exploration_text.replace(
                    "Use when the change is narrow, the system is coherent, and the answer is learned or accepted after owner/dependency inspection. Examples: repair focus, add a known state, correct a close icon, extend a tokenized component. A one-component symptom with a shared owner belongs in Focused, not Direct.",
                    "Every Direct task must run architecture, broad research, candidates, assets, and motion.",
                    1,
                ),
            ),
            (
                "design-loop depth model",
                skill_text.replace(
                    "Build the smallest useful model for the calibrated depth. The dimensions below are a depth-scoped menu, not a universal checklist:",
                    "Build the whole-journey model for every task.",
                    1,
                ),
                exploration_text,
            ),
            (
                "design-loop proof route",
                skill_text.replace(
                    "### 8. Render, Critique, Learn (the affected state for Direct; affected comparisons for Focused; required proof slices for Portfolio)",
                    "### 8. Render, Critique, Learn (full designer evaluation for every task)",
                    1,
                ),
                exploration_text,
            ),
            (
                "skill focused implementation contract",
                skill_text.replace(
                    "Focused does not require an experience/architecture thesis, site scope/navigation/page jobs, whole-journey model, visual identity carrier, or unrelated asset/motion roles.",
                    "Focused must freeze the complete architecture, visual, asset, and motion contract for every task.",
                    1,
                ),
                exploration_text,
            ),
            (
                "exploration candidate scope",
                skill_text,
                exploration_text.replace(
                    "Candidate directions and whole-journey candidate records are Portfolio-only unless calibration explicitly escalates.",
                    "Every Focused task must create whole-journey candidate records before implementation.",
                    1,
                ),
            ),
            (
                "exploration durable journal scope",
                skill_text,
                exploration_text.replace(
                    "Only Portfolio records the accepted whole-experience design in the full implementation contract and durable decision journal.",
                    "Every Focused task records the accepted whole-experience design in a durable decision journal.",
                    1,
                ),
            ),
            (
                "exploration stop scope",
                skill_text,
                exploration_text.replace(
                    "Direct stops when the affected invariant is proved; Focused stops when the affected decision and sibling-system proof are closed; Portfolio stops when its whole-journey uncertainty and required proof slices are closed.",
                    "Every task stops only after whole-journey uncertainty and all candidate proof slices are closed.",
                    1,
                ),
            ),
            (
                "exploration proof-slice scope",
                skill_text,
                exploration_text.replace(
                    "The slice examples below are Portfolio-oriented when they describe a journey, topology, or opening composition. Direct and Focused select only the example that can invalidate their affected invariant or decision.",
                    "Every Focused task must prototype a site map, navigation transition, and opening composition.",
                    1,
                ),
            ),
            (
                "exploration convergence scope",
                skill_text,
                exploration_text.replace(
                    "Direct and Focused apply only the criteria relevant to the affected invariant or decision. Portfolio applies the whole set when its material uncertainty requires it; architecture/content resilience and full identity/asset/motion criteria are not mandatory for an unrelated Focused correction.",
                    "Every Focused task must apply the complete architecture, identity, asset, and motion criteria.",
                    1,
                ),
            ),
            (
                "exploration reopen scope",
                skill_text,
                exploration_text.replace(
                    "Apply the reopen triggers below only when they reach the calibrated change surface. A whole-journey, architecture, or unrelated asset/motion trigger is an escalation signal, not a new Focused obligation.",
                    "Every Focused task must reopen the full journey and all asset/motion decisions for any rendered change.",
                    1,
                ),
            ),
            (
                "skill implementation scope",
                skill_text.replace(
                    "Implementation stays at the calibrated change surface. Only Portfolio implementation spans the whole architecture when its uncertainty requires it; Direct and Focused preserve the accepted system outside the affected owner/flow and its proof contexts.",
                    "Every implementation must span the whole architecture and accepted system.",
                    1,
                ),
                exploration_text,
            ),
        )
        for label, mutated_skill, mutated_exploration in mutations:
            failures, _, _ = runner.scope_calibration_contract(
                original, mutated_skill, mutated_exploration
            )
            self.assertTrue(
                any("scoped contract" in failure for failure in failures),
                (label, failures),
            )

        free_form = copy.deepcopy(original)
        free_form["scope_calibration"][0]["task"] = (
            "Every task must run architecture, research, candidates, assets, and motion; "
            "this caller phrase is evidence, not a route instruction."
        )
        failures, _, _ = runner.scope_calibration_contract(
            free_form, skill_text, exploration_text
        )
        self.assertEqual(failures, [])

        benign_prose = exploration_text + (
            "\n\nA non-operative evidence note may mention architecture, research, candidates, assets, and motion as trade-off vocabulary.\n"
        )
        failures, _, _ = runner.scope_calibration_contract(
            original, skill_text, benign_prose
        )
        self.assertEqual(failures, [])

    def test_uncertainty_surface_is_independent_of_runner_vocabulary(self):
        runner = load_runner()
        self.assertEqual(EXPECTED_UNCERTAINTY_SURFACE_FIELDS, runner.UNCERTAINTY_SURFACE_FIELDS)
        skill = SKILL.read_text(encoding="utf-8")
        for phrase in (
            "user goals",
            "topology",
            "journey",
            "content/object relationships",
            "interaction contracts",
            "responsive transformations",
            "system contracts",
        ):
            self.assertIn(phrase, skill)


if __name__ == "__main__":
    unittest.main()
