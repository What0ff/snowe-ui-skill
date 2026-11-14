# CLI Reference

The bundled scripts give deterministic local evidence: retrieval, a Portfolio decision packet, identity-bound persistence, stack guidance, SVG validation, icon comparison, browser observation, visual-system contracts, checked visual reports and exact contrast. None of them designs or aesthetically judges the rendered result.

## Runtime

```text
python <skill-directory>/scripts/search.py --help
python <skill-directory>/scripts/asset_quality.py --help
python <skill-directory>/scripts/icon_review.py --help
python <skill-directory>/scripts/contrast.py --help
```

Use Python 3.11+; isolated mode (`python -I`) works. Do not install or modify system Python to run Snowe without user authorization.

`search.py` exits `0` on success, `1` when a lookup reports an error (the message goes to stderr; with `--json` the error object stays on stdout) or another run holds a persistence lock, and `2` for invalid arguments or an unusable `--output-dir`.

## Open a Decision Packet

Open a packet only for Portfolio work or when the caller asks; Direct and Focused work keep their compact records.

```text
python <skill-directory>/scripts/search.py \
  "Bicycle retailer for urban riders; fit confidence before purchase; responsive web" \
  --decision-packet --format markdown --project-name "Project Name"
```

`--decision-packet` (`-dp`) preserves the brief verbatim and returns unresolved product, architecture, art-direction, imagery, custom-graphic, motion, responsive, research and evaluation questions. It never detects the language, classifies vocabulary, infers a domain, platform or work mode, or invents pressures; unknown framing stays unresolved.

Local analogs are off by default. Add a caller-chosen lexical query only when a product analogy can change an open decision:

```text
python <skill-directory>/scripts/search.py \
  "Городской магазин велосипедов; уверенность в посадке до покупки" \
  --decision-packet --analog-query "cycling retail shop"
```

`--analog-query` ranks at most three subordinate product-catalog matches. It is not semantic confidence, does not expand the brief, and changes no situation or architecture field when results are absent.

Declare a work mode, platforms, facts or pressures the caller already knows in a file; the runtime never derives them from the brief:

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

The file is a UTF-8 JSON object: `work_mode` is nonempty text; `platforms`, `facts` and `pressures` are arrays of nonempty strings; other keys pass through to `situation.other_declared_context`. Declarations mark framing `PARTIALLY_DECLARED` and appear in the packet and a persisted `BRIEF.md`. They are caller claims, so verify their provenance.

`--format json` gives structured output; with `--persist`, stdout stays one packet JSON document and the persistence confirmation goes to stderr. `--json` belongs to domain and stack search and cannot combine with a packet. `--design-system` / `-ds` is a compatibility alias for the same open packet, not the old recipe generator; new tooling uses `--decision-packet`. The packet is a starting workbench, never the delivered design.

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

- `PROJECT.json` binds the exact project identity to its slug. A different identity that normalizes to the same slug is refused, as is a shared-hardlink/inode manifest.
- `BRIEF.md` is atomically regenerated from the current inquiry. `--page` preserves an existing project brief and creates one only when absent; the page brief goes into the page inquiry. The brief is stored verbatim, so keep credentials, personal data and internal hosts out of it: persistence warns on stderr (and returns `sensitive_content`) for likely secrets, emails or private hosts and never redacts silently.
- `DECISIONS.md`, the decision ledger, is created only when absent and then preserved byte for byte; a shared-hardlink/inode ledger is refused, so preserving it cannot mutate another file. Record accepted causal decisions, scope, evidence, risk and revisit trigger there, never hypotheses as facts.

The confirmation prints the resolved project directory and marks each file `written` or `preserved` as persistence actually did, on stdout or on stderr with `--format json`. An `--output-dir` that is, or runs through, an existing file is refused with that file named. If another run holds the project lock (Windows gives up after about ten seconds; POSIX waits), the command exits `1` with `Another persistence operation is active`; retry after it finishes.

Add an unresolved page inquiry:

```text
python <skill-directory>/scripts/search.py \
  "Product selection and fit evidence" --decision-packet --persist \
  --project-name "City Cycles" --page "find-a-bike" \
  --output-dir <project-directory>
```

This adds `<project-directory>/design-intelligence/city-cycles/pages/find-a-bike.md`, which asks for the page job, content and objects, entry and exit, candidate architectures, responsive transformations, states and proof without classifying the page or prescribing sections.

`--page` and `--output-dir` require `--persist`; persistence requires a decision packet and an explicit `--project-name`. One per-project lock serializes manifest, brief, ledger and page publication, each a complete atomic write. Page identity and parent-directory checks run before `BRIEF.md` is published and again just before the page is; accepted ledger bytes are never regenerated. `--output-dir` (default: the current directory) is resolved once to its real path, so a directory under a redirected ancestor such as macOS `/tmp` or `/var/folders` works and Windows short names expand to the long spelling; the resolved path is rechecked before locking or writing. Project and page slug collisions, Windows-reserved identities, malformed identity manifests without a safe recovery basis, and any symlink, junction or reparse point at or below the resolved directory are refused rather than followed or overwritten.

A persisted brief or page inquiry ranks just above labelled local analogs and generated hypotheses in the [source precedence](../SKILL.md#evidence-and-authority).

## Search Local Evidence

```text
python <skill-directory>/scripts/search.py "query" --domain <domain> --max-results 5
python <skill-directory>/scripts/search.py "query" --domain <domain> --json
```

Every result reports a **source role** and **use boundary**. Rows from catalogs that number them start with `No`, a stable row id within the named file (removed rows leave gaps), so a finding can cite, for example, `charts.csv` row 3. `data/CATALOGS.md` records each catalog's source, dates, row count and license notice. A top row is not semantic classification, current external truth or a design selection.

Ranking is English-oriented lexical BM25 over a bundled snapshot:

- Query and rows share one normalization: case folding, a small English stopword list (`for`, `the`, `vs`, ...), light suffix stemming (`rerenders`, `rerendering` → `rerender`; `lists` → `list`), and hyphen compounds indexed split and joined (`re-render` also matches `rerender`). Non-English words pass through unstemmed. This is normalization, not a synonym table or query expansion.
- The row's name column (`Issue`, `Product Type`, `Family`, `Guideline`, ...) counts three times, `Keywords` and `Category` twice, other searched columns once. UX, React and mobile lookups also search the `Do` column.
- A row whose name equals the query ranks first, then rows whose name starts with it (`IBM Plex Sans` before `IBM Plex Sans Condensed`), then rows whose name and query overlap as a phrase.
- Scores are multiplied by the share of distinct query terms a row matches. When some row matches several terms, rows matching fewer than half as many are dropped as incidental, so fewer than `--max-results` rows can return.
- `unmatched_terms` (JSON) lists query words found in no searched column; when it is not empty, the use boundary names them too. They did not affect ranking: `geometric` cannot match the font index, which has no construction or mood vocabulary.

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

There is no layout, landing, style, palette, typography-pairing or motion-preset domain: those catalogs were removed because their bundled combinations acted like solutions even when labelled as historical evidence.

Query with the unresolved decision and its context, not `modern app`, and search a domain only when it can change a decision. Unstable, high-leverage or unsupported questions still need current external research; the English-oriented lexical limit affects only an explicit lookup, never packet framing. For `icon-candidates`, name exactly one supported family per query, repeat exact-glyph lookup across sources, and render finalists in the same component; package counts and catalog thumbnails are not visual evidence.

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

The `uwp` catalog was retired on 2026-11-12 because it targeted retired device families such as Windows 10 Mobile; `--stack uwp` returns an error naming `winui`, whose catalog covers choosing WinUI 3 and migrating UWP code.

Use the repository's actual stack. Stack rows are bundled guidance, not proof of current API behavior; check official documentation when versions, platform behavior or dependencies may have changed. Rows start with their `No` id where the file has one. Every stack response carries the domain evidence boundary plus `documentation_coverage` counts for returned rows with and without a `Docs URL`. A URL is a discovery pointer, not proof that a source is primary or current, and when a returned row lacks one, text and JSON output say it stays unsourced until independently verified.

## Validate Custom SVG Structure

Start from the SVG: write the metadata skeleton, replace its placeholders, then bind evidence digests and validate.

```text
python <skill-directory>/scripts/asset_quality.py path/to/icon.svg --init-metadata
python <skill-directory>/scripts/asset_quality.py \
  path/to/icon.svg --metadata path/to/icon.metadata.json --rehash
python <skill-directory>/scripts/asset_quality.py \
  path/to/icon.svg --metadata path/to/icon.metadata.json
```

- `--init-metadata` writes `<svg-stem>.metadata.json` beside the SVG (or at `--metadata`) and never overwrites a file. It computes the name, grid, a full-grid live area, the observed drawing language (mode, stroke width, caps, joins, duotone tone) and the exact SVG digest; everything needing judgment stays a `<...>` placeholder that fails validation until a person replaces it. The default skeleton is original artwork under a project-owned license; `--provenance external` starts an imported-asset skeleton (unverified external source plus a retained license file).
- `--rehash` is for an intentional edit. It recomputes the original-provenance digest and the digests of local evidence files already named in the metadata, prints every changed, unchanged and skipped field, then validates; a changed digest rewrites the file atomically as two-space-indented JSON. It never rebinds external or brand-mark artwork digests (restore the upstream bytes, or re-import and review them), and writes nothing when a named evidence path is unsafe or unreadable.

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

Declare unique positive targets for the real implemented slots: the validator checks geometry at the smallest declared size, and the comparison manifest requires every context size to be covered, so an 18 px owner declares 18, not an invented 16/20/24. Specific source, license and accessibility declarations, exact grid and live area, a consistent drawing language, the SVG provenance digest and structured safe local evidence bindings are required. External source truth stays explicitly unverified, and evidence paths are never inferred from prose.

`grid` matches the viewBox width and height. `live_area` is measured from the viewBox origin, so a Material Symbols `viewBox="0 -960 960 960"` declares its full grid as `{"min_x": 0, "min_y": 0, "max_x": 960, "max_y": 960}`. Original artwork may declare `evidence.license` as exactly `{"kind": "project-owned"}` instead of a `{path, sha256}` binding; external sources still bind a retained license file.

Choose the drawing mode per role: `stroke` draws outlines only, `fill` solid shapes only, `mixed` is one tone that needs both, and `duotone` layers a full-strength primary over a lighter secondary. A solid icon declares no stroke language:

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

Every painted duotone element resolves to `primary` or `secondary`, and a primary layer is required. The secondary layer renders at exactly `tones.secondary_opacity`, a finite number from 0.12 to 0.6: its `opacity`, `fill-opacity` and `stroke-opacity` multiply to that tone, while the root and primary layer stay at opacity 1. Undeclared tones, unknown layer values, a layer changing inside another layer, a secondary without a primary, `tones` outside duotone, and layers in any other mode fail. A stroked duotone layer declares its positive `stroke_width` and concrete linecap and linejoin; otherwise declare 0 and `not applicable`.

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

Root `width`/`height` are optional unitless or px lengths that keep the viewBox aspect ratio. An unpainted `<rect>` or `<path>` exactly covering the viewBox (the spacer Phosphor and Tabler export) is ignored. Arc flags may be compact, as SVGO writes them (`a8 8 0 0116 0`), and path data must begin with a moveto.

The subset rejects event handlers; document, entity and stylesheet declarations; nested viewports; executable, linked, animated, text, embedded, styled, external, unknown or namespaced content; `id` and all URI and local-fragment references; transforms, masks, filters and clipping; other attributes and values; malformed or clipped geometry; collapsed root dimensions or a contradictory aspect ratio; non-`currentColor` paint; muted opacity outside the duotone secondary layer; and drawing-language contradictions. Round and bevel joins are supported; miter geometry (and `arcs`, which browsers render as miter) is rejected because the bounds proof cannot certify its spike extent. Square caps are bounded by their diagonal corner reach.

Two checks warn instead of failing. Under `fill-rule` `nonzero`, an inner subpath with the same winding as its outer one renders solid, so a drawn hole disappears; reverse it or declare `evenodd`. In `fill` and `duotone` modes, a filled subpath whose shorter side renders below 1 CSS px at the smallest target can close up or vanish. A structural `PASS` cannot prove source or license truth, recognition, silhouette, optical balance, metaphor or family and UI fit.

For unchanged imported brand SVGs, declare `asset_type:"brand-mark"` and add `brand:{schema:"1.0",identity:<exact identity>,variant:<supplied variant>,artwork:{path,sha256},usage:{path,sha256}}`. Other metadata fields stay required, with drawing-language fields describing the supplied artwork rather than prescribing a redesign. Provenance must be `external` with a canonical HTTPS source URL, and `evidence.source` stays `{kind:"external",verification:"unverified"}`. `artwork` binds a retained upstream copy whose digest must also match the delivered SVG; `usage` binds a local reviewed usage record; both use the license evidence's metadata-relative regular-file, path and digest checks, within a 1,000,000-byte budget each. The profile also permits opaque `#RGB`, `#RRGGBB`, black and white paint; all other self-contained checks stay in force. It supports no gradients, masks or styles and certifies neither officialness, licensing nor context: use another official variant or the host's asset proof for unsupported originals, and never trace, recolor or flatten an external identity to pass. Missing or stale records fail; hashes do not stop someone rewriting both self-authored records, so primary-source review is still required, and a URL never authorizes remote references inside the SVG.

Both profiles bound quadratic and cubic curves by their actual extrema, including reflected smooth controls, rather than the control-point hull, so a rounded solid whose control points leave the grid is not reported as clipped. Curve arithmetic keeps the 1,000,000-coordinate safety envelope. The imported profile tolerates only 1e-7 of the smaller viewBox dimension for decimal rounding (below 0.000003 CSS px at a 24 px slot); `interface-icon` keeps an absolute 1e-7, so a curve that really overshoots still fails. Host clipping and appearance still need rendered inspection.

## Compare Existing, Custom, and No-Icon Candidates

Once exact candidates and a real role are known, write a compact manifest and generate a self-contained representative-control sheet:

```text
python <skill-directory>/scripts/icon_review.py \
  path/to/manifest.json --output path/to/comparison.html --json
```

The manifest binds every SVG candidate to its validated metadata name, provenance kind, explicit asset SHA-256, metadata provenance digest and every context target size. It rejects duplicate SVG bytes posing as different candidates, custom candidates without original provenance, unsafe local host routes, malformed, deep or extreme-number JSON and Unicode scalar inputs, uninspectable paths, invalid selection and verdict combinations, and repository-derived contexts whose source file is absent. Repository-derived host proof must select a candidate (use `representative` evidence for unresolved `REJECT`/`UNKNOWN` contexts), and its explicit `host_proof.state_map` covers every declared comparison state exactly once with the same-name host state, except `high-contrast`, which maps to the exercised `forced-colors` state. A button-clone no-icon candidate uses the exact visible label of its owning control. The sheet renders the same labels and declared states for every alternative, and a no-icon alternative shows the visible UI truth once rather than a blank icon cell.

To decide a drawing style for one role, a schema-`1.2` interface context can set `"comparison_axis": "style"` instead of the default `"kind"`. Candidates may then share a kind (two custom drawings, or two variants of one library glyph), but at least two SVG candidates are required, each differing from every other in declared drawing style (mode, stroke width, caps, joins, duotone tone) in at least one state. A candidate may add `state_assets`, keyed by declared non-default states, to show different artwork per state, for example outline by default and solid when selected:

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

Each state asset is validated, digest-bound and size-checked like the default asset, must differ from it, and is listed on the card with its own name, digest, source and license. A candidate with state assets names a combination, so its `id` need not equal one asset name, but it cannot borrow another asset's name; duplicates are detected on the exact bytes shown in every state. Brand contexts accept neither field.

Repository-derived host proof may also exercise a `selected` host state. It must declare `selected_attribute` (`aria-pressed`, `aria-current` or `aria-selected`) and may declare `select_selector`, a control to click first. Browser smoke requires that attribute to report selection on the host target, never a style alone, keeps the accessible-label check of every other state, and renders each candidate's state artwork in the host.

New manifests use schema `1.2`, with explicit `lang` (language tag), `dir` (`ltr`, `rtl`, `auto`) and `symbol_role` (`interface-icon` or `brand-mark`) on every context. Brand contexts also declare `brand_identity`, bind matching `brand-mark` metadata for every artwork candidate and reject `custom` substitutes; they may hold one known supplied `existing` candidate or a visible-text `none` fallback without manufactured alternatives. Ordinary interface contexts keep the comparison requirements and cannot silently consume brand artwork. Versions `1.0` and `1.1` stay readable; typed role fields need schema 1.2, and `1.0` keeps `en`/`ltr` defaults. The attributes apply to preview content, while English inspector metadata keeps its own language. Long headers and text alternatives wrap and grow rather than clip. Language and semantic role are never inferred from label vocabulary.

The sheet is representative comparison evidence, not a pixel-identical host render or an automatic decision. Inspect it at wide and narrow viewports, then render the claimed winner and the closest rejected alternative inside the owning component beside real neighbors, recording the optical and semantic choice as human judgment. Source fidelity and usage suitability still need primary-source and host review. A worked example is the [icon-decisions proof](https://github.com/What0ff/snowe-ui-skill/tree/main/evals/icon-decisions) in the source repository; it is not part of an installed skill.

## Observe in a Browser

Prefer the host's browser tools when they support the target application. The skill also ships an optional, dependency-free adapter for **Node 22+ with a system Chrome, Chromium or Edge**:

```text
node <skill-directory>/scripts/observe.mjs capabilities
node <skill-directory>/scripts/observe.mjs capture <workspace> <plan.json> <fresh-output-directory>
node <skill-directory>/scripts/observe.mjs compare <workspace> <before-receipt.json> <after-receipt.json> <comparison.html>
```

`capabilities` reports the browser found, `available`, and `reasons` when capture cannot run (Node older than 22, or no browser). Discovery tries `CHROME_PATH`, then Chrome, Edge and Chromium in standard locations: `%ProgramFiles%`, `%ProgramFiles(x86)%` and `%LOCALAPPDATA%` on Windows; `/Applications` and `~/Applications` on macOS; `/usr/bin` (including `microsoft-edge-stable`) and `PATH` on Linux. Nothing is downloaded, and Python stays standard-library-only. Missing Node or a browser blocks only formal browser proof: use the host's tools, report their actual capabilities, and mark the unavailable proof `UNKNOWN`. The adapter serves local static files only and refuses external or unbound assets; app-server builds, authentication, native apps, closed shadow roots and temporal canvas or video proof need the host adapter and explicit environment records. Never substitute a static fixture for a working backend claim.

The Chromium sandbox stays on unless it cannot start (running as root on Linux, or inside a Linux container), or you pass `--no-sandbox` to `capabilities`/`capture` or set `SNOWE_OBSERVE_NO_SANDBOX=1`; `capabilities` reports the decision and why. If the browser exits before DevTools starts, the error says so and, on Linux, suggests the opt-out. Usage mistakes print usage and exit `2`; capture failures print one `observe.mjs: error:` line and exit `1` (`SNOWE_OBSERVE_DEBUG=1` adds a stack). Headless capture hides native scrollbar paint so full-page and detail geometry stay comparable, bound through the observer revision; check scroll behavior and native scrollbar affordances with the host, and never infer a scrollbar bug from these captures.

Observation plan schema `1.0` has `scope`, `sourceRoots` and `cases`. Each case looks like:

```json
{"id":"mobile-selected","state":"selected","viewport":"390x844@1","theme":"light","input":"touch","motion":"reduced","context":"page","route":"/index.html","steps":[{"action":"click","selector":"#choose"}],"expect":[{"selector":"#choose","property":"attribute:aria-pressed","equals":"true"}],"probes":[{"selector":"main","pseudo":""},{"selector":".selection","pseudo":""},{"selector":".selection","pseudo":"::before"}],"details":[{"id":"selected-owner","selector":".selection","padding":12,"scale":2}]}
```

- **Viewport** is `<CSS width>x<CSS height>@<device pixel ratio>`, the ratio from 1 to 4 with up to two decimals, compared numerically with the browser's `devicePixelRatio` (`@1` and `@1.0` are the same capture).
- **Matrix.** Choose explicit combinations from affected states, breakpoints, themes, inputs and composition contexts instead of multiplying irrelevant dimensions, and record why representative siblings suffice and which dependencies would require widening. Reduced motion can remove nodes: plan the static layer.
- **Steps.** Actions are `click`, `fill` (`selector`, `value`), `key` (`Tab`, `Enter`, `Escape`, `ArrowDown`, `ArrowUp` or `Space`; `space` is accepted, a literal space character is not, and other names are rejected), `wait-for-selector` and `scroll-to-selector`. Keyboard cases activate with keys, touch cases dispatch touch. Reproduce loading and error states through stable local routes or explicit setup, never screenshots labelled after capture.
- **Source roots** are the complete bounded owner, import, asset and build scopes, not a hand-picked list that omits changed CSS; include separately owned shared dependencies, and directory roots detect additions and removals. The server serves only inventoried bytes and records requests; output directories must be disjoint; secrets and unrelated large repositories stay out of scope. Capture fails when a resource falls outside the inventory, source or plan bytes change during observation, fonts, motion or layout do not settle, or a required probe is absent.
- **Details** are required for the affected owners: unique `id`, measured `selector`, `padding` (0–100 CSS px) and `scale` (1 native, 2 diagnostic). The receipt binds crop bounds and lossless PNG dimensions and hashes; missing or unassessed details block closure. Fixed, top-layer and portalled owners use `space:"viewport"`, cropped from the exact bound native viewport PNG with its parent digest and pixel rectangle, not a later screenshot. A 2× crop enlarges captured pixels and proves nothing about higher-density rendering; use a real DPR case for that. Receipts keep scroll coordinates and separate viewport and whole-page captures; pseudo-element measurements report computed paint plus labelled owner-element bounds.
- **Postconditions** (`expect`) are planned independently: `selector`, `property` and `equals` or text `includes`, with property `attribute:<name>`, `css:<property>`, `text`, `focused`, `disabled`, `checked`, `open` or `value`. A state name or dispatched click does not prove a selected value, open overlay or confirmation. The adapter scrolls click targets into view and rejects covered or out-of-viewport targets; a met postcondition is technical state evidence, not visual quality.
- **Sequences.** Optional `sequence:{fps,durationMs,start,events}` records bounded temporal proof (1–30 fps, up to 10 s): `start` is replay steps and `events` carry increasing `atMs` and `steps`. A trusted caller-authored `script` step with `value` can set up or replay application state; inspect its code first and never run instructions scraped from page content. Each frame binds time, environment and PNG bytes; the checker validates coverage, not choreography, and endless canvas or video work still needs a deliberate capture protocol and human inspection.

Each immutable receipt binds the plan, observer revision, browser product, user agent and protocol, actual CSS viewport and DPR, emulated theme, touch and motion, route, font settlement, requested and rendered font faces, source inventory, loaded resources, measured layers, and whole and detail captures. Compare at the intended display scale; a full-page image does not replace viewport attention or interaction proof. Receipt reads have an 8 MB budget, while contract and journal JSON keep 1 MB; split an oversized scope into justified plans. `compare` pairs identical combinations and warns when measured content changed; it has no score or winner.

## Version a Visual-System Contract

Write a new revision file instead of overwriting the accepted one. The decision ledger stays byte-preserved; a new contract may supersede a decision only in appended history, with its reason and revisit trigger. `visual_system.py` keeps schema `1.0` and supports opt-in schema `1.1`:

- `revision` (positive integer), `previous` (path and SHA-256 when revision > 1), `scope`, `depth` (Direct, Focused or Portfolio).
- `direction`: `status` (proposed, selected or user-specified), `thesis`, `axes` and `revisit` conditions. Axes are composition, typography, color, surfaces, shape, imagery, motion and responsive; Portfolio addresses all, bounded work only the affected ones, and a justified no-image or no-motion decision is a real axis decision.
- `tokens`: `{id, owner, property, value}` with source-bound owners; values record intent, not guessed computed equivalents.
- `components`: `{id, role, owner, selector, tokens, states, consumers, layers}`. Consumers name `{case, selector}`; layers name `{kind, selector, pseudo, sources, cases}` with kinds element, pseudo, backdrop, portal, font, image, svg, canvas and video. Every declared consumer and layer needs a planned measurement, and dependencies and owners must be inventoried.
- `relations`: `{id, members, intent, checks}`. Each check has `id, case, selector, pseudo, property` and either `equals` or `sameAs:{selector,pseudo}`, applied to all matching siblings. Use measured properties, bounds or text only for a justified explicit contract, never as a beauty formula.
- `exceptions`: `{check, reason, revisit}` naming a real check. An exception preserves a justified scoped distinction, including a user-specified design; it never waives missing browser evidence or a negative visual finding.
- `hypotheses`: `{id, observation, cause, change, prediction, outcome, evidence, applicability, counterexamples, reason}` with outcome untested, supported, rejected or inconclusive. A supported result needs current path and digest evidence; keep why a repair was rejected and where the lesson does not transfer. Prose stays reasoned judgment, not proven causality.

Schema `1.1` adds `property:"bounds.<axis>"` for x, y, width, height, right, bottom, centerX and centerY. Each geometry check needs `tolerance:{cssPixels:<finite nonnegative number>,reason:<context-specific justification>}` and either a numeric `equals` or one `sameAs:{selector,pseudo:""}` reference owner that matches exactly one element; every actual match must satisfy the axis. For example, compare `.toolbar button` `bounds.centerY` with `.toolbar input`, excluding the field caption. Use native element probes with an empty pseudo, since pseudo paint has only owner-element bounds. Missing, ambiguous or invalid geometry cannot be waived. The tolerance is declared for the target, not a universal aesthetic threshold, and box centers certify neither text baseline nor optical mass. Older contracts keep exact-property semantics and opt in to geometry explicitly.

Direction selection, checked implementation, recorded verdict and user acceptance stay separate: `selected` means neither verified nor approved, a supplied design can be `user-specified` while its fidelity is unverified, and silence is `UNCONFIRMED`.

## Check a Recorded Visual Verdict

For a material visual decision whose review is reused or handed off:

```text
python <skill-directory>/scripts/visual_review.py design/REVIEW.json --workspace .
```

This read-only command checks a caller-authored report. `--workspace` is resolved once to its real path, and evidence paths inside it must not run through a symlink, junction or reparse point. It never inspects pixels, infers attention from CSS, scores taste or turns self-review into approval. Ordinary Direct corrections keep their short record.

The attention contract is authored before evaluation:

```json
{"schema":"1.0","scope":"Run monitoring","states":[{"id":"running","question":"Is this run progressing?","priority":["Run progress","Affected records"],"cues":["Progress value grouped with coverage"],"competing":["Create new"]}]}
```

Schema `2.0` of the contract keeps `scope` and the independent `states`, and adds `plan` and `system` path and digest bindings. A schema `3.0` report keeps the schema-2 fields `scope, method, reviewer, contract, sources, renders, visualAssessment, userAcceptance` and adds `capture`, the browser receipt binding; `sources` exactly equal the receipt inventory, and each render combines its receipt binding with `id, state, viewport, theme, input, motion, context` from the planned observations. The fields:

- `scope` matches the contract; `method` is `self-review`, `peer-review` or `user-review`; `reviewer` is named; `userAcceptance` is separate (`UNCONFIRMED`, `ACCEPTED`, `REJECTED`). A method never supplies either verdict.
- `contract` is `{path, sha256}` for the independent expectation file; `sources` and `renders` are nonempty, renders as `{path, sha256, state, viewport}`, with forward-slash paths relative to `--workspace` and an explicit viewport such as `390x844@1`. Bind every implementation owner and inspected render, and cover all required contract states.
- `visualAssessment` has an explicit `verdict` (`KEEP`, `REVISE`, `REJECT`, `UNKNOWN`), a concrete overall `finding`, and `assessments` and `findings` arrays. Each state assessment is `{state, renders, observedAttention, finding, verdict}`, and every bound render is assessed once in its declared state. Observed attention is the reviewer's judgment, not eye tracking or a copied expectation.
- Each material finding is `{id, states, owner, observation, consequence, blocking, status, renders}`, with `status` `open`, `resolved` or `accepted`. Resolution or acceptance needs a `resolution` reason, a blocking defect cannot be accepted away, its renders cover its states, and a negative state verdict needs an open causal finding rather than a generic label.

The checker verifies every planned combination and mapped relationship: dropping mobile renders, relabelling a viewport, omitting CSS or losing a dependency cannot keep a PASS. Use empty findings only when nothing was observed; never invent defects to fill the format. Optional `date`, `notes`, `evidence` and `inspectedCaptures` add metadata without replacing bindings. Schema-1/2 reports and inline receipts stay readable as history but never PASS new obligations: re-review explicitly and keep the prior version, because the checker never rewrites history or upgrades it to KEEP. A narrowed plan is a changed obligation to justify, not a way to erase missing evidence.

Exit dispositions: `0/PASS` for a current, consistent recorded KEEP; `2/BLOCKED` for unresolved blocking findings, REVISE or REJECT, or user rejection; `3/REVIEW_REQUIRED` for missing or unknown judgment, incomplete coverage or stale evidence; `1` for invalid structure, paths or I/O. Output separates `integrity`, `visual_verdict`, `method` and `user_acceptance`. PASS confirms the recorded acceptance conditions, not aesthetic truth, independent review or user acceptance; local JSON and hashes are an audit trail, not tamper-proof attestation.

The correction journal closes a visual criterion with such a report or with a host-browser capture ([close a visual criterion](correction-memory.md#close-a-visual-criterion)); its commands, schemas and exit codes are in [correction-memory.md](correction-memory.md#checked-journal-commands).

## Check an Exact Opaque Color Pair

```text
python <skill-directory>/scripts/contrast.py "#18201B" "#F4F0E6"
python <skill-directory>/scripts/contrast.py "#18201B" "#F4F0E6" --large
python <skill-directory>/scripts/contrast.py "#5A6B61" "#F4F0E6" --non-text --json
```

The helper accepts `#RGB`, `#RRGGBB`, `rgb(r,g,b)`, `black` and `white`, and uses WCAG relative-luminance math. The default minimum is 4.5:1 (1.4.3 AA normal text); `--large` requires 3:1 for large text (at least 24px, or 18.66px bold); `--non-text` requires 3:1 for UI component boundaries, states and graphical objects (1.4.11). `--minimum <ratio>` sets any finite ratio from 1 to 21 and cannot combine with a preset. Choosing the criterion for the rendered element stays your judgment; output and JSON name the criterion used.

Exit status is `0` PASS, `1` FAIL and `2` invalid input: an unsupported color, alpha, an out-of-range channel or an invalid minimum prints one stderr line. The helper rejects alpha, gradients, images and effects because those need rendered measurement.

## Interpret Output Honestly

- `source_role` explains what a dataset can contribute; `warning` states what it cannot decide.
- Empty or weak lexical results mean the local snapshot has little evidence, not that the design space is empty.
- Retrieved numeric claims are unverified until traced to a credible current source; unsupported chart thresholds, threshold-bearing use/avoid prose, grades, palette values, library advice and interaction prescriptions are not in the bundled catalog at all.
- A contrast calculation applies only to its exact solid pair; imagery, gradients, transparency, effects and states need contextual measurement.
- A font stays `UNKNOWN` until its files, script coverage, license, metrics, representative content, fallbacks and rendering are checked.
- An SVG `PASS` is structural only; an icon sheet proves that the declared contexts rendered, not that the selected glyph is optically or semantically best.
- The CLI cannot select or certify architecture, art direction, imagery, custom asset quality, motion, usability or taste; those need causal comparison and rendered evidence.
