# Goodturn Cycles — Rendered QA

This record evaluates the rendered benchmark with `KEEP | REVISE | REJECT | UNKNOWN`; it does not turn taste into a numeric score.

## Coverage

- **Wide:** 1440 × 1000 viewport.
- **Pressure:** 900 × 1000 viewport, after primary navigation converts to the menu model.
- **Narrow:** 390 × 844 viewport, including the stacked range and full-width product sheet.
- **States:** menu open/close, product-use filter, empty finder error, all three finder steps, recommendation, product details, size error and selection, reservation toast, cart, two-bike compare, booking form, closed-day constraint, and booking success.
- **Inspection:** image/font loading, horizontal overflow, console errors/warnings, dialog/focus behavior, control labels, duplicate IDs, dialog labelling, image `alt`, broken assets, custom icons in their service context, and key target sizes.

## Pass 1 findings

| Status | Finding | Consequence |
| --- | --- | --- |
| KEEP | The complete three-bike field, prices, fit evidence, and peer test-ride/reservation paths remain understandable without using the finder. | The architecture solves novice uncertainty without hiding the commercial offer. |
| KEEP | Wide, pressure, and narrow views use different compositions while retaining product, price, fit, ownership, and conversion evidence. | Responsive behavior is transformation rather than desktop shrinkage. |
| KEEP | Generated bicycle imagery remains in-scale and composition-specific; the no-image alternative was materially weaker for form and fit context. | Imagery earns its cost and is disclosed as fictional/generated. |
| KEEP | Motion is limited to state continuity: filter change, menu/dialog origin, comparison rail, and toast. | Product inspection stays calm; the static experience remains complete. |
| KEEP | The four custom service symbols are recognizable and coherent beside visible labels at their rendered 32 px size. | Custom graphics add a specific measurement/workshop language without making routine controls novel. |
| REVISE | At narrow widths the visible `Menu` text was removed with CSS, which also removed the button's accessible name. | A screen-reader user could reach an unnamed control. |
| REVISE | Finder recommendation and booking success changed content but focus remained on a newly hidden control. | Keyboard and screen-reader continuity did not match visual continuity. |
| REVISE | Header cart/menu targets were 42 px and the horizontal filter scrollbar used the heavy browser default. | The most repeated mobile controls and filtering surface felt less deliberate than the rest of the system. |

## Corrections

- Added a persistent `aria-label` that changes between `Open menu` and `Close menu`.
- Moved focus to a programmatically focusable recommendation heading and booking-success heading after state replacement.
- Increased mobile cart and menu controls to 44 × 44 px.
- Added a restrained 3 px scrollbar treatment while retaining visible horizontal-scroll affordance.
- Re-rendered every affected width/state after the corrections. Early captures with a stale viewport compositor were rejected and replaced from fresh browser contexts.

## Pass 2 evidence

- Wide, pressure, and narrow documents reported no horizontal page overflow.
- Mobile menu exposed the expected accessible name, focused its first link on open, and measured 44 × 44 px for both menu and cart controls.
- Finder focus moved to `H3[tabindex="-1"]`; booking confirmation focus moved to `H2[tabindex="-1"]`.
- The DOM audit found zero duplicate IDs, unlabelled visible form controls, missing image `alt` attributes, broken images, or invalid dialog label references.
- Final browser console audit reported zero errors or warnings.
- Fonts and all four 1536 px source images loaded successfully. Structural/provenance SVG validation is also covered by the repository test suite.

## Final captures

| Evidence | File |
| --- | --- |
| Wide offer | `screenshots/desktop-home.jpg` |
| Wide product field | `screenshots/desktop-products.jpg` |
| Comparison state | `screenshots/desktop-compare.jpg` |
| Guided choice | `screenshots/desktop-finder.jpg` |
| Workshop/custom-icon context | `screenshots/desktop-workshop.jpg` |
| Pressure width | `screenshots/intermediate-home.jpg` |
| Narrow offer | `screenshots/mobile-home.jpg` |
| Narrow navigation state | `screenshots/mobile-menu.jpg` |
| Narrow product sheet | `screenshots/mobile-product-sheet.jpg` |

## Remaining limits

- Goodturn and every commercial fact are fictional; this proves design behavior and frontend coherence, not market demand or a live inventory/payment integration.
- Generated mechanical imagery was inspected in layout and at source resolution, but it is not evidence for a real bicycle specification.
- Reduced-motion behavior is implemented as a CSS media branch and all core state changes remain immediate without animation. This run did not emulate the operating-system preference in the in-app browser.
- Rendered review is still human judgment. Automated tests defend evidence, structure, and UX contracts; they do not certify taste.
