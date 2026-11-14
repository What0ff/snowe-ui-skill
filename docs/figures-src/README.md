# Reference figure sources

HTML sources for the PNG figures in `skill/snowe-ui-skill/references/figures/`. Only the rendered PNGs ship with the skill; these sources and the render script stay in the repository.

## Render

```powershell
node docs/figures-src/render.mjs              # every source
node docs/figures-src/render.mjs geometry     # sources whose file name contains "geometry"
```

The script needs Node 22 and a system Chrome (set `CHROME_PATH` for another location). Each page declares its output in one tag, `<meta name="figure" content="name.png WIDTHxHEIGHT@SCALE">`. The script renders that fixed CSS viewport and device scale with headless Chrome, blocks network access, writes the PNG next to the references and prints each size. It exits non-zero when a figure exceeds 120 KB.

The committed PNGs were rendered on Windows with its system fonts (Segoe UI, Segoe UI Variable, Bahnschrift, Georgia, Segoe UI Emoji). Other systems substitute fonts, so re-render on Windows to keep the committed look.

## Figure rules

- A pair shows the same content; only the variable under test changes. Shared parts live in one stylesheet per pair or set (`attention.css`, `dropdown.css`, `surface.css`, `geometry.css`, `icon-style.css`). The landing pair is the exception: its variable is the whole direction, so each page carries its own styles.
- System fonts only, no web fonts and no remote resources.
- Keep each PNG at or under 120 KB; the whole figure set ships in every install.
- Never use the domains of the measurement briefs in `evals/skill-outcome/briefs.json`.
- After rendering, open every changed PNG and confirm that each caption that uses it in `references/` is literally true.

`dialog-resolved.png`, `lid-artifact.png` and `lid-repaired.png` are captures of the Doppler benchmark (`benchmarks/soda-campaign/`) and have no source here.
