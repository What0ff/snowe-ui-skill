# Repository Agent Guide

## Scope and authority

- This file applies to the entire repository. A future nested `AGENTS.md` may refine guidance for its subtree; the closest file wins, and durable nested guidance must be version-controlled.
- Base claims and changes on verified repository facts and professional architecture.
- Source code and configuration are authoritative. Tests encode intended contracts; correct documentation when it contradicts implementation.
- `skill/snowe-ui-skill/` is the installable product. Keep repository-only guidance, tests, benchmarks, evaluations, and maintenance tooling outside it.
- Do not change Snowe runtime or methodology during documentation or repository-context maintenance.

## Public context router

A fresh public clone contains the complete durable contributor context:

1. Read this file.
2. Start at `docs/atlas/00_README.md`.
3. Use `docs/atlas/repo-map.md` to route the task, then read only the focused atlas documents relevant to the change.
4. Inspect actual source and configuration wherever implementation details matter.
5. Prefer durable repository context over reconstructing architecture from conversation history.

`.codex/CURRENT_TASK.md` is an optional, ignored local continuity checkpoint. If it exists and the work is a continuation, read it after the public guidance and verify its claims against current source. Its absence is normal in a fresh clone, it is not repository truth, and no public instruction or workflow may require it. Conversation history, raw logs, `work/`, `outputs/`, `PROJECT-MEMORY.md`, `HANDOFF.md`, and personal agent configuration are likewise local state, not contributor architecture.

## Architectural invariants

- The copied product must remain self-contained under `skill/snowe-ui-skill/`; repository infrastructure must never enter an installation.
- Product Python remains standard-library-only and Python 3.11+ unless an intentional dependency change revises the public contracts, CI, and portability evidence.
- Local catalogs are explicitly selected, subordinate evidence. They do not classify a brief or choose layout, style, palette, typography, imagery, or motion.
- Decision packets preserve the brief and unresolved state; they do not infer language, work mode, platform, pressures, or ambiguous domain roles.
- Persistence may regenerate inquiries but must byte-preserve an existing accepted `DECISIONS.md` ledger.
- Benchmarks, screenshots, and deterministic fixtures are regression evidence, not proof that Snowe caused an outcome or that taste is automated.

Read `docs/atlas/01_ARCHITECTURE.md`, `docs/atlas/04_STATE_SOURCES_OF_TRUTH.md`, and `docs/atlas/06_GOTCHAS.md` only when a change touches those boundaries.

## Working method

Before significant implementation:

1. Inspect affected callers, dependencies, execution paths, and existing tests.
2. Establish focused success and failure evidence before editing.
3. Preserve unrelated user changes in a dirty worktree.

Completion requires more than writing code:

1. Run the most relevant focused checks.
2. Run applicable canonical checks from `docs/atlas/07_TEST_MATRIX.md`.
3. Investigate and report every failed or unavailable validation step.
4. Inspect complete `git status`, unstaged diff, and staged diff.
5. Check for accidental TODOs, stubs, incomplete branches, unrelated edits, and product-boundary leakage.

The normal repository baseline is:

```powershell
python -m compileall -q skill/snowe-ui-skill/scripts
python -m unittest discover -s tests -v
python evals/designer-behavior/run_eval.py
```

Repository-context changes additionally require:

```powershell
python scripts/check_contributor_context.py
python scripts/atlas/generate_atlas.py --check
```

Rendered benchmark changes require the Node/Chrome checks routed by the test matrix.

## Atlas maintenance

Keeping `docs/atlas/` synchronized with meaningful code or configuration changes is part of the Definition of Done. Use `.agents/skills/atlas-maintainer/SKILL.md` after implementation and before completion.

1. Inspect the complete final status and diff.
2. Identify only the atlas claims that changed paths could invalidate.
3. Verify those claims against source/configuration and update only affected documents.
4. Run `python scripts/atlas/generate_atlas.py --write` after structural changes.
5. Always run `python scripts/atlas/generate_atlas.py --check` before completion.

Atlas updates are normally required for changes to structure, entrypoints, architecture, lifecycle, public contracts, ownership, sources of truth, critical flows, persistence formats, configuration, integrations, dependencies, build/test strategy, invariants, or documented gotchas. Internal changes that leave every documented claim true need no atlas edit.

Report exactly one outcome:

```text
Atlas updated:
- <documents>
- <reason>
```

```text
Atlas unchanged:
- <verified reason>
```

## Git safety

- Do not commit, push, create a branch, or open a pull request unless the user asks.
- Never use destructive reset or checkout to discard user work without explicit approval.
- Public contribution branches and pull requests follow `CONTRIBUTING.md`; personal maintainer automation belongs in ignored local configuration, not this guide.
