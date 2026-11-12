# Local evidence audit

This audit records the hardening decision for fields that could silently move Snowe from evidence toward solution selection. The current CSV files are not a knowledge boundary, and no catalog is queried unless the caller names its domain (or explicitly requests product analogs in a decision packet).

## Removed recipe material

| Former dataset / fields | Epistemic finding | Action |
|---|---|---|
| `landing.csv`: `Pattern Name`, `Keywords` | Historical labels without source, date, product context, or outcome evidence. Potentially useful only as opt-in examples, but inseparable here from prescriptions. | Dataset deleted. |
| `landing.csv`: `Section Order`, `Primary CTA Placement` | Obsolete recipe fields that convert a product problem into a page skeleton. | Deleted; never returned by retrieval. |
| `landing.csv`: `Color Strategy`, `Recommended Effects` | Recipe-like art direction attached to page labels rather than brand/content evidence. | Deleted. |
| `landing.csv`: `Conversion Optimization` | Mixed universal prescriptions and unsupported numeric conversion, engagement, and time-on-page claims. | Deleted; repository regression scans all bundled CSVs for these numeric claim forms. |
| `products.csv`: style, landing, dashboard, palette, and consideration fields | Product categories were acting as keys into ready-made solutions. `Key Considerations` mixed useful questions with untraceable prescriptions. | Only `Product Type` and `Keywords` remain as explicit, unverified lexical analogy evidence. |
| `styles.csv`: colors, effects, usage rules, performance/accessibility flags, conversion flag, prompts, CSS, checklists, variables | A complete implementation recipe with unsupported suitability claims. | Removed before this hardening pass. |
| `styles.csv`: category, type, keywords, era | Initially retained as vocabulary, then found to mix visual labels with landing skeletons, dashboard topology, product-specific mobile bundles, palette, type, components, and motion. Even the reduced schema still anchored art direction. | Entire style domain and dataset deleted. Current visual-space exploration is contextual and externally verifiable. |
| `colors.csv`: product key and every palette role | Product-to-palette mapping with no brand evidence, rendered contrast, state coverage, provenance, or current context. | Dataset and domain deleted. |
| `typography.csv`: pairing, mood, `Best For`, imports, config, notes | Ready-made pairing recipes; font availability, scripts, license, metrics, files, and representative content were not proven. | Dataset and domain deleted. The Google Fonts catalog remains metadata only. |
| `motion.csv`: intensity, trigger, duration, easing, snippet, framework notes, `Do` / `Don't` | Motion was encoded as a preset rather than a consequence of state, continuity, explanation, feedback, or character. Snippets and framework claims can also age. | Dataset and domain deleted. Motion remains an open design outcome, including no animation. |
| `charts.csv`: `When to Use`, `When NOT to Use`, `Data Volume Threshold`, `Color Guidance`, `Accessibility Grade`, `Library Recommendation`, `Interactive Level` | Output already withheld these unsourced thresholds, hex palettes, grades, and library picks, but the installed file still shipped them to any agent that opened it. Several returned notes also misstated WCAG (for example, that pie charts "fail WCAG"). | Columns deleted from the file (2026-11-12). Returned notes rewritten to cite the actual success criteria (SC 1.4.1, 1.4.13, 2.1.1, 2.2.2) or to describe the perceptual limitation without an invented threshold. |
| `ux-guidelines.csv` / `app-interface.csv`: duration ranges, easing presets, per-view animation counts, hex and Tailwind color examples, `glass material`, obsolete `fastclick`, duplicate rows | Motion and color presets in a guidance costume; a 44 px target misattributed to WCAG; duplicate rows split retrieval. | Values removed or replaced with the governing standard (WCAG 2.2 SC 2.5.8 24×24 CSS px floor, platform 44 pt / 48 dp guidance stated as platform guidance); eight duplicate or obsolete UX rows merged or removed with stable row ids (2026-11-12). |
| `stacks/uwp.csv` | Legacy platform guidance (Windows 10 Mobile device families, `CoreDispatcher`, `ApplicationView`) presented as a current stack. | File and stack deleted (2026-11-12); the two still-useful rows (prefer WinUI 3 for new work, migrate UWP code) folded into `winui.csv`. `--stack uwp` returns an error naming `winui`. |
| `stacks/flutter.csv`, `swiftui.csv`, `jetpack-compose.csv`: superseded APIs taught as current (`FutureBuilder(future: fetchData())`, `textScaleFactor`, `onPopInvoked`, named routes, `primaryColor`; value-less `.animation`, `ObservableObject` as the High-severity default; Channel navigation events, pre-strong-skipping stability advice, code columns without code) | Version-sensitive guidance had aged into anti-patterns; Compose rows had lost their code and arrows. | Rows rewritten against current official documentation with a Docs URL each (2026-11-12); unverifiable or vacuous Compose rows deleted with stable ids. `tests/test_catalogs.py` rejects the superseded APIs in recommending columns. |

The deleted layouts were not moved into an “archive” inside the installable skill: the rows lacked provenance and unique evidence strong enough to justify the anchoring risk. Git history remains the historical record.

## Retained evidence and boundary

| Catalog | Useful evidence | Boundary |
|---|---|---|
| `products.csv` | Product-category names and lexical terms for caller-requested analogy search. | Never auto-classifies a brief; result absence changes no framing; output contains no layout, style, palette, typography, or considerations. |
| `google-fonts.csv` | Family/category/script/designer and catalog metadata snapshot. | Does not choose a font or prove current files, license, metrics, language coverage, or rendering. |
| icon family/concept/candidate catalogs | Source discovery, exact known exports, role/metaphor questions, license/version URLs. | One named family for exact candidates; verify current source and rendered optical fit; custom and no-icon outcomes remain available. |
| `icons.csv` | Legacy lookup for familiar system actions. | Style/guideline rows are filtered; product-specific symbols require the broader icon process. |
| chart guidance | Encoding alternatives, failure cases, accessibility notes, and fallback prompts. | Caller selects the domain; the real analytical question and representative data determine the encoding. |
| `ux-guidelines.csv`, `react-performance.csv`, and stack guidance | Scoped implementation heuristics, failure modes, and code examples. | Explicit domain/stack only; reconcile with current official documentation, repository versions, platform behavior, and measured runtime. |
| `app-interface.csv` (`mobile`, alias `web`) | iOS, Android, and React Native app-interface and accessibility prompts. | Mobile only, despite the legacy `web` name; reconcile with current platform guidance and the repository's framework version. |

## Regression boundary

Automated coverage protects the following facts:

- automatic semantic domain detection is unavailable;
- decision packets do not retrieve analogs unless the caller provides `--analog-query`;
- obsolete recipe domains and files cannot reappear unnoticed;
- the product catalog exposes only lexical analogy fields;
- bundled CSVs contain no numeric conversion/engagement/time-on-page claims in the rejected forms;
- no bundled CSV cell contains a hex color, millisecond duration, Tailwind color utility, numbered template prescription, or frame-rate claim, except exact pending findings in stack catalogs owned by a separate cleanup (`tests/test_catalogs.py`);
- every bundled CSV is BOM-free UTF-8 with LF endings and rectangular rows, and every configured column exists;
- deleting or perturbing local analog retrieval does not change situation framing or architecture inquiry.

`skill/snowe-ui-skill/data/CATALOGS.md` records each retained catalog's source, import and edit dates, row count, and license notice. Most catalogs derive from the MIT-licensed UI UX Pro Max skill (Next Level Builder); its notice ships with the data.

This audit classifies evidence quality; it does not claim that a retained row is current truth. Every retrieved result still carries a source role and a use boundary.
