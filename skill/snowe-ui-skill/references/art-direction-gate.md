# Art Direction

Use this reference to build a visual direction once the page job and real content are known ([page-hierarchy.md](page-hierarchy.md)): its sources, its recognizable move, its tokens. Depth, candidate scope, verdicts and when to ask the user live in SKILL.md and [exploration-protocol.md](exploration-protocol.md). Direct repairs inside an accepted system do not use this file.

Construct before subtracting: removing pills, spacing and color is cleanup, not a direction. Accepted quiet utility and exact supplied targets gain no novelty obligation; let the quiet direction win when it fits.

## Source the Direction From the Subject

Start from the subject, not adjectives. Inventory what the audience already sees and handles:

| Source | Look for | Usually becomes |
|---|---|---|
| Materials | paper, metal, glass, wood, textile | canvas tone, edges, rules, texture, radius |
| Artifacts | labels, receipts, forms, maps, packaging, instruments | grid, data blocks, type roles, the signature move |
| Era and vernacular | print, signage and lettering the audience reads | type construction, case, numerals, rule weight |
| Working conditions | distance, light, posture, hands, frequency, stress | type-size floor, contrast, density, motion |
| Content shape | name lengths, numbers, scripts, image aspect | columns, measure, image frame |
| Verified brand | accepted marks, colors and voice | fixed constraints |

Write 6–10 observations as nouns with physical properties ("collection label: typed, lower right, ruled boxes"). Use only what the brief, product or verifiable references support; a metaphor must not invent features or blur familiar actions. For reading at a distance, give capitals at least 16 arcmin, 20 preferred: cap height ≈ distance × 0.006, or 6 mm at 1 m.

Turn brief adjectives into questions: "modern" asks which current artifacts this audience trusts; "premium" asks what care looks like here; "clean" asks what must get quieter; "bold" asks which one thing earns the loud axis.

Write the perceptual job in one line, "It should feel ___ because ___; it must never imply ___", and tie attention to visible cues with the [page-hierarchy record](page-hierarchy.md#connect-importance-to-visible-cues). Turn each source into a move: observed property → perceptual mechanism → move → expected consequence → rendered proof.

## One Signature Move

Default: one signature move per direction. It is the direction's identity carrier, the one repeatable decision that makes the product recognizable or easier to understand; everything else supports it. It can be a composition rule, type behavior, content framing, graphic or data grammar, material or edge, or an interaction tied to real state. A logo, gradient, glow or motif is not a carrier by itself.

Write its boundary: where it appears (usually page frame, repeated item and detail view) and where it stops (fields, system dialogs and errors usually stay plain).

Subtraction test: remove logo, decoration, gradients, shadows and motion. Hierarchy, type, content and interaction should still look intentional; restore only what improves recognition, comprehension or feedback.

**Contrast budget.** Pick one or two loud axes, usually those the signature move uses, and keep the rest quiet:

| Axis | Loud | Quiet |
|---|---|---|
| Scale | a jump of 3+ scale steps; display 3–6× body | ratio 1.2–1.25, adjacent steps |
| Weight | 300 against 800–900 | regular and semibold |
| Color | a saturated dominant over a third of the view | tinted neutrals, accent under 10% |
| Space | wide margins, section gaps 2–3× the base rhythm, or deliberate crowding | one even rhythm |
| Texture | grain, halftone, visible grid, heavy rules | flat surfaces, 1 px rules |

If a third axis turns loud, demote one.

## Typographic Voice and Font Pairing

This is the single home for choosing and pairing families; [design foundations](design-foundations.md#typography) own the role map and rendered verification.

**Voice.** Describe the needed type structurally: construction (serif, sans, slab, mono), width, stroke contrast, x-height, terminals, numerals (lining or oldstyle, tabular) and case. Take these from the vernacular: a typed label suggests a mono role, an engraved plate high contrast and small caps, a stencil condensed capitals.

**Roles.** Assign display, text and mono before naming families; UI labels use the text role. Default: one text family. Add a display face only for a role the text family cannot carry at size, and a mono only for code, identifiers or fixed-width data that tabular figures cannot align. Ceiling: two families plus a mono; deviate for a required script or a verified brand face.

| Strategy | How | Fits | Watch for |
|---|---|---|---|
| One family | weights, widths, optical sizes of one family | utility, dense apps, most products | a flat voice; add width or scale contrast |
| Superfamily | sans, serif and mono on shared proportions | role contrast at low risk | a corporate tone |
| Structural contrast | differ in one trait (serif against sans, or high against low stroke contrast); share x-height, proportion and era | editorial, brand voice | two similar faces of one class look like a mistake |
| Display accent | one expressive face at one or two sizes | campaign, one signature | spreading into controls and body |

Pair on one clear difference; share the rest.

**Match x-heights at real sizes.** Most text faces have an x-height of 0.45–0.55 of the font size. Where families share a line (inline mono, mixed runs), keep x-heights within about 5%: set the mono at 0.9–0.95em or use `font-size-adjust`. Render heading, paragraph, label and a row of numbers at the sizes where they meet (for example 32, 16 and 13 px) at the target width; compare line breaks, punctuation, italics and numerals. A specimen, popularity rank or dataset pairing is discovery evidence only.

**Cover every script before shortlisting.** List the alphabets, diacritics in real names (ș, ț, ő, ł), currency signs, quotes (« », „ “) and units. Keep only families that cover them in every style you use; some ship Cyrillic in roman only. Set `lang` so localized forms such as Bulgarian Cyrillic apply. Drop a display face that lacks a required script rather than mixing fallback glyphs into a heading.

**Write a fallback stack per role**, nearest metrics first, and limit shift with `size-adjust` ([starting points](design-foundations.md#starting-points)):

```css
--font-text: "Chosen Sans", system-ui, "Segoe UI", Roboto, "Noto Sans", sans-serif;
--font-display: "Chosen Serif", Georgia, "Noto Serif", "Times New Roman", serif;
--font-mono: "Chosen Mono", ui-monospace, "SF Mono", Menlo, Consolas, monospace;
```

**Use the local font index as a filter, never a chooser.** `google-fonts` lists category, subsets, axes, styles, designers and license, with no mood or construction terms, in lexical order. Shortlist by category and script (`python <skill-directory>/scripts/search.py "serif cyrillic" --domain google-fonts`), list superfamily siblings by a family-name stem, and read Axes and Styles. Judge three to five candidates in specimens with real content; confirm license and files ([cli-reference.md](cli-reference.md#interpret-output-honestly)).

## Color Construction

Default painted-area proportions:

| Role | Brand or editorial | Utility or app |
|---|---|---|
| Neutral: canvas, surfaces, rules | about 60% | 85–90% |
| Dominant: the subject's color as field, band or ink | about 30% | 5–10% |
| Accent | 10% or less | 5% or less |

Deviate when a verified brand leads with a full field; the dominant then becomes the canvas.

1. Sample the dominant from the subject's materials or artifacts (card stock, steel, ink, signage paint).
2. Tint neutrals toward it: OKLCH chroma about 0.005–0.02 at its hue for light surfaces, with even lightness steps.
3. Give each accent hue one job: action, selection, one domain state or one data series. Default one accent hue; add a second only for a job weight or position cannot carry.
4. Keep status hues apart from the accent so "selected" never reads as "warning".
5. Check 4.5:1 for text and 3:1 for focus, controls and graphics, then judge the full render with the [color and material rules](design-foundations.md#color-and-material).

## Composition

| Move | Default | Check |
|---|---|---|
| Grid | 12 columns on desktop, 4–6 on tablet, 4 on phone; gutters 16–24 px; outer margin at least one gutter | five alignment axes per view at most |
| Deliberate break | one or two per view, owned by the focal or signature element: full bleed, hanging into the margin, spanning rows | offset a full column or to the frame edge; small offsets read as errors |
| Asymmetry | a 7/5 or 8/4 split; center only single-message moments | the light side holds something by intent |
| Cropping | crop subject images tight for scale; bleed display type off an edge only while it stays readable | never crop body text |
| Scale jump | routine steps adjacent on the ratio; one jump of 3+ steps per view | the jumped element is the real priority |
| Density rhythm | alternate dense and open bands; in apps, a dense work region inside calm chrome | density follows content |
| Edge tension | margins of 24 px or more (16 px on phones) for calm; bleed or near-edge placement for energy | text keeps its safe margin |

Mechanics and responsive transformation: [design foundations](design-foundations.md#composition-and-hierarchy).

## Imagery, Material and Motion

| Facet | Decide | Default | Mechanics |
|---|---|---|---|
| Imagery | one treatment rule for every image: crop, grade, frame (bleed, mounted, inset), relation to type | no image until a slot has a job | [imagery-and-assets.md](imagery-and-assets.md) |
| Material and texture | surfaces from the subject's material | flat surfaces, 1 px rules; texture only on the canvas or signature surface, grain at 4% opacity or less, never under small text | [shape and edge](design-foundations.md#shape-and-edge-language) |
| Motion personality | posture (immediate, functional, expressive) and character: mechanical (short ease-out, no overshoot), soft (longer ease-in-out) or springy (overshoot under 5%) | immediate controls; functional motion for state changes | [motion-and-interaction.md](motion-and-interaction.md) |

## Translate the Direction Into Tokens

Write the token sheet before components and name tokens by role (`--accent`, not `--green-500`). Each signature decision becomes a token or named variant so it cannot drift.

| Group | Tokens | Derive from |
|---|---|---|
| Type | `--font-text`, `--font-display`, `--font-mono`; `--step--1` to `--step-5`; line height and tracking per role | ratio 1.2–1.25 quiet, 1.333 balanced, 1.5+ loud |
| Color | `--canvas`, `--surface`, `--surface-raised`, `--ink`, `--ink-muted`, `--rule`, `--dominant`, `--accent`, `--on-accent`, `--focus`, `--status-*` | proportions, one-job accents |
| Radius | `--radius-control`, `--radius-container`, `--radius-overlay` | material: paper 0–2 px, molded plastic 6–12 px |
| Elevation | `--elev-0` to `--elev-2` | what sits above what |
| Space | base 4 or 8 px; `--space-1` to `--space-8` | density |
| Motion | `--dur-fast` 100–150 ms, `--dur-base` 200–250 ms, `--dur-slow` 300–350 ms; `--ease-out`, `--ease-in-out` | motion posture |

Type scale: size(n) = base × ratio^n, rounded to whole pixels. Base 16 at ratio 1.25 gives 13, 16, 20, 25, 31, 39, 49.

## Generate Two or Three Directions

Default: three directions for an open identity, two for a bounded visual thesis, on fixed brief, content, page job and viewport. Directions differ in signature move and at least one loud axis; a palette, radius or icon swap is the same direction renamed. Use three generators:

| Generator | How |
|---|---|
| Vernacular | take one of the subject's own artifacts and make it the frame |
| Transfer | apply a principle from an adjacent medium: print, signage, instrument, map, packaging |
| Reduction | hierarchy by type, space and order alone, no motif; every other direction must beat it |

Record each as `thesis | source | signature move and boundary | loud axes | pairing strategy | color proportions | image and material | motion posture | risk`.

Sketch each at the primary surface with real content at one width; judge the thumbnail before reading its rationale. Kill a direction that:

- resembles another direction or a common template at thumbnail size;
- needs placeholder-short copy, a perfect image or an unavailable asset;
- lets its loud axes compete with the primary task;
- fails legibility or contrast in its own palette;
- breaks in a repeated item, form, long heading or narrow width.

Render survivors with a secondary context and select with [exploration-protocol.md](exploration-protocol.md#6-converge-without-false-precision). When the brief asks for distinctive character, recognizability and product-specific invention count beside clarity and fit.

## Worked Derivations

**Herbarium catalogue** (browsing digitized plant sheets)
- Subject: plants on cream archival card at about 1:1.45; typed label lower right; binomials italic by convention.
- Move: each record is a sheet, image on a mount at sheet ratio with data anchored lower right, on grid items and detail pages; search and filters stay plain. Loud: space and image scale.
- Type: structural contrast; a text serif whose true italic sets binomials, a mono for accession numbers; Latin Extended for collectors' names.
- Tokens: `--canvas: oklch(96% 0.015 85)`, `--ink: oklch(25% 0.02 60)`, `--accent: oklch(52% 0.17 28)` for type specimens only; ratio 1.25 from 17 px; radius 0; no shadows; `--sheet-ratio: 1 / 1.45`.

**Chess tournament pairings** (checked on phones between rounds in a noisy hall)
- Subject: pairing sheets pinned to a wall; board numbers; white and black assignments.
- Move: the board number is each row's largest object, with literal white or black squares beside the names. Loud: scale, weight; color stays black, white and gray plus one accent for the player's own row.
- Type: one family with tabular figures, from a superfamily whose mono sets game notation.
- Tokens: board number 48 px at weight 800; names 20 px; ratio 1.333; `--radius-control: 2px` echoing the squares; one 200 ms crossfade when a round is published.

**Kitchen order rail** (display read from about 1 m across the pass)
- Subject: printed order slips clipped to a steel rail as they arrive; all-caps thermal print; modifiers handwritten in red.
- Move: orders as tall strips on a horizontal rail; age shows as a heat band on each slip's top edge beside the printed timer, stepping at the kitchen's target times. Loud: color, weight.
- Type: one family with width and weight axes: heavy condensed item names, regular normal-width tabular timers.
- Tokens: dark steel `--canvas`, slip-paper `--surface`, three-step heat ramp, red `--accent-modifier`; item names 32 px and nothing under 26 px at 96 ppi (20 and 16 arcmin at 1 m); ratio 1.25; radius 0; new orders slide in over 200 ms, instantly under reduced motion.

## Hand Off the Direction

Record in the existing decision record: thesis and perceptual job, subject sources, signature move and boundary, contrast budget, token sheet, forbidden drift ("no second accent"), the strongest rejected direction with its decisive weakness, and a revisit trigger. Before scaling, pass the [early gate](quality-gates.md#early-gate-for-a-visual-system). Keep a material successful invention as a conditional project hypothesis (source, mechanism, comparison, outcome, counterexample), not a global taste rule. Reopen the direction when real content, rendered behavior, assets or platform constraints break its premise. A user-rejected proposal stays rejected until a materially changed one is reviewed.

## Check

- Subject observations, not adjectives, drive every decision.
- One signature move with a written boundary survives the subtraction test.
- One or two loud axes; the rest quiet.
- At most two families plus a mono, each with a role, checked at real sizes, scripts covered, fallbacks written.
- Each accent has one job; neutrals are tinted; proportions match the defaults or a stated reason.
- A named grid with at most two deliberate breaks per view.
- Role-named tokens exist before components.
- The selected direction beats the reduction at narrow, pressure and wide widths, including a repeated item.
- Rendered review follows [quality-gates.md](quality-gates.md) and [failure-patterns.md](failure-patterns.md).
