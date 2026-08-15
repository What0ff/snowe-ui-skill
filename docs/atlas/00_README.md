# Repository Atlas

## Purpose

This atlas is the public durable navigation layer for Snowe UI Skill. It lets a human or agent identify the relevant subsystem, load one or two focused documents, and then inspect the corresponding source. It is not a replacement for source code.

## Cold-start path

1. Read root `AGENTS.md`.
2. Use `repo-map.md` to route a task to a path.
3. Read only the focused document named below.
4. Verify behavior-critical details in current source/configuration.
5. After implementation, inspect the complete diff and maintain only invalidated atlas claims.

`.codex/CURRENT_TASK.md` is optional maintainer-local task state. Its absence is normal in a fresh public clone. If it exists during a genuine continuation, it may be read after the public context and checked against source; neither this atlas nor any contributor workflow depends on it.

## Documents

| Document | Read when |
| --- | --- |
| `repo-map.md` | You need structure, entrypoints, task routing, or danger zones. Generated. |
| `01_ARCHITECTURE.md` | You need product boundaries, module responsibilities, lifecycle, or entrypoints. |
| `02_DOMAIN_MODEL.md` | You need runtime vocabulary, data contracts, result shapes, or status models. |
| `03_CRITICAL_FLOWS.md` | You are changing search, synthesis, persistence, or data regeneration. |
| `04_STATE_SOURCES_OF_TRUTH.md` | You are changing CSV evidence, persisted decision packets, benchmark evidence, memory, or ownership. |
| `05_EXTERNAL_DEPENDENCIES.md` | You are changing runtime/toolchain requirements, CI actions, URLs, or integrations. |
| `06_GOTCHAS.md` | You are touching CSV schemas, policy filtering, persistence, imports, or packaging. |
| `07_TEST_MATRIX.md` | You need existing setup, focused/full validation, CI parity, or known gaps. |

## Truth and scope

- Source code and configuration are authoritative when they contradict the atlas.
- The installable product is `skill/snowe-ui-skill/`. Repository context/tooling stays outside that directory.
- `AGENTS.md`, this atlas, `scripts/atlas/`, and the allowlisted atlas-maintainer skill are public contributor infrastructure. Checkpoints, handoffs, logs, generated working context, and personal agent configuration remain private and ignored.
- No database, application service, package manager, or benchmark build runtime exists in this repository. GitHub Pages publishes the checked-in Doppler static files directly as a repository-only public showcase.
- Large CSV catalogs are subordinate evidence sources, not recipe boundaries. Inspect headers, relevant rows, or targeted search results instead of reading them in full.

## Maintenance

Manual documents are selectively maintained through `.agents/skills/atlas-maintainer/SKILL.md`.

The structural map is deterministic:

```powershell
python scripts/atlas/generate_atlas.py --write
python scripts/atlas/generate_atlas.py --check
```

Run `--write` after structural changes. Run `--check` before completion. The generator deliberately owns only `repo-map.md`; it cannot overwrite the focused manual documents.

`python scripts/check_contributor_context.py` verifies that required public context is Git-visible, private state stays ignored, and public guidance treats local checkpoints as optional. CI adds `--require-tracked` to verify the committed public clone.

Every completed implementation task must report either the atlas documents updated and why, or a verified reason no atlas claim changed.
