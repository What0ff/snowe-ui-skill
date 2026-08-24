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
- JSON mode reserves stdout for one valid JSON document; persistence summaries go to stderr. Packet-only and search-only flags are rejected outside their owning mode rather than silently ignored.

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
- Calibrate from the observed consequence and actual owner/consumer change surface, not English keywords, request category, or file count. Search exact user-supplied product/feature/route/visible-label identifiers in paths **and content**, then follow manifests/entrypoints/rendered routes before declaring a target absent.
- The deterministic scope fixtures use an authored boolean uncertainty-surface record only to test route consistency. Do not turn those fields into a runtime classifier or infer them from task text. Exact per-case reference/process/artifact/stop/escalation contracts, exact progressive-route reasons, and the structurally closed Direct/Focused/Portfolio Delivery obligations prevent contradictory global workshop claims from passing.
- Architecture, imagery, custom work, and motion remain open, with no image/custom asset/animation valid.
- A Direct correction records and proves only the affected invariant; it skips packets, broad research, candidate generation, architecture, unrelated assets/motion, and full designer evaluation. A shared owner or one unresolved established-system choice is Focused. Portfolio activates only for named material goal/topology/journey/content/interaction/responsive/system-contract uncertainty. High consequence increases failure-mode proof without automatically increasing process breadth.
- Architecture work should not load iconography without a live icon decision. A no-image result ends generation work. A routine learned glyph in an accepted family does not trigger custom drawing.
- Automated `KEEP` proves epistemic boundaries only. It cannot certify architecture, aesthetic distinction, icon optics, motion quality, or responsive coherence.

## Persistence and paths

- Re-running persistence atomically replaces `BRIEF.md` and a matching requested page inquiry but preserves `DECISIONS.md` via exclusive creation.
- Project/page names are identities as well as path inputs. `PROJECT.json` and embedded page identity prevent distinct printable values from silently sharing a normalized slug; nonprintable or Windows-reserved identities, redirected path chains, external hardlink targets, and competing slug claims are rejected before replaceable inquiry writes. Expand Windows 8.3 aliases to their long lexical spelling without resolving redirect targets, recheck both spellings after expansion, and keep containment lexical.
- A bounded torn-manifest recovery path must never infer identity from a slug alone. Keep the per-project lock, page preflight, and immediate parent revalidation: there is no database or multi-file transaction, so these serialize known races while preserving per-file atomicity.

## Validators

- `asset_quality.py` approves only a strict self-contained structural/declared-provenance contract under explicit byte/depth/node and arc-magnitude budgets. It requires structured source/license evidence bound to metadata-relative safe regular files (or an explicitly `unverified` external source), and rejects redirected input chains, placeholder/extra/contradictory metadata, exact-byte digest mismatch, grid/live-area/viewBox mismatch, active/embedded/external/style/namespace/link content, unsupported transforms/paint, malformed/non-finite/extreme/clipped/empty geometry, embedded text/raster, and artwork that deterministically collapses at its smallest declared target. It still cannot validate current external source/license truth, recognition, metaphor, silhouette, optical balance, or family/UI fit.
- `icon_review.py` binds exact candidates, metadata, structured source/license evidence, sizes, canonical comparison→host state maps (same-name states except `high-contrast` → `forced-colors`), context source digests/routes/selectors/labels/viewports, verdict, selection, and all non-selected alternatives into a deterministic LF-normalized representative sheet. Repository-derived host proof requires a selected candidate; unresolved `REJECT | UNKNOWN` contexts must remain representative. It rejects malformed/extreme numeric input, uninspectable or redirected paths, state-label swaps, and output/input aliases. It does not choose the winner and is not a pixel-identical host renderer. Inspect the winner and closest rejected alternative in the real owning component; custom, existing, modified surrounding UI, and no icon remain valid outcomes.
- `contrast.py` accepts exact opaque colors. It does not composite alpha, gradients, images, blend modes, overlays, or state opacity.

## Benchmark and browser evidence

- All five businesses are fictional. Their artifacts are rendered/browser regressions, not observed-agent or causal model evidence. Goodturn generated imagery is not engineering truth; keep its disclosure, local font licenses, original-asset metadata, and pinned Lucide source/license metadata distinct.
- Forward-test screenshot filenames are a manifest/test contract. Rerun `node scripts/browser-smoke.mjs --capture` after material visual changes.
- Browser smoke uses system Chrome CDP and catches runtime/interaction failures, not taste. Manual in-app review remains necessary for composition and optical hierarchy.
- Measure final component geometry only after the scoped owning transition has stopped and its bounds are stable; ancestor transforms make otherwise correct descendants appear fractionally smaller during entry motion.
- Keep selector scopes specific: the warehouse first pass showed how shared `[data-filter]` attributes on controls and rows can corrupt state.
- Model durable object state explicitly: setting `hidden` before a recomputation can be undone, as the initial resolution flow demonstrated.
- Check inherited responsive grid placement at every breakpoint; the literary tablet membership placement initially leaked into phone order without causing overflow.
- Full-page and viewport screenshots serve different evidence. Fixed elements can appear misleadingly in full-page state captures.

## Installer boundary

- The repository installer owns a short-lived destination lock and per-run transient staging/backup claims. It preserves recognizable interrupted previous state until staging succeeds and must never treat a forgeable stale marker as permission for recursive deletion.
- Validate the source, completed staging tree, and activated destination. Expand Windows short names through the longest existing ancestor without resolving reparse targets, then recheck both original and long lexical spellings before containment, locking, and swaps so aliases cannot bypass overlap checks or split ownership identity. Copy or rename success alone is not proof that a concurrent path swap stayed safe. The post-swap checks are still path-based; complete protection against a hostile same-user TOCTOU adversary would require platform-specific secure directory handles.

## Current validation gaps

The repository has unit/regression, deterministic contract, exact standalone-install, compile, cross-platform CI browser smoke, screenshots, manual rendered QA, an operational icon comparison, and a bounded observed-host scope series. The host series is small, single-configuration, noncausal, and cannot observe exact token totals or runtime self-identity; it is not a reproducible population comparison. The repository still has no lint/format, static typing, coverage, package/plugin publication verification, automated visual diff, full accessibility engine, local deployment verification, production backend tests, or icon recognition/usability study. Aesthetic and optical quality remain human/rendered judgment.
