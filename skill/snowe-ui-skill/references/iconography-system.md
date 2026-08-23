# Iconography System

Use this reference when selecting, extending, or creating interface icons, pictograms, category symbols, feature graphics, or a symbol family. Familiarity, visual fit, ownership, and implementation cost are separate decisions.

## Decide Whether an Icon Helps

Start from role and context:

```text
role | intended meaning | audience/domain | placement | surrounding label |
frequency | state | target size | input/platform | accessibility owner
```

Prefer visible text when a symbol would be unfamiliar, ambiguous, rarely used, high-stakes, or harder to scan than the label. Use an icon when it improves recognition, spatial economy, repeated scanning, direct manipulation, cross-language support, or identity without hiding meaning.

Do not add a decorative icon to every title, statistic, feature, or card. Illustrative symbols and interface controls have different jobs and may use different systems.

## Inspect the Existing Symbol Ecology

Before searching:

- inventory current sources, exact glyphs, sizes, stroke/fill modes, optical weight, alignment, color behavior, labels, and component wrappers;
- identify platform-native expectations and repository-owned assets;
- distinguish brand marks, interface actions, object/category symbols, status indicators, data glyphs, and decorative/illustrative graphics;
- find semantic duplication and misleading metaphors;
- verify installed packages, versions, adapters, licenses, tree-shaking or font loading, and ownership.

An established source is evidence and usually the baseline, not an automatic winner or a closed allowlist. Preserve it for routine actions when it already fits; explore further only where coverage, meaning, platform, or art direction makes the difference material.

## Choose Meaning Before Source

For each unresolved concept, create a small semantic set:

- direct object or action;
- mechanism or transformation;
- output, consequence, or state;
- domain-specific metaphor users already know;
- visible text or no icon.

Test the metaphor in its full label, neighboring actions, state, and user vocabulary. Reject a clever symbol that becomes ambiguous without explanation. Avoid reusing one glyph for different meanings in the same experience.

Only then compare exact glyphs. Local `icon-concepts` results can prompt metaphor alternatives; `icon-families` and `icon-candidates` are discovery snapshots, not current package or quality truth.

## Select an Existing Source

Rank exact candidates on:

- semantic recognition in context;
- optical size, weight, density, baseline, perspective, terminals, corners, and negative space beside the actual UI;
- required state and variant coverage;
- platform and brand fit;
- accessibility and localization behavior;
- current official availability, license, maintenance, adapter, payload, and repository compatibility.

Render finalists at target size beside real neighbors before dependency economics break a semantic/visual tie. Do not install an entire comparison set. When an external winner is justified in build work, verify its current official source and license, install only the selected adapter with the repository package manager, and update the lockfile. Review-only work does not authorize dependency changes.

Multiple sources may coexist only with an explicit role boundary and compatible rendering. Normalize size or wrapper behavior where appropriate; do not distort paths until incompatible drawings merely look uniformly mediocre.

## Decide Whether to Draw Custom

Custom work is justified when at least one is true:

- the product has a specific object, mechanism, category, or brand behavior no existing symbol expresses clearly;
- a small signature family materially strengthens identity or product comprehension;
- platform/native templates support a coherent extension;
- licensing, language, state, or technical constraints make available sources unsuitable.

It is not justified merely because custom feels premium, a generator can produce SVG, or a library is imperfect. Compare text, native/existing, compatible external, and custom candidates. Keep custom only when it wins at real size and in context.

## Specify the Drawing Language

Write a family specification before drawing paths:

```text
family role and semantic range
coordinate grid, live area, key lines, and optical overshoot
target sizes and smallest detail
stroke / fill / hybrid mode and weight variants
cap, join, terminal, corner, and taper behavior
primitive shapes, curvature, diagonals, and perspective
positive / negative-space rhythm and counters
baseline, visual center, and center-of-mass rules
detail budget and simplification by size
state, badge, directional, mirrored, and animation variants
color/currentColor and theme behavior
accessibility ownership, provenance, license, and maintainer
```

The grid is a construction aid, not the optical result. Curves may overshoot; asymmetrical subjects may need asymmetric padding; diagonals and circles often need visual compensation. Equal numeric boxes do not guarantee equal perceived size.

When the change introduces or materially extends a family, build a proof with unlike subjects: one simple orthogonal icon, one circular or curved icon, one diagonal/asymmetric icon, and one dense domain-specific icon. This exposes a weak language earlier than polishing a single favorable symbol. A single bounded icon correction does not need a ceremonial family workshop; compare it against the established neighbors and the strongest exact alternative at its real sizes.

## Construct and Iterate

1. Sketch silhouettes and semantic alternatives at or near target size.
2. Choose the clearest skeleton and reduce it to the family primitives.
3. Draw clean source geometry on the declared viewBox. Use as few paths and control points as clarity permits, but do not sacrifice optical correction for mathematical purity.
4. Render at every target size, including 16, 20, and 24 px for ordinary interface icons unless the real component uses a different documented set.
5. Compare light/dark themes and relevant default, hover, active, disabled, selected, and high-contrast contexts.
6. Place it beside real family neighbors, labels, buttons, fields, navigation, and dense content. Inspect blur/squint, silhouette, baseline, center of mass, counters, terminal rhythm, and detail loss.
7. Compare with the strongest existing candidate and visible text. Revise or reject.

For very small sizes, create a deliberate optical variant when necessary; do not uniformly scale a detailed large pictogram into illegibility.

## SVG Contract

For interface SVGs:

- declare a stable `viewBox`; avoid unexplained transforms and fractional drift;
- use `currentColor` or documented semantic color roles unless multicolor conveys required meaning;
- keep inline text, scripts, embedded remote images, and external references out of the asset;
- avoid masks, filters, and clipping when simpler geometry produces the same result;
- let the owning component provide the accessible name for action icons; decorative duplicates remain hidden;
- preserve raw editable source or construction parameters when future optical variants are expected.

Validate structure and provenance:

```text
python <skill-directory>/scripts/asset_quality.py path/to/icon.svg --metadata path/to/icon.metadata.json
```

Metadata requires the icon role, grid/live area, drawing language, target sizes, source/license, accessibility owner, and structured local evidence bindings. Local source and license records must resolve from metadata-relative paths to safe regular files whose exact bytes match their digests; external source URLs remain explicitly unverified. A passing validator proves only the declared structural contract. It cannot certify beauty, recognition, optical balance, or family coherence.

The validator accepts a strict self-contained interface-icon subset. It rejects nested viewports, executable or linked content, embedded text/raster content, URI/local-fragment dependencies, transforms/masks/filters/clipping, unknown attributes, malformed or clipped geometry, collapsed root dimensions, non-`currentColor` paint, asset-level muted opacity, unsupported miter joins, and metadata/provenance contradictions. The exact schema and boundary are in [cli-reference.md](cli-reference.md).

## Operational Candidate Comparison

When the outcome is genuinely unresolved, compare only the strongest plausible existing, custom, and visible-text/no-icon alternatives. A familiar routine action in an accepted family can stay Direct; do not manufacture challengers after the answer is already learned and contextually sound.

For a material icon decision, the standard-library helper generates a self-contained representative-control matrix after validating each SVG and cross-binding its metadata:

```text
python <skill-directory>/scripts/icon_review.py \
  path/to/manifest.json --output path/to/comparison.html --json
```

Declare the role, component type, visible label/content, target sizes, relevant states, candidates, context evidence, current verdict, and selected candidate. Use `repository-derived` context evidence only when the named source file and selector exist and a candidate is selected; otherwise label unresolved evidence `representative`. For repository-derived proof, map every comparison state to exactly one exercised host state (including `high-contrast` → `forced-colors`) and bind the selected candidate to the actual owning host when the owner can be exercised. The matrix is useful for like-for-like size/state comparison but is not a substitute for the actual host component.

Inspect the generated matrix at wide and narrow viewports, then inspect claimed winners and close losers in the real UI at every implemented size and relevant default, focus, selected, disabled, light, dark, and high-contrast state. Record four evidence categories separately:

- deterministic contract: SVG/metadata/manifest structure, exact SVG-byte binding, structured source/license byte bindings, and explicit comparison-state→host-state coverage;
- rendered/browser regression: what the comparison sheet and host component actually render;
- current source evidence: official asset bytes, version/revision, and license where external; external URL truth remains unverified until current primary-source review;
- human visual judgment: recognition, silhouette, optical center, weight, negative space, metaphor, and neighboring fit.

The checked source-repository proof under `evals/icon-decisions/` demonstrates all three legitimate outcomes: an existing glyph wins and custom is rejected, custom wins for a product-specific mechanism, and visible text/no icon wins because an icon would assert the wrong state.

## Recognizability and Optical Review

Use short-context checks, not a popularity vote:

- Can a representative user distinguish the icon from its nearest semantic neighbors?
- Does the label-icon pair reinforce one meaning rather than contradict it?
- At target size, which details disappear or merge?
- Does it appear the same size and weight as neighboring icons without measuring larger?
- Is the baseline and visual center correct in the real control?
- Do curves, diagonals, counters, terminals, and corners feel from one hand?
- Does selected/filled treatment change meaning or only emphasis?
- Does mirroring preserve meaning across directionality, or is the symbol culturally/spatially fixed?

Mark custom work `REJECT` when recognition, ambiguity, balance, detail survival, state clarity, or family coherence is worse than the best existing or text alternative. Record the loser; do not keep it because it is ownable or took effort.

## Delivery

Report semantic decisions, established ecology, exact finalists, current source/license evidence, family role boundaries, custom family specification when used, target-size/context renders, validator output, accessibility ownership, rejected candidates, and unresolved symbols. Do not claim an icon family is coherent from SVG validity alone.
