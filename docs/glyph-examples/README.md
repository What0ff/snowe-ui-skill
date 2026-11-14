# glyph.py demo: one family, two voices

Repository-only visual proof for `skill/snowe-ui-skill/scripts/glyph.py`; nothing here ships in the installed skill.

The fictional product is **Larder**, a recipe and pantry app. Each spec draws the same fourteen glyphs: twelve familiar actions that keep their learned metaphors (home, search, settings, user, bell, calendar, chart, folder, lock, upload, download, trash) and two product-specific inventions:

- `scale-servings`: a bowl under two narrowing rims, a stack of portions;
- `pantry-stocked`: a jar with a check, an ingredient already at home.

| Spec | Tokens | Voice |
|---|---|---|
| [`larder-soft.json`](larder-soft.json) | 1.5 stroke, round caps and joins, radius 3, medium detail, duotone 0.22 | Light, rounded, slightly richer (lens glint, calendar days, bin slots, folder flap) |
| [`larder-crisp.json`](larder-crisp.json) | 2 stroke, butt caps, bevel joins, radius 1, low detail, duotone 0.35 | Heavy, flat-cut, chamfered, pixel-snapped, sparse |

The specs share metaphors and nearly all construction; the difference comes from the tokens, plus a few coordinates moved so the heavier stroke keeps 1 px counters.

## Sheets

- [`larder-soft-sheet.png`](larder-soft-sheet.png) and [`larder-crisp-sheet.png`](larder-crisp-sheet.png): the full contact sheet at 1x (every glyph and variant at 16, 20, 24 and 32 px in light and dark, label-less and squinted strips, and tab bars with outline idle and solid selected).
- [`larder-soft-detail-2x.png`](larder-soft-detail-2x.png) and [`larder-crisp-detail-2x.png`](larder-crisp-detail-2x.png): the two matrices at 2x, for joins, cut-outs and terminals.

Rebuild and render (Node 22 and Chrome or Edge; set `CHROME_PATH` otherwise):

```text
python skill/snowe-ui-skill/scripts/glyph.py build docs/glyph-examples/larder-soft.json -o <out>/soft --sheet <out>/larder-soft-sheet.html
node docs/glyph-examples/render.mjs <out>/larder-soft-sheet.html docs/glyph-examples/larder-soft-sheet.png --scale 1 --width 1400
node docs/glyph-examples/render.mjs <out>/larder-soft-sheet.html docs/glyph-examples/larder-soft-detail-2x.png --scale 2 --width 1400 --clip 32,92,1248,656
```

Each build validates all 42 SVGs with `asset_quality.py`, and `tests/test_glyph.py` rebuilds both specs, checks byte-identical regeneration and revalidates every output.

## Self-review

This is the author's critique, not a representative-user study; the PNGs are regression evidence, not proof of recognition in a real host.

- **Consistency:** within each family, every glyph shares one stroke, terminal, corner and density, and the outline, solid and duotone columns read as one family because they come from one construction.
- **Optical balance:** keylines keep circular (settings), square (home, chart, calendar) and portrait (lock, jar) glyphs at the same apparent size; the circle overshoots the square.
- **16 px:** every glyph is nameable without its label. The densest are the soft calendar's day dots, which become a texture, and the gear's teeth, which merge at 16 px in both families yet keep their silhouette.
- **Crispness:** crisp's 2-unit stroke lands axis-aligned edges on whole pixels at 24 px; soft's 1.5 stroke cannot be crisp on both edges and relies on antialiasing, a property of the token rather than a defect.
- **State:** in the tab bars the solid glyph marks the selection by mass alone. Solid upload and download match their outlines on purpose: purely linear glyphs gain no mass, so they suit actions rather than selectable tabs.

Rejected along the way:

- `scale-servings` as "+ −" over a bowl read as a smiley face at every size; a stepper beside the bowl collapsed into "±"; dots, dashes or heads over a bowl were faces too. The stacked rims say "portions" with no face.
- A radius-3 gable rounded the soft home into a dome, so the house takes radius 1.5.
- The crisp solid search was a black disc; a solid-only glint cut-out makes it read as glass.
- The builder's own refusals caught an arc that touched the live edge after SVG rounding, a "+" cut-out whose overlap even-odd would refill, and gaps under 1 px that the painted-outline lint now measures.
