# Iconography System

Use this reference when selecting, replacing, implementing, or reviewing interface icons. The objective is recognizable interaction, product-specific metaphors, and coherent rendered drawing languages with explicit source roles—not a particular dependency count or novelty in every control.

## Contents

1. Decision order
2. Familiarity versus distinctiveness
3. Anti-cliche metaphor map
4. Family pool
5. Exploration closure gate
6. Source roles and compatibility
7. Dependency acquisition gate
8. Custom SVG gate
9. Size, alignment, and containers
10. Accessibility and meaning
11. Visual QA

## Decision Order

1. Inventory the repository before selecting a family:
   - Search package manifests, imports, icon wrappers, asset folders, design tokens, and native-symbol usage.
   - Record every existing source, wrapper, assigned role, size, stroke or fill policy, color behavior, license, and migration state.
   - Identify the likely primary interface drawing language. Preserve coherent existing sources by default, but correct accidental source mixing or inaccessible behavior inside scope without requiring a full redesign.
   - Treat dependency count as inventory, not a quality score. Several sources may be correct when they serve stable roles; one package may still be visually inconsistent.
   - Treat the manifest as the current baseline, not a closed allowlist. Keep installable families in the comparison when they may materially improve recognition, domain coverage, platform fidelity, or product voice.
2. Classify the role:
   - Universal action or navigation
   - Status or feedback
   - Data view
   - Product or domain concept
   - Brand or provider
   - Decorative or illustrative
3. Choose the metaphor before the glyph:
   - Universal actions should use learned platform symbols.
   - For every product concept, write `real subject → mechanism/output` before searching. For automation, name the actual trigger, transformation or output, and destination.
   - Product concepts should map the real object, input, output, mechanism, or consequence.
   - If no symbol is clear, use a visible text label. An icon is optional.
4. Choose the exploration mode before looking at glyphs:
   - **Routine:** use only for a confirmed learned universal action such as close, search, back, disclosure, delete, upload, or download when the established source has clear, coherent coverage.
   - **Broad cross-library:** use by default for every non-universal product, domain, navigation, status, or signature icon. It is also mandatory when the user asks for other or new libraries, a wider pool, the best available icon, or rejects the current set; keep it broad when primary coverage is weak, the candidate is a high-cliché shortcut, or the metaphor remains unresolved.
5. Complete the exploration-closure gate below before naming a winner in broad mode. A strong installed candidate, lower dependency cost, or a quick catalog skim cannot terminate discovery.
6. Rank candidates in two phases. First compare semantic specificity, recognition, silhouette, detail, optical balance, and drawing-language fit without penalizing installation state. Only after that ranking apply source compatibility, license, bundle, migration, maintenance, and lockfile cost. A proven legal or platform incompatibility may eliminate a source earlier, but package newness alone may not.
7. If primary-source coverage remains weak, compare visible text, a compatible auxiliary source, and a custom SVG through the source-compatibility and custom-icon gates below.
8. For authorized build or change work, install the selected official source when it wins the dependency-acquisition gate. For review or direction-only work, record the recommendation without changing dependencies.

Use this compact decision record for every non-universal product icon:

```text
real subject → mechanism/output | role | primary drawing language | candidates considered | chosen metaphor and why | source and exception role if any | compatibility evidence | label requirement
```

After the role and metaphor are fixed, retrieve verified named candidates one source at a time:

```text
python <skill-directory>/scripts/search.py "Lucide invoice extraction scan text" --domain icon-candidates --max-results 5
python <skill-directory>/scripts/search.py "Tabler route logistics handoff" --domain icon-candidates --max-results 5
python <skill-directory>/scripts/search.py "Hugeicons scatter relationship distribution" --domain icon-candidates --max-results 5
```

The candidate registry is a verified snapshot, not permission to skip repository inspection. Confirm that the named export exists in the installed version or in the current official version selected for acquisition before implementation.
The `icon-candidates` domain requires exactly one supported family per lookup and filters every result to it. Repeat the lookup for another justified source when comparison is needed. This keeps retrieval results auditable; it is not a rule that the repository may contain only one package.

Useful repository checks:

```text
rg -n "lucide|phosphor|tabler|iconoir|remixicon|heroicons|radix-ui/react-icons|material-symbol|systemName|hugeicons" package.json pnpm-lock.yaml yarn.lock package-lock.json src app
rg --files | rg "(^|/)(icons?|assets?)/|\.svg$"
```

Adapt paths to the repository. Do not install every detected family or treat a transitive dependency as an intentional source. First map actual imports and rendered roles.

## Familiarity Versus Distinctiveness

Keep these conventional unless the platform already defines another learned symbol:

- Search, close, back, forward, disclosure, delete, add, remove, play, pause, upload, and download
- Common text formatting and media transport controls
- Native window controls and platform-specific navigation

Create distinctiveness in these areas:

- Product navigation destinations
- Domain objects and workflows
- Feature entry points
- Empty-state or onboarding illustration motifs
- A small set of reusable custom compound symbols

Do not make a common destructive or navigation action harder to recognize in pursuit of visual originality.

## Anti-Cliche Metaphor Map

The following symbols are not forbidden and are not required to be literally physical. Treat them as high-cliche-risk: use them when they are literal, learned for the action, established by the brand or platform, or demonstrably clearer than the alternatives. Do not use them as automatic shorthand for product value.

| Concept | Avoid as default | Prefer |
|---|---|---|
| AI or assistant | Sparkles, magic wand, brain, generic robot head | The capability or output: compose, extract, classify, translate, summarize, route |
| Automation | Wand, sparkles, lightning, lone gear, one generic workflow glyph reused everywhere | The named trigger, transformation/output, and destination; for example invoice received → fields extracted → approval queue |
| Launch or release | Rocket, confetti | Version tag, package, deployment path, staged rollout, publish action |
| Growth | Rocket, plant sprout, generic rising chart | The actual KPI, cohort, acquisition path, retention curve, expanding range |
| Performance | Lightning, flame | Latency trace, stopwatch, gauge, frame timeline, throughput lanes |
| Security | Shield on every feature | Key, lock, identity, fingerprint, firewall, audit trail—the actual mechanism |
| Trust | Shield-check or badge without evidence | Verified credential, signed record, agreement, provenance, audit source |
| Global | Generic globe | Translation, time zone, region nodes, route map, locale |
| Integrations | Puzzle piece | Connector, plug, linked nodes, webhook, official provider mark |
| Platform | Layers or floating cubes | Workspace modules, runtime boundary, API surface, component graph |
| Analytics | Same chart-up icon everywhere | The real view: line, bars, funnel, scatter, table |
| Data | Database cylinder everywhere | Records, table, schema, document set, event stream, warehouse |
| Community | Generic three-person silhouette | Discussion, event, directory, collaboration cursors, shared workspace |
| Achievement | Trophy, star, crown | Certificate, checkpoint, completed route, verified skill, streak calendar |
| Settings | Gear on every management page | Sliders, wrench, key, switches, or the specific configuration object |

For detailed search results:

```text
python <skill-directory>/scripts/search.py "automation workflow" --domain icon-concepts --max-results 5
python <skill-directory>/scripts/search.py "security identity" --domain icon-concepts --max-results 5
```

## Family Pool

Repository-native is the first baseline, not an installation boundary. Compare candidates appropriate to the platform and product whenever the existing source is unclear, visually incompatible, or materially weaker for the required domain role; choose the strongest primary or auxiliary source before implementation.

| Family | Character and strong use | License note |
|---|---|---|
| [Lucide](https://lucide.dev/) | Disciplined geometric outline for general product UI and familiar actions | ISC |
| [Phosphor](https://phosphoricons.com/) | Multiple weights, fill, and duotone within one flexible system | MIT |
| [Tabler Icons](https://tabler.io/icons) | Broad technical and specialist coverage on a precise 24px system | MIT |
| [Iconoir](https://iconoir.com/) | Distinctive monoline vocabulary for product navigation and creator or data tools | MIT |
| [Remix Icon](https://www.remixicon.com/) | Neutral 24px outlined and filled pairs for content-rich products | Remix Icon License v1.0 |
| [Radix Icons](https://www.radix-ui.com/icons) | Compact crisp 15px glyphs for dense web toolbars and inspectors | MIT |
| [Heroicons](https://heroicons.com/) | Restrained outline and solid variants for conventional Tailwind-oriented UI | MIT |
| [Material Symbols](https://developers.google.com/fonts/docs/material_symbols) | Material-native variable fill, weight, grade, and optical-size behavior | Apache-2.0 |
| [SF Symbols](https://developer.apple.com/sf-symbols/) | Native Apple symbols, text alignment, localization, weights, and rendering modes | Apple terms; check OS availability and trademark restrictions |
| [Hugeicons](https://hugeicons.com/docs/) | Broad free rounded-stroke coverage for domain objects and activities | Hugeicons terms; verify the current tier and do not redistribute raw assets |

Search the local registry for package and fit details:

```text
python <skill-directory>/scripts/search.py "dense technical dashboard" --domain icon-families --max-results 5
python <skill-directory>/scripts/search.py "native Apple toolbar" --domain icon-families --max-results 5
python <skill-directory>/scripts/search.py "consumer activities broad catalog" --domain icon-families --max-results 5
```

Catalog size, package names, and license terms can change. Verify the official source before adding a dependency or redistributing assets.

The local named-candidate pool contains concrete exports for Lucide, Tabler Icons, Iconoir, Phosphor, Radix Icons, Remix Icon, and Hugeicons Free. Material Symbols and SF Symbols remain platform catalogs whose availability must be checked against the target platform version rather than frozen into a cross-platform export list.

## Exploration Closure Gate

Use this gate whenever broad cross-library mode is active. It measures whether the search was completed; it does not force novelty or require a new dependency to win.

1. **Declare the eligible pool.** Start with every platform- and role-relevant family in the bundled registry, then use current official catalogs or authoritative registries when the local snapshot lacks the subject. Do not treat the bundled pool as exhaustive.
2. **Inspect concrete glyphs across sources.** Include the installed baseline plus named candidates from at least three relevant uninstalled families when that many viable families exist. Search real nouns, verbs, mechanisms, outputs, and close synonyms. A family name or catalog landing page without a concrete glyph is not evaluated evidence.
3. **Account for sparse coverage.** If fewer than three external families expose a viable glyph, record the official source searched, exact terms, and the no-result or incompatibility evidence for each missing slot. Do not silently reduce the pool.
4. **Render external finalists.** Render the strongest candidate from at least two uninstalled families beside the installed baseline with identical visible size, color, surrounding label, state, and surface. Use official SVGs or a temporary comparison sandbox for review-only work; do not add comparison packages to the repository.
5. **Record the matrix.** Capture `family | exact glyph/export | official source | metaphor | rendered at target size | semantic/visual finding | advance/reject reason`. Catalog browsing without an exact same-context render remains discovery, not comparison.
6. **Close discovery before integration economics.** Produce the semantic and visual ranking first. Then apply drawing-language compatibility, license, bundle, migration, maintenance, and dependency cost. The installed source may still win, but only after this evidence exists.

For routine mode, do not manufacture a broad benchmark for a confirmed learned universal action with coherent primary-source coverage. Every non-universal icon starts broad; no user reminder is required.

## Source Roles and Compatibility

Use a primary interface drawing language as the default, not a one-package or installed-only law.

Multiple sources are valid when they serve explicit, stable roles such as:

- Routine interface actions and navigation
- Native operating-system controls or platform-owned surfaces
- Current official brand and provider marks
- Specialized domain objects whose recognition materially improves
- Repository-owned product symbols or illustration
- A documented staged migration where old and new sources do not alternate arbitrarily

Before adding or retaining an auxiliary source, pass this compatibility gate:

1. Name its role and where that role begins and ends.
2. Verify that primary-source coverage is genuinely weaker for the use case; a missing glyph alone is evidence to investigate, not an automatic decision.
3. Compare grid, stroke or fill behavior, caps, joins, corner language, detail level, negative space, baseline, and optical weight in the real surface.
4. Normalize visible size, color, alignment, accessible naming, and state behavior through a shared wrapper. Do not distort internal geometry merely to fake sameness.
5. Verify license, provenance, installed-version support, asset or bundle cost, tree shaking where applicable, and maintenance ownership.
6. Document the source-role map and remove accidental duplicates.

Fail the rendered result when icons used together are visually or semantically inconsistent, not merely because more than one package exists. Conversely, do not pass a surface merely because every glyph came from the same package.

Run `icon-candidates` separately for each source under consideration. Keep the source name in the query so every result remains auditable.

## Dependency Acquisition Gate

For an authorized implementation, build, refactor, or change task, installing the selected icon dependency is a normal scoped implementation action. Do not stop merely because the strongest source is absent from the manifest. For review, audit, or direction-only work, recommend the dependency without mutating the repository. In broad mode this gate begins only after the exploration-closure gate produces a semantic and visual ranking; do not use bundle, lockfile, or migration cost to justify an incomplete search.

Install only when the candidate wins on the required role, recognition, drawing-language fit, platform support, accessibility behavior, license, asset or bundle cost, and maintenance. A new source is justified when the installed sources remain materially weaker after real candidate comparison; one missing glyph alone starts the investigation but does not decide it.

Use this sequence:

1. **Verify the current official source.** Use the official documentation and authoritative package registry to confirm the exact adapter, current compatible version, license or usage terms, exports, release or maintenance state, and framework or platform support. Package details change; do not rely on memory or the local snapshot alone.
2. **Detect the repository package manager.** Read `packageManager`, workspace configuration, and lockfiles. Preserve the existing manager, version, registry configuration, and workspace placement.
3. **Select before installing.** Compare candidates from the registry or official catalog, then install only the winner. Do not add the whole shortlist to create a local contact sheet.
4. **Install through the package manager.** Add the official stack adapter as a runtime dependency so the manifest and lockfile update together. Do not hand-edit a guessed version when the package manager can resolve it.
5. **Integrate behind a role boundary.** Add or extend a shared icon wrapper, document the new source role, use named or tree-shakable imports where supported, and migrate only the approved role. Do not turn one successful glyph into an unsolicited library-wide replacement.
6. **Verify the repository.** Run its dependency integrity, build, type or static, tests, and bundle checks. Render the selected icons at their actual sizes beside neighboring sources in applicable default, selected, disabled, light, dark, and high-contrast states.
7. **Record the decision.** Capture `source | role | package | installed version | license/provenance | why installed sources lost | bundle/loading model | wrapper | rendered compatibility | owner`. Promote the source role to confirmed project memory only after repository and accepted render evidence support it.
8. **Roll back a failed acquisition.** If licensing, build, framework, bundle, maintenance, or rendered compatibility fails, remove the package with the same manager and evaluate the next qualified source or a repository-owned SVG.

Do not install when the task is read-only, repository policy explicitly forbids new dependencies, official package or license evidence is unavailable, paid terms are not authorized, or no stable role and maintenance owner can be stated. Ask for direction only when resolving that condition would require new authority or a materially broader migration—not merely because the package is new.

## Custom SVG Gate

Choose a custom symbol over visible text or a compatible auxiliary source when all of these are true:

- The concept is recurring, product-specific, or a signature navigation destination.
- The selected family has no clear metaphor after searching related nouns, verbs, mechanisms, and consequences.
- A visible text label alone is insufficient for the repeated context.
- The team can own the source, provenance, maintenance, and accessibility behavior.

Do not assume a custom SVG is automatically more coherent or cheaper than a compatible maintained source. Compare ownership, recognition, bundle, license, and maintenance costs through the source gate above.

Construction requirements:

- Match the declared drawing language's grid, stroke, caps, joins, corner language, negative space, and fill behavior, or document a deliberate role boundary that calls for another language.
- Prefer one base object plus one modifier for compound concepts. Avoid ornamental complexity.
- Test at 16px, 20px, and 24px. Simplify any detail that closes, blurs, or becomes visually heavier than neighbors.
- Test default, hover where relevant, selected, disabled, light, dark, and high-contrast conditions.
- Use `currentColor` for single-color UI glyphs unless multicolor is semantically necessary.
- Keep an accessible name on the owning control; the SVG is normally decorative inside a labelled control.
- Store source and license provenance with the asset.

Do not create custom replacements for search, close, back, delete, disclosure, or other learned system actions.

## Size, Alignment, and Containers

- Use the family's native grid and available optical-size variants.
- Common UI sizes are 16–20px for dense desktop controls and 20–24px for primary navigation or touch UI. Choose by context, then adjust optically.
- Align by perceived center and text baseline, not only by SVG bounds.
- Use a transparent hit area by default.
- A compact rounded-square surface may communicate hover, press, focus, selection, grouping, or elevation.
- Avoid a wide pill behind a standalone icon when it adds decoration but no state, grouping, platform, or brand meaning.
- Avoid putting every navigation glyph in its own badge, disc, or capsule unless those containers encode a real role and the repetition preserves hierarchy.

## Accessibility and Meaning

- Give every icon-only control an accessible name.
- Use a visible label for unfamiliar, consequential, or product-specific actions until recognition is established.
- Tooltips may supplement a name on hover-capable platforms; they do not replace the accessible name.
- Do not communicate status with color or icon shape alone when the consequence matters.
- Mirror directional symbols for right-to-left interfaces when the platform or icon family requires it; do not mirror universal media or brand symbols blindly.
- Use official provider marks and follow their color, clear-space, and trademark rules.

## Visual QA

Review icons inside the real interface, not as an isolated contact sheet:

- Recognition: can a user predict the action without guessing?
- Drawing-language coherence: grid, stroke or fill, corners, detail level, baseline, and optical weight match where icons appear together; intentional role boundaries remain obvious.
- Density: icons do not overpower labels or metrics.
- Alignment: baselines and perceived centers hold across rows and toolbars.
- State: default, selected, disabled, destructive, and loading meanings remain distinct.
- Theme: icons retain contrast without neon edges, glow, or arbitrary accent color.
- Container restraint: hit targets are accessible without visible pills or oversized discs.
- Source and maintenance: roles are documented; package count alone is ignored; imports are tree-shakable where supported; no deprecated source was added; and provenance is recorded.
- Exploration integrity: broad-search requests show concrete candidates from independent external families and same-context renders of the finalists; a catalog skim or early installed-family winner is reported as incomplete.
