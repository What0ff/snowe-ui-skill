# Evaluating Snowe Itself

Repository-only guidance for maintainers who change the skill and need to know whether the change improved agent behavior. It moved here from the installed `designer-evaluation.md`, which now covers only evaluating a design. The concrete harnesses are [creative-search](creative-search/README.md) and the no-skill / before / after [skill-outcome](skill-outcome/README.md) comparison.

## Build a Scenario Portfolio

Use materially different businesses, user contexts, content structures, stakes, platforms, and conversion/task goals. Include sparse and dense products, commerce and non-commerce, repeat work and first-time persuasion, identity-led and utility-led contexts, and at least one brief where imagery or motion is likely unnecessary.

Do not encode the expected layout, style, image choice, or number of candidates in the brief. Keep scenario facts stable between revisions. Prevent the evaluated agent from seeing the evaluator's diagnosis or intended answer.

Add adversarial cases that expose known failure modes, such as ambiguous vocabulary, multilingual content, long prices/titles, incomplete product data, high stakes, keyboard-first work, or an existing visual system that should be preserved.

For visual acceptance, include technically valid but weak outcomes: an unclear emphasis, a priority that stays wrong after the task state changes, a corrected candidate on the same content, and a justified restrained interface. Inspect their renders before assigning visual verdicts. The technical suite should pass the legible weak cases while the visual review records their actual weaknesses. A rejected example is successful evaluation evidence only when the diagnosis and scope are credible.

## Paired Cases for Specific Changes

Each pairs misuse with a legitimate use of the same treatment, so success means repairing the cause rather than banning a shape:

- **Visual acceptance:** decorative capsules that compete with actions, functional selected/removable filters, and an explicitly accepted rounded brand system. Add a radius-only revision that leaves weak grouping intact, a quiet but poorly organized alternative, and missing rendered evidence. Zero pills, extra paperwork, and an automatic preference for plainness are not success criteria.
- **Density:** an oversized repeated-use workspace that already passes overflow, alignment and font checks, with content held constant across empty, sparse and populated states. Add a tighter challenger with readable text and targets, plus a deliberately spacious reading case that should stay unchanged. Look for cumulative padding and min-height causes rather than shrinking every size.
- **Typography:** deliberate display/text/code roles, arbitrary family changes among equivalent cards, a native control or portal that loses inheritance, a loaded subset that lacks required glyphs, and a weight mapped to the wrong file. Add an explicit reference and a correct multilingual fallback as counterexamples. Success is repairing role drift while keeping meaningful contrast, not minimizing font count.
- **Visible numbering:** unordered benefits beside a genuine dependent process, chapter cross-references and an explicitly numbered supplied design, including CSS counters and a renamed index. Success removes unsupported sequence cues and keeps useful numbering.
- **Correction memory and icon backings:** a new context where the same failure mechanism applies and one where the same shape has a valid different role, including renamed class or pseudo-element backings, a selected control, an approved reference, a superseding instruction and an unavailable-proof case. A remembered local preference must neither vanish in its scope nor become a global prohibition.
- **Identity, custom icons and alignment:** third-party marks beside an original identity, a learned action, a domain symbol and a text-only fallback; a caption-expanded field wrapper that shifts adjacent actions; long and wrapped text; a deliberately staggered accepted target. For more custom-icon exploration, add an approximate library match for a distinctive concept, a conventional action that should stay, a custom metaphor that asserts the wrong state, and a draft that only works enlarged. More SVG files is not success.
- **Surfaces, stability and copy:** a workspace with several secondary tasks, async loading and a recoverable save failure, judged on surface allocation, frame stability and visible text (see the skill-outcome cases).

Use held-out tasks after developing a lesson; do not tune a scenario until it produces the desired verdict.

## Compare Revisions Fairly

Freeze held-out briefs before editing the skill. Use immutable complete skill copies (and a no-skill control), isolated fresh host contexts, identical prompts, content and tools, and repeated runs with balanced condition order. Preserve unsuccessful runs and raw usage and timing. Do not prescribe a candidate count, metaphor, palette or expected winner.

Compare visible organizing differences and finished artifacts before exposing rationale or condition labels. Record invention, fit, coherence, responsive and content resilience, technical and behavioral failures, and unnecessary process separately. Look for:

- newly opened solution space;
- better selection reasoning;
- reduced recipe anchoring;
- fewer unnecessary assets and effects;
- improved rendered outcome and UX resilience;
- added process cost that did or did not change the result.

Separate the implementer's rationale from the acceptance pass: give a fresh evaluator the brief, artifacts, viewports, states and applicable skill, and withhold the intended winner until its first findings are recorded. Label self-review as self-review. A stronger rejection record is evidence about that review, not proof that future generated designs improve; that claim needs repeated generation and rendered comparison across briefs. Keep useful regressions when a change weakens an established invariant, and remove tests that merely require obsolete prose.
