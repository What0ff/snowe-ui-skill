# Test and Validation Matrix

## Environment

- Installable product/test runtime: Python 3.11+ standard library.
- Repository browser smoke/capture: Node 22 plus system Chrome/Chromium; no npm install; CI covers Ubuntu and Windows.
- Public showcase deployment: GitHub Pages custom workflow uploading `benchmarks/soda-campaign/` without a build step.
- Working directory: repository root.
- CI covers the strict public contributor-context/atlas contract on Ubuntu/Python 3.13, Python 3.11/3.13 regressions on Ubuntu/Windows, deterministic contracts on Ubuntu/Python 3.13, and browser smoke on Ubuntu/Windows with Node 22.

## Canonical checks

### Runtime compilation

```powershell
python -m compileall -q skill/snowe-ui-skill/scripts
```

Checks installable Python syntax/import compilation. It does not validate Markdown, CSV semantics, aesthetics, browser behavior, or atlas files.

### Full regression suite

```powershell
python -m unittest discover -s tests -v
```

Current inspected result: **86 tests pass**.

- `tests/test_snowe_ui_skill.py`: package routing/docs, schema-3 unresolved framing, multilingual/ambiguity/unknown behavior, opt-in analogs, persistence/path safety, evidence deletion/schemas/claims, icon constraints, contrast, SVG, and CLI.
- `tests/test_bicycle_benchmark.py`: Goodturn commercial content, local/provenanced assets, semantics, interactions, responsive/reduced motion, design trace, and screenshot coverage.
- `tests/test_forward_benchmarks.py`: three causal experience classes, deliberate absences, local semantic implementations, responsive/motion contracts, cross-comparison, completed QA/findings, screenshots, and CI/browser commands.
- `tests/test_soda_benchmark.py`: local/semantic product content, flavor/conversion disclosure, motion/responsive/reduced ownership, complete design trace/provenance, local SVG safety, screenshot/GIF evidence, README/live-URL positioning, Doppler smoke contracts, and Pages workflow/artifact-root contracts.
- `tests/test_installation.py`: fresh exact install, stale-file-free reinstall, interrupted-run recovery, staging-failure cleanup, activation rollback, source/destination containment, exact public CLI copy, and current installation guidance.

Focused examples:

```powershell
python -m unittest tests.test_snowe_ui_skill.DecisionPacketTests -v
python -m unittest tests.test_snowe_ui_skill.RetrievalTests -v
python -m unittest tests.test_forward_benchmarks -v
python -m unittest tests.test_bicycle_benchmark -v
python -m unittest tests.test_soda_benchmark -v
```

### Deterministic designer-contract regression

```powershell
python evals/designer-behavior/run_eval.py
```

Current inspected result: **17 `KEEP` findings**, no `REVISE`/`REJECT`. Coverage includes six businesses, English/Russian/mixed equivalence, ambiguous vocabulary, unknown domain, unresolved pressure, paraphrase stability, meaningful business change, coherent-system preservation, no-image/no-motion/custom rejection, dataset absence, authored progressive-disclosure fixtures, and semantic/evidence boundaries. Output marks deterministic contracts as measured, rendered/browser regression as separate, and observed real-agent behavior as not measured. It contains no creativity/layout/style score.

### Benchmark JavaScript and browser smoke

```powershell
node --check benchmarks/bicycle-commerce/app.js
node --check benchmarks/soda-campaign/app.js
node --check benchmarks/forward-tests/municipal-service/app.js
node --check benchmarks/forward-tests/warehouse-operations/app.js
node --check benchmarks/forward-tests/literary-publication/app.js
node --check scripts/browser-smoke.mjs
node scripts/browser-smoke.mjs --smoke
```

Smoke starts a loopback server and isolated headless Chrome, then exercises all five benchmarks at 1440, 900, and 390 widths; benchmark-specific interactions/focus; mobile navigation; broken assets/network/runtime/console errors; horizontal overflow; dialog semantics; and reduced-motion emulation. Doppler additionally checks 48/40/32 product segments, one attached lid layer, keyboard and pointer-drag yaw, synchronized flavor state, front-facing revolution completion, six-pack validation/confirmation, finite animation cleanup, and its authored static reduced mode. Browser shutdown is awaited and temporary-profile removal retries bounded transient locks but remains a hard failure if cleanup cannot complete.

Regenerate the 18 forward-test and seven Doppler captures only after validated visual changes:

```powershell
node scripts/browser-smoke.mjs --capture
```

For Doppler-only correction/rerender work:

```powershell
node scripts/browser-smoke.mjs --capture-soda
$env:SODA_MOTION_DIR = "<empty-temporary-directory>"
node scripts/browser-smoke.mjs --soda-motion-frames
```

The motion-frame command captures 72 PNGs from the live implementation; it does not define a repository image-encoder dependency or overwrite `hero-motion.gif`.

### Low-level assets

```powershell
python skill/snowe-ui-skill/scripts/asset_quality.py `
  benchmarks/bicycle-commerce/assets/icons/fit.svg `
  --metadata benchmarks/bicycle-commerce/assets/icons/fit.metadata.json

python skill/snowe-ui-skill/scripts/contrast.py "#151a17" "#f2eee3" --minimum 4.5
```

### Manual rendered review

Serve the repository root and inspect implementations, not only screenshots:

```powershell
python -m http.server 4173 --bind 127.0.0.1
```

Current hardening pass reviewed desktop/intermediate/mobile, menu/dialog/error/result/focus states, keyboard operation, scroll/composition, and console output in the in-app browser. Doppler also includes normal/reduced product states and intermediate rotation frames; a user-supplied tight crop exposed a lid-occlusion defect that was corrected, regressed structurally, and fully rerendered. Findings/fixes live in each benchmark's `QA.md`; cross-scenario conclusions live in `benchmarks/CROSS-BENCHMARK.md`.

For Pages-root compatibility, serve Doppler itself as the server root and verify `/`, assets, fresh hash entry, and interactions:

```powershell
Set-Location benchmarks/soda-campaign
python -m http.server 4174 --bind 127.0.0.1
```

### Contributor-context boundary

```powershell
python scripts/check_contributor_context.py
```

Checks that every required durable context file is present and Git-visible, public guidance/tooling is not ignored, private task/session probes are ignored, no private path class is tracked, root guidance makes the local checkpoint optional, and the generated map contains no local-state marker. The normal working-tree mode permits new nonignored public additions before staging.

Fresh-clone/CI validation is strict:

```powershell
python scripts/check_contributor_context.py --require-tracked
```

The strict mode additionally fails if any required public context file is absent from the Git index.

### Atlas freshness

```powershell
python scripts/atlas/generate_atlas.py --write  # structural changes only
python scripts/atlas/generate_atlas.py --check
```

`--check` must report `Atlas structural map is up to date.` before completion.

## CI jobs

| Job | Surface |
|---|---|
| Public contributor context | Strict tracked public/private boundary plus atlas freshness on Ubuntu/Python 3.13. |
| Python matrix | compile + 86 unittests on Ubuntu/Windows, Python 3.11/3.13 |
| Designer behavior | behavior runner on Ubuntu/Python 3.13 |
| Rendered benchmark smoke | Node 22/system Chrome CDP on Ubuntu and Windows, five-minute timeout per matrix job |
| Doppler Pages deployment | Path-filtered static artifact upload/deploy to the `github-pages` environment |

Normal CI triggers on pushes to `main`, pull requests, and manual dispatch with read-only permissions. Pages triggers only on `main` changes beneath `benchmarks/soda-campaign/`, changes to its workflow, or manual dispatch; it adds only `pages: write` and `id-token: write` required for deployment.

Normal CI does not run manual aesthetic review, lint/format/type/coverage, packaging, deployment, or release validation. The separate Pages workflow publishes only the validated static Doppler artifact and performs no aesthetic certification or benchmark build.

## Change-to-test routing

| Changed area | Minimum evidence before full suite |
|---|---|
| `SKILL.md` / references | Package/reference tests, relevant behavior assertions, progressive trace, rendered proof when output behavior changes. |
| `decision_packet.py` | DecisionPacket/Persistence/CLI tests, behavior runner, representative English/Russian/ambiguous JSON/Markdown smoke. |
| `core.py` / CSV data | Retrieval tests, domain/stack evidence-role and URL-coverage audit, obsolete-domain and numeric-claim scans. |
| `search.py` | CLI tests, `--help`, explicit domain/stack/packet/analog examples. |
| Asset/contrast validators | Focused unit tests plus every affected real asset/pair and rendered optical/contextual review. |
| Behavior scenarios/runner | Runner output review; no expected layout/style encoding. |
| Goodturn | Bicycle suite, JS check, browser smoke, affected states/screenshots/manual QA. |
| Doppler | Soda suite, JS check, five-benchmark smoke, affected normal/reduced/transition captures, GIF, QA, and cross-comparison. |
| Forward-tests | Forward suite, all affected JS, browser smoke, captures, QA, and cross-comparison when causal dimensions change. |
| Browser script/CI | Node syntax, local smoke on system Chrome, CI contract test, platform/path review. |
| Installer/public install docs | Installation tests for exact fresh/repeated copies, rollback/recovery, path overlap, public CLI, and stale legacy-command removal. |
| Pages workflow/live URL | Soda suite, folder-as-root asset/hash/interaction audit, workflow syntax/run result, Pages settings read-back, and public URL browser verification. |
| Repository structure or context boundary | Contributor-context check, atlas `--write` then `--check`, fresh-clone simulation, complete status/diff/ignore inspection. |

## Missing command surfaces

No local command currently provides linting/formatting, static typing, coverage, package/plugin build or publication, visual-diff approval, full accessibility-engine audit, or backend integration validation. Exact standalone-copy installation is tested; GitHub Pages deployment exists only through its hosted workflow. Do not invent or report unavailable checks as executed.
