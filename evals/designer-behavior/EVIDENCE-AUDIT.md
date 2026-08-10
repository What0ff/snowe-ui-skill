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

The deleted layouts were not moved into an “archive” inside the installable skill: the rows lacked provenance and unique evidence strong enough to justify the anchoring risk. Git history remains the historical record.

## Retained evidence and boundary

| Catalog | Useful evidence | Boundary |
|---|---|---|
| `products.csv` | Product-category names and lexical terms for caller-requested analogy search. | Never auto-classifies a brief; result absence changes no framing; output contains no layout, style, palette, typography, or considerations. |
| `google-fonts.csv` | Family/category/script/designer and catalog metadata snapshot. | Does not choose a font or prove current files, license, metrics, language coverage, or rendering. |
| icon family/concept/candidate catalogs | Source discovery, exact known exports, role/metaphor questions, license/version URLs. | One named family for exact candidates; verify current source and rendered optical fit; custom and no-icon outcomes remain available. |
| `icons.csv` | Legacy lookup for familiar system actions. | Style/guideline rows are filtered; product-specific symbols require the broader icon process. |
| chart guidance | Encoding alternatives, failure cases, accessibility notes, and fallback prompts. | Caller selects the domain; the real analytical question and representative data determine the encoding. |
| UX, web, React, and stack guidance | Scoped implementation heuristics, failure modes, and code examples. | Explicit domain/stack only; reconcile with current official documentation, repository versions, platform behavior, and measured runtime. |

## Regression boundary

Automated coverage protects the following facts:

- automatic semantic domain detection is unavailable;
- decision packets do not retrieve analogs unless the caller provides `--analog-query`;
- obsolete recipe domains and files cannot reappear unnoticed;
- the product catalog exposes only lexical analogy fields;
- bundled CSVs contain no numeric conversion/engagement/time-on-page claims in the rejected forms;
- deleting or perturbing local analog retrieval does not change situation framing or architecture inquiry.

This audit classifies evidence quality; it does not claim that a retained row is current truth. Every retrieved result still carries a source role and a use boundary.
