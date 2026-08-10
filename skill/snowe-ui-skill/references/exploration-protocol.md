# Exploration Protocol

Use this reference before committing any material design decision. Its purpose is to search the full relevant option space, compare real candidates, and prevent repository familiarity or implementation cost from deciding quality before discovery is complete.

## Contents

1. Always-on contract
2. Define the relevant universe
3. Explore, compare, commit
4. Domain coverage
5. Evidence ledger
6. Closure rule
7. Integration economics
8. Failure patterns

## 1. Always-on Contract

Run this protocol for every material choice in visual direction, composition, typography, iconography, color or material, component behavior, imagery, motion, and data visualization. Treat installed packages, current tokens, native components, and existing assets as the baseline—not the search boundary.

“All possible options” means all options that remain relevant after explicit product, platform, script, accessibility, brand, license, performance, and scope constraints are applied. It does not mean enumerating an infinite catalog, every hex value, or cosmetic variants that cannot change the decision.

Skip broad discovery only for a confirmed invariant or a routine decision whose answer is learned, native, or already fixed by the accepted system, such as a close icon, a platform back gesture, an unchanged spacing token, or a narrow bug fix. Still verify fit in context. Promote the decision to full exploration as soon as the current system is unclear, weak, rejected, or materially challenged.

## 2. Define the Relevant Universe

Before searching, record:

- Decision and real user consequence
- Required platform, input modes, scripts, content, states, and accessibility behavior
- Verified brand, repository, native, license, performance, and delivery constraints
- Current baseline and why it may or may not be sufficient
- Candidate classes and authoritative sources that could plausibly change the outcome
- Excluded classes with evidence; do not exclude a source merely because it is uninstalled or unfamiliar

Search both bundled datasets and current primary sources. Treat a local registry as an index, not an exhaustive market boundary. Deduplicate cosmetic variants and preserve materially different approaches.

## 3. Explore, Compare, Commit

1. **Explore for quality.** Retrieve concrete options across the relevant candidate classes. Do not apply dependency, migration, lockfile, procurement, or familiarity penalties yet, except to remove a proven legal, platform, or hard-delivery incompatibility.
2. **Compare in context.** Put finalists on the same real content, viewport, state, theme, size, and task. Names, catalog pages, trend labels, and package descriptions are discovery evidence—not visual proof.
3. **Rank semantic and visual fit.** Compare task clarity, recognition, hierarchy, content resilience, script coverage, optical behavior, system coherence, product identity, and accessibility feasibility.
4. **Apply integration economics.** Only after the quality ranking, evaluate license, package or asset model, bundle or runtime cost, loading, maintenance, migration, lockfile impact, and ownership.
5. **Commit one coherent decision.** Record why it won and why the strongest rejected option lost. Install or integrate the winner when implementation is authorized; do not keep the comparison set.

## 4. Domain Coverage

| Domain | Discovery coverage | Required comparison proof |
|---|---|---|
| Visual direction and composition | Current baseline plus structurally distinct directions that represent the material product trade-offs | Same content and requirements; use the direct, refinement, or full art-direction gate rather than palette-only variants |
| Typography | Scan applicable repository, platform, open, and licensed foundry or catalog candidates for required scripts, weights, axes, numerals, tone, and loading constraints; include materially different typographic archetypes | Render the baseline and at least three strongest external finalists when available using real headings, body, labels, long localized strings, numerals, and fallback behavior; a font-name list or specimen page is insufficient |
| Iconography | Search concrete glyphs across every relevant family class; in broad cases include at least three uninstalled sources when available | Render at least two external finalists beside the installed baseline at the exact UI size and state; follow [iconography-system.md](iconography-system.md) |
| Color and material | Compare complete semantic role systems and material treatments appropriate to the product, brand, themes, and content—not isolated swatches | Apply finalists to the same focal hierarchy, controls, data, states, and themes; measure applicable contrast and inspect repetition |
| Shape, surfaces, and controls | Compare coherent geometry and density systems plus behaviorally correct native, repository, and viable stack primitives | Render representative controls together with focus, selected, disabled, error, content expansion, and target behavior; do not select by component-gallery aesthetics |
| Imagery and illustration | Inspect verified brand or repository assets plus relevant licensed, commissioned, generated, or diagrammatic directions | Compare crops or compositions on the real layout; verify provenance, rights, responsive behavior, text contrast, and loading |
| Motion | Compare the static or reduced-motion baseline with the relevant functional transition models; exclude decorative motion that cannot explain cause, continuity, hierarchy, or status | Exercise the real interaction, interruption, repeated use, reduced motion, and performance rather than approving a demo clip |
| Data visualization | Enumerate chart families capable of answering the real analytical question and reject incompatible encodings with evidence | Render the strongest encodings with representative data, labels, extremes, empty/error states, and accessible text or table support |

The numeric floors above are evidence floors for high-variety searches, not quality scores or mandates to add dependencies. If fewer viable options exist, document every authoritative source searched and the exact constraint or no-result evidence.

## 5. Evidence Ledger

Use one compact row per candidate:

```text
decision | candidate class | exact candidate/source | external or baseline | constraints passed | same-context render | semantic/visual finding | integration finding | advance/reject reason
```

Keep phase-A quality findings separate from phase-B integration findings. A candidate cannot be called visually weaker merely because it is new, and it cannot be called production-ready merely because it is installed.

## 6. Closure Rule

Exploration closes only when:

- The relevant universe and exclusions are declared.
- Every applicable candidate class has concrete evidence, not only a name.
- External challengers were gathered wherever the baseline was not an invariant.
- Finalists were compared with identical real content and conditions.
- Required scripts, states, themes, sizes, and platform behaviors were exercised.
- The quality ranking exists before integration economics.
- The strongest rejected candidate and decisive difference are recorded.
- Another unsearched relevant class is not reasonably likely to change the winner; if it might, keep the result `UNKNOWN` and continue.

Stop after evidence saturation. Do not continue collecting near-duplicates after every relevant class is covered and new candidates no longer introduce a materially different or stronger answer.

## 7. Integration Economics

After closure, prefer the winner that preserves the strongest task and design outcome inside real constraints. Reuse the baseline when it genuinely wins. When an external option wins and implementation is authorized, verify its current official source, license, version or asset provenance, platform compatibility, loading or bundle model, maintenance, and owner; then integrate only that winner and verify the build plus render.

For review-only work, keep all comparison artifacts outside the repository and report the exact future integration action without mutating dependencies or project assets.

## 8. Failure Patterns

- Stopping after the first acceptable installed or familiar option
- Calling a catalog skim, search-result list, moodboard, or font-name list a comparison
- Applying dependency or migration cost during discovery instead of after quality ranking
- Comparing superficial variants while omitting another relevant structural or typographic class
- Searching only bundled datasets when current official sources could change the answer
- Installing the whole shortlist to make a contact sheet inside the product repository
- Reopening confirmed invariants and routine platform conventions without evidence
- Continuing indefinitely through near-duplicates after coverage and evidence saturation
