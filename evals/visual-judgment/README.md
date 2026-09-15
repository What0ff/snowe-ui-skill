# Visual judgment beyond technical validity

Four authored scan-manager candidates share the same content, font family and local data. `ATTENTION.json` was written before implementation and review. Its expected priorities concern the operator's current question in running, completed and failed states; it does not prescribe a universal palette or layout. This is sequential implementer self-review, not a blind trial, measured gaze or proof of future generation quality.

## Results after viewing the renders

| Candidate | Running | Completed | Error | Reason |
| --- | --- | --- | --- | --- |
| A | REVISE | REVISE | REVISE | Small muted current-run information competes with a much stronger new-run button. |
| B | KEEP | REVISE | REVISE | Progress emphasis is useful while running, but keeps dominating the result or recovery afterward. |
| C | KEEP | KEEP | KEEP | State-specific emphasis puts progress, the ready result or the affected kingdoms first. |
| D | KEEP | KEEP | KEEP | Restrained type and surfaces preserve useful distinctions. Its initial narrow running order was corrected after review. |

Every candidate passes the same technical checks. These visual verdicts were assigned by inspection and are recorded in `reviews/a.json` through `reviews/d.json`. The checker validates their consistency and freshness; it does not calculate those judgments. All user-acceptance fields remain UNCONFIRMED.

Compare the same error state: [A](captures/a-error-900.png), [B](captures/b-error-900.png), [C](captures/c-error-900.png), [D](captures/d-error-900.png). Narrow examples: [B error](captures/b-error-390.png), [C error](captures/c-error-390.png), [D running](captures/d-running-390.png). The named problem and recovery remain clear in the quieter D; a bright palette is not a passing criterion.

## Reproduce

From the repository root:

```powershell
node scripts/browser-smoke.mjs --smoke --scenario visual-judgment
node scripts/browser-smoke.mjs --capture-visual-judgment
python skill/snowe-ui-skill/scripts/visual_review.py evals/visual-judgment/reviews/c.json --workspace .
python -m unittest tests.test_visual_review tests.test_visual_judgment_cases -v
```

Checking A or B intentionally returns `2/BLOCKED`; that is a successful detection of the recorded unresolved finding. C and D return `0/PASS` for current recorded KEEP. A changed contract, source or render returns `3/REVIEW_REQUIRED`. Recapture does not rewrite reviews or turn them into KEEP: inspect changed evidence and explicitly update the report bindings and judgment.

The browser checks 24 PNG states (four candidates × three states × 900/390), identical comparison content, required-text visibility, overflow, keyboard opening/closing, kingdom disclosure, result preview and local recovery. An additional 200% text check covers the problem and recovery controls. `captures/evidence.json` binds sources, fonts, runner, images, states and sizes. Local Inter files/license are reused from the existing Title Bot pilot.

## Work and evidence boundaries

The examples use fictional data and no production API. Controls demonstrate local disclosure/result preview/retry only; New scan identifies a local scope and does not create a real job. This is a focused visual-evaluation surface, not a second production application or a replacement scan manager. Experiment names, expected verdicts and review commentary stay outside the captured customer surface.

The first D draft put a disabled result control before progress on narrow screens. That was found in visual review despite technical success; the running-state order was repaired and both widths inspected again. The eye icon represents opening a result; partial history uses its own state tone. The first keyboard probe also exposed that the canonical CDP Enter helper omitted its character text; it now sends the normal Enter text and the native button action is exercised.

The new report schema demonstrates a reliable distinction between method, verdict, evidence integrity and user acceptance. The examples demonstrate this author's scoped reasoning and corrections. They cannot establish an independent aesthetic standard, stronger future models or a general ban on quiet, native-looking or familiar interfaces.
