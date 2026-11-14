# CLI Reference

The bundled scripts give deterministic local evidence: retrieval, a Portfolio decision packet, identity-bound persistence, stack guidance, icon-family building, SVG validation, icon comparison, isometric illustration, browser observation, visual-system contracts, checked visual reports and exact contrast. None of them designs or judges the rendered result.

## Runtime

```text
python <skill-directory>/scripts/search.py --help
python <skill-directory>/scripts/glyph.py --help
python <skill-directory>/scripts/asset_quality.py --help
python <skill-directory>/scripts/icon_review.py --help
python <skill-directory>/scripts/contrast.py --help
python <skill-directory>/scripts/iso.py --help
```

Use Python 3.11+ (`python -I` works); never install or modify system Python for Snowe without user authorization. `search.py` exits `0` on success, `1` when a lookup reports an error (stderr; with `--json` the error object stays on stdout) or another run holds a persistence lock, and `2` for invalid arguments or an unusable `--output-dir`.

## Open a Decision Packet

Open a packet only for Portfolio work or when the caller asks.

```text
python <skill-directory>/scripts/search.py \
  "Bicycle retailer for urban riders; fit confidence before purchase; responsive web" \
  --decision-packet --format markdown --project-name "Project Name"
```

`--decision-packet` (`-dp`) keeps the brief verbatim and returns unresolved product, architecture, art-direction, imagery, custom-graphic, motion, responsive, research and evaluation questions. It never detects language, classifies vocabulary, infers domain, platform or work mode, or invents pressures.

Local analogs are off by default; add a caller-chosen lexical query only when an analogy can change an open decision:

```text
python <skill-directory>/scripts/search.py \
  "Городской магазин велосипедов; уверенность в посадке до покупки" \
  --decision-packet --analog-query "cycling retail shop"
```

`--analog-query` ranks at most three subordinate product-catalog matches; it is not semantic confidence, does not expand the brief, and changes no situation or architecture field when nothing matches.

Declare known work mode, platforms, facts or pressures in a file; the runtime never derives them:

```text
python <skill-directory>/scripts/search.py \
  "Seasonal hand-off for field crews" \
  --decision-packet --declared-context context.json
```

```json
{
  "work_mode": "evolution",
  "platforms": ["shared kiosk", "printed fallback"],
  "facts": ["The existing visual system is coherent and must be preserved."],
  "pressures": ["Protect the seasonal hand-off ritual crews already rely on."]
}
```

The file is a UTF-8 JSON object: `work_mode` is nonempty text, `platforms`, `facts` and `pressures` are arrays of nonempty strings, and other keys pass through to `situation.other_declared_context`. Declarations mark framing `PARTIALLY_DECLARED` and appear in the packet and a persisted `BRIEF.md`; they are caller claims whose provenance still needs checking.

`--format json` gives structured output; with `--persist`, stdout stays one packet JSON document and the persistence confirmation goes to stderr. `--json` belongs to domain and stack search only. `--design-system` / `-ds` is a compatibility alias for the same packet, not the old recipe generator. The packet is a starting workbench, never the delivered design.

## Persist Design Intelligence

```text
python <skill-directory>/scripts/search.py \
  "Healthcare scheduling across referral, booking, visit, and follow-up" \
  --decision-packet --persist --project-name "Care Flow" \
  --output-dir <project-directory>
```

This writes `PROJECT.json`, `BRIEF.md` and `DECISIONS.md` under `<project-directory>/design-intelligence/care-flow/`:

- `PROJECT.json` binds the exact project identity to its slug; another identity with the same slug, or a shared-hardlink/inode manifest, is refused.
- `BRIEF.md` is atomically regenerated from the current inquiry; `--page` keeps an existing project brief, creates one only when absent, and puts the page brief into the page inquiry. The brief is stored verbatim, so keep credentials, personal data and internal hosts out: persistence warns on stderr (and returns `sensitive_content`) for likely secrets, emails or private hosts and never redacts silently.
- `DECISIONS.md`, the decision ledger, is created only when absent and then preserved byte for byte; a shared-hardlink/inode ledger is refused. It holds accepted causal decisions with scope, evidence, risk and revisit trigger, never hypotheses as facts.

The confirmation prints the resolved project directory and marks each file `written` or `preserved` (stdout, or stderr with `--format json`). An `--output-dir` that is or runs through an existing file is refused with that file named. If another run holds the project lock (Windows gives up after about ten seconds; POSIX waits), the command exits `1` with `Another persistence operation is active`; retry afterwards.

Add an unresolved page inquiry with `--page`:

```text
python <skill-directory>/scripts/search.py \
  "Product selection and fit evidence" --decision-packet --persist \
  --project-name "City Cycles" --page "find-a-bike" \
  --output-dir <project-directory>
```

It writes `pages/find-a-bike.md`, asking for the page job, content and objects, entry and exit, candidate architectures, responsive transformations, states and proof, without classifying the page or prescribing sections.

`--page` and `--output-dir` require `--persist`, which requires a packet and an explicit `--project-name`. One per-project lock serializes manifest, brief, ledger and page writes, each complete and atomic; page identity and parent-directory checks run before `BRIEF.md` is published and again before the page; accepted ledger bytes are never regenerated. `--output-dir` (default: current directory) is resolved once to its real path, so redirected ancestors such as macOS `/tmp` work and Windows short names expand, and the resolved path is rechecked before locking or writing. Slug collisions, Windows-reserved identities, malformed manifests without a safe recovery basis, and any symlink, junction or reparse point at or below the directory are refused.

A persisted brief or page inquiry ranks just above local analogs and generated hypotheses in the [source precedence](../SKILL.md#evidence-and-authority).

## Search Local Evidence

```text
python <skill-directory>/scripts/search.py "query" --domain <domain> --max-results 5
python <skill-directory>/scripts/search.py "query" --domain <domain> --json
```

Every result reports a **source role** and **use boundary**. Rows from numbered catalogs start with `No`, a stable row id within the named file (removed rows leave gaps), so a finding can cite `charts.csv` row 3; `data/CATALOGS.md` records each catalog's source, dates, row count and license. A top row is not semantic classification, current external truth or a design selection.

Ranking is English-oriented lexical BM25 over a bundled snapshot:

- Query and rows share one normalization: case folding, a small English stopword list (`for`, `the`, `vs`, ...), light stemming (`rerenders`, `rerendering` → `rerender`; `lists` → `list`), and hyphen compounds indexed split and joined (`re-render` matches `rerender`). Non-English words pass through unstemmed; there is no synonym table or query expansion.
- The name column (`Issue`, `Product Type`, `Family`, `Guideline`, ...) counts three times, `Keywords` and `Category` twice, other searched columns once; UX, React and mobile lookups also search `Do`.
- An exact name match ranks first, then names starting with the query (`IBM Plex Sans` before `IBM Plex Sans Condensed`), then phrase overlap.
- Scores scale with the share of distinct query terms matched; when some row matches several terms, rows matching fewer than half as many drop out, so fewer than `--max-results` can return.
- `unmatched_terms` (JSON) lists query words found in no searched column, also named in the use boundary; they did not affect ranking (`geometric` cannot match the font index, which has no construction or mood vocabulary).

| Domain | Evidence role |
|---|---|
| `product` | Product analogs and concern prompts; never project identity |
| `google-fonts` | Slim Google Fonts metadata index (snapshot 2026-11-12): category, stroke, subsets, primary script, axis ranges, styles, designers, license; no mood or construction terms, so search by family, category, script, or designer |
| `ux` | Issue prompts and heuristics to verify in the actual flow |
| `mobile` | iOS, Android, and React Native app-interface/accessibility prompts (`app-interface.csv`); not web or browser guidance |
| `web` | Compatibility alias of `mobile` (same catalog and results); the rows are mobile-app guidance despite the name |
| `chart` | Unsourced encoding/accessibility prompts; unsupported exact thresholds, threshold-bearing use/avoid prose, palettes, grades, libraries, and interaction prescriptions are absent from the bundled catalog |
| `react` | React/Next performance prompts; verify current repository/version |
| `icon-concepts` | Role-first metaphor prompts and ambiguity warnings |
| `icon-families` | Source discovery snapshot; verify current official source/license |
| `icon-candidates` | Exact known glyph/import hints for one named family |
| `icons` | Legacy concrete icon-name lookup |

There is no layout, landing, style, palette, typography-pairing or motion-preset domain: those catalogs were removed because their bundled combinations acted like solutions.

Query with the open decision and its context, not `modern app`, and search a domain only when it can change a decision; unstable or high-leverage questions still need current external research. The English-oriented limit affects explicit lookups only, never packet framing. For `icon-candidates`, name one supported family per query, repeat exact-glyph lookup across sources, and render finalists in the same component; package counts and thumbnails are not visual evidence.

## Search Stack Guidance

```text
python <skill-directory>/scripts/search.py \
  "accessible dialog focus restoration" --stack react --max-results 5
```

Supported stack datasets:

```text
react, nextjs, vue, svelte, astro, swiftui, react-native, flutter,
nuxtjs, nuxt-ui, html-tailwind, shadcn, jetpack-compose, threejs,
angular, laravel, javafx, wpf, winui, avalonia, uno
```

The `uwp` catalog was retired on 2026-11-12 (it targeted retired device families such as Windows 10 Mobile); `--stack uwp` returns an error naming `winui`, which covers choosing WinUI 3 and migrating UWP code. Use the repository's actual stack, and check official documentation when versions or platform behavior may have changed: rows are bundled guidance, not proof of current APIs. Rows start with their `No` id where the file has one, and each response carries the evidence boundary plus `documentation_coverage` counts of rows with and without a `Docs URL`. A URL is a discovery pointer, not proof of a primary or current source; output says when a returned row stays unsourced until verified.

## Build an Icon Family

`glyph.py` builds a custom family from one JSON spec: every glyph in `outline`, `solid` and `duotone`, each with metadata in the [validator's schema](#validate-custom-svg-structure). Nothing is written unless every output passes `asset_quality.py`.

```text
python <skill-directory>/scripts/glyph.py check family.json
python <skill-directory>/scripts/glyph.py build family.json -o icons/ --sheet icons/sheet.html
```

`build` copies the spec to `icons/<family>.spec.json` and writes `icons/<variant>/<glyph>.svg` with `<glyph>.metadata.json` (name `<glyph>-<variant>`, original provenance, source evidence bound to the copied spec, project-owned license). `--sheet` adds a self-contained contact sheet: every glyph and variant at 16, 20, 24 and 32 px in light and dark, label-less and squinted strips, and a tab bar with outline idle and solid selected. Identical input gives byte-identical output. Exit codes: `0` built or checked, `1` spec refused, output failed validation, or I/O error (nothing published), `2` invalid arguments. `--json` reports files, the validated count and warnings.

```json
{
  "schema": "1.0",
  "family": "larder-soft",
  "tokens": {"grid": 24, "padding": 2, "stroke": 1.5, "linecap": "round", "linejoin": "round",
             "radius": 3, "detail": "medium", "secondary_opacity": 0.22},
  "target_sizes": [16, 20, 24, 32],
  "metadata": {"creator": "product icon author", "reviewed": "2026-11-14"},
  "sheet": {"tabs": ["home", "search"]},
  "glyphs": [
    {"name": "home", "role": "go to the home screen", "keyline": "square", "shapes": [
      {"type": "path", "d": "M4 11 L12 3.5 L20 11 V20 H14.5 V15 H9.5 V20 H4 Z", "radius": 1.5}]},
    {"name": "search", "role": "search recipes", "keyline": "square", "shapes": [
      {"type": "circle", "center": [10.5, 10.5], "r": 6.5},
      {"type": "line", "from": [15.5, 15.5], "to": [20, 20]},
      {"type": "arc", "center": [10.5, 10.5], "r": 3.5, "start": 195, "end": 255,
       "role": "detail", "min_detail": "medium"}]}
  ]
}
```

Tokens: `grid` 16, 20, 24 or 32 (default 24); `padding` (default 1, 2, 2 or 3 by grid); `stroke` in grid units, a multiple of 0.125; `linecap` `round`, `butt` or `square`; `linejoin` `round` or `bevel` (miter cannot be bounded and fails validation); `radius`, the family corner radius; `detail` `low`, `medium` or `high` (default `medium`). Optional: `dot` diameter, `snap` construction grid (0.125, 0.25 by default, 0.5 or 1), `crisp` (default true) and `secondary_opacity` (0.12–0.6), which enables `duotone`. `metadata` requires `creator` and `reviewed` (an ISO date, not in the future) and takes optional `license`, `source` and `accessibility_owner`. Optional `variants` narrows the family, and `target_sizes` defaults to 16, 20, 24 and 32.

Coordinates are grid units on the construction grid, y pointing down; angles are degrees, 0 pointing right and 90 down.

| Type | Fields |
|---|---|
| `line` | `from`, `to` |
| `polyline` | `points`, optional `closed`, `radius` (default: family radius) |
| `path` | `d` with absolute `M L H V A Z`, circular arcs only; optional `radius` |
| `arc` | `center`, `r`, `start`, `end` in whole degrees |
| `circle` | `center` and `r`, or `fit: "circle"` |
| `ellipse` | `center`, `rx`, `ry` |
| `rect`, `rounded-rect` | `x`, `y`, `w`, `h`, or `fit` (`square`, `portrait`, `landscape`); optional `radius` (default 0, or the family radius) |
| `polygon` | `center`, `r`, `sides` (3–12), optional `rotation`, `radius` |
| `gear` | `center`, `r`, `root`, `teeth` (4–16), optional `tooth` fraction and `radius` |
| `chevron` | `tip`, `dir` (`up`, `down`, `left`, `right`), `span`, optional `depth`, `radius` |
| `arrow` | `from`, `to`, optional `head` |
| `dot` | `at`, optional `d` |

Every shape also takes `id`, `role`, `variants`, `min_detail`, `duotone_fill` and transforms. `role` is `body`, `detail` or `stroke`: closed shapes default to `body`, open ones to `stroke`, dots to `detail`. A body fills in solid and tints in duotone (`duotone_fill`), a detail becomes an even-odd cut-out from the body around it, and a stroke stays a positive mark. Transforms apply in order: `rotate` (multiples of 15°), `repeat` (`{count, step}`), `radial` (copies around `about`) and `mirror` (`x`, `y` or `xy`), with `about` defaulting to the grid center. Keylines on a 24 grid are a 20 circle, an 18 square, a 16 × 20 portrait and a 20 × 16 landscape. With a whole-pixel stroke and `crisp`, authored axis-aligned edges move to the nearest crisp pixel position, ties toward the center.

The builder lists every refusal: unknown fields, primitives or values; duplicate-key, non-finite or malformed JSON; off-grid coordinates; geometry outside the live area (curves need 0.002 units of clearance because SVG arcs are rebuilt from rounded endpoints); a stroke under 0.5 CSS px at the smallest target; solid cut-outs that cross a body's edge, overlap or lie outside every body; and families over 64 glyphs, 24 shapes per glyph, 64 shapes after repeats or 256 KiB. Warnings flag keyline mismatches, gaps under 1 px and slivers at the smallest target. A built family is structurally valid, not yet recognizable or optically right.

## Validate Custom SVG Structure

Start from the SVG: write the metadata skeleton, replace its placeholders, then bind digests and validate.

```text
python <skill-directory>/scripts/asset_quality.py path/to/icon.svg --init-metadata
python <skill-directory>/scripts/asset_quality.py \
  path/to/icon.svg --metadata path/to/icon.metadata.json --rehash
python <skill-directory>/scripts/asset_quality.py \
  path/to/icon.svg --metadata path/to/icon.metadata.json
```

- `--init-metadata` writes `<svg-stem>.metadata.json` beside the SVG (or at `--metadata`), never overwriting. It computes name, grid, a full-grid live area, the observed drawing language and the SVG digest; everything needing judgment stays a `<...>` placeholder that fails until a person replaces it. The default is original artwork under a project-owned license; `--provenance external` starts an imported skeleton (unverified source plus retained license file).
- `--rehash` is for an intentional edit: it recomputes the original-provenance digest and named local evidence digests, prints every changed, unchanged and skipped field, validates, and rewrites changed digests atomically as two-space-indented JSON. It never rebinds external or brand-mark artwork (restore the upstream bytes or re-import and review them), and writes nothing when a named evidence path is unsafe or unreadable.

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

Declare unique positive targets for the real slots: geometry is checked at the smallest size and the comparison manifest must cover every context size, so an 18 px owner declares 18. Source, license and accessibility declarations, exact grid and live area, a consistent drawing language, the provenance digest and safe local evidence bindings are required; external source truth stays unverified, and evidence paths are never inferred from prose. `grid` matches the viewBox width and height, and `live_area` is measured from the viewBox origin, so a Material Symbols `viewBox="0 -960 960 960"` declares `{"min_x": 0, "min_y": 0, "max_x": 960, "max_y": 960}`. Original artwork may declare `evidence.license` as exactly `{"kind": "project-owned"}`; external sources bind a retained license file.

Choose the drawing mode per role: `stroke` outlines only, `fill` solid shapes only, `mixed` one tone needing both, `duotone` a full-strength primary over a lighter secondary. A solid icon declares no stroke language:

```json
"drawing_language": {
  "mode": "fill",
  "stroke_width": 0,
  "linecap": "not applicable",
  "linejoin": "not applicable",
  "corner_language": "soft rounded silhouette",
  "detail_budget": "one solid shape and one evenodd counter at 16 px"
}
```

A duotone icon marks each painted element, or a `<g>` around it, with `data-icon-layer`, keeps all paint `currentColor`, and declares its one secondary tone:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" fill="currentColor" aria-hidden="true">
  <rect width="256" height="256" fill="none"/>
  <path data-icon-layer="secondary" opacity="0.2" d="M40 40h176v176H40z"/>
  <path data-icon-layer="primary" d="M24 24h208v16H24z"/>
</svg>
```

```json
"drawing_language": {
  "mode": "duotone",
  "stroke_width": 0,
  "linecap": "not applicable",
  "linejoin": "not applicable",
  "tones": {"secondary_opacity": 0.2},
  "corner_language": "square tile with a solid header bar",
  "detail_budget": "one tinted field and one solid bar at 16 px"
}
```

Every painted duotone element resolves to `primary` or `secondary`, and a primary is required. The secondary renders at exactly `tones.secondary_opacity` (0.12–0.6), its `opacity`, `fill-opacity` and `stroke-opacity` multiplying to that tone, while root and primary stay at 1. Undeclared tones, unknown or nested-changing layer values, a secondary without a primary, `tones` outside duotone, and layers in other modes fail. A stroked layer declares a positive `stroke_width` and concrete caps and joins; otherwise 0 and `not applicable`.

The default `interface-icon` subset accepts `svg`, `g`, `title`, `desc`, `path`, `circle`, `ellipse`, `rect`, `line`, `polyline` and `polygon` with their geometry attributes, `currentColor`/`none`/`transparent` paint, stroke, opacity, `display` and `visibility`, plus these inert or fixed-value attributes:

| Attribute | Accepted values | Where |
|---|---|---|
| `fill-rule`, `clip-rule` | `nonzero`, `evenodd` | any element |
| `aria-hidden` | `true` | any element |
| `focusable` | `false` | any element |
| `role` | `img` | root `<svg>` only |
| `data-slot` | one name token | any element |
| `class` | whitespace-separated name tokens; never changes validation | any element |
| `pathLength` | positive number | drawing elements |
| `vector-effect` | `none`, `non-scaling-stroke` (stroke bounded at the smallest target) | any element |
| `shape-rendering` | `auto`, `geometricPrecision` | any element |
| `data-icon-layer` | `primary`, `secondary` (duotone only) | drawing elements, `<g>` |

Root `width`/`height` are optional unitless or px lengths keeping the viewBox ratio; an unpainted `<rect>` or `<path>` covering the viewBox (the Phosphor and Tabler spacer) is ignored; compact SVGO arc flags (`a8 8 0 0116 0`) are accepted; path data must begin with a moveto.

The subset rejects event handlers; document, entity and stylesheet declarations; nested viewports; executable, linked, animated, text, embedded, styled, external, unknown or namespaced content; `id` and all URI and fragment references; transforms, masks, filters and clipping; other attributes and values; malformed or clipped geometry; collapsed root dimensions or a contradictory ratio; non-`currentColor` paint; muted opacity outside the duotone secondary; and drawing-language contradictions. Round and bevel joins pass; miter geometry (and `arcs`, which renders as miter) fails because its spike extent cannot be bounded. Square caps are bounded by their diagonal reach.

Two checks only warn: under `nonzero`, an inner subpath with the outer one's winding renders solid, so reverse it or declare `evenodd`; in `fill` and `duotone`, a subpath narrower than 1 CSS px at the smallest target can close up or vanish. A structural `PASS` proves neither source or license truth nor recognition, silhouette, balance, metaphor or fit.

For unchanged imported brand SVGs, declare `asset_type:"brand-mark"` with `brand:{schema:"1.0",identity:<exact identity>,variant:<supplied variant>,artwork:{path,sha256},usage:{path,sha256}}`. Other fields stay required and describe the supplied artwork; provenance is `external` with a canonical HTTPS URL, and `evidence.source` stays `{kind:"external",verification:"unverified"}`. `artwork` binds a retained upstream copy whose digest matches the delivered SVG and `usage` a reviewed local usage record, each a metadata-relative regular file within a 1,000,000-byte budget. The profile adds opaque `#RGB`, `#RRGGBB`, black and white paint and keeps every other check; it supports no gradients, masks or styles and certifies neither officialness, license nor context. Use another official variant or the host's asset proof for unsupported originals, never tracing, recoloring or flattening an identity to pass. Missing or stale records fail, but hashes cannot stop both self-authored records being rewritten, so primary-source review stays required, and a URL never permits remote references inside the SVG.

Both profiles bound curves by their actual extrema (including reflected smooth controls), not the control hull, within the 1,000,000-coordinate envelope. The imported profile tolerates 1e-7 of the smaller viewBox side for decimal rounding (under 0.000003 CSS px at 24 px); `interface-icon` keeps an absolute 1e-7, so a real overshoot still fails. Host clipping and appearance still need rendered inspection.

## Compare Existing, Custom, and No-Icon Candidates

Once exact candidates and a real role are known, write a manifest and generate a self-contained representative-control sheet:

```text
python <skill-directory>/scripts/icon_review.py \
  path/to/manifest.json --output path/to/comparison.html --json
```

The manifest binds each SVG candidate to its validated metadata name, provenance kind, asset SHA-256, metadata provenance digest and every context size. It rejects duplicate bytes posing as different candidates, custom candidates without original provenance, unsafe host routes, malformed, deep or extreme-number JSON and Unicode scalar inputs, uninspectable paths, invalid selection and verdict combinations, and repository-derived contexts whose source file is missing. Repository-derived host proof must select a candidate (unresolved `REJECT`/`UNKNOWN` contexts use `representative` evidence), and its `host_proof.state_map` maps every comparison state once to the same-name host state, except `high-contrast` → exercised `forced-colors`. A button-clone no-icon candidate uses its control's exact visible label; every alternative gets the same labels and states, and no-icon shows the visible UI truth once rather than a blank cell.

To decide a drawing style for one role, a schema-`1.2` interface context can set `"comparison_axis": "style"` instead of `"kind"`. Candidates may then share a kind, but at least two SVG candidates must each differ from every other in declared drawing style (mode, stroke width, caps, joins, duotone tone) in at least one state. A candidate may add `state_assets` keyed by declared non-default states, for example outline by default and solid when selected:

```json
{
  "id": "heart-outline-selected-solid",
  "name": "Outline, solid when selected",
  "kind": "custom",
  "asset": "heart-outline.svg",
  "asset_sha256": "<exact SHA-256 of heart-outline.svg>",
  "metadata": "heart-outline.metadata.json",
  "state_assets": {
    "selected": {
      "asset": "heart-solid.svg",
      "asset_sha256": "<exact SHA-256 of heart-solid.svg>",
      "metadata": "heart-solid.metadata.json"
    }
  },
  "source": "repository-owned favorite drawings",
  "license": "project-owned",
  "rationale": "Solid only marks the saved state."
}
```

Each state asset is validated, digest-bound and size-checked like the default, must differ from it, and is listed with its own name, digest, source and license. A combination's `id` need not equal one asset name but cannot borrow another's, and duplicates are detected on the bytes shown in every state. Brand contexts accept neither field. Repository-derived host proof may also exercise a `selected` state by declaring `selected_attribute` (`aria-pressed`, `aria-current` or `aria-selected`) and optionally `select_selector`, a control to click first; browser smoke requires that attribute, never a style alone, keeps the accessible-label check, and renders each candidate's state artwork in the host.

New manifests use schema `1.2`, with explicit `lang`, `dir` (`ltr`, `rtl`, `auto`) and `symbol_role` (`interface-icon` or `brand-mark`) on every context. Brand contexts also declare `brand_identity`, bind matching `brand-mark` metadata for every artwork candidate and reject `custom` substitutes; they may hold one supplied `existing` candidate or a visible-text `none` fallback without manufactured alternatives, and ordinary contexts cannot silently consume brand artwork. Versions `1.0` and `1.1` stay readable (`1.0` defaults to `en`/`ltr`); typed role fields need 1.2. The attributes apply to preview content, long headers and text alternatives wrap rather than clip, and language and role are never inferred from label vocabulary.

The sheet is representative evidence, not a pixel-identical host render or an automatic decision. Inspect it at wide and narrow viewports, render the winner and the closest rejected alternative inside the owning component, and record the optical and semantic choice as human judgment; source fidelity and usage still need primary-source and host review. A worked example is the [icon-decisions proof](https://github.com/What0ff/snowe-ui-skill/tree/main/evals/icon-decisions) in the source repository, not part of an installed skill.

## Draw an Isometric Illustration

`iso.py` turns a JSON scene in grid units into a deterministic, self-contained SVG. It owns projection, face shading, back-to-front order, connector routing and label placement; when to draw and how to compose stay in [illustration-craft.md](illustration-craft.md).

```text
python <skill-directory>/scripts/iso.py render scene.json -o scene.svg --manifest scene.manifest.json
```

Without `-o` the SVG goes to standard output. Exit `0` on success (label-fit warnings go to stderr and the manifest), `1` with one `iso.py: error:` line per problem when the scene is refused or a file cannot be read or written, and `2` for usage errors. An output path never overwrites the scene file.

```json
{
  "title": "Data platform",
  "desc": "Events flow through ingest into the processing core and on to the warehouse.",
  "id_prefix": "dp-",
  "unit": 36,
  "objects": [
    {"id": "floor", "type": "ground-grid", "x": -1, "y": -4, "w": 10, "d": 9, "pattern": "dots"},
    {"id": "ingest", "type": "stack", "x": 0, "y": 1.5, "w": 2, "d": 2, "count": 4, "label": "Ingest"},
    {"id": "core", "type": "chip", "x": 4, "y": 1, "w": 3, "d": 3, "label": "Process", "accent": true, "order": 1},
    {"id": "dwh", "type": "cylinder", "x": 4.7, "y": -3, "w": 1.6, "h": 1.8, "bands": 2, "label": "DWH", "order": 2},
    {"type": "connector", "from": "ingest", "to": "core", "accent": true, "order": 1},
    {"type": "connector", "from": "core", "to": "dwh", "from_side": "y-", "to_side": "y+", "order": 2}
  ]
}
```

- **Scene:** `projection` (`isometric` at 30 degrees, or `dimetric` 2:1), `style` (`line`: light faces with crisp outlines; `solid`: tonal faces without outlines), `unit` (px per grid unit, 8–96, default 32), `padding` (px), `stroke` and `detail_stroke` (px), `title` and `desc`, `id_prefix` (default `iso-`; give every SVG on a page its own), `colors` (fallback `#rgb` or `#rrggbb` per role: `top`, `left`, `right`, `stroke`, `detail`, `accent`, `text`, `grid`) and `objects`.
- **Coordinates:** x runs to the lower right on screen, y to the lower left and z up. A solid's `x`, `y` is the minimum corner of its footprint and `z` (default 0) its base. The visible faces are `top`, `x+` (right, darkest) and `y+` (left).
- **Solids** take `id`, `x`, `y`, optional `z`, `role`, `order` (flow step, 0–999) and `accent`. Labelled types take `label` (at most 40 characters) and `label_size` (px, default 11); those marked "face" also take `label_face` (`top`, `x+`, `y+`) and `label_axis` (`x` or `y`, top faces only).

| type | size fields | options |
|---|---|---|
| `box` | `w`, `d`, `h` | `radius`, `bands`, `glyph`, face |
| `slab` | `w`, `d`, `h` (0.25) | `radius` (0.2), `inset`, `glyph`, face |
| `stack` | `w`, `d`, `count` (2–12), `h` per slab (0.3) | `gap`, `radius`, `leds`, `front` (`x+`, `y+`), face |
| `chip` | `w`, `d`, `h` (0.3) | `pins` per side (default from size; pins reach 0.18 outside), `die`, `radius`, `glyph`, face |
| `cylinder` | `w` (diameter), `h` | `bands`, `glyph`; labels on top |
| `building` | `w`, `d`, `floors` (1–40), `floor_h` (0.55) | `windows` (`grid`, `ribbon`, `none`), `roof`, face |
| `card` | `w`, plus `d` when flat or `h` when upright | `orient` (`flat`, `x+`, `y+`), `t`, `radius`, `glyph`, `lines` (0–4) |
| `screen` | `w`, `h` | `orient` (`x+`, `y+`), `t`, `radius`, `lines` (0–6), `stand` |
| `tree` | `w`, `h` | `shape` (`round` needs `h` ≥ 1.1 `w`; `cone` needs `h` ≥ `w`) |
| `ground-grid` | `w`, `d` | `step`, `pattern` (`lines`, `dots`), `fade` (dots) |

Glyphs are `dot`, `ring`, `check`, `plus`, `bars`, `user`, `spark` and `play`.

- **Connectors** (`"type": "connector"`) join two solids: `from`, `to`, optional `id` (default `<from>-to-<to>`), `from_side` and `to_side` (`x+`, `x-`, `y+`, `y-`; by default the sides that face each other), `from_offset` and `to_offset` along the side, `via` (`[x, y]` waypoints), `start` (`none`, `dot`), `end` (`arrow` by default, `dot`, `none`), `gap` (0.3), `radius` of rounded bends (0.35), `z` (default: the base both objects share), `accent`, `role` and `order`. Routes run only along grid axes: straight when facing sides overlap and no offset is given, otherwise as an L or a Z.
- **Output:** every solid and connector is a `<g>` with `id="<prefix><id>"`, the classes `iso-obj` or `iso-link`, `iso-<type>` and, when set, `iso-accent`, plus `data-kind`, `data-role`, `data-order` and `data-paint`. A connector adds `data-from`, `data-to`, one `<path class="iso-path" pathLength="1">` with id `<group id>-path`, and its end markers. Faces carry `iso-t`, `iso-l` or `iso-r`, outlines `iso-o` and detail `iso-d`. Paint comes only from the embedded stylesheet as `var(--iso-<role>,<fallback>)`; labels are real `<text>` placed with a face matrix in `--iso-font`; strokes use `vector-effect: non-scaling-stroke`; nothing external is referenced. A title emits `role="img"` with `aria-labelledby`; without one the SVG is `aria-hidden`.
- **Manifest:** the projection, size and warnings, and for every group its id, kind, role, order, paint index, accent and projected bounding box in viewBox pixels. Connectors add their sides, length in grid units and path id.
- **Refusals:** unknown types or fields; missing, mistyped, non-finite or out-of-range numbers (coordinates within ±100, sizes up to 60, `z` from 0 to 60); duplicate ids or JSON keys; labels over 40 characters (title and description over 400) or containing control characters; intersecting volumes (each solid occupies its bounding box, including chip pins and screen stands; touching and stacking are allowed); connectors to unknown objects, between different levels without a shared `z`, leaving backwards, passing through a solid, too short for their arrow, or passing both behind and in front of one object; cyclic occlusion; and scenes over 200 objects, 1,000,000 bytes, 4,000 characters of text, 12,000 px per side or 20,000 drawn elements. Every problem found is reported in one run. Label-fit warnings estimate text width; they never refuse.

A render proves geometry and structure only. Composition, crowding, hidden arrows and label legibility need inspection at real size.

## Observe in a Browser

Prefer the host's browser tools when they support the app. The skill also ships an optional, dependency-free adapter for **Node 22+ with a system Chrome, Chromium or Edge**:

```text
node <skill-directory>/scripts/observe.mjs capabilities
node <skill-directory>/scripts/observe.mjs capture <workspace> <plan.json> <fresh-output-directory>
node <skill-directory>/scripts/observe.mjs compare <workspace> <before-receipt.json> <after-receipt.json> <comparison.html>
```

`capabilities` reports the browser found, `available`, and `reasons` when capture cannot run. Discovery tries `CHROME_PATH`, then standard Chrome, Edge and Chromium locations (`%ProgramFiles%`, `%ProgramFiles(x86)%`, `%LOCALAPPDATA%`; `/Applications`, `~/Applications`; `/usr/bin` including `microsoft-edge-stable`, and `PATH`), downloading nothing. Without Node or a browser, use the host's tools, report their real capabilities, and mark formal browser proof `UNKNOWN`. The adapter serves local static files only and refuses external or unbound assets: app servers, authentication, native apps, closed shadow roots and temporal canvas or video proof need the host and explicit environment records, and a static fixture never stands in for a working backend.

The Chromium sandbox stays on unless it cannot start (root on Linux, or a Linux container) or `--no-sandbox` / `SNOWE_OBSERVE_NO_SANDBOX=1` turns it off; `capabilities` reports why. A browser that exits before DevTools starts is named in the error, with the opt-out suggested on Linux. Usage mistakes exit `2`; capture failures print one `observe.mjs: error:` line and exit `1` (`SNOWE_OBSERVE_DEBUG=1` adds a stack). Headless capture hides native scrollbar paint for comparable geometry, so check scrollbar affordances with the host and never infer a scrollbar bug from these captures.

Observation plan schema `1.0` has `scope`, `sourceRoots` and `cases`:

```json
{"id":"mobile-selected","state":"selected","viewport":"390x844@1","theme":"light","input":"touch","motion":"reduced","context":"page","route":"/index.html","steps":[{"action":"click","selector":"#choose"}],"expect":[{"selector":"#choose","property":"attribute:aria-pressed","equals":"true"}],"probes":[{"selector":"main","pseudo":""},{"selector":".selection","pseudo":""},{"selector":".selection","pseudo":"::before"}],"details":[{"id":"selected-owner","selector":".selection","padding":12,"scale":2}]}
```

- **Viewport:** `<CSS width>x<CSS height>@<DPR>`, DPR 1–4 with up to two decimals, compared numerically with `devicePixelRatio`.
- **Matrix:** explicit combinations of affected states, breakpoints, themes, inputs and contexts, not a product of irrelevant dimensions; record why representative siblings suffice and which dependencies would require widening. Reduced motion can remove nodes, so plan the static layer.
- **Steps:** `click`, `fill` (`selector`, `value`), `key` (`Tab`, `Enter`, `Escape`, `ArrowDown`, `ArrowUp`, `Space`; `space` is accepted, a literal space and other names are rejected), `wait-for-selector`, `scroll-to-selector`. Keyboard cases use keys, touch cases dispatch touch. Reach loading and error states through local routes or explicit setup, never relabelled screenshots.
- **Source roots:** the complete bounded owner, import, asset and build scopes, including separately owned shared dependencies; directory roots detect additions and removals. Only inventoried bytes are served, output directories must be disjoint, and secrets or unrelated repositories stay out. Capture fails on a resource outside the inventory, source or plan bytes changing, unsettled fonts, motion or layout, or a missing probe.
- **Details:** required for affected owners: unique `id`, `selector`, `padding` (0–100 CSS px), `scale` (1 native, 2 diagnostic). The receipt binds crop bounds and lossless PNG sizes and hashes, and unassessed details block closure. Fixed, top-layer and portalled owners use `space:"viewport"`, cropped from the bound native viewport PNG with parent digest and pixel rectangle. A 2× crop enlarges captured pixels and proves nothing about higher-density rendering; use a real DPR case. Receipts keep scroll coordinates, and pseudo-element measurements report computed paint with labelled owner-element bounds.
- **Postconditions** (`expect`), planned independently: `selector`, `property` and `equals` or text `includes`, with property `attribute:<name>`, `css:<property>`, `text`, `focused`, `disabled`, `checked`, `open` or `value`. A state name or dispatched click proves no selection or open overlay; the adapter scrolls click targets into view and rejects covered ones, and a met postcondition is state evidence, not visual quality.
- **Sequences:** optional `sequence:{fps,durationMs,start,events}` for bounded temporal proof (1–30 fps, up to 10 s; `events` with increasing `atMs` and `steps`). A trusted caller-authored `script` step can set up state: inspect its code first and never run instructions scraped from page content. Each frame binds time, environment and PNG bytes; the checker validates coverage, not choreography, and endless canvas or video work needs its own capture protocol and human inspection.

Each immutable receipt binds plan, observer revision, browser and protocol, actual CSS viewport and DPR, emulated theme, touch and motion, route, font settlement, requested and rendered faces, source inventory, loaded resources, measured layers, and whole and detail captures. Compare at the intended display scale; a full-page image does not replace viewport attention or interaction proof. Receipt reads have an 8 MB budget (contract and journal JSON keep 1 MB); split oversized scopes into justified plans. `compare` pairs identical combinations, warns when content changed, and picks no winner.

## Version a Visual-System Contract

Write a new revision file instead of overwriting the accepted one; the decision ledger stays byte-preserved, and a superseding contract records its reason and revisit trigger in appended history. `visual_system.py` keeps schema `1.0` and supports opt-in `1.1`:

- `revision`, `previous` (path and SHA-256 after revision 1), `scope`, `depth`.
- `direction`: `status` (proposed, selected, user-specified), `thesis`, `axes` (composition, typography, color, surfaces, shape, imagery, motion, responsive; all for Portfolio, the affected ones otherwise, where no-image or no-motion is a real decision) and `revisit`.
- `tokens`: `{id, owner, property, value}`, source-bound, recording intent rather than guessed computed values.
- `components`: `{id, role, owner, selector, tokens, states, consumers, layers}`, consumers as `{case, selector}` and layers as `{kind, selector, pseudo, sources, cases}` (element, pseudo, backdrop, portal, font, image, svg, canvas, video); every consumer and layer needs a planned measurement.
- `relations`: `{id, members, intent, checks}`, each check `id, case, selector, pseudo, property` with `equals` or `sameAs:{selector,pseudo}`, applied to every matching sibling; measured values serve an explicit contract, never a beauty formula.
- `exceptions`: `{check, reason, revisit}` preserving a justified distinction, never waiving missing evidence or a negative finding.
- `hypotheses`: `{id, observation, cause, change, prediction, outcome, evidence, applicability, counterexamples, reason}`, outcome untested, supported, rejected or inconclusive; supported needs current digest evidence, rejected repairs keep their reason, and prose stays judgment, not proven causality.

Schema `1.1` adds `property:"bounds.<axis>"` (x, y, width, height, right, bottom, centerX, centerY) with `tolerance:{cssPixels:<finite nonnegative>,reason:<justification>}` and a numeric `equals` or one `sameAs:{selector,pseudo:""}` owner matching exactly one element; every match must satisfy the axis. For example, compare `.toolbar button` `bounds.centerY` with `.toolbar input`, excluding the caption. Probe native elements with an empty pseudo. Missing or ambiguous geometry cannot be waived, tolerance belongs to the target rather than an aesthetic threshold, box centers certify neither baseline nor optical mass, and older contracts opt in explicitly.

Direction selection, checked implementation, recorded verdict and user acceptance stay separate: `selected` is neither verified nor approved, a supplied design can be `user-specified` with fidelity unverified, and silence is `UNCONFIRMED`.

## Check a Recorded Visual Verdict

For a material visual decision whose review is reused or handed off:

```text
python <skill-directory>/scripts/visual_review.py design/REVIEW.json --workspace .
```

The command is read-only. `--workspace` is resolved once, and evidence paths must not pass through a symlink, junction or reparse point. It never inspects pixels, infers attention from CSS, scores taste or turns self-review into approval; Direct corrections keep their short record.

The attention contract is authored before evaluation:

```json
{"schema":"1.0","scope":"Run monitoring","states":[{"id":"running","question":"Is this run progressing?","priority":["Run progress","Affected records"],"cues":["Progress value grouped with coverage"],"competing":["Create new"]}]}
```

Contract schema `2.0` adds `plan` and `system` path and digest bindings. A schema `3.0` report keeps `scope, method, reviewer, contract, sources, renders, visualAssessment, userAcceptance` and adds `capture`, the receipt binding; `sources` equal the receipt inventory, and each render adds `id, state, viewport, theme, input, motion, context` from the plan.

- `method` is `self-review`, `peer-review` or `user-review` with a named `reviewer`; `userAcceptance` (`UNCONFIRMED`, `ACCEPTED`, `REJECTED`) is separate, and a method supplies no verdict.
- `contract` is `{path, sha256}`; `sources` and `renders` are nonempty, renders `{path, sha256, state, viewport}` with forward-slash workspace-relative paths and explicit viewports such as `390x844@1`, covering every owner, inspected render and required state.
- `visualAssessment` has an explicit `verdict`, a concrete `finding`, and `assessments` (`{state, renders, observedAttention, finding, verdict}`, each render assessed once) and `findings`. Observed attention is the reviewer's judgment, not eye tracking.
- Each finding is `{id, states, owner, observation, consequence, blocking, status, renders}`, `status` `open`, `resolved` or `accepted` with a `resolution` reason; a blocking defect cannot be accepted away, and a negative verdict needs an open causal finding.

The checker verifies every planned combination and relationship, so dropping renders, relabelling a viewport, omitting CSS or losing a dependency loses PASS. Empty findings mean nothing was observed; never invent defects. Optional `date`, `notes`, `evidence` and `inspectedCaptures` add metadata only. Schema-1/2 reports and inline receipts stay readable as history but never PASS new obligations: re-review and keep the prior version, since history is never rewritten. A narrowed plan is a changed obligation to justify.

Exit dispositions: `0/PASS` for a current, consistent recorded KEEP; `2/BLOCKED` for blocking findings, REVISE or REJECT, or user rejection; `3/REVIEW_REQUIRED` for missing judgment, incomplete coverage or stale evidence; `1` for invalid structure, paths or I/O. Output separates `integrity`, `visual_verdict`, `method` and `user_acceptance`. PASS confirms recorded conditions, not aesthetic truth, independent review or acceptance, and the JSON trail is not tamper-proof. The correction journal closes a visual criterion with such a report or a host capture ([close a visual criterion](correction-memory.md#close-a-visual-criterion); [commands](correction-memory.md#checked-journal-commands)).

## Check an Exact Opaque Color Pair

```text
python <skill-directory>/scripts/contrast.py "#18201B" "#F4F0E6"
python <skill-directory>/scripts/contrast.py "#18201B" "#F4F0E6" --large
python <skill-directory>/scripts/contrast.py "#5A6B61" "#F4F0E6" --non-text --json
```

It accepts `#RGB`, `#RRGGBB`, `rgb(r,g,b)`, `black` and `white` and uses WCAG relative luminance. The default minimum is 4.5:1 (1.4.3); `--large` needs 3:1 (at least 24px, or 18.66px bold); `--non-text` needs 3:1 for component boundaries, states and graphics (1.4.11); `--minimum <ratio>` sets any finite 1–21 and cannot combine with a preset. Choosing the criterion stays your judgment, and the output names the one used. Exit `0` PASS, `1` FAIL, `2` invalid input (unsupported color, alpha, out-of-range channel, invalid minimum). Alpha, gradients, images and effects need rendered measurement.

## Interpret Output Honestly

- `source_role` says what a dataset can contribute; `warning` says what it cannot decide.
- Empty or weak lexical results mean little local evidence, not an empty design space.
- Retrieved numeric claims stay unverified until traced to a credible current source; unsupported chart thresholds, threshold-bearing use/avoid prose, grades, palettes, library advice and interaction prescriptions are absent from the bundled catalog.
- A contrast result covers only its exact solid pair.
- A font stays `UNKNOWN` until its files, script coverage, license, metrics, representative content, fallbacks and rendering are checked.
- An SVG `PASS` is structural only, and an icon sheet proves that contexts rendered, not that a glyph is best.
- An `iso.py` render proves projection, order and structure, not that the illustration earns its place or reads well.
- The CLI cannot select or certify architecture, art direction, imagery, custom asset quality, motion, usability or taste.
