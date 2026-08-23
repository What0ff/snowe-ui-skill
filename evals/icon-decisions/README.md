# Icon Decision Forward Proof

This compact evaluation exercises the complete icon-decision path without claiming that automation certifies taste. It compares exact existing, custom, and no-icon alternatives inside representative controls, then keeps the selected outcome and rejected alternatives explicit.

## Reproduce

From the repository root:

```text
python skill/snowe-ui-skill/scripts/icon_review.py \
  evals/icon-decisions/manifest.json \
  --output evals/icon-decisions/comparison.html --json
python -m unittest tests.test_icon_workflow -v
node scripts/browser-smoke.mjs --smoke
```

The generated HTML must byte-match the checked artifact in the current worktree. Browser smoke renders it at the manifest's exact wide/mobile viewports, verifies all declared SVG target dimensions, accessible no-icon controls, declared comparison states, self-containment, and horizontal containment. Every repository-derived context binds an exact source-byte digest, a non-redirecting local route, selector, and expected host label. Its explicit state map covers every comparison state and maps high-contrast to browser forced-colors. The selected `dialog-close` Lucide X is exercised in the actual Goodturn `.sheet-close-icon` owner; other candidates are rendered in that owning shell as challengers. Each rendered asset candidate is fetched from its manifest path, checked against the manifest `asset_sha256` and metadata provenance digest/identity, and decoded into a cleared canvas to require nontransparent paint; this proves technical asset binding/content, not recognition or optical quality. Smoke then opens the Goodturn dialog and renders the selected and rejected candidates in its owning shell, renders the selected fit and both alternatives in the real service card, and renders the selected no-icon action plus its badge-check alternative in Larkhaven's real eligibility control. It binds the selected no-icon label to the real owning button text and checks that actual and cloned disabled controls have an observable computed-style treatment. It exercises each manifest-declared host state and the exact mobile/desktop sizes. The normal Goodturn smoke separately checks the external exchange glyph in its implemented host component.

## Materially different outcomes

- `dialog-close`: **KEEP existing.** Pinned Lucide X wins; the repository-owned orbit challenger is rejected because its extra ring crowds the 16 px silhouette and suggests a status badge. Visible Close text remains a viable but less compact alternative in the Goodturn product-dialog shell.
- `bicycle-fit`: **KEEP custom.** The repository-owned fit glyph carries the specific bicycle-measurement mechanism more clearly than a generic ruler or label-only presentation in Goodturn's service family.
- `eligibility-action`: **KEEP no icon.** Visible “Check and continue” text is complete. A badge-check glyph is rejected because it implies a verified result before eligibility has been checked.

These decisions are not an instruction to prefer custom work. They prove that the workflow can keep external work, keep custom work, or refuse an icon.

## Evidence boundaries

- **Deterministic contracts:** `asset_quality.py` checks the self-contained SVG/metadata subset, canonical HTTPS external provenance, structured local source/license files with exact digests, bounded JSON/scalar inputs, and exact SVG bytes; `icon_review.py` binds candidate name, manifest asset SHA-256, metadata provenance digest/identity, sizes, context source digest, safe local route/selector host proof, canonical comparison→host state bindings, verdict, selection, and complete challenger coverage. Unit tests protect malformed/deep/extreme-number inputs, Unicode surrogates, uninspectable/reparse paths, output aliases, state swaps, label/digest mutations, evidence-byte mutations, failure cases, and deterministic regeneration.
- **Current source evidence:** Lucide SVG bytes and the included local license records are pinned to upstream revision `33a44aa8b0b43d9b0ed14eb08860a1b5550a1573`. The metadata records exact official source URLs and SHA-256 digests; external URL truth remains explicitly unverified until current primary-source review.
- **Rendered/browser regression evidence:** `comparison.html` demonstrates technical rendering in declared representative contexts. Browser smoke proves dimensions, declared comparison states, containment, self-containment, exact source-byte/route/selector/label binding, candidate asset/metadata digest binding, nontransparent decoded paint, observable disabled treatment, and host rendering of every selected/challenger candidate at the manifest's exact wide/mobile viewports and host states.
- **Human visual judgment:** recognition, metaphor, silhouette, optical balance, family fit, and every KEEP/REJECT rationale in `manifest.json`. Neither the validator nor browser smoke certifies these judgments.

The comparison sheet intentionally uses a small supported set of component shells. Host challenger rendering proves technical placement, asset loading, state reachability, and containment; it does not decide recognition, metaphor, optical balance, or the winner. The deterministic sheet exercises a selected state, but none of the repository's current owning components has a real selected-state icon scenario, so selected-state host evidence remains unavailable rather than inferred. It is not a usability study, recognition study, or general proof that an icon family is coherent. A production decision still requires human inspection inside the actual owning component and current source/license verification.
