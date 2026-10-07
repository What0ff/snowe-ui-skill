# Doppler Soda — Accepted Design Decisions

All brand, product, flavor, price, packaging, and commercial content in this benchmark is fictional.

## Selected implementation contract

- **Architecture thesis:** a pressure sequence that makes product recognition immediate, gives flavor tuning equal status with drag, explains the three blends, then converts through an editable six-pack.
- **Art-direction thesis:** a compressed pressure field derived from carbonation, label wrap, aluminum reflection, and a product that appears to bend a typographic signal around itself.
- **Primary identity carrier:** the Doppler can crossing and compressing horizontal type/wave fields. It belongs in the opening and selected flavor scenes, not on routine form controls, navigation links, or every section.
- **Focal order:** product/category and can → campaign proposition → selected flavor and all variants → six-pack action → supporting product story.
- **Typography:** local Unbounded for authored campaign/display roles; local Manrope for controls, facts, descriptions, prices, and status. No remote font request.
- **Color/material:** warm mineral paper and near-black provide the stable reading layer; each flavor owns one high-chroma field plus a darker ink tone. Aluminum rims, controlled highlights, shadow, and condensation communicate the physical container.
- **Graphics:** code-native concentric signal bands, bubbles, quantity slots, and three editable SVG label textures. Universal menu, close, increment, and decrement actions stay conventional.
- **Motion posture:** expressive only for the rare product establishment and direct product manipulation; functional for flavor, navigation, and order feedback; still elsewhere.
- **Imagery:** no generated bitmap imagery. The physical product is a code-native composition because coherent rotation, label change, responsive transformation, and reduced motion have higher decision value than a single photoreal still.
- **Conversion:** an in-page six-pack builder begins valid at two of each flavor, exposes explicit quantities, prevents totals outside six, and reports fictional local confirmation without pretending to transact.

## Causal decision graph

### D1 — Product truth occupies the first frame

**Driver → move → consequence:** expressive motion can turn a campaign into a reel → keep `carbonated soft drink`, can format, flavor options, price, and pack CTA in the initial hierarchy → visitors understand what moves and why before interacting.

- **Evidence:** explicit benchmark clarity and conversion requirements; static product/category proof remains visible before JS enhancement.
- **Risk:** oversized campaign type competes with the category line.
- **Revisit trigger:** wide, pressure, or narrow first-view critique cannot identify soda, flavor count, and next action without scrolling.

### D2 — Time communicates pressure release and flavor continuity

**Driver → move → consequence:** carbonation and a cylindrical label are stateful physical phenomena → introduce the can with finite rise/rotation/fizz, then use horizontal drag or flavor buttons to rotate one persistent object → motion communicates material, product sensation, and state instead of generic arrival polish.

- **Evidence:** CSS-3D proof supports perspective, interruption, texture continuity, and local static delivery without a rendering dependency.
- **Risk:** segmented geometry can reveal seams or feel synthetic at intermediate widths.
- **Revisit trigger:** rendered review finds broken rims, label discontinuity, implausible rotation axis, or sustained frame instability.

### D3 — Flavor selection never depends on direct manipulation

**Driver → move → consequence:** drag can express physicality but cannot be the only accessible control → keep visible native flavor buttons with name and blend, synchronized `aria-pressed` state, live copy, and can label → keyboard, touch, pointer, and reduced-motion users receive identical product state.

- **Evidence:** essential actions must not be gesture-, color-, or motion-dependent.
- **Risk:** duplicate controls can look like UI chrome competing with the can.
- **Revisit trigger:** selectors are visually detached from the product or selection state is unclear without color.

### D4 — Generated imagery loses to editable product construction

**Driver → move → consequence:** exact packaging continuity across rotation and flavor states matters more than a single photographic frame → build product and labels from HTML/CSS/SVG, reserve raster output for final evidence only → every viewport and motion mode depicts the same fictional container without text artifacts or inconsistent geometry.

- **Evidence:** no-image, generated-still, video, SVG-only, WebGL, and hybrid comparisons in `CANDIDATES.md` and `ASSETS.md`.
- **Risk:** code-native can may fall short of photographic reflection/condensation.
- **Revisit trigger:** after material/light correction the product still reads as a flat UI illustration rather than aluminum packaging.

### D5 — Conversion stays ordinary and honest

**Driver → move → consequence:** the campaign needs useful product communication beyond the hero but has no backend → use direct quantity steppers, explicit total, price, six-can constraint, and an inline demo confirmation → the final action is legible, reversible, keyboard-safe, and does not impersonate payment.

- **Evidence:** benchmark requires CTA/conversion and real-shaped fictional content; repository benchmarks are static.
- **Risk:** a conventional builder may feel visually unrelated to the campaign.
- **Revisit trigger:** the pack state does not visibly inherit flavor identity or feedback is missed after activation.

### D6 — Responsive scenes change composition, not product truth

**Driver → move → consequence:** the wide product/type collision cannot simply shrink → at pressure width reduce depth and separate labels from the can; at narrow width stack proposition, compact product stage, selectors, and CTA in reading order while removing pointer-dependent tilt → product, flavor, state, and action remain clear without preserving desktop spectacle.

- **Evidence:** required 1440, ~900, and 390 views plus touch and reduced-motion modes.
- **Risk:** mobile product stage becomes either too small to feel flagship or too tall to expose the action.
- **Revisit trigger:** 390 × 844 capture hides all flavor choices/CTA or the can label loses recognition.

### D7 — Reduced motion is a separate composition

**Driver → move → consequence:** removing durations from a 3D entrance would leave a broken spatial premise → show a front-facing, materially lit static can with fixed signal arcs, direct flavor swaps, persistent selection labels, and immediate pack/nav feedback → identity and state survive without spin, fizz travel, tilt, or inertia.

- **Evidence:** motion reference and benchmark requirement; browser smoke inspects emulated reduced mode for active animation.
- **Risk:** hidden animated nodes still consume work or an event assumes a running transition.
- **Revisit trigger:** reduced-motion browser audit reports active animations, missing state, delayed feedback, or different content/action availability.

## Responsive invariants and transformations

| Concern | Wide ≥ 1100 | Pressure 760–1099 | Narrow < 760 |
| --- | --- | --- | --- |
| Invariant | Product/category, selected flavor, all variants, six-pack path, reading order | Same | Same |
| Product scene | Can collides with oversized signal type; pointer tilt and horizontal drag | Can and copy become balanced peers; depth/tilt reduced | Compact front-dominant can below proposition; no hover tilt; touch drag is optional |
| Typography | Campaign word spans stage and can interrupts it | Headline wraps on controlled axes | Display scale and line breaks change; category and CTA stay before supporting copy |
| Flavor switching | Named selector rail beside stage | Full-width rail below scene | Three stacked/scroll-safe buttons with persistent names; tap is primary |
| Navigation | Visible section links and pack CTA | Same until collision | Toggle panel; first link focus, Escape/outside close, trigger focus restoration |
| Heavy effects | Finite 3D entrance, 48-strip cylinder, finite bubbles | Fewer bubbles and shallower pointer response | Fewer bubbles, no pointer tilt, smaller cylinder; animations stop when hidden |
| Reduced mode | Static front can and signal arcs | Same simplified composition | Static compact can; direct state and short non-spatial feedback only |

## Forbidden drift

- No perpetual can rotation, full-page scroll hijack, mandatory reveal sequence, blanket parallax, or movement in every section.
- No remote asset, CDN, analytics, WebGL library, generated lifestyle image, invented certification, or unsupported product benefit.
- No custom icon family for routine controls, generic feature-card grid, or equal-volume sections that dilute the opening carrier.
- No change under `skill/snowe-ui-skill/` unless a reproducible core defect is independently demonstrated.

## Strongest rejected alternative

The Flavor Instrument/WebGL direction remains the strongest challenger. Revisit it only if the dependency-free cylinder fails the material proof after targeted correction or if later user evidence shows that exploration—not immediate comprehension—is the campaign's primary business position.

