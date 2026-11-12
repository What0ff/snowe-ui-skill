# Skill outcome comparison

Repository-only, opt-in real-agent evaluation. It answers one question the earlier pilots could not: **does Snowe improve the finished artifact compared with the same host working without any skill?** Normal CI and unit tests never invoke a model.

## Conditions

| Condition | Snapshot | Meaning |
|---|---|---|
| `no-skill` | `run_pilot.py snapshot <dir> --no-skill --briefs evals/skill-outcome/briefs.json` | Same host, same prompt requirements, no skill copy and an instruction not to use installed skills |
| `before` | `--source` set to the product as of `main` commit `6447ca7` (before the 2026-11-12 audit) | The skill as it was when the audit started |
| `after` | default source (this product) at the commit under test | The revised skill |

The harness is the shared [creative-search runner](../creative-search/run_pilot.py). Every subject gets a fresh temporary workspace, the frozen brief, identical task requirements and, for skill conditions only, its selected skill copy. Seeded cases start from the files under `seeds/<case>/`, copied into `site/`.

**Precondition:** no Snowe copy may be discoverable by the host. `generate` refuses a `no-skill` run while one exists under `~/.agents/skills`, `~/.codex/skills` or `$CODEX_HOME/skills`, and records any copies seen during skill runs. Move a global installation aside for the whole batch and restore it afterwards.

## Frozen briefs

[briefs.json](briefs.json) was written on 2026-11-12, before the audit-driven skill changes, and must not change during a measurement. Each case targets one known weakness without naming a solution:

| Case | What it exposes |
|---|---|
| `clinic-desk` | Secondary tasks (book, reschedule, cancel with fee, patient record) and whether they get appropriate surfaces; loading and save-failure states; on-screen copy |
| `transit-mobile` | Mobile navigation, icon-heavy interface and icon style decisions; purchase failure recovery |
| `energy-monitor` | Live and asynchronous data, an offline building, drill-in detail, layout stability while values change |
| `radio-workshop` | Distinctive authored character (identical to the creative-search brief for continuity) |
| `settings-fix` | Proportionality: a bounded correction in existing code (a clipped menu and a jumping button) must stay a correction |

## Procedure

```powershell
git archive 6447ca7 skill/snowe-ui-skill | tar -x -C work/skill-outcome/main-source
python evals/creative-search/run_pilot.py snapshot work/skill-outcome/snapshots/no-skill --no-skill --briefs evals/skill-outcome/briefs.json
python evals/creative-search/run_pilot.py snapshot work/skill-outcome/snapshots/before --source work/skill-outcome/main-source/skill/snowe-ui-skill --briefs evals/skill-outcome/briefs.json
python evals/creative-search/run_pilot.py snapshot work/skill-outcome/snapshots/after --briefs evals/skill-outcome/briefs.json
python evals/creative-search/run_pilot.py generate work/skill-outcome/snapshots/<condition> <case> <repeat> work/skill-outcome/runs/<condition>-<case>-<repeat>
python evals/creative-search/run_pilot.py capture work/skill-outcome/runs/<run>
python evals/creative-search/run_pilot.py check work/skill-outcome/runs/<run>
```

Run two repetitions per case and condition (30 generations). Rotate condition order between repetitions. Preserve every failed or incomplete run. Raw runs stay under ignored `work/`; summarized results and their limitations belong in this directory.

## Judging, fixed before any run

Reviewers see artifacts under neutral labels, at 1440, 1024 or 820, and 390 px, and interact with them before reading any notes or rationale.

**Primary measure:** blind pairwise preference per case and repetition, `after` versus `no-skill` and `after` versus `before`, by at least one human reviewer (more reviewers are better; record disagreements).

**Secondary checklist** (each item PASS / FAIL / N/A per artifact, judged by the reviewer):

1. Every required task and fact is present and works.
2. Secondary tasks use proportionate surfaces: nothing important is buried, and the main screen is not overloaded with everything inline.
3. Panels, dialogs and controls keep their size when state changes (loading, error, selection, saving, live updates).
4. Visible text helps the user; there are no self-descriptions of the screen, design rationale, internal terms or evaluation notes.
5. Icons are intentional: one coherent style, with a filled or outline choice that fits the role and state.
6. The 390 px and intermediate widths transform deliberately rather than squeeze.
7. `settings-fix` only: both reported problems are fixed and nothing else is redesigned.

**Cost:** elapsed seconds and reported tokens per run, descriptive only.

**Pre-registered reading:** `after` is supported when reviewers prefer it to `no-skill` in at least 7 of 10 pairs and it is not worse than `before` on `settings-fix`. Fewer than that is reported as no demonstrated improvement. Two repetitions, one host and few reviewers cannot establish population-level causation; report what was observed, with ties and failures.
