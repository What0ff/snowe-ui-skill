# Isometric illustration examples

Demo scenes for `skill/snowe-ui-skill/scripts/iso.py`. They are repository-only visual evidence of what the generator draws; none of these files ships with the skill.

| Scene | What it shows |
| --- | --- |
| `data-platform.scene.json` | Events, CRM and log sources flowing through ingest and the processing core into lake and warehouse storage and out to BI, API and ML apps. A chevron composition puts the core at the front vertex; the accent follows one path from events to BI. |
| `data-platform-narrow.scene.json` | The same flow re-arranged for a 390 px column: four objects in a +x/+y staircase, 244 px wide at its natural size, so labels stay at 11 px instead of shrinking. |
| `agent-hub.scene.json` | A team building sending requests to an orchestrator chip that dispatches research, code and review agent cards and returns a report. The accent follows one request to the code agent. |

For each scene the directory holds the generated `.svg` and `.manifest.json` and captures at 1x and 2x in the light theme and in a dark theme (`-dark`) that only redefines the `--iso-*` custom properties.

## Render

```powershell
node docs/iso-examples/render.mjs            # every scene
node docs/iso-examples/render.mjs agent      # scenes whose name contains "agent"
```

The script needs Node 22, Python 3.11+ and a system Chrome (set `CHROME_PATH` for another browser, `PYTHON` for another interpreter). It runs `iso.py render` under `python -I`, inlines each SVG into a page so the custom properties apply, blocks network access and captures it with headless Chrome. The committed PNGs were captured on Windows with Segoe UI, so labels render with other fonts elsewhere.

`tests/test_iso.py` checks that the committed `.svg` and `.manifest.json` files equal what the current generator produces and that no scene raises a label-fit warning. After changing `iso.py` or a scene, re-render and inspect every changed PNG at real size; the tests cannot judge composition.

Keep scene domains away from the measurement briefs in `evals/skill-outcome/briefs.json`.
