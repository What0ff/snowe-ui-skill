# Snowe Designer-Behavior Evaluation

This evaluation asks whether Snowe changes how it frames and selects design, not whether generated prose contains expected rules. It deliberately has no creativity or taste score.

## Automated boundary

Run:

```text
python evals/designer-behavior/run_eval.py
```

The runner checks raw decision packets for:

- contextual signal collisions;
- premature layout/style/type/palette selection;
- automatic imagery or motion;
- local datasets escaping their `UNVERIFIED_ANALOG` role;
- suspiciously identical pressure profiles across deliberately different scenarios.

These are behavioral contracts, not aesthetic certification. A `KEEP` means the packet leaves a causal design space open and identifies the scenario pressure; it does not mean an interface is good.

## Rendered evaluation

For implementation forward-tests, preserve the full trace: brief, verified facts, research, causal decisions, materially different candidates, strongest rejected alternative, implementation contract, working UI, wide/pressure/narrow captures, important states, findings, corrections, and rerenders.

Use `KEEP | REVISE | REJECT | UNKNOWN` findings from `skill/snowe-ui-skill/references/designer-evaluation.md`. Compare scenarios side by side for repeated topology, hero/section rhythm, navigation, conversion, visual carrier, type voice, palette behavior, imagery posture, custom assets, and motion grammar. Similarity is a failure only when it lacks independent causal support; superficial variation is not diversity.

The bicycle-commerce benchmark is the first complete rendered evaluation. Its design record and QA evidence live with the benchmark rather than in this harness.
