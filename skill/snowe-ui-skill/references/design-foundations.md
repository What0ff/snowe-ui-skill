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

Compare candidates on identical real content at target widths. Inspect x-height, width, rhythm, line breaks, baseline, punctuation, numeral alignment, fallback shift, and loading failure. A font specimen, popularity rank, or dataset pairing is discovery evidence only.

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
