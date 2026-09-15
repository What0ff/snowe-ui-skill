# Experience Architecture

Use this reference before art direction for new sites, products, page families, navigation systems, conversion journeys, and structural redesigns. Its purpose is to let architecture emerge from people, outcomes, content, and product relationships—not from a landing-page or dashboard recipe.

For the hierarchy of one page with a known job and surrounding flow, use [page-hierarchy.md](page-hierarchy.md) at Focused depth. Do not begin a whole-journey exercise for that local composition. Use this broader reference when the product topology, page job or relationships themselves are unresolved.

## 1. Model the Whole Journey

Start outside the interface.

Record:

- actors and their different knowledge, access, motivation, and responsibilities;
- the outcome each actor seeks and the circumstances in which the need appears;
- existing behavior, workarounds, channels, handoffs, delays, anxieties, and failures;
- what happens before entry and after the apparent conversion or task completion;
- recurring use, re-entry, saved state, progress, history, and support;
- offline, physical, service, operational, or organizational dependencies;
- business outcome, service obligation, and evidence of success.

Do not scope the experience around an org chart, database, existing transaction, or competitor navigation without evidence. A website may be only one part of a larger journey; make its boundary and handoffs intentional.

## 2. Build the Object and Content Model

Before pages, identify the things users need to understand or act on:

- product, service, plan, article, event, person, place, project, task, record, alert, route, document, order, status, or another domain object;
- attributes that support recognition, filtering, comparison, trust, and action;
- relationships among objects;
- quantity, variety, hierarchy, chronology, ownership, lifecycle, and update frequency;
- required editorial content, evidence, help, policy, and recovery content;
- missing, partial, expired, unavailable, or user-generated forms of the same content.

The model determines whether users need search, browsing, guided selection, comparison, sequencing, direct access, a map, a timeline, a workspace, or another interaction. Do not choose those mechanisms first.

## 3. Identify Decision Moments

For each important step, state:

```text
what the user knows → what they need to know → what decision/action becomes possible → what could block confidence or recovery
```

Examples of evidence needs—not prescribed modules—include price, availability, dimensions, fit, provenance, compatibility, status, deadline, location, demonstration, policy, review, result preview, or expert support.

Place conversion where intent becomes ready. Do not force every page to repeat an identical CTA, and do not hide the action after the user has enough evidence.

## 4. Synthesize Site or Product Topology

Generate enough architectures to cover the live organizing trade-offs. Each candidate defines:

- product/site boundary and cross-channel handoffs;
- top-level areas or destinations and why they belong together;
- entry points for high-intent, exploratory, returning, and assisted users;
- navigation, search, filtering, comparison, re-entry, and recovery;
- key page jobs and transitions;
- conversion or task-completion path;
- persistent context, saved work, history, or state when relevant;
- responsive and input-mode transformations;
- strongest assumption and failure mode.

Change the organizing principle between candidates. One might organize around the assortment, another around use situations, another around a guided choice, and another around expertise or story—but only when those principles arise from the real domain. These examples are prompts, not a finite list.

A candidate is not different because it uses a sidebar instead of a top bar, cards instead of a list, or dark instead of light surfaces while preserving the same information logic.

## 5. Design Navigation From Orientation Needs

Navigation must answer:

- Where am I?
- What belongs here?
- What can I do next?
- How do I get to a known target?
- How do I explore when I do not know the target?
- How do I return to an object, comparison, saved state, or incomplete task?

Select global, local, contextual, sequential, search-led, spatial, or object-centric navigation roles according to those needs. More than one role may coexist when the boundary is clear.

Rules:

- Use user and domain language rather than internal team names.
- Keep mutually important destinations visible or quickly discoverable.
- Show current location and parent/peer relationships when hierarchy matters.
- Preserve labels for unfamiliar destinations; icons alone are rarely sufficient for product concepts.
- Do not use a hamburger, mega menu, tab bar, command palette, rail, or carousel because the platform or a template makes it available.
- Ensure keyboard, screen-reader, touch, back/history, and deep-link behavior matches the information model.

## 6. Define Every Page by Its Job

Define the page's entry state, job, objects, decision readiness and place in the journey. Then use [page-hierarchy.md](page-hierarchy.md) for its internal roles, reading/action order, copy, navigation and state-dependent grouping before selecting components. No hero, sidebar or card count is mandatory.

## 7. Commerce Architecture

Commerce is not “hero + products + testimonials.” Model the real buying decision:

- breadth and differences of the assortment;
- novice versus expert knowledge;
- selection criteria and compatibility;
- price, availability, fulfilment, service, returns, warranty, and financing;
- desire and product truth;
- comparison and saved consideration;
- online, store, appointment, test, trial, or assisted paths;
- post-purchase setup, service, ownership, and repeat purchase.

Use imagery to prove and create desire where it helps, but keep factual selection attributes legible. Conversion may be purchase, reserve, test, configure, contact, visit, or another action; the business and user journey decide.

## 8. Service and Transaction Architecture

Model eligibility, preparation, evidence, submission, progress, decision, recovery, support, and status as one journey. Users should not need to understand the service provider's structure.

- Explain whether the service is relevant before demanding effort.
- Show required evidence and time/cost consequences early enough.
- Preserve entered work and provide a safe return path.
- Keep validation and recovery close to the problem.
- Explain progress and status in plain language.
- Provide assisted or alternative routes when the digital path cannot complete the outcome.

One-question-per-page, long form, wizard, review screen, dashboard, and document list are implementation candidates, not universal rules.

## 9. Editorial and Narrative Architecture

Model the relationship among issues, articles, authors, topics, archives, collections, events, paid products, and subscriber benefits. Preserve reading momentum while giving discovery and orientation clear roles.

- Let content voice and hierarchy carry identity where appropriate.
- Avoid interrupting the reading task with premature conversion.
- Make archives and related content meaningful, not a generic card field.
- Use motion or immersive composition only when it strengthens narrative, authorship, or spatial understanding and survives reduction.

## 10. Operational Architecture

Model domain objects, states, transitions, exceptions, urgency, ownership, history, and repeated actions.

- Optimize detect → understand → act → confirm → recover.
- Preserve the context needed to make a decision while acting.
- Keep scan paths and comparison axes stable.
- Use density where it reduces time and errors, not to demonstrate sophistication.
- Support keyboard loops, bulk actions, undo, and frequent re-entry when evidence calls for them.
- A dashboard is not automatically a card grid; use the information relationships that experts need.

## 11. Responsive Transformation

For every key experience, specify:

- invariants: outcome, priority, reading/task order, required content, state, and conversion;
- reorder and collapse rules;
- navigation transformation;
- disclosure changes and alternative controls;
- comparison and table behavior;
- imagery crop, substitution, or removal;
- fixed/sticky behavior and safe areas;
- pointer, touch, keyboard, hover, and gesture differences;
- long content, localization, zoom/text scaling, and orientation changes.

Choose breakpoints where the composition or interaction stops working. Always test at a pressure width between convenient presets.

## 12. Architecture Proof

Test candidates with real content and the smallest slice that can fail them:

- first-time and returning entry;
- known-item and exploratory discovery;
- comparison with realistic attribute differences;
- long labels and missing data;
- conversion readiness and hesitation;
- error, unavailable, out-of-stock, or permission failure;
- mobile reordering and intermediate width;
- keyboard/focus order and screen-reader landmarks;
- cross-channel handoff and return.

Reject an architecture when it requires users to understand the organization instead of their task, hides required evidence, fragments one outcome across unrelated paths, depends on ideal content, or becomes a generic template once decorative styling is removed.
