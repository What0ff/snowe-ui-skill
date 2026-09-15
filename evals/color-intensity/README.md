# Color intensity and contextual fit

This follow-up records a failed selection approach as well as its correction. The user first reported pale accents, then clarified that tables and dialogs also need a coherent page palette. The initial response solved only the accent pair. The later ocean/plum themes colored every major surface but were questioned as strange for this operator page. They are **rejected directions for this context**, not recommended palettes.

## Outcomes

| Example | Technical paint/contrast | Recorded visual result | Reason |
| --- | --- | --- | --- |
| Soft | PASS | REVISE | Does not settle the requested color direction; pale roles and default surfaces remain unexplained. |
| Vivid accent only | PASS | REVISE | Stronger action/status colors leave the rest of the page palette unresolved. |
| Ocean | PASS | REJECT | Large blue surfaces introduce an unsupported product identity. |
| Plum | PASS | REJECT | Harmonious violet tones are not sufficient justification for this product/task. |

The original hierarchy variants retain their own earlier scoped judgments: all 24 default hierarchy captures are byte-identical after the token split. A restrained system can be valid for its brief. Neither this rejection nor the user's feedback creates a universal ban on blue, purple, neutral or pastel interfaces.

## What changed in the skill

Color selection now explicitly starts from product context, accepted references/brand values, content and task, with a positive rationale before a hue family. Whole-page review covers canvas, working panels, table header/body/hover, dialogs, controls, typography and states. It does not require every surface to be colorful. Hue, chroma/saturation, lightness and area are separate decisions; a saturated or well-contrasted palette can still be unsuitable.

Fill, on-color text, accent foreground and interactive states are independent roles. In the vivid example, dark text on orange measures 6.591:1 normally, 7.391:1 on hover and 5.493:1 pressed. White on that orange is only 2.645:1. This demonstrates role pairing, not a prescription that all products should use orange or maximum saturation.

## Evidence and reproduction

`PALETTES.json` declares example paint expectations before implementation. `captures/evidence.json` binds the fixture/runner to 16 whole-page and eight modal captures at 900/390. The browser checks identical content/geometry, actual resolved colors, expected opacity, normal/hover/pressed paint, and table/modal coverage. The Python tests check current bytes and exact opaque contrast pairs. The small HLS comparison describes these examples; it is not a general perceptual or beauty score.

`CONTEXT.json` records a read-only frontend context snapshot. The current source contains dark working surfaces and orange accents in several feature owners, with a blue global accent also present; source is evidence to inspect, not automatic design approval. `ATTENTION.json` transcribes the user's contextual requirement for explicit review. `reviews/*.json` record self-review and open blocking findings. The rejected reports must remain blocked even though color-role and contrast tests pass.

```powershell
node scripts/browser-smoke.mjs --smoke --scenario visual-judgment
node scripts/browser-smoke.mjs --capture-visual-judgment
python -m unittest tests.test_color_intensity -v
python skill/snowe-ui-skill/scripts/visual_review.py evals/color-intensity/reviews/ocean.json --workspace .
```

The last command intentionally exits `2/BLOCKED`. This is correct acceptance behavior, not a failing test infrastructure. Rejected examples are retained for evaluation; no production palette is selected or deployed here. Future generation quality and independent aesthetic agreement are not established by these authored examples.

The final clarification was that the skill should choose appropriately on its own, not hand palette experiments back to the user. The design guidance therefore puts synthesis, full-context comparison and selection before theme implementation and user-facing delivery. This study exposed a selection failure; it does not demonstrate reliable autonomous color taste on new tasks. No third unsupported theme was proposed as a replacement.
