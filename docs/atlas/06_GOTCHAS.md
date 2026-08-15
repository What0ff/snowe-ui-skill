# Gotchas and Fragile Boundaries

## Installable and contributor-context boundaries

- `skill/snowe-ui-skill/` is the copied product. Repository atlas/task state, evaluations, benchmarks, tests, browser script, and maintenance scripts remain outside it.
- `agents/openai.yaml` and copied `LICENSE` are intentional product files.
- Root `AGENTS.md`, `docs/atlas/`, `scripts/atlas/`, and `.agents/skills/atlas-maintainer/` are durable public contributor infrastructure. Their AI-assisted use does not make them private or installable product content.
- `.codex/`, non-allowlisted `.agents/` content, work/output/log directories, raw memory/handoff files, and personal runtime configuration remain ignored. Never solve a missing-public-context defect by publishing those artifacts.
- The structural generator reads tracked files plus nonignored candidate additions. If a durable path is accidentally ignored it disappears from `repo-map.md`; if private state becomes visible it can contaminate the map. Run both context and atlas checks after ignore-rule changes.

## Imports and console behavior

- `search.py` and `decision_packet.py` use bare sibling imports. Run documented script paths or add the scripts directory to `sys.path` as tests do; this is not an installed Python package.
- UTF-8 console normalization exists in `search.py`; direct module callers do not inherit it.

## Deterministic framing has deliberately low authority

- The packet is language-neutral because it does not interpret the brief, not because it contains a multilingual classifier.
- Do not restore `_SIGNAL_RULES`, query expansions, pressure mappings, language-specific synonym tables, automatic work-mode/platform inference, or fallback domain detection.
- Ambiguous terms and unknown domains must remain unresolved unless a caller supplies verified context. `UNKNOWN` is preferable to plausible false confidence.
- Caller-declared pressures are free-form and passed through. Do not limit them to a catalog.

## Retrieval is evidence, not design

- General search requires an explicit domain. BM25 remains lexical and may be English-oriented, but this affects only caller-requested lookup, never packet framing.
- Product analogs are off by default. `--analog-query` is caller chosen, limited, labelled `UNVERIFIED_ANALOG`, and its absence changes no situation/architecture field.
- Every domain and stack result retains `source_role` and `warning`. Stack responses also count returned rows with and without `Docs URL`; a present URL is not automatically current/primary, and a missing URL is explicitly unsourced bundled guidance. Removing these boundaries can turn a snapshot into apparent authority.
- Landing/layout, style bundle, palette, typography pairing, and motion preset catalogs were deleted. Do not reintroduce their solution fields under a new evidence label without provenance and an observed failure that outweighs anchoring.
- `icon-candidates` requires exactly one supported family and a real subject; compare sources through separate auditable lookups.
- `CSV_CONFIG`/`STACK_CONFIG` headers are exact contracts; malformed quoting or renamed columns can silently empty fields.

## Open-decision and progressive-disclosure contracts

- `--design-system` aliases `--decision-packet`; it must not resurrect recipe generation or old numeric dials.
- Architecture, imagery, custom work, and motion remain open, with no image/custom asset/animation valid.
- A narrow focus fix should not load architecture/imagery/motion/evaluation. Architecture work should not load iconography. A no-image result ends generation work. A routine existing-family glyph does not trigger custom drawing.
- Automated `KEEP` proves epistemic boundaries only. It cannot certify architecture, aesthetic distinction, icon optics, motion quality, or responsive coherence.

## Persistence and paths

- Re-running persistence overwrites `BRIEF.md` and requested page inquiries but preserves `DECISIONS.md` via exclusive creation.
- Project/page names are path inputs. Preserve slug and containment tests; slugging can still create collisions.
- There is no transaction/lock across persisted files.

## Validators

- `asset_quality.py` approves only a bounded structural/provenance contract. It rejects placeholder metadata, grid/viewBox mismatch, active/embedded/style elements, inline styles, handlers, base overrides, unsafe declarations, and non-local URI/CSS references, but cannot validate provenance truth, license validity, recognition, or optics. Render at actual sizes beside neighbors; optical review can reject a structural pass.
- `contrast.py` accepts exact opaque colors. It does not composite alpha, gradients, images, blend modes, overlays, or state opacity.

## Benchmark and browser evidence

- All five businesses are fictional. Their artifacts are rendered/browser regressions, not observed-agent or causal model evidence. Goodturn generated imagery is not engineering truth; keep its disclosure, local font licenses, and SVG metadata.
- Forward-test screenshot filenames are a manifest/test contract. Rerun `node scripts/browser-smoke.mjs --capture` after material visual changes.
- Browser smoke uses system Chrome CDP and catches runtime/interaction failures, not taste. Manual in-app review remains necessary for composition and optical hierarchy.
- Keep selector scopes specific: the warehouse first pass showed how shared `[data-filter]` attributes on controls and rows can corrupt state.
- Model durable object state explicitly: setting `hidden` before a recomputation can be undone, as the initial resolution flow demonstrated.
- Check inherited responsive grid placement at every breakpoint; the literary tablet membership placement initially leaked into phone order without causing overflow.
- Full-page and viewport screenshots serve different evidence. Fixed elements can appear misleadingly in full-page state captures.

## Current validation gaps

The repository has unit/regression, deterministic contract, exact standalone-install, compile, cross-platform browser smoke, screenshots, and manual rendered QA. It still has no lint/format, static typing, coverage, package/plugin publication verification, automated visual diff, full accessibility engine, local deployment verification, production backend tests, or reproducible observed-agent comparison. Aesthetic quality remains human/rendered judgment.
