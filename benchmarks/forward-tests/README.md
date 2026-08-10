# Snowe rendered forward-tests

These prototypes provide rendered evidence about whether the architecture-first Decision Graph generalizes beyond Goodturn. They are fictional, dependency-free HTML/CSS/JavaScript experiences with real content shapes, interactions, responsive transformations, decisions, QA, and browser captures. They cover three materially different tested classes; they do not certify universal performance or aesthetic quality.

| Experience | Organizing logic | Deliberate absence |
|---|---|---|
| Larkhaven permit service | One resident request from eligibility through status and assisted recovery | No generated imagery, no custom asset, no choreographed motion |
| Relay North warehouse | Repeated detect → inspect → act loop around live objects and exceptions | No imagery, no custom asset, state feedback only |
| The Morrow Review | Issue relationships and sustained reading before archive/membership | No generated imagery or custom asset; reading progress only |

Serve the repository root so all paths match browser smoke and screenshots:

```text
python -m http.server 4173
```

The executable browser smoke is `node scripts/browser-smoke.mjs`; CI runs it against system Chrome with no package install or browser download. See `CROSS-BENCHMARK.md` for the causal comparison with Goodturn.
