# Doppler Soda — Rendered QA

Status: passed on 2026-08-11 after correction and rerender.

The final implementation was served from the repository root over loopback and inspected in a real Chromium browser at 1440 × 1000, 900 × 1000, and 390 × 844. The dependency-free Chrome/CDP smoke repeated wide, intermediate, narrow, interactive, keyboard, navigation, conversion, and emulated reduced-motion checks. Screenshots were regenerated only after the material findings below were corrected.

## Acceptance evidence

| Surface / state | Executed evidence | Result |
| --- | --- | --- |
| 1440 × 1000 opening | Normal-motion entrance and settle; product/category/flavor/CTA hierarchy; 48-segment cylinder; wide hero and full-page capture | Passed; can, category, three-flavor system, and pack path are readable in the first composition |
| 1440 × 1000 Pink Noise | Named flavor activation, synchronized selector states, live label/copy, full product revolution, final front-facing package | Passed; final yaw is divisible by 360 degrees and the Pink Noise face is legible |
| 900 × 1000 pressure width | Intermediate composition, 40-segment cylinder, label continuity, navigation, selector placement, overflow | Passed; product and copy become balanced peers rather than a scaled desktop scene |
| 390 × 844 opening | Narrow title/product/selector sequence, 32-segment cylinder, touch-safe controls, horizontal overflow | Passed after mobile overflow correction; browser smoke reports no overflow at 390 px |
| 390 × 844 Night Signal | Product-stage-aligned capture, direct flavor selection, can/field/label/copy synchronization | Passed; the selected can and named selector remain visible in one intentional mobile state |
| Reduced motion | Emulated `prefers-reduced-motion: reduce`, separate static can, Night Signal direct swap, unchanged CTA and pack path | Passed; 3D can is hidden, static can is shown, and flavor activation starts zero animations |
| Direct product control | Can focused and rotated with ArrowRight; CDP pointer drag moved 84 px across the product | Passed; both keyboard and pointer change yaw, and pointer ownership remains local to the product stage |
| Mobile navigation | Toggle opens panel, first destination receives focus, Escape closes, trigger regains focus | Passed at 390 × 844 |
| Six-pack conversion | Remove one Sun Shift → total 5/disabled/one-space guidance; add Pink Noise → total 6; submit local confirmation | Passed; status explicitly says no order or payment was sent and submit retains focus |
| Finite lifecycle | Wait after interaction, then inspect active Web Animations and `.bubble` nodes | Passed; zero running/pending animations and zero bubbles remain after the bounded sequence |

## Findings and response

| Status | Viewport / state | Visible or measured evidence | Consequence | Correction / rerender |
| --- | --- | --- | --- | --- |
| REVISE → PASS | 390 × 844, lower content | The unbroken display word `interruption.` widened the document to 478 px | Mobile opening was not a truthful 390 px composition and allowed horizontal scroll | Reduced narrow display size/measure and removed intrusive off-canvas ring pressure; rerender measured `clientWidth = 375`, `scrollWidth = 375` in the in-app browser and the 390 px CDP overflow audit passed |
| REVISE → PASS | Flavor switch, wide and narrow | The first flavor transition stopped near 155°, so the newly selected label could settle on the rear/blank side | State was technically selected but the physical package did not confirm it | Changed selection motion to one bounded forward revolution from the current yaw, settling on a multiple of 360°; added a smoke assertion and rerendered Pink Noise/Night Signal states |
| REVISE → PASS | Product top geometry, especially transition crops | A true 3D top disc painted behind rotating front segments while an auxiliary lid layer also existed; a tight user-provided crop exposed the disc as a detached circular “saucer” with the can wall cutting through it | The flagship physical product was mechanically implausible, and the first manual pass had incorrectly accepted the settled silhouette | Removed the conflicting 3D top plane and retained one screen-aligned aluminum rim outside the rotating body; the label cylinder now rotates beneath that mask while lid hardware tracks yaw. Added a three-width smoke assertion for exactly one centered, attached lid layer; recaptured every product still and all 72 GIF source frames |
| REVISE → PASS | Mobile interaction evidence | The first Night Signal capture showed the selector after a generic scroll position without enough can context | Evidence did not prove the product/selector relationship even though the interaction worked | Capture now aligns `.product-stage` before selection; rerender shows selected can, caption, and complete flavor controls together |
| REVISE → PASS | README motion preview | First frame capture included the browser scrollbar; low-color encoding introduced visible field dithering | The loop looked like tooling evidence rather than a polished campaign preview | Added scrollbar suppression only to isolated capture Chrome, recaptured 72 live frames after the lid repair, and encoded a 23-frame 720 × 560 shared-palette loop without dithering; final loop is 5.89 s and 1,582,174 bytes |
| PASS | 1440 / 900 / 390 product geometry | Final renders show aligned vertical axis, attached top/bottom, coherent label bands, controlled highlight/condensation, contact shadow, and no broken front seams | Physical product remains convincing across responsive segment reductions | Retained 48 / 40 / 32 panels by viewport; reduced mode uses an authored front can instead of reconstructing the cylinder |

No material `REJECT` remains. Every `REVISE` above was corrected and the affected state was rerendered.

## Diagnostics and accessibility

- Page initialization: `window.__benchmarkReady === true` at all smoke widths.
- Runtime/console/network: zero page exceptions, console errors or warnings, failed requests, or non-2xx local assets in manual and automated browser checks.
- Assets: HTML, CSS, JavaScript, SVG labels, fonts, and captures remain repository-local; runtime source contains no HTTP(S) dependency.
- Overflow: no horizontal page overflow at 1440, 900, or 390 widths after correction.
- Semantics: one `main`, one `h1`, labelled navigation, labelled product figures, named native buttons, synchronized `aria-pressed`, and polite flavor/pack status regions; regression parsing reports no duplicate IDs or unnamed buttons.
- Focus: visible focus was inspected on flavor controls, can, navigation, quantity controls, and submit; mobile menu handoff/restoration and Escape behavior passed.
- Motion interruption: pointer/key/flavor actions cancel the authored entrance; latest flavor input cancels stale rotation completion; hidden documents clear transient work.
- Repetition: flavor switching and pack editing were repeated without stale labels, stale pressed states, count drift, or delayed control availability.
- Reduced mode: product recognition, selected flavor, all content, navigation, quantity editing, CTA, and honest confirmation remain available without spatial choreography.
- Layering/crops: final wide, pressure, narrow, and static captures were visually inspected for typography collisions, z-index, product rims, label face, orbit lines, contact shadow, and selector overlap.

## Performance boundary

There is no WebGL/model/video dependency, media autoplay, scroll listener, persistent canvas, or idle animation loop. `requestAnimationFrame` exists only during the finite entrance, user drag release, keyboard turn, and flavor revolution; bubbles are deterministic finite DOM nodes cleared after 2.6 s. Chrome reports zero active animations and zero bubble nodes after settling. A formal cross-device frame-time trace, low-end hardware matrix, and energy profile were not run; those remain delivery limits rather than implied passes.

## Executed validation

| Command / inspection | Final result |
| --- | --- |
| `python -m unittest tests.test_soda_benchmark -v` | 5 focused Doppler tests passed |
| `python -m unittest discover -s tests -v` | 71 repository tests passed |
| `python evals/designer-behavior/run_eval.py` | 17 `KEEP`, zero `REVISE`/`REJECT` |
| `python -m compileall -q skill/snowe-ui-skill/scripts` | Passed |
| `node --check` for Goodturn, Doppler, all three forward-test apps, and `scripts/browser-smoke.mjs` | Passed |
| `node scripts/browser-smoke.mjs --smoke` | All five benchmarks passed wide/intermediate/mobile, interactions, and reduced motion; Doppler's single attached lid regression passed at 1440/900/390 |
| `node scripts/browser-smoke.mjs --capture-soda` | Seven final Doppler JPEG states recaptured after the product repair |
| `node scripts/browser-smoke.mjs --soda-motion-frames` with an isolated temporary directory | 72 final live-browser PNG frames captured, inspected through transition states, encoded into the committed loop, then removed |
| In-app Chromium inspection | 1440 × 1000, 900 × 1000, 390 × 844; normal/reduced; Sun/Pink/Night; menu focus/Escape; keyboard can; pack editing/confirmation; zero console warnings/errors |
| `python scripts/atlas/generate_atlas.py --check` | `Atlas structural map is up to date.` |

The repository exposes no lint, formatter, static typecheck, package build/install, automated visual-diff approval, full accessibility-engine audit, deployment, or backend integration command; none is reported as executed.

## Final evidence

- `screenshots/wide-overview.jpg` — 1440 × 5331 final page.
- `screenshots/wide-hero.jpg` — 1440 × 1000 opening product scene.
- `screenshots/wide-flavor.jpg` — 1440 × 1000 Pink Noise state.
- `screenshots/intermediate.jpg` — 900 × 1000 pressure composition.
- `screenshots/mobile-hero.jpg` — 390 × 844 narrow opening.
- `screenshots/mobile-interaction.jpg` — 390 × 844 Night Signal product/selector state.
- `screenshots/reduced-motion.jpg` — 1440 × 1000 authored static can.
- `screenshots/hero-motion.gif` — 720 × 560, 23 encoded frames, 5.89 s; final browser implementation, not separately fabricated motion.

Asset byte sizes, source hashes, licenses, and capture provenance are recorded in `ASSETS.md`. Architecture/art/motion selection and revisit triggers are recorded in `CANDIDATES.md`, `DECISIONS.md`, and `MOTION.md`.
