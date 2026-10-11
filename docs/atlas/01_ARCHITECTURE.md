# Architecture

## System overview

Snowe UI Skill is an installable `SKILL.md` design practice plus a standard-library Python decision-support runtime. It is not a web service, Python package, daemon, or hosted application.

Two product paths share one purpose but execute in different hosts:

- A compatible agent runtime discovers `skill/snowe-ui-skill/SKILL.md`, follows only references relevant to the live decision, researches or generates assets when justified, implements in the target repository, and performs rendered critique.
- A Python 3.11+ process runs `skill/snowe-ui-skill/scripts/search.py` for explicitly selected CSV evidence or an unresolved architecture-first decision packet. The Python runtime makes no network request and does not implement designer judgment by itself.

Repository-only deterministic contracts, five rendered implementations, an operational icon-decision comparison, screenshots, browser smoke, bounded observed-host probes, and the public Doppler Pages showcase provide distinct evidence surfaces without becoming part of copied skill installations. The host probes record specified tasks, configuration, loaded references, process depth, and limitations; they are a small noncausal observation set, not proof that Snowe alone caused the behavior.

## Boundaries

| Boundary | Location | Responsibility |
|---|---|---|
| Installable product | `skill/snowe-ui-skill/` | Copied skill, specialist references, local evidence, validators, metadata, and license. |
| Agent workflow | `SKILL.md`, `references/` | Consequence/change-surface calibration from Direct through Focused to Portfolio, then only the relevant framing, exploration, implementation, and rendered learning. |
| Local decision support | `skill/snowe-ui-skill/scripts/` | Explicit retrieval, unresolved packets, correction memory, checked visual verdicts, persistence, SVG and contrast checks. Shared bounded evidence reads are owned by `checked_evidence.py`. |
| Evidence catalogs | `skill/snowe-ui-skill/data/` | Subordinate snapshots and stack guidance; never automatic classification or a solution boundary. |
| Deterministic contract regression | `evals/designer-behavior/` | Multilingual, ambiguity, perturbation, absence, discretion, progressive-disclosure, and six authored scope traces; `HOST-PROBES.md` is separately labelled bounded observed-host evidence. |
| Operational icon proof | `evals/icon-decisions/` | Existing/custom/no-icon decisions, exact SVG/metadata/source binding, deterministic comparison generation, representative controls, and real-host selector/browser checks without aesthetic certification. |
| Visual acceptance proof | `evals/visual-acceptance/` | Authored static A/B/C fixture, verified viewport/source/image evidence, and one paired review; neither generated-design improvement nor functional release certification. |
| Correction transfer proof | `evals/correction-transfer/` | Authored icon-backing fixture, scoped correction/counterexample task, hash-bound captures and implementer self-review; no independent or generated-quality claim. |
| Rendered regression | `benchmarks/` | Goodturn, Doppler, municipal, warehouse, and literary implementations, decisions, QA, cross-comparison, and screenshots; demonstrates authored outcomes without causal attribution. |
| Browser regression | `scripts/browser-smoke.mjs`, `scripts/ui-proof.mjs`, `scripts/titlebot-pilot.mjs` | Dependency-free Chrome/CDP lifecycle; benchmark checks; declared-role visibility/action identity; isolated pilot interactions and captures. |
| Single-page hierarchy pilot | `evals/titlebot-hierarchy/` | Existing Title Bot contract snapshot, fictional distinct per-title data, local functional UI, pre-component page map, bound captures and separate self-review; no production API. |
| Public showcase | GitHub Pages source branch `codex/doppler-pages` | Publishes a snapshot of `benchmarks/soda-campaign/` at the branch root with `.nojekyll`; repository Actions stay disabled. The checked-in Pages workflow is an inactive alternative. |
| Public contributor layer | root `AGENTS.md`/`CONTRIBUTING.md`, `docs/atlas/`, allowlisted `.agents/skills/atlas-maintainer/`, `scripts/`, `tests/`, `.github/` | Durable contributor guidance, architecture, maintenance tooling, CI, exact standalone installation/update, and regressions; never copied into the product. |
| Maintainer-local state | ignored `.codex/`, non-allowlisted `.agents/`, `work/`, `outputs/`, `logs/`, handoffs, and personal configuration | Optional task/session continuity only; absent from public clones and never authoritative for repository behavior. |

`agents/openai.yaml` and the copied `LICENSE` are intentional installable files. Public repository development context remains version-controlled outside the product; private task/session state remains ignored.

## Runtime graph

```text
search.py (CLI)
├── core.py
│   └── caller-selected configured CSV or stack catalog
└── decision_packet.py
    └── core.search("product") only when caller supplies analog_query

asset_quality.py (standalone SVG/metadata validator)
icon_review.py   (standalone representative-control icon comparison builder)
contrast.py      (standalone exact-color checker)
```

### `search.py`

Owns CLI argument constraints and dispatch. It requires an explicit evidence domain, explicit stack, or packet mode. `--design-system` is only a compatibility spelling for `--decision-packet`; `--analog-query` is packet-only and caller chosen. Windows console output is normalized to UTF-8 when required.

### `core.py`

Owns `CSV_CONFIG`, `STACK_CONFIG`, in-process BM25, exact searchable/output headers, evidence roles/warnings, icon-row exclusion, and exact icon-candidate family constraints. It deliberately has no automatic domain detector or layout/style/palette/type/motion recipe domains.

### `decision_packet.py`

Owns schema `3.0`, verbatim brief preservation, unresolved-first framing, pass-through caller declarations, language/ambiguity policy, optional product analog evidence, open architecture/art-direction/asset/motion/responsive/evaluation contracts, Markdown/JSON formatting, and identity-bound `design-intelligence/` persistence. Persistence requires an explicit printable project identity, rejects Windows-reserved or colliding project/page slugs, serializes one project with an OS-backed lock, preflights page identity before replaceable inquiry writes, uses atomic replace/create operations, rejects redirected or shared-file targets, and byte-preserves an existing accepted ledger. It performs no language detection, translation, keyword signal classification, query expansion, work-mode inference, platform inference, or default pressure inference.

### Validators

Symbol source choice precedes custom exploration: third-party identities retain verified supplied artwork, learned actions retain meaning, and open product-specific symbols use the native-owner drawing/repair loop. `asset_quality.py` keeps the default `interface-icon` contract and adds explicit `brand-mark` metadata schema 1.0 with external provenance, unchanged upstream-artwork and usage byte bindings, supplied opaque colors, and exact quadratic/cubic extrema under bounded arithmetic. Its imported-only containment envelope is 1e-7 of the smaller viewBox dimension for source decimal rounding; default icon bounds remain unchanged. Unsupported official assets use an appropriate official variant or host asset proof rather than a redraw. Icon comparison schema 1.2 binds explicit identity roles and forbids custom brand substitutes; 1.0/1.1 remain supported. `visual_system.py` schema 1.1 adds declared owner-axis geometry with justified numeric tolerance and an unambiguous reference; schema 1.0 retains exact-property semantics. None certifies source truth, optics or acceptance.

`asset_quality.py` checks a deliberately strict self-contained SVG subset plus companion metadata: exact-byte provenance digest, structured local source/license evidence, external/original source shape, drawing language, grid/live-area/viewBox geometry, bounded finite path/arc geometry, painted visibility, small-target viability, unsafe/external content, monochrome/current-color contracts, and explicit byte/depth/node budgets. It rejects symlink/junction/reparse input chains and returns bounded failures for malformed input. `icon_review.py` validates typed manifest decisions, existing/custom/no-icon candidates, declared sizes/states, exact assets and metadata, structured evidence bindings, digest-bound repository context, one-to-one comparison→host state maps (`high-contrast` → `forced-colors`), host routes/selectors/labels/viewports/states, output/input non-aliasing, and deterministic regeneration before producing a self-contained representative comparison sheet. Neither command verifies external provenance/license truth, recognition, metaphor, or optical/UI quality. `contrast.py` measures exact opaque pairs and rejects alpha/unsupported syntax rather than guessing compositing.

### Repository installer

`scripts/install_skill.py` is repository tooling, not part of the copied product. It acquires an OS-backed destination lock, validates lexical/physical containment and a regular self-contained source tree, claims per-run transient slots without treating forgeable stale markers as ownership, preserves a recognizable interrupted previous tree until staging succeeds, stages and revalidates an exact copy immediately before activation, revalidates the activated object, safely restores the current or recovered prior destination on failure, removes obsolete files on update, and accepts an explicit final destination for compatible hosts.

## Repository proof layer

- `evals/identity-alignment/` owns official imported assets, original compact glyph before/after examples, declared control-axis relationships and bound wide/narrow/DPR2 captures. `scripts/identity-alignment-proof.mjs` uses a copied product, checks measured weak/corrected rows and injected icon shrinking/brand distortion, and exercises local controls. It is an authored regression and implementer review, not a model-improvement or general-intelligence claim.

- `evals/designer-behavior/run_eval.py` produces 18 deterministic contract/metamorphic findings covering six product scenarios, multilingual equivalence, ambiguity, unknown domains, paraphrase/business deltas, preservation, optional assets/motion, dataset absence, progressive disclosure, six consequence/change-surface traces, and semantic/evidence boundaries. Exact per-case reference/process/artifact/stop/escalation/reason contracts reject both flattening and contradictory global ceremony without classifying task text. Its own output correctly marks host behavior as not measured by that runner. `HOST-PROBES.md` separately records a bounded GPT-5.6 Luna/max host series, including one pre-change control, actual reference loads, process activations/skips, task-target discovery, observable timings, fingerprints, and unresolved limitations.
- `evals/icon-decisions/` regenerates a self-contained existing/custom/no-icon comparison from exact local assets and metadata. Browser smoke checks declared dimensions, comparison states, explicit comparison→host mappings, containment, repository-derived source digests/routes/selectors/labels, and renders the selected Goodturn dialog Lucide X in its actual `.sheet-close-icon` owner while rendering challengers in that owning shell; selected/rejected candidates for the other controls are exercised at exact wide/mobile viewports and declared host states. The implemented Goodturn fit and Larkhaven no-icon baselines are checked separately; selection and optical rationales remain human visual judgment.
- `benchmarks/bicycle-commerce/` is the image-led Goodturn flagship. `benchmarks/soda-campaign/` is the dependency-free Doppler expressive-motion flagship with a CSS-3D can, local SVG labels, authored reduced mode, and browser-captured motion evidence. `benchmarks/forward-tests/` contains causally different public-service, keyboard-operations, and editorial experiences, all intentionally without generated imagery or custom assets.
- `benchmarks/CROSS-BENCHMARK.md` compares topology, navigation, opening, action placement, carriers, type, palette, cards, imagery, custom assets, motion, and responsive transformation rather than scoring cosmetic novelty.
- `scripts/browser-smoke.mjs` launches a local standard-library HTTP server and a system Chrome/Chromium through CDP; it installs no package and downloads no browser. Shutdown awaits browser exit, retries transient profile removal, and still fails if cleanup cannot complete.
- The active Pages branch publishes the checked-in Doppler folder without a framework or build step. `.github/workflows/pages.yml` remains an inactive alternative while repository Actions are disabled; neither route is installable Snowe runtime behavior.
- `tests/test_snowe_ui_skill.py`, `tests/test_bicycle_benchmark.py`, `tests/test_soda_benchmark.py`, and `tests/test_forward_benchmarks.py` protect product, evidence, UX/artifact, CI, QA, and screenshot contracts.
- `scripts/check_contributor_context.py` and `scripts/atlas/generate_atlas.py` protect the public/private contributor boundary and a local-state-independent structural map; the CI context job runs both from a fresh checkout.

## Lifecycle and invariants

- Runtime paths resolve relative to the copied skill directory, never the repository root.
- Deterministic framing prefers `UNRESOLVED` to a plausible but unverified semantic guess; caller declarations are not restricted to built-in vocabulary.
- Architecture and art direction remain open until an agent compares real candidates; packet generation is not design completion.
- Detailed methods remain behind conditional direct links from `SKILL.md` for progressive disclosure.
- Existing code is a baseline, not evidence of an accepted visual direction. Explicit rejection reopens the affected choice at Focused depth; original design requires a positive product-specific intention and whole-screen finishing, separate from technical fixture checks.
- Density is a scoped composition decision before dimensions are propagated. The quality gate compares empty/sparse/populated repeated-use states with a tighter challenger when that choice remains open, preserving target/text size and justified stable workspace geometry. `evals/density` supplies an authored analogue and source-bound before/after evidence, not an automatic compactness score.
- Typography acceptance checks explicit role contracts from evals/typography/goodturn.json: family, weight, style, line-height, tracking, variable settings and pinned font files/face declarations. Browser evidence covers cards, controls, navigation and open dialogs, plus deliberate mutations. Placement/scroll acceptance distinguishes bounded work regions from document flow and geometric from optical alignment.
- Scoped user corrections use the installable corrections CLI and identity-bound CORRECTIONS.json with atomic updates, history, explicit scope and hashed source/artifact proof. Existing DECISIONS.md remains byte-preserved. Applicable open or stale obligations block completion; this is evidence integrity, not machine visual judgment.
- Product-specific icon decisions actively explore feasible custom candidates, with native-size semantic, optical, host/backing and accessibility acceptance. Accepted conventional actions remain preserved. The icon comparison helper gives text-bearing states full-width rows; browser proof checks cell-level content containment and detects the original narrow-row failure via an injected regression probe.
- New/material visual systems pass a scoped early rendered comparison before propagation. Visual acceptance has explicit blocking findings, same-content subtraction when treatment value is unresolved, preservation of justified shape/brand roles, and `UNKNOWN` for missing required proof; Python packets repeat the evidence boundary without judging aesthetics.
- The quality gate explicitly exercises changes that invalidate an already-visible derived preview/result: current output must refresh or invalidate, with input retention, recovery and dependent state cues proved. Historical/accepted records remain distinct. This is affected-state proof rather than automatic whole-journey expansion.
- A definite supplied design closes its specified visual decisions: conformance compares target and implementation, including control geometry, without unauthorized restyling. A brand/content brief alone does not close composition; unresolved affected visual choices still need Focused comparison. Fidelity, source-design critique, and functional/accessibility acceptance are distinct claims.
- Local catalogs require explicit activation, expose evidence roles/limitations, and can be absent without changing the reasoning contract. Stack results additionally report returned-row `Docs URL` coverage without treating URL presence as authority or freshness proof.
- Process breadth follows observed consequence, actual owner/consumer change surface, material uncertainty, and reversibility. A high-consequence bounded correction raises proof intensity without automatically widening to architecture.
- Creative search breadth is independent of architectural scope: an open visual thesis may compare multiple directions at Focused depth while owners and settled product contracts stay fixed. Direct repairs, exact supplied targets and accepted quiet utility gain no novelty obligation. Art direction translates verified sources into perceptual mechanisms and rendered proof; material successful inventions remain conditional project hypotheses.
- `evals/creative-search/run_pilot.py` is opt-in repository-only real Codex CLI generation/capture tooling with complete frozen skill copies, frozen held-out briefs, neutral temporary subject workspaces, exact prompt/artifact checks and exposed timing/usage. It does not run in normal CI or certify taste; raw host evidence stays in ignored `work/` and durable summaries remain in the evaluation directory.
- Persistence serializes each project, preflights identities before replaceable writes, atomically regenerates `BRIEF.md`, identity-binds project/page slugs, handles recoverable torn manifests, revalidates page parents before publication, and byte-preserves an existing `DECISIONS.md`.
- Python product/runtime remains standard-library and 3.11+; The copied product also offers an optional Node 22/system Chromium observer; repository browser scenarios stay outside the copied product.
- Benchmarks are fictional rendered regressions, not causal model proof, installable product behavior, or production integrations; the Doppler Pages site remains a static public demonstration with no purchase/payment backend.

There is no database, long-running product process, shared runtime cache, telemetry path, network client, package manager, or browser dependency in the installable Python runtime. Project persistence and the repository-only installer use short-lived OS file locks plus filesystem identity/atomicity; neither creates an ongoing service.

- Six authored acceptance tasks under evals/acceptance-cases exercise retained typography, role drift, contextual custom icons, backings, multilingual bounded lists/alignment, and correction continuation. Hash-bound PNGs and implementer self-review remain separate from technical assertions and generalization claims.
- The primary skill entry is reduced to priorities, scoped routing, a short execution/proof loop and concise delivery. Document fingerprints identify revisions; critical clauses and authored route scenarios provide bounded contract checks.
- The repository installer diagnoses duplicate copies and explicitly migrates the legacy location into a digest-recorded backup outside discovery; retry and post-move failure recovery preserve old files.

## Known-page composition boundary

`references/page-hierarchy.md` owns the Focused page map, useful-copy audit and action identity (`operation + target + outcome + context`) before component choice. The root router, exploration and architecture references route known page jobs here; unresolved page jobs or wider product contracts retain Portfolio framing. Direct property corrections do not create a page-map document. These clauses and the existing six scope traces are explicit authored contracts, not an automatic task classifier. Technical, evidence-integrity, visual and user-acceptance outcomes stay separate.

Visible ordinals are part of that copy/relationship audit. The entrypoint rejects automatic `01/02` landing-section/benefit/service prefixes, while the focused reference and quality gate preserve actual process order, useful navigation/references, factual data and explicitly supplied identity. Open numbering treatments use same-content comparison; no keyword classifier, numeric quota or runtime taste verdict selects the outcome.

## Explicit visual review contract

`visual_review.py` checks new schema-3 reports against schema-2 attention contracts, independently bound observation plans and scoped visual-system revisions. `observation.py` owns complete declared combination/source inventories, actual browser metadata, whole/detail PNG and temporal bindings. `visual_system.py` owns component/role/token/owner/consumer/layer maps, observable relationships, exceptions and conditional hypotheses. Method, recorded verdict, integrity and user acceptance remain distinct; none grades taste. Historical schema-1/2 reports remain readable but cannot mint PASS. New visual correction verification requires method, explicit KEEP and a current linked report; old inline receipts need renewed verification without history rewriting.

The repository-only `evals/visual-judgment` cases contrast technically valid A/B weaknesses with a corrected C and restrained D across running/completed/error states. `scripts/visual-judgment.mjs` handles their browser proof through the canonical lifecycle. Formal reports record implementer self-review; source/record validation never establishes independent quality.

Color selection guidance assigns the agent the reversible palette decision before implementation, grounded in product context and full-surface roles. The repository-only color-intensity extension to visual-judgment tests role-specific fill/foreground and canvas/table/dialog paint. Ocean/plum examples retain technical success but explicit contextual rejection; the fixture palette JSON is not an installable color catalog or universal chooser.

The iconography reference owns autonomous control label-mode selection (icon-only, text-only or combined) by action recognition, context, density and input, with scoped in-control comparison only for unresolved choices. Icon-only controls retain accessible naming and hover/focus help; ambiguous or consequential actions retain needed visible wording. Design foundations and quality gates route to that section without reopening icon sourcing for a bounded caption change. Passive service/data/form labels are outside that removal scope.

## Portable observation and regenerated Doppler

`observe.mjs` is a self-contained optional Node/CDP adapter: capability discovery, isolated loopback static serving, state replay, measured layers/rendered fonts, complete scoped source/resource closure, immutable whole/detail captures, bounded temporal sequences and a paired comparison viewer. It uses only Node built-ins and a system browser. Headless native scrollbar paint is hidden for stable capture geometry; native scrollbar behavior, application-server builds, external resources, closed shadow content and independent visual judgment remain host responsibilities. Python remains standard-library-only.

The regenerated Doppler page separates `can.css` from composition, attaches its top plane to the cylinder's 3D owner, uses five original control masks and finite authored choreography. Its anchored menu and native confirmation dialog share the page's type/material hierarchy and have keyboard/text-pressure proof. `references/overlays-and-selection.md` owns conditional visual composition guidance for secondary surfaces; `references/icon-craft.md` owns actual-slot optical review. The old accepted ledger is byte-preserved. `REGENERATION.md` and `evals/doppler-regeneration/` separate new selection, old/new integrity controls, real-browser detail injections, current self-review and unconfirmed user acceptance. `scripts/doppler-detail-probe.mjs` copies product and target into an isolated workspace and injects construction, paint, mask, icon-host and visibility defects; no Doppler semantics enter installed tools.
