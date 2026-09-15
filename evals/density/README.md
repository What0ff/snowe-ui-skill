# Operator density and visual-direction regression

## Root cause

The supplied Title Bot screen was traced read-only through its real entry, component and stylesheet. Its fixed 100px rows, repeated 24–30px spacing, 25px holder/placeholder text and unconditional 300px queue region accumulate before useful content. Screenshot scale was not measured, so these are source values, not measurements extracted from screenshot pixels.

A second failure occurred in this work: the implementer's first tighter candidate was rejected by the user as unfinished, gray and dull. It must not be treated as a visual KEEP. Correcting density numbers did not resolve composition or establish a finished visual direction. Existing code/palette was being preserved too readily even though that direction was not accepted.

The skill now explicitly reopens the affected visual choice after such feedback, requires a positive product-specific intention for original design, and separates technical fixture acceptance from visual readiness. This does not make every utility colorful or forbid approved restrained references.

## Current candidate

The current after variant changes the composition: title choices become a horizontal selector (two rows on smaller widths), current-title/holder information is grouped, the active title has a clear warm accent, and an original code-native symbol family distinguishes title roles. Both alternatives use the same locally bundled Manrope font and preserve the same text-node inventory and 15px choice labels; content order may change intentionally with grouping. The font's existing OFL record remains under the bicycle benchmark assets.

This is an authored regression/proposal, not a production Title Bot update, a pixel-identical reconstruction, or a user-approved visual direction. The working frontend has not been edited. The original user-rejected tightening remains a documented rejection, not an example of successful aesthetic improvement.

## Technical evidence

- Empty, sparse (two entries) and populated (24 entries) states at 1280, 820 and 390 CSS widths.
- 68px after selector rows retain readable labels and control targets; the Settings height is unchanged between alternatives.
- The after empty region uses 68px, the sparse queue fits its rows, and the populated queue caps at 240px and scrolls by keyboard.
- Holder label/value proximity and queue-anchor stability across states are checked. These bounds belong to this fixture, not a universal compactness rule.
- Exact text-node inventories are compared, allowing deliberate grouping/order changes without removing information. Header, body, native target sizing and actual viewport are separately observable.
- Eighteen lossless captures bind the current fixture and local font bytes to their hashes and measured states in `captures/evidence.json`.

```text
node scripts/browser-smoke.mjs --capture-density
node scripts/browser-smoke.mjs --smoke --scenario density
python -m unittest tests.test_visual_acceptance tests.test_corrections -v
```

The correction-memory regression also verifies that an explicit user rejection reopens previously verified work even when source hashes remain unchanged. Technical PASS cannot overrule that feedback. The existing unchanged editorial example remains a counterexample to mandatory compression.

Visual assessment here is implementer self-review, not a blind model test or a guarantee of future creativity. Current candidate screenshots are proposals; passing geometry, font and scrolling checks does not itself establish visual KEEP or user acceptance.

## Customer copy boundary

Experimental notices belong to this report. The fixture no longer renders the technical footer or, for the six cases, instructions describing its own acceptance exercise. Source-bound captures were regenerated after this copy correction. The standalone functional hierarchy pilot is documented in [Title Bot hierarchy](../titlebot-hierarchy/README.md); this older fixture is still regression evidence only.
