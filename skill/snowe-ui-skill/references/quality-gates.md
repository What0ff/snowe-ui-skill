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
- Does real content expose false symmetry, repetitive cards, weak grouping, or a generic page pattern?
- Are type, color/material, shape, imagery/graphics, icons, and motion one thesis with explainable role boundaries?
- Is the identity carrier distinctive, useful, and repeated with restraint?
- Do imagery and custom assets remain truthful, well cropped, optically balanced, and coherent at actual size?
- Are controls recognizable and important actions proportionate rather than theatrically oversized?
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

1. Capture the complete key surface at narrow, pressure, and wide widths.
2. Exercise primary conversion/task, keyboard path, open/selected/error/loading states, and reduced motion.
3. Review whole-page hierarchy and crop, then component detail and optical alignment.
4. Record findings with direct evidence and consequence. Avoid vague taste notes.
5. Correct every `REJECT` and material `REVISE` in causal order: truth/architecture, task/interaction, responsive/accessibility, art direction, then polish.
6. Rerender the affected evidence. Run another complete pass only after a material compositional change or unresolved major failure.
7. Stop when remaining changes no longer improve a stated driver, not when the first render looks acceptable.

Pixel difference proves change, not improvement. A screenshot cannot prove keyboard, motion, loading, or assistive behavior; a passing test cannot prove hierarchy, crop, or optical quality.

## Delivery Evidence

Report checks run, viewports and states inspected, assistive/input modes covered, important measurements, findings fixed, rerender evidence, unresolved `UNKNOWN`s, and unavailable checks. Never report compilation alone as visual QA.
