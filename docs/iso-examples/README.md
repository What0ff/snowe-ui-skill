# Isometric illustration examples

Demo scenes for `skill/snowe-ui-skill/scripts/iso.py`. They are repository-only visual evidence of what the generator draws; none of these files ships with the skill.

| Scene | What it shows |
| --- | --- |
| `data-platform.scene.json` | Events, CRM and log sources flowing through ingest and the processing core into lake and warehouse storage and out to BI, API and ML apps. A chevron composition puts the core at the front vertex; the accent follows one path from events to BI. |
| `data-platform-narrow.scene.json` | The same flow re-arranged for a 390 px column: four objects in a +x/+y staircase, 244 px wide at its natural size, so labels stay at 11 px instead of shrinking. |
| `agent-hub.scene.json` | A team building sending requests to an orchestrator chip that dispatches research, code and review agent cards and returns a report. The accent follows one request to the code agent. |
| `orchestration-hub-v2.scene.json` | Schema 1.1 in the `technical` style: record, contract and app tiles feed a plaza with a curtain-wall tower, an office with entrance, canopy and roof sign, and two tree groups; the office hands work to an exploded `core` whose inverted cap carries a `glyph.py` icon; ground routes with risers end in ports on intake, billing and dispatch agent tiles; a dashboard reports the result. The accent follows a contract through billing. |

For each scene the directory holds the generated `.svg` and `.manifest.json` and captures at 1x and 2x in the light theme and in a dark theme (`-dark`) that only redefines the `--iso-*` custom properties.

The three schema 1.0 scenes are frozen regression evidence: `tests/test_iso.py` pins their SVG digests from before schema 1.1, so 1.1 work cannot change them.

## Icons

`icons-src/relay-agents.json` is a `glyph.py` spec (outline only) for the intake, billing, dispatch and hub glyphs; `icons/` is its build output, which the v2 scene loads through `icons`. The tests rebuild the spec and compare every file byte for byte. Rebuild after editing the spec:

```powershell
python skill/snowe-ui-skill/scripts/glyph.py build docs/iso-examples/icons-src/relay-agents.json -o docs/iso-examples/icons
```

## Animation

`animated.html` embeds the generated v2 SVG between `<!-- iso-scene: orchestration-hub-v2 -->` markers and adds page CSS and JavaScript only: a dot travels along every `.iso-path` with `getPointAtLength`, staggered by `data-order` and appended inside its connector group so objects in front still cover it; the accented agent card pulses gently; an `IntersectionObserver` and `visibilitychange` pause everything off-screen; `prefers-reduced-motion` shows the complete static frame. `render.mjs` refreshes the embedded SVG, and the tests check that it matches the committed file.

## Render

```powershell
node docs/iso-examples/render.mjs            # every scene
node docs/iso-examples/render.mjs agent      # scenes whose name contains "agent"
```

The script needs Node 22, Python 3.11+ and a system Chrome (set `CHROME_PATH` for another browser, `PYTHON` for another interpreter). It runs `iso.py render` under `python -I`, inlines each SVG into a page so the custom properties apply, blocks network access and captures it with headless Chrome. The committed PNGs were captured on Windows with Segoe UI, so labels render with other fonts elsewhere.

`tests/test_iso.py` checks that the committed `.svg` and `.manifest.json` files equal what the current generator produces and that no scene raises a label-fit warning. After changing `iso.py` or a scene, re-render and inspect every changed PNG at real size; the tests cannot judge composition.

Keep scene domains away from the measurement briefs in `evals/skill-outcome/briefs.json`.
