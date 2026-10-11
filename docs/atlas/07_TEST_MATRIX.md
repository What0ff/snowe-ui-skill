# Test and Validation Matrix

## Environment

- Installable product/test runtime: Python 3.11+ standard library.
- Repository browser smoke/capture: Node 22 plus system Chrome/Chromium; no npm install; CI covers Ubuntu and Windows.
- Public showcase deployment: GitHub Pages branch `codex/doppler-pages:/`, a Doppler folder snapshot plus `.nojekyll`, with repository Actions disabled. The checked-in custom workflow remains an inactive alternative.
- Working directory: repository root.
- CI covers the strict public contributor-context/atlas contract on Ubuntu/Python 3.13, Python 3.11/3.13 regressions on Ubuntu/Windows, deterministic contracts on Ubuntu/Python 3.13, and browser smoke on Ubuntu/Windows with Node 22.

## Canonical checks

### Runtime compilation

```powershell
python -m compileall -q skill/snowe-ui-skill/scripts
```

Checks installable Python syntax/import compilation. It does not validate Markdown, CSV semantics, aesthetics, browser behavior, or atlas files.

### Full regression suite

```powershell
python -m unittest discover -s tests -v
```

Current inspected result: **250 tests run successfully, with one Windows directory-symlink capability skip**.

- `tests/test_snowe_ui_skill.py`: package routing/docs, schema-3 unresolved framing, multilingual/ambiguity/unknown behavior, opt-in analogs, persistence/path safety, evidence deletion/schemas/claims, icon constraints, contrast, SVG, and CLI.
- `tests/test_bicycle_benchmark.py`: Goodturn commercial content, local/provenanced assets, semantics, interactions, responsive/reduced motion, design trace, and screenshot coverage.
- `tests/test_forward_benchmarks.py`: three causal experience classes, deliberate absences, local semantic implementations, responsive/motion contracts, cross-comparison, completed QA/findings, screenshots, CI historical-checkout coverage, and transition-settled browser commands.
- `tests/test_soda_benchmark.py`: local/semantic product content, flavor/conversion disclosure, motion/responsive/reduced ownership, complete design trace/provenance, local SVG safety, screenshot/GIF evidence, README/live-URL positioning, Doppler smoke contracts, and Pages workflow/artifact-root contracts.
- `tests/test_installation.py`: fresh exact install, stale-file-free reinstall, interrupted-run recovery/preservation, staging-failure cleanup, activation rollback, source/destination containment, exact public CLI copy, and current installation guidance.
- `tests/test_scope_contract.py`: six materially different consequence/change-surface traces; exact reference/process/artifact/stop/escalation/reason mutations; unjustified widening and consequential flattening; high-consequence proof floors; depth-proportional delivery; and target-discovery guidance.
- `tests/test_color_intensity.py`: declared per-role intensity/contrast, full-page/table/modal paint bindings and contextual rejection despite measurable non-neutral colors.
- `tests/test_visual_review.py`: explicit method/verdict distinction, legacy reading, unresolved findings, state coverage, stale contract/source/render, paths, read-only CLI and user disposition.
- `tests/test_visual_judgment_cases.py`: A/B negative judgments versus C/D accepted scoped judgments despite common technical PASS, 24 source-bound renders, and preserved legacy review.
- `tests/test_page_hierarchy.py`: critical page/copy/action routes and removal mutations, isolated pilot source/runner/capture/review bindings, distinct per-title fixture coverage and report-copy boundaries.
- `tests/test_corrections.py`: definition/proof drift, pre-filter scope retention, legacy unbound confirmation, explicit re-verification, invalid structure, identity-bound lifecycle, idempotency/conflicts, scope, required owner/state proof, stale/lost evidence, supersession inheritance, ledger preservation, hardlinks, atomic failure and concurrent records.
- `tests/test_install_migration.py`: identical/differing legacy copies, duplicate diagnostics, post-move rollback, process-death recovery and unsafe targets.
- `tests/test_visual_acceptance.py`: visual-acceptance and correction-transfer fixture/capture hash binding, variant coverage, decoded JPEG width and measured viewport/document geometry, plus rejection of stale-source reuse; no aesthetic assertion.
- `tests/test_icon_workflow.py`: strict SVG grammar/geometry/paint/path safety and resource budgets, structured source/license evidence byte bindings, metadata/provenance/schema boundaries, typed/digest/one-to-one host-state icon manifest binding, actual-owner dialog selection, deterministic comparison regeneration, no-icon behavior, unresolved repository-derived selection rejection, and manifest/asset/output redirection or alias protection.
- `tests/test_runtime_hardening.py`: project/page identity collisions and races, reserved-name/page-preflight/atomic/shared-file/reparse persistence, real Windows 8.3 alias/lock identity and alias-normalization swap probes, retrieval-limit/mode failures, installer ownership/locking/quarantine/recovery, source/staging/activation revalidation, and junction/symlink boundaries.

Focused examples:

```powershell
python -m unittest tests.test_snowe_ui_skill.DecisionPacketTests -v
python -m unittest tests.test_snowe_ui_skill.RetrievalTests -v
python -m unittest tests.test_scope_contract -v
python -m unittest tests.test_icon_workflow -v
python -m unittest tests.test_runtime_hardening -v
python -m unittest tests.test_forward_benchmarks -v
python -m unittest tests.test_bicycle_benchmark -v
python -m unittest tests.test_soda_benchmark -v
```

### Deterministic designer-contract regression

```powershell
python evals/designer-behavior/run_eval.py
```

Current inspected result: **18 `KEEP` findings**, no `REVISE`/`REJECT`. Coverage includes six businesses, English/Russian/mixed equivalence, ambiguous vocabulary, unknown domain, unresolved pressure, paraphrase stability, meaningful business change, coherent-system preservation, no-image/no-motion/custom rejection, dataset absence, progressive disclosure, six authored scope traces, a complete boolean whole-system uncertainty surface, exact per-case reference/process/artifact/stop/escalation and progressive-reason contracts, structurally exclusive depth-proportional delivery, widening/flattening/high-consequence/global-ceremony mutations, and semantic/evidence boundaries. The booleans are authored test evidence, never inferred from task text. Output marks deterministic contracts as measured, rendered/browser regression as separate, and observed real-agent behavior as not measured by this runner. It contains no creativity/layout/style score.

`evals/designer-behavior/HOST-PROBES.md` is the separately inspected bounded host series. It records the exact commit/diff fingerprint, configured GPT-5.6 Luna/max task/context/tools, reference loads, packet/research/candidate activation, implementation/proof depth, and observable timing for a pre-change control and current narrow, shared, medium, high-consequence, unfamiliar-target, and Portfolio work. Tokens and independent runtime self-identity were not observable; the small non-repeated series is not causal or generalization evidence.

### Opt-in creative-search generation pilot

`evals/creative-search/README.md` routes frozen complete baseline/candidate copies, three held-out single-page briefs and repeated real Codex CLI subjects. `run_pilot.py snapshot`, `generate`, `capture` and `check` preserve exact source/prompt bindings, unchanged generated artifacts and exposed usage/time. Generation uses inherited authenticated host configuration; browser capture uses the frozen optional observer with Node 22/system Chrome or Edge. Neither generation nor model judgment is invoked by normal CI.

`python -m unittest discover -s tests -p test_creative_pilot.py -v` tests changed snapshots/briefs/prompts/artifacts, added resources, incomplete runs, raw completed-turn usage and refusal to overwrite evidence without invoking a model. Default captures use 1440/820/390 and reduced motion; important interaction, normal-motion, accessibility and aesthetic claims require separately recorded actual proof. Offline assets and small repetitions bound the pilot.

### Benchmark JavaScript and browser smoke

```powershell
node --check benchmarks/bicycle-commerce/app.js
node --check benchmarks/soda-campaign/app.js
node --check benchmarks/forward-tests/municipal-service/app.js
node --check benchmarks/forward-tests/warehouse-operations/app.js
node --check benchmarks/forward-tests/literary-publication/app.js
node --check scripts/browser-smoke.mjs
node scripts/browser-smoke.mjs --smoke
node scripts/browser-smoke.mjs --smoke --scenario icon-decisions
```

Smoke starts a loopback server and isolated headless Chrome, then exercises all five benchmarks at 1440, 900, and 390 widths; benchmark-specific interactions/focus; mobile navigation open/activation/Escape/breakpoint behavior; broken assets/network/runtime/console errors; horizontal overflow; dialog semantics; and reduced-motion emulation. The icon-decision scenario checks three contexts/eight alternatives, exact comparison dimensions/states, canonical comparison→host mappings, accessible no-icon controls, self-containment, repository-derived source digests/routes/selectors/labels, and every selected/rejected candidate inside its owning host at exact wide/mobile viewports and declared default/hover/focus/disabled/dark/forced-color states as applicable. It polls the opened owning dialog's scoped CSS motion and stable bounds before measuring descendant geometry, preserving the strict final-size assertion without disabling product motion or accepting transition frames. The selected Goodturn dialog X is exercised in the actual `.sheet-close-icon` owner; challengers render in that shell. The Goodturn fit and Larkhaven no-icon choices are also checked as implemented baselines. Doppler additionally checks 48/40/32 product segments, one attached lid layer, keyboard and pointer-drag yaw, synchronized flavor state, front-facing revolution completion, six-pack validation/confirmation, finite animation cleanup, and its authored static reduced mode. Browser shutdown is awaited and temporary-profile removal retries bounded transient locks but remains a hard failure if cleanup cannot complete; aggregated cleanup failures print each underlying process/server/profile cause.

Regenerate the 18 forward-test and seven Doppler captures only after validated visual changes:

```powershell
node scripts/browser-smoke.mjs --capture
node scripts/browser-smoke.mjs --capture-goodturn-workshop
```

For Doppler-only correction/rerender work:

```powershell
node scripts/browser-smoke.mjs --capture-soda
$env:SODA_MOTION_DIR = "<empty-temporary-directory>"
node scripts/browser-smoke.mjs --soda-motion-frames
```

The motion-frame command captures 72 PNGs from the live implementation; it does not define a repository image-encoder dependency or overwrite `hero-motion.gif`.

### Visual acceptance fixture

```powershell
node scripts/browser-smoke.mjs --capture-visual-acceptance
python -m unittest tests.test_visual_acceptance -v
```

This explicit capture route uses the same isolated Chrome/CDP lifecycle to produce nine full-page JPGs for A/B/C at 1280, 820 and 390 CSS widths, preserving the variant query parameter. It verifies actual viewport and document geometry and writes source/image SHA-256 bindings. It does not exercise the fixture's intentionally nonfunctional controls or grade appearance. `evals/visual-acceptance/README.md` records the one paired old/proposed review: both selected C and withheld functional acceptance; the proposed review rejected A more explicitly, without proving better generated design. The rejected preliminary window-size-only capture set is not public regression evidence.

Additional bounded local probes in that README cover stale-source detection, explicit-reference button size/shape conformance, and an expressive-brand generation whose initial typography failed despite no overflow. The reference correction and brand generation were interrupted before their final agent proof reports; parent browser verification/corrections are labelled separately. Live Figma access, repeated generation quality, and complete accessibility certification were not measured.

### Low-level assets

Goodturn's normal browser smoke checks the separately declared role contract in `evals/typography/goodturn.json`: heading/body/card/control, navigation, booking fields and open dialogs at 1440/900/390. It verifies CSS metrics, rendered faces and pinned font-file/face mapping, and rejects mutations of family, weight 400→800, italic, line-height, tracking, variable settings, control inheritance and per-glyph fallback. Font/paint settling precedes inspection; dialog probes are isolated from the interaction suite. These are declared role regressions, not automatic aesthetic or font-engine certification.

The icon comparison additionally checks preview, glyph and text containment within state cells at 1440, 900 and 390 widths. A temporary narrow-column mutation reproduces the original service-copy overflow and must be detected; it is removed before host proof. Document-wide overflow alone is insufficient. Service and labelled-action state rows use their candidate's full available width; compact icon controls retain a state grid.

For scoped correction and backing evidence:

```powershell
node scripts/browser-smoke.mjs --capture-correction-transfer
python -m unittest tests.test_visual_acceptance -v
```

This separate fictional fixture includes pseudo-element icon backings, a radius-only change, below-the-fold repetition, accepted rounded controls and a superseding brand instruction. Nine A/B/C images at 1280/820/390 bind source and actual viewport geometry. Its README records implementer self-review only, with absent behavior and generalization proof explicit; no automated aesthetic score is produced.

```powershell
python skill/snowe-ui-skill/scripts/asset_quality.py `
  benchmarks/bicycle-commerce/assets/icons/fit.svg `
  --metadata benchmarks/bicycle-commerce/assets/icons/fit.metadata.json

python skill/snowe-ui-skill/scripts/icon_review.py `
  evals/icon-decisions/manifest.json `
  --output evals/icon-decisions/comparison.html --json

python skill/snowe-ui-skill/scripts/contrast.py "#151a17" "#f2eee3" --minimum 4.5
```

Run the SVG validator for every changed SVG/metadata pair, then regenerate the comparison and require exact checked-artifact bytes. A structural pass proves only the strict file/metadata contract; visually inspect selected and closest rejected alternatives at every live target size/state and inside the real owning control.

### Manual rendered review

Serve the repository root and inspect implementations, not only screenshots:

```powershell
python -m http.server 4173 --bind 127.0.0.1
```

Current hardening pass reviewed desktop/intermediate/mobile, menu/dialog/error/result/focus states, keyboard operation, scroll/composition, and console output in the in-app browser. It also inspected the icon comparison at 1440×1000 and 390×844, the open Goodturn product dialog, Goodturn's complete service-icon family, and Larkhaven's eligibility form. The existing X kept the clearest 16 px close silhouette; custom fit better matched Goodturn's product-specific implemented 28/32 px service role despite explicit 16/20 px recognition risk; eligibility text remained more truthful without a premature badge-check. These are human visual judgments, not automated certification. Findings/fixes live in each benchmark's `QA.md`; cross-scenario conclusions live in `benchmarks/CROSS-BENCHMARK.md`.

For Pages-root compatibility, serve Doppler itself as the server root and verify `/`, assets, fresh hash entry, and interactions:

```powershell
Set-Location benchmarks/soda-campaign
python -m http.server 4174 --bind 127.0.0.1
```

### Contributor-context boundary

```powershell
python scripts/check_contributor_context.py
```

Checks that all 25 required durable context paths are present and Git-visible, public guidance/tooling is not ignored, private task/session probes are ignored, no private path class is tracked, root guidance makes the local checkpoint optional, and the generated map contains no local-state marker. The normal working-tree mode permits new nonignored public additions before staging.

Fresh-clone/CI validation is strict:

```powershell
python scripts/check_contributor_context.py --require-tracked
```

The strict mode additionally fails if any required public context file is absent from the Git index.

### Atlas freshness

```powershell
python scripts/atlas/generate_atlas.py --write  # structural changes only
python scripts/atlas/generate_atlas.py --check
```

`--check` must report `Atlas structural map is up to date.` before completion.

## CI jobs

| Job | Surface |
|---|---|
| Public contributor context | Strict tracked public/private boundary plus atlas freshness on Ubuntu/Python 3.13. |
| Python matrix | compile + current full unittest suite on Ubuntu/Windows, Python 3.11/3.13 |
| Designer behavior | behavior runner on Ubuntu/Python 3.13 |
| Rendered benchmark smoke | Node 22/system Chrome CDP on Ubuntu and Windows, five-minute timeout per matrix job |
| Doppler Pages deployment | Active static branch snapshot with `.nojekyll`; retained workflow is an inactive alternative |

Configured normal CI triggers are pushes to `main`, pull requests, and manual dispatch with read-only permissions; repository Actions are currently disabled. The retained Pages workflow has path-filtered `main` and manual triggers with `pages: write` and `id-token: write`, but is not the active publication route. The active branch snapshot must be updated separately from `main`.

Normal CI does not run manual aesthetic review, lint/format/type/coverage, packaging, deployment, or release validation. Either Pages route publishes static Doppler files and performs no aesthetic certification or benchmark build.

## Change-to-test routing

| Changed area | Minimum evidence before full suite |
|---|---|
| `SKILL.md` / references | Package/reference tests, relevant behavior assertions, progressive trace, rendered proof when output behavior changes. |
| `decision_packet.py` | DecisionPacket/Persistence/CLI tests, behavior runner, representative English/Russian/ambiguous JSON/Markdown smoke. |
| `core.py` / CSV data | Retrieval tests, domain/stack evidence-role and URL-coverage audit, obsolete-domain and numeric-claim scans. |
| `search.py` | CLI tests, `--help`, explicit domain/stack/packet/analog examples. |
| Scope calibration/delivery | Scope-contract tests, behavior runner, bounded host traces where available, and rendered proof at the calibrated surface. |
| Asset/contrast validators | Focused unit tests plus every affected real asset/pair and rendered optical/contextual review. |
| Icon lifecycle/comparison | Icon-workflow and asset tests, deterministic comparison regeneration, targeted icon browser scenario, actual host selectors, and human visual inspection. |
| Imported identities / mixed-control geometry | `tests.test_role_and_alignment`, existing icon/observation suites, `node scripts/identity-alignment-proof.mjs`, and native-size source/context review. |
| Behavior scenarios/runner | Runner output review; no expected layout/style encoding. |
| Goodturn | Bicycle suite, JS check, browser smoke, affected states/screenshots/manual QA. |
| Doppler | Soda suite, JS check, five-benchmark smoke, affected normal/reduced/transition captures, GIF, QA, and cross-comparison. |
| Forward-tests | Forward suite, all affected JS, browser smoke, captures, QA, and cross-comparison when causal dimensions change. |
| Browser script/CI | Node syntax, local smoke on system Chrome, CI contract test, platform/path review. |
| Installer/public install docs | Installation/runtime-hardening tests for exact fresh/repeated copies, lock contention, safe transient recovery, source/staging revalidation, rollback, redirected/path overlap, public CLI, and stale legacy-command removal. |
| Pages publication/live URL | Soda suite, exact static snapshot plus `.nojekyll`, folder-as-root asset/hash/interaction audit, Pages source/Actions settings read-back, and public URL browser verification; workflow result only when that route is used. |
| Repository structure or context boundary | Contributor-context check, atlas `--write` then `--check`, fresh-clone simulation, complete status/diff/ignore inspection. |

## Identity and control relationship proof

Identity/alignment evidence uses `evals/identity-alignment/build_contracts.py` to regenerate declarations, `tests/test_role_and_alignment.py` for role/profile/curve/axis compatibility and failure cases, and `scripts/identity-alignment-proof.mjs` for copied-product browser proof at 900/390 and DPR2. CI includes that command in the existing browser job. `--capture captures-<revision>` creates fresh persistent evidence for inspection; normal runs use temporary copies. The checked fixture includes actual imported assets, an intentionally weak row and compact original before/after glyphs, with implementer review in `REVIEW.md`. Authored fixtures and deterministic rejection do not establish model improvement; bounded paired host runs must retain their limitations. On this Windows host the existing directory-symlink ownership test is unavailable without platform symlink support; junction and other path tests still run.

## Missing command surfaces

No local command currently provides linting/formatting, static typing, coverage, package/plugin build or publication, visual-diff approval, full accessibility-engine audit, icon recognition/usability research, or backend integration validation. The bounded host series cannot expose exact token totals or independently attest runtime model identity. Exact standalone-copy installation is tested; Pages publication uses the remote branch/settings or the inactive workflow alternative. The direct `.nojekyll` deployment has no latest-build record in the inspected API; verify actual public bytes and behavior rather than claiming a workflow run. Do not invent or report unavailable checks as executed.

## Completion cases and migration checks

The density scenario is included in main browser smoke and can run alone with `--smoke --scenario density`. `--capture-density` writes 18 native PNGs for before/after empty/sparse/populated states at 1280/820/390; the visual-evidence suite validates fixture/font/image hashes and geometry. It checks the authored fixed-chrome/row/placeholder bounds, unchanged text-node inventory, label size and control height, nearby related values, stable queue anchor and keyboard scrolling for 24 rows. These numerical bounds belong only to the fixture; the skill's acceptance criterion remains contextual comparison and visual review.

```powershell
python -m unittest tests.test_corrections tests.test_install_migration -v
node scripts/browser-smoke.mjs --capture-acceptance-cases
node scripts/browser-smoke.mjs --smoke --scenario acceptance-cases
python scripts/install_skill.py --diagnose
```

Main smoke includes six authored before/after cases with current 900/390 PNGs: preserved type roles, drift, contextual glyphs, backings, multilingual bounded lists/alignment and continuation. It verifies keyboard scrolling to the end, empty/loading states and panel-centered action geometry. Icon stress uses schema 1.1 Russian/German/Arabic content at 320/390/900/1440 and 100/200% text, checking headers, status, metadata, preview text and focus bounds. Version 1.0 remains a regression input. Screenshots/self-review do not prove independent model improvement.

The instruction fingerprint is an output revision identifier only. Critical route clauses and six authored consequence/scope traces still reject their tested contradictions; removed whole-document equality and obsolete stage wording are not semantic-quality evidence. Internal proof records remain detailed, while user-facing delivery is brief.

The density fixture’s first tighter visual proposal was user-rejected and is not a visual KEEP. The current candidate changes grouping/selector composition and uses scoped identity cues; README distinguishes its technical contract from proposal/user acceptance. A correction regression ensures new user rejection reopens verified work even without source changes.

### Single-page hierarchy and perceptible content

```powershell
node --check scripts/ui-proof.mjs
node --check scripts/titlebot-pilot.mjs
node --check evals/titlebot-hierarchy/app.js
node scripts/browser-smoke.mjs --smoke --scenario titlebot-hierarchy
node scripts/browser-smoke.mjs --capture-titlebot
python -m unittest tests.test_page_hierarchy tests.test_corrections -v
```

Main smoke includes the isolated Title Bot pilot. It covers four widths (320/390/900/1440), 200% text, Russian, native accessible names, pointer/keyboard/focus behavior, independently keyed title data, one Settings entry, valid per-player actions, modal editing/validation/cancel/save, permission/loading/error states, local mutation failures/retries and duplicate-submit guards. Thirty lossless captures bind sources, runner, state and dimensions. The narrow settings scroller is inspected at both ends. Required-content mutation checks reject opacity-zero, clipped and covered values; action mutation checks reject different labels that call the same settings handler. Bounds and sampled occlusion are incomplete substitutes for human rendering review; they are never a taste score. The pilot README records the optional inspector-font probe limitation and separate manual review.

### Visual verdict and state emphasis

```powershell
python -m unittest tests.test_visual_review tests.test_visual_judgment_cases tests.test_corrections -v
python skill/snowe-ui-skill/scripts/visual_review.py evals/visual-judgment/reviews/c.json --workspace .
node scripts/browser-smoke.mjs --smoke --scenario visual-judgment
node scripts/browser-smoke.mjs --capture-visual-judgment
```

The main browser suite includes four same-content candidates across three states at 900/390, 24 captures, native keyboard activation/return, local disclosure/result/retry and an additional 200% text-pressure probe. A/B are deliberately retained negative visual examples while technical checks pass. C/D record historical scoped KEEP, with D preserving a restrained visual language. Those schema-2 reports retain their original bytes and runner binding; they cannot issue a new current PASS and can be STALE after runner changes. These are authored self-review judgments, not scores generated by Python or observed future model quality. The narrow D running order was revised after inspection. Linked report freshness and non-KEEP correction rejection have separate regression tests.

The visual-judgment browser group also runs a separate color study: four role palettes, completed/error pages and a completed-result dialog at 900/390, totaling 24 additional captures. It verifies unchanged content/geometry, actual opaque paint, normal/hover/pressed action colors and full table/dialog coverage. Python checks exact foreground/background pairs and fixture-specific intensity relations; these are not beauty scores. The original 24 hierarchy captures remain byte-identical, preserving their earlier judgments. Color examples remain negative for the user-requested context and are not production recommendations.

## Portable observation, detail defects and Doppler regeneration

```powershell
python -m unittest tests.test_observation tests.test_visual_review tests.test_corrections -v
python evals/doppler-regeneration/integrity_control.py
node --check skill/snowe-ui-skill/scripts/observe.mjs
node skill/snowe-ui-skill/scripts/observe.mjs capabilities
node scripts/doppler-detail-probe.mjs
node scripts/browser-smoke.mjs --smoke --scenario soda-campaign
```

The paired integrity control loads the exact previous validators from commit `92eeb724fcfa889cafe8cb47c219b7e80a8e2635`; it reproduces mobile removal, viewport relabelling, changed-CSS omission and implicit visual KEEP, then checks current refusal. It measures integrity, never quality. Full Git history is required only for that explicit control.

`test_observation` covers required combinations, browser/PNG dimensions, dependency additions, missing layers/details, crop rescaling/assessment omission, relationship drift, justified exceptions, proposed direction, conditional memory and missing temporal proof. Synthetic unit bytes have no aesthetic meaning.

The detail browser probe copies the installed product and Doppler target into a temporary workspace, injects a detached lid, an extra painted layer, a broken label mask, a shrunken real icon host, projected rather than local cylinder sizing and a covered selected label. Every tested mutation must be detected and restored; a positive paint-survival check rejects an invisible but structurally attached lid. A copied validator then reports integrity PASS with visual UNKNOWN, preserving the evidence boundary. CI runs this after canonical smoke on Ubuntu/Windows with Node 22, system Chrome and Python 3.13.

Current schema-3 Doppler evidence lives under `evals/doppler-regeneration/verified/`, with immutable `SYSTEM.v3.json`, `ATTENTION.v3.json` and `REVIEW.v3.json` bindings. Fifteen whole-page images, fifteen native viewports, 65 required details and 72 timed frames support scoped implementer review, not causal skill improvement, representative-user icon recognition or independent aesthetic acceptance. Overlay details bind their exact viewport parent. Historical schema-2 reports remain unchanged and may be stale after runner updates. Main typography/control interactions, finite-motion cleanup, rigid top-plane geometry, menu/confirmation focus and reduced mode remain in canonical browser smoke.
