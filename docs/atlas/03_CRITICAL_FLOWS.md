# Critical Execution Flows

## 1. Agent design workflow

**Trigger:** a compatible host activates `skill/snowe-ui-skill/SKILL.md`.

1. Route only to references relevant to the live decision and choose Direct, Focused, or Portfolio depth.
2. Establish verified business/user/product/content/platform truth and preserve existing coherent decisions when the task is evolutionary.
3. Open material causal decisions; for new experiences synthesize whole-journey/site/page architectures before art direction.
4. Compare structurally or perceptually meaningful candidates with real content and prototype risky slices.
5. Decide whether imagery, generated assets, custom graphics, icons, and motion exist; absence remains a valid result.
6. Freeze an implementation contract, build in the real target architecture, and preserve UX/accessibility invariants.
7. Render narrow, pressure, and wide states; exercise real interactions; record `KEEP | REVISE | REJECT | UNKNOWN`; correct material weakness and reopen upstream decisions when necessary.

**End state:** an evidence-backed implementation and design record. Skill prose or a packet alone is not completion.

## 2. Explicit evidence search

**Trigger:** `python skill/snowe-ui-skill/scripts/search.py "<query>" --domain <domain>`.

1. `search.py` rejects missing or conflicting modes; no automatic domain fallback exists.
2. `CSV_CONFIG` resolves the exact caller-selected file/search/output headers.
3. `_load_csv` reads UTF-8 CSV and `_search_csv` builds/ranks an in-memory BM25 corpus.
4. Icon-family/subject constraints and legacy icon-row filtering run where applicable.
5. The result receives `source_role` and `warning`, then prints as bounded text or JSON.

**End state:** advisory lexical evidence is printed; no state/cache is written and no framing changes.

## 3. Stack search

**Trigger:** the CLI receives `--stack <stack>`.

The CLI excludes domain/packet mode. `core.search_stack` loads one configured stack catalog, ranks shared headers, and adds a stack evidence role, a current-primary-source warning, and returned-row `Docs URL` coverage before printing bounded text or JSON.

**End state:** one advisory implementation snapshot is returned without writes or dependency installation; missing URLs and the limits of present URLs remain explicit.

## 4. Unresolved decision packet

**Trigger:** `--decision-packet` (or compatibility alias `--design-system`) or `generate_decision_packet`.

1. Preserve the brief exactly; do not detect language, translate, classify vocabulary, infer work mode/platform, or derive pressures.
2. Normalize only caller-supplied declarations and pass through free-form fields/pressures.
3. Emit generic pressure questions and unknowns, explicitly favoring unresolved framing over false confidence.
4. Emit research triggers with activation questions and stop conditions; brief terms do not activate them automatically.
5. If and only if the caller supplies `analog_query`, run lexical product retrieval, limit results to three, label each `UNVERIFIED_ANALOG`, and keep absence non-consequential.
6. Emit open architecture, art-direction, asset, motion, responsive, and evaluation contracts in Markdown or JSON.

**End state:** a causal workbench is printed. No domain, layout, style, type, palette, image, icon family, or motion result is selected.

## 5. Decision-intelligence persistence

**Trigger:** `--decision-packet --persist [--page ...] [--output-dir ...]`.

1. CLI constraints reject persistence/page/output flags outside packet mode.
2. Project/page names are slugged and resolved beneath the requested output root.
3. `BRIEF.md` is regenerated.
4. `DECISIONS.md` is exclusive-created; an existing ledger is reported as preserved.
5. A requested page inquiry is written beneath `pages/` without page-type/section-order selection.

**End state:** replaceable inquiry plus durable accepted decisions; there is no multi-file transaction or lock.

## 6. Low-level validators

- `asset_quality.py <svg> --metadata <json>` parses both files; requires specific non-placeholder provenance/drawing-language metadata, a grid matching a finite positive `viewBox`, and unique positive targets; rejects active/embedded/style elements, inline styles, handlers, `xml:base`, unsafe declarations, non-local URI/CSS references, and invalid monochrome paint; and returns an optical-QA warning even on structural pass.
- `contrast.py <foreground> <background> [--minimum N]` parses exact opaque CSS colors, computes relative luminance/ratio, and returns `PASS` or `FAIL`.

These are deterministic structural evidence, not rendered design approval.

## 7. Behavioral and rendered evaluation

`python evals/designer-behavior/run_eval.py` loads deterministic equivalence, ambiguity, delta, preservation, discretion, dataset-absence, and authored progressive-disclosure scenarios. It rejects hidden classification, automatic assets/motion, recipe keys, or obsolete datasets; it never invokes a model/host, observes reference loading, or scores creativity/layout/style.

Rendered proof has five implementations:

- Goodturn image-led bicycle commerce;
- Doppler expressive-motion soda campaign;
- Larkhaven public-service journey;
- Relay North keyboard-first warehouse workspace;
- Morrow typographic editorial issue.

Each new forward-test includes causal decisions, a strongest rejected alternative, responsive transforms, live interactions, QA, and six screenshots. `benchmarks/CROSS-BENCHMARK.md` audits unexplained repetition.

`node scripts/browser-smoke.mjs --smoke` serves the repository, launches system Chrome/Chromium through CDP, and checks wide/intermediate/mobile states, runtime/console/network failures, assets, semantics, overflow, benchmark-specific interactions/focus, mobile navigation, and reduced motion. `--capture` regenerates the 18 forward-test JPEGs.

## 8. Public contributor-context maintenance

**Trigger:** a change affects repository structure, contributor guidance, architecture claims, validation contracts, or ignore rules.

1. Root `AGENTS.md` routes the contributor through the public atlas and treats any `.codex/CURRENT_TASK.md` checkpoint as optional local state.
2. `.agents/skills/atlas-maintainer/SKILL.md` scopes documentation review to claims the final diff could invalidate.
3. `scripts/atlas/generate_atlas.py` derives `repo-map.md` from tracked files plus nonignored candidate additions, so ignored local files cannot affect generated public context.
4. `scripts/check_contributor_context.py` verifies required public paths, public/private ignore behavior, non-tracking of private path classes, and optional-checkpoint language.
5. Structural changes run atlas `--write`; every completed implementation runs atlas `--check`.

**End state:** the public candidate is self-contained and reproducible from a fresh clone, while task/session state remains local.

## 9. CI validation and Pages publication

GitHub Actions runs four independent surfaces:

1. strict contributor-context validation plus atlas freshness on Ubuntu/Python 3.13;
2. `compileall` plus all unittests on Python 3.11/3.13, Ubuntu/Windows;
3. the designer-behavior runner on Ubuntu/Python 3.13;
4. the dependency-free browser smoke on Ubuntu and Windows/Node 22/system Chrome.

CI does not perform aesthetic certification, manual browser review, lint/format/type/coverage, packaging, deployment, or release publication.

The independent `.github/workflows/pages.yml` path-filtered workflow uploads `benchmarks/soda-campaign/` as the GitHub Pages artifact root and deploys it through the `github-pages` environment. It runs only for Doppler/workflow changes or manual dispatch, does not replace or alter the three normal CI surfaces, and adds no benchmark build step.
