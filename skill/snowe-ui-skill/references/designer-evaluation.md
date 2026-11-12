# Designer Behavior Evaluation

Use this reference to evaluate or compare designs: whether the work made strong design decisions, not whether it mentioned the expected rules. Automated checks protect contracts and invariants; rendered and comparative evidence evaluates the design.

## Evaluation Unit

Evaluate a complete trace where possible:

```text
brief and verified context
questions and assumptions
research evidence
decision graph
architecture and art-direction candidates
selected implementation contract
working artifact
wide / pressure / narrow renders and important states
findings, corrections, and rerenders
```

A generated plan alone can reveal anchoring or bureaucracy but cannot prove visual quality, interaction, or responsive coherence.

Use the method/verdict distinction in [quality-gates.md](quality-gates.md#explicit-visual-disposition). For sequential work without another evaluator, label the second pass as self-review; do not call it blind or independent. A stronger report contract demonstrates reliable bookkeeping. Better generation or criticism still needs repeated observed tasks and fair comparisons.

## Evaluate With Findings, Not a Creativity Score

Judge findings against the rendered artifacts. A self-review must be labelled as such; neither a second agent nor a numeric score replaces rendered or behavioral evidence.

Use:

```text
KEEP | REVISE | REJECT | UNKNOWN
criterion | artifact/state/viewport | evidence | consequence | correction or acceptance reason
```

Do not average taste into a number. One severe failure in truth, primary-task clarity, accessibility, conversion, or responsive behavior can invalidate an otherwise attractive result.

## Behavioral Questions

### Problem and architecture

- Did the work model the user's whole outcome, business mechanism, actors, objects, content, decision moments, return/recovery, and conversion before naming a familiar page pattern?
- Are candidates structurally different because of live trade-offs, or are they cosmetic variants?
- Could the selected site/page architecture have been synthesized without a matching local recipe?
- Does navigation follow orientation and object relationships rather than an organizational chart or default header?
- Is the strongest rejected alternative real and fairly represented?

### Art direction and coherence

- Is the visual thesis traceable to product, audience, content, brand, place, or behavior rather than a trend label?
- Do composition, type, color/material, imagery/graphics, icons, interactions, and motion reinforce that thesis with understandable role boundaries?
- Is there meaningful distinction without compulsory decoration?
- Does the result survive real content and secondary states rather than only one hero view?

### Discretion and invention

- Were `no image`, `no custom asset`, and `no motion` treated as valid alternatives where relevant?
- When generation or custom work was used, did it outperform a simpler existing option in the actual layout?
- Did external research introduce, challenge, or eliminate real candidates rather than produce copied styling?
- Does novelty serve comprehension, identity, desirability, or interaction instead of merely differing from the catalog?

### UX and delivery

- Are primary outcomes, prices/claims/content, actions, states, focus, error recovery, and accessible names clear and truthful?
- Does responsive behavior transform sequence, controls, navigation, imagery, density, and disclosure while preserving priority?
- Do localization, long content, missing data, zoom/text scaling, reduced motion, input modes, and performance constraints survive?
- Did rendered findings cause real corrections, including reopening a weak premise when necessary?

## Cross-Scenario Comparison

Lay traces side by side and look for unjustified convergence:

- repeated site topology, page sequence, hero construction, card rhythm, conversion flow, navigation, visual carrier, type voice, palette behavior, imagery posture, or motion grammar;
- the same output vocabulary with nouns swapped;
- identical candidate counts and comparison rituals regardless of uncertainty;
- local dataset categories leaking into briefs that do not fit them.

Different briefs do not have to look different for its own sake. Convergence is acceptable when the causal evidence independently supports it; demand that explanation. Conversely, cosmetic variation does not count as architecture diversity.

## Custom Asset Evaluation

Structural SVG validation is necessary but not aesthetic proof. Render custom icons/graphics:

- at every target size and theme;
- beside real neighboring icons, type, controls, and surfaces;
- in simple and dense roles;
- with default, active, disabled, and focus/hover states when applicable;
- on representative displays or pixel-density captures.

Check recognition, ambiguity, optical size, center of mass, baseline, stroke/fill weight, terminal and corner coherence, negative space, detail loss, color inheritance, and repeated-family rhythm. Compare with text, native/existing symbols, and the strongest external candidate. Reject custom work when it loses.

Evaluating changes to Snowe itself (scenario portfolios, paired revisions, held-out briefs) is repository maintenance and lives outside the installed skill.

## Benchmark Acceptance

A showcase benchmark is accepted only when:

- the business and offer are concrete, truthful within the fictional scenario, and immediately understandable;
- architecture, content, conversion, and visual identity form one product-specific thesis;
- representative products, prices, comparison/selection evidence, and an actionable conversion path exist;
- used imagery, custom assets, and motion each have a stated job and in-layout comparison; omissions are deliberate;
- wide, pressure, and narrow screenshots plus important interaction/reduced-motion states were reviewed;
- every `REJECT` and material `REVISE` was corrected and rerendered;
- build, static, accessibility, and relevant performance checks passed or their limitations are explicit.

Store the brief, decision evidence, raw renders, findings, and final artifacts so another evaluator can inspect the claim. A README screenshot is a showcase, not the sole proof.
