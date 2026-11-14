# Failure Patterns

Use before accepting an original visual design, and whenever a result looks generic, templated or "AI-made". Each pattern is a symptom to inspect in the render, not a ban: when one appears, either apply the replacement or record why this product is the exception. Fewer patterns alone do not make a design good; pair this check with a positive direction from [art-direction-gate.md](art-direction-gate.md).

## Generic Output

| Symptom | Usual cause | What to check | Constructive replacement | Legitimate when |
|---|---|---|---|---|
| Purple-to-blue gradient hero, gradient headline text | Model default for "modern" | Does the hue come from the product, brand or content? | Derive a palette from product evidence: one accent with a clear role, neutrals tinted toward it | The verified brand uses that gradient |
| One sans family at one or two weights everywhere (Inter, system UI) | Default stack, no type decision | Do headings, body, data and labels read as different roles? | Assign type roles; create hierarchy with size and weight contrast; consider a display face for identity work | An accepted design system or dense utility already uses it deliberately |
| Every block wrapped in a card, often in a uniform grid | Container-first layout | Is each item an independent object or action? | Group with proximity, alignment, dividers and type; keep cards for independent, comparable objects | A collection of peer objects (products, files, people) |
| Centered hero, three feature cards, centered CTA | Landing-page template | Does the order follow the visitor's decision? | Build the page map first; lead with the offer and its proof | — |
| Icon in a tinted circle or tile above every feature | Decoration default | Does the icon add meaning the heading lacks? | Remove it, place a bare icon by its label, or use a real image or diagram | Platform app grids and launchers |
| Emoji used as interface icons | Convenience | Is there a consistent icon family? | Use a family chosen with [iconography-system.md](iconography-system.md) | Casual user-generated content such as reactions and chat |
| Pills around metadata, eyebrows and plain labels | Styling short strings | Is the capsule selectable, removable or a status? | Plain text with weight, color or position | Filters, removable tokens, status chips |
| Uppercase tracked eyebrow above every heading | Template rhythm | Does it add orientation the heading lacks? | Remove it, or use a real category or breadcrumb | Editorial sections with a real taxonomy |
| Light gray body text (for example `#9ca3af` on white) | "Elegant" restraint | Contrast is at least 4.5:1 for body text | Darker text; build hierarchy with size and weight instead | Disabled controls (exempt, but still legible) |
| Shadows or glows on most elements | Default depth | What is actually above what? | One or two elevation levels; separate siblings with borders or tone | Floating overlays such as menus, dialogs, toasts |
| Glass panels with backdrop blur by default | Trend | Does content behind the panel matter to the task? | Solid surfaces with a clear tone step | Over media where context matters, with a contrast-safe scrim |
| Many accent colors, a rainbow of categories | Coloring everything | Which colors carry a role: action, status, data? | One accent plus semantic status colors; data colors from a validated palette | Charts that genuinely need categorical hues |
| Large radii on everything (24 px and up) | "Friendly" default | Do edges differ by role (control, container, overlay)? | Derive edge logic by role; see [design-foundations.md](design-foundations.md) | A verified soft brand language applied consistently |
| Decorative blobs, orbs, noise or grid backgrounds | Filling empty space | Would the page lose meaning without them? | Use content, product imagery or deliberate whitespace | A brand motif with a defined role and boundary |
| Invented stats, testimonials, client logos ("10k+ teams") | Filler social proof | Is each claim supplied or verified? | Omit unverified proof; show real facts | Real data provided by the user |
| Generic marketing copy ("Unlock the power of…", "seamless") | Template language | Could the sentence describe any product? | Specific claims from product facts, in the audience's words | — |
| Interface text describing itself ("This dashboard helps you…") | Model narrating its work | Does the line help the next action? | Remove it; let headings and labels name things | — |
| `01 / 02 / 03` on unordered sections | Template polish | Does order carry meaning? | Descriptive headings and grouping; see the [numbering incident](#section-numbering-added-as-polish) | Real steps, chapters, references |
| Dark theme in pure `#000` and `#fff` with neon accents | Inverting a light theme | Do elevated surfaces get lighter, and is chroma reduced? | Off-black base, lighter elevated layers, softened text white, less saturated accents | OLED-specific products that verified the choice |
| Hover lift or scale on every card | Default interactivity cue | Is the element actually interactive? | Hover only on interactive elements, with a change that doesn't shift layout | — |

![Generic landing page for a squad availability app](figures/landing-generic.png)

**Generic:** a purple gradient, one system sans, a centered hero whose copy fits any product, invented metrics, and three identical feature cards with emoji icons.

![Authored landing page for the same offer](figures/landing-authored.png)

**Authored:** the same offer, led by the question it answers, set in a condensed display face on pitch green and chalk, with the real availability sheet as the hero image, the price stated, and orange used only on the action.

## How to Use

1. Look at the full render first, at thumbnail and actual size, before reading the code or your own rationale.
2. List each pattern you see, with the element and the state.
3. For each, apply the replacement, or write the one-line reason this product is the exception.
4. Rerender and compare. Removing a pattern must leave a positive design, not an emptier one. If the result looks bare, revisit the direction with [art-direction-gate.md](art-direction-gate.md) rather than adding new decoration.

## Recorded Incidents

Specific past failures, kept as worked examples. Each entry names the general lesson; apply it only where the same mechanism exists.

### A detached-looking lid on a rotated 3D can

![Detached-looking lid reported in a product scene](figures/lid-artifact.png)

- **Symptom:** a bright oval floated above a CSS-3D can and was explained away as "metallic lighting".
- **Cause:** the cylinder was built from `getBoundingClientRect()` width, an axis-aligned screen box that already includes ancestor transforms, while the lid used local CSS width, so the parts used incompatible geometry. A first repair still hid the visible top at that camera angle, and a second exposed the radius mismatch.
- **Fix:** build both parts from local resolved dimensions under one rigid 3D owner, with a viewing angle that shows the real surface.

![Repaired local geometry and connected top surface](figures/lid-repaired.png)

- **Lesson:** derive object geometry from local dimensions and apply one projection. Projected boxes stay correct for hit testing and placement. Verify painted contact, not DOM attachment, and do not dismiss an unexplained bright sliver as lighting before checking that it attaches to its surface. Deliberate foil or illustrated reflections remain legitimate.

### A focus ring that vanished beside a dark button

- **Symptom:** after the lid repair, keyboard focus on a dark button showed no ring against the light area around it.
- **Cause:** the ring inherited a light `currentColor` meant for the button's text.
- **Lesson:** focus rings, borders and icons are separate contrast roles. Check each against its own adjacent substrate in the real focus state.

### A short menu stretched across a tablet header

- **Symptom:** a five-item navigation menu spanned the full header width at tablet size.
- **Cause:** `left: 0; right: 0` was convenient, not chosen.
- **Lesson:** size a secondary surface from its content and its relationship to the trigger.

### Section numbering added as polish

- **Symptom:** landing-page benefits, services, testimonials and ordinary sections carried `01:`, `02:`, leading-zero counters (including CSS-generated counters) or oversized indices. The numbers implied sequence, priority or progress among unordered peers and competed with the real headings.
- **Cause:** numbering was applied as a default polish device instead of being treated as a content relationship.
- **Fix:** descriptive headings and grouping for unordered peers; the unsupported counter removed at its shared owner, not swapped for letters, Roman numerals or icons.
- **Lesson:** a visible ordinal is a content relationship. Keep it when changing the order changes the meaning, when visitors use the numbers to navigate or refer back, or when a supplied design establishes it; a familiar benchmark's numbering is not evidence for the current brief. Keep process and dependency order, chapters and cross-references, identifiers, factual quantities and requested numbering. When numbering is an open identity choice, compare the same content without it, keeping useful grouping and links, and name the orientation or identity benefit; a style adjective is not one, and no number count or blanket no-numbers rule proves quality. Internal planning lists are separate from the visible page. A reported recurrence blocks the affected visual `KEEP` until the current result is repaired and inspected.

### A field caption that pushed its input off the row axis

- **Symptom:** in a mixed field, filter and action row, a field's caption enlarged its wrapper, so the input sat off the axis of the neighboring filters and buttons.
- **Cause:** alignment was applied to the wrappers rather than to the visible controls.
- **Fix:** align the actual input and button boxes on the axis the composition intends (control center, bottom edge or text baseline are different contracts) while the caption stays with its field, for example a shared controls row with a separate caption, or a correctly aligned field wrapper.
- **Lesson:** separate visible controls from label, help and error wrappers. Inspect CSS flex/grid or Figma Auto Layout at the real owner before changing offsets, and measure the actual input and button owners in the browser (raster measurements from a design file are estimates). Do not compensate with per-button translations or force equal heights where different roles are justified. Check settled fonts, long labels and help, wrapping and sibling states; a multiline toolbar may need a new relationship. No page overflow does not prove peer alignment. A material unexplained shift is `REVISE` until the layout owner is fixed and rerendered; a supplied staggered design stays the target.

### Accents that kept collapsing to pale tints

- **Symptom:** an open accent choice repeatedly landed on the lightest ramp steps, as if "professional", "calm", "accessible" or dark mode implied pastel; the correction then overshot into a fully tinted page skin.
- **Cause:** hue, chroma, lightness and painted area were treated as one dial, and the rationale was never revisited.
- **Fix:** a same-content intensity comparison within the intended product direction, judging fill, foreground and on-color text separately with compositing and interactive states.
- **Lesson:** choose hue, chroma, lightness and area separately; a light color can be strongly chromatic. Revisit the color rationale rather than oscillating between pale accents and a tinted skin. Neither neutrality nor maximum saturation proves quality, and a specified color or accepted role needs no new palette workshop.

### Pills replaced with square buttons

- **Symptom:** after a correction against decorative capsules, controls and icon backings were converted to square corners; the competing emphasis remained and buttons departed from the reference curvature.
- **Cause:** the finding was about an unnecessary wrapper or emphasis, but the repair changed only the shape.
- **Fix:** remove the unnecessary wrapper and rebalance spacing and type; derive control edges from the reference or the control family, independently of card and image edges.
- **Lesson:** a circle-to-square conversion, a smaller radius, recoloring or lower opacity does not by itself resolve an unnecessary backing, and replacing every pill with a rectangle does not repair hierarchy. An oversized or inappropriately squared button fails its control family or target even when it is clickable.

### A variable font reported as ExtraLight

- **Symptom:** font inspection reported a face named "ExtraLight", which looked like proof that the wrong weight was rendering.
- **Cause:** a variable font can report its named base face while rendering another valid axis value; the CSS alias, the internal family name and the PostScript name are different things.
- **Lesson:** verify the file and axis mapping and the actual rendered result before diagnosing synthesis or substitution.

### A screenshot narrower than its layout

- **Symptom:** a capture was described by its image width or the browser launch flag, but it showed a crop of a wider layout.
- **Lesson:** read the browser's actual layout viewport (CSS width and device pixel ratio) before naming the width a review covers.

### Report notes inside the product screen

- **Symptom:** fixture notices, source hashes, test results and implementation disclaimers rendered inside customer screenshots, styled as product copy.
- **Lesson:** keep them in the review report or an inspector outside the target surface. The surrounding report must still say clearly which data is fictional and which screens are prototypes.
