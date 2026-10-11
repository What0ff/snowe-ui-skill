# Quality Gates

For reusable visual proof, use the scoped [system map and observation contract](visual-system-and-observation.md). Inspect real paint owners, repeated consumers and overlays; require independently planned browser combinations and current dependency closure. Historical receipts remain history. For perceptual diagnosis and professionally explained image pairs, use [visual reasoning](visual-reasoning.md); a mechanically consistent map still needs a strong whole-screen judgment.

For menus, modals, drawers, selects, comboboxes, popovers and other secondary surfaces, use [overlays-and-selection.md](overlays-and-selection.md) when that owner is active. Inspect the whole open composition, portal/theme context, hierarchy, type, material, row rhythm, anchoring, close/action details and state distinctions. A polished trigger or technically reachable content cannot close acceptance of a raw or unrelated secondary surface.

## Detail and artifact acceptance

For every touched composition, inspect the whole screen, the actual-size affected owner with its neighbors, and diagnostic detail at high-risk joins. A thumbnail can establish mass and hierarchy while hiding a broken rim, extra highlight, clipped glyph or merged icon counter. A formal browser plan therefore includes bound detail crops as well as the whole composition; the review must explicitly assess all of them. Direct work needs only its local affected owner and dependencies, not a whole-product audit.

Sweep silhouettes, joints, corners, masks/crops, borders, baselines, small typography, image edges and material highlights. Trace unexplained paint to the actual owner: descendants, pseudo-elements, ancestors, portal/backdrop, SVG, shader/media or an independently transformed layer. Do not explain an isolated bright sliver away as “lighting” without verifying its surface attachment and continuity. Overlapping highlights, a floating cap, a seam at a mask boundary or a raw icon join are defects even if the geometry fits its bounding box.

For motion/3D/media, inspect start, peak, interruption, representative orientation and settled frames at native size; check that attached parts share the same spatial model. A static front view can conceal a bad side or a detached layer. Compare the reduced/static equivalent separately. Use enlarged crops for diagnosis, then confirm at the actual display size and current viewport/DPR. A reported artifact reopens the affected KEEP; its correction requires a current confirming detail and collateral full-context check.

Distinguish local geometry from projected measurement. `getBoundingClientRect()` includes ancestor transforms and gives an axis-aligned screen box; using that width to construct a rotated cylinder while its lid uses local CSS width makes the parts incompatible. Derive object geometry from local resolved dimensions and apply one coherent projection. The same distinction matters for SVG slots, canvas coordinates, pointer conversion and transformed overlays. Verify both the construction relation and actual painted contact; neither an attached DOM parent nor matching external boxes is enough.

Record the concrete observation and cause, the owner-level change, a comparable rerender and any adverse consequence. A source/PNG hash proves freshness, not absence of artifacts. Structural and injected-defect tests close only their declared construction/visibility contracts; unresolved visual ambiguity remains UNKNOWN or REVISE. For custom glyphs use [icon-craft.md](icon-craft.md), retaining clean geometry, optical placement and recognizable context rather than merely producing original SVG bytes.

Use this reference to prove that the accepted design works. Quality gates protect outcomes and system integrity; they do not prescribe a style or turn every project into the same checklist.

## Define Proof Before Polish

For a new or reworked page hierarchy, start with the [page map, copy and action inventory](page-hierarchy.md) before choosing containers. At acceptance, inspect the whole affected surface for role distinction, useful text and redundant operations. Required content must be visible/accessibly named and free of relevant clipping/occlusion; text existing in the DOM is not sufficient. Keep technical, evidence-integrity, visual and user-acceptance outcomes separate.

For each material decision, state what evidence could keep, revise, or reject it. Cover only applicable surfaces, but always include the primary outcome, truthful content, accessibility, responsive behavior, important states, and build/runtime integrity.

When a live selection or input determines an already-visible preview, quote, result or inspector, exercise the dependency-changing transition. The current output must update or visibly invalidate before it can contradict the new selection; verify retained inputs and recovery, dependent counts and state styling as applicable. Correct states viewed separately do not prove this transition. Preserve deliberately historical or accepted snapshots as clearly identified records rather than clearing them as if they were current drafts. Keep the check scoped to the affected dependency, including its relevant narrow/pressure contexts.

Use one record:

```text
KEEP | REVISE | REJECT | UNKNOWN
viewport / input / state | visible or measured evidence | consequence |
correction or acceptance reason | rerender / retest result
```

`UNKNOWN` is appropriate when a font file, claim, real asset, device behavior, assistive technology, analytics result, or stakeholder fact has not been verified. It is not a passing state.

Keep proof proportional to the calibrated change surface: Direct checks the affected invariant, Focused checks the affected decision and shared consumers, and Portfolio checks the required experience slices. The broader menus below apply only where they can change acceptance. Use the existing task record; a separate document is unnecessary for a bounded correction.

## Conformance to a Specified Design

When the task is to implement, reproduce, or accept a definite supplied design, the reference closes the visual choices it actually specifies. This is conformance work, not a new art-direction portfolio. A new codebase or many changed files does not reopen the supplied composition. General anti-pattern guidance must not remove its pills, square corners, cards, decorative treatment, or distinctive proportions. Redesign and stylistic adaptation require that scope in the user's request; fix implementation deviations autonomously within the already authorized target.

1. Inspect the actual target: designated Figma node/frame and its screenshot/properties/variants where accessible, or the supplied image/approved interface. Identify version, frame, dimensions, relevant state, crop and scale. A nearby library component, remembered reference, generic moodboard, or inaccessible link is not proof of the selected instance. If the source cannot be read, report that specific evidence gap and continue only work supported by available evidence; do not substitute an imagined reference.
2. Establish the smallest comparison contract: target region/state, layout relationships and dimensions, type metrics, gaps/padding, control size and corner shape, color/surface, asset/crop, and behavior explicitly specified. Mark measurements inferred from raster pixels as estimates; do not label them extracted Figma values. Resolve actual fonts/assets and component variants before measuring fidelity, because fallback fonts and default library styles can change geometry.
3. Implement those decisions in the repository architecture. Reuse primitives only when their rendered result matches; override or extend the appropriate owning variant when necessary. A default tall button, square reset, pill utility, stock icon, alternate font, or changed text is not an acceptable substitute merely because the library supplies it.
4. Compare reference and functioning implementation at matching CSS viewport, content, state and scale. Use side-by-side views or aligned overlays when available, then inspect target-size details. Prioritize layout/reading order and proportions, then typography/assets, then spacing, control geometry and optical detail. Pixel differences can locate drift but cannot decide whether antialiasing, rendering environment, or a genuine design deviation caused it.
5. Keep a compact deviation record: `target frame/region/state | specified or estimated value | rendered value/evidence | consequence | correction | confirming comparison`. Use tolerances supported by source precision and the rendering environment; never invent one global similarity score or pixel threshold that excuses material mismatches. Correct known material deviations and rerender before accepting the affected scope.

Unspecified responsive states and interactions remain distinct from the supplied target. Infer only the minimum coherent behavior needed for implementation, preserve known priorities and visual language, and label that extrapolation. Do not claim exact mobile fidelity from a desktop-only frame, and do not block acceptance of a proved desktop scope merely because mobile is unspecified. A missing font, inaccessible frame, or unverified behavior remains `UNKNOWN` for that claim.

If the reference conflicts with a required accessibility, platform, content, or functional constraint, identify the exact conflict. First seek a solution that preserves the visible design, such as correct semantics or a non-overlapping transparent hit region. If a visible departure is unavoidable, record it as an unresolved deviation and explain the smallest needed change; do not silently redraw the reference and call it faithful. The supplied design can be implemented faithfully while a separate accessibility or functional acceptance claim remains unresolved.

## Early Gate for a Visual System

Before repeating a new or materially revised visual system across pages, render its primary decision surface and one representative secondary or repeated context with real content. Inspect a full composition and actual-size controls/type at the widths that pressure this decision. This can be the Focused baseline/challenger or the Portfolio risky-slice prototype already in progress; do not duplicate it.

Establish the reading/task order, content grouping, typographic emphasis, and control hierarchy before spreading decorative treatments. Look for capsules around static eyebrows or metadata, equal-weight cards around unrelated content, nested surfaces, ornamental icons, and effects that compete with the offer or task. These are inspection triggers, not forbidden styles or numeric budgets.

When a treatment's value is unresolved, render a credible challenger on identical content, viewport, and state. Choose the move from the diagnosed cause: subtraction can reduce competing wrappers, while a weak focal hierarchy or visual proposition may need stronger grouping, type, material or graphics. Use [art-direction-gate.md](art-direction-gate.md) for the constructive choice. Preserve required content and hit targets. Compare attention, scan path, density, affordances and identity; retain the richer or quieter version when it visibly works better. A text-only argument, token swap, deliberately weakened challenger, or radius-only change cannot settle a compositional finding.

Check product specificity without demanding novelty: temporarily disregard the logo/name and ask which content relationships, composition, type, imagery, or behavior still follow this brief. A familiar layout can pass on task fit. A claimed distinctive identity needs visible support beyond interchangeable adjectives, badges, and effects. Do not force a signature motif onto a utility interface.

For visible section/card numbering, verify the [ordinal's content role](page-hierarchy.md#audit-user-facing-text) in the actual page, including CSS-generated counters. `01/02` can imply sequence, priority or progress among unordered peers and compete with the real headings. Revise unsupported automatic numbering at its shared owner; do not replace it mechanically with letters, Roman numerals or icons. When its value is genuinely open, inspect the same content without the disputed indices, preserving useful grouping and links. Keep verified process order, chapter/reference navigation and supplied identity treatments; no number count or blanket no-numbers rule proves quality. A reported material recurrence blocks affected visual KEEP until the current result is repaired and inspected.

## Acceptance Rules

### Explicit Visual Disposition

Record review method separately from `KEEP | REVISE | REJECT | UNKNOWN`. “Self-reviewed,” “screenshots inspected” and technical PASS describe evidence or process, not visual acceptance. Assess the intended attention/cue contract against the actual render for the material states, then identify the concrete owner, visible observation and user consequence for each material problem. Do not require a fixed number of defects or invent novelty to fail an approved quiet interface.

Use KEEP only when the inspected scope has no unresolved blocking visual finding. REVISE identifies a repairable weakness; REJECT rejects the current direction; UNKNOWN identifies missing judgment or evidence. A resolution needs an explained change and a current confirming render. User acceptance is a separate disposition; neither a self-review nor silence creates it.

For material visual-system work with a reusable report, use the [checked visual report](cli-reference.md#check-a-recorded-visual-verdict). Its checker validates the recorded disposition, scope coverage and evidence freshness. It cannot establish perceptual quality from prose, CSS metrics or a screenshot hash. Existing short Direct records can use the same method/verdict distinction inline; do not create a JSON report for every local property fix.

### Icon Backings and Nested Surfaces

During visual review of an affected composition or icon treatment, inspect both the glyph and the visible surface behind it. This includes circular and capsule backings, rounded-square tiles, borders, rings, shadows and glows; inspect ancestor backgrounds and `::before`/`::after` when needed to locate the paint owner. Do not restrict the search to classes named `pill` or to the SVG file.

For each materially different role in the affected scope, establish what the backing communicates: a real action/hit region, selected state, status, image mask, necessary contrast, accepted identity, or decoration. These are claims to verify in the actual UI, not automatic exemptions. A noninteractive feature icon inside a button-like tile must be evaluated alongside real controls. Several crisp glyphs in identical decorative disks can still dominate their labels or obscure the reading order.

Inspect the whole affected composition and an actual-size crop beside its label and neighboring control at the relevant narrow/pressure/wide widths and states. A glyph-only contact sheet cannot close this check. If the backing violates an explicit scoped correction, fix it. If its value remains open, use the existing same-content subtraction comparison: remove only the disputed painted surface, retain meaning, layout alignment, hit targets and focus cues, then compare hierarchy, recognition and affordances. Preserve useful selected/removable chips, icon buttons, avatars and user-approved treatments. A circle-to-square conversion, smaller radius, recoloring, or lower opacity does not by itself resolve an unnecessary backing.

Record the backing's role, owner, verdict and evidence in the existing finding record. Retain it when verified interaction, readability or identity supports it; revise an unsupported competing surface. No global radius threshold, pill count, or blanket removal rule can establish acceptance. If the glyph is clear but its backing is uninspected, icon-treatment acceptance remains incomplete.

For new or materially revised custom glyphs, also apply the [contextual icon acceptance claims](iconography-system.md#accept-the-context-not-the-drawing-sheet). A correct backing does not close semantic truth, small-size recognition, family fit or accessible host behavior. Routine wrapper-only fixes need not reopen glyph generation.

### Density and State Composition

When sizing/composition is new, materially revised, or reported as oversized, apply the [density contract](design-foundations.md#density-before-dimensions) before propagating the layout. Inspect actual CSS viewport, zoom/DPR and reference scale; screenshot pixels alone do not establish CSS dimensions. For the affected task, account for total header/summary height, repeated row height, cumulative padding and the location of the first useful content/action. Include empty, sparse and populated states at a pressure width and the relevant desktop/mobile contexts.

When density remains an open choice in repeated-use work, require a rendered tighter challenger when unexplained large rows, ceremonial headers, amplified placeholder values or oversized empty wells separate related information. Compare the same content and states, keeping readable text and usable targets. `REVISE` and block affected visual acceptance when the extra space has no demonstrated grouping, input, stability or identity benefit and the challenger supports the task better. A page fitting inside the viewport, centered correctly, or having an internal scrollbar cannot overrule this finding. A fixed dimension is acceptable when its role is justified; an explicitly approved spacious reference remains a conformance target.

Fix the cause at the owning layout: additive padding, min-height, stretching, typography role or state treatment. Do not use global zoom, a CSS scale transform, shrinking all fonts or arbitrary clipping. Recheck that long lists still scroll inside the intended region and that empty/short states do not receive the same unused height by accident. Automated geometry checks prove an authored density contract; they do not decide which density is aesthetically or functionally best.

### Typography Coherence

For an affected page/visual system or reported font inconsistency, inspect a representative set of each real type role: display heading, repeated section/card heading, body, navigation, button/field/select, price/data, and applicable menu/dialog/error/chart text. Include below-the-fold siblings and relevant responsive/localized states. A bounded font fix inspects its owner and affected consumers; it does not reopen all type choices across the product.

Compare the current implementation with the accepted role map. Record `role/selector/state → intended stack and weight/style → computed request → actual rendered face when inspectable → visible consequence → correction/rerender`. Check local overrides, imported component CSS, resets, font-face files and weight/axis mappings. Inspect required scripts and mixed-script labels for per-glyph fallback. A family token, successful font response, completed font loading promise or attractive isolated specimen does not prove the final text uses the intended face.

Treat an unexplained family/style switch among equivalent labels, headings or controls as `REVISE` that blocks affected visual acceptance. Also block unresolved fake/mismapped weights, unintended default browser control fonts, missing-glyph boxes, or mixed fallback that disrupts required text. Use `REJECT` when readability, content, task completion or accessibility fails; use `UNKNOWN` when the necessary render or font identity evidence is unavailable. Do not assert a specific rendering cause from a screenshot alone.

Judge the complete typographic voice: do headings, prose, controls and data read as one intentional hierarchy, or as fragments from different templates? A formally assigned role can still look incoherent. When a new pairing is unresolved, compare identical content and viewport against the accepted family assignment. Keep useful display/text/mono or script-specific distinctions and user-specified references. One-font-for-everything, a universal two-font maximum, and counting CSS stack entries are not acceptance criteria.

After repair, inspect actual text at native size in the current page and relevant overlay/control states. Recheck line breaks, baselines, button dimensions, clipping and responsive fit after fonts settle; a font change can cause layout regressions without page-level overflow. Report which roles, scripts and states were verified, and separate transient loading/fallback resilience from settled visual acceptance.

### Placement and Scroll Acceptance

For reported placement or scrolling issues, inspect the [layout contracts](design-foundations.md#placement-and-alignment) in the affected context. Identify the intended reference frame and alignment axis, then compare actual bounds, padding, visible mass, reading order and action proximity. An icon can be numerically centered but optically displaced; a correctly centered component can still be in the wrong part of the page. Use measured geometry for an explicit contract and rendered comparison for an open composition decision.

For a mixed field/filter/action row, inspect the whole row and native-size control detail after fonts settle. Compare visible control edges/centers and text placement separately from captions, help and error wrappers. In Figma inspect the actual frames, Auto Layout alignment and sizing where accessible; raster measurements remain estimates. In a browser measure the actual input/button owners. Verify relevant long-text and narrow/wrapped states and representative shared consumers. No page overflow does not prove peer alignment. A material unexplained shift blocks affected acceptance as REVISE until the responsible layout owner is fixed and rerendered. Preserve a supplied staggered design or justified different control heights; do not turn this check into a universal equal-height or centering rule.

For checked browser geometry, [visual-system-and-observation.md](visual-system-and-observation.md) schema 1.1 can compare an explicit owner axis with a justified CSS-pixel tolerance. Bounds establish geometry, not glyph baseline or optical balance; inspect those in the rendered result. Missing native source/renderer evidence leaves only that claim UNKNOWN and cannot be replaced by a claimed Auto Layout/CSS diagnosis from a screenshot.

For bounded lists, verify the panel remains within its intended height, the list actually has scrollable overflow, and header/actions stay reachable. Test keyboard access, focus visibility, long content, empty state and relevant mobile transformation. Unintended document growth, unreachable actions, an inert scrollbar or a focus/scroll trap blocks acceptance. Ordinary document-flow lists must not acquire arbitrary height limits just to pass this check. Record the actual scroll owner and affected state; page-level overflow checks cannot prove this contract.

### Dispositions

Visual readiness has a positive bar as well as defect checks: the whole affected screen must read as an intentional, resolved experience with coherent hierarchy, rhythm, type/graphic relationships and the character requested by the brief. Technical correctness and a quieter layout cannot establish that bar. Treat an unfinished or interchangeable proposal as `REVISE` when the task calls for an authored visual direction; reopen the affected decision rather than appending arbitrary color, shadows or decorative assets. Preserve deliberately restrained approved references. Engineering fixtures may pass their technical contract while retaining a separate visual `REVISE` disposition.

Judge the implementation, not the author's explanation. Review the artifact and brief before reading its design rationale when feasible. For a specified target, distinguish implementation drift from an issue already present in the source design: a faithfully reproduced trait can pass conformance while a separate usability/accessibility finding remains open. That finding does not authorize silently changing the reference. Use these dispositions for the affected scope and name which acceptance claim they address:

| Finding | Disposition and required action |
| --- | --- |
| Truth, primary task, accessibility, or required responsive/state behavior fails | `REJECT`; repair the failure. Visual appeal cannot compensate. |
| Passive labels/status and controls appear interchangeable, or decorative emphasis obscures the next action or content relationships | `REJECT`; restore semantic and attention hierarchy, then render the affected contexts again. A pill count or CSS radius is not the evidence. |
| Repeated cards, badges, effects, or hero/section patterns flatten meaningful content differences, contradict the selected thesis, or lose to a credible subtraction challenger without a compensating task/identity benefit | `REVISE` and block visual acceptance; change the grouping/composition or treatment, then compare again. Renaming the style does not resolve the finding. |
| Local type, crop, spacing, alignment, control size/corner shape, or optical defect | `REVISE`; fix and rerender if it materially affects readability, hierarchy, fit, or the requested fidelity. An oversized or inappropriately squared button cannot pass merely because it is clickable. A small cosmetic preference can remain only with an explicit scoped acceptance reason. |
| A material explicit user correction recurs, or a glyph is polished while its unsupported backing still competes with labels/actions | `REVISE` and block acceptance of the affected scope; repair the responsible owner and inspect the current result. Required functionality/semantics failures still take `REJECT`. |
| Equivalent text roles drift between families/styles, or intended typography is undermined by unverified font files, weights or glyph fallback | `REVISE` and block affected typography acceptance; apply the typography coherence check and verify the settled rendered result. Missing required evidence stays `UNKNOWN`. |
| Required render, interaction, content, or comparison evidence is absent, stale, or inaccessible | `UNKNOWN` for that claim; do not label it passed or replace it with source inspection. |
| Applicable proof supports the task, visual hierarchy, role coherence, and requested identity; no blocking findings remain | `KEEP` for the inspected scope, with concrete evidence. Do not extrapolate to uninspected routes or states. |

For visual acceptance, identify the actual route/component, viewport/state, and inspected capture or live-render evidence. Verify the browser's actual layout viewport; an image's pixel width or a launch flag alone can describe a cropped wider layout. Bind findings to the current implementation (revision or a clear before/after artifact identity). Record what visibly failed, its consequence, what changed, and the confirming rerender. Screenshots that were produced but never inspected are not review evidence. A build, source scan, or aggregate score cannot overrule a blocking visual finding; a polished screenshot cannot certify keyboard or recovery behavior.

If required proof cannot be obtained, finish the verifiable implementation work and report exactly which acceptance claims remain `UNKNOWN`. Do not invent a pass, force a user approval step, or loop through unrelated changes. No arbitrary minimum iteration count is required when the first inspected result already meets the evidence-based bar.

## Repository and Content Integrity

- Run the repository's actual build, typecheck, lint, tests, and format/static checks that exist.
- Preserve framework, component, token, state, routing, data, and asset ownership unless a justified accepted decision changes them.
- Use real or representative content early: products, prices, units, labels, long titles, empty values, errors, legal copy, names, dates, locales, and user-generated data.
- Distinguish factual claims from fictional benchmark content, inference, and placeholder material.
- Check failure without JavaScript/media/animation when the platform requires a meaningful fallback.

## Accessibility and Interaction

Verify the implemented result, not the intent:

- semantic elements or correct native equivalents;
- accessible names, descriptions, roles, states, relationships, and announcements;
- for icon controls, an intentional [label mode](iconography-system.md#choose-the-control-label-mode): avoid automatic icon-plus-caption duplication, preserve necessary visible wording, and check the accessible name/state, hover/focus tooltip, dismissal, touch usability and clipping;
- keyboard access, logical focus order, visible focus, focus restoration, escape/cancel, and no traps outside intentional modal behavior;
- target behavior and spacing suitable for the input/context;
- text, icons, controls, statuses, charts, and focus indicators with sufficient rendered contrast for their roles;
- meaning not dependent on color, hover, image, gesture, sound, or animation alone;
- labels and errors that explain recovery, preserve entered data where safe, and associate with the right control;
- zoom, text scaling, reflow, orientation, high contrast/forced colors, themes, reduced motion, and relevant assistive technologies;
- captions, transcripts, alt text, or intentionally empty alternatives according to media purpose.

Automated audits can find structural failures but cannot prove reading order, clarity, useful alternative text, focus behavior, or task completion. Manually exercise the primary path and recovery.

For solid color pairs, use deterministic contrast calculation. For gradients, imagery, transparency, overlays, filters, video, and state changes, measure representative rendered points and test variation; a token-level pass is insufficient.

## Responsive Transformation

Choose widths from content and composition pressure, not device labels alone. Inspect at least:

- a narrow width;
- a pressure/intermediate width where layout, navigation, comparison, imagery, or controls are most likely to fail;
- a wide width;
- relevant orientation, zoom/text scaling, and container contexts.

At each, verify priority and task/reading order, navigation, disclosure, comparison, form labels/errors, sticky behavior, overlays, virtual keyboards, long content, media crop, table/data alternatives, focus visibility, targets, and overflow. Page-level horizontal scrolling is a defect unless the product deliberately provides a spatial canvas; contained data regions still need understandable keyboard and touch behavior.

Responsive design may reorder, change navigation or control form, alter disclosure, simplify a graphic, replace a side panel with an overlay, or move conversion support closer to the decision. It must not merely shrink the wide composition or hide required content.

## State and Content Resilience

Test the states that can materially change understanding or completion:

- default, hover, pressed, focus-visible, selected, disabled;
- loading, progressive/partial, empty, no result, error, success;
- validation, destructive confirmation, undo/recovery, offline/retry;
- signed-out/permission-limited/expired states;
- long, translated, bidirectional, missing, user-authored, and extreme-but-valid content;
- open menus/dialogs/drawers, interrupted motion, and rapid repeated input.

Do not fabricate every state for every element. Trace the actual lifecycle and high-risk failures. Empty and error states must preserve context and offer the next useful action.

## Visual and Brand Critique

Review the rendered whole before isolated components:

- Is the attention order aligned with the user decision or task?
- Does composition remain intentional between showcase widths?
- Are alignment, rhythm, density, type measure, and whitespace carrying hierarchy before decoration?
- Does typography fit its actual column without unintended mid-word breaks, clipping, or collision? Zero horizontal overflow can hide emergency wrapping and undersized content columns. Fix the measure, type scale or composition rather than treating `overflow-wrap` as visual acceptance.
- Is the opening's height and emphasis proportionate to the visitor's task and frequency? In a returning-user task surface, inspect how far branding or introductory copy displaces the first useful choice, particularly on narrow screens; preserve character without burying the task.
- Does real content expose false symmetry, repetitive cards, weak grouping, or a generic page pattern?
- Are type, color/material, shape, imagery/graphics, icons, and motion one thesis with explainable role boundaries?
- Does actual color intensity match the intended role and user/brand direction? Check fill versus foreground and on-color text separately, including compositing and interactive states. If an open accent choice repeatedly collapses to pale tints, use the same-content intensity comparison in [design-foundations.md](design-foundations.md#color-and-material); neutrality or maximum saturation alone does not prove quality.
- Is the whole palette resolved in tables, dialogs, fields and supporting surfaces as well as primary actions, and does it belong to this product? Inspect an open overlay and repeated data region beside the page. Neither unexplained default grays nor a mechanically tinted full-page skin closes that decision; name the contextual rationale and whether large color areas help or overpower the work.
- Was the palette selected from a product-specific direction before implementation and then challenged in the render, or merely rationalized after painting? An unresolved comparison or readable but contextually weak palette is not a finished color result to hand to the user.
- Is the identity carrier distinctive, useful, and repeated with restraint?
- Do imagery and custom assets remain truthful, well cropped, optically balanced, and coherent at actual size?
- Are controls recognizable and important actions proportionate rather than theatrically oversized?
- Do button height, padding, text/icon scale, corner shape and alignment match the supplied target or their established control family? Does the actual visible box remain proportionate beside nearby fields and secondary actions, independently of its hit region?
- Can effects or containers be removed with no loss of meaning or identity?

Compare the strongest rendered challenger when a finding implicates the accepted premise. Reopen architecture or art direction rather than polishing around a structural mistake.

## Performance and Robustness

- Reserve media space and avoid unintended layout shifts.
- Match image format, dimensions, density, and responsive delivery to the rendered role.
- Keep fonts, icon delivery, scripts, animation, canvas/WebGL, and third-party dependencies proportional to value.
- Test loading sequence and interaction responsiveness on a constrained profile appropriate to the product.
- Avoid unnecessary main-thread/layout work and clean up observers, listeners, timelines, and media.
- Preserve a usable result when nonessential assets, fonts, effects, analytics, or animation fail.

Performance budgets are contextual, but unmeasured heavy decoration is not a design decision.

## Rendered Review Loop

1. Capture the affected state for Direct, the affected comparison and shared contexts for Focused, or the required complete surfaces for Portfolio. Include narrow, pressure, and wide widths when responsive composition or a visual system is under review; a bounded state correction does not automatically require a whole-page tour.
2. Exercise the affected task/keyboard path and applicable open, selected, error, loading, and reduced-motion states. Do not fabricate unrelated states to fill a checklist.
3. Review the hierarchy and crop of the affected context, then component detail and optical alignment. Inspect the whole page when its composition is the active decision.
   Include the icon-backing check for affected icons/surfaces and reconcile applicable user corrections with the current result. Inspect representative shared variants, including below-the-fold instances when the treatment is repeated there; a polished first screen does not prove the family.
   Apply typography coherence to affected text roles and their actual rendered fonts, including controls and overlays. Review the page's combined typographic voice as well as individual text metrics.
4. Record findings with direct evidence and consequence. Avoid vague taste notes.
5. Correct every `REJECT` and material `REVISE` in causal order: truth/architecture, task/interaction, responsive/accessibility, art direction, then polish.
6. Rerender the affected evidence. Run another complete pass only after a material compositional change or unresolved major failure.
7. Apply the acceptance rules to the current evidence. Stop when no blocking findings remain and further changes no longer improve a stated driver; if required evidence is unavailable, stop with those claims explicitly `UNKNOWN`.

Pixel difference proves change, not improvement. A screenshot cannot prove keyboard, motion, loading, or assistive behavior; a passing test cannot prove hierarchy, crop, or optical quality.

## Delivery Evidence

Report checks run, viewports and states inspected, assistive/input modes covered, important measurements, findings fixed, rerender evidence, unresolved `UNKNOWN`s, and unavailable checks. Never report compilation alone as visual QA.
