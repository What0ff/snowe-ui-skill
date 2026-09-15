# CLI Reference

Use the CLI for deterministic local evidence retrieval, a Portfolio/open-inquiry packet, identity-bound project decision persistence, stack guidance, structural SVG validation, and representative-control icon comparison. It does not design or aesthetically evaluate the rendered result for the agent.

## Runtime

```text
python <skill-directory>/scripts/search.py --help
python <skill-directory>/scripts/asset_quality.py --help
python <skill-directory>/scripts/icon_review.py --help
python <skill-directory>/scripts/contrast.py --help
```

Use an available Python 3 interpreter. Do not install or modify system Python merely to run Snowe without user authorization.

## Open a Decision Packet

Open the packet only for proportionate Portfolio/open-inquiry work or when the caller explicitly requests it. A bounded Direct correction skips it; ordinary Focused work uses a compact record for the affected decision and sibling proof.

```text
python <skill-directory>/scripts/search.py \
  "Bicycle retailer for urban riders; fit confidence before purchase; responsive web" \
  --decision-packet --format markdown --project-name "Project Name"
```

`--decision-packet` (short form `-dp`) preserves the brief verbatim and returns unresolved product, architecture, art-direction, imagery, custom-graphic, motion, responsive, research, and evaluation questions. It does not detect the language, classify vocabulary, infer a domain/platform/work mode, or invent pressures. Unknown and ambiguous framing remains explicitly unresolved.

Local analogs are also off by default. Add a caller-chosen lexical query only when a product analogy can change an open decision:

```text
python <skill-directory>/scripts/search.py \
  "Городской магазин велосипедов; уверенность в посадке до покупки" \
  --decision-packet --analog-query "bicycle retailer fit"
```

`--analog-query` ranks at most three subordinate product-catalog matches. It is not semantic confidence, does not expand the brief, and changes no situation or architecture field when results are absent.

Use `--format json` for structured evaluation or tooling. When combined with `--persist`, stdout remains one valid packet JSON document and the human persistence confirmation is written to stderr. `--json` belongs to domain/stack search and cannot be combined with a decision packet.

The historical `--design-system` / `-ds` spelling is a compatibility alias for the same open packet. It does not invoke the old recipe generator. New documentation and tooling should use `--decision-packet`.

Treat the packet as a starting workbench. Resolve product truth, generate real candidates, compare proof slices, implement, and render according to the skill workflow. Do not deliver the packet as the design.

## Persist Design Intelligence

```text
python <skill-directory>/scripts/search.py \
  "Healthcare scheduling across referral, booking, visit, and follow-up" \
  --decision-packet --persist --project-name "Care Flow" \
  --output-dir <project-directory>
```

This writes:

```text
<project-directory>/design-intelligence/care-flow/PROJECT.json
<project-directory>/design-intelligence/care-flow/BRIEF.md
<project-directory>/design-intelligence/care-flow/DECISIONS.md
```

- `PROJECT.json` binds the exact explicit project identity to its slug. A different identity that normalizes to the same slug is refused, as is a shared-hardlink/inode manifest.
- `BRIEF.md` is atomically regenerated from the current inquiry.
- `DECISIONS.md` is created only when absent and then preserved byte-for-byte. A shared-hardlink/inode ledger is refused so preserving it cannot mutate another file. Record accepted causal decisions, scope, evidence, risk, and revisit trigger there; do not turn hypotheses into facts.

Add an unresolved page inquiry:

```text
python <skill-directory>/scripts/search.py \
  "Product selection and fit evidence" --decision-packet --persist \
  --project-name "City Cycles" --page "find-a-bike" \
  --output-dir <project-directory>
```

This adds:

```text
<project-directory>/design-intelligence/city-cycles/pages/find-a-bike.md
```

The file asks for the page job, content/objects, entry/exit, candidate architectures, responsive transformations, states, and proof. It does not classify the page or prescribe sections. `--page` and `--output-dir` require `--persist`; persistence requires a decision packet and an explicit `--project-name`. One per-project lock serializes manifest, brief, ledger, and page publication. Project, brief, ledger, and page publication use complete atomic writes; page identity and parent-directory checks run before BRIEF publication and again immediately before page publication; accepted ledger bytes are never regenerated. Windows short names are expanded to a shared long lexical spelling without resolving redirects, and both spellings are rechecked before locking or writing. Project/page slug collisions, Windows-reserved identities, malformed identity manifests without a safe recovery basis, and symlink/junction/reparse paths are refused rather than followed or overwritten.

Use this precedence:

```text
current explicit requirements and verified repository/product/brand facts
> accepted scoped decisions with evidence and revisit triggers
> current rendered/measured learning
> open brief/page inquiry
> labeled local analogs and generated hypotheses
```

## Search Local Evidence

```text
python <skill-directory>/scripts/search.py "query" --domain <domain> --max-results 5
python <skill-directory>/scripts/search.py "query" --domain <domain> --json
```

Every result reports a **source role** and **use boundary**. Ranking is English-oriented lexical BM25 over a bundled snapshot. A top row is not semantic classification, current external truth, or a design selection.

| Domain | Evidence role |
|---|---|
| `product` | Product analogs and concern prompts; never project identity |
| `google-fonts` | Bundled font metadata snapshot; verify current official files and license |
| `ux` | Issue prompts and heuristics to verify in the actual flow |
| `web` | App-interface/accessibility prompts; verify platform applicability |
| `chart` | Unsourced encoding/accessibility prompts; unsupported exact thresholds, threshold-bearing use/avoid prose, palettes, grades, libraries, and interaction prescriptions are withheld |
| `react` | React/Next performance prompts; verify current repository/version |
| `icon-concepts` | Role-first metaphor prompts and ambiguity warnings |
| `icon-families` | Source discovery snapshot; verify current official source/license |
| `icon-candidates` | Exact known glyph/import hints for one named family |
| `icons` | Legacy concrete icon-name lookup |

There is intentionally no layout, landing, style, palette, typography-pairing, or motion-preset domain. Those catalogs were removed because their bundled combinations acted like solutions even when labeled as historical evidence.

Use concrete queries with the unresolved decision and context, not `modern app`. Query several domains only when each can change a decision. External current research remains necessary for unstable, high-leverage, or unsupported questions. Lexical catalogs may be English-oriented; that limitation affects only an explicitly requested lookup, never decision-packet framing.

For `icon-candidates`, name exactly one supported family per query so results remain auditable. Repeat exact-glyph lookup across sources, then render finalists in the same component. Do not use package count or catalog thumbnails as visual evidence.

## Search Stack Guidance

```text
python <skill-directory>/scripts/search.py \
  "accessible dialog focus restoration" --stack react --max-results 5
```

Supported stack datasets:

```text
react, nextjs, vue, svelte, astro, swiftui, react-native, flutter,
nuxtjs, nuxt-ui, html-tailwind, shadcn, jetpack-compose, threejs,
angular, laravel, javafx, wpf, winui, avalonia, uno, uwp
```

Use the repository's actual stack. Stack rows are bundled implementation guidance, not proof of current API behavior; check current official documentation when versions, platform behavior, or dependencies can have changed.

Every stack response includes the same top-level evidence boundary as domain retrieval plus `documentation_coverage` counts for returned rows with and without a `Docs URL`. A URL is only a discovery pointer; it does not prove that the source is primary or current. When any returned row has no URL, both text and JSON output say that the row remains unsourced bundled guidance until independently verified.

## Validate Custom SVG Structure

Prepare an SVG and adjacent JSON metadata, then run:

```text
python <skill-directory>/scripts/asset_quality.py \
  path/to/icon.svg --metadata path/to/icon.metadata.json
```

Use `--json` for machine-readable output.

Required metadata fields:

```json
{
  "name": "cargo-rack",
  "asset_type": "interface-icon",
  "role": "interface icon",
  "grid": 24,
  "live_area": {
    "min_x": 2,
    "min_y": 8,
    "max_x": 22,
    "max_y": 16
  },
  "drawing_language": {
    "mode": "stroke",
    "stroke_width": 1.75,
    "linecap": "round",
    "linejoin": "round",
    "corner_language": "small mechanical radii",
    "detail_budget": "one cargo-rack outline and two supports; no secondary detail"
  },
  "target_sizes": [16, 20, 24],
  "source": "repository-owned custom drawing",
  "license": "project-owned",
  "accessibility_owner": "owning labeled button; SVG decorative",
  "provenance": {
    "kind": "original",
    "creator": "project icon author",
    "source_ref": "design-intelligence/icons/cargo-rack.md",
    "reviewed": "2026-08-23",
    "sha256": "<exact lowercase SHA-256 of icon.svg bytes>"
  },
  "evidence": {
    "source": {
      "kind": "local",
      "path": "source-record.md",
      "sha256": "<exact lowercase SHA-256 of source-record.md bytes>",
      "locator": "#cargo-rack"
    },
    "license": {
      "path": "LICENSE.txt",
      "sha256": "<exact lowercase SHA-256 of LICENSE.txt bytes>"
    }
  }
}
```

Ordinary interface icons must declare unique positive 16, 20, and 24 px targets; add every other real implemented size. Required strings must be specific and non-placeholder, the numeric grid must match the root `viewBox`, the declared live area must contain the painted geometry, the drawing mode/weight/caps/joins must match the SVG, and the provenance digest must exactly match the SVG bytes. `evidence.source` and `evidence.license` are deterministic structured bindings: local records use metadata-relative safe regular-file paths and exact byte digests, with an optional `#fragment` only as an explicit locator; external source records must say `verification: "unverified"` and retain a canonical HTTPS `provenance.source_ref`. The validator never infers evidence paths by parsing human-readable source or license prose.

The strict self-contained subset rejects event handlers; document/entity/stylesheet declarations; nested SVG viewports; executable, linked, animated, text, embedded, styled, external, unknown, or namespaced content; all URI and local-fragment references; transforms, masks, filters, and clipping; unsupported attributes; malformed or clipped geometry; collapsed/conflicting root dimensions; non-`currentColor` paint; SVG-level muted opacity; and drawing-language contradictions. Round/bevel joins are supported; miter geometry is rejected because the current deterministic bounds proof cannot certify its spike extent. A structural `PASS` cannot prove source/license truth, recognition, silhouette, optical balance, metaphor, or family/UI fit.

## Compare Existing, Custom, and No-Icon Candidates

After exact candidates and a real role are known, create a compact manifest and generate a self-contained representative-control sheet:

```text
python <skill-directory>/scripts/icon_review.py \
  path/to/manifest.json --output path/to/comparison.html --json
```

The manifest binds every SVG candidate to its validated metadata name, provenance kind, explicit asset SHA-256, metadata provenance digest, and every context target size. It rejects duplicate SVG bytes masquerading as different candidates, custom candidates without original provenance, unsafe local host routes, malformed/deep/extreme-number JSON or Unicode scalar inputs, uninspectable paths, invalid selection/verdict combinations, and repository-derived contexts whose source file is absent. Repository-derived host proof must select a candidate; use `representative` evidence for unresolved `REJECT`/`UNKNOWN` contexts. Its explicit `host_proof.state_map` must cover every declared comparison state exactly once with the canonical same-name host state, except `high-contrast`, which maps to the exercised browser `forced-colors` state. A button-clone no-icon candidate must use the exact visible label of its owning control. It renders the same labels and declared states for existing, custom, and no-icon alternatives. A no-icon alternative renders visible UI truth once rather than a blank icon-sized cell.

The sheet is representative comparison evidence, not a pixel-identical host render and not an automatic decision. Inspect it in a browser at wide and narrow viewports, then render any claimed winner and the closest rejected alternative inside the actual owning component beside real neighbors. Record optical and semantic selection/rejection as human visual judgment. See the checked operational proof in `evals/icon-decisions/` in the source repository.

New icon comparison manifests use schema `1.1` and explicit `lang` (language tag) and `dir` (`ltr`, `rtl`, `auto`) on every context. Version `1.0` remains readable with `en`/`ltr` defaults. The attributes belong to the preview content; English inspector metadata retains its own language. The renderer handles long headers and text alternatives with wrapping and height growth, not clipping. Language is never inferred from label vocabulary.

For identity-bound correction commands, JSON schemas, proof requirements and exit codes, use [correction-memory.md](correction-memory.md#checked-journal-commands). These commands work independently of decision-packet generation and preserve an existing `DECISIONS.md`. A changed definition/proof or legacy verification without its snapshot requires explicit re-verification; a scope edit cannot hide the last confirmed obligation. See the journal reference for the separate `list.review_required` result and `check` exit dispositions.

## Check an Exact Opaque Color Pair

```text
python <skill-directory>/scripts/contrast.py "#18201B" "#F4F0E6" --minimum 4.5
```

The helper accepts `#RGB`, `#RRGGBB`, `rgb(r,g,b)`, `black`, and `white`. It uses WCAG relative-luminance contrast math and returns a nonzero exit code when the exact pair fails the requested minimum. It deliberately rejects alpha, gradients, images, and effects because those require rendered contextual measurement.

## Interpret Output Honestly

- `source_role` explains what a dataset can contribute; `warning` states what it cannot decide.
- Empty or low-quality lexical results mean the local snapshot has little evidence, not that the design space is empty.
- Retrieved numeric claims are unverified until traced to a credible current source; unsupported chart thresholds, threshold-bearing use/avoid prose, grades, palette values, library advice, and interaction prescriptions are not returned at all.
- A contrast calculation applies only to its exact solid rendered pair; imagery, gradients, transparency, effects, and states require contextual measurement.
- A font remains `UNKNOWN` until actual files/dependency, script coverage, license, metrics, representative content, fallbacks, and rendering are checked.
- An SVG `PASS` is structural only; an icon-comparison sheet proves only that the declared contexts rendered technically, not that the selected glyph is optically or semantically best.
- The CLI cannot select or certify architecture, art direction, imagery, custom asset quality, motion, usability, or taste. Those require causal comparison and implemented rendered evidence.
