# Snowe Design Decision Packet

**Project:** Goodturn Cycles
**Schema:** 2.0
**Brief:** Responsive commerce website for Goodturn Cycles, a fictional independent city-bike retailer. First-time and returning urban riders need to choose by daily use, carrying needs, terrain, maintenance tolerance, and fit; the business sells a curated three-bike range with transparent euro prices, guided fit, free local test rides, workshop care, delivery, and a 30-day right-ride exchange. Primary conversion is a fit-informed test ride or reserve/buy decision, not generic lead capture.

> This packet opens decisions; it does not select a layout, style, palette, font, image, icon family, or motion recipe.

## Design situation

- **Mode:** new_direction
- **Platforms:** responsive_web
- **Signals:** commerce
- **Fact policy:** The original brief and verified repository or external evidence are facts. Retrieved analogs, inferred audiences, market assumptions, and generated directions remain hypotheses until verified.

### Design pressures

- Make the offer concrete, support confident selection, expose price and fulfilment evidence, and place conversion where the decision becomes ready.

### Resolve before architecture

- What outcome is the primary user trying to reach, in what context, and what currently makes it difficult?
- What business outcome and conversion event matter, and what evidence would show success without harming the user outcome?
- Which actors, objects, content, states, entry points, return visits, and offline or cross-channel steps belong to the whole journey?
- Which requirements are facts, which are reversible assumptions, and which unknowns could change the architecture or brand position?
- What is sold, how does the assortment differ, which criteria drive selection, and which fulfilment, service, warranty, availability, or price facts remove purchase anxiety?

## Decision graph

- **Purpose:** Keep freedom causal: every material move traces back to a real driver and forward to an observable consequence.
- **Record:** `driver → design move → expected user/business consequence → evidence → risk → revisit trigger`
- **Freedom rule:** A downstream choice may be novel or absent from every local catalog. Keep it when its causal chain is stronger than the alternatives and it survives real-content and rendered tests.

- Outcomes and constraints
- Whole journey, actors, objects, content, decisions, and states
- Site/service topology, navigation, page jobs, and conversion paths
- Art direction, type, color/material, imagery, graphics, and motion language
- Components, interactions, responsive transformations, and implementation
- Rendered evidence, behavioral evidence, learning, and accepted decisions

## External research

- **Posture:** targeted, decision-led research; never a mandatory moodboard
- **Synthesis:** Extract transferable principles, tensions, and counterexamples. Do not copy a competitor's composition, brand codes, imagery, or interaction signature.

- **Question:** What does the current product, market, cultural, and visual landscape make familiar—and where is there room to be meaningfully distinct?
  - Sources: Real current products, official brand assets, primary platform guidance, and credible domain research
  - Stop: Stop when new sources repeat known approaches and no longer introduce a material architecture, content, or art-direction challenger.
- **Question:** What information and interaction evidence do buyers currently need to compare, trust, and purchase this category?
  - Sources: Current category retailers and manufacturers plus evidence-based ecommerce UX research
  - Stop: Stop after the main decision anxieties, content conventions, and strongest counterexamples are represented.
- **Record:** `decision | source | observed fact | implication | confidence | freshness | candidate changed?`

## Experience architecture

- **Status:** OPEN — synthesize after the whole journey and content model are understood

### Inputs

- Actors, contexts, frequency, stakes, and input modes
- User jobs, decision moments, dependencies, failure/recovery, and re-entry
- Business model, conversion, trust obligations, and success evidence
- Content and product objects, attributes, relationships, quantities, lifecycle, and ownership
- Entry points, search/discovery behavior, navigation depth, and cross-channel steps

### Synthesis

- Map the whole journey and object/content relationships before naming pages or sections.
- Define the site or product boundary around outcomes; do not mirror the organization, database, or a familiar template.
- Generate enough structurally different candidates to cover the live trade-offs. Change the organizing principle, sequence, navigation, disclosure, or conversion model—not only visual styling.
- Include a synthesized candidate when the strongest answer is not represented by retrieved patterns. Local data is evidence and analogy, never the candidate boundary.
- Prototype the riskiest page slice or journey transition with real content before selecting the complete architecture.

### Candidate record

- **Thesis:** How this architecture organizes the user's world
- **Site Scope:** What belongs, what does not, and how cross-channel steps join up
- **Topology:** Destinations or product areas and the relationships that justify them
- **Navigation:** How users orient, move, search, compare, return, and recover
- **Page Jobs:** For every key page: what the user should understand, decide, or do
- **Content Sequence:** Questions and dependencies that determine order; no hero or section type is mandatory
- **Conversion Path:** Where intent becomes ready and what proof precedes the action
- **Responsive Transformation:** What stays invariant and what reorders, collapses, changes control, or changes medium
- **Risk:** The assumption most likely to invalidate this candidate
- **Selection:** Select by causal fit, clarity, content resilience, identity potential, accessibility, and feasibility. Hybridize only compatible moves that form one coherent organizing logic.

## Art direction

- **Status:** OPEN — architecture and real content constrain the visual language before styling begins

### Identity sources

- The product's real objects, construction, workflow, or information relationships
- Audience language, culture, habits, and context of use
- Verified brand history, voice, assets, materials, place, and behavior
- The form and quality of real content—not placeholder volume or trend labels
- Product engineering, materials, fit, use environments, service expertise, and the rituals of selection and ownership

### Direction method

- Frame directions as perceptual and behavioral theses, not style labels or mood adjectives.
- Make finalists differ in composition, typographic voice, image/graphic logic, material behavior, or interaction character where those differences express a real product trade-off.
- Choose one primary identity carrier and define its repetition boundary. The carrier may be architecture, type, content behavior, imagery, graphics, data, or motion; decoration is optional.
- Use typography, color, shape, and material as a coherent system derived from content, scripts, platform, and desired perception. A dataset pairing or palette is only a candidate.
- **Record:** `thesis | perception | product-specific source | dominant composition | type voice | color/material logic | imagery/graphic logic | interaction/motion character | signature boundary | strongest risk`

## Imagery and custom assets

- **Visual decision:** OPEN — What must a visual explain, prove, orient, reveal, or make desirable that type, layout, real product UI, or no image cannot do better?
- **Selection:** Choose by communicative job, truthfulness, provenance, art-direction fit, responsive crop, performance, and maintenance—not by novelty or tool availability.

### Eligible outcomes

- No image
- Verified existing or brand asset
- Product photography or commissioned photography
- Illustration
- Diagram or data-led graphic
- 3D/product composition
- Generated artwork or photography
- Repository-owned custom graphic

### Generated imagery

- **Use when:** Generation can produce a needed, truthful, ownable composition that is unavailable from real product, brand, licensed, commissioned, or diagrammatic sources inside scope.
- **Art-direction brief:** `page role | communicative job | exact aspect/crop | subject and action | camera/perspective | subject placement and negative space | light/material/palette | continuity with type and surfaces | required truth | prohibited artifacts/cliches | responsive variants`

- Generate a small set of meaningfully different compositions, not prompt paraphrases.
- Place finalists in the actual layout at target crops and widths before judging them.
- Inspect anatomy, product truth, text-like artifacts, edge quality, focal competition, crop resilience, loading cost, and provenance disclosure.
- Regenerate, edit, or reject the asset when the real layout is weaker than the no-image or non-generated alternative.

### Custom graphics and icons

- **Family specification:** `role | grid/viewBox | live area/keylines | stroke or fill model | caps/joins/corners | curvature | optical overshoot | counter/negative-space minimum | detail budget by size | color modes | source/provenance`

- Decide whether visible text, an existing symbol, a compatible external family, or a custom graphic gives the clearest and most ownable result.
- Sketch materially different silhouettes and compound constructions before polishing paths.
- Draw to the family specification; use optical compensation rather than mechanically identical bounds.
- Run structural SVG/provenance validation, then render at 16, 20, and 24px and at every actual interface size beside neighboring icons.
- Test default, selected, disabled, dark, high-contrast, and labelled contexts where applicable.
- **Reject when:** Reject or redraw when recognition depends on explanation, counters close, stroke/area feels heavier than neighbors, the metaphor conflicts with the action, the silhouette collapses, or an existing asset is visibly stronger.

## Motion

- **Status:** OPEN — the static and reduced-motion experience is the baseline
- **Decision:** Does motion clarify cause, continuity, hierarchy, spatial relationship, progress, feedback, or story—and is that benefit worth its repetition and runtime cost?
- **Record:** `trigger/state change | information motion carries | affected hierarchy | frequency | choreography | interruption | performance budget | reduced/static equivalent | reject condition`

- Use immediate restrained feedback for frequent controls; reserve expressive choreography for low-frequency moments whose narrative or spatial role earns it.
- Motion must be interruptible and must not delay task completion, hide required state, or create a gesture-only path.
- Test repeated use and `prefers-reduced-motion`; reduction may preserve a short opacity/state transition when removing all feedback would weaken comprehension.
- Choose no animation when the static state change is clearer, faster, calmer, or more accessible.

## Responsive behavior

- **Principle:** Design transformations, not three screenshots. Preserve outcome, priority, reading order, state, and conversion while changing composition and controls when space or input mode changes.
- **Contract:** `invariants | reorder/collapse rules | navigation transition | content disclosure | media crop/substitution | comparison behavior | sticky/fixed behavior | pointer/touch/keyboard differences | long-content and localization stress`
- **Proof:** Render narrow, at least one pressure width between planned breakpoints, and wide; include zoom/text scaling, long real content, focus, open overlays, selected/disabled/error states, and reduced motion.

## Evaluation

- **Verdicts:** `KEEP | REVISE | REJECT | UNKNOWN`

- Causal fit: important moves trace to real user, business, content, brand, or platform drivers.
- Structural range: candidates change organizing logic where the brief contains a real trade-off; cosmetic variants do not count.
- Synthesis: the chosen answer may exceed every local recipe and does not inherit an analog's identity by accident.
- Coherence: architecture, visual language, assets, interactions, and motion reinforce one thesis without uniformity for its own sake.
- Discretion: imagery, generation, custom graphics, and animation appear only when they outperform simpler alternatives.
- UX resilience: task clarity, accessibility, localization, content variation, performance, and responsive behavior survive the direction.
- Rendered proof: visible hierarchy and interaction quality are evaluated in the real product, not certified by policy prose or code tokens.
- **Finding record:** `verdict | viewport/state | visible or behavioral evidence | consequence | correction or acceptance reason | rerender/retest`
- **Stop:** Resolve every REJECT and material REVISE finding, rerender the affected evidence, and stop when further change no longer improves a stated driver. Preserve UNKNOWN where evidence genuinely cannot be obtained.

## Local evidence

- **Role:** lexical analogs and prompts for investigation—not classification, direction, or architecture
- **Limitations:** Bundled CSVs are snapshots, mainly English, and contain historical recipes and unverified claims. Confirm current facts externally and synthesize beyond them.

- **E-commerce** — `UNVERIFIED_ANALOG`; matched: buy, commerce, ecommerce, primary, retail
  - Possible evidence: Engagement & conversions. High visual hierarchy.
  - Warning: Use only the relevant concern or content clue. Do not inherit this row's product identity, layout, style, palette, or landing recipe.
- **E-commerce Luxury** — `UNVERIFIED_ANALOG`; matched: buy, commerce, ecommerce, retail
  - Possible evidence: Elegance & sophistication. Premium materials.
  - Warning: Use only the relevant concern or content clue. Do not inherit this row's product identity, layout, style, palette, or landing recipe.
- **Logistics/Delivery** — `UNVERIFIED_ANALOG`; matched: conversion, delivery
  - Possible evidence: Real-time tracking. Delivery scheduling. Route optimization. Driver management. Status updates. Map integration.
  - Warning: Use only the relevant concern or content clue. Do not inherit this row's product identity, layout, style, palette, or landing recipe.
