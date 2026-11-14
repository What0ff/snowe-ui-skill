# Critical Execution Flows

## 1. Agent design workflow

**Trigger:** a compatible host activates `skill/snowe-ui-skill/SKILL.md`.

1. Resolve the real target through exact user-supplied identifiers in paths and file contents, then manifests/entrypoints/rendered routes; inspect the actual owner, dependencies, sibling consumers, states, breakpoints, and shared contracts.
2. Record consequence, affected invariant, owner/consumers, material uncertainties, reversibility, loaded/skipped references, proof, stop, and escalation; choose the smallest responsible `Direct | Focused | Portfolio` depth from that evidence rather than request vocabulary or file count.
3. Keep a bounded accepted-system correction Direct, widen a shared/unresolved affected decision to Focused, and activate whole-journey/architecture work only for named material goal/topology/journey/content/interaction/responsive/system-contract uncertainty. High consequence raises relevant proof intensity independently of breadth.
4. Establish verified business/user/product/content/platform truth only at that surface and preserve existing coherent decisions when the task is evolutionary.
5. Open material causal decisions where proportionate; Portfolio work may synthesize whole-journey/site/page architectures before art direction.
6. Compare structurally or perceptually meaningful candidates only for the live decision and prototype risky slices.
7. Decide whether imagery, generated assets, custom graphics, icons, and motion exist; absence remains a valid result.
8. Freeze the calibrated implementation contract, build in the real target architecture, and preserve UX/accessibility invariants.
9. Render the affected Direct state, Focused comparison/siblings, or Portfolio proof slices; exercise relevant interactions; record `KEEP | REVISE | REJECT | UNKNOWN`; stop when proof closes the live uncertainty or escalate only on new evidence.

**End state:** an evidence-backed implementation and design record. Skill prose or a packet alone is not completion.

## 2. Explicit evidence search

**Trigger:** `python skill/snowe-ui-skill/scripts/search.py "<query>" --domain <domain>`.

1. `search.py` rejects missing or conflicting modes; no automatic domain fallback exists.
2. `CSV_CONFIG` resolves the exact caller-selected file/search/output headers.
3. `_load_csv` reads UTF-8 CSV and `_search_csv` builds an in-memory weighted-field BM25 corpus over normalized terms, applies matched-term coverage and the incidental-match floor, ranks exact/prefix/overlap name matches first, and records `unmatched_terms`.
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
2. Normalize only caller-supplied declarations and pass through free-form fields/pressures. From the CLI they come only from `--declared-context <file.json>`, a UTF-8 JSON object whose `work_mode` (text) and `platforms`/`facts`/`pressures` (arrays of nonempty strings) are type-checked before generation; other keys pass through.
3. Emit generic pressure questions and unknowns, explicitly favoring unresolved framing over false confidence.
4. Emit research triggers with activation questions and stop conditions; brief terms do not activate them automatically.
5. If and only if the caller supplies `analog_query`, run lexical product retrieval, limit results to three, label each `UNVERIFIED_ANALOG`, and keep absence non-consequential.
6. Emit open architecture, art-direction, asset, motion, responsive, and evaluation contracts in Markdown or JSON.

**End state:** a causal workbench is printed. No domain, layout, style, type, palette, image, icon family, or motion result is selected.

## 5. Decision-intelligence persistence

**Trigger:** `--decision-packet --persist [--page ...] [--output-dir ...]`.

1. CLI constraints reject persistence/page/output flags outside packet mode.
2. A printable, non-Windows-reserved explicit project identity is slugged beneath the requested output root. That caller-selected root is resolved once with `realpath` (redirected ancestors such as macOS `/tmp` are accepted); on Windows the resolved path's 8.3 names are expanded to their long spelling, both spellings are rechecked to the drive root, and every later check refuses any redirect at or below the resolved root. Lexical containment beneath the resolved root prevents false escapes; external shared-file targets are rejected.
3. A per-project OS lock serializes identity claims, torn-manifest recovery, and subsequent writes.
4. Existing project and requested-page identities are preflighted before any replaceable inquiry write. `PROJECT.json` atomically claims the slug; exact identity can resume, while distinct identities that collapse to the same slug fail without modifying existing files.
5. `BRIEF.md` is atomically regenerated (with `--page`, it is exclusive-created and an existing project brief is preserved) and `DECISIONS.md` is exclusive-created; an existing ledger is reported as preserved byte-for-byte. The verbatim brief is scanned for likely secrets, emails and private hosts; matches are reported as `sensitive_content` and a stderr warning, never redacted.
6. A requested page inquiry is exclusive-claimed on first write, identity-checked on update, and atomically replaced beneath a parent revalidated after formatting and immediately before publication; a collision or competing claim fails without overwrite.

**End state:** identity-bound replaceable inquiry plus durable accepted decisions. Individual file transitions are atomic and races are rejected; there is deliberately no database or multi-file transaction.

## 6. Low-level validators

- `asset_quality.py <svg> --metadata <json>` rejects redirected input paths, returns structured read/decode failures, binds the exact SVG bytes to declared original/external provenance, parses the default strict self-contained `currentColor` subset (or explicitly bound imported brand artwork) under explicit byte/depth/node budgets, checks metadata/drawing language (`stroke | fill | mixed | duotone`; duotone layers via `data-icon-layer` with one declared secondary tone), grid/viewBox-origin-relative live area, exact curve-extrema geometry, painted visibility, clipping bounds, unique target sizes, and small-target viability, accepts fixed-value inert library markup, compact arc flags, and unpainted full-viewBox spacers, and rejects active/embedded/external content, malformed or extreme path/arc data, unsafe namespaces/links/styles/transforms/paint. It warns, without failing, on same-winding nonzero holes and fill/duotone details below 1 CSS px, and returns an optical-QA warning even on structural pass. `--init-metadata` writes a placeholder skeleton (placeholders fail validation) and `--rehash` rebinds original-provenance and local evidence digests after an intentional edit; external and brand artwork digests are never rebound.
- `icon_review.py <manifest> --output <html>` validates typed representative contexts, exact source digests/routes/selectors/labels, wide/mobile host viewports, applicable host states (a `selected` host state declares the ARIA attribute that exposes it), existing/custom/no-icon alternatives or a schema-1.2 drawing-style comparison with optional digest-bound per-state assets, complete non-selected candidate coverage, SVG metadata/source/license consistency, selection/verdict coherence, safe local paths, and output/input non-aliasing, then emits a deterministic LF-normalized self-contained comparison sheet on every platform. The sheet and validator do not choose or visually approve the winner; inspect the claimed winner and closest rejection in the real host.
- `glyph.py build <spec> -o <dir> [--sheet <html>]` reads at most 256 KiB of strict JSON, compiles tokens and grid-snapped primitives into centerline geometry, refuses every invalid field, coordinate, overshoot or cut-out with all problems listed, then renders outline, solid and duotone SVGs plus metadata into a sibling staging directory, validates each SVG with `asset_quality.py`, and moves files into place only when all pass (exit 1 and nothing published otherwise). `check` runs the same compilation and lints without writing.
- `contrast.py <foreground> <background> [--minimum N | --large | --non-text]` parses exact opaque CSS colors, computes relative luminance/ratio against 4.5:1 by default, 3:1 for the large-text/non-text presets or a finite 1–21 minimum, and exits 0 PASS, 1 FAIL or 2 for invalid colors/arguments (one stderr line, no traceback).

- `iso.py render <scene> [-o <svg>] [--manifest <json>] [--no-labels]` reads a scene under a 1,000,000-byte budget, decides schema 1.0, 1.1 or 1.2 from the declared schema and the features used (before computing geometry, because 1.2 changes object geometry and defaults), loads and re-serializes any icon SVGs beside the scene file, collects every field, range, text, id, budget, icon, intersection, connector-level, routing, hidden-marker and cyclic-occlusion problem before refusing (exit 1, one `iso.py: error:` line each, nothing written), renders each primitive's paint-ordered face/outline/detail/text operations, sorts objects and connectors back to front, fits the viewBox to all geometry plus padding (1.2: on a whole-pixel origin, snapping vertical and horizontal hairlines to pixel centers), and atomically writes LF-only SVG and manifest files; label-fit estimates and the 1.2 scale and label-collision checks become warnings with exit 0. `--no-labels` drops every text op after rendering, under any schema. It refuses to overwrite the scene file.

These are deterministic structural evidence, not rendered design approval.

## 7. Behavioral and rendered evaluation

`python evals/designer-behavior/run_eval.py` loads deterministic equivalence, ambiguity, delta, preservation, discretion, dataset-absence, progressive-disclosure, and six materially different scope traces. Each authored trace declares the seven whole-system uncertainty dimensions as booleans; no task or free-form phrase is matched to a vocabulary. Exact per-case reference/process/artifact/stop/escalation contracts and exact progressive-route reasons prove both sides: narrow work cannot silently gain ceremony, every documented consequential dimension prevents flattening, high-consequence Direct work cannot omit relevant failure-mode proof, and the structurally closed Delivery section cannot regain an unscoped workshop obligation. It rejects hidden classification, automatic assets/motion, recipe keys, or obsolete datasets; it never invokes a model/host, observes reference loading, or scores creativity/layout/style.

`evals/designer-behavior/HOST-PROBES.md` is a separate bounded observation series for the configured GPT-5.6 Luna/max host. It records a pre-change control and current narrow, shared, medium, high-consequence, and Portfolio tasks with task fingerprints, available tools/context, actual loaded references, process activations/skips, implementation/proof depth, observable timing, and unknown token/runtime-identity fields. It is not generated by the deterministic runner and does not establish Snowe causation or general model behavior.

Rendered proof has five implementations:

- Goodturn image-led bicycle commerce;
- Doppler expressive-motion soda campaign;
- Larkhaven public-service journey;
- Relay North keyboard-first warehouse workspace;
- Morrow typographic editorial issue.

Each new forward-test includes causal decisions, a strongest rejected alternative, responsive transforms, live interactions, QA, and six screenshots. `benchmarks/CROSS-BENCHMARK.md` audits unexplained repetition.

`evals/icon-decisions/comparison.html` is deterministically regenerated from its manifest and exact assets. Browser smoke verifies the three decisions/eight candidates, comparison target sizes/states, containment and self-containment, repository-derived source digests/routes/selectors/labels, and every selected/rejected candidate inside its owning host at exact wide/mobile viewports and declared states. The selected Goodturn dialog X, Goodturn custom fit, and Larkhaven no-icon choices are verified in their actual owners; dialog challengers render in the same host shell. Smoke also binds per-state asset bytes and requires a declared `selected` host state to be exposed through `aria-pressed`, `aria-current`, or `aria-selected`; the checked manifest exercises neither because no current owning component has a selected-state icon. Human inspection supplies the optical/metaphor/family-fit verdicts.

`node scripts/browser-smoke.mjs --smoke [--scenario <slug>]` serves the repository, launches system Chrome/Chromium through CDP, and checks selected or all scenarios at relevant wide/intermediate/mobile states, runtime/console/network failures, assets, semantics, overflow, interactions/focus, mobile navigation, and reduced motion. `--capture` regenerates the 18 forward-test JPEGs; `--capture-goodturn-workshop` regenerates the Goodturn workshop image after icon changes.

## 8. Public contributor-context maintenance

**Trigger:** a change affects repository structure, contributor guidance, architecture claims, validation contracts, or ignore rules.

1. Root `AGENTS.md` routes the contributor through the public atlas and treats any `.codex/CURRENT_TASK.md` checkpoint as optional local state.
2. `.agents/skills/atlas-maintainer/SKILL.md` scopes documentation review to claims the final diff could invalidate.
3. `scripts/atlas/generate_atlas.py` derives `repo-map.md` from tracked files plus nonignored candidate additions, so ignored local files cannot affect generated public context.
4. `scripts/check_contributor_context.py` verifies the 25 required public paths, public/private ignore behavior, non-tracking of private path classes, and optional-checkpoint language.
5. Structural changes run atlas `--write`; every completed implementation runs atlas `--check`.

**End state:** the public candidate is self-contained and reproducible from a fresh clone, while task/session state remains local.

## 9. CI validation and Pages publication

GitHub Actions runs four independent surfaces:

1. strict contributor-context validation plus atlas freshness on Ubuntu/Python 3.13;
2. `compileall` plus all unittests on Python 3.11/3.13, Ubuntu/Windows;
3. the designer-behavior runner on Ubuntu/Python 3.13;
4. the dependency-free browser smoke on Ubuntu and Windows/Node 22/system Chrome.

CI does not perform aesthetic certification, manual browser review, lint/format/type/coverage, packaging, deployment, or release publication.

Active publication uses GitHub Pages `build_type:legacy`, source `codex/doppler-pages:/`. The branch contains an exact snapshot of `benchmarks/soda-campaign/` at its root plus `.nojekyll`, bypassing Jekyll while repository Actions remain disabled. Updating `main` alone does not update that snapshot; publication must also update the source branch. Verify the Pages settings and public HTML/CSS/JavaScript/assets after publication. The independent `.github/workflows/pages.yml` remains an inactive path-filtered alternative with no benchmark build step.

## Identity and mixed-control acceptance

1. Establish the symbol's actual role before source/metaphor choice. Verify supplied third-party artwork and usage separately from custom product-symbol exploration; unavailable source proof remains UNKNOWN with useful visible wording preserved.
2. Imported SVGs explicitly select `brand-mark`; unchanged artwork/usage bindings, supplied opaque paint and a relative decimal-rounding envelope supplement the default validator (whose exact bounded curve extrema both profiles share) without weakening ordinary icon checks. Schema-1.2 comparison contexts bind the exact identity and refuse custom substitutes.
3. For mixed rows, identify real visible control owners independently of captions/help/errors, choose the intended axis and inspect actual rendering. Schema-1.1 geometry checks measure that declared relation with a justified tolerance; wrapped rows can use a different reference. A blocking shift needs an owner repair and confirming render.
4. Run `node scripts/identity-alignment-proof.mjs`: copied-product observation, actual weak/corrected geometry, native glyph sizes, supplied image loading, brand-distortion/icon-shrink mutations and local action states. Human optical judgment and source authority remain distinct.

## Checked corrections and installation migration

Correction commands validate explicit input, acquire the existing project identity/lock via `locked_project_state`, load/validate CORRECTIONS.json, perform the permitted transition, and atomically publish the complete journal. The journal is opt-in: multi-session correction work or an explicit user request. No packet is generated. `unavailable` records, on an implemented record, why one criterion's evidence cannot be produced; the record stays BLOCKED with that reason listed until update, verify or supersede. Record is idempotent for identical IDs/content; conflicting reuse fails. Verify binds every source owner and all required criterion results. Read-only integrity checks compare current definition/proof with the recorded snapshot before filtering; a mismatched current scope cannot hide its last recorded or most recently verified obligation. Legacy unbound verification and drift require explicit fresh verification. Check also detects source/artifact changes and follows supersession across later scope edits. The decision ledger remains untouched. Every command requires an existing workspace directory. Missing state for a read-only check returns an empty scoped result (`journal: absent`) without creating a directory, unless other identities in the workspace already have journals; then `check` reports `NO_JOURNAL` (exit 4) with `known_projects` so a mistyped identity cannot pass. Scope owner comparison normalizes `./` prefixes.

Explicit legacy migration validates separate source/canonical/legacy/backup paths, completes the canonical installation, fingerprints and locks the regular legacy tree, writes a digest manifest outside discovery, and renames the old tree into that archive. Post-move failure restores the old path when identity still matches. If the process dies after rename, a repeated run finds and verifies the manifest-bound archive. Differing legacy files are preserved rather than merged or deleted; ordinary install does not silently migrate them.

## Visual disposition and correction closure

1. Author the state question, intended attention, visible cues and competing elements before evaluating the candidate.
2. Scope affected owners/dependencies and explicit browser combinations plus whole/detail targets. `observe.mjs` replays local states, measures and captures immutable evidence; missing probes, dependency drift or unsettled output fail observation.
3. Write schema 3 with a separately bound schema-2 attention contract and visual-system revision. `visual_review.py` checks source closure, actual environment, complete combinations, every detail assessment, relationships and current bytes. Preserve historical schema-1/2 records; they cannot supply new PASS.
4. New visual correction receipts require method, explicit KEEP and either a bound report or a host-browser capture. For a report the journal follows nested evidence and checks source-owner/state/viewport coverage; for a host capture (any app the static observer cannot serve) it checks the hash-bound image, its format and provenance fields, never the pixels. Historical inline receipts need renewed verification. The accepted ledger remains untouched.
