# Art Direction Gate

Use this reference for a new product, a redesign, a material visual-identity change, or any task where the direction is genuinely unresolved. Apply [exploration-protocol.md](exploration-protocol.md) first so direction cards represent the relevant option space rather than the first familiar recipes. Use the compact path for contained work inside an established system.

## Contents

1. Choose the review mode
2. Frame direction cards
3. Run the critic pass
4. Prove creative distinction
5. Select without averaging
6. Freeze an implementation contract
7. Critique the rendered result
8. Record the decision
9. Avoid false rigor

## 1. Choose the review mode

Match the amount of exploration to the decision at stake.

| Situation | Mode | Required comparison |
|-----------|------|---------------------|
| Bug fix, state addition, or narrow component change | Direct execution | Check the proposed change against the current system and task |
| Polish or extension of an established interface | Refinement gate | Compare the current baseline with one focused refinement hypothesis |
| New product, redesign, or unresolved identity | Full concept gate | Compare two direction cards; add a third only for another material product trade-off |
| Two viable directions imply materially different brand positions | User checkpoint | Present the trade-off and evidence; do not invent certainty |

Do not create several concepts for routine maintenance. Do not skip concept selection for a new identity merely because implementation can start quickly.

## 2. Frame direction cards

Keep every candidate on the same product truth, content, functional requirements, and platform constraints. Change the design approach, not the problem being solved.

Build candidates only after declaring the relevant universe of composition, typography, material, imagery, interaction, and motion approaches. Search outside the repository while treating the current product as the baseline. Direction cards are finalists from that exploration, not substitutes for it.

For each candidate, define:

- A concrete name and one-sentence thesis
- The desired perception and primary user task
- The dominant composition, focal point, and reading path
- Information density and disclosure model
- Typography roles and hierarchy
- Color, material, surface, and elevation logic
- Shape and visible control scale
- Icon, imagery, illustration, and data language
- Motion purpose and restraint
- One signature device that belongs to the product when it improves recognition, or an explicit decision that content, typography, or composition already carries the identity
- Explicit defaults to reject for this direction
- Required assets, implementation cost, and main risk
- Evidence from the repository, brief, content, platform, or supplied brand material

Use representative real content. A concept that works only with short placeholder copy is not ready for selection.

Make each full-gate candidate express a material design trade-off through relevant dimensions such as composition, type hierarchy, density, content model, imagery or material language, interaction, or motion. A palette, radius, or icon swap alone is a variant, but do not force an arbitrary number of differences unrelated to the brief.

Keep an established product baseline visible during a refinement gate. Preserve existing tokens and interaction patterns unless the requested scope authorizes changing them.

## 3. Run the critic pass

Critique the concept before implementation. Use only these statuses:

- `PASS`: supported by evidence and ready for the current stage
- `BLOCKER`: contradicts a requirement, harms the primary task, or cannot be delivered safely
- `UNKNOWN`: material evidence is missing; do not silently convert it to a pass
- `N/A`: the criterion does not apply, with a short reason

Put exactly one token in the status field. Put evidence, risk, caveats, and corrective actions in separate fields; never invent `PASS with risk`, `conditional pass`, or another softened status.

Do not use numeric taste scores. They create false precision and encourage the evaluator to reward its own prose.

Reserve `BLOCKER` for a violated requirement, inaccessible or unsafe outcome, loss of required content or functionality, or a delivery constraint that makes the concept infeasible. Package counts, class names, exact pixel values, raw hue names, card or font counts, and preferred recipes are diagnostic signals; they can motivate investigation but cannot block a concept by themselves.

Evaluate each direction against the same dimensions:

| Dimension | Evidence to inspect | Typical blocker |
|-----------|---------------------|-----------------|
| Product and audience fit | Brief, product behavior, real user task | The visual story describes a different product or audience |
| Task clarity and hierarchy | Content order, focal point, action priority | Multiple dominant actions or the main task is visually secondary |
| Information architecture | Real content, states, navigation, disclosure | Required information is hidden or fragmented for the sake of composition |
| Content resilience | Long labels, localization, large values, empty/error/loading data | The concept depends on ideal-length copy or complete data |
| System coherence | Tokens, component roles, icon source-role map, rendered drawing languages, motion language | Several unrelated visual grammars, accidental source mixing, or one-off primitives |
| Distinctiveness | Product-specific subject, mechanism, data, or content | The identity is only a fashionable effect or generic SaaS template |
| Brand provenance | Supplied assets and verified brand rules | Invented brand claims, unofficial marks, or unsupported palette assumptions |
| Accessibility feasibility | Contrast, semantics, focus, zoom, targets, reduced motion | A core visual device requires inaccessible text, color-only meaning, or hidden controls |
| Platform and interaction fit | Native conventions, input modes, responsive behavior | The concept fights expected navigation or cannot work with the target input mode |
| Technical feasibility | Existing stack, component library, asset and performance budget | The direction requires a rewrite, dependency, asset, or runtime cost that is incompatible with the authorized scope |
| Guardrail integrity | Shape, controls, color, icon roles and compatibility, surfaces | Repeated decoration harms hierarchy, controls are inflated, icon sources conflict visibly, metaphors mislead, or unrequested neon/glow becomes the identity |

Write one short evidence statement and, for `BLOCKER` or `UNKNOWN`, one corrective action. Use separate `Status`, `Evidence`, and `Risk / correction` columns when comparing directions. Critique the direction, not the author.

Reject a concept immediately when it removes required functionality, contradicts verified brand or platform requirements, depends on assets confirmed unavailable within scope, or makes accessibility structurally infeasible. Mark unverified asset availability as `UNKNOWN` with a corrective action rather than fabricating a blocker. Do not polish a blocked concept to make the comparison look balanced.

## 4. Prove creative distinction

Distinctiveness is an outcome gate, not a requirement to add decoration. Mark it `UNKNOWN` until a rendered comparison demonstrates the following:

- The direction is anchored in the product's real object, workflow, data shape, language, audience, or interaction consequence rather than only a trend name.
- One repeatable identity carrier improves recognition, comprehension, or task flow. It may be composition, typography, content framing, data treatment, imagery, material, or interaction; ornament is optional.
- The carrier has a written repetition boundary and does not appear on every surface.
- The hierarchy remains intentional when the logo, gradient, glow, shadow, and decorative layer are temporarily removed.
- The result cannot be reduced to a centered headline, gradient word, floating mockup, equal icon-card grid, or default component library with new colors, fonts, and radii.
- An established product retains recognizable equity unless the authorized scope explicitly replaces it.

Use the product-specific noun test: describe why the direction belongs to this product without relying only on adjectives such as modern, clean, premium, bold, or futuristic. Use the subtraction test to remove one decorative layer at a time and restore only what materially strengthens hierarchy, meaning, brand recognition, or feedback.

Do not force novelty when familiar platform composition best serves the task. In that case, product language, information architecture, typography, or interaction detail can carry the distinction.

## 5. Select without averaging

- Eliminate unresolved blockers before comparing aesthetic potential.
- Treat unknown evidence as risk, not as a pass.
- Prefer the direction that makes the primary task clearest while producing the strongest product-specific identity inside the real constraints.
- Use novelty only as a tiebreaker after usability, coherence, brand fit, and feasibility survive.
- Synthesize candidates only when their contributions are compatible and can be restated as one new thesis. Do not average colors, radii, motifs, and layouts into a compromise collage.
- Request a user decision when equally viable options imply materially different brand positions or business trade-offs. Continue autonomously only with reversible details.

Record why the chosen direction won and why the strongest rejected direction lost. Keep this rationale concise and evidence-based; do not expose private chain-of-thought or manufacture an internal debate transcript.

## 6. Freeze an implementation contract

Before building, record:

- Selected thesis and desired perception
- Dominant composition and primary focal point
- Signature device and where it may repeat, or the decision not to add one
- Required type, color, shape, icon, imagery, and motion rules
- Existing repository conventions to preserve and evidence-backed deviations approved within scope
- Explicit forbidden defaults for this product
- Representative content and states to preserve
- Target viewports, themes, input modes, and accessibility modes
- Known unknowns and reversible assumptions
- Product-specific identity carrier, its purpose, and its repetition boundary
- Typography role contract, required scripts, real-content stress set, actual font evidence, and fallback behavior
- Scoped effect and geometry exceptions; permission for one hero, brand, data, illustration, CTA, native, or semantic role must not propagate to unrelated surfaces or controls

Treat the contract as a drift boundary. Change it only when new evidence appears or the user changes the brief. Do not let implementation convenience silently replace the selected direction.

## 7. Critique the rendered result

Compare the real render with both the product task and the implementation contract.

Use a bounded critic loop:

1. Capture the functionally correct render with representative real content at compact, intermediate, and wide sizes. Include applicable focus, selected, disabled, loading, empty, error, success, overflow, theme, zoom or text-scaling, high-contrast, and reduced-motion evidence.
2. For refinement work, place the current baseline beside the candidate at identical content, state, viewport, and theme.
3. Run one full critic pass across composition, typography, density, and noise or identity. Inspect focal order, alignment axes, grouping, wrapping, font and fallback metrics, visible control geometry, hit areas, card nesting, pills, icon containers, source coherence, glow, gradients, and template resemblance.
4. Record only evidence-visible findings as `severity | viewport/state | visible evidence | task or system consequence | correction | verification`.
5. Use `BLOCKER` for requirement, accessibility, content, or task failure; `MAJOR` for clear hierarchy, coherence, responsive, or identity harm; `MINOR` for local polish; and `UNKNOWN` when required evidence is absent.
6. Apply the smallest coherent correction set that resolves blockers and majors without reopening the entire direction.
7. Rerender the same evidence set and verify the recorded findings. This is targeted verification, not another unrestricted taste pass.

Use one full critic pass by default. Run another full pass only when a correction materially changes composition or a blocker or major remains. Stop when the selected task, contract, and quality gates are satisfied; disclose missing evidence. Do not use pixel-delta scoring as a quality verdict, tweak roulette, or endless screenshot churn.

## 8. Record the decision

Use this compact record in working notes or delivery when the choice matters:

```text
Art-direction mode: <direct | refinement | full>
Chosen direction: <name and thesis>
Why it won: <task, product, and evidence-based reason>
Strongest rejected direction: <name and decisive weakness>
Blockers resolved: <items or none>
Unknowns retained: <items and reversible fallback>
Implementation contract: <optional signature + preserved conventions + approved deviations + non-negotiables + forbidden defaults>
Rendered evidence: <viewports, states, themes, accessibility modes>
Project memory: <confirmed project-wide decisions added or superseded, or none>
```

Do not force this entire record into a terse user response. Preserve it internally or in the project design-system artifact and report only decisions, evidence, and remaining risk that help the user. When `PROJECT-MEMORY.md` exists, preserve confirmed entries; write generated directions as `PROPOSED`, and add or supersede a project-wide decision only with user confirmation, verified repository or brand evidence, or an accepted rendered result.

## 9. Avoid false rigor

- Do not let the same prose generate a concept, praise it, and call that validation.
- Do not disguise three cosmetic variants as exploration.
- Do not let a familiar repository style or the first plausible external reference terminate exploration before every relevant direction class is represented or explicitly excluded.
- Do not score taste numerically without measured user or business data.
- Do not cite trends, competitor aesthetics, or generated search rankings as proof of product fit.
- Do not confuse the removal of bad defaults with a distinctive identity; add one product-specific visual idea.
- Do not postpone critique until after a complete implementation when the direction itself is still uncertain.
- Do not reject an established, effective system merely because a fresh concept appears more novel.
- Do not claim a render was reviewed when only source code was inspected.
- Do not treat screenshot pixel difference as design quality; inspect the semantic and visual consequence of the difference.
- Do not repeat a full critic pass when targeted rerender evidence has already resolved every blocker and major.
