# Goodturn Cycles — Bicycle Commerce Benchmark

Goodturn is the first complete rendered forward-test for the redesigned Snowe designer behavior. It is a fictional independent city-bike workshop in Bucharest with a deliberately small range, personal fitting, free test rides, workshop care, a refundable reservation path, and a human-scale retail visit.

![Goodturn Cycles homepage](screenshots/desktop-home.jpg)

## What the benchmark proves

- Site architecture is synthesized from product, audience, decision anxiety, content, and conversion—not selected from a landing-page recipe.
- Three concrete bicycles, prices, use cases, fit ranges, fulfilment facts, and ownership terms appear before optional guidance.
- The visual system has one contextual thesis: an urban workshop field guide with warm paper, mechanical ink, vermilion signals, citron utility marks, condensed display type, route geometry, and realistic product imagery.
- Generated imagery exists because physical bicycle form, scale, crop, and desirability matter; its provenance is disclosed.
- Four custom service icons use one repository-owned drawing language and are validated structurally before optical review in context.
- Motion is limited to functional state continuity; the static and reduced-motion experience remains complete.
- Wide, pressure, and narrow compositions preserve the same evidence and conversion paths through different layouts.
- Filtering, comparison, finder, product sizing, reservation/cart, test-ride booking, errors, focus, and success are implemented states rather than mockups.

Everything commercial in this benchmark—brand, products, specifications, prices, availability, policies, address, and imagery—is fictional. It must not be presented as a real retailer or real product catalog.

## Run locally

From the repository root:

```bash
python -m http.server 4173 --directory benchmarks/bicycle-commerce
```

Open `http://127.0.0.1:4173/`. No build step or package installation is required.

## Design evidence

- [Brief](design-intelligence/goodturn-cycles/BRIEF.md)
- [External research](design-intelligence/goodturn-cycles/RESEARCH.md)
- [Architecture and art-direction candidates](design-intelligence/goodturn-cycles/CANDIDATES.md)
- [Accepted causal decisions and strongest rejected alternative](design-intelligence/goodturn-cycles/DECISIONS.md)
- [Asset decisions and provenance](design-intelligence/goodturn-cycles/ASSETS.md)
- [Rendered QA, revisions, retest evidence, and remaining limits](design-intelligence/goodturn-cycles/QA.md)

## Visual evidence

| Wide product field | Comparison state |
| --- | --- |
| ![Wide product field](screenshots/desktop-products.jpg) | ![Comparison state](screenshots/desktop-compare.jpg) |

| Pressure width | Mobile product sheet |
| --- | --- |
| ![Intermediate viewport](screenshots/intermediate-home.jpg) | ![Mobile product sheet](screenshots/mobile-product-sheet.jpg) |

Additional captures in [`screenshots/`](screenshots/) cover the optional finder, custom-icon service context, mobile homepage, and mobile navigation.

## Validation

The repository suite checks benchmark structure, concrete commerce content, local/provenanced assets, semantic references, responsive and reduced-motion branches, implemented interaction contracts, SVG validation, design trace completeness, and final screenshot coverage. Visual quality itself is preserved as rendered human evidence in `QA.md`, not collapsed into a synthetic score.
