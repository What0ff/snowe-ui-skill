# Finish a custom icon inside its owner

Use for new custom interface glyphs, a family extension, or a reported raw/crooked/contextually weak result. Custom drawings are the preferred exploration for open product-specific roles and when the user prefers them. Improve a promising construction before defaulting to a near-match from a library. Keep familiar meaning and accepted assets unless their decision is open; custom is an authorship choice, not an exemption from recognition or accessibility.

Resolve the [symbol role](iconography-system.md#resolve-identity-before-inventing-a-metaphor) first. A third-party brand mark uses verified supplied artwork; this drawing loop applies to the product's own open symbols. Establish the action/object/state and nearest meaning it must not imply before choosing a silhouette. Keep a compact semantic brief tied to the real slot, not an invented capability or a list of visual adjectives.

## Start with the actual slot

Inspect the owning button/row/tab before drawing. Record glyph CSS size, target/hit region, label and gap, line-height/baseline, padding, state indicator, clipping, neighboring glyphs, theme and DPR. Separate the glyph box from the button box and its painted backing. A 24 px construction does not belong in an 18 px slot merely because it scales without overflow.

Render the rough skeleton in that exact owner immediately. Derive its live area, optical weight, corners and direction from the control family, not from a generic SVG preset. A dense labelled button can need a simpler, more open glyph than an isolated service illustration. Preserve an accepted control geometry; do not inflate every button to accommodate an over-detailed draft. Add or retain text for an unfamiliar action.

## Make the drawing intentional

Choose one dominant silhouette and one essential distinguishing cue. Test the skeleton without decorative detail. For a mechanism, show the relationship that makes it specific: a measured span needs two termini and a dimension relationship; a generic ruler rectangle can lose that meaning at small size. Do not compress a whole feature description into a stack of tiny pictograms.

Use coherent primitives, a small set of curves and intentional terminals. For each join inspect whether it closes cleanly, creates a dark knot, leaves an accidental gap, or makes a tangent that reads as a second object. Round caps can lengthen strokes beyond nominal endpoints and collapse nearby counters; adjust actual geometry, not only `stroke-width`. At diagonals/curves check apparent thickness beside horizontal/vertical strokes. A circle often needs different dimensions from a square to read as a peer. Triangles and asymmetric subjects need optical rather than equal numeric padding.

Inspect positive and negative shapes together. A recognizable outline can still feel raw if interior gaps vary accidentally, a modifier nearly touches the body, or one detail is denser than the whole family. Keep a detail only if it changes recognition at the implemented size. Simplify or create a deliberate small optical variant when the cue collapses; do not scale a good large drawing into an uninspected compact control.

Move the visible mass, not the hit target, for optical correction. Compare the proposed offset against the zero-offset baseline in the actual button with its real label; align to the appropriate visible center or text baseline. Never use a blanket `translateY(1px)` for every glyph or distort aspect ratios to force equivalent viewBoxes. Exact centering and path count are construction facts, not finish.

## Review at three scales

1. **Full composition:** can people distinguish actions, objects and status? Does this icon family belong to the product rather than a collage of individual drawings? Does any custom detail pull more attention than its label or primary task?
2. **Native owner:** compare exact candidates inside the same real button/row, with identical content, size, background and state. Inspect apparent size/weight, baseline, label gap and recognition without a tooltip. Include a repeated dense context and an overlay if they consume the owner.
3. **Diagnostic detail:** use lossless 2× detail captures to inspect joins, counters, clipping, fractional scaling, doubled strokes and raster artifacts, then return to native size. Enlargement diagnoses the cause; it cannot certify compact recognition.

The [portable observation contract](visual-system-and-observation.md) supports whole-page and bound owner/detail captures. Declare native slot, DPR, theme and input in the plan. Include the actual SVG file/metadata, CSS owner, shared tokens, font/label and any pseudo-element backing in dependency scope. Relevant states include normal/pressed/selected/disabled/focus and forced colors when supported; test actual used states, not every theoretical permutation.

## Retain the closest losing attempt

Run the loop against the current render: identify the most consequential semantic or native-size defect, locate geometry versus host cause, predict one useful change, rerender identical context, then check whether the cue improved and whether another claim regressed. Repair misleading meaning before detail. A promising custom construction deserves an actual repair when feasible; switching to a stock near-match without testing the identified repair does not develop custom quality. Stop when the applicable positive bar is met or the improved candidate still loses to a stronger existing/text result. No fixed number of drafts or enlarged specimens proves progress.

Record `observed weakness → cause → geometry/host change → predicted effect → same-context rerender → consequence`. For example: two nearly touching strokes merge at 16 px → remove an unnecessary inner segment rather than thinning the entire family → the dominant silhouette should remain clear and match neighboring weight. The counterexample is a larger technical diagram where that inner segment communicates real structure.

Keep why a repair lost. Increasing stroke weight may fix apparent weakness but close counters; enlarging a viewBox may correct clipping but make the glyph look too small; moving it upward may fix a standalone center but misalign the label baseline. Reinspect neighboring family members after changing shared grammar. An unlike circular, diagonal and dense subject is a useful family stress set, not a mandatory workshop for one accepted glyph correction.

## Positive acceptance bar

Choose KEEP only when the icon looks deliberate and finished in the real owner: clear silhouette, stable negative spaces, clean joins and terminals, matching apparent weight, intentional optical placement, truthful metaphor and coherent states. Technical SVG PASS, an enlarged attractive specimen, a custom provenance label or a generic “balanced” rationale cannot close this bar. Record the exact context renders and the limiting sizes. If custom remains weaker, repair it or use the strongest existing/text outcome with the reason retained; never ship a raw custom draft to satisfy a source quota.
