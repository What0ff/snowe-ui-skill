# CLI Reference

Use the CLI for deterministic local evidence retrieval, an open design-inquiry packet, project decision persistence, stack guidance, and structural SVG validation. It does not design or evaluate the rendered result for the agent.

## Runtime

```text
python <skill-directory>/scripts/search.py --help
python <skill-directory>/scripts/asset_quality.py --help
python <skill-directory>/scripts/contrast.py --help
```

Use an available Python 3 interpreter. Do not install or modify system Python merely to run Snowe without user authorization.

## Open a Decision Packet

```text
python <skill-directory>/scripts/search.py \
  "Bicycle retailer for urban riders; fit confidence before purchase; responsive web" \
  --decision-packet --format markdown --project-name "Project Name"
```

`--decision-packet` (short form `-dp`) returns unresolved product, architecture, art-direction, imagery, custom-graphic, motion, responsive, research, and evaluation questions. It detects brief pressures with word-boundary signals and retrieves labeled local analogs, but intentionally does not select a category, page pattern, layout, section order, style, palette, font, image, or animation.

Use `--format json` for structured evaluation or tooling. `--json` belongs to domain/stack search and cannot be combined with a decision packet.

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
<project-directory>/design-intelligence/care-flow/BRIEF.md
<project-directory>/design-intelligence/care-flow/DECISIONS.md
```

- `BRIEF.md` is regenerated from the current inquiry.
- `DECISIONS.md` is created only when absent and then preserved byte-for-byte. Record accepted causal decisions, scope, evidence, risk, and revisit trigger there; do not turn hypotheses into facts.

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

The file asks for the page job, content/objects, entry/exit, candidate architectures, responsive transformations, states, and proof. It does not classify the page or prescribe sections. `--page` and `--output-dir` require `--persist`; persistence requires a decision packet. Resolved paths must remain inside the selected output directory.

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
| `landing` | Historical page examples and counterexamples; never section recipes |
| `style` | Visual vocabulary and implementation cues; never an art-direction winner |
| `color` | Palette examples to inspect and verify; never brand or contrast proof |
| `typography` | Pairing hypotheses and loading clues; never file/script/metric proof |
| `google-fonts` | Bundled font metadata snapshot; verify current official files and license |
| `ux` | Issue prompts and heuristics to verify in the actual flow |
| `web` | App-interface/accessibility prompts; verify platform applicability |
| `chart` | Visualization candidates, limitations, and accessibility prompts |
| `react` | React/Next performance prompts; verify current repository/version |
| `gsap` | Historical implementation examples; never evidence that motion is needed |
| `icon-concepts` | Role-first metaphor prompts and ambiguity warnings |
| `icon-families` | Source discovery snapshot; verify current official source/license |
| `icon-candidates` | Exact known glyph/import hints for one named family |
| `icons` | Legacy concrete icon-name lookup |

Use concrete queries with the unresolved decision and context, not `modern app`. Query several domains only when each can change a decision. External current research remains necessary for unstable, high-leverage, or unsupported questions.

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
  "role": "interface icon",
  "grid": "24 x 24",
  "live_area": "2..22 with optical overshoot for curves",
  "drawing_language": {
    "mode": "stroke",
    "stroke_width": 1.75,
    "linecap": "round",
    "linejoin": "round",
    "corner_language": "small mechanical radii",
    "detail_budget": "recognizable at 16 px"
  },
  "target_sizes": [16, 20, 24],
  "source": "repository-owned custom drawing",
  "license": "project-owned",
  "accessibility_owner": "owning labeled button; SVG decorative"
}
```

Ordinary interface icons must declare 16, 20, and 24 px targets unless their real documented component uses another role. The validator checks metadata, XML/viewBox, unsafe/embedded content, external references, interface color behavior, and structural warnings. It does not prove recognition, optical balance, provenance truth, license validity, or coherence. Complete the rendered neighbor comparison in [iconography-system.md](iconography-system.md).

## Check an Exact Opaque Color Pair

```text
python <skill-directory>/scripts/contrast.py "#18201B" "#F4F0E6" --minimum 4.5
```

The helper accepts `#RGB`, `#RRGGBB`, `rgb(r,g,b)`, `black`, and `white`. It uses WCAG relative-luminance contrast math and returns a nonzero exit code when the exact pair fails the requested minimum. It deliberately rejects alpha, gradients, images, and effects because those require rendered contextual measurement.

## Interpret Output Honestly

- `source_role` explains what a dataset can contribute; `warning` states what it cannot decide.
- Empty or low-quality lexical results mean the local snapshot has little evidence, not that the design space is empty.
- Retrieved numeric claims are unverified until traced to a credible current source.
- A contrast calculation applies only to its exact solid rendered pair; imagery, gradients, transparency, effects, and states require contextual measurement.
- A font remains `UNKNOWN` until actual files/dependency, script coverage, license, metrics, representative content, fallbacks, and rendering are checked.
- An SVG `PASS` is structural only.
- The CLI cannot select or certify architecture, art direction, imagery, custom asset quality, motion, usability, or taste. Those require causal comparison and implemented rendered evidence.
