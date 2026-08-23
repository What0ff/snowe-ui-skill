# Goodturn Cycles — Accepted Design Decisions

This benchmark is a fictional business. Product names, specifications, prices, policies, availability, and imagery are concept content created for the Snowe evaluation, not real commercial claims.

## Product truth

- **Offer:** a deliberately small range of three city bicycles plus fit, test rides, delivery, and workshop care.
- **Primary audience:** people who want an everyday bicycle but do not speak component-catalog language; experienced riders remain welcome.
- **Primary anxiety:** choosing the wrong use case or fit for a high-consideration purchase.
- **Business conversion:** a fit-informed free test ride, or a refundable €50 reservation when the buyer is ready.
- **Success condition:** a visitor can identify what Goodturn sells, understand why the three models differ, see prices and ownership terms, choose a likely model, and reach a credible next action without a forced quiz.

## Causal decision graph

### D1 — Product field with optional guidance

- **Status / scope:** ACCEPTED / site architecture
- **Driver:** novices need guidance, but hiding the assortment behind questions prevents immediate comprehension and price comparison.
- **Decision:** show the complete three-bike range early as a use-case field; offer an optional three-step “Find my ride” path and an explicit comparison layer. Organize navigation around `Bikes`, `Find my ride`, `Workshop`, and `Visit`, not component categories.
- **Expected consequence:** visitors can browse directly, understand the range boundary, or ask for help without entering a funnel.
- **Evidence:** Canyon’s current city/touring finder begins with intended riding; ecommerce research makes product detail central to purchase; the benchmark brief requires concrete bikes and prices.
- **Risk:** three choices may feel artificially narrow.
- **Revisit trigger:** representative users cannot place themselves in one use case, or repeatedly ask for a category outside the range.

### D2 — Test ride and reservation are peer conversion paths

- **Status / scope:** ACCEPTED / conversion
- **Driver:** fit and ride feel cannot be proven entirely on screen; some returning riders are ready to reserve.
- **Decision:** make `Book a test ride` the reassurance path and `Reserve for €50` the direct-commerce path. State that the reservation is refundable and deducted from the final price. Keep price, included setup, pickup/delivery cost, availability, and 30-day exchange beside the product action.
- **Expected consequence:** the primary action matches confidence level rather than forcing every visitor into checkout or lead capture.
- **Evidence:** Brompton positions test rides as the final comparison/reassurance step; Baymard’s 2026 product-page synthesis emphasizes visible fulfilment cost and return information near buying.
- **Risk:** two actions can compete.
- **Revisit trigger:** rendered hierarchy makes both actions equal before fit/use evidence, or interaction tests show uncertainty about what “reserve” means.

### D3 — Workshop field guide art direction

- **Status / scope:** ACCEPTED / visual system
- **Driver:** the retailer must feel expert and human, distinct from both mass catalogs and glossy performance manufacturers.
- **Decision:** use an urban workshop field-guide thesis: warm uncoated-paper surfaces, near-black mechanical ink, vermilion signal color, one citron utility accent, condensed display type, precise utility text, ruled measurements, and route/wheel geometry. Product photography remains materially realistic.
- **Expected consequence:** Goodturn feels specific, local, useful, and desirable without borrowing racing codes or generic “premium minimal” styling.
- **Evidence:** product engineering, fitting measurements, workshop artifacts, city route marks, and physical ownership rituals are native identity sources.
- **Risk:** field-guide detail can become decorative clutter.
- **Revisit trigger:** annotations compete with product facts or repeated linework stops carrying hierarchy.

### D4 — Generated product photography defines fictional inventory

- **Status / scope:** ACCEPTED / imagery
- **Driver:** bicycles are physical high-consideration products; scale, frame form, mounting style, racks, and carrying behavior cannot be replaced by abstract decoration.
- **Decision:** use one in-scale editorial riding image and one coordinated studio image per fictional model. No generated image contains type, logos, or unverified real-brand claims. Label the benchmark and generated provenance. Reject transparent cutouts because spokes, reflective metal, and contact shadows make chroma extraction visibly weaker than grounded studio frames.
- **Expected consequence:** the page communicates product truth, human scale, and desirability while maintaining a coherent asset system.
- **Evidence:** Baymard reports that product imagery is used to judge scale; Snowe’s no-image comparison found that type/specification alone could not prove bicycle form or fit context.
- **Risk:** generated mechanical details can be subtly wrong.
- **Revisit trigger:** full-resolution or in-layout review exposes impossible drivetrain, wheels, contact, crop, or inconsistency that undermines trust.

### D5 — Custom graphics are a small functional family

- **Status / scope:** ACCEPTED / brand mark and service icons
- **Driver:** generic icon libraries cannot carry Goodturn’s measurement/route identity, but custom symbols must not reduce recognition.
- **Decision:** draw a code-native wordmark symbol plus three product-specific 24-grid service icons for fit, test ride, and workshop. Use the pinned external Lucide `Repeat 2` glyph for exchange after the custom crate/delivery challenger proved semantically wrong. Familiar close, menu, plus/minus, and navigation controls remain conventional text or simple universal symbols.
- **Expected consequence:** product-specific character appears where the metaphor is genuinely specific, while the learned exchange action remains immediately recognizable.
- **Risk:** small bicycle-derived symbols lose clarity at 16px.
- **Revisit trigger:** target-size neighbor comparison is weaker than visible text or an established symbol.

### D6 — Motion explains state, not atmosphere

- **Status / scope:** ACCEPTED / interaction
- **Driver:** filtering, guided choice, dialogs, cart state, and comparison have real continuity needs; repeated scroll choreography would distract from inspection.
- **Decision:** use immediate/short motion for menu/dialog origin, filter/product state, recommendation progress, comparison rail, and cart feedback. No looping decoration, parallax, or mandatory scroll reveal. Reduced motion keeps immediate state feedback without spatial travel.
- **Expected consequence:** state changes feel connected while dense product reading remains calm.
- **Risk:** transition polish delays actions on mobile.
- **Revisit trigger:** repeated use feels slower than the static baseline or focus/state falls out of sync.

### D7 — Responsive transformation preserves decision evidence

- **Status / scope:** ACCEPTED / responsive
- **Driver:** product selection, price, fit, and conversion cannot disappear when the wide editorial composition collapses.
- **Decision:** wide view pairs thesis and in-scale image; pressure width reduces display scale and converts navigation before columns collide; narrow view moves image below the promise, turns the product field into stacked inspection, keeps visible size/use facts, and converts comparison/dialogs to full-width sheets. No primary action is hover-only.
- **Expected consequence:** the same decision can be completed at every width with a different composition rather than a shrunken desktop.
- **Risk:** mobile page length becomes excessive.
- **Revisit trigger:** key bike differences or the next action require repeated backtracking at 360–430px.

## Strongest rejected alternative

An obligatory guided bike-finder as the homepage was rejected. It would directly address novice uncertainty, but it would hide the small, comprehensible assortment, prices, and Goodturn’s core commercial offer until after interaction. The accepted optional guide preserves that help without making a questionnaire the site architecture.
