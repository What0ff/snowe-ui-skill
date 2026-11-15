# glyph.py demo: one family, six voices

Repository-only visual proof for `skill/snowe-ui-skill/scripts/glyph.py`; nothing here ships in the installed skill.

The fictional product is **Larder**, a recipe and pantry app. Each spec draws the same fourteen glyphs: twelve familiar actions that keep their learned metaphors (home, search, settings, user, bell, calendar, chart, folder, lock, upload, download, trash) and two product-specific inventions:

- `scale-servings`: a bowl under two narrowing rims, a stack of portions;
- `pantry-stocked`: a jar with a check, an ingredient already at home.

## The two baselines

`larder-soft` and `larder-crisp` use only stroke, caps, joins and radius. They prove the builder, and they also show the problem the character tokens solve: both still read as Lucide or Feather.

| Spec | Tokens | Voice |
|---|---|---|
| [`larder-soft.json`](larder-soft.json) | 1.5 stroke, round caps and joins, radius 3, medium detail, duotone 0.22 | Light, rounded, slightly richer (lens glint, calendar days, bin slots, folder flap) |
| [`larder-crisp.json`](larder-crisp.json) | 2 stroke, butt caps, bevel joins, radius 1, low detail, duotone 0.35 | Heavy, flat-cut, pixel-snapped, sparse |

## Four voices from four art directions

Each voice derives its character tokens from a stated direction (typeface, loud axis, signature move), following [Give the family a voice](../../skill/snowe-ui-skill/references/icon-craft.md#give-the-family-a-voice). Coordinates move only where a voice's keylines or gaps need it.

| Spec | Art direction | Character tokens |
|---|---|---|
| [`larder-almanac.json`](larder-almanac.json) | **Editorial almanac.** A humanist old-style serif with chiselled, angled terminals; loud axis: scale (large serif headlines over quiet text); signature move: every recipe opens like a printed page | `terminal: "angled"` at 45°, `contrast` 0.65 (details 1.125 against 1.75), `corner: "sharp"` with `miter` joins, `proportion: "narrow"` |
| [`larder-ledger.json`](larder-ledger.json) | **Technical ledger.** A monospaced face with square-cut ends and data set on a visible grid; loud axis: line and texture; signature move: a plotter drawing where strokes never touch | butt caps, `corner: "chamfer"` at 2.5, `junction_gap` 1 (closed in the 16 and 20 px optical set) |
| [`larder-picnic.json`](larder-picnic.json) | **Warm picnic.** A heavy rounded sans; loud axis: weight and a saturated tomato colour; signature move: sticker-like filled marks | 2.25 round stroke, radius 4, `aperture` 2 at 1 o'clock, `accent` (the working part, filled: lens glint, gear hub, clapper, today, keyhole) |
| [`larder-linen.json`](larder-linen.json) | **Calm linen.** A light geometric sans with flat terminals; loud axis: space; signature move: leaf-cornered cards (rounded upper left and lower right) | 1.25 butt stroke, `corner: "leaf"` at 4, `proportion: "wide"` at `fill` 0.9, low detail |

## Sheets

- `larder-<voice>-sheet.png`: the full contact sheet at 1x for all six specs (every glyph and variant at 16, 20, 24 and 32 px in light and dark, label-less and squinted strips, and tab bars with outline idle and solid selected).
- `larder-<voice>-detail-2x.png`: the two matrices at 2x, for joins, cuts, gaps and notches.
- [`voices-compare.png`](voices-compare.png) and [`voices-compare-2x.png`](voices-compare-2x.png): eight glyphs in all six voices side by side at 20 and 32 px, light and dark.

Rebuild and render (Node 22 and Chrome or Edge; set `CHROME_PATH` otherwise):

```text
python skill/snowe-ui-skill/scripts/glyph.py build docs/glyph-examples/larder-ledger.json -o <out>/ledger --sheet <out>/larder-ledger-sheet.html
node docs/glyph-examples/render.mjs <out>/larder-ledger-sheet.html docs/glyph-examples/larder-ledger-sheet.png --scale 1 --width 1400
node docs/glyph-examples/render.mjs <out>/larder-ledger-sheet.html docs/glyph-examples/larder-ledger-detail-2x.png --scale 2 --width 1400 --clip 32,92,1248,656
python skill/snowe-ui-skill/scripts/glyph.py compare docs/glyph-examples/larder-soft.json docs/glyph-examples/larder-crisp.json docs/glyph-examples/larder-almanac.json docs/glyph-examples/larder-ledger.json docs/glyph-examples/larder-picnic.json docs/glyph-examples/larder-linen.json --sheet <out>/voices-compare.html --glyphs home,search,settings,bell,calendar,lock,trash,pantry-stocked
node docs/glyph-examples/render.mjs <out>/voices-compare.html docs/glyph-examples/voices-compare-2x.png --scale 2 --width 1400
```

Each build validates every SVG with `asset_quality.py`: 42 per voice, and 84 for the ledger, whose junction gaps add the closed small set. `tests/test_glyph.py` rebuilds all six specs, checks byte-identical regeneration and revalidates every output. It also pins the soft and crisp builds to their digests from before the character tokens existed.

## Self-review

This is the author's critique, not a representative-user study. The PNGs are regression evidence, not proof of recognition in a real host.

- **Distinct products, not stock sets:** in the comparison sheet, picnic (heavy, open, filled accents), linen (light, wide, leaf corners) and ledger (octagonal chamfers, floating parts) read as three different products at 20 px, and none could pass for Lucide or Feather. Almanac is the **weakest voice**: at 32 px its sharp miters, 45° chisel cuts and light details read as print, but at 20 px the cuts disappear and it reads as crisp with sharper corners and a narrower frame. It needs its typeface beside it to carry the direction.
- **Consistency:** every token is family-wide. Exceptions are recorded in the specs: no aperture on picnic's gear (no straight run or single curve holds it), head (a broken face reads as damage) or lock and jar (no clear place), and ledger's trash handle is a bar because trimming a handle's legs left an odd floating squiggle.
- **16 px:** every glyph stays nameable in the label-less rows. Almanac's 1.125 details paint 0.75 px at 16 px and turn grey: lighter is the intent, but its chart bars are the faintest mark on any sheet. Ledger's 1-unit junction gaps would paint 0.67 px at 16 px, so its 16 and 20 px cells come from the closed optical set.
- **Joins, cuts and gaps at 2x:** cut faces are exact parallelograms, aperture notches in solid follow the outline's gap, and junction gaps keep the full token from the painted edge, oblique and chamfered neighbours included.
- **Solid and duotone:** apertures become notches (picnic's solid search reads as a bitten lens, deliberately playful), accents become cut-outs inside masses (picnic's solid lock gets a real keyhole) and stay positive on open ground (the bell's clapper). Duotone keeps one unbroken tone under gaps.

## Rejected along the way

- **Offset duotone** (the secondary layer shifted like misregistered print) was implemented and removed. Up to one unit, the heavy picnic stroke hides the shift. At 1.25 units it peeks out as a thin sliver that reads as a drop shadow on the light linen voice and as a smeared edge at 20 px, never as deliberate print. A readable misregistration would need more offset than the live area allows.
- **Broad-nib modulation and tapered terminals** were not built. At 16 to 20 px a 1.5 to 1.75 stroke is 1 to 1.5 px; any nib thinning drops parts under 1 px and greys them out, and modulated arcs need approximated offsets where every other expansion here is exact. Almanac takes its stroke contrast from the detail hierarchy instead.
- **Almanac at 30° with round joins and a 1.5 radius** read as the soft baseline with odd ends; 45° cuts, sharp corners and miter joins made the voice. SVG's default miter limit of 4 grew horns at the bell's 53° lip, so expanded miters bevel past 60°. Sharp polyline shoulders made the user a desk, so they became an arc. A slanted keyhole read as "unlocked", so it became a dot. Long 45° rings read as lightning bolts, an energy connotation outside this product, so they became stubs.
- **Ledger at a 2-unit chamfer** read as a radius at 32 px; 2.5 reads as cut. At 3, the octagonal calendar with three dots became a robot face and the chamfered folder a rock, so those two keep smaller corners.
- **Picnic's first home** (a squat house with a filled round window) read as a camera at 16 px; it keeps the door.
- **Builder fixes the voices exposed:** a junction trim measured from the centerline let a chamfer's band or an oblique wall come closer than the token, so trims now measure from the painted end and step back until the gap holds. Expanded closed strokes drew even-odd rings, in which a tight inner corner punched holes, so they are now nonzero paths with a reversed inner edge. A circle's two-arc seam pushed apertures off their clock position, so the seam now sits a quarter turn away.
