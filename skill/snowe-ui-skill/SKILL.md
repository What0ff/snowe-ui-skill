---
name: snowe-ui-skill
description: Professional UI/UX design, implementation, refactoring, and review for web, mobile, and desktop products. Use when Codex must create or improve pages and components, establish or critique a visual direction or design system, explore relevant external alternatives before material design decisions, choose layout, typography, color, shape, iconography, imagery, motion, or control density, select and install a justified icon source, implement responsive and accessible interfaces, audit usability or perceived quality, or retrieve stack-specific UI guidance. Includes evidence-based exploration, art-direction and creative-distinction gates, content- and script-aware typography direction, searchable datasets, deterministic design-system generation, durable project design memory, bounded rendered critique, and guardrails against decorative pill/capsule overuse, oversized controls, generic icon metaphors, and AI-blue/cyan/violet neon or glow as the default identity.
---

# Snowe UI Skill

Create interfaces that are coherent, distinctive, accessible, and grounded in the real product context. Treat bundled search results as decision support, not as permission to overwrite repository conventions or platform behavior.

## Operating Contract

- Inspect the repository, current UI, component library, tokens, brand assets, target platforms, and real content before proposing a direction.
- If `design-system/<project>/PROJECT-MEMORY.md` exists, read its `CONFIRMED` decisions before material UI work and verify them against the current repository and brief. Never overwrite confirmed memory with generated defaults.
- Preserve an established design system by default. Correct accessibility, semantic, consistency, or task-level defects that are inside the requested scope without turning them into an unsolicited redesign.
- Match the requested scope: review without mutation for review tasks; implement and verify for build or change tasks.
- Base claims on rendered evidence, source code, official assets, measured values, or cited platform standards. Do not invent brand rules, user research, or test results.
- Prefer semantic or native controls and the repository's existing components over unnecessary custom primitives.
- For every material decision, search the full relevant option space through [exploration-protocol.md](references/exploration-protocol.md) before committing. Treat repository, platform, brand, installed-package, and current-token choices as the baseline, not the search boundary. Compare concrete external challengers on identical real content, rank semantic and visual quality first, and apply dependency, license, performance, migration, and maintenance cost only afterward.
- Do not turn this into infinite churn: preserve confirmed invariants and learned or native routine decisions, declare the relevant candidate universe, and stop at evidence saturation after every applicable class is covered. A catalog, package, font, trend, or moodboard list without same-context finalist evidence does not close exploration.
- Treat installed icon packages as evidence and a migration baseline, not a closed allowlist.
- Use broad cross-library exploration by default for every non-universal product, domain, navigation, status, or signature icon; also enter it whenever the user asks to inspect other libraries, expand the pool, find the best available glyph, or rejects the current candidates. Reserve routine primary-source lookup for confirmed learned universal actions with clear coherent coverage. Do not finalize after finding a strong installed glyph: inspect concrete candidates from at least three relevant uninstalled families when available and render at least two external finalists beside the installed baseline at the same size and in the same UI context. A catalog skim or package-name list is not a comparison. Rank semantic and visual quality before applying dependency, lockfile, bundle, migration, or maintenance cost.
- During authorized implementation work, install the strongest justified package-based adapter or integrate the selected official native or asset source when it passes the source and dependency gates; do not mutate dependencies during review-only work or acquire every candidate speculatively.
- Make one coherent visual decision at a time. Avoid mixing unrelated trends, icon families, radius systems, or motion languages.
- Separate invariants from defaults and heuristics. Accessibility, semantics, content integrity, verified brand rules, and explicit product constraints are invariants. Package counts, class names, exact pixel ranges, raw hue names, numbers of cards or fonts, and preferred visual recipes are diagnostic signals—not automatic pass/fail rules.
- Judge rendered behavior and visual coherence before implementation proxies. Permit a documented platform, brand, content, or task exception when it produces the stronger outcome without weakening an invariant.

## Route the Work

- For every material choice in direction, composition, typography, iconography, color or material, component behavior, imagery, motion, or data visualization, read [exploration-protocol.md](references/exploration-protocol.md) first and retain its Explore → Compare → Commit phase order.
- For a new page, product, redesign, or unresolved visual identity, read [design-foundations.md](references/design-foundations.md) and [art-direction-gate.md](references/art-direction-gate.md), inspect the project, then compare and critique design hypotheses and prove a product-specific identity carrier before selecting one.
- For an existing UI review or polish pass, read [quality-gates.md](references/quality-gates.md), inspect the rendered UI, and search only the relevant domains.
- For a material visual change inside an established product, read [art-direction-gate.md](references/art-direction-gate.md) and use the current interface as the comparison baseline.
- For typography, shape, control, or visual-hierarchy work, read the relevant sections in [design-foundations.md](references/design-foundations.md). Typography decisions require representative content, required-script coverage, font-file and fallback evidence, and rendered metrics—not a font-name pairing alone.
- For icon selection, replacement, source choice, package acquisition, custom SVGs, or icon QA, read [iconography-system.md](references/iconography-system.md). Choose its routine or broad exploration mode before searching. Query `icon-concepts` whenever the metaphor is unresolved; query `icon-families` to compare installed and uninstalled families; then query `icon-candidates` one source at a time after the role and metaphor are fixed, using `<family> <real subject> <mechanism/output>`. In broad mode, repeat concrete searches and rendered comparisons until the exploration-closure gate passes; an acceptable installed result does not end that search.
- For CLI options, domains, stacks, persistence, or query construction, read [cli-reference.md](references/cli-reference.md).
- For accessibility or target-size claims, use [quality-gates.md](references/quality-gates.md) and preserve the distinction between web conformance and platform recommendations.

## Workflow

Before the domain workflow below, declare the relevant option universe and open an exploration ledger for every material decision. Search outside the repository by default, render the strongest relevant challengers on the same real content, close exploration, and only then apply implementation economics. Do not reopen accepted invariants or benchmark unchanged routine tokens.

### 1. Establish the Product Truth

Identify:

- Primary user and task
- Product type and information density
- Platform and input modes
- Existing brand and design-system constraints
- Required content and states
- Technical stack and component library
- Accessibility, localization, performance, and delivery constraints
- Confirmed project-memory decisions, their scope, evidence, and revisit triggers when memory exists

If critical context is absent, infer only reversible visual details. Do not fabricate product requirements.

### 2. Select the Direction Through an Art-Director Gate

Choose the smallest review mode that matches the decision:

- For a narrow fix or state addition, execute inside the current system and run a compact fit check.
- For polish or extension of an established interface, compare the current baseline with one focused refinement hypothesis.
- For a new product, redesign, or unresolved identity, create two direction cards and add a third only when it represents another material product trade-off; then run the full gate in [art-direction-gate.md](references/art-direction-gate.md).

Keep every candidate on the same real content, user task, functional requirements, and platform constraints. Make full-gate candidates differ structurally rather than presenting palette, radius, or icon swaps.

Critique each applicable direction with `PASS`, `BLOCKER`, `UNKNOWN`, or `N/A` across product fit, task hierarchy, information architecture, content resilience, system coherence, distinctiveness, brand provenance, accessibility feasibility, platform fit, implementation feasibility, and the visual guardrails. Put exactly one of those tokens in the status field and record caveats separately; never invent `PASS with risk` or another softened status. Reserve `BLOCKER` for a violated requirement or outcome-level harm, not a heuristic count. Do not use numeric taste scores or silently turn missing evidence into a pass.

Eliminate unresolved blockers, select one coherent direction, and record why it won and why the strongest alternative lost. Synthesize only compatible ideas that can be restated as one thesis; do not average unrelated concepts. Ask for a user decision only when equally viable directions imply materially different brand or business positions.

State the selected compact design thesis before implementation:

- Desired perception
- Primary visual direction and one supporting influence
- Dominant composition and focal point
- Type, color, shape, icon, imagery, and motion approach
- One product-specific signature device when it improves recognition, or an explicit decision that content, typography, and composition carry the identity without added ornament
- Explicit anti-patterns for this product

Prove creative distinction without manufacturing decoration: derive one repeatable identity carrier from the product's real objects, workflow, data, language, or audience; define where it may repeat; and run a subtraction test. The interface must still have intentional hierarchy when the logo, gradient, and decorative layer are temporarily removed. An ownable move may be composition, typography, content behavior, data treatment, imagery, or interaction; ornament is optional.

When no reliable design system exists, generate a starting hypothesis:

```text
python <skill-directory>/scripts/search.py "<product audience task tone density platform>" --design-system --format markdown --project-name "<name>"
```

Treat generated retrieval as one input to the gate, not as proof that a direction is correct. Use the optional `--variance`, `--motion`, `--density`, and `--roundness` dials only when they express a real product decision. Even `--roundness 10` does not permit generic pill-shaped controls.

### 3. Resolve the System Before Components

Define or reuse:

- Semantic color roles and verified foreground/surface pairs
- Role-based type scale and content measure
- Required scripts, actual font files and weights, fallback metrics, numeral behavior, and localization stress content
- Spacing, grid, gutters, and responsive behavior
- Component-specific radius tokens
- Surface and elevation hierarchy
- Icon family, visible size, and hit-target strategy
- Icon roles and metaphors, including explicit anti-cliche decisions for product and domain concepts
- Motion tokens and reduced-motion behavior
- Component roles and state coverage

Fix any generated `ADJUST` contrast result before delivery or document why the pair is not used for normal text.

### 4. Implement in the Existing Architecture

- Freeze a compact implementation contract from the selected direction: thesis, dominant composition, optional signature device, preserved repository conventions, approved deviations, non-negotiables, forbidden defaults, representative content and states, and target viewports or devices.
- Query the actual stack when implementation guidance is needed:

```text
python <skill-directory>/scripts/search.py "<concern>" --stack <stack> --max-results 5
```

- Extend existing tokens and variants instead of scattering one-off values.
- When the selected package-based icon source is not installed, verify the current official package, compatible version, license, framework support, bundle behavior, and maintenance; detect the repository package manager from metadata and lockfiles; install only the selected runtime adapter so the manifest and lockfile update together; then integrate it through a documented source role and shared wrapper. For native symbols, fonts, or official assets, use the platform-supported integration and availability checks. Acquisition is a normal implementation step for an authorized build/change task and does not require a separate installed-only fallback.
- Do not acquire a package for a review, audit, or direction-only task. Do not add several libraries for comparison, hand-edit dependency versions when the package manager is available, or replace unrelated icons opportunistically.
- Keep structure, behavior, state, and styling responsibilities clear.
- Use real content and representative edge cases while building.
- Include default, hover where supported, pressed, focus-visible, selected, disabled, loading, empty, error, and success states as applicable.
- Preserve keyboard behavior, accessible names, focus order, text scaling or zoom, reduced motion, and theme behavior.
- Use official brand assets. If new imagery is required, obtain or generate it intentionally instead of shipping arbitrary placeholders.

### 5. Render and Iterate

- Run the relevant build, tests, and static checks.
- Inspect the real interface at narrow, intermediate, and wide sizes.
- Compare the render with the selected thesis and implementation contract; for refinement work, compare it with the previous interface baseline as well.
- Exercise interaction states instead of reviewing only the default screenshot.
- Check light and dark themes independently when both exist.
- Inspect hierarchy at thumbnail scale and alignment, wrapping, icon balance, surface nesting, and state contrast at full scale.
- Run one full rendered critic pass across composition, typography, density, noise, and product identity. Record each visible finding as `severity | viewport/state | evidence | consequence | correction | verification`.
- Apply the smallest coherent correction set, then rerender the same evidence set. Treat that rerender as targeted verification rather than a fresh taste pass.
- Run another full critic pass only when a correction materially changes composition or a blocker or major remains. Do not use pixel-delta scoring, tweak roulette, or endless screenshot churn.
- Do not approve perceived quality from code inspection alone. Deliver only after blockers and majors are resolved or explicitly reported as external limitations.

### 6. Report Evidence

Summarize the implemented direction, files changed, checks run, viewport or device coverage, accessibility modes tested, and any remaining limitation. Distinguish executed checks from inferred guidance. Add or supersede a `PROJECT-MEMORY.md` entry only for a project-wide decision that is confirmed by the user, verified repository or brand evidence, or an accepted rendered result; keep generated hypotheses `PROPOSED`.

## Shape Defaults and Exceptions

Apply these defaults across generated guidance and implementation:

- Do not use a pill or capsule as generic decoration.
- Do not use full rounding as the default for buttons, fields, cards, toolbars, or navigation. The presence of `rounded-full`, `999px`, `Capsule`, or an equivalent token is not itself a failure; evaluate the component role and repeated rendered effect.
- Avoid a wide pill behind a standalone icon when it adds decoration but no state, grouping, platform, or brand meaning.
- Avoid a separate pill behind every navigation icon or icon-label item unless the items genuinely behave as compact semantic choices and the repetition preserves hierarchy.
- Preserve the interaction target with transparent padding. Use a compact rounded-square container only when it communicates hover, press, focus, selection, grouping, or elevation.
- Prefer color, weight, underline, side marker, icon fill, or a restrained tonal surface for navigation selection.
- Prefer true pills for semantic chips, tags, filters, statuses, entered entities, and compact choices. Preserve established native or brand controls without requiring special permission, but do not propagate their geometry to unrelated components.
- Use circles for avatars, true FABs, record or media controls, swatches, and established compact icon controls when the silhouette communicates a real role; do not repeat circles as generic chrome.
- If legitimate chips dominate the screen, replace some with a list, menu, checkbox group, tabs, or another behaviorally correct control.
- Do not inflate buttons, fields, selects, segmented controls, or icon containers to make the interface feel important.
- Separate visible geometry from the interaction target: extend the hit area transparently and without overlap when accessibility requires more space.
- For pointer-first desktop, use approximately 32–36px controls in dense workspaces and 36–40px in standard layouts as starting ranges. For touch, separate visible geometry from the platform target. Treat these values as heuristics, not thresholds; content, native components, input mode, density, brand, and measured usability may justify another value.
- Size controls to their content by default. Use full-width or unusually tall actions only when the narrow layout or task flow gives them a clear reason.

Preserve native component geometry when the target platform, repository architecture, or user brief makes native fidelity relevant. Do not copy that geometry to unrelated controls without the same reason.

## Professional Visual Guardrails

- Avoid card soup. Use cards only for independent or actionable groups; use spacing, headings, and dividers for ordinary structure.
- Avoid generic centered hero + identical icon-card grid composition unless the content genuinely calls for it.
- Establish a clear action hierarchy. Use one dominant action when the task has one obvious next step; permit peer actions when the workflow genuinely gives them equal priority.
- Define a primary icon drawing language and a source-role map. Do not count packages as a quality metric: multiple sources can be coherent, while one package can still be inconsistent through mixed weights, fills, sizes, and metaphors.
- Prefer the repository's established interface source for routine additions when it remains the strongest fit. Evaluate installable challengers for weak coverage or a materially stronger product, domain, or platform role; install the selected official adapter after the compatibility and dependency-acquisition gates pass.
- Treat a missing glyph as a decision point, not automatic permission or prohibition. Compare visible text, a compatible auxiliary source, and a repository-owned SVG using recognition and ownership evidence.
- Preserve familiar symbols for universal actions, but make product and domain icons specific to the real object, mechanism, input, output, or consequence.
- For every non-universal product icon, record `real subject → mechanism/output`, explore enough plausible candidates to make a real choice, start with the primary source, and document any source exception plus compatibility evidence.
- Prefer verified named exports from `icon-candidates` over recalled component names, but confirm the installed package version before implementation.
- Treat sparkles, wands, brains, rockets, shields, lightning, globes, puzzle pieces, cubes, generic charts, trophies, stars, and gears as high-cliche-risk symbols. Use them when literal, learned, branded, or demonstrably clearest—not as automatic shorthand for product value.
- When brand evidence is absent, start from a context-derived solid foundation. Do not use generic AI-blue/cyan/violet neon, electric edge light, bloom, glow, or ambient luminous gradients as the default identity.
- Do not reject blue, cyan, violet, a gradient, or a shadow solely by token or hue name. A restrained functional color or evidence-backed brand, domain, data, illustration, or material treatment is valid when hierarchy, contrast, and repetition remain controlled.
- Use accent color, gradients, shadows, blur, and animation selectively and semantically. Avoid readability-damaging text glow, indiscriminate glowing borders, aura blobs, or blue-purple light washes without a brief, brand, genre, or content reason.
- Do not add hover motion to noninteractive surfaces.
- Do not hide essential actions behind hover, swipe, drag, or gesture-only interaction.
- Do not claim accessibility from palette metadata or static screenshots alone.
- Do not disable zoom, remove focus indicators, or truncate essential content to preserve a composition.

## Search Discipline

- Build queries from product, audience, task, tone, density, and platform.
- Run one complete design-system search, then targeted domain searches for unresolved decisions.
- Use `ux`, `web`, `chart`, or stack search for an audit; do not regenerate the visual direction unless redesign is in scope.
- Treat rankings as lexical evidence. Validate semantic and product fit.
- See [cli-reference.md](references/cli-reference.md) for the complete domain and stack inventory.

## Delivery Gate

Before delivering UI work, confirm:

- The applied direction passed the appropriate art-direction mode, and any material unknown or rejected alternative is recorded without fake certainty.
- The primary task and focal point are obvious.
- The result has a product-specific identity carrier that improves recognition, comprehension, or task flow and does not depend on a generic SaaS recipe or compulsory ornament.
- Layout works with real content at intermediate widths.
- Color and focus states are measured or visually verified in the rendered UI.
- Controls have correct semantics, accessible names, and platform-appropriate targets.
- Pills normally belong to legitimate semantic, native, or verified brand roles; a standalone icon does not receive a pill merely as decoration.
- Universal action icons remain recognizable; product icons avoid vague stock metaphors; every icon source has a documented role; and icons that appear together form a coherent rendered drawing language.
- Any requested broad icon search includes a source-by-source candidate record and same-context renders of external finalists; catalog-only review or an early installed-family winner does not satisfy the exploration-closure gate, and integration cost is applied only after semantic and visual ranking.
- Every material font, composition, color or material, component, imagery, motion, and data-visualization choice has the relevant-universe declaration, external challenger evidence, same-context finalist comparison, quality-first ranking, and strongest-rejected rationale required by the exploration protocol.
- Any newly selected icon dependency was verified against current official package and license evidence, installed with the repository package manager, recorded with its role and version, included in build and bundle checks, and rendered beside neighboring icons; rejected candidates were not left installed.
- Typography was rendered with representative content, required scripts, long labels, numeric stress where relevant, and actual fallback behavior; hierarchy survives without clipping or accidental reflow.
- Fixed UI does not cover content or focused controls.
- Motion is purposeful, interruptible, and reduced when requested by the system.
- Empty, loading, error, success, and disabled states are coherent with the system.
- One bounded full critic pass was completed, blocker and major findings were corrected, and the final result was rerendered after the last material change.
- Confirmed project-memory decisions were preserved, scoped exceptions stayed local to their named role, and newly generated hypotheses were not written as facts.
