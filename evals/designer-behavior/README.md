# Snowe Designer-Behavior Evaluation

This evaluation asks whether Snowe changes how it frames and selects design, not whether generated prose contains expected rules. It deliberately has no creativity or taste score.

## Automated boundary

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

These are behavioral contracts, not aesthetic certification. A `KEEP` means the packet preserves epistemic boundaries and leaves causal synthesis open; it does not mean an interface is good.

## Progressive-disclosure probes

The scenarios also record the references that are causally relevant for representative work:

| Task | Needed | Intentionally not loaded |
|---|---|---|
| Restore focus after an existing dialog closes | `quality-gates.md` | architecture, imagery, motion, designer evaluation |
| Reorganize a municipal permit journey | exploration + experience architecture | iconography, imagery, motion |
| Decide whether a dense warehouse workspace needs imagery | imagery/assets until no image wins | iconography, motion, designer evaluation |
| Choose a familiar close glyph in an existing family | iconography | imagery, art direction, architecture |
| Compare rendered products for unexplained repetition | designer evaluation | CLI retrieval, iconography |

The runner verifies that every trace has a reason, a small relevant set, and no overlap between needed and excluded references. It does not reward a minimum file count; relevance is the boundary.

## Rendered evaluation

For implementation forward-tests, preserve the full trace: brief, verified facts, research, causal decisions, materially different candidates, strongest rejected alternative, implementation contract, working UI, wide/pressure/narrow captures, important states, findings, corrections, and rerenders.

Use `KEEP | REVISE | REJECT | UNKNOWN` findings from `skill/snowe-ui-skill/references/designer-evaluation.md`. Compare scenarios side by side for repeated topology, hero/section rhythm, navigation, conversion, visual carrier, type voice, palette behavior, imagery posture, custom assets, and motion grammar. Similarity is a failure only when it lacks independent causal support; superficial variation is not diversity.

Goodturn and the municipal, warehouse, and literary forward-tests provide the rendered layer. Their design records, QA, and cross-benchmark comparison live under `benchmarks/` rather than inside the installable skill.
