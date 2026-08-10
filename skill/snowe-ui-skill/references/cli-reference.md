# CLI Reference

Use the search CLI for deterministic retrieval from the bundled UI/UX datasets and for generated design-system foundations.

## Contents

1. Runtime
2. Design-system generation
3. Design dials
4. Persistence
5. Domain search
6. Stack search
7. Query strategy
8. Output interpretation

## 1. Runtime

Run the script with an available Python 3 interpreter:

```text
python <skill-directory>/scripts/search.py "<query>" [options]
```

On systems where the command is named `python3`, substitute `python3`. Prefer an already available project, Codex, or system runtime. Do not install or modify system Python without user authorization.

Inspect supported arguments directly when uncertain:

```text
python <skill-directory>/scripts/search.py --help
```

## 2. Design-system generation

Generate a complete recommendation:

```text
python <skill-directory>/scripts/search.py "B2B analytics dashboard calm precise" --design-system --format markdown --project-name "Ops Console"
```

The result includes:

- Product and landing pattern
- Visual direction and composition
- An art-direction gate that marks generated retrieval as an unverified hypothesis until comparison, critique, and rendered review are complete
- A creative-distinction gate anchored in the product rather than compulsory ornament or a trend label
- Layout and responsive foundation
- Component-specific shape scale
- Restrained pill policy
- Icon source roles, drawing-language compatibility, and component roles
- Semantic color tokens
- Deterministic contrast checks for complete solid-color pairs
- A font-pairing hypothesis, role-based type scale, and content-, script-, metric-, and fallback-aware typography director
- Scoped visual-treatment permissions so a requested hero, brand, data, illustration, or CTA effect does not automatically spread into navigation, fields, cards, or page chrome
- A bounded rendered-critic loop with evidence schema, severity rules, rerender verification, and a stop condition
- A durable project-memory policy with explicit precedence and confirmation states
- An always-on Explore → Compare → Commit protocol for material typography, icon, direction, color or material, component, imagery, motion, and data-visualization decisions
- Motion guidance when requested
- Anti-patterns and delivery gates

Treat search output as a design hypothesis. Reconcile it with the repository, real content, brand constraints, platform conventions, and rendered QA.

## 3. Design dials

All dials accept integers from 1 to 10 and require `--design-system`.

| Option | Low | Middle | High |
|--------|-----|--------|------|
| `--variance` | Centered/minimal | Balanced | Bold/asymmetric |
| `--motion` | Subtle | Standard | Complex |
| `--density` | Spacious | Standard | Dense/dashboard |
| `--roundness` | Sharp/editorial | Balanced/professional | Soft/expressive |

Example:

```text
python <skill-directory>/scripts/search.py "creative project workspace" --design-system --variance 7 --motion 4 --density 6 --roundness 5 --format markdown
```

`--roundness 10` does not enable pills everywhere. It selects the soft profile while full rounding normally belongs to semantic chips, tags, filters, statuses, entered entities, genuinely circular controls, or established native and brand components. Judge exceptions by role and rendered repetition.

## 4. Persistence

Persist a project master file:

```text
python <skill-directory>/scripts/search.py "healthcare scheduling app" --design-system --persist --project-name "Care Flow" --output-dir <project-directory>
```

This writes:

```text
<project-directory>/design-system/care-flow/MASTER.md
<project-directory>/design-system/care-flow/PROJECT-MEMORY.md
```

`MASTER.md` contains regenerated working defaults and may be replaced by a later `--persist` run. `PROJECT-MEMORY.md` is initialized only when absent and is then preserved byte-for-byte by the generator. Read confirmed memory before `MASTER.md` when making material decisions.

Add a page override:

```text
python <skill-directory>/scripts/search.py "healthcare scheduling appointment calendar" --design-system --persist --project-name "Care Flow" --page "appointments" --output-dir <project-directory>
```

This also writes:

```text
<project-directory>/design-system/care-flow/pages/appointments.md
```

Page files override page-level details only. Accessibility, semantics, and required content remain project-wide invariants. Shape and density defaults may vary when a page role, native component, verified brand rule, or rendered usability evidence justifies the exception and the override records it.

Use this precedence order:

```text
current explicit requirements and verified repository/brand evidence
> CONFIRMED project memory
> scoped page overrides
> MASTER defaults
> generated hypotheses
```

Memory statuses are `PROPOSED`, `CONFIRMED`, and `SUPERSEDED`. Add or supersede a project-wide entry only with user confirmation, verified repository or brand evidence, or an accepted rendered result. Include scope, evidence, owner/source, and revisit trigger. Do not store experiments, generated taste claims, or private reasoning as confirmed facts.

`--page` and `--output-dir` require `--persist`.

## 5. Domain search

```text
python <skill-directory>/scripts/search.py "<query>" --domain <domain> --max-results 5
```

Available domains:

| Domain | Use |
|--------|-----|
| `product` | Product-type patterns and concerns |
| `style` | Visual directions, effects, implementation cues |
| `color` | Semantic palettes by product context |
| `typography` | Font pairings and loading details |
| `google-fonts` | Font metadata and subsets |
| `landing` | Landing-page structure and CTA strategy |
| `chart` | Chart selection, limitations, accessibility |
| `ux` | General UX issues, do/don’t guidance, severity |
| `icons` | Familiar system-icon name lookup in the legacy concrete catalog |
| `icon-concepts` | Role-first metaphor choices and anti-cliche alternatives |
| `icon-families` | Curated family, platform, package, character, and license comparison |
| `icon-candidates` | Verified concrete glyph names and import hints after family and metaphor are fixed |
| `gsap` | Motion patterns by intensity |
| `react` | React and Next.js performance guidance |
| `web` | App-interface and accessibility guidance |

Use `--json` only for domain or stack searches when structured output is useful:

```text
python <skill-directory>/scripts/search.py "focus keyboard" --domain ux --json
```

Icon examples:

```text
python <skill-directory>/scripts/search.py "automation workflow" --domain icon-concepts --max-results 5
python <skill-directory>/scripts/search.py "dense technical dashboard" --domain icon-families --max-results 5
python <skill-directory>/scripts/search.py "Lucide invoice extraction scan text" --domain icon-candidates --max-results 5
python <skill-directory>/scripts/search.py "delete" --domain icons --max-results 3
```

`icon-candidates` requires exactly one supported family per query and returns only that source. Repeat the lookup across sources when comparison is needed. This retrieval boundary keeps results auditable and is neither a one-package rule nor an installed-only rule. When the user explicitly asks for other libraries, a wider pool, or the best available glyph, repeat concrete lookups and same-context renders until the broad exploration-closure gate in [iconography-system.md](iconography-system.md) passes. An installed winner or catalog-only scan cannot stop that search; use the dependency-acquisition gate only after semantic and visual ranking.

## 6. Stack search

```text
python <skill-directory>/scripts/search.py "<implementation concern>" --stack <stack> --max-results 5
```

Available stacks:

```text
react, nextjs, vue, svelte, astro, swiftui, react-native, flutter,
nuxtjs, nuxt-ui, html-tailwind, shadcn, jetpack-compose, threejs,
angular, laravel, javafx, wpf, winui, avalonia, uno, uwp
```

Examples:

```text
python <skill-directory>/scripts/search.py "accessible dialog focus management" --stack react
python <skill-directory>/scripts/search.py "large list navigation accessibility" --stack react-native
python <skill-directory>/scripts/search.py "responsive data grid theming" --stack javafx
```

Use the actual repository stack. Do not assume React Native or any other framework from the skill alone.

## 7. Query strategy

Use concrete multidimensional queries:

```text
product + audience + task + tone + density + platform
```

Good:

```text
fleet maintenance dashboard dispatchers high-density calm industrial desktop
```

Weak:

```text
modern app
```

For a new surface:

1. Run `--design-system` once with a precise query.
2. Inspect the result against repository and brand evidence.
3. Run targeted domain searches only for unresolved decisions.
4. Run the stack search for implementation-specific guidance.
5. Implement and visually validate the result.

For an audit, search the relevant `ux`, `web`, `chart`, or stack domain instead of regenerating the product direction unless the user requested a redesign.

## 8. Output interpretation

- `PASS` contrast checks apply only to the listed solid-color pair.
- `ADJUST` means the token pair must be corrected or reserved for a role with a different requirement.
- Missing contrast checks mean the palette did not provide a complete parseable solid-color pair; measure the rendered result.
- Search ranking is lexical and advisory. Validate semantic fit before implementation.
- Bundled search results seed the candidate universe but never define its outer boundary. For material choices, continue through current authoritative sources, compare finalists on identical real content, and apply implementation economics only after the semantic and visual ranking required by [exploration-protocol.md](exploration-protocol.md).
- Package count, class names, exact pixel values, raw hue names, and element counts are diagnostic signals rather than automatic quality failures. Judge the rendered role and outcome.
- Icon family results may name sources absent from the current manifest. Installed packages are the baseline, not a closed allowlist; for a build or change task, verify the current official adapter, version, license, compatibility, bundle behavior, and maintenance, then install the selected winner with the repository package manager and update the lockfile. Do not mutate dependencies for review-only work or install the comparison set speculatively.
- For broad icon exploration, package names and catalog visits are not candidate evidence. Record exact glyphs from independent sources and render the strongest external finalists beside the baseline before applying dependency or migration cost.
- Style results are normalized by the global restrained-shape policy so historical `999px`, `rounded-full`, and generic pill-button advice does not become implementation guidance.
- Preserve platform-native geometry when the target platform, repository architecture, or brief makes native fidelity relevant; do not copy it to unrelated roles without the same reason.
- A positive effect request is role-scoped. For example, a verified gradient in a campaign hero does not authorize gradient CTAs, active tabs, fields, cards, navigation, or a cool-washed product foundation unless those roles are separately supported.
- Typography output remains `UNKNOWN` until the actual font files or dependency, required scripts, representative content, fallback metrics, and rendered behavior are inspected.
- The rendered critic uses one full pass by default and a targeted rerender to verify fixes. Run another full pass only after a material compositional change or while a blocker or major remains; screenshot pixel difference is evidence of change, not a quality score.
