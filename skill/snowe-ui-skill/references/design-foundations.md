# Design Foundations

Use this reference to turn an accepted architecture and art direction into a coherent visual system. Foundations are role contracts, not universal recipes. Existing verified systems remain the baseline in evolution work; new work derives tokens from real content, platform, perception, and behavior.

## Composition and Hierarchy

- Define the attention order for each important viewport and state.
- Use scale, proportion, alignment, rhythm, spacing, contrast, image/content relationships, and disclosure before adding containers.
- Let important content occupy meaningful space; equal boxes produce equal visual weight even when the content is not equal.
- Establish a small set of alignment axes and break them only to create an intentional focal event.
- Use whitespace as structure. Use dividers, tonal change, or type hierarchy before cards when content is not an independent object or action.
- A monitoring, comparison, editing, or creative workspace may have coordinated peer regions rather than one dominant focal point. The task decides.
- Marketing and editorial pages need rhythm, but rhythm can come from content density, media, type, alignment, or interaction—not a forced alternation of identical sections.

## Layout and Responsive Transformation

### Placement and Alignment

Choose the reference frame before aligning: the content column, control, panel, visual group or viewport. A sidebar or asymmetric padding can make viewport centering wrong for the usable region. State whether the role needs edge alignment, text baseline, geometric center, optical center or a deliberate offset. Inspect the real box, internal padding and visible glyph/image mass; `align-items:center` alone does not prove visual balance.

Place actions near the object and decision they affect. Keep related labels, values and controls grouped; repeated peers should use consistent axes. Compare the accepted position with a credible alternative when placement is open. Do not center long reading text, lists or numeric columns by default, and do not preserve an arbitrary offset merely because it avoids centering. If a supplied reference specifies placement, conformance remains the target.

### Bounded Lists and Scroll Ownership

Decide which surface owns scrolling. A document/content page may grow naturally; a list inside a height-bounded dialog, dashboard panel or persistent workspace should scroll in its assigned region while its heading and actions remain reachable. Establish the parent height/max-height and shrinking chain, use `min-height:0` on the relevant flex/grid children, and apply `overflow:auto` to the list owner. Do not hide rows, shrink text or put overflow on an unrelated ancestor to disguise the failure.

Check long/empty/loading lists, keyboard focus and scrolling, and narrow/touch layouts. A scroll region needs a useful accessible name and keyboard reachability where native focusable contents do not provide it. Keep focused items visible and avoid nested scroll traps. At a mobile breakpoint, explicitly choose retained internal scrolling or a coherent page-flow transformation; do not accidentally inherit an unbounded desktop panel.

- Begin with content relationships and task sequence; choose grid and breakpoints after the composition exists.
- Use intrinsic sizing, flex/grid, container queries, `min()`, `max()`, and `clamp()` where they improve resilience.
- Define invariants and transformation rules for order, navigation, disclosure, comparison, imagery, sticky behavior, and input mode.
- Test a pressure width where the chosen composition becomes difficult, not only popular device presets.
- Preserve readable measure for sustained text, scan alignment for dense data, and spatial/attribute relationships for comparison.
- Do not hide the primary outcome, shrink type below readability, or create page-level horizontal scroll to save a desktop composition.

No fixed 4/8/12 grid or gutter scale is mandatory. Use a scaffold when it fits; derive another when the content, brand, platform, or interaction needs it.

## Typography

Choose type from language, content, role, metrics, and voice.

Inventory:

- required scripts, locales, diacritics, bidirectionality, and fallback paths;
- headings, body, navigation, labels, validation, prices, currencies, dates, units, tables, code, and identifiers;
- longest realistic strings, shortest labels, user-generated content, and missing-glyph behavior;
- actual font files, license, weights, axes, subsets, loading, and synthetic style behavior.

Define role contracts before family names. A display face may create authorship, a text face may disappear into reading, and a numeric or mono role may support comparison—but every additional family must earn its semantic or brand role.

Keep a compact role map in the existing implementation/decision record: `role → family stack → real weights/styles/axes → size/line-height/tracking → scripts → owner → exception`. Start from the accepted system. In an ordinary interface, reuse its primary text family for body copy, navigation, labels and controls unless a verified role needs a deliberate contrast. Express hierarchy first through size, real weight, spacing and placement rather than changing family section by section. Prices do not automatically need a different font; tabular figures within the existing family may solve alignment. Preserve an accepted display face, code face, logotype and legitimate script-specific fallback.

Audit assignments across the whole affected composition, including similar cards, repeated headings, tooltips, menus, dialogs, validation text and embedded chart labels. Reused library components can silently import a different default stack. Fix the shared typography token, inheritance/reset or component variant at its owner, rather than adding independent font overrides to each occurrence. Make native controls inherit the relevant role where appropriate; do not globally force every element to the body font and erase intentional display, code, icon-font or locale roles.

Critique the combination as well as its implementation: compare x-height, width, density, terminals, numerals and tone in actual neighboring text. Two nearly similar faces may look like a mistake; dramatic contrast may compete with the task. An explanation that each font is attractive does not establish a coherent page. If an extra family has no distinct role, compare the same content using the accepted role family and retain the extra face only when its contribution is visible. No fixed font-count limit can replace this judgment.

Compare candidates on identical real content at target widths. Inspect x-height, width, rhythm, line breaks, baseline, punctuation, numeral alignment, fallback shift, and loading failure. A font specimen, popularity rank, or dataset pairing is discovery evidence only.

Verify real font files, declared weight ranges, styles and required script coverage. A requested weight may be synthetic or mapped to the wrong static file; a Latin subset may fall back within a Cyrillic label. Browser rendered-font inspection, where available, can expose which face supplies actual glyphs. `getComputedStyle().fontFamily` reports the requested stack, not necessarily the rendered face; `document.fonts.ready` and `document.fonts.check` alone do not certify glyph coverage or visual coherence. Required fallback/loading states may differ transiently but must remain readable and usable; the settled intended state still needs separate proof.

Distinguish the CSS alias from the font's internal family/PostScript name. Variable fonts can report a named base face even while rendering another valid axis value; a name such as “ExtraLight” alone does not prove the wrong weight. Verify file/axis mapping and the actual rendered result before diagnosing synthesis or substitution.

Use fluid size where it preserves hierarchy, not as a default spectacle. Avoid very light small text. Use tabular figures when alignment communicates meaning. Allow zoom and system text scaling without clipping or content loss.

## Color and Material

Start with semantic and perceptual roles:

- canvas, surface, raised/overlay, foreground, muted, border/divider;
- primary/secondary actions and their foregrounds;
- focus, selection, hover, pressed, disabled;
- success, warning, danger, information, availability, or domain states;
- data series, annotations, imagery interaction, and brand expression.

Compare complete systems on real hierarchy and states, not isolated swatches. Verify rendered contrast, color vision resilience, theme behavior, compositing, and image overlays.

Color can be quiet or exuberant. Gradients, glow, translucency, texture, hard color blocking, dark foundations, or monochrome can be strong when they express the brief and remain legible. They are not defaults and not forbidden tokens. Reject a treatment when repetition, contrast, performance, or generic trend resemblance weakens the product.

Material is broader than shadow and blur. It includes edge, join, density, layering, texture, line, transparency, image treatment, and how surfaces respond to state. Define a small semantic elevation/layering model when layering exists.

## Shape and Edge Language

Shape follows component behavior, visual thesis, platform, content, and hierarchy.

- Define edges by role: small detail, control, container, overlay, image, semantic token, or genuinely circular object.
- Keep interaction targets independent from visible geometry.
- Use pills when compact selection/removal, a meaningful token, or verified brand/native behavior benefits from that silhouette. A short string alone is not a semantic token. Ordinary metadata, section eyebrows, navigation links, fields, and calls to action do not inherit a capsule from a nearby filter.
- Use circles where the silhouette communicates the object or action.
- Sharp, rounded, irregular, cut, framed, or borderless systems can all work when coherent and usable.
- Check nested surfaces, text fit, focus, selected, disabled, and error states together.

Do not derive a system from one global radius dial. A repeated edge can be an identity carrier, but it needs a product reason and repetition boundary.

For a new or revised shape system, distinguish interactive controls, selected/filter tokens, passive status, and plain content in the rendered context. They may share curvature, but must not acquire indistinguishable affordances or equal emphasis. Compare a disputed capsule with unwrapped text, a bounded control, or another role-appropriate treatment using identical content. Keep the capsule when it improves recognition, state reading, or established identity; otherwise remove the wrapper and rebalance spacing/type. Do not replace every pill with a rectangle and call the hierarchy repaired.

## Surfaces and Containers

- A card is justified when content behaves as an independent, selectable, movable, comparable, purchasable, or actionable unit.
- Ordinary sections often need only alignment, spacing, type, or a divider.
- Avoid card-in-card structures unless the object hierarchy is real and visually legible.
- Use shadow, border, tone, texture, blur, or overlap to explain layers or interaction. Remove them when they only decorate.
- Never add hover lift to a noninteractive surface.

## Controls and Components

Choose components by behavior and platform semantics, then style them within the direction.

- Use links for navigation and buttons for actions.
- Use persistent labels for form fields; placeholders are supplemental.
- Preserve native or repository primitives when they meet the task.
- Custom controls must reproduce keyboard, focus, selected, disabled, validation, text scaling, and assistive-technology behavior.
- Visible control scale follows density, content, input mode, and brand. The hit target can be larger through transparent non-overlapping space.
- Full-width, oversized, icon-only, segmented, chip, tab, menu, or drawer patterns need a behavioral reason.

For a button family, resolve visible height, content width, horizontal/vertical padding, label metrics, icon size/gap, edge treatment, and alignment from the accepted reference/system or the local density and task. Primary importance can come from placement and contrast; it does not automatically require a taller, wider button. A compact toolbar action, an inline action, and a campaign CTA need not share one size. Likewise, removing pills does not authorize square corners: preserve the reference's curvature or derive a coherent control edge independently of card/image edges.

Compare controls at actual rendered size beside nearby fields, tabs, text, and secondary actions, including narrow and long-label states when relevant. Reject a size/shape change when it departs from the specified target, dominates the content without a task benefit, breaks the density/alignment of its control family, or squeezes essential neighboring content. Trace unexpected size or corners to their owner: inherited font/line-height, component size variant, min-height, padding, flex stretch, global radius utilities, or box sizing. Correct that cause rather than overriding every button globally. Keep the visual box distinct from a larger non-overlapping hit region; enlarging a target must not silently inflate the visible control or steal adjacent targets.

## Icons and Graphics

Define the primary drawing language and source roles. Familiar universal actions should remain recognizable; product and domain symbols can become more ownable when the metaphor and rendering stay clear. Open [iconography-system.md](iconography-system.md) only when icon-source, metaphor, family, or custom drawing is an active decision.

## Imagery and Illustration

Give each visual a communicative role and a treatment: source, truth, subject, framing, crop, aspect, light/color behavior, caption, responsive transformation, fallback, and loading. Compare no-image and alternative media directions when the visual is material. Open [imagery-and-assets.md](imagery-and-assets.md) only while that decision remains active; stop after a justified no-image choice.

## Motion and Interaction

Define states and transitions before animation. Motion can clarify cause, continuity, hierarchy, progress, feedback, spatial relationships, or narrative. It can also slow, distract, or harm. Start with the static/reduced experience and open [motion-and-interaction.md](motion-and-interaction.md) only when motion is an active decision or defect.

## System Coherence

Coherence is not uniformity. It means roles and exceptions are understandable:

- type roles share a hierarchy even when expressive display differs from utility text;
- icon sources have stable roles and compatible rendered weight;
- product imagery may be rich while routine chrome stays quiet;
- marketing motion may be expressive while frequent controls are immediate;
- one page family may be dense and another spacious while both share product logic.

Document the role boundary rather than forcing one token, package, or visual treatment everywhere.

## Foundation Review

Ask:

- Does every visible system choice support the accepted architecture or art-direction thesis?
- Does the hierarchy survive without decorative effects?
- Do real prices, labels, long copy, missing data, and localization fit?
- Are state, focus, and disabled meanings still clear without color alone?
- Are image and type competing or cooperating?
- Do custom assets belong beside their neighbors at actual size?
- Does responsive transformation preserve priority and conversion?
- Does the result have too many role exceptions to remain teachable and maintainable?
- Can any container, effect, asset, or animation be removed with no loss of meaning or identity?
