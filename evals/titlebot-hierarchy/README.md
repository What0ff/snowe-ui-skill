# Title Bot hierarchy pilot

An isolated, functional application with fictional local data. It follows the inspected Title Bot contracts; it does not call the production backend or modify the working frontend. All operations reset on reload. This is implementer-authored work and self-review, not an independent agent trial or proof of future generation quality.

The user-provided [baseline](baseline.png), [source snapshot](sources.json) and [page map](PAGE-MAP.md) precede the implementation. The comparison retains the dark palette, Inter and existing title icon paths. The reference attribute is hierarchy in [Cloudflare's security dashboard](https://blog.cloudflare.com/security-overview-dashboard/), rather than its public marketing homepage or palette.

## Run and verify

From the repository root:

```powershell
python -m http.server 8080 --bind 127.0.0.1
# Open http://127.0.0.1:8080/evals/titlebot-hierarchy/
node scripts/browser-smoke.mjs --smoke --scenario titlebot-hierarchy
node scripts/browser-smoke.mjs --capture-titlebot
python -m unittest tests.test_page_hierarchy tests.test_corrections -v
```

No build, npm install, database or API credentials are needed. For inspection, URL parameters choose explicit states: `lang=ru`, `state=empty|loading|error|readonly`, or one local failure `fail=save|advance|remove|add`. `delay=650` keeps pending state observable. These controls belong to the test URL, not the customer interface.

## Contract and action coverage

| Surface | Operation / target / result | Verification |
| --- | --- | --- |
| Title tabs | Select a title / title key / its workspace | Distinct holders, queues, durations and action targets; Arrow/Home/End keys. |
| Settings | Open settings / kingdom / settings dialog | One entry. A differently labelled duplicate reaches this same handler and is detected by the action audit. |
| Duration editor | Save / kingdom settings / normalized settings | Global/per-title regular and VIP modes, ranges, VIP-only title scope, invalid input, cancel, save, failure and retry. |
| Assignment | Confirm then advance/release / selected title / next holder or vacancy | Cancel preserves state; confirmed operations change only the selected title. |
| Queue | Remove / title + player ID / queue entry removed | Separate player targets remain separate valid actions. Repeated submit is guarded. |
| VIP | Lookup, add, remove / player ID / VIP membership | Local search, independent list, mutations and read-only access. |
| Blocked players | Add or remove / player ID / blocked membership | ID validation, duplicate membership guard, mutations and read-only access. |
| Commands | Toggle disclosure / selected title / request aliases | Domain commands and player IDs stay available. |

The app registers action identity as `operation + target + outcome + context`; the runner exercises the associated handlers and state results. The generic checker cannot infer business meaning from arbitrary handlers. An explicitly justified duplicate-entry counterexample and independent per-row operations are preserved.

## Evidence and limits

- Thirty lossless captures cover 320/390/900/1440, 200% text, Russian, all title contexts, long/empty queues, settings, confirmation, lists, pending, failures, loading, error and view-only. The narrow Russian settings dialog also has a bottom-scroll capture.
- `captures/evidence.json` binds application, fixture, source snapshot, local fonts, runner files, images, dimensions and state. `tests/test_page_hierarchy.py` checks those bindings. Review findings live separately in `REVIEW.json`; its evidence digest prevents silently reusing an old review after recapture.
- `scripts/ui-proof.mjs` checks declared information for presence, style/ancestor visibility, opacity, accessible names, clipping and sampled occlusion. Opacity-zero, clipped and opaque-overlay mutations must fail. This is sampled geometry/DOM evidence, not exhaustive pixel/contrast or aesthetic certification.
- Native accessibility-tree names, real pointer input, keyboard focus, modal boundaries/return focus, local errors and external-request absence are checked. The test-only snapshot is read-only; transitions run through DOM handlers.
- Pilot typography evidence is the preserved font files, CSS roles and rendered review. An optional CDP per-glyph probe triggered a reproducible inspector `ERR_CACHE_MISS` after enabling its CSS domain; it is not included as passing pilot evidence. Existing canonical Goodturn actual-font/role regressions remain separate.
- Technical contract, evidence integrity, visual self-review and user acceptance are separate dispositions. User acceptance of the revised candidate is unconfirmed. One authored pilot does not establish durable model taste or generalization.

## Reproduction and corrections

The initial memory probes retained PASS after editing requirements, criterion text or proof; a scope edit hid an earlier obligation. They now require review until explicit verification. The original opacity-zero density probe passed its DOM/bounds inventory; the new required-content check rejects it, clipping and overlap.

The first pilot failed enlarged-text navigation; intrinsic room and wrapping fixed it without deleting labels. Visual review then rejected a broken Russian word despite valid bounds, so narrow Russian title navigation uses full-width rows. The first technical screen was also too close to stock admin styling: the revised candidate groups assignment facts in one surface and gives controls a consistent treatment while keeping the comparison palette and font.

Focus tests initially used programmatic `click()` and did not reproduce pointer focus. Pilot tests now dispatch real pointer events. Native dialog Tab can visit browser chrome; the check rejects background controls and verifies return to dialog controls. These harness corrections do not masquerade as application defects.

Experimental notices and instructional copy were removed from the customer surfaces in `evals/density` and `evals/acceptance-cases`; their disclosures remain in their reports. These older fixtures remain authored regressions, not finished product designs.

Final render review found a real recovery defect: on narrow settings, the error was at the bottom of the scrolling form. A new required-error visibility assertion first failed despite the existing text-presence check. The message now has a persistent dialog-owned area next to the footer actions; the same check passes for all four failure paths. Dialog captures use the actual viewport; page captures may include the full page, avoiding artificial backdrop gaps below a fixed modal.

The same failure-path regression reproduced focus loss when pending controls were disabled. Failed operations now restore the initiating control by its stable identity, including queue rows recreated during render. The browser test checks the visible error and retry focus together.
