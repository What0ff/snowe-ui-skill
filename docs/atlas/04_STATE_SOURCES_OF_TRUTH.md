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

- `design-intelligence/<project>/PROJECT.json` — atomic source of exact printable project identity for the slug;
- `design-intelligence/<project>/BRIEF.md` — replaceable current inquiry;
- `design-intelligence/<project>/DECISIONS.md` — durable create-once accepted-decision ledger;
- `design-intelligence/<project>/CORRECTIONS.json` — optional schema-1 checked correction history, written only by explicit journal commands;
- `design-intelligence/<project>/pages/<page>.md` — identity-bound replaceable open page inquiry.

The exact explicit project/page identities own slug claims; a Windows-reserved or different identity that normalizes to the same slug is rejected, not permission to overwrite. Windows 8.3 names are expanded to a shared long lexical spelling without resolving reparse targets, then both spellings are rechecked before lexical containment, locking, or writes. A short-lived per-project lock serializes claims and recovery. The generator owns atomically replaceable inquiry files only after identity preflight and immediate parent revalidation. Existing `DECISIONS.md` owns accepted evidence and is preserved byte-for-byte. Explicit current requirements or verified evidence can supersede it only through an explicit `SUPERSEDED` record.

## Repository evaluation state

Correction memory is scoped caller-declared project evidence checked by `corrections.py`. `locked_project_state` reuses the existing identity/lock infrastructure without generating a packet. Records retain source/requirement/scope/criteria, lifecycle snapshots and exact source/artifact hashes. Definition/proof integrity is checked before active owner/route/state filtering. Changed definitions retain their last recorded/most recently verified applicability; source/artifact changes and unbound old confirmations also make prior verification REVIEW_REQUIRED. Supersession chains retain their obligations. Read-only checks never rewrite history. The tool checks recorded proof integrity, never aesthetic truth or automatic user preferences.

- `evals/designer-behavior/scenarios.json` is deterministic scenario/route-fixture input; `run_eval.py` is the packet/repository/scope-contract runner; `EVIDENCE-AUDIT.md` is the legacy-field decision record. None is observed real-agent evidence.
- `evals/designer-behavior/HOST-PROBES.md` is bounded observed-host evidence for explicitly recorded GPT-5.6 Luna/max tasks, tool/context conditions, task/diff fingerprints, loaded references, process depth, timing, and uncertainty. It is not deterministic runner output, a transcript, a representative model sample, or causal proof.
- `evals/icon-decisions/manifest.json`, exact local SVG/metadata/license files, and deterministically generated `comparison.html` are operational icon-decision evidence. The manifest owns the selected/rejected human judgment; validators own only structure, exact-byte/declared-metadata/context binding, and comparison consistency; browser smoke owns route/selector/label/viewport/state reachability, exact local candidate rendering, and containment. The benchmark HTML/CSS remains implementation truth.
- `evals/visual-acceptance/fixture.html` owns the deliberately static A/B/C presentations. `captures/geometry.json` binds current source/image hashes and actual CDP viewport measurements; the JPEGs and README preserve inspectable evidence and the bounded paired review. `tests/test_visual_acceptance.py` checks evidence identity/geometry only. Neither the capture command nor the review establishes generated-design improvement or functional behavior.
- `evals/correction-transfer/` owns a separate static A/B/C icon-backing fixture, scoped user-correction task and nine similarly hash-bound captures. Its README records implementer self-review and counterexample reasoning only; an interrupted independent review is not used as proof. The same evidence suite rejects stale-source reuse.
- `benchmarks/bicycle-commerce/{index.html,styles.css,app.js}` are Goodturn implementation truth; its `design-intelligence/`, assets, and screenshots preserve design/rendered evidence. Its exchange mark is now a pinned Lucide Repeat2 SVG with exact external provenance/license metadata; the product-specific fit mark remains original custom work and is the custom-wins case in the operational icon proof.
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
- If project/page identity and a normalized slug disagree, reject the write; do not infer that similar labels denote the same project or page. A torn project manifest is recoverable only through the bounded source-verified path implemented by persistence.
- If screenshots/QA contradict current HTML/CSS/JS, implementation is current truth and visual evidence must be rerendered.
- If cross-benchmark comparison finds similarity without causal justification, change the decision mechanism and rerun affected benchmarks; do not add cosmetic anti-template rules.
- Structural SVG validation and exact-byte metadata binding cannot establish source/license truth or override a weak rendered icon; real-context optical review can reject a structurally valid custom asset, keep a compatible existing glyph, or keep no icon.

There is no database, browser storage, network cache, queue or shared memory service in the installable product. Correction journals are local identity-bound files; legacy installation migration is repository-only tooling.

Typography role expectations are separately authored in `evals/typography/goodturn.json`; tests do not derive them from the current page. `evals/acceptance-cases` owns the six fictional before/after tasks and capture/hash evidence; `memory-check.json` records a scoped lifecycle self-review. Installer migration manifests live outside discovery alongside preserved legacy trees and identify exact archived bytes.

`evals/titlebot-hierarchy` owns its inspected source snapshot, pre-component page map, distinct local fixtures and functional pilot. `captures/evidence.json` binds source/runner/image bytes and states. `REVIEW.json` binds the separately authored visual review to that evidence manifest; user acceptance remains unconfirmed. `scripts/ui-proof.mjs` owns sampled declared-role/action checks, not business inference or aesthetic judgment. The production Title Bot is outside the edited/certified scope.

Attention contracts are separately authored expectations. A visual report owns explicit reviewer judgments and source/render bindings; it is not the authority for whether its own pixels are good. `visual_review.py` verifies recorded consistency and freshness only. `evals/titlebot-hierarchy/review-history/` preserves the former schema-1 report; its current schema-2 review is an explicit scoped reassessment. `evals/visual-judgment/ATTENTION.json`, captures and four reports preserve the same-content state comparison, including intended negative examples with technical PASS and visual REVISE. User acceptance remains unconfirmed.
