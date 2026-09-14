# Quality Gates

Use this reference to prove that the accepted design works. Quality gates protect outcomes and system integrity; they do not prescribe a style or turn every project into the same checklist.

## Define Proof Before Polish

For each material decision, state what evidence could keep, revise, or reject it. Cover only applicable surfaces, but always include the primary outcome, truthful content, accessibility, responsive behavior, important states, and build/runtime integrity.

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

When a treatment's value is unresolved, render a subtraction challenger on identical content, viewport, and state. Remove the disputed wrappers/effects while preserving required labels, state cues, grouping, and hit targets; rebalance type, spacing, and alignment so the challenger is credible. Compare the attention order, scan path, density, affordances, and product identity. Retain the richer version when it visibly wins. A text-only argument, token swap, deliberately weakened challenger, or radius-only change cannot settle a compositional finding.

Check product specificity without demanding novelty: temporarily disregard the logo/name and ask which content relationships, composition, type, imagery, or behavior still follow this brief. A familiar layout can pass on task fit. A claimed distinctive identity needs visible support beyond interchangeable adjectives, badges, and effects. Do not force a signature motif onto a utility interface.

## Acceptance Rules

Judge the implementation, not the author's explanation. Review the artifact and brief before reading its design rationale when feasible. For a specified target, distinguish implementation drift from an issue already present in the source design: a faithfully reproduced trait can pass conformance while a separate usability/accessibility finding remains open. That finding does not authorize silently changing the reference. Use these dispositions for the affected scope and name which acceptance claim they address:

| Finding | Disposition and required action |
| --- | --- |
| Truth, primary task, accessibility, or required responsive/state behavior fails | `REJECT`; repair the failure. Visual appeal cannot compensate. |
| Passive labels/status and controls appear interchangeable, or decorative emphasis obscures the next action or content relationships | `REJECT`; restore semantic and attention hierarchy, then render the affected contexts again. A pill count or CSS radius is not the evidence. |
| Repeated cards, badges, effects, or hero/section patterns flatten meaningful content differences, contradict the selected thesis, or lose to a credible subtraction challenger without a compensating task/identity benefit | `REVISE` and block visual acceptance; change the grouping/composition or treatment, then compare again. Renaming the style does not resolve the finding. |
| Local type, crop, spacing, alignment, control size/corner shape, or optical defect | `REVISE`; fix and rerender if it materially affects readability, hierarchy, fit, or the requested fidelity. An oversized or inappropriately squared button cannot pass merely because it is clickable. A small cosmetic preference can remain only with an explicit scoped acceptance reason. |
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
4. Record findings with direct evidence and consequence. Avoid vague taste notes.
5. Correct every `REJECT` and material `REVISE` in causal order: truth/architecture, task/interaction, responsive/accessibility, art direction, then polish.
6. Rerender the affected evidence. Run another complete pass only after a material compositional change or unresolved major failure.
7. Apply the acceptance rules to the current evidence. Stop when no blocking findings remain and further changes no longer improve a stated driver; if required evidence is unavailable, stop with those claims explicitly `UNKNOWN`.

Pixel difference proves change, not improvement. A screenshot cannot prove keyboard, motion, loading, or assistive behavior; a passing test cannot prove hierarchy, crop, or optical quality.

## Delivery Evidence

Report checks run, viewports and states inspected, assistive/input modes covered, important measurements, findings fixed, rerender evidence, unresolved `UNKNOWN`s, and unavailable checks. Never report compilation alone as visual QA.
