# State and Sources of Truth

## Authority order

For design work:

1. Explicit requirements plus verified repository, product, brand, content, user, and platform facts.
2. Accepted scoped decisions with evidence/revisit triggers and current rendered/measured behavior.
3. Current primary standards, official assets/packages/platform sources, credible domain research, and real-product observation.
4. Open brief/page inquiry.
5. Caller-selected local evidence as analogs, constraints, counterexamples, and discovery indexes.
6. Generated hypotheses.

For repository behavior: source/configuration wins over tests, tests over `docs/atlas/`, and durable public repository context over conversation recollection or local task notes. Correct this atlas when implementation contradicts it.

## Installable sources

### Procedural design behavior

- **Location:** `skill/snowe-ui-skill/SKILL.md`, `references/*.md`.
- **Consumer:** compatible agent host.
- **Authority:** `SKILL.md` is the core router; specialist references apply only when routed.
- **Boundary:** prose guides judgment but does not become deterministic Python selection.

### Configured CSV evidence

- **Location:** `skill/snowe-ui-skill/data/`.
- **Consumer:** `core.py`; `decision_packet.py` calls only the product domain when an explicit analog query exists.
- **Written by runtime:** never.
- **Authority:** `CSV_CONFIG`/`STACK_CONFIG` and exact headers define live inputs; directory presence does not.
- **Boundary:** explicit caller activation, lexical rank, source role, and warning are mandatory. Results cannot establish current truth or select design.

Each invocation reloads one selected CSV. BM25 tokens, scores, rows, packets, and formatted strings are ephemeral and discarded at process exit.

The absence of deleted recipe catalogs is an intentional source-of-truth decision, not missing data. Field-level rationale is in `evals/designer-behavior/EVIDENCE-AUDIT.md`.

## Optional project state outside the repository

`decision_packet.py` writes beneath the caller-selected root:

- `design-intelligence/<project>/BRIEF.md` — replaceable current inquiry;
- `design-intelligence/<project>/DECISIONS.md` — durable create-once accepted-decision ledger;
- `design-intelligence/<project>/pages/<page>.md` — replaceable open page inquiry.

The generator owns replaceable inquiry files. Existing `DECISIONS.md` owns accepted evidence and is preserved. Explicit current requirements or verified evidence can supersede it only through an explicit `SUPERSEDED` record.

## Repository evaluation state

- `evals/designer-behavior/scenarios.json` is deterministic scenario/route-fixture input; `run_eval.py` is the packet/repository contract runner; `EVIDENCE-AUDIT.md` is the legacy-field decision record. None is observed real-agent evidence.
- `benchmarks/bicycle-commerce/{index.html,styles.css,app.js}` are Goodturn implementation truth; its `design-intelligence/`, assets, and screenshots preserve design/rendered evidence.
- `benchmarks/soda-campaign/{index.html,styles.css,app.js}` are Doppler implementation truth; its six `design-intelligence/` records, local fonts/SVG labels, seven JPEGs, and browser-derived GIF preserve candidate, provenance, motion, and corrected rendered evidence.
- `benchmarks/forward-tests/manifest.json` is the comparison metadata/source for required scenario outcomes and screenshot names.
- Each forward-test's HTML/CSS/JS is implementation truth; `DECISIONS.md` records causal choices; `QA.md` records browser findings/fixes; `screenshots/*.jpg` is final visual evidence.
- `benchmarks/CROSS-BENCHMARK.md` is the manual hidden-template comparison plus expressive-motion companion, not an automated score.
- `scripts/browser-smoke.mjs` is the executable rendered smoke/capture and isolated-profile cleanup contract; it does not certify taste or model causation.
- `.github/workflows/pages.yml` is the public Doppler deployment contract; `benchmarks/soda-campaign/` is its complete artifact root. The Pages API/deployment output is authoritative for the public URL, which the root and benchmark READMEs expose.
- All benchmark businesses and operational/commercial facts are fictional. Goodturn generated imagery and Doppler's code-native product/labels remain benchmark-specific and disclosed; Doppler uses no AI-generated imagery.

## Repository context state

`AGENTS.md`, `CONTRIBUTING.md`, `docs/atlas/`, `scripts/atlas/`, and the allowlisted atlas-maintainer skill are version-controlled repository context. `repo-map.md` is generated solely by `scripts/atlas/generate_atlas.py` from tracked files plus nonignored candidate additions; focused atlas files remain manually curated.

`.codex/CURRENT_TASK.md` is optional ignored active-task state. It can help a maintainer resume local work but is absent from a fresh clone, subordinate to source and public context, and never a required contributor dependency. Conversation-derived memory, handoffs, logs, generated work/output, and non-allowlisted agent configuration have the same private, non-authoritative status.

## Reconciliation rules

- If a CSV header and configuration disagree, runtime follows configuration strings; fix the intended schema/config and add a regression.
- If a retrieved row conflicts with verified evidence, verified evidence wins; the row remains only a bounded snapshot.
- If a new packet conflicts with existing `DECISIONS.md`, do not overwrite the ledger; reconcile explicitly.
- If screenshots/QA contradict current HTML/CSS/JS, implementation is current truth and visual evidence must be rerendered.
- If cross-benchmark comparison finds similarity without causal justification, change the decision mechanism and rerun affected benchmarks; do not add cosmetic anti-template rules.
- Structural SVG validation cannot override a weak rendered icon; optical review can reject a structurally valid asset.

There is no database, migration system, service state, browser storage, environment configuration model, runtime network cache, queue, or shared memory in the installable product.
