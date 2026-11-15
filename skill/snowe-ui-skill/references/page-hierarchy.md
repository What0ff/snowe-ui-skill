# Page Hierarchy, Copy and Actions

Use before component and layout selection for a new page with a known job, a material change to one page's hierarchy, or an explicitly rejected composition. This is a Focused route when the objects and surrounding product flow are known. A specified local property correction stays Direct. Unknown page goals or whole-product relationships escalate to [experience architecture](experience-architecture.md); the size of the diff does not choose the route.

## Map the Page Before Containers

In the existing working record, state the user task and context, list the content and operations the page needs, and assign their roles and relationships:

```text
group / purpose / parent or related group / importance / required states / surface
what the user must understand or do / what must be seen together
```

`surface` is where the group lives (main surface, side panel, dialog, popover, tabs, in-place disclosure or its own route), chosen with [surfaces-and-disclosure.md](surfaces-and-disclosure.md); keeping a group on the main surface is a choice too.

Roles can include resource context, page identity, local navigation, selected object, primary work or data, current action, supporting state and reference or help; extend or omit them by task. Distinguish a selector from a status summary and a working collection from settings before styling either, and state the reading and task order and which relationships must survive a narrow viewport.

Only then choose grouping, composition, components and visual emphasis. A container represents an independent object or operation; ordinary attributes usually need only proximity, alignment and type. A section heading must distinguish its contents, not repeat a nearby selector.

For a material open choice, compare the baseline map with a credible alternative that changes the weak relationships; reordering identical boxes without changing importance or grouping is not an alternative. Implement a complete affected surface with real content before claiming its hierarchy works, and keep the map concise rather than a new document per correction.

### Connect Importance to Visible Cues

For a live hierarchy choice, extend the record with the few states that change the user's decision:

```text
state / immediate user question / intended attention order
visible cue and owner / competing element / observed render / disposition
```

Name the actual content, not "primary" and "secondary", and explain which placement, scale, weight, grouping, contrast or disclosure makes it distinguishable and what competes with it. "Use a journal" or "make the palette neutral" names a treatment, not proof that it helps this task. Keep useful technical data and a calm accepted system when they work.

Inspect meaningful transitions: while a scan runs, progress and affected records may lead; on failure, the problem and recovery; after completion, the result and next useful operation. This is a worked example, not a dashboard recipe. Change emphasis only where the user's question changes, without jumping panels or ceremonial animation.

Author the intended order and cues before evaluating, then compare them with what the full render emphasizes; never derive the expectation from the DOM and CSS being checked. A self-review's observed attention is reasoned judgment, not measured gaze. When structure is clear but its visual expression stays weak, settle that bounded choice with [art-direction-gate.md](art-direction-gate.md).

## Use References at the Requested Level

Identify what the user likes (hierarchy, density, navigation, typography, material, interaction) and inspect the actual referenced surface; a vendor's marketing homepage is not evidence of its dashboard hierarchy. Record which observed relationship transfers and why, such as distinct resource context or secondary tools, not the reference's palette, sidebar, module count or content model, and keep the target product's semantics, rights and identity. Direct-copy conformance stays separate from reference-inspired work. An engineering fixture or visually rejected candidate never becomes a quality reference because its tests passed.

## Audit User-Facing Text

Classify visible text by its job: domain data, state, action, useful guidance, or implementation and reporting detail. A phrase earns space when it helps orientation, a decision, an operation, identification or recovery; remove lines that restate a heading, explain an obvious empty container, or expose internal vocabulary. Treat a visible ordinal as a content relationship: unordered peers get descriptive headings and grouping, not `01:`/`02:` prefixes ([incident](failure-patterns.md#section-numbering-added-as-polish)).

Technical products keep legitimate technical content: IDs, command aliases, API concepts and parameters can be essential data. Move occasional reference material into an accessible disclosure without hiding the primary task's evidence. Explain errors in user language, keep recovery, and put diagnostic detail outside the main flow. Never use a global forbidden-word list. Keep fixture notices, hashes, test results and disclaimers out of the target surface ([incident](failure-patterns.md#report-notes-inside-the-product-screen)).

## Keep Marketing Copy Scannable

A landing or marketing page is scanned, not read: visitors take in the headline, the hero visual and the section headings, then act or leave, and every extra sentence competes with the product for that glance. Default budgets, starting points to beat only with a reason such as long-form editorial, documentation or a regulated product's required disclosure:

| Part | Default |
|---|---|
| Hero | a headline of about 10 words or fewer, one or two supporting sentences (30 words or fewer), one primary action |
| Section | one idea: a heading of about 8 words, then one short paragraph (about 40 words) or three to four one-line points, beside the visual that proves it ([visual by section job](imagery-and-assets.md#give-each-section-the-visual-its-job-needs)) |
| Page | about five to seven sections and 600–1,200 words of prose outside product visuals |
| Product visual | readable at a glance: a few states with short labels and realistic sample content; a visual that must be read line by line is prose in disguise |

Show before telling: a paragraph that describes what the product does gives way to the product doing it, as a UI state, a mechanism illustration or a chart, with a few words of label. A sentence earns its place by changing a decision: what this is, who it is for, why to believe it, what it costs, what to do next. Cut repetition between hero, sections and FAQ, and move depth into FAQ disclosures or deeper pages instead of the main scroll.

Check the render: count visible words, prose and product visuals separately, and run the skim test. From headings, hero sentences and visual labels alone, a visitor can say what it is, for whom, why to believe it and what to do next; cutting words must leave a page that still says so.

## Audit Actions by Meaning

For each action record `operation + target object + outcome + context`, verify it against the handler/destination, and choose its placement. Different labels do not make identical operations distinct. Default: one primary entry to the same outcome in the same context; a contextual shortcut, long-form repeat, bulk action or responsive alternative needs its own benefit and state boundary.

Identical row buttons for different objects are legitimate distinct actions. Never deduplicate by text or enforce one button per name. Inspect simultaneously available desktop and mobile variants and repeated submits. A retained repeat gets a recorded reason and a clear hierarchy; a second equally prominent control with the same effect is no benefit by itself.

## Accept the Relationships

From the current complete render, the user should see where they are, what is selected, which object and data matter, what can be done now and which tools are secondary, through grouping, prominence and proximity rather than by reading every panel. Check empty, sparse and populated states, important permission, error and dialog states, keyboard access, text scaling and responsive transformation. Required information must be perceptible and accessible in the state under review: DOM presence, text inventories and boxes do not prove visibility through opacity, clipping, occlusion or hidden accessibility ancestors, and sampled checks cannot certify visual quality.

A clear role map is not a finished visual direction: review the whole screen for deliberate type relationships, readable surface separation, balanced grouping and coherent control states. Keeping a palette or font does not require keeping rough stock styling. Equally, approved quiet or native-looking controls are valid: change them only when context or feedback warrants it.

Record four separate outcomes: technical contract, evidence integrity, visual assessment and user acceptance. Resolve material hierarchy, copy and action findings before visual `KEEP`. User rejection reopens the affected direction, and silence is not approval. Report only the scope actually proved, without a numerical taste score.
