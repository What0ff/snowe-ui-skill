# Quality Gates

Use this reference to prove that the accepted design works. Gates protect outcomes and system integrity; they prescribe no style. Scope proof to the calibrated change surface: Direct checks the affected invariant, Focused the affected decision and its shared consumers, Portfolio the required experience slices. Keep findings in the existing task record. For each material decision, state what evidence would keep, revise or reject it, covering the primary outcome, truthful content, accessibility, responsive behavior, important states and build integrity where they apply.

## Verdicts

| Verdict | Meaning |
|---|---|
| `KEEP` | No unresolved blocking finding in the inspected scope, with concrete evidence; it never extends to uninspected routes or states |
| `REVISE` | A repairable weakness; a material one blocks acceptance of the affected scope |
| `REJECT` | The direction or implementation fails a required outcome |
| `UNKNOWN` | Judgment or evidence is missing, such as an unverified font file, claim, asset, device behavior, assistive technology, analytics result or stakeholder fact; never a pass |

Keep four outcomes separate: technical contract, evidence integrity, visual assessment and user acceptance. A review method (self-review, peer review, user review) is not a verdict, and "screenshots inspected" or a technical PASS describes process. Label a self-review as one; neither it nor silence creates user acceptance. A resolution needs an explained change and a current confirming render.

Record each finding once, with its owner, visible observation and user consequence:

```text
KEEP | REVISE | REJECT | UNKNOWN
viewport / input / state | visible or measured evidence | consequence |
correction or acceptance reason | rerender / retest result
```

Assess the intended attention and cue contract against the render for the material states; never require a defect quota or invent novelty to fail an approved quiet interface. A checked JSON [visual report](cli-reference.md#check-a-recorded-visual-verdict) is for reusable material work; a Direct record keeps the method/verdict split inline.

The bar is positive: the affected screen reads as an intentional, resolved experience with coherent hierarchy, rhythm, type and graphics and the character the brief asks for; technical correctness or a quieter layout does not meet it. When the task calls for an authored direction, an unfinished or interchangeable result is `REVISE`: reopen the decision rather than add color, shadow or decoration. Approved restrained references stay valid, and an engineering fixture can pass technically while its visual verdict stays `REVISE`. Judge the implementation, not the author's explanation, reading the artifact and brief before its rationale. For a specified target, a faithfully reproduced trait passes conformance while a usability or accessibility finding about it stays open, without authorizing a silent change to the reference.

| Finding | Disposition |
| --- | --- |
| Truth, primary task, accessibility, or required responsive or state behavior fails | `REJECT`; repair it, whatever the visual appeal |
| Passive labels or status look like controls, or decoration hides the next action or content relationships | `REJECT`; restore semantic and attention hierarchy and rerender. A pill count or radius is not the evidence |
| Repeated cards, badges, effects or section patterns flatten real differences, contradict the thesis, or lose to a credible subtraction challenger without a task or identity benefit | `REVISE`, blocking; change grouping, composition or treatment and compare again. Renaming the style resolves nothing |
| The page reads as the category's untuned median, or as an earlier period the direction did not choose | `REVISE`, blocking where original or impressive work was asked; reopen the direction against the [category's present](art-direction-gate.md#speak-the-categorys-present), with [slop and dated signals](failure-patterns.md#generic-output) as the checklist |
| Local type, crop, spacing, alignment, control size or corner shape, or optical defect | `REVISE` when it affects readability, hierarchy, fit or requested fidelity; an oversized or wrongly squared button fails even when clickable ([incident](failure-patterns.md#pills-replaced-with-square-buttons)). A small cosmetic preference stays only with a scoped acceptance reason |
| A material explicit user correction recurs, or a polished glyph keeps an unsupported backing that competes with labels | `REVISE`, blocking; repair the owner and inspect the current result. Functional failures still take `REJECT` |
| Equivalent text roles drift between families or styles, or files, weights or fallback undermine the typography | `REVISE`, blocking typography acceptance ([typography check](#typography-coherence)) |
| Required render, interaction, content or comparison evidence is absent, stale or inaccessible | `UNKNOWN` for that claim; source inspection does not replace it |
| Applicable proof supports the task, hierarchy, role coherence and requested identity | `KEEP` for the inspected scope |

Bind acceptance to the route or component, viewport, state and an inspected capture or live render of the current revision, and verify the browser's actual layout viewport ([incident](failure-patterns.md#a-screenshot-narrower-than-its-layout)). Uninspected screenshots are not evidence. A build, source scan or score cannot overrule a blocking visual finding, a screenshot cannot certify keyboard or recovery behavior, and pixel difference proves change, not improvement. When proof cannot be obtained, finish the verifiable work and report which claims remain `UNKNOWN`; do not invent a pass, force an approval step, loop through unrelated changes or require a minimum number of iterations.

## Rendered Review Loop

1. Capture the affected state (Direct), the affected comparison and shared contexts (Focused), or the required complete surfaces (Portfolio), adding narrow, pressure and wide widths when responsive composition or a visual system is under review.
2. Exercise the affected task and keyboard path and the applicable open, selected, error, loading and reduced-motion states; fabricate no unrelated states.
3. Review the whole composition and crop, then component detail and optical alignment, including the [icon-backing check](#icon-backings-and-nested-surfaces), [typography coherence](#typography-coherence) for affected text roles, applicable user corrections, and representative shared variants below the fold; a polished first screen does not prove the family.
4. Record findings with direct evidence and consequence, not taste notes.
5. Correct every `REJECT` and material `REVISE` in causal order: truth and architecture, task and interaction, responsive and accessibility, art direction, polish.
6. Rerender the affected evidence; run another complete pass only after a material compositional change or an unresolved major failure.
7. Stop when no blocking finding remains and further change no longer improves a stated driver, or with the unobtainable claims marked `UNKNOWN`.

## Visual and Brand Critique

Review the rendered whole before isolated components:

- Does the attention order follow the user's decision or task, and does the composition hold between showcase widths?
- Do alignment, rhythm, density, measure and whitespace carry hierarchy before decoration?
- Does type fit its column without mid-word breaks, clipping or collision? Zero overflow can hide emergency wrapping; fix measure, scale or composition instead of accepting `overflow-wrap`.
- Is the opening proportionate to the visitor's task and frequency? On returning-user task surfaces, check how far branding or intro copy pushes the first useful choice down on narrow screens.
- Does real content (prices, long labels, missing data, localization) expose false symmetry, repetitive cards, weak grouping or a [generic pattern](failure-patterns.md)?
- Are type, color, material, shape, imagery, icons and motion one thesis with explainable role boundaries and few enough exceptions to stay teachable?
- Does color intensity fit each role (fill, foreground, on-color text, with compositing and states), is the palette resolved across tables, dialogs, fields and supporting surfaces, and was it chosen from a product direction before painting ([color rules](design-foundations.md#color-and-material))? A readable but contextually weak palette is not finished.
- Is the identity carrier distinctive, useful and repeated with restraint?
- Do imagery and custom assets stay truthful, well cropped and optically balanced at actual size?
- Are controls recognizable and important actions proportionate, with button height, padding, type and icon scale, corners and alignment matching the target or control family, and the visible box proportionate beside nearby fields regardless of hit region?
- Can any effect, container, asset or animation be removed with no loss of meaning or identity?

When a finding implicates the accepted premise, compare the strongest rendered challenger and reopen architecture or art direction instead of polishing around a structural mistake.

## Accessibility and Interaction

Verify the implemented result, not the intent:

- semantic elements or correct native equivalents;
- accessible names, descriptions, roles, states, relationships and announcements;
- for icon controls, the chosen [label mode](iconography-system.md#choose-the-control-label-mode) with its name, state, tooltip, touch use and clipping;
- keyboard access, logical focus order, visible focus, focus restoration, escape and cancel, and no traps outside intentional modal behavior;
- targets and spacing suited to the input and context;
- rendered contrast for text, icons, controls, statuses, charts and focus indicators;
- meaning that never depends on color, hover, image, gesture, sound or animation alone;
- labels and errors that explain recovery, keep entered data where safe and attach to the right control;
- zoom, text scaling, reflow, orientation, forced colors, themes, reduced motion and relevant assistive technologies;
- captions, transcripts, alt text or intentionally empty alternatives by media purpose.

Thresholds to check (WCAG 2.2 level AA unless the project sets a different target):

| Requirement | Threshold | Criterion |
|---|---|---|
| Body text contrast | 4.5:1 | 1.4.3 |
| Large text contrast (24 px, or 18.66 px bold, and above) | 3:1 | 1.4.3 |
| UI component boundaries, icons that carry meaning, focus indicators, chart marks | 3:1 against adjacent colors | 1.4.11 |
| Pointer target size | 24×24 CSS px, or enough spacing around a smaller target | 2.5.8 |
| Reflow | No two-dimensional scrolling at 320 CSS px width, except tables, maps and similar | 1.4.10 |
| Text resize | Usable at 200% zoom; `clamp()` type needs a `rem` term so zoom still scales it | 1.4.4 |
| Text spacing | Survives 1.5 line height, 0.12em letter spacing, 0.16em word spacing, 2em paragraph spacing | 1.4.12 |
| Focus | Visible, and not hidden behind sticky headers or overlays | 2.4.7, 2.4.11 |
| Auto-moving content | Pause, stop or hide when it starts automatically and lasts more than 5 seconds beside other content | 2.2.2 |
| Flashing | Nothing flashes more than three times per second | 2.3.1 |

Use `contrast.py --minimum 4.5` (or `3`) for exact opaque pairs, and measure gradients, imagery, transparency, overlays, filters, video and state changes at representative rendered points; a token-level pass is insufficient. A `box-shadow`-only focus ring disappears in forced-colors mode; use an `outline` (transparent if needed) so the system color applies. Automated audits miss reading order, clarity, useful alternatives, focus behavior and task completion, so exercise the primary path and recovery by hand.

## Responsive Transformation

Choose widths from content pressure, not device labels: a narrow width; a pressure width where layout, navigation, comparison, imagery or controls are most likely to fail; a wide width; and the relevant orientation, zoom, text scaling and container contexts. At each, verify priority and reading order, navigation, disclosure, comparison, form labels and errors, sticky behavior, overlays, virtual keyboards, long content, media crop, table alternatives, focus visibility, targets and overflow. Page-level horizontal scrolling is a defect unless the product is a deliberate spatial canvas, and contained data regions still need clear keyboard and touch behavior.

Responsive design may reorder, change navigation or control form, alter disclosure, simplify a graphic, turn a side panel into an overlay or move conversion support closer to the decision. It never merely shrinks the wide composition or hides required content.

### Narrow Screens

Render at 390 and 320 px and at 200% text size, and judge each as a composition designed for that width. Defaults where agents most often fail:

- **Header:** the logo plus one control (a menu, or the primary action when there are two links or fewer); other links and actions move into the menu or the page. The row never wraps, truncates the logo or crowds its groups.
- **First screen:** heading, supporting line and primary action fit the first viewport unless the visual is the message; a heading runs to about four lines at most. Full-height sections use `svh`/`dvh`, not `vh`, and respect `env(safe-area-inset-*)`. Sticky header and bottom bar together take about a fifth of the height at most.
- **Type and input:** body text stays at 16 px or more, and form fields at 16 px so iOS does not zoom on focus. Display type steps down the scale with `rem`-based sizes, so text zoom still works.
- **Diagrams, charts and illustrations:** recompose rather than shrink: fewer nodes, a vertical flow or a separate narrow scene. Labels stay 11–12 CSS px or more at the rendered size, with no collisions between labels, lines and marks.
- **Code, terminals and tables:** wrap where meaning allows. Otherwise scroll inside the block with a visible edge cue and keyboard access, and shorten authored sample lines; tables become stacked rows or keep priority columns with a sticky first column. The page itself never scrolls sideways (`document.documentElement.scrollWidth` equals the viewport width).
- **Touch:** anything shown on hover gets a tap path; targets follow [platform sizes](app-patterns.md#mobile) with space between neighbors; overlays transform as [surfaces](surfaces-and-disclosure.md) specify.

## State and Content Resilience

Test the states that can change understanding or completion: default, hover, pressed, focus-visible, selected, disabled; loading, partial, empty, no result, error, success; validation, destructive confirmation, undo, offline and retry; signed-out, permission-limited and expired; long, translated, bidirectional, missing, user-authored and extreme-but-valid content; open menus, dialogs and drawers, interrupted motion and rapid repeated input. Trace the actual lifecycle and high-risk failures rather than fabricating every state for every element. Empty and error states keep context and offer the next useful action. Required content must be visible and accessibly named, free of clipping and occlusion, in the state under review; presence in the DOM is not enough.

For each affected state change, compare the frame regions and the control under the pointer before and after at the same viewport; unrequested movement or resizing is a material finding ([stable geometry](design-foundations.md#stable-geometry-across-states)). When a live selection or input drives an already-visible preview, quote, result or inspector, exercise that transition: the output must update or visibly invalidate before it can contradict the new selection, keeping inputs, recovery, dependent counts and state styling, because states checked one by one do not prove it. Keep deliberately historical or accepted snapshots as labelled records instead of clearing them like drafts.

## Special Checks

Run a check only when its owner is in the change surface. Owned elsewhere: open secondary surfaces in [overlays-and-selection.md](overlays-and-selection.md) (a polished trigger never closes a raw open surface); page roles, useful text and redundant operations in [page-hierarchy.md](page-hierarchy.md); each secondary task through its surface in [surfaces-and-disclosure.md](surfaces-and-disclosure.md#check); perceptual diagnosis in [visual-reasoning.md](visual-reasoning.md); new custom glyphs in the [contextual icon claims](iconography-system.md#accept-the-context-not-the-drawing-sheet) and [icon-craft.md](icon-craft.md); reusable browser evidence in the [observation contract](cli-reference.md#observe-in-a-browser).

### Conformance to a Specified Design

A definite supplied design closes the visual choices it specifies. This is conformance work, not a new art-direction portfolio: a new codebase or many changed files does not reopen the composition, and generic anti-pattern guidance does not remove its pills, square corners, cards, decoration or proportions. Redesign needs that scope in the user's request; fix implementation deviations yourself.

1. Inspect the actual target (the designated Figma node or frame with properties and variants, or the supplied image or approved interface) with version, frame, dimensions, state, crop and scale. A nearby library component, remembered reference, moodboard or inaccessible link does not prove the instance; report an unreadable source and continue only what the evidence supports.
2. Set the smallest comparison contract: region and state, layout relationships and dimensions, type metrics, gaps, control size and corners, color and surface, asset and crop, specified behavior. Label raster-derived measurements as estimates, not extracted Figma values, and resolve real fonts, assets and variants first, since fallbacks and library defaults change geometry.
3. Implement in the repository architecture, reusing a primitive only when its render matches and otherwise extending the owning variant. A default tall button, square reset, pill utility, stock icon, alternate font or changed text is no substitute because a library supplies it.
4. Compare reference and implementation at matching CSS viewport, content, state and scale, side by side or overlaid, then at target-size detail: layout, reading order and proportions, then type and assets, then spacing, control geometry and optical detail. Pixel differences locate drift but cannot separate antialiasing or environment from a real deviation.
5. Keep a deviation record: `target frame/region/state | specified or estimated value | rendered value/evidence | consequence | correction | confirming comparison`. Use tolerances the source precision supports, never one global similarity score or pixel threshold, and rerender after correcting material deviations.

Unspecified responsive states and interactions get the minimum coherent behavior that keeps known priorities and visual language, labelled as extrapolation; a desktop-only frame proves no mobile fidelity, and an unspecified mobile state does not block a proved desktop scope. A missing font, inaccessible frame or unverified behavior stays `UNKNOWN`. When the reference conflicts with a required accessibility, platform, content or functional constraint, name the conflict and first seek a fix that keeps the visible design, such as correct semantics or a non-overlapping transparent hit region; record an unavoidable departure as an unresolved deviation, never a silent redraw.

### Early Gate for a Visual System

Before repeating a new or revised visual system across pages, render its primary decision surface and one representative secondary or repeated context with real content, at the widths that pressure it, reusing the Focused comparison or Portfolio slice already in progress. Settle reading order, grouping, type emphasis and control hierarchy before spreading decoration; [failure patterns](failure-patterns.md) are inspection triggers, not bans.

When a treatment's value is open, render a credible challenger on identical content, viewport and state, and choose the move from the diagnosed cause: subtraction for competing wrappers, stronger grouping, type, material or graphics for a weak focal hierarchy ([art-direction-gate.md](art-direction-gate.md)). Keep required content and hit targets, and keep whichever version visibly works better. A text-only argument, token swap, weakened challenger or radius-only change cannot settle a compositional finding. Verify visible section numbering as a content relationship ([incident](failure-patterns.md#section-numbering-added-as-polish)).

Check product specificity: set the logo and name aside and ask which content relationships, composition, type, imagery or behavior still follow this brief. A familiar layout can pass on task fit, a claimed distinctive identity needs visible support beyond adjectives, badges and effects, and a utility interface needs no signature motif.

### Detail and Artifact Acceptance

For every touched composition, inspect the whole screen, the affected owner at actual size beside its neighbors, and diagnostic detail at high-risk joins; a thumbnail hides a broken rim, extra highlight, clipped glyph or merged counter. A formal browser plan binds detail crops as well as the whole, and the review assesses each. Direct work covers its own owner and dependencies.

Sweep silhouettes, joints, corners, masks, borders, baselines, small type, image edges and highlights, and trace unexplained paint along `role → component/selector → source owner → tokens → states → consumers → layers` (descendants, pseudo-elements, ancestors, portals and backdrops, font files, images, SVG, canvas, video, shaders, third-party defaults, transformed layers). Write the intended relationship before measuring: computed equality detects drift, not quality, and unexercised branches, shadow roots and runtime styles still need source discovery. A floating cap, overlapping highlight, mask seam or raw icon join is a defect even when geometry fits its box; build transformed objects from local dimensions, not projected screen boxes ([incident](failure-patterns.md#a-detached-looking-lid-on-a-rotated-3d-can)).

For motion, 3D, canvas and media, record scene, data and time, DPR, fonts and textures, color space and loading state; inspect start, peak, interruption, orientation and settled frames at native size, check that attached parts share one spatial model, and compare the reduced or static equivalent separately. A DOM probe cannot see shader pixels, video frames, closed shadow content or native overlays: use host capabilities and mark the rest `UNKNOWN`. Enlarged crops diagnose; confirm at actual display size.

A reported artifact reopens the affected `KEEP` until a current detail and full-context check confirm the [repair](visual-reasoning.md#repair-as-an-experiment-then-remember-conditionally). A hash proves freshness, not absence of artifacts, and structural or injected-defect tests close only their declared contracts.

### Icon Backings and Nested Surfaces

Inspect the glyph and the visible surface behind it (circles, capsules, tiles, borders, rings, shadows, glows, ancestor backgrounds and `::before`/`::after`), not only classes named `pill` or the SVG file. For each role, establish what the backing communicates (an action or hit region, selected state, status, image mask, needed contrast, accepted identity or decoration) and verify it in the real UI; a noninteractive icon in a button-like tile is judged beside real controls, and identical decorative disks can dominate their labels.

Inspect the composition and an actual-size crop beside the label and neighboring control at the relevant widths and states; a contact sheet cannot close this. Fix a backing that violates a scoped correction. When its value is open, remove only the disputed surface on the same content, keeping meaning, alignment, targets and focus cues, and compare hierarchy, recognition and affordances; keep useful selected or removable chips, icon buttons, avatars and approved treatments. A shape or color swap does not resolve an unnecessary backing ([incident](failure-patterns.md#pills-replaced-with-square-buttons)). Record role, owner, verdict and evidence; no radius threshold, pill count or blanket rule decides it, an uninspected backing leaves icon acceptance incomplete, and a wrapper-only fix need not reopen the glyph.

### Typography Coherence

For an affected page or system, or a reported font inconsistency, inspect each real type role (display, repeated section and card headings, body, navigation, buttons, fields, prices and data, and applicable menu, dialog, error and chart text), including below-the-fold siblings and responsive and localized states; a bounded font fix inspects its owner and affected consumers only.

Compare against the accepted [role map](design-foundations.md#typography), recording `role/selector/state → intended stack and weight/style → computed request → rendered face → visible consequence → correction`. Check local overrides, imported component CSS, resets, `@font-face` files and weight or axis mappings, and required scripts and mixed-script labels for per-glyph fallback. `getComputedStyle().fontFamily` reports the requested stack, and a family token, successful font request, `document.fonts.ready` or `document.fonts.check` proves neither the rendered face nor glyph coverage; browser rendered-font inspection can show which face supplies the glyphs. A face name alone does not prove a wrong weight ([incident](failure-patterns.md#a-variable-font-reported-as-extralight)).

An unexplained family or style switch among equivalent labels, headings or controls is `REVISE`, blocking, as are fake or mismapped weights, default browser control fonts, missing-glyph boxes and disruptive fallback. A readability or task failure is `REJECT`, unavailable evidence `UNKNOWN`, and no rendering cause is named from a screenshot alone.

Judge the whole voice: headings, prose, controls and data should read as one hierarchy, not fragments of different templates. When a pairing is open, compare identical content against the accepted assignment and keep an extra family only where its contribution shows; keep useful display, text, mono and script-specific distinctions and user-specified references. Family count is not an acceptance criterion: the [pairing method](art-direction-gate.md#typographic-voice-and-font-pairing)'s two families plus a mono is a starting default, and counting CSS stack entries proves nothing. After repair, inspect native-size text in the page and its overlay and control states once fonts settle (line breaks, baselines, button dimensions, clipping, fit), report the roles, scripts and states verified, and judge transient loading fallback apart from the settled result.

### Density, Placement and Scroll

When sizing is new, revised or reported as oversized, apply the [density contract](design-foundations.md#density-before-dimensions). Measure in CSS pixels at the actual viewport, zoom and DPR, not screenshot pixels, across empty, sparse and populated states at a pressure width, accounting for header height, row height, cumulative padding and where the first useful content sits. When a tighter challenger on the same content serves the task better and the extra space shows no grouping, input, stability or identity benefit, the verdict is `REVISE`, blocking, whatever the viewport fit, centering or internal scrollbar; an approved spacious reference stays a conformance target, and geometry checks prove an authored contract, not the best density.

For placement, inspect the [layout contracts](design-foundations.md#placement-and-alignment): reference frame and axis, actual bounds, padding, visible mass, reading order and action proximity. Use measured geometry for an explicit contract and rendered comparison for an open composition; a numerically centered icon can look displaced, and box bounds establish geometry, not baseline or optical balance ([checked geometry](cli-reference.md#version-a-visual-system-contract)). In a mixed field row, compare the visible controls, not their caption wrappers ([incident](failure-patterns.md#a-field-caption-that-pushed-its-input-off-the-row-axis)).

For bounded lists, verify the panel keeps its height, the list really scrolls, and its header and actions stay reachable, with keyboard access, visible focus, long and empty content and the mobile transformation. Unintended document growth, unreachable actions, an inert scrollbar or a scroll trap blocks acceptance, while ordinary document lists get no arbitrary height limit. Record the actual [scroll owner](design-foundations.md#bounded-lists-and-scroll-ownership); page-level overflow checks cannot prove it.

### Repository, Content and Performance

- Run the repository's actual build, typecheck, lint, tests and static checks.
- Preserve framework, component, token, state, routing, data and asset ownership unless an accepted decision changes it.
- Use real or representative content early (prices, units, long titles, empty values, errors, legal copy, names, dates, locales, user-generated data), and separate factual claims from fictional, inferred and placeholder material.
- Check failure without JavaScript, media or animation where the platform needs a meaningful fallback.
- Reserve media space, match image format and density to the rendered role, and keep fonts, icons, scripts, animation, canvas and third-party dependencies proportional to value.
- Test loading and responsiveness on a constrained profile, clean up observers, listeners, timelines and media, and keep a usable result when nonessential assets, fonts, effects, analytics or animation fail. Unmeasured heavy decoration is not a design decision.

## Delivery Evidence

Report checks run, viewports and states inspected, assistive and input modes covered, important measurements, findings fixed, rerender evidence, unresolved `UNKNOWN`s and unavailable checks. Compilation alone is never visual QA.

## Review-Only and Audits

Use when the user asks to review, audit or critique an interface without asking for changes. The deliverable is a findings report, and the repository stays as it was.

- **No edits.** Do not change source, tokens, configuration, dependencies or the correction journal, and open no decision packet. Keep captures and measurement scripts outside the repository. When a fix is small, describe it in the finding and offer to apply it; do not apply it.
- **State the scope.** Name the routes or components, revision or URL, viewports, themes, states and input modes reviewed, and what was left out. Unreviewed surfaces are not passing.
- **Gather evidence with the acceptance methods.** Render at the [responsive widths](#responsive-transformation), exercise keyboard and screen-reader paths, measure contrast with `contrast.py`, read computed styles and geometry, and read source only to locate each finding's owner.

Give each finding one record:

```text
ID · severity · title
location: route / component / selector, viewport, state
evidence: screenshot or crop path, selector with computed value, or measurement
why it matters: who is affected and how
fix: the change at the owning file, token or component, with a target value
status: verified | suspected (and the check that would settle it)
```

| Severity | Meaning |
|---|---|
| Critical | Blocks a primary task, loses data, misleads about money, consent or safety, or shuts people out of the primary path through an accessibility failure |
| High | Degrades a primary task for many users, or fails WCAG AA on a frequent path |
| Medium | Friction, inconsistency, or an AA failure off the main path |
| Low | Polish: spacing, alignment, wording |

- **Order** findings by severity, then by reach. One cause is one finding: a shared token defect lists every location under a single record.
- **Verified is not suspected.** A verified finding was reproduced in the rendered product or measured. A finding inferred from source, seen once without confirmation, or needing a device, assistive technology or data you lacked is suspected: list it in its own section with the check that would confirm or dismiss it. It is `UNKNOWN`, never a pass or a failure.
- **Accessibility audits** name the conformance target (WCAG 2.2 AA unless stated), cite the success criterion on each finding, and measure against the [threshold table](#accessibility-and-interaction) rather than restating it. Say which checks were manual; automated tools cover only part of the criteria.
- **Report in this order**, in the user's language: scope and the top three issues; verified findings; suspected findings; strengths to preserve during fixes; what was not reviewed. A `KEEP | REVISE | REJECT | UNKNOWN` disposition may summarize the reviewed scope.

### Check

- `git status` shows no change made by the review.
- Every finding has location, evidence, why it matters, a fix and a status.
- Verified and suspected findings are separated and ordered by severity.
- Scope and unreviewed areas are stated.
