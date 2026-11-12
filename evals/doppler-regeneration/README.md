# Doppler: current observation and integrity regression

This evaluation uses the repository's Doppler site, as requested. `before-complete/` retains seven historical full-page captures and their original receipt; their sources/observer/plan have since changed, so they are historical comparison material, never current PASS. The baseline source revision is `92eeb724fcfa889cafe8cb47c219b7e80a8e2635`. Current source, plan and final evidence supersede it without rewriting accepted history.

`PLAN.v3.json` is the current explicit scoped observation matrix, not an automatic task classifier. Its 15 cases cover wide, pressure, narrow, touch/keyboard/pointer, dark environment, static/reduced, flavor, menu, confirmation and temporal contexts. `verified/receipt.json` binds 15 whole-page images, 15 native viewports, 65 owner/detail images and 72 timed frames. Theme emulation does not assert that this deliberately light campaign has a separate dark skin. Fixed/top-layer details are cropped from the exact native viewport parent, not a later whole-page capture.

`integrity_control.py` loads the previous validators from that exact commit and reproduces mobile removal, viewport relabelling, omission of changed CSS, and new visual verification without method/KEEP. Previous code returns PASS; current code requires review or refuses verification. These controls measure integrity only. Synthetic unit fixtures have no aesthetic meaning.

`scripts/doppler-detail-probe.mjs` copies the complete product and the Doppler target into an isolated temporary workspace, runs the general installed observer, injects six concrete construction/visibility/host defects, restores them, and checks the resulting report with the copied Python validator. A positive paint-survival check guards against an invisible but structurally attached lid. Integrity PASS with visual UNKNOWN is the required result. The installed observer has no benchmark imports or package dependencies.

`SYSTEM.v1.json` through `SYSTEM.v3.json` preserve direction/map revisions and previous-byte bindings. `ATTENTION.v3.json` and `REVIEW.v3.json` are the current authored criteria and immutable review; `REVIEW.json` is its current alias. `PLAN.json`, `ATTENTION.json`, `final/` and `review-history/REVIEW.v2.json` preserve the earlier review. Rejected joint/focus/replay examples remain in `review-history/`; historical records are never rewritten into current proof. The original accepted campaign ledger is byte-preserved and checked against `ledger.sha256`.

The final browser receipt binds actual Chromium product/user agent, CSS viewport/DPR, environment, complete scoped source/resource inventory, font/layer measurements, whole/detail PNGs and a timed motion sequence. `build_review.py` binds the **authored** direction/map/relationships to a supplied receipt; it defaults to UNKNOWN and never selects a verdict from metrics. KEEP can be recorded only after the implementer inspects the actual images and sequence. The report is self-review, and user acceptance remains UNCONFIRMED.

Run from repository root:

```powershell
python evals/doppler-regeneration/integrity_control.py
node scripts/doppler-detail-probe.mjs
node scripts/browser-smoke.mjs --smoke --scenario soda-campaign
node skill/snowe-ui-skill/scripts/observe.mjs capture . evals/doppler-regeneration/PLAN.v3.json <fresh-output-directory>
python evals/doppler-regeneration/build_review.py <receipt.json> <review.json>
python skill/snowe-ui-skill/scripts/visual_review.py <review.json> --workspace .
```

Host evidence for this change is Windows/Python 3.11/Node 22/system Chrome. CI is configured for Ubuntu and Windows but has not been executed remotely by this task. The regenerated page is a whole-direction comparison with changed headline/copy, not a controlled single-variable beauty experiment. There is no beauty score, independent aesthetic review, repeated-model generation study or demonstrated causal effect on future model behavior. A self-reviewed result does not erase the user-found artifact or establish user acceptance.

Final local validation on 2026-10-08: Python compilation; 250 regression tests (one Windows directory-symlink capability skip); 18 deterministic KEEP findings; canonical browser smoke across all five benchmarks and the icon, acceptance, density, Title Bot, visual-judgment and color scenarios; copied six-defect probe; paired historical/current integrity control; all five SVG/metadata checks; skill, contributor-context and atlas checks. At that date the review and correction journal returned PASS, user acceptance remained UNCONFIRMED, and the accepted ledger digest was unchanged. Since 2026-11-12 the observer (`observe.mjs`) has changed (Space-key replay, sandbox and browser discovery), so these receipts are bound to an older observer revision and both now report `REVIEW_REQUIRED`; a fresh capture plus a new inspected review is needed before PASS can be claimed again. Seven showcase JPEGs and the GIF were refreshed from current browser output. No commit, push, PR or deployment was performed.
