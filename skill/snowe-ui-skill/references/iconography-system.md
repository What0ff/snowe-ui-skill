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

An icon and its backing are separate decisions. Inspect the real owner for circles, capsules, tiles, nested rings and pseudo-element paint; a clean path or valid metadata cannot justify a button-like surface behind a passive symbol. Apply the [icon-backing acceptance check](quality-gates.md#icon-backings-and-nested-surfaces) in context, preserving justified interaction, contrast, masks and accepted identity. A wrapper-only correction can keep the existing glyph and stay Direct when its answer and owner are bounded.

## Choose the Control Label Mode

Use the role/context record above to choose the presentation that makes the action quickest to understand and operate at the intended density. Do not automatically add a caption to every icon or remove text because another app looks cleaner. Reason by action family, keep peers consistent, and justify meaningful exceptions rather than re-deciding every identical row.

- **Icon only:** a recognizable, repeated utility whose meaning and state remain clear in its toolbar, view switcher or row context before a tooltip appears.
- **Text only:** wording communicates the action well and an accompanying glyph adds no useful recognition, scanning or identity value.
- **Icon with text:** the pair materially helps recognition or scanning, or visible wording is needed to understand an unfamiliar, ambiguous or consequential action.

Inspect the actual handler/outcome and neighbors before naming or hiding the label. A table/list view switcher can use familiar symbols with localized “Table view” / “List view” tooltips and a visible/programmatic selected state. An important commitment may need an action phrase. Preserve accepted conventional controls; a passive service name, data label or form label is not a redundant button caption.

Own this reversible decision. If it remains material and unresolved, compare the credible modes in the real control set at its actual size and input contexts, then select the clearest result yourself. Inspect icon-only recognition with the tooltip closed: hover help cannot rescue an unclear metaphor or make touch users guess. Retain necessary wording when uncertainty remains. A known accepted pattern or bounded caption correction does not require an icon-source workshop or a new decision document.

Every icon-only action needs an accessible name independent of hover, such as the owning button's `aria-label` or `aria-labelledby`; hide decorative SVG content from assistive output. Reuse the site's tooltip component/style: concise help on hover and keyboard focus, readable while hovered, and Escape dismissal without moving focus or activating the action. A plain tooltip contains no focusable controls. Do not rely on HTML `title` alone or announce identical name/description twice. On touch, preserve understandable operation without hover; use wording or an equivalent labelled path when needed. See [button naming and state](https://www.w3.org/WAI/ARIA/apg/patterns/button/) and [hover/focus content behavior](https://www.w3.org/WAI/WCAG22/Understanding/content-on-hover-or-focus.html).

Verify the chosen mode's recognition, accessible name/state, input behavior, target size and tooltip clipping at the affected viewport. Do not present speculative label stripping as an improvement before checking the whole control set.

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

## Develop Custom Candidates Where They Add Value

Custom work is justified when at least one is true:

- the product has a specific object, mechanism, category, or brand behavior no existing symbol expresses clearly;
- a small signature family materially strengthens identity or product comprehension;
- platform/native templates support a coherent extension;
- licensing, language, state, or technical constraints make available sources unsuitable.

For an open product-specific feature, category, service or repeated family, actively sketch a custom candidate when feasible instead of ending the search at an approximate library match. This is a preferred exploration route, not a requirement to add icons where text works. An explicit request for custom icons puts drawing in scope; do not repeatedly ask whether to try it. A bounded correction to an accepted glyph does not reopen its source decision.

Compare the custom candidate against the strongest relevant existing or text alternative at equal size and in the same host. Prefer custom when recognition, accessibility and rendering are at least as strong and its metaphor or family fit is visibly more specific. Do not require custom to be unprecedented or to defeat every external library. Preserve conventional Home, close, search, back and similar actions unless the user opens that decision; custom drawing may refine a familiar silhouette without inventing a new meaning.

It is not justified merely because custom feels premium, a generator can produce SVG, or a library is imperfect. More custom work should come from exploring meaningful opportunities and improving candidates, never from weakening acceptance or decorating every label.

## Generate From the Real Meaning

Before paths, inspect the feature's actual input, action or object, outcome, current state, label, nearest sibling meanings and smallest real slot. Write a short semantic brief: `this symbol represents …; it must not imply …; it sits beside … at … CSS px`. Use repository/product evidence; keep an unknown mechanism unresolved rather than inventing a capability. A service name alone is insufficient when its meaning is ambiguous.

Choose the distinguishing visual cue. For compound concepts, start with a dominant silhouette and the minimum modifier that changes the meaning; test different constructions only while the metaphor is open. Avoid generic sparkle, shield, crown, gear or crossed-tool substitutions that could accompany any feature. A shield/check can assert safety or completion; a download arrow can turn a history view into an action. Verify these implications against the actual state. Do not stack several tiny symbols to reproduce an entire description.

Draw editable SVG geometry or extend the established vector system. Use raster generation only for a genuinely raster illustration role, not as a shortcut for crisp small interface glyphs. Establish the native grid and stroke/fill language around the smallest implemented size; choose coordinates and stroke alignment that survive its actual scale. Integer coordinates alone do not guarantee crisp curves or diagonals. Inspect computed SVG dimensions, viewBox scaling, ancestor transforms, flex shrinking and device-pixel ratio when blur appears; redrawing the asset cannot fix a scaled host.

Render the rough candidate in its real slot early, alongside its label and nearest semantic sibling. Reduce tangencies, merged counters, redundant strokes and unstable detail before adding polish. Use optical variants when an essential cue fails at a smaller implemented size; do not hide a weak 16/20 px symbol behind a successful enlarged preview. Avoid `crispEdges` as a blanket fix for curved/diagonal paths and avoid raster upscaling or blur filters. Keep directional meaning, visual weight and state behavior consistent across variants.

Once the construction works, propagate the grammar to the required family and inspect the full set. A familiar library asset reused unchanged remains existing; call an adaptation derived, preserve its license/provenance, and distinguish it from an original drawing. Ownership is not a visual-quality claim.

### Repair Weak or Pixelated Results

Treat reports of weak, muddy or pixelated icons as a defect to reproduce at the user's actual size, scale and background. First distinguish a raster source/upscaled screenshot from vector geometry, host resampling and ordinary edge antialiasing. Preserve the original asset and capture conditions so a sharper screenshot is not mistaken for a better drawing.

Use a lossless, unresized capture or the live renderer for sharpness judgments, recording CSS size and DPR. JPEG compression, thumbnail downsampling and enlarged chat previews can introduce artifacts absent from the SVG. They may reveal a suspected defect but cannot settle its cause; inspect the actual native-size rendering before changing paths. A sharper capture proves better evidence, not an improved icon.

Inspect the silhouette at 100% display scale. A thin, fragmented or visually timid mark needs a stronger construction: remove incidental segments, open counters, balance dominant masses and redraw joins or diagonals that merge. Do not simply thicken every path; that can close gaps and make dense icons heavier than their neighbors. Use the simplest distinguishing form the context supports, with deliberate curvature, terminal treatment and optical spacing. Rounded caps alone do not make a family polished.

For a 16/20 px owner, simplify around that native slot; use an optical small-size drawing if scaling the larger mark loses the essential cue. Compare it against the established family at the same apparent weight and background. Reject unresolved jagged, fuzzy, doubled, cramped or fragmented forms when they materially weaken recognition or fit, even if the file passes structural validation. An enlarged polished render cannot excuse a weak actual-size result. State exactly which sizes passed; do not propagate an accepted large version into uninspected compact controls.

When the source is sound but the host is soft, fix actual width/height, accidental fractional translation or scaling, flex shrink, CSS filter, bitmap delivery or screenshot resampling at its owner. Inspect relevant DPR and zoom conditions; do not force all paths to integer coordinates, disable antialiasing, or add sharpening as a universal repair. After the cause changes, recapture native-size context and confirm both clarity and semantic fit before accepting it.

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

## Accept the Context, Not the Drawing Sheet

For a new or materially revised custom symbol, close each applicable claim separately in the existing finding record:

| Claim | Required evidence and failure disposition |
| --- | --- |
| Context and truth | Compare the label/action/state with the metaphor and its nearest sibling meanings. `REJECT` a false capability, premature status, misleading action, or semantic collision; a polished shape cannot compensate. A self-review is not a representative-user recognition study. |
| Small-size recognition | Inspect every implemented size at native display scale, first for silhouette and then detail. `REVISE` merged strokes, lost distinguishing cues, muddy diagonals, crowded counters or ambiguous composites; simplify or redraw and rerender. |
| Optical family fit | Compare unlike neighboring glyphs in their real rows/controls, including the densest and most asymmetric required symbol. `REVISE` inconsistent apparent weight, baseline, size or rhythm. Equal viewBoxes and stroke numbers are not proof. |
| Host and backing | Inspect the actual owner, surrounding label, painted backing and affected states. Fix host scaling/shrinking and unjustified surfaces independently; use the [backing check](quality-gates.md#icon-backings-and-nested-surfaces). A contact sheet does not certify host rendering. |
| Technical and accessible behavior | Validate the changed SVG/metadata, then verify accessible ownership, color inheritance, clipping and relevant themes/focus/disabled/forced-color states. Fix applicable failures before acceptance; distinguish asset integrity from interaction proof. |
| Fresh proof | Bind findings to exact asset bytes and the current host/state/viewport. Missing or stale required context stays `UNKNOWN`; screenshots created but not inspected cannot close the claim. |

Use a native-size context view for acceptance; an enlarged crop helps diagnose geometry only. When small-size softness is at issue, compare ordinary DPR 1 and an available higher-density render, with actual browser metrics recorded; inspect fractional scale only where it is used or implicated. Do not invent device coverage. Review icon-only ambiguity without the author's explanation, then restore the real label context; a labelled domain icon need not become a universally understood standalone symbol, but it must not contradict or confuse that label.

Repair failed semantics before polishing paths, paths before optical alignment, and host paint/scaling at its owner. Compare the improved candidate with the same viable baseline, preserve rejected evidence, and stop when the applicable claims pass. If a contextual custom candidate still loses, use the better existing/text outcome and record the limiting cause so the next attempt can improve it. Delivery must not count an unverified custom draft as an accepted icon.

## Delivery

Report semantic decisions, established ecology, exact finalists, current source/license evidence, family role boundaries, custom family specification when used, target-size/context renders, validator output, accessibility ownership, rejected candidates, and unresolved symbols. Do not claim an icon family is coherent from SVG validity alone.
