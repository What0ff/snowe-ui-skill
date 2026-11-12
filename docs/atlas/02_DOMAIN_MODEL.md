# Domain Model and Contracts

## Canonical vocabulary

Checked correction records use schema `1.0`: stable ID, explicit source/requirement, scope (relative source owners, routes, states), technical/behavior/visual criteria, `requested | implemented | verified | superseded` status, history snapshots and optional proof/replacement. `check` reports `PASS | BLOCKED | REVIEW_REQUIRED | NO_JOURNAL` independently of the historical status; `NO_JOURNAL` means the requested identity has no journal while other workspace identities do. Visual proof requires recorded review for each required state and exact source/artifact bindings; the caller's judgment is not independently certified. Current definition/proof is compared with the latest history snapshot before scope filtering. Mismatches also retain the most recent verified scope; legacy verified entries without snapshots remain readable but require explicit re-verification. `list.review_required` exposes these integrity findings without changing records. Malformed structure is an error. See the installable correction-memory reference for JSON fields and CLI exit codes.

Icon comparison schema `1.2` requires context `lang`, `dir` (`ltr | rtl | auto`) and explicit `symbol_role` (`interface-icon | brand-mark`). Brand contexts also require `brand_identity`, matching imported metadata and no custom substitutes; a known existing brand asset or text fallback can stand alone. The reader retains schema `1.1` and schema `1.0` defaults `en/ltr` unchanged; typed roles require 1.2. Preview language applies to target content, while English inspector metadata retains its own language. Long labels and text-only controls can wrap/grow without changing SVG target sizes.

| Term | Meaning | Source |
|---|---|---|
| Skill | Copied `skill/snowe-ui-skill/` unit discovered from `SKILL.md` frontmatter. | `SKILL.md`, package tests |
| Evidence domain | Caller-selected CSV category such as `product`, `chart`, or `icon-candidates`; never an inferred product domain. | `core.py:CSV_CONFIG` |
| Stack | Caller-selected implementation-guidance catalog such as `react`, `swiftui`, or `wpf`. | `core.py:STACK_CONFIG` |
| Decision packet | Schema-3.0 unresolved workbench preserving the brief, caller declarations, research questions, candidate contracts, and proof obligations. | `decision_packet.py` |
| Declared context | Caller-supplied work mode, platforms, facts, free-form pressures, and other fields passed through without a controlled vocabulary. | `decision_packet.py:_normalize_declared_context`; CLI `search.py --declared-context` (`load_declared_context`) |
| Pressure inquiry | Generic prompt to discover consequential pressures; not a keyword-derived answer. | packet `situation.pressure_inquiry` |
| Local analog | At most three caller-requested product rows labelled `UNVERIFIED_ANALOG`; lexical evidence, not classification. | packet `local_evidence` |
| Causal decision | `driver → design move → expected consequence → evidence → risk → revisit trigger`. | `SKILL.md`, packet `decision_graph` |
| Depth record | Evidence-bound `Direct | Focused | Portfolio` route naming consequence, affected invariant, owner/consumers, exact loaded/skipped references and skipped processes, artifacts, proof stop, and escalation trigger. | `SKILL.md`, scope scenarios/tests |
| Rendered finding | `KEEP`, `REVISE`, `REJECT`, or `UNKNOWN` tied to viewport/state evidence. | `designer-evaluation.md`, benchmark QA |
| Accepted decision ledger | Durable project decisions under `design-intelligence/<slug>/DECISIONS.md`. | `persist_decision_packet` |
| Atlas | Public durable repository navigation/facts under `docs/atlas/`; unrelated to project design intelligence or private task memory. | root `AGENTS.md` |

## Retrieval contract

`core.py` exposes 11 general domain names (`mobile` and its compatibility alias `web` share one catalog) and 21 stacks. Each configuration declares a CSV filename, exact searchable/output headers, and the `name_cols` that name a row. `_search_csv` normalizes query and rows identically (stopwords, light English stemming, hyphen compounds split and joined), weights fields (name ×3, `Keywords`/`Category` ×2, others ×1), multiplies BM25 by matched-term coverage, ranks exact > prefix > phrase-overlap name matches first, drops rows matching fewer than half the best row's distinct terms, and returns positive scores only. There is no persisted index, embedding/semantic model, automatic domain detector, remote service, or cache.

`search(query, domain, max_results)` requires `domain` and returns:

```text
{
  domain, query, file,
  source_role, warning,
  count, results,
  unmatched_terms
}
```

`unmatched_terms` lists query words absent from every searched column (they cannot affect ranking); a non-empty list is also named in `warning`. Each `results` item maps catalog column names to values; catalogs with a `No` column return that stable row id first (removed rows leave gaps). Every live domain has an epistemic role and use boundary. Product output is only `No`, `Product Type`, and `Keywords`. Icon lookup removes legacy style/guideline rows. `icon-candidates` additionally requires exactly one named supported family and a real subject.

Chart retrieval is a visualization-discovery snapshot. `charts.csv` holds only the returned columns: unsupported exact data-volume thresholds, use/avoid prose, color prescriptions, accessibility grades, library recommendations, and interaction levels were deleted from the shipped file, not merely hidden from output.

`search_stack(query, stack, max_results)` returns:

```text
{
  domain, stack, query, file,
  source_role, warning,
  documentation_coverage: {
    returned_rows, docs_urls_present, docs_urls_missing
  },
  count, results,
  unmatched_terms
}
```

Stack results are caller-selected bundled snapshots. Every response requires current primary-source/repository verification, treats any returned URL as a discovery pointer rather than freshness proof, and explicitly reports returned rows with no `Docs URL` as unsourced bundled guidance.

Removed domains are part of the contract: no landing/layout, style-combination, palette, typography-pairing, or motion-preset retrieval exists.

## Decision-packet contract

Principal schema-3.0 groups are:

- `situation`: verbatim brief, unresolved/partially declared status, caller facts/pressures, generic pressure inquiry, language policy, ambiguity policy, and unknowns;
- `decision_graph`: causal record, decision layers, and novelty rule;
- `research`: generic decision-led triggers with activation questions, source posture, and stop conditions; brief vocabulary never auto-activates them;
- `architecture`: `OPEN` whole-journey inputs, synthesis method, candidate record, and selection rule;
- `art_direction`: `OPEN` product-specific identity sources, direction method, and record;
- `assets`: `OPEN` visual-need outcomes including `No image`, image-generation loop, and custom-graphic workflow/rejection rules;
- `motion`: `OPEN` eligible outcomes including `No animation`, beginning from static/reduced motion;
- `responsive`: invariant/transformation contract and wide/pressure/narrow proof;
- `evaluation`: non-numeric verdicts, evidence criteria, finding record, and stop condition;
- `local_evidence`: `NOT_REQUESTED` by default or caller-requested lexical product analogs with an absence rule.

No `signals` field or deterministic signal/pressure table exists. The terms `service`, `platform`, `audit`, `history`, `store`, and `application` are named examples of vocabulary that remains unresolved without context; they are not special classification keys.

Forbidden premature-selection keys in evaluation include `pattern`, `section_order`, `landing_pattern`, `style`, `palette`, `font`, `typography`, `colors`, `motion_snippet`, and `motion_intensity`.

## Persistence contract

Persistence requires an explicit printable, non-Windows-reserved project identity and serializes one normalized project slug with a short-lived OS lock. For `design-intelligence/<project-slug>/`:

| File | Write behavior |
|---|---|
| `PROJECT.json` | Atomic identity manifest; an exact matching project can resume, a slug collision is rejected, and a recoverable torn manifest can be regenerated only when the existing directory is consistent with the same explicit identity. |
| `BRIEF.md` | Atomically regenerated from the current packet without following redirected/shared-file targets. |
| `DECISIONS.md` | Exclusive-create only; existing bytes are preserved. |
| `pages/<page-slug>.md` | Atomically identity-claimed/updated as an open inquiry with no prescribed page type or section order; a colliding or racing page identity is rejected. |

`slugify_name` case-folds Unicode, converts non-word runs/underscores to collapsed dashes, trims to 80 characters, and applies a fallback. Identity manifests prevent distinct printable names from silently sharing that slug. Page identity is preflighted before `BRIEF.md` can change and its parent is revalidated immediately before publication. Tests verify traversal-like and reserved names fail safely, redirects at or below the resolved selected root and shared-file targets are refused while a redirected ancestor of the selected root is accepted, corrupt-manifest recovery is serialized, and competing page claims cannot overwrite each other.

Decision-ledger statuses are `PROPOSED`, `ACCEPTED`, and `SUPERSEDED`. Packet status `OPEN` and rendered `KEEP | REVISE | REJECT | UNKNOWN` are separate contracts.

## Evidence datasets

Live configuration, not directory presence, defines runtime inputs. `data/CATALOGS.md` is the shipped provenance manifest (source, import/edit dates, row count, license notice, including the MIT notice for catalogs derived from UI UX Pro Max); `tests/test_catalogs.py` keeps its file list and row counts exact.

| Catalog | Rows | Role |
|---|---:|---|
| `products.csv` | 192 | Caller-requested lexical product analog terms only. |
| `google-fonts.csv` | 1,961 | Slim metadata index dated 2026-11-12 (category, stroke, subsets, primary script, axis ranges, styles, designers, license, last modified); no keywords, mood words, or popularity. Not a font decision. |
| `ux-guidelines.csv` | 91 | General UX prompts with contextual verification boundary; row ids are stable (merged duplicates leave gaps). |
| `app-interface.csv` | 30 | iOS/Android/React Native app-interface prompts via `mobile` (alias `web`); not browser guidance. |
| `react-performance.csv` | 44 | React performance prompts requiring version/current-doc verification. |
| `charts.csv` | 25 | Encoding alternatives, limitations, and accessibility prompts (seven columns; nothing withheld remains in the file). |
| `icons.csv` | 104 | Legacy familiar-action lookup after style/guideline filtering; no third-party brand marks (those come from official artwork). |
| `icon-families.csv` | 10 | Source discovery snapshot. |
| `icon-concepts.csv` | 21 | Role/metaphor questions. |
| `icon-candidates.csv` | 70 | Exact known exports with family/source constraints. |
| `data/stacks/*.csv` | 21 files | Explicit stack guidance. `uwp.csv` was retired (2026-11-12); `RETIRED_STACKS` makes `--stack uwp` return an error naming `winui`. |

`landing.csv`, `styles.csv`, `colors.csv`, `typography.csv`, and `motion.csv` were deleted because they contained solution-shaped recipes or unsupported suitability/conversion claims. `products.csv` was reduced to lexical taxonomy. `evals/designer-behavior/EVIDENCE-AUDIT.md` records field-level rationale.

## Custom-icon contracts

`asset_type:brand-mark` is an explicit imported-identity profile, distinct from the `interface-icon` default. Its `brand` schema 1.0 declares identity, supplied variant, exact upstream artwork and usage file bindings. External provenance is required and the delivered digest must equal upstream artwork; opaque supplied hex/black/white paint is permitted. Active/dependent content stays rejected. Exact bounded Bézier extrema apply to every profile; this profile alone adds a tiny relative viewBox rounding envelope, which is not an aesthetic clipping waiver. Matching hashes do not independently establish authenticity or permission.

An SVG metadata document declares exact required fields for name, UI role, source/license text, accessibility ownership, grid/live area, drawing language, target sizes, original/external provenance, and structured evidence. Provenance includes the exact SVG-byte SHA-256 digest; local source/license evidence resolves through metadata-relative safe regular-file paths and exact digests, while external source evidence is explicitly `unverified`. A matching digest proves byte binding only, not current external source or license truth. `drawing_language.mode` is `stroke | fill | mixed | duotone`; duotone adds `tones.secondary_opacity` (0.12–0.6) and marks SVG elements or groups `data-icon-layer=primary|secondary`. `live_area` is relative to the viewBox origin. Original artwork may bind `evidence.license` as `{"kind":"project-owned"}`; external artwork keeps a license file. Whole-value `<...>` strings are placeholders that fail like other placeholder words; `--init-metadata` writes them and `--rehash` rebinds only original/local digests.

`evals/icon-decisions/manifest.json` records representative UI contexts, exact local sources and SHA-256 digests, route/selector/label bindings, exact wide/mobile host viewports, a canonical comparison-state→host-state map (same-name states except `high-contrast` → `forced-colors`), applicable host states, candidates of kind `existing | custom | none`, one selected outcome, and human-authored `KEEP | REJECT` decision evidence. Repository-derived host proof requires a selected candidate; unresolved `REJECT | UNKNOWN` contexts remain representative evidence. Dark host evidence additionally binds its owning surface and computed background. The comparison builder rejects malformed/deep/extreme-number inputs, uninspectable or redirected paths, duplicate names, invalid selections/verdicts, incomplete challenger coverage, missing target sizes, state-label swaps, structured evidence/source-license disagreement with SVG metadata, custom assets without original provenance, output/input aliases, and non-deterministic checked output. Schema-1.2 interface contexts may set `comparison_axis: kind | style`; a style comparison admits same-kind candidates whose declared drawing styles differ in some state. Candidates may bind `state_assets` per non-default comparison state (each `{asset, asset_sha256, metadata}`), and duplicates are judged on the bytes shown in every state. A `selected` host state requires `selected_attribute: aria-pressed | aria-current | aria-selected` and optional `select_selector`. These deterministic contracts do not certify recognition, optical balance, metaphor, or neighboring-UI fit.

## Recorded visual disposition

A schema-3 visual review binds a schema-2 attention contract, observation plan, visual-system revision and immutable capture receipt. Planned combinations explicitly name state/viewport/theme/input/motion/context. Receipts bind actual browser environment, complete bounded source inventory, loaded resources, measured layers/fonts, whole/detail lossless PNGs and optional timed frames. Every required whole/detail render needs an assessment. Method, KEEP/REVISE/REJECT/UNKNOWN and UNCONFIRMED/ACCEPTED/REJECTED remain separate. Historical schema-1/2 records are readable but cannot close current proof. PASS/BLOCKED/REVIEW_REQUIRED and integrity never certify taste or user acceptance. CLI/reference documentation owns exact formats.

A visual-system revision records proposed/selected/user-specified direction separately from implementation and acceptance, affected perceptual axes, component ownership, tokens, states/consumers/layers, observable checks, scoped exceptions and conditional hypotheses. Direct maps remain compact; Portfolio addresses all axes. SVG targets now name actual implemented slots; the icon manifest enforces exact context-size coverage instead of requiring fictitious 16/20/24 usage.

Visual-system schema 1.1 retains schema 1.0 and permits `bounds.x/y/width/height/right/bottom/centerX/centerY` checks with justified nonnegative CSS-pixel tolerance and numeric `equals` or one measured `sameAs` reference. Every actual match is checked. Pseudo-element geometry, empty/ambiguous references and nonfinite/nonpositive owner boxes cannot be excepted away. Box geometry cannot certify optical mass or text baseline.
