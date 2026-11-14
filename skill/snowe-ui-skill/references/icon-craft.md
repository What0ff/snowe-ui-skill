# Finish a custom icon inside its owner

Use for new custom interface glyphs, a family extension, or a reported raw, crooked or contextually weak result. When custom drawing is the right exploration ([when](iconography-system.md#develop-custom-candidates-where-they-add-value)), improve a promising construction before falling back to a near-match from a library; custom is an authorship choice, not an exemption from recognition or accessibility.

Resolve the [symbol role](iconography-system.md#resolve-identity-before-inventing-a-metaphor) first: a third-party brand uses verified supplied artwork, and this loop serves the product's own open symbols. Establish the action, object or state and the nearest meaning it must not imply, in a semantic brief tied to the real slot rather than to adjectives or invented capabilities.

## Start with the actual slot

Inspect the owning button, row or tab before drawing: glyph CSS size, target and hit region, label and gap, line height and baseline, padding, state indicator, clipping, neighboring glyphs, theme and DPR. Separate the glyph box from the button box and its painted backing. A 24 px construction does not belong in an 18 px slot just because it scales without overflow.

Render the rough skeleton in that exact owner immediately. Derive live area, optical weight, corners and direction from the control family, not a generic SVG preset; a dense labelled button can need a simpler, more open glyph than an isolated service illustration. Keep the accepted control geometry instead of inflating buttons around an over-detailed draft, and keep text for an unfamiliar action.

## Make the drawing intentional

Choose one dominant silhouette and one essential distinguishing cue, and test the skeleton without decoration. For a mechanism, show the relationship that makes it specific: a measured span needs two termini and a dimension relationship, while a generic ruler rectangle loses that meaning at small size. Never compress a whole feature description into a stack of tiny pictograms.

Use coherent primitives, a small set of curves and intentional terminals, with as few paths as clarity allows but never at the cost of optical correction. At each join, check for a clean close, a dark knot, an accidental gap or a tangent that reads as a second object. Round caps lengthen strokes past their endpoints and can collapse nearby counters, so adjust the geometry, not only `stroke-width`. Diagonals and curves need their apparent thickness checked against horizontals and verticals; a circle often needs different dimensions from a square to read as a peer; triangles and asymmetric subjects need optical rather than equal numeric padding.

Inspect positive and negative shapes together: uneven interior gaps, a modifier that nearly touches the body or one detail denser than the family make an outline feel raw. Keep a detail only if it changes recognition at the implemented size. A thin, fragmented or timid mark needs stronger construction (remove incidental segments, open counters, balance the dominant masses, redraw joins and diagonals that merge), not every path thickened, which closes gaps and outweighs neighbors; rounded caps alone do not make a family polished. For a 16 or 20 px owner, simplify around that slot or draw a deliberate small optical variant rather than scaling down a good large drawing.

Move the visible mass, not the hit target, for optical correction. Compare the offset against the zero-offset baseline in the actual button with its real label, aligning to the right visible center or text baseline. A blanket `translateY(1px)` or distorted aspect ratio is never the fix; exact centering and path count are construction facts, not finish.

## Build solid and duotone forms

The stroke advice above applies to outline glyphs. Solid and duotone forms are built from masses:

- Start from the silhouette as one filled shape. Express inner detail as cut-outs (counters) using `fill-rule="evenodd"` or opposite winding, not as strokes laid over a fill.
- Keep cut-out widths consistent across the family, and no narrower than one device pixel at the smallest target size. Leave gaps between separate parts at least as wide as a cut-out, or they merge at 16 px.
- A solid glyph reads larger than its outline peer. Shrink its live area slightly, then compare both in the same row until their apparent size matches.
- Corner radius is more visible on a mass than on a stroke. Keep one family radius, and round outer corners slightly more than inner cut-outs.
- For an outline/solid pair, keep the same skeleton: the solid version fills the outline's interior and turns inner strokes into cut-outs. Switching between them must not shift the glyph's position.
- Duotone: the secondary tone is one filled area behind or inside the primary silhouette. Hide the secondary layer and the glyph must still read. Check forced-colors mode, where both layers may render at full strength.

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
