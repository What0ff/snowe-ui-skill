# Creative-search generation pilot

Repository-only, opt-in real-agent evaluation. It is outside the installed skill and normal CI does not invoke a model. The subject host is the locally authenticated Codex CLI with inherited model/reasoning/tool configuration; no model override is made. Node 22 and system Chrome/Edge are needed for the separate portable capture step.

## Frozen design

`briefs.json` was written and the complete baseline product copied before the creative-search revision. Three fictional briefs cover radio restoration, a textile exhibition and a repeated-use marina workspace. Page jobs, factual content and actions are settled, while composition is open. Two briefs request distinct character; the utility brief does not. No expected palette, metaphor, layout, imagery or candidate count is encoded.

Use two repetitions per condition as a small pilot. Alternate baseline/candidate order across repetitions; preserve all failures. Every subject receives the same case prompt and a fresh neutral temporary workspace, only its selected complete local skill, and no other run or intended answer. Offline/self-contained assets are a controlled limitation. Global host metadata may still expose installed skill names; inspect actual command/reference traces for use of the wrong copy. These runs measure this configured host, not all models.

Before reviewing, compare at 1440/820/390 with identical case facts. Record source/reference loading, actual candidates, rendered comparisons, process depth, time and exposed token usage. Inspect factual/action completeness, default and important interactive states, responsive fit, typography/detail and invented carrier coherence. Compare same-case renders under neutral labels before exposing condition and rationale. A fresh model review is labelled model review, separate from the implementer's visual self-review and user acceptance. Reviewer preference is not an automatic beauty score.

Success requires an observed useful difference in the finished artifact; longer explanations or more candidates alone do not qualify. Distinctive tasks may benefit from product-specific invention, while added decoration or unnecessary work in the utility case counts against the change. A severe factual, task or responsive regression blocks acceptance. Ties, disagreements and unavailable proof remain visible. Two repetitions per brief cannot establish population-level improvement.

## Commands

Before editing product methodology:

```powershell
python evals/creative-search/run_pilot.py snapshot work/creative-search-pilot/baseline
```

After editing, create the candidate snapshot, then run each case and repetition with fresh destinations. The generation command invokes a real model and may take several minutes; tests do not.

```powershell
python evals/creative-search/run_pilot.py snapshot work/creative-search-pilot/candidate
python evals/creative-search/run_pilot.py generate work/creative-search-pilot/baseline radio-workshop 1 work/creative-search-pilot/runs/b-radio-1
python evals/creative-search/run_pilot.py capture work/creative-search-pilot/runs/b-radio-1
python evals/creative-search/run_pilot.py check work/creative-search-pilot/runs/b-radio-1
```

`snapshot` also accepts `--source <skill-dir>` (freeze another skill copy), `--briefs <file>` (freeze another case set, plus its sibling `seeds/` directory) and `--no-skill` (a control with no skill copy and a skill-free prompt; `generate` refuses it while a global Snowe installation is discoverable). [../skill-outcome](../skill-outcome/README.md) uses these for the no-skill / before / after comparison. `snapshot.json` binds all skill files and frozen briefs. `run.json` retains status, exact prompt/source bindings, elapsed time and usage actually exposed by completed-turn events. Raw CLI output, notes, the final response and the unchanged site are retained locally. Capture failures preserve the log; post-run artifact changes invalidate checking. Technical capture integrity never implies a visual verdict. Raw host context and generated artifacts stay under ignored `work/`; durable summarized evidence and its limitations belong in this directory.

Unit checks: `python -m unittest discover -s tests -p test_creative_pilot.py -v`.

## Recorded pilot

[REPORT.md](REPORT.md) summarizes the 2026-10-09 twelve-generation pilot, masked model reviews, reproduced stale-preview failure, scoped repair evidence and final guidance amendments. [results.json](results.json) preserves reported timing/usage, source/prompt/capture fingerprints, review findings and practical limits. The local raw evidence and viewer are optional ignored state; they are not a public-clone prerequisite.
