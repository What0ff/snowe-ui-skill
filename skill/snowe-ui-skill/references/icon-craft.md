# Finish a custom icon inside its owner

Use for new custom interface glyphs, a family extension, or a reported raw, crooked or contextually weak result. When custom drawing is the right exploration ([when](iconography-system.md#develop-custom-candidates-where-they-add-value)), improve a promising construction before falling back to a near-match from a library; custom is an authorship choice, not an exemption from recognition or accessibility. Build a family, and any glyph that joins one, with [glyph.py](#build-a-family-with-glyphpy); hand-write SVG paths only for a one-off its primitives cannot express, in the same tokens.

Resolve the [symbol role](iconography-system.md#resolve-identity-before-inventing-a-metaphor) first: a third-party brand uses verified supplied artwork, and this loop serves the product's own open symbols. Establish the action, object or state and the nearest meaning it must not imply, in a semantic brief tied to the real slot rather than to adjectives or invented capabilities.

## Start with the actual slot

Inspect the owning button, row or tab before drawing: glyph CSS size, target and hit region, label and gap, line height and baseline, padding, state indicator, clipping, neighboring glyphs, theme and DPR. Separate the glyph box from the button box and its painted backing. A 24 px construction does not belong in an 18 px slot just because it scales without overflow.

Render the rough skeleton in that exact owner immediately. Derive live area, optical weight, corners and direction from the control family, not a generic SVG preset; a dense labelled button can need a simpler, more open glyph than an isolated service illustration. Keep the accepted control geometry instead of inflating buttons around an over-detailed draft, and keep text for an unfamiliar action.

## Make the drawing intentional

Choose one dominant silhouette and one essential distinguishing cue, and test the skeleton without decoration. For a mechanism, show the relationship that makes it specific: a measured span needs two termini and a dimension relationship, while a generic ruler rectangle loses that meaning at small size. Never compress a whole feature description into a stack of tiny pictograms.

Use as few shapes as clarity allows. Consistent primitives, terminals, joins and keylines come from the builder; judging them stays yours. At each join, check for a dark knot, an accidental gap or a tangent that reads as a second object. Round caps lengthen strokes past their endpoints and can close nearby counters, so move the geometry rather than thinning the stroke. Check diagonals and curves for apparent thickness against horizontals and verticals, and give triangles and asymmetric subjects optical rather than equal numeric padding.

Inspect positive and negative shapes together: uneven interior gaps, a modifier that nearly touches the body or one detail denser than the family make an outline feel raw. Keep a detail only if it changes recognition at the implemented size. A thin, fragmented or timid mark needs stronger construction (remove incidental segments, open counters, balance the dominant masses, redraw joins and diagonals that merge), not every path thickened, which closes gaps and outweighs neighbors; rounded caps alone do not make a family polished. For a 16 or 20 px owner, simplify around that slot or draw a deliberate small optical variant rather than scaling down a good large drawing.

Move the visible mass, not the hit target, for optical correction. Compare the offset against the zero-offset baseline in the actual button with its real label, aligning to the right visible center or text baseline. A blanket `translateY(1px)` or distorted aspect ratio is never the fix; exact centering and path count are construction facts, not finish.

## Build a family with glyph.py

`glyph.py` turns one JSON spec into outline, solid and duotone SVGs with validated metadata and a contact sheet ([schema](cli-reference.md#build-an-icon-family)). Tokens are declared once, so stroke, corners, terminals and optical size cannot drift between glyphs, and every selected solid matches its outline.

Derive the tokens from the art direction, not from a library's defaults:

- **Stroke:** match the stem weight of the UI text beside the icon at its rendered size: `stroke = stem px × grid ÷ rendered px`, so 1.5 px stems beside 20 px icons give 1.8, which rounds to 1.75 on a 24 grid. A whole-pixel stroke at the base size also snaps axis-aligned edges crisp.
- **Corner radius:** carry the control radius over in proportion, scaling it by the square keyline (18 units on a 24 grid) over the control height: an 8 px radius on a 40 px button gives 3.5. Override a shape whose character needs a tighter corner, such as a gable.
- **Caps, joins and character:** from the type and the art direction ([give the family a voice](#give-the-family-a-voice)).
- **Detail density:** `low` for dense 16 px interfaces, `medium` by default, `high` only for large feature glyphs; shapes marked `min_detail` drop out below it.
- **Duotone tone:** 0.15–0.35, checked on the real surfaces.

Keep learned metaphors for familiar actions (a magnifier for search, a bell for notifications, a gear for settings, a house for home) and redraw them in these tokens. Invent a metaphor only for a product-specific concept, and keep it only if it beats visible text.

Give every shape a role. A `body` is a closed silhouette that fills in solid and tints in duotone; a `detail` inside a body becomes an even-odd cut-out in solid; a `stroke` stays a positive mark. Fit main bodies to the circle, square, portrait or landscape keylines so unlike shapes read the same size, circles overshooting squares. A line that reaches its body's edge cannot become a cut-out, so limit it with `variants` and give solid an inset version; build a cut-out such as a plus as one shape, because overlapping cut-outs refill under even-odd.

Work in a loop: write the spec, `check` it, `build` it with `--sheet`, inspect the sheet at native size, then adjust tokens or construction and rebuild. The builder refuses off-grid, out-of-area and contradictory geometry and publishes nothing unless every output passes `asset_quality.py`. Its warnings (keyline mismatch, gaps under 1 px at the smallest size, slivers beside cut-outs) are prompts to look, not verdicts.

Test recognition on the sheet, then in the host:

1. **Label-less at 16 px:** name each glyph without its label and tell it from its nearest neighbor.
2. **Squint:** in the blurred row, a glyph that reads darker, larger or lower than its row needs a construction change, not a stroke change.
3. **Side by side:** unlike neighbors (circular, diagonal, dense) share apparent size, weight and baseline. Two marks above a curve read as a face.
4. **State:** in the tab bar, the solid glyph marks the selection without its label; hiding the duotone secondary still leaves a readable glyph, and forced colors may render both layers at full strength.

The sheet is evidence, not acceptance: finish in the owner with the review below.

## Give the family a voice

One stroke, round caps, round joins and a small radius read as Lucide or Feather in any product. Character tokens make the family the product's own ([schema](cli-reference.md#build-an-icon-family)). Derive them from the art direction, never from taste, and apply them to the whole family.

Start from the typeface beside the icons:

| Type | Terminals | Contrast | Corners and proportion | Open forms |
|---|---|---|---|---|
| Grotesk, flat cuts | `butt` caps | none | small radius or `sharp` | none |
| Humanist sans or serif, angled cuts | `terminal: "angled"`, 30–45° | `contrast` 0.6–0.75 | `sharp` with `miter` joins, `narrow` | none |
| Rounded sans | `round` caps and joins | none | large radius | `aperture` |
| Mono or technical, square-cut | `butt` or `square` caps | none | `chamfer` | `junction_gap` |
| Geometric sans, light | `butt` caps | none | `leaf` or a large radius, `wide` at `fill` 0.85–0.9 | none |

Then read the [loud axes and signature move](art-direction-gate.md#one-signature-move):

- **Line or texture loud:** character lives in terminals, corners and junction gaps; fills stay plain.
- **Weight loud:** heavier stroke, round or chamfered masses.
- **Color loud:** an `accent` carries one meaning (the working part, the fresh item); duotone stays for pictograms.
- **Space or scale loud:** light stroke, airy keylines and one quiet signature corner.
- **Shape as signature move:** when the move is a leaf card, a cut corner or a stencil break, the family repeats it as its corner or open-form token. Icons then belong to the product at no extra cost.

Budget by density: a dense data UI or a 16 px row carries one quiet token (contrast or a corner); navigation and marketing surfaces carry two or three. Never use them all, because an aperture, an accent and angled cuts together compete with the label.

Character serves recognition:

- Exempt a shape only where a token breaks its meaning (`"aperture": false` on a head, `"junction": false` on parts that must touch) and record why. A glyph with no closed body simply has no aperture.
- An accent means the same thing in every glyph; write that meaning in `tokens.accent`, and give a glyph none rather than a decorative one.
- Gaps that paint under 1 CSS px close in a small optical set (`<variant>-small/`); inspect both sets.
- Angled terminals, contrast and miter joins expand strokes into exact filled outlines, so the outline variant becomes `fill` mode and CSS can no longer change its stroke width.

Test the voice:

1. Run the recognition steps above. Every glyph must stay nameable in the label-less 16 px row and the squint row. If voicing makes a glyph need its label, ease the token for the whole family.
2. Run `glyph.py compare family.json --sheet compare.html`: the family appears beside its plain monoline baseline (same construction and weight, round caps and joins, a 2-unit radius, no character). If the columns read alike at 20 and 32 px, or the family could pass for Lucide, Feather or Tabler, the voice is not there yet: strengthen first the one token the art direction names.

## Review at three scales

1. **Full composition:** can people tell actions, objects and status apart? Does the family belong to the product rather than a collage of drawings, and does any custom detail pull more attention than its label or task?
2. **Native owner:** compare exact candidates in the same real button or row with identical content, size, background and state, for apparent size and weight, baseline, label gap and recognition without a tooltip, including a blur or squint test. Include a dense repeated context and an overlay when they consume the owner.
3. **Diagnostic detail:** lossless 2× captures expose joins, counters, clipping, fractional scaling, doubled strokes and raster artifacts; then return to native size, because enlargement diagnoses but cannot certify compact recognition.

The [portable observation contract](cli-reference.md#observe-in-a-browser) binds whole-page and owner detail captures. Declare the native slot, DPR, theme and input, and put the SVG and metadata, CSS owner, shared tokens, font and label and any pseudo-element backing in dependency scope. Test the states actually used (normal, pressed, selected, disabled, focus, forced colors where supported), not every permutation.

## Retain the closest losing attempt

Run the loop on the current render: find the most consequential semantic or native-size defect, locate whether geometry or the host causes it, predict one change, rerender the same context, and check whether the cue improved and whether another claim regressed. Repair misleading meaning before detail. A promising custom construction deserves a real repair; switching to a stock near-match without testing the identified repair does not develop custom quality. Stop when the positive bar is met or the improved candidate still loses to a stronger existing or text result. No fixed number of drafts or enlarged specimens proves progress.

Record `observed weakness → cause → geometry/host change → predicted effect → same-context rerender → consequence`. For example: two nearly touching strokes merge at 16 px, so remove an unnecessary inner segment rather than thinning the whole family, and the silhouette should stay clear at neighboring weight; in a larger technical diagram that segment may carry real structure.

Keep why a repair lost: heavier strokes can fix apparent weakness but close counters; a larger viewBox can fix clipping but shrink the glyph; moving it up can fix a standalone center but misalign the label baseline. After changing shared grammar, reinspect neighboring family members. A circular, a diagonal and a dense subject make a useful family stress set, not a mandatory workshop for one accepted glyph.

## Positive acceptance bar

Choose `KEEP` only when the icon looks deliberate and finished in its real owner: clear silhouette, stable negative space, clean joins and terminals, matching apparent weight, intentional optical placement, truthful metaphor and coherent states. A technical SVG PASS, an attractive enlarged specimen, a custom provenance label or a generic "balanced" rationale cannot close this bar, and an enlarged render never excuses a weak actual-size result. Record the context renders and the sizes that passed, and never propagate an accepted large version into uninspected compact controls. If custom stays weaker, repair it or use the strongest existing or text outcome with the reason recorded; never ship a raw custom draft to satisfy a source quota.
