# Quality Gates

Use this reference for UI review, accessibility checks, interaction validation, and pre-delivery QA.

## Contents

1. Standards baseline
2. Evaluation discipline
3. Accessibility facts
4. Interaction targets
5. State coverage
6. Responsive and theme QA
7. Typography and localization QA
8. Content and forms
9. Motion and performance
10. Bounded rendered critic
11. Delivery evidence

## 1. Standards baseline

Verified against official sources on 2026-07-21:

- [WCAG 2.2 Recommendation](https://www.w3.org/TR/WCAG22/)
- [WCAG 2.2 Understanding documents](https://www.w3.org/WAI/WCAG22/Understanding/)
- [Apple UI Design Dos and Don’ts](https://developer.apple.com/design/tips/)
- [Apple Human Interface Guidelines: Buttons](https://developer.apple.com/design/human-interface-guidelines/buttons)
- [Android accessibility foundations](https://developer.android.com/design/ui/mobile/guides/foundations/accessibility)
- [Android Material components](https://developer.android.com/develop/ui/compose/components)
- [Android chip guidance](https://developer.android.com/develop/ui/compose/quick-guides/content/create-chip)

Apply the standard relevant to the target platform. Product, legal, procurement, or organizational requirements may be stricter.

## 2. Evaluation discipline

Classify every check before assigning severity:

- **Invariant:** semantics, accessibility, content integrity, explicit requirements, verified brand rules, destructive-action safety, or a platform behavior the product depends on. A violated invariant can block delivery.
- **Contextual default:** a preferred starting direction such as restrained rounding, compact controls, a solid foundation, or primary-source icon use. Depart when platform, brand, content, task, or measured usability evidence is stronger.
- **Heuristic or diagnostic signal:** package count, class name, exact pixel value, number of cards or fonts, presence of a cool hue, gradient, shadow, `rounded-full`, or screenshot pixel delta. Investigate the rendered effect; do not fail on the signal alone.

Examples:

| Weak proxy check | Outcome-based check |
|------------------|---------------------|
| “Fail whenever more than one icon source is installed” | Sources have documented roles and icons used together share compatible geometry, behavior, and optical weight |
| “No `rounded-full` anywhere” | Full rounding belongs to a semantic, native, brand, or genuinely circular role and is not repeated as generic decoration |
| “No blue or gradients” | Color treatment supports the brief and hierarchy without generic ambient AI glow or contrast loss |
| “Every desktop control is 32–36px” | Visible geometry fits density and content while the applicable interaction target remains usable and non-overlapping |
| “At most two fonts/cards/actions” | Every additional family, surface, or peer action has a clear role and the resulting hierarchy remains coherent |
| “Screenshot differs from baseline” | The difference is explained, intended, and free of hierarchy, clipping, responsive, state, or interaction regression |

Use static scans to locate risk quickly. Confirm severity from the repository context, rendered interface, interaction behavior, and applicable standards.

## 3. Accessibility facts

For WCAG 2.2:

- Normal text needs at least 4.5:1 contrast for Level AA.
- Large text needs at least 3:1 contrast for Level AA.
- Meaningful non-text UI components and graphical objects generally need 3:1 contrast against adjacent colors under Success Criterion 1.4.11.
- Information must not rely on color alone.
- Keyboard focus must be visible for Level AA.
- Focused components must not be entirely hidden by author-created content under Success Criterion 2.4.11.
- The specific two-CSS-pixel-perimeter and 3:1 focus appearance requirement is Success Criterion 2.4.13 at Level AAA, not AA.
- Content must reflow without loss of information or functionality at the WCAG-defined narrow equivalent under Success Criterion 1.4.10, subject to its exceptions.
- Text must support resizing up to 200% without loss of content or functionality under Success Criterion 1.4.4, subject to its exceptions.
- Dragging functionality needs a single-pointer alternative under Success Criterion 2.5.7 unless dragging is essential.
- Target Size (Minimum), Success Criterion 2.5.8 at Level AA, uses 24 by 24 CSS pixels with documented spacing and other exceptions.
- Target Size (Enhanced), Success Criterion 2.5.5 at Level AAA, uses 44 by 44 CSS pixels with documented exceptions.

Do not label an interface “WCAG compliant” from a palette or static screenshot alone. Conformance depends on content, semantics, interaction, focus behavior, errors, media, and the complete user flow.

## 4. Interaction targets

- Apple’s design tips specify controls of at least 44 by 44 points for accurate finger tapping.
- Android accessibility guidance recommends touch targets of at least 48 by 48 dp.
- A visible icon can be smaller than its hit target. Add transparent padding or platform hit slop instead of a large decorative background.
- For web Level AA, use the WCAG 2.2 target-size rule and exceptions correctly; aim larger for primary touch interactions.
- Keep adjacent targets sufficiently separated to reduce accidental activation.
- Do not hide essential actions behind hover, swipe, drag, long-press, or context menus without an accessible alternative.

The hit target is an interaction requirement, not a justification for putting a pill behind an icon. Prefer transparent target expansion. Add a visible square, rounded, or circular surface when state, grouping, native behavior, brand language, or the control's real role calls for it—not merely to expose the target area.

## 5. State coverage

Validate every applicable state:

| State | Required checks |
|-------|-----------------|
| Default | Label, hierarchy, semantics, contrast |
| Hover | Pointer-only enhancement; no hidden essential action |
| Pressed | Immediate feedback without layout shift |
| Focus-visible | Clear indicator, correct order, not obscured |
| Selected/current | More than color alone when ambiguity remains |
| Disabled | Semantic disabled state and sufficient distinction |
| Loading | Progress feedback, stable geometry, repeated action prevented |
| Empty | Explain the state and provide the next useful action |
| Error | State the problem and recovery path near the source |
| Success | Confirm completion without blocking the next task |
| Offline/timeout | Preserve user work and offer retry or fallback |

Test state combinations such as selected + focus, disabled + loading, validation error + dark mode, and long text + narrow width.

## 6. Responsive and theme QA

- Inspect the rendered interface at narrow, intermediate, and wide widths.
- Include at least one width between named design breakpoints.
- Test portrait and landscape when the target platform supports both.
- Verify zoom or system text scaling, not only viewport resizing.
- Check long localized strings, large numbers, and user-generated content.
- Ensure fixed UI does not obscure content or keyboard focus.
- Ensure dialogs and sheets fit short screens and remain dismissible.
- Test light and dark themes independently.
- Test high-contrast or forced-colors behavior where the platform supports it.
- Do not remove browser zoom or override platform accessibility settings.

## 7. Typography and localization QA

- Verify the actual licensed font files or installed dependency, required weights or variable axes, subsets, loading strategy, and supported glyphs. A retrieved font name is a proposal, not evidence.
- Render representative content in every required script and locale, including realistic expansion, punctuation, diacritics, mixed case, and missing-glyph conditions.
- For right-to-left or bidirectional interfaces, verify logical spacing, mirrored directional controls, mixed-script values, numerals, punctuation, reading order, focus order, and truncation in the real platform.
- Verify fallback behavior with font loading disabled or delayed. Compare x-height, character width, weight, baseline, wrapping, hierarchy, and layout shift.
- For data-heavy interfaces, verify tabular figures, decimals, currencies, percentages, signs, dates, times, identifiers, and large-value overflow.
- Inspect compact, intermediate, and wide widths plus zoom or system text scaling. Reject clipping, illegible density, unstable baselines, and hierarchy that depends on one ideal string length.
- Judge additional font families by role, script coverage, metrics, performance, and fallback behavior—not by a fixed count.

Record the tested content, scripts, files or dependency, weights, fallback, viewports, and result. Keep the status `UNKNOWN` when required font or rendered evidence is unavailable.

## 8. Content and forms

- Use persistent visible labels for inputs. Placeholder text is supplemental.
- Associate errors with their fields programmatically and visually.
- Move focus to an error summary or first invalid field only when it improves recovery and does not surprise the user.
- Preserve entered data after validation, network errors, or navigation back.
- Use semantic input types and autocomplete tokens where appropriate.
- Explain required formats before submission.
- Confirm destructive or irreversible actions, or provide a reliable undo path when appropriate.
- Keep destructive actions spatially and visually separate from routine actions.
- Do not use a toast as the only channel for critical or persistent information.
- Use plain, specific language that states what happened and what the user can do next.

## 9. Motion and performance

- Give input feedback promptly.
- Use motion to explain state change, continuity, hierarchy, or progress.
- Keep animations interruptible and avoid blocking input while they run.
- Prefer transform and opacity when they preserve layout stability.
- Reserve layout space for asynchronous content and media.
- Respect reduced-motion preferences and verify the reduced experience directly.
- Avoid infinite decorative motion near reading, forms, and dense data.
- Lazy-load below-the-fold media and heavy features when appropriate, but do not defer content needed for the current task.
- Measure actual runtime behavior. Do not claim performance from framework choice or static code inspection alone.

## 10. Bounded rendered critic

1. Render the real, functionally correct interface with representative content before visual polishing.
2. Compare it with the selected design thesis and implementation contract; for refinement work, capture the previous interface at identical content, state, viewport, and theme.
3. Capture compact, intermediate, and wide sizes plus applicable interaction, content, theme, zoom or text-scaling, high-contrast, and reduced-motion states.
4. Run one full critic pass across composition, typography, density, and noise or identity. Inspect focal order at thumbnail size and alignment, spacing, type and fallback metrics, wrapping, icon optical balance, control geometry, hit areas, and surface nesting at full size.
5. Search for repeated decorative pills, unnecessary icon containers, uncontrolled icon-source mixing, vague stock metaphors, card soup, arbitrary shadows, unrequested blue/cyan/violet luminous identity, decorative gradients, overused motifs, and generic template composition. Treat tokens, counts, hue names, and package inventory as clues; confirm harm in the render.
6. Record each visible issue as `severity | viewport/state | evidence | task or system consequence | correction | verification`.
7. Classify a requirement, accessibility, content, or task failure as `BLOCKER`; clear hierarchy, coherence, responsive, or identity harm as `MAJOR`; local polish as `MINOR`; and missing evidence as `UNKNOWN`.
8. Apply the smallest coherent correction set for blockers and majors, then rerender the same evidence set and verify the recorded issues.

Use browser screenshots or platform previews when available. Code review alone cannot verify perceived hierarchy, clipping, overlap, contrast after compositing, or interaction feel. A screenshot pixel delta can locate change but cannot determine design quality.

Run another full critic pass only when a correction materially changes composition or a blocker or major remains. Otherwise stop after targeted verification and disclose untested evidence. Every change must answer a recorded finding; avoid tweak roulette and endless screenshot churn.

## 11. Delivery evidence

Report what was actually verified:

- Tested viewport or device sizes
- Themes and accessibility modes tested
- Interaction states exercised
- Automated checks run
- Contrast pairs measured
- Remaining limitations or untested platform behavior
- Rendered-critic findings corrected and the matching rerender evidence
- Typography files or dependencies, required scripts, fallback path, and stress content tested
- Newly acquired icon sources: official package and installed version, license/provenance, package-manager and lockfile update, assigned role, build/bundle result, rendered compatibility, and rollback of rejected candidates
- Confirmed project-memory decisions preserved or updated, including scope and evidence
- Material-decision exploration ledger: declared relevant universe, authoritative sources searched, external challengers, same-context finalist renders, quality-first ranking, strongest rejected option, and only then integration-cost evidence

Do not report checks that were inferred but not run. Distinguish automated validation, code inspection, and visual/manual testing.
