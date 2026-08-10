# Imagery and Visual Assets

Use this reference when a design may need photography, illustration, product media, diagrams, generated imagery, textures, or custom graphics. Start with the communication problem, not an asset tool.

## Decide Whether a Visual Exists

Write the visual job in one sentence:

```text
For [person in context], this visual must [explain / prove / orient / reveal / compare / make desirable] [specific thing] before or while they [decision or action].
```

If the sentence is vague, compare the page without the asset first. Composition, type, real product UI, data, or direct product facts may do the job better.

Consider only relevant outcomes:

- **No image:** strongest when information, task speed, privacy, credibility, or type/composition already carries the experience.
- **Verified product media:** strongest when exact form, finish, scale, condition, or operation affects a purchase or decision.
- **Photography:** strongest for people, place, use, craft, evidence, and emotional specificity that can be represented truthfully.
- **Illustration:** strongest for an ownable world, abstraction, sensitive subjects, impossible scenes, or controlled narrative continuity.
- **Diagram or data graphic:** strongest for mechanism, sequence, relationship, comparison, or consequence.
- **Product composition:** strongest when several real objects or interface states must be art-directed into one sales or explanatory frame.
- **Generated imagery:** strongest when a sufficiently truthful visual is needed, existing assets cannot meet the composition, and generation can be directed and evaluated.
- **Custom graphic or texture:** strongest when a repeatable visual grammar can encode the product, brand, content, or interaction more specifically than decoration.

Record why the winner beats the no-visual baseline and the strongest non-generated alternative. `No image` is a completed decision, not missing polish.

## Build the Image System

Treat imagery as a system of roles rather than a collection of attractive files. Define only the roles the experience needs, for example:

- product truth and inspection;
- proof of use or outcome;
- editorial story and place;
- orientation or category distinction;
- explanatory mechanism;
- atmospheric identity;
- background material or transition.

For each role, define subject, distance, viewpoint, light, color behavior, environment, human presence, realism, crop logic, caption or attribution, responsive treatment, and repetition limit. A deliberate contrast between roles can be coherent; unexplained variation cannot.

Prefer real representative content. Do not let one unusually good hero asset hide a weak catalog, article, empty, loading, or mobile state.

## Art-Direct the Slot, Not an Isolated Image

Before sourcing or generating, inspect the actual composition and write an asset brief:

```text
page and decision role
slot dimensions and responsive variants
subject, action, and factual requirements
camera / projection / illustration viewpoint
subject placement, gaze or motion direction, and negative-space map
foreground, background, depth, light, material, and color relationship
type, controls, or product UI that must coexist with the image
crop-safe and protected regions
continuity rules with neighboring assets
prohibited errors, cliches, false claims, logos, text, and artifacts
performance, provenance, editability, and fallback requirements
```

Specify where the page needs calm space and where detail may live. Do not generate a conventional centered scene and try to repair the composition with an arbitrary crop afterward.

## Use Existing or Licensed Assets

- Inspect repository-owned and brand-approved assets before searching elsewhere.
- Verify source, license, usage rights, attribution, model/property releases where relevant, and whether edits are permitted.
- Prefer official product media when exact product appearance is material.
- Record source URLs and license evidence close to the asset or in the project's accepted decision record.
- Do not infer rights from search-result availability.

## Generate Only When It Wins

Use an available image generator only after the asset brief and a real layout slot exist.

1. Generate or edit for the exact composition, aspect, placement, and art-direction system.
2. Inspect factual details, anatomy, product geometry, logos, text-like artifacts, perspective, reflections, shadows, hands, wheels, repeated objects, and edge quality at full resolution.
3. Place the result in the implemented layout at wide, pressure, and narrow widths. Test overlays, crops, contrast, loading space, and adjacent real assets.
4. Compare it with the no-image baseline and the strongest existing, photographed, illustrated, or diagrammatic alternative.
5. Edit, regenerate, replace, or reject it. Effort already spent is not evidence.

Do not use generated imagery as proof of an exact product, medical result, property, person, historical event, certification, or other claim it cannot verify. For commerce, never let a generated frame misrepresent a purchasable item's geometry, included components, color, scale, condition, or performance. Generated atmosphere may support verified product imagery; it must not replace product truth.

Keep the prompt or generation brief and provenance when reproducibility, disclosure, brand governance, or future editing matters. Optimize and export only after selection.

## Design Custom Graphics as a Family

Custom graphics include diagrams, badges, maps, patterns, textures, illustrations, product callouts, empty-state art, and hybrid data/editorial visuals. Before drawing, specify:

```text
semantic roles | primitives | geometry or perspective | line/fill language |
corner and terminal behavior | positive/negative-space rhythm | detail budget |
color roles | type relationship | scale range | motion potential |
responsive simplification | source/provenance | ownership and editability
```

Create a small family proof with unlike roles, not several versions of the easiest motif. Test a simple, dense, small, large, light, dark, and content-adjacent case when those contexts exist. A custom visual language should remain recognizable without turning every surface into the same motif.

Use vector/code-native construction for precise scalable systems when possible. Use raster generation for photographic, painterly, textured, or otherwise bitmap-native outcomes. Do not rasterize a maintainable interface symbol merely because a generator is available.

## Layout Evaluation

Judge the complete page, not the asset preview:

- Does the visual complete its stated job faster or more convincingly than the alternatives?
- Is the focal subject where the composition and reading direction need it?
- Is the crop still truthful and strong at each pressure width?
- Does text remain readable without crude overlays or excessive dead zones?
- Do product, people, environment, scale, and context feel credible?
- Does the asset belong to the selected art direction beside real content and neighboring assets?
- Are repeated images adding information, rhythm, or story rather than visual inventory?
- Is the file cost, decoding, layout stability, and loading behavior proportional to its value?
- Is useful alt text possible, or is the image decorative and correctly silent?

Mark the result `REJECT` when the page becomes less clear, less truthful, more generic, compositionally dependent on one crop, incoherent with real assets, or slower without equivalent user value. Keep the simpler alternative.

## Delivery Evidence

Report the visual job, alternatives considered, source or generation method, selected crop/variants, provenance, in-layout viewports reviewed, accessibility behavior, performance treatment, rejected artifacts, and the reason an image or custom asset was deliberately omitted when that decision materially shaped the design.
