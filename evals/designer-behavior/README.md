# Snowe Deterministic Designer-Contract Evaluation

This runner checks whether Snowe's deterministic packet and repository contracts preserve open design decisions and epistemic boundaries. It does not invoke Codex, another model, or a skill host, so it cannot establish that Snowe changes how an agent frames or selects design. It deliberately has no creativity or taste score.

## Deterministic contract boundary

Run:

```text
python evals/designer-behavior/run_eval.py
```

The runner checks raw decision packets for:

- English/Russian equivalence, mixed-language input, ambiguous terms, and unknown-domain behavior;
- stable framing under small paraphrases and changed pressures under explicit business changes;
- premature layout/style/type/palette selection;
- automatic imagery or motion;
- caller declarations being rewritten by a hidden taxonomy;
- local evidence being retrieved without opt-in or changing reasoning when absent;
- coherent-system preservation;
- task-specific progressive-disclosure traces;
- reintroduction of classifier tables or obsolete recipe datasets.

These are deterministic contract checks, not observed agent behavior or aesthetic certification. A `KEEP` means the generated packet and repository fixtures preserve the asserted boundary; it does not mean an interface is good or that an agent followed the route.

## Authored progressive-disclosure fixtures

The scenarios declare references that are causally relevant for representative work:

| Task | Needed | Intentionally not loaded |
|---|---|---|
| Restore focus after an existing dialog closes | `quality-gates.md` | architecture, imagery, motion, designer evaluation |
| Reorganize a municipal permit journey | exploration + experience architecture | iconography, imagery, motion |
| Decide whether a dense warehouse workspace needs imagery | imagery/assets until no image wins | iconography, motion, designer evaluation |
| Choose a familiar close glyph in an existing family | iconography | imagery, art direction, architecture |
| Compare rendered products for unexplained repetition | designer evaluation | CLI retrieval, iconography |

The runner verifies that every declared fixture has a reason, a small relevant set, and no overlap between needed and excluded references. It does not run an agent or observe actual file loading. It does not reward a minimum file count; relevance is the boundary.

## Rendered and browser regression evidence

For implementation forward-tests, preserve the full trace: brief, verified facts, research, causal decisions, materially different candidates, strongest rejected alternative, implementation contract, working UI, wide/pressure/narrow captures, important states, findings, corrections, and rerenders.

Use `KEEP | REVISE | REJECT | UNKNOWN` findings from `skill/snowe-ui-skill/references/designer-evaluation.md`. Compare scenarios side by side for repeated topology, hero/section rhythm, navigation, conversion, visual carrier, type voice, palette behavior, imagery posture, custom assets, and motion grammar. Similarity is a failure only when it lacks independent causal support; superficial variation is not diversity.

Goodturn, Doppler, and the municipal, warehouse, and literary forward-tests provide the rendered layer. Their design records, QA, captures, and cross-benchmark comparison live under `benchmarks/` rather than inside the installable skill. Browser smoke verifies known runtime, interaction, focus, responsive, asset, and reduced-motion states; neither layer attributes causation to Snowe or proves generalization.

## Observed real-agent behavior

No reproducible observed-agent evaluation is currently committed. A future claim in this layer must record the exact prompt, target repository commit, model and reasoning configuration, tool access, references actually loaded, output and rendered result, repeated-run variance, and an appropriate no-Snowe or alternate-workflow control. Until then, the deterministic and rendered layers must not be described as causal model evidence.
