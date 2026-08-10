# Design Foundations

Use this reference when defining, implementing, or revising the visual direction of a product interface. First apply [exploration-protocol.md](exploration-protocol.md) so repository defaults do not bound the candidate space. For a new identity, redesign, or material visual change, use it with [art-direction-gate.md](art-direction-gate.md) so the direction is compared and selected before implementation.

## Contents

1. Design intent
2. Composition and hierarchy
3. Layout and responsive behavior
4. Typography
5. Color
6. Shape and pill restraint
7. Control scale
8. Icons
9. Surfaces and elevation
10. Imagery and data visualization
11. Motion
12. Component selection
13. Design review questions

## 1. Design intent

Define the interface before styling individual components:

- Name the product type, primary audience, main task, platform, and expected usage context.
- Write one sentence describing the desired perception, such as “calm clinical precision” or “energetic creator tool.”
- Select one coherent primary direction. Add supporting influences only when their roles and product reasons are clear.
- Choose a memorable signature device—a composition move, type treatment, illustration language, data motif, or material treatment—when it improves recognition. If content, typography, or interaction already carries the identity, explicitly avoid adding ornamental signature work.
- Repeat the signature selectively. If every component is distinctive, the interface has no focal point.
- Anchor the identity in a product-specific noun, workflow, data shape, language pattern, audience behavior, or interaction consequence. A trend label, palette, radius swap, or component-library skin is not an identity by itself.
- Run a subtraction test: temporarily remove the logo, gradient, shadow, and decorative layer. The composition, hierarchy, content behavior, or interaction model should still feel intentional and appropriate to the product.
- Define a repetition boundary for the ownable move. A signature that appears on every surface becomes texture and loses meaning.
- Preserve existing brand assets, tokens, and component language unless the task explicitly calls for a redesign.
- Treat the existing direction as the baseline in exploration, not automatic proof that no external composition, typography, material, imagery, or interaction approach can be stronger. Search relevant external classes before freezing a material decision, while preserving confirmed invariants.
- Freeze the selected thesis, optional signature device, preserved conventions, approved deviations, non-negotiables, and forbidden defaults as an implementation contract. Reopen the direction only when new evidence or a changed brief requires it.

Avoid using “modern,” “clean,” or “premium” as the complete direction. Translate them into observable choices: contrast, density, geometry, type, imagery, motion, and hierarchy.

## 2. Composition and hierarchy

- Establish a clear attention order per viewport or task state. Use one dominant focal point when the workflow has one obvious next step; allow coordinated peer regions in monitoring, comparison, editing, or other genuinely parallel work.
- Create hierarchy through size, weight, spacing, alignment, and contrast before adding containers.
- Keep primary, secondary, and tertiary actions visibly distinct.
- Group by proximity first. Add a divider when separation is needed. Add a card only when the group is independent, actionable, draggable, selectable, or materially distinct.
- Avoid card-in-card nesting unless the hierarchy is meaningful and remains obvious at a glance.
- Alternate section rhythm intentionally on marketing pages; avoid a monotonous stack of identical icon-card grids.
- Let important content occupy more space. Do not give every metric, feature, or action equal visual weight.
- Use whitespace as structure, not leftover space.
- Align content to a small number of shared axes. Misaligned edges create visual noise even when individual components are polished.

## 3. Layout and responsive behavior

- Start with the content and task flow, then choose breakpoints where the composition stops working.
- Use a 4-column compact, 8-column medium, and 12-column wide grid as a starting scaffold, not a mandatory device taxonomy.
- Use consistent gutters: approximately 16px compact, 24px medium, and 32px wide unless the existing product scale differs.
- Constrain long-form text to roughly 45–75 characters per line.
- Prefer `min()`, `max()`, `clamp()`, grid, flexbox, intrinsic sizing, and container queries over fixed viewport assumptions on the web.
- Preserve reading order and task priority when columns collapse.
- Do not solve mobile by hiding the main task, shrinking text, or creating horizontal page scroll.
- Keep fixed headers, bottom bars, and call-to-action bars from covering content or focused controls.
- Account for safe areas on touch devices.
- Test intermediate widths. A layout that works only at a phone preset and a large desktop preset is not responsive.

For data-dense products:

- Preserve scan paths and column alignment.
- Use progressive disclosure for secondary detail.
- Make density adjustable when users have materially different workflows.
- Prefer a stable page shell and flexible data canvas over many floating cards.

## 4. Typography

- Start with content, language, and role—not a fashionable pairing. Inventory required scripts, locales, numerals, punctuation, longest labels, dense values, validation copy, and any code or identifiers before choosing families.
- Scan the full relevant repository, platform, open, and licensed font space after hard script, weight, license, loading, and platform constraints are known. Render the current family and strongest external finalists on identical real content before implementation cost selects the winner; a font-name list or specimen page is not approval evidence.
- Use role-based tokens: display, heading, title, body, label, caption, and data.
- Minimize font families and loaded styles. Give every additional family a specific semantic, brand, script-coverage, numeric, or editorial role and verify the performance and fallback cost; do not fail a system by count alone.
- Build hierarchy through type size, weight, line height, letter spacing, and surrounding space.
- Keep body copy readable and allow browser zoom or system text scaling without clipping.
- Use tighter line height for large display text and more generous line height for reading text.
- Avoid very light weights for small text and long passages.
- Use tabular figures for aligned metrics, prices, counters, and timers.
- Use sentence case by default for interface text unless the platform or brand explicitly uses another convention.
- Write labels that describe the action or value; do not use iconography to compensate for vague copy.
- Load only the font weights and subsets the interface actually uses.
- Inspect the actual licensed files or installed dependency, supported weights or variable axes, glyph coverage, subsetting, loading strategy, and synthetic-bold or synthetic-italic behavior. A font named in a dataset remains `UNKNOWN` until this evidence exists.
- Choose fallbacks with compatible x-height, width, weight, baseline, numeral behavior, and script coverage. Render the fallback path deliberately; do not list `system-ui` as ceremonial insurance.
- For dense numeric products, verify tabular figures, decimal and currency alignment, minus signs, percentages, dates, times, identifiers, and large-value overflow.
- For multilingual products, render representative strings in every required script and realistic localized expansion. Reject the pairing when fallback changes hierarchy, spacing, or line breaks enough to harm the task.
- For right-to-left or bidirectional content, use logical layout properties and verify mirrored directional controls, mixed-script values, numerals, punctuation, reading order, focus order, and truncation in the real platform.

Typography approval requires a real-content proof at compact, intermediate, and wide widths plus zoom or system text scaling. Inspect x-height, character width, line breaks, measure, line height, baseline alignment, numeral alignment, clipping, and font-loading failure. Record the chosen role contract and fallback evidence; do not approve typography from font names or a specimen screenshot alone.

## 5. Color

- Define semantic roles before component colors: background, surface, foreground, muted, border, primary, accent, destructive, focus ring, and their `on-*` counterparts.
- Compare complete semantic color and material systems on the same hierarchy, content, states, and themes before choosing; do not mistake browsing isolated swatches or fashionable palettes for system evidence.
- Use accent color to direct attention, not to decorate every section.
- Verify text and meaningful non-text contrast from rendered colors, including disabled, hover, selected, error, and dark-theme states.
- Do not infer dark-theme colors by simple inversion.
- Communicate status with text, icon, pattern, or position in addition to color.
- Keep data-series palettes distinguishable without relying on red/green pairs alone.
- Treat gradients as a deliberate material or brand device. Do not add a gradient merely to make a control look “premium.”
- When brand evidence is absent, use a context-derived solid foundation and reserve chroma for clear roles. Do not make blue/cyan/violet neon, electric edge light, glow, bloom, aura blobs, or ambient luminous gradients the product identity without a brief, brand, genre, or content reason.
- A supplied brand palette takes precedence after contrast validation. Without one, keep cool chromatic colors local and functional instead of washing the canvas, surfaces, typography, borders, and shadows in blue.
- Do not equate dark mode with navy plus electric blue. A dark theme can use neutral charcoal surfaces and one restrained domain-appropriate accent.
- If a generated contrast check reports `ADJUST`, correct the token pair before delivery; do not hide the warning.

## 6. Shape and pill restraint

Use a component-specific radius scale. A professional default is approximately:

| Role | Typical radius |
|------|----------------|
| Small detail | 2–6px |
| Inputs and buttons | 6–12px |
| Cards | 10–18px |
| Dialogs and large overlays | 16–24px |
| Semantic chips | 6–10px |

These are starting ranges, not universal platform requirements. Let the selected style and existing tokens decide the exact scale.

Role-driven default policy:

- Do not use pills or capsules as generic decoration.
- Do not use full rounding as the default for buttons, fields, cards, toolbars, or navigation. Treat `rounded-full`, `999px`, `Capsule`, and equivalent tokens as clues to inspect, not automatic failures.
- Avoid a wide pill behind a standalone icon when it adds decoration but no state, grouping, platform, or brand meaning.
- Avoid giving every navigation icon or icon-label pair its own pill background unless the items genuinely act as compact semantic choices and the repetition preserves hierarchy.
- Preserve icon hit targets with transparent padding. If visible containment is required, prefer a compact rounded square.
- Show navigation selection with color, weight, an underline, side marker, icon fill change, or a restrained tonal surface.
- Prefer a true pill for semantic chips, tags, filters, statuses, entered entities, and compact choices. Preserve established native or brand components without requiring explicit permission, but do not copy their geometry to unrelated roles.
- Use circles for avatars, true FABs, record or media controls, swatches, and established compact icon controls when the silhouette communicates a real role; avoid repeating circles as generic chrome.
- Avoid repeating even legitimate chips until the screen becomes a field of capsules. Consider a list, menu, checkbox group, tabs, or segmented control instead.
- Do not let chip labels wrap. If the content needs a sentence, it is not a chip.

When native fidelity is relevant to the target platform or existing architecture, preserve the native component. Do not propagate that geometry to unrelated controls without the same platform, brand, or behavioral reason.

## 7. Control scale

Keep visible geometry proportional to the task. A larger accessibility target does not require a larger colored surface.

- Pointer-first dense desktop: use approximately 32–36px visible buttons, fields, and selects.
- Standard desktop: use approximately 36–40px visible controls.
- Touch layouts: use approximately 40–48px/pt/dp visible geometry when the platform component and task call for it, while meeting the applicable interaction-target guidance separately; avoid escalating routine controls to 52–64px without a specific reason.
- Icon-only controls may use a compact 28–40px rounded-square or transparent visible surface while transparent, non-overlapping padding supplies the required hit area.
- Match select triggers to adjacent field height. Keep labels persistent, chevrons compact, and widths driven by content or the form grid.
- Keep segmented controls visually secondary. Do not stretch a two- or three-option selector across the viewport merely to fill space.
- Size desktop buttons to their label and icon. Reserve full-width buttons for narrow layouts, linear forms, or a genuinely dominant task.
- Do not use oversized padding, inflated type, or a tall pill to manufacture hierarchy. Establish importance with placement, contrast, label, and surrounding space.
- Validate adjacent expanded hit areas so they do not overlap or trigger the wrong control.
- Treat the listed size ranges as starting heuristics. Evaluate native geometry, content, input mode, density, brand, and measured usability before treating any exact pixel value as correct or incorrect.

## 8. Icons

- Inventory and reuse the repository’s existing icon sources and wrappers before adding anything.
- Identify the primary interface drawing language and map any additional source to a stable role. Do not infer quality from dependency count.
- Otherwise compare the curated candidates in [iconography-system.md](iconography-system.md), select a platform-appropriate primary source, and keep stroke or fill behavior, corner language, detail level, alignment, and optical weight coherent where icons appear together.
- Use familiar symbols for common actions; pair unfamiliar symbols with visible text.
- Classify each need as universal action, navigation, status, data view, product/domain concept, brand, or decoration before choosing the glyph.
- For product and domain concepts, record `real subject → mechanism/output`, explore enough candidates to make a real choice starting with the primary source, and map the real object, mechanism, input, output, or consequence instead of defaulting to a stock value symbol.
- Treat sparkles, wands, brains, rockets, shields, lightning, globes, puzzle pieces, cubes, generic charts, trophies, stars, and gears as high-cliche-risk metaphors. Use them when literal, learned, branded, or demonstrably clearest.
- Give icon-only actions accessible names and tooltips where the platform supports hover.
- Treat 20–24px/pt/dp as a common visible size, then adjust optically.
- Keep the interaction target larger than the glyph without making the background visually heavy.
- A missing glyph triggers a comparison between visible text, a compatible auxiliary source, and a repository-owned custom SVG. Use the recognition, role-boundary, rendered-compatibility, optical-size, provenance, bundle, license, accessibility, and maintenance gate in [iconography-system.md](iconography-system.md).
- Do not use emoji as structural navigation, toolbar, settings, or status icons. Emoji may remain user content or intentional illustration.
- Use official brand marks from verified assets; do not redraw or recolor them from memory.

## 9. Surfaces and elevation

- Prefer whitespace, tonal contrast, and borders before shadows.
- Use elevation to communicate layering or interaction, not as a universal decoration.
- Keep one small elevation scale and map it to semantic layers such as raised control, menu, and dialog.
- Do not apply hover lift to noninteractive cards.
- Avoid blurred glass over busy imagery unless text contrast remains reliable in every state.
- Keep nested surface radii and padding proportional; an inner element should not look more inflated than its parent without purpose.

## 10. Imagery and data visualization

- Use real assets, licensed imagery, generated visuals, or intentional illustration. Do not ship placeholder gradients or arbitrary stock imagery as final design.
- Explore verified repository or brand assets and relevant licensed, commissioned, generated, diagrammatic, or data-led directions before selecting an image language; compare finalists in the real crop and layout.
- Define an image treatment: crop, aspect ratio, color grade, border, caption, and responsive behavior.
- Reserve image space to prevent layout shift.
- Match chart type to the question: trend, comparison, distribution, relationship, composition, or flow.
- Include units, labels, source context, empty/loading/error states, and an accessible tabular or text summary when needed.
- Reduce chart decoration until the data relationship is dominant.

## 11. Motion

- Use motion to explain cause, hierarchy, continuity, or system status.
- Compare the static or reduced-motion baseline with every materially relevant functional motion model before selecting one; a polished demo clip outside the actual interaction is not evidence.
- Keep feedback immediate. Do not delay navigation or task completion for decoration.
- Animate composited properties such as transform and opacity when practical.
- Make interaction animations interruptible.
- Use a small motion-token set rather than unrelated durations and easing curves.
- Respect reduced-motion preferences and keep the interface fully usable when motion is removed.
- Avoid entrance animation on every item. Animate the hierarchy, not the DOM tree.
- Do not use constant ambient motion near reading or data-entry tasks.

## 12. Component selection

Choose a component by behavior, not by appearance:

For a material component decision, compare behaviorally viable native, repository, and stack-appropriate alternatives through the exploration protocol. Preserve the existing primitive when it satisfies the task; do not let familiarity end discovery or let a component-gallery screenshot trigger a needless library migration.

- Use a button for an action.
- Use a link for navigation to a resource or route.
- Use an icon button for a familiar minor action with a clear accessible name.
- Use a chip for compact metadata, filters, entered entities, or contextual choices.
- Use tabs for peer views that remain available.
- Use a segmented control for a small mutually exclusive set or view switch.
- Use a checkbox for independent multi-selection.
- Use radio buttons for a visible single-choice set.
- Use a select/menu when the option list is long or secondary.
- Use a card only when its contents behave as a meaningful unit.

Prefer semantic/native primitives and the repository’s component library. Custom controls must reproduce keyboard, focus, disabled, selected, validation, and assistive-technology behavior.

## 13. Design review questions

Before implementation or approval, answer:

- Did the task use the appropriate direct, refinement, or full art-direction gate, and what evidence selected the direction?
- What is the first thing the user should notice?
- What is the primary task, and does the action hierarchy match the workflow—including genuinely equal peer actions when they are warranted?
- Which visual choice makes this product recognizable rather than generic?
- Can that product-specific identity be described without relying only on aesthetic adjectives, and does it survive the subtraction test?
- Which findings violate an invariant, and which are merely heuristic warnings such as package count, class name, exact pixel value, hue name, or element count?
- Can any card, pill, shadow, gradient, icon container, or animation be removed without losing meaning?
- Does the palette still look intentional without blue/cyan/violet glow, and was every cool luminous treatment explicitly justified?
- Are visible buttons, selects, segmented controls, and icon containers compact while their actual hit targets remain sufficient and non-overlapping?
- Does the hierarchy survive grayscale, zoom, text scaling, and narrow widths?
- Were the actual font files, required scripts, realistic content, numeric behavior, and fallback metrics rendered rather than assumed?
- Are all component roles behaviorally correct?
- Are real content, long labels, empty states, errors, and loading states represented?
- Does the interface remain coherent in both light and dark themes when both are supported?
