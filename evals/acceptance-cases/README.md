# Acceptance and continuation cases

Six fictional tasks exercise the revised workflow sequentially. This is implementer-authored work and self-review, not a blind evaluation, independent agent trial, causal improvement claim or automatic aesthetic score. The fixture contains both failing and repaired states; it is regression evidence, not a production application. Generic Open actions are static; the internal-list keyboard path and filter toggle are exercised separately.

## Tasks and findings

| Case / requirement | Before | Result and acceptance boundary |
| --- | --- | --- |
| `coherent`: retain editorial display, reading and identifier roles | Already coherent | KEEP. Georgia display, system reading text and mono identifier serve distinct roles. Before/after PNGs are byte-identical at both widths; no forced font-count reduction. |
| `typography`: repair role drift within peer service rows | One row switches to a serif and one Open action to monospace | REVISE → KEEP for the inspected typography. Peer roles share the text family; display heading remains distinct. |
| `custom`: represent completed route history without suggesting download | Downward arrow/tray implies a download action | REVISE → KEEP for the labelled 24px context. Original code-native route/stops glyph aligns with the feature and differs from the neighboring location pin. It does not claim standalone user recognition or smaller-size acceptance. |
| `backings`: remove individual passive backings while preserving controls | Repeated disks dominate labels; the shared wrapper also escapes the Settings button | REVISE → KEEP. Glyphs render directly beside labels, while the actual round button and selected filter retain their shapes. |
| `workspace`: bound an 80-row work panel and place its main action relative to that panel | Panel expands the document; action moves offscreen and has an arbitrary horizontal offset | REJECT → KEEP for bounded layout/keyboard behavior. A 440px/max-viewport panel keeps header/footer reachable; the min-height/overflow chain scrolls internally. Main action is centered in its owning panel; list text remains aligned for reading. German compounds and Arabic/Latin identifiers remain contained. |
| `resume`: extend the previously corrected service owner | Reintroduced backings repeat the earlier defect | REVISE → KEEP for rendered scope. The checked correction lifecycle separately blocks open work and stale proof; `memory-check.json` records the actual sequence. |

All distinct before/after images at 900 and 390 CSS widths were inspected; the unchanged coherent pair was also byte-compared. The workspace after capture includes focus on the named scroll region, reset to the top after keyboard End reaches the bottom. No complete assistive-technology or product-service certification is claimed.

## Reproduction and evidence

```text
node scripts/browser-smoke.mjs --capture-acceptance-cases
node scripts/browser-smoke.mjs --smoke --scenario acceptance-cases
python -m unittest tests.test_visual_acceptance tests.test_corrections -v
```

`captures/evidence.json` binds the fixture and all 24 lossless PNGs to exact hashes and measured states. The tests verify image geometry/freshness, not appearance. Main browser smoke covers these six cases along with the existing benchmark and icon scenarios. Correction-history transitions, independent scope, stale/lost evidence, supersession, atomic-write failure and concurrency are separate Python regressions.

## Resolved execution failures

New localization tests first failed on the missing language contract. Migration tests first failed on absent migration APIs. The existing audit reproduced accepted weight 800 and long-label overflow before the fixes. During implementation, integration failures exposed a missing slug-helper argument, native font family aliases, modal focus-state contamination between tests, metadata overflow at 200% text, and premature keyboard-scroll capture. Those causes were corrected and targeted checks rerun. A Windows default-encoding edit was detected by the remaining critical-clause checks and repaired to UTF-8. Test-state navigation resets isolate dialog/font probes from the existing interaction suite; their failures are not suppressed.

Remaining boundaries: variable-axis matching checks declared/computed settings and pinned font files, not an independent font-engine certification. Snapshot review is self-review. The journal verifies recorded evidence integrity and cannot certify that an arbitrary reviewer told the truth or that every future agent follows the skill.
