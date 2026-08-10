# Doppler Soda — Asset and Provenance Record

## Visual job

For a visitor encountering a fictional drink, the product visual must make a cold aluminum soda can, selected flavor, and carbonation pressure desirable and recognizable before they choose a blend or compose a six-pack.

## Alternatives compared

| Approach | In-layout result | Decision |
| --- | --- | --- |
| No product visual | Type can name the product but cannot prove package form, cold material, or the physical motion thesis | Rejected |
| Generated product still | Could improve photographic surface quality in one crop but cannot preserve exact label/geometry across rotation and flavor change | Rejected |
| Generated lifestyle photography | Adds occasion but introduces hands, reflections, package-text continuity, crop, and imitation risks without improving selection | Rejected |
| Pure flat illustration | Keeps labels editable and local but does not satisfy spatial physicality | Rejected as the primary normal-motion asset; retained as reduced/static fallback |
| Modeled/WebGL product | Strongest raw physical rendering; adds model, texture, renderer, license, performance, and separate fallback ownership | Rejected unless CSS-3D material proof fails |
| CSS-3D + SVG label + code-native graphics | One editable product identity supports rotation, flavor state, responsive changes, static fallback, and repository-local delivery | Selected |

## Drawing language

```text
roles: package label, pressure/signal field, carbonation/fizz, flavor state
primitives: horizontal bands, offset rings, circles, cropped oversized wordforms
geometry: cylindrical wrap and front-facing orthographic fallback
line/fill: solid high-contrast fields; no decorative outline family
edges: crisp label blocks against soft aluminum light and circular bubble highlights
positive/negative rhythm: dense signal compression at product, calm reading space around facts
detail budget: package name + flavor + category + 330 ml; no simulated legal microcopy
color: one light/dark pair per flavor plus stable aluminum/ink/paper
type relationship: label and campaign share Unbounded; utility content stays Manrope
motion potential: horizontal surface continuity, rotational flavor change, finite rising fizz
responsive simplification: reduce segment count/effect density; static front label in reduced mode
ownership: original benchmark SVG/CSS/HTML/JS, MIT repository license
```

## Repository-local assets

| Path | Bytes | SHA-256 | Source / license | Role |
| --- | ---: | --- | --- | --- |
| `assets/fonts/unbounded-latin.woff2` | 50,904 | `22F9B928AA3928A896340422B54D690FBB5875C30EAE4C106F029C61F2289FD6` | Google Fonts official `Unbounded` Latin webfont; SIL Open Font License 1.1 copied locally | Campaign, brand, package label |
| `assets/fonts/manrope-latin.woff2` | 24,836 | `A30DDCD349703AFF7464C34BEF3FFFDFF405EE50C113440D7C8693C02D210972` | Existing repository copy from Google Fonts; SIL Open Font License 1.1 copied locally | Body, controls, facts, price/status |
| `assets/fonts/OFL-Unbounded.txt` | 4,392 | `31E5D4E83955E7103C34570DD49B0570EF490800BD65B42923C0DD02445263B3` | Official Google Fonts license text | Unbounded redistribution record |
| `assets/fonts/OFL-Manrope.txt` | 4,383 | `F612090FB72B6DCA3E807E66FA0D2B5DEF163CEF86F1A3209B5C897CBA5EE4B7` | Existing repository OFL text | Manrope redistribution record |
| `assets/labels/sun-shift.svg` | 2,233 | `B6C322F82E975950C5A96D8965F37B18F9F7B017F1D0C548B197FE845E10F131` | Original code-native benchmark asset | Sun Shift cylindrical label texture and static package face |
| `assets/labels/pink-noise.svg` | 2,236 | `940EA2752CA94B3DA33E43ED4126290BC6A59059A767879E01974A7844A50AEF` | Original code-native benchmark asset | Pink Noise cylindrical label texture and static package face |
| `assets/labels/night-signal.svg` | 2,257 | `BB3438059DC433170B4E12B71E9667FE0A8C9285D83F1C883201E37DE96B0E05` | Original code-native benchmark asset | Night Signal cylindrical label texture and static package face |

Official source snapshot used during development: `https://github.com/google/fonts/tree/main/ofl/unbounded`. The top-level Google Fonts repository documents that font directories carry their own license files. No asset makes a runtime network request.

## Generated imagery decision

No AI-generated imagery is used. The comparison ended before generation because a bitmap still lost on the defining requirement: one coherent package must rotate, change label, adapt to three compositions, and become a truthful static fallback. Browser screenshots and the GIF are evidence captured from the implemented site, not source imagery or separately fabricated animation.

## Captured evidence assets

| Path | Dimensions / duration | Bytes | Provenance |
| --- | --- | ---: | --- |
| `screenshots/hero-motion.gif` | 720 × 560, 23 encoded frames, 5.89 s, looping | 1,582,174 | Optimized from 72 sequential frames captured from the final browser implementation; begins and ends on Sun Shift |
| `screenshots/wide-overview.jpg` | 1440 × 5331 | 614,835 | Final browser full-page capture |
| `screenshots/wide-hero.jpg` | 1440 × 1000 | 201,838 | Final normal-motion opening state |
| `screenshots/wide-flavor.jpg` | 1440 × 1000 | 170,948 | Final Pink Noise product state |
| `screenshots/intermediate.jpg` | 900 × 1000 | 151,116 | Final pressure-width composition |
| `screenshots/mobile-hero.jpg` | 390 × 844 | 75,707 | Final narrow opening composition |
| `screenshots/mobile-interaction.jpg` | 390 × 844 | 51,081 | Final narrow Night Signal product/selector state |
| `screenshots/reduced-motion.jpg` | 1440 × 1000 | 199,224 | Final separately composed static product state |

All captures came from the repository-local implementation served on loopback. They are evidence outputs, not runtime dependencies.

## Asset QA result

- Inspect label text at full-size source and on the actual curved can; no generated text-like artifacts are possible.
- Inspect cylinder top/bottom alignment, panel seams, perspective, reflection direction, contact shadow, condensation placement, and rotation axis at all three widths.
- Inspect the static label as a complete product representation in reduced mode.
- Verify SVGs contain no remote references, scripts, embedded rasters, trademarks, or accidental real-brand copy.
- Final byte sizes, source hashes, and rejected asset approaches are recorded above; rendered findings and corrections are in `QA.md`.
