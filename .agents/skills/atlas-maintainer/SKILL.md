---
name: atlas-maintainer
description: Keep this repository's atlas synchronized after meaningful code or configuration changes without broad rescans or documentation churn.
---

# Atlas Maintainer

This is public repository-maintenance infrastructure, not part of the installable
`skill/snowe-ui-skill/` product.

Use after an implementation change and before declaring completion.

1. Read root `AGENTS.md` and the small `docs/atlas/00_README.md` router.
2. Inspect complete `git status`, `git diff`, and `git diff --cached`.
3. Map changed paths to claims in existing atlas documents; do not read the whole atlas by default.
4. Read only potentially affected documents and the changed source/configuration needed to verify them.
5. Treat source/configuration as truth. Update only claims made stale by the final diff.
6. Preserve manually curated context and avoid unrelated rewrites.
7. Run `python scripts/atlas/generate_atlas.py --write` only for structural changes, then require `python scripts/atlas/generate_atlas.py --check` to pass.
8. Never regenerate the entire atlas after a small change and never claim synchronization without inspecting the actual final diff.

Report exactly one outcome:

```text
Atlas updated:
- <document(s)>
- <reason each changed>
```

```text
Atlas unchanged:
- <verified reason all existing claims remain true>
```
