# External Dependencies and Integrations

## Installable product runtime

| Dependency | Evidence | Role |
|---|---|---|
| Python 3.11+ | README, contributor docs, CI matrix | Runs retrieval, decision packets, validators, eval runner, atlas generator, and tests. |
| Python standard library | Imports and absence of package manifests | `argparse`, `csv`, `json`, `pathlib`, `re`, XML parsing, `unittest`, and related modules. |

There is no `pyproject.toml`, `requirements.txt`, package-manager lockfile, package manifest, virtual-environment bootstrap, or third-party product/test package. The short-lived installer and per-project persistence locks plus atomic filesystem operations use only operating-system facilities exposed by the standard library.

`scripts/install_skill.py` is a repository-only Python standard-library installer. It copies the existing installable directory exactly to `$HOME/.agents/skills/snowe-ui-skill` by default, supports an explicit compatible-host destination, and does not add an installable-product dependency or package format.

## Agent host and design tools

The installable directory targets Codex and compatible hosts that discover `SKILL.md` and follow linked references. The host may provide current web research, image generation, browser inspection, or repository tools. Snowe decides when those capabilities add value, but the copied skill does not implement, authenticate, or require a particular external service.

The Python CLI is local. It contains no HTTP client, socket, telemetry, secret, auth flow, external model call, or installer. URLs in evidence rows are returned but not fetched or verified.

## Benchmark assets/runtime

All five benchmarks are dependency-free HTML/CSS/JavaScript with no build step, CDN, analytics, backend, form endpoint, or runtime network dependency. Doppler is additionally published as a static GitHub Pages showcase from its checked-in folder.

Goodturn additionally commits:

- Barlow Condensed and Manrope WOFF2 plus OFL texts;
- four generated WebP images reviewed in layout;
- three original custom SVG icons plus pinned Lucide Repeat2 and X SVGs, JSON provenance/drawing-language/structured-evidence metadata, and the Lucide license notice;
- nine JPEG browser captures.

The three forward-tests intentionally use no image or custom-asset files; their identity comes from content, typography, state, structure, and interaction. Each commits six JPEG captures.

Doppler commits local Unbounded/Manrope WOFF2 files and OFL texts, three original SVG label textures, seven JPEG captures, and one optimized browser-derived GIF. Its product scene is HTML/CSS/JavaScript rather than an image/model/video dependency; no generated imagery is used.

Image generation and external research created Goodturn evidence during development. Doppler's final GIF was encoded from Chrome-captured local frames with a host-provided image encoder; Pillow is not a repository runtime/test dependency. Reproducing those development artifacts requires a capable host, but using/testing the committed benchmarks does not.

The repository-only icon-decision proof includes pinned Lucide X, Ruler, and BadgeCheck SVG bytes plus local Lucide license records, one original rejection challenger with a local source record, and the existing Goodturn fit asset. Their metadata binds structured local source/license bytes and official HTTPS source revisions; external URL truth remains explicitly unverified. No runtime fetch occurs.

## Repository browser infrastructure

`scripts/browser-smoke.mjs` requires Node 22 and a locally installed Chrome/Chromium only when running rendered smoke or captures. It uses Node built-ins (`http`, `fs`, `child_process`, `os`, `path`, global `fetch`/`WebSocket`) and Chrome DevTools Protocol directly. It does not use npm, Playwright, Selenium, chromedriver, or a downloaded browser.

The script starts a loopback-only temporary HTTP server, an isolated temporary browser profile, and a random debug port. Cleanup requests graceful browser close, waits for exit, forces and awaits termination when necessary, closes the server, and uses bounded retries for transient profile locks; remaining cleanup errors fail the command. `CHROME_PATH` can select a nonstandard browser executable. `--scenario <slug>` can focus smoke on one supported benchmark/proof; `--capture-goodturn-workshop` refreshes the Goodturn workshop evidence after icon changes; `--capture-soda` writes the seven final Doppler JPEG states; `--soda-motion-frames` writes 72 raw browser frames to the explicitly supplied `SODA_MOTION_DIR` and does not itself encode the committed GIF.

This is repository validation infrastructure, not an installable-skill dependency.

## CI dependencies

`.github/workflows/ci.yml` uses:

- `actions/checkout@v4`;
- `actions/setup-python@v5` with 3.11/3.13 on Ubuntu/Windows;
- `actions/setup-node@v4` with Node 22 for Ubuntu and Windows browser smoke;
- the system Chrome/Chromium available on each GitHub-hosted runner.

Its public contributor-context job uses only Python 3.13 standard-library code plus Git already present in the checkout environment. It runs `scripts/check_contributor_context.py --require-tracked` and the atlas freshness check; neither command adds an installable-product dependency.

Permissions are `contents: read`; CI performs no deployment, release, package publication, cache, credential write, or artifact upload.

`.github/workflows/pages.yml` uses the official Pages artifact flow:

- `actions/checkout@v4`;
- `actions/configure-pages@v5`;
- `actions/upload-pages-artifact@v3`, scoped to `benchmarks/soda-campaign/`;
- `actions/deploy-pages@v5` with the `github-pages` environment.

Its minimal workflow permissions are `contents: read`, `pages: write`, and `id-token: write`. Push triggers are path-limited to Doppler or the Pages workflow itself, with manual dispatch and non-canceling `pages` concurrency. GitHub Pages is repository deployment infrastructure, not a runtime dependency of the static site or installable skill.

## Failure behavior

- Missing/unknown explicit CSV domain returns an error dictionary; no fallback classifier runs.
- Missing configured CSV returns an error dictionary.
- Invalid icon-candidate family/subject fails boundedly rather than broadening lookup.
- Invalid persistence flag combinations exit before writes.
- Project/page identity collisions, Windows-reserved identities, redirected/shared persistence targets, and competing page claims fail before replaceable inquiry writes; corrupt-manifest recovery is serialized and existing `DECISIONS.md` bytes are preserved and reported.
- Invalid/placeholder/contradictory SVG metadata, digest mismatch, active/unsafe/external/malformed/deep/extreme/invisible/clipped SVG content, redirected asset/manifest paths, output aliases, an inconsistent icon comparison, or an invalid opaque pair exits nonzero with explicit failures.
- Installer lock contention, unsafe source/destination/transient paths, and invalid staged or activated copies fail boundedly; staging failure preserves the existing destination or recognizable interrupted previous tree, activation failure safely restores it, and successful reinstall removes stale files rather than nesting another product directory.
- Missing agent host disables skill activation/research/generation but not local Python commands.
- Missing Chrome/Chromium makes browser smoke fail with an explicit `CHROME_PATH` instruction; committed captures/tests remain available.
- Missing/ignored durable contributor files, tracked private state, or a stale structural atlas fails the repository-context CI job before those defects can become accepted public guidance.
- Missing image generator does not invalidate no-image scenarios or committed benchmark viewing.
- GitHub Pages or Actions unavailability affects only the public Doppler mirror; the checked-in benchmark remains directly runnable as a static site.

Before adding a dependency, intentionally revise the standard-library/no-build contracts, add manifest/lock strategy where relevant, update CI/setup docs, and test copied-skill portability.
