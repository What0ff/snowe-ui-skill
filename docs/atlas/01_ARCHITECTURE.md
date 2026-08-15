# Architecture

## System overview

Snowe UI Skill is an installable `SKILL.md` design practice plus a standard-library Python decision-support runtime. It is not a web service, Python package, daemon, or hosted application.

Two product paths share one purpose but execute in different hosts:

- A compatible agent runtime discovers `skill/snowe-ui-skill/SKILL.md`, follows only references relevant to the live decision, researches or generates assets when justified, implements in the target repository, and performs rendered critique.
- A Python 3.11+ process runs `skill/snowe-ui-skill/scripts/search.py` for explicitly selected CSV evidence or an unresolved architecture-first decision packet. The Python runtime makes no network request and does not implement designer judgment by itself.

Repository-only deterministic contracts, five rendered implementations, screenshots, browser smoke, and the public Doppler Pages showcase provide distinct regression surfaces without becoming causal model evidence or part of copied skill installations. No reproducible observed-agent evaluation is currently committed.

## Boundaries

| Boundary | Location | Responsibility |
|---|---|---|
| Installable product | `skill/snowe-ui-skill/` | Copied skill, specialist references, local evidence, validators, metadata, and license. |
| Agent workflow | `SKILL.md`, `references/` | Product framing, causal exploration, architecture, art direction, assets, motion, implementation, and rendered learning. |
| Local decision support | `skill/snowe-ui-skill/scripts/` | Explicit lexical retrieval, unresolved decision packets, persistence, SVG checks, and contrast checks. |
| Evidence catalogs | `skill/snowe-ui-skill/data/` | Subordinate snapshots and stack guidance; never automatic classification or a solution boundary. |
| Deterministic contract regression | `evals/designer-behavior/` | Multilingual, ambiguity, perturbation, absence, discretion, and authored progressive-disclosure fixtures without a host/model run or taste score. |
| Rendered regression | `benchmarks/` | Goodturn, Doppler, municipal, warehouse, and literary implementations, decisions, QA, cross-comparison, and screenshots; demonstrates authored outcomes without causal attribution. |
| Browser regression | `scripts/browser-smoke.mjs` | Dependency-free system-Chrome/CDP runtime, interaction, focus, responsive, asset, overflow, reduced-motion, and temporary-state cleanup checks. |
| Public showcase | `.github/workflows/pages.yml` | Uploads only `benchmarks/soda-campaign/` as the root of the Doppler GitHub Pages artifact. |
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
contrast.py      (standalone exact-color checker)
```

### `search.py`

Owns CLI argument constraints and dispatch. It requires an explicit evidence domain, explicit stack, or packet mode. `--design-system` is only a compatibility spelling for `--decision-packet`; `--analog-query` is packet-only and caller chosen. Windows console output is normalized to UTF-8 when required.

### `core.py`

Owns `CSV_CONFIG`, `STACK_CONFIG`, in-process BM25, exact searchable/output headers, evidence roles/warnings, icon-row exclusion, and exact icon-candidate family constraints. It deliberately has no automatic domain detector or layout/style/palette/type/motion recipe domains.

### `decision_packet.py`

Owns schema `3.0`, verbatim brief preservation, unresolved-first framing, pass-through caller declarations, language/ambiguity policy, optional product analog evidence, open architecture/art-direction/asset/motion/responsive/evaluation contracts, Markdown/JSON formatting, and `design-intelligence/` persistence. It performs no language detection, translation, keyword signal classification, query expansion, work-mode inference, platform inference, or default pressure inference.

### Validators

`asset_quality.py` checks an SVG plus companion metadata for specific non-placeholder provenance/drawing-language fields, matching grid/viewBox geometry, active/embedded/declaration/external content, paint contracts, and unique positive target sizes. It cannot approve provenance truth, license validity, recognition, or optical balance. `contrast.py` measures exact opaque pairs and rejects alpha/unsupported syntax rather than guessing compositing.

### Repository installer

`scripts/install_skill.py` is repository tooling, not part of the copied product. It stages an exact standard-library copy beside the final `$HOME/.agents/skills/snowe-ui-skill` destination, swaps only after staging succeeds, restores the prior destination on activation failure, removes obsolete files on update, and accepts an explicit final destination for compatible hosts.

## Repository proof layer

- `evals/designer-behavior/run_eval.py` produces 17 deterministic contract/metamorphic findings covering six product scenarios, multilingual equivalence, ambiguity, unknown domains, paraphrase/business deltas, preservation, optional assets/motion, dataset absence, authored progressive-disclosure fixtures, and semantic/evidence boundaries. Its output explicitly marks observed real-agent behavior as not measured.
- `benchmarks/bicycle-commerce/` is the image-led Goodturn flagship. `benchmarks/soda-campaign/` is the dependency-free Doppler expressive-motion flagship with a CSS-3D can, local SVG labels, authored reduced mode, and browser-captured motion evidence. `benchmarks/forward-tests/` contains causally different public-service, keyboard-operations, and editorial experiences, all intentionally without generated imagery or custom assets.
- `benchmarks/CROSS-BENCHMARK.md` compares topology, navigation, opening, action placement, carriers, type, palette, cards, imagery, custom assets, motion, and responsive transformation rather than scoring cosmetic novelty.
- `scripts/browser-smoke.mjs` launches a local standard-library HTTP server and a system Chrome/Chromium through CDP; it installs no package and downloads no browser. Shutdown awaits browser exit, retries transient profile removal, and still fails if cleanup cannot complete.
- `.github/workflows/pages.yml` deploys the checked-in Doppler folder without a framework or build step; it is public evidence, not installable Snowe runtime behavior.
- `tests/test_snowe_ui_skill.py`, `tests/test_bicycle_benchmark.py`, `tests/test_soda_benchmark.py`, and `tests/test_forward_benchmarks.py` protect product, evidence, UX/artifact, CI, QA, and screenshot contracts.
- `scripts/check_contributor_context.py` and `scripts/atlas/generate_atlas.py` protect the public/private contributor boundary and a local-state-independent structural map; the CI context job runs both from a fresh checkout.

## Lifecycle and invariants

- Runtime paths resolve relative to the copied skill directory, never the repository root.
- Deterministic framing prefers `UNRESOLVED` to a plausible but unverified semantic guess; caller declarations are not restricted to built-in vocabulary.
- Architecture and art direction remain open until an agent compares real candidates; packet generation is not design completion.
- Detailed methods remain behind conditional direct links from `SKILL.md` for progressive disclosure.
- Local catalogs require explicit activation, expose evidence roles/limitations, and can be absent without changing the reasoning contract. Stack results additionally report returned-row `Docs URL` coverage without treating URL presence as authority or freshness proof.
- Persistence regenerates `BRIEF.md` and requested page inquiries but byte-preserves an existing `DECISIONS.md`.
- Python product/runtime remains standard-library and 3.11+; Node 22 plus system Chrome is repository test infrastructure only.
- Benchmarks are fictional rendered regressions, not causal model proof, installable product behavior, or production integrations; the Doppler Pages site remains a static public demonstration with no purchase/payment backend.

There is no database, long-running product process, thread, lock, shared cache, telemetry path, network client, package manager, or browser dependency in the installable Python runtime.
