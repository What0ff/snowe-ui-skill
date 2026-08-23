#!/usr/bin/env python3
"""Generate the deterministic structural portion of the public repository atlas.

This repository-specific generator owns only docs/atlas/repo-map.md. Focused
manual atlas documents remain curated, so a structural refresh cannot erase
useful context. The map is built from tracked files plus nonignored candidate
additions: ignored maintainer-local state can neither change nor leak into it.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from collections import Counter
from pathlib import Path, PurePosixPath


REPO_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_NAME = "snowe-ui-skill"
OUTPUT = REPO_ROOT / "docs" / "atlas" / "repo-map.md"
OUTPUT_RELATIVE = "docs/atlas/repo-map.md"
MAX_TREE_DEPTH = 4

DIRECTORY_NOTES = {
    ".agents": "public repository-local agent workflows",
    ".github": "continuous integration",
    "benchmarks": "rendered forward-tests",
    "docs": "public repository documentation and atlas",
    "evals": "deterministic behavior contracts and bounded operational proofs",
    "scripts": "repository maintenance tooling",
    "skill": "installable product boundary",
    "skill/snowe-ui-skill/data": "bundled retrieval evidence and analog catalogs",
    "skill/snowe-ui-skill/references": "progressive-disclosure UI guidance",
    "skill/snowe-ui-skill/scripts": "standard-library retrieval, decision support, SVG validation, and icon comparison",
    "tests": "unittest product and benchmark regression coverage",
}

ENTRYPOINTS = (
    ("skill/snowe-ui-skill/SKILL.md", "Agent-runtime activation metadata and workflow router"),
    ("skill/snowe-ui-skill/scripts/search.py", "Local evidence-search and decision-packet CLI"),
    ("skill/snowe-ui-skill/scripts/decision_packet.py", "Portfolio/open-inquiry generation and identity-bound persistence API"),
    ("skill/snowe-ui-skill/scripts/asset_quality.py", "Strict self-contained SVG structure/provenance validator"),
    ("skill/snowe-ui-skill/scripts/icon_review.py", "Deterministic icon decision/context comparison builder"),
    ("skill/snowe-ui-skill/scripts/contrast.py", "Exact opaque-color contrast checker"),
    ("evals/designer-behavior/run_eval.py", "Cross-business deterministic-contract regression"),
    ("benchmarks/bicycle-commerce/index.html", "Rendered bicycle-commerce forward-test"),
    ("scripts/install_skill.py", "Exact standalone skill install/update helper"),
    ("scripts/browser-smoke.mjs", "Cross-platform Chrome/CDP rendered regression"),
    ("scripts/check_contributor_context.py", "Public/private contributor-context boundary check"),
    ("tests/test_snowe_ui_skill.py", "Skill/runtime unittest regression suite"),
    ("tests/test_bicycle_benchmark.py", "Benchmark artifact and UX-contract suite"),
    ("tests/test_installation.py", "Standalone install/update and recovery regression suite"),
    ("tests/test_scope_contract.py", "Process-depth proportionality and escalation regression suite"),
    ("tests/test_icon_workflow.py", "Icon lifecycle, context proof, and SVG safety regression suite"),
    ("tests/test_runtime_hardening.py", "Persistence identity/race and runtime failure regression suite"),
    (".github/workflows/ci.yml", "Cross-platform runtime, browser, and context validation workflow"),
    ("scripts/atlas/generate_atlas.py", "Structural atlas write/check command"),
)

ROUTER = (
    ("Understand contributor workflow or context boundaries", "AGENTS.md"),
    ("Understand agent activation, process depth, and UI workflow", "skill/snowe-ui-skill/SKILL.md"),
    ("Change detailed design guidance (follow routing links in SKILL.md)", "skill/snowe-ui-skill/references/"),
    ("Change CLI options or output dispatch", "skill/snowe-ui-skill/scripts/search.py"),
    ("Change domains, stacks, BM25 retrieval, or result filtering", "skill/snowe-ui-skill/scripts/core.py"),
    ("Change open inquiry generation, analog filtering, or identity-bound decision persistence", "skill/snowe-ui-skill/scripts/decision_packet.py"),
    ("Change custom SVG validation", "skill/snowe-ui-skill/scripts/asset_quality.py"),
    ("Change icon need, custom/existing/no-icon comparison, or context proof", "skill/snowe-ui-skill/scripts/icon_review.py"),
    ("Change exact color/contrast validation", "skill/snowe-ui-skill/scripts/contrast.py"),
    ("Change a runtime dataset or schema (verify configured headers)", "skill/snowe-ui-skill/scripts/core.py"),
    ("Change process-depth contracts or inspect bounded observed-host probes", "evals/designer-behavior/"),
    ("Change the operational icon decision proof", "evals/icon-decisions/"),
    ("Change or inspect the rendered bicycle benchmark", "benchmarks/bicycle-commerce/"),
    ("Change standalone installation or update behavior", "scripts/install_skill.py"),
    ("Add or focus regression coverage", "tests/"),
    ("Change CI validation", ".github/workflows/ci.yml"),
    ("Navigate architecture, flows, state, or validation", "docs/atlas/00_README.md"),
    ("Maintain public repository context", ".agents/skills/atlas-maintainer/SKILL.md"),
)

DANGER_ZONES = (
    ("skill/snowe-ui-skill/", "This is the copied installable unit; repository-only files must stay outside it."),
    ("skill/snowe-ui-skill/scripts/core.py", "CSV headers, evidence-role labels, stack URL coverage, and icon-source boundaries are public contracts."),
    ("skill/snowe-ui-skill/scripts/decision_packet.py", "Identity manifests, atomic inquiry writes, race handling, containment, and byte-preserved DECISIONS.md form one persistence contract."),
    ("skill/snowe-ui-skill/scripts/asset_quality.py", "A structural PASS requires a strict self-contained SVG/metadata subset but can never certify visual or provenance truth."),
    ("skill/snowe-ui-skill/scripts/icon_review.py", "Comparison sheets bind exact assets, metadata, source/license text, UI-context selectors, decisions, and rejected alternatives."),
    ("skill/snowe-ui-skill/data/*.csv", "Schemas are accessed by exact header strings; malformed quoting or renamed columns can silently empty fields."),
    ("benchmarks/bicycle-commerce/assets/", "Generated media, local fonts/licenses, SVGs, and provenance metadata must stay coherent with the benchmark disclosure."),
    ("scripts/install_skill.py", "Successful updates exactly replace the final skill directory; staging, containment, recovery, and rollback must remain intact."),
    (".gitignore", "Public contributor context is allowlisted while task/session state remains private; validate both sides after edits."),
)


def relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def git_visible_files() -> set[str]:
    """Return files that belong to the public working-tree candidate.

    Tracked paths are public even if an ignore rule later changes. Nonignored
    untracked paths are included so structural additions can be mapped before
    staging. Deleted tracked paths are omitted because they are absent on disk.
    """

    result = subprocess.run(
        (
            "git",
            "-C",
            str(REPO_ROOT),
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
        ),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Git-visible file discovery failed: {detail}")

    files: set[str] = set()
    for raw_path in result.stdout.split(b"\0"):
        if not raw_path:
            continue
        posix_path = PurePosixPath(raw_path.decode("utf-8", errors="surrogateescape"))
        local_path = REPO_ROOT.joinpath(*posix_path.parts)
        if local_path.is_file():
            files.add(posix_path.as_posix())
    return files


def repository_directories(files: set[str]) -> set[str]:
    directories: set[str] = set()
    for filename in files:
        parent = PurePosixPath(filename).parent
        while parent != PurePosixPath("."):
            directories.add(parent.as_posix())
            parent = parent.parent
    return directories


def directory_tree(
    directories: set[str],
    parent: str = "",
    prefix: str = "",
    depth: int = 0,
) -> list[str]:
    if depth >= MAX_TREE_DEPTH:
        return []

    parent_path = PurePosixPath(parent) if parent else PurePosixPath(".")
    children = sorted(
        (
            path
            for path in directories
            if PurePosixPath(path).parent == parent_path
        ),
        key=lambda path: PurePosixPath(path).name.casefold(),
    )
    lines: list[str] = []
    for index, path in enumerate(children):
        last = index == len(children) - 1
        connector = "└── " if last else "├── "
        name = PurePosixPath(path).name
        note = DIRECTORY_NOTES.get(path) or DIRECTORY_NOTES.get(name)
        suffix = f"  # {note}" if note else ""
        lines.append(f"{prefix}{connector}{name}/{suffix}")
        child_prefix = prefix + ("    " if last else "│   ")
        lines.extend(directory_tree(directories, path, child_prefix, depth + 1))
    return lines


def file_statistics(files: set[str]) -> list[tuple[str, int]]:
    counts: Counter[str] = Counter()
    for filename in files:
        if filename == OUTPUT_RELATIVE:
            continue
        suffix = PurePosixPath(filename).suffix.casefold() or "[no extension]"
        counts[suffix] += 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def markdown_table(
    headers: tuple[str, ...],
    rows: tuple[tuple[str, ...], ...] | list[tuple[str, ...]],
) -> str:
    def cell(value: str) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")

    output = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    output.extend("| " + " | ".join(cell(value) for value in row) + " |" for row in rows)
    return "\n".join(output)


def render() -> str:
    files = git_visible_files()
    directories = repository_directories(files)
    root_files = sorted(path for path in files if "/" not in path)
    present_entrypoints = tuple(
        (f"`{path}`", role) for path, role in ENTRYPOINTS if path in files
    )
    statistics = [(f"`{suffix}`", str(count)) for suffix, count in file_statistics(files)]
    router = tuple((task, f"`{path}`") for task, path in ROUTER)
    danger = tuple((f"`{path}`", reason) for path, reason in DANGER_ZONES)
    tree = "\n".join(directory_tree(directories))
    root_file_lines = "\n".join(f"- `{name}`" for name in root_files)

    return f"""<!-- AUTO-GENERATED by scripts/atlas/generate_atlas.py; edit the generator, not this file. -->
# Repository Map

This deterministic structural map is generated from the Git-visible public working tree: tracked files plus nonignored candidate additions. Ignored local context, caches, and build output cannot affect it. Read `00_README.md` first and load only the domain document relevant to the task.

## Directory tree

```text
{REPOSITORY_NAME}/
{tree}
```

## Root files

{root_file_lines}

## Entrypoints

{markdown_table(("Path", "Role"), present_entrypoints)}

## File statistics

The generated map itself is excluded from the counts.

{markdown_table(("Extension", "Files"), statistics)}

## Where to look

{markdown_table(("Task", "Start here"), router)}

## Danger zones

{markdown_table(("Path/area", "Why it is fragile"), danger)}
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or check docs/atlas/repo-map.md")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="write the generated map")
    mode.add_argument("--check", action="store_true", help="fail if the generated map is stale")
    args = parser.parse_args()

    try:
        content = render()
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 2

    if args.check:
        if not OUTPUT.exists():
            print(f"Missing: {relative(OUTPUT)}")
            return 1
        if OUTPUT.read_text(encoding="utf-8") != content:
            print(f"Stale: {relative(OUTPUT)}")
            print("Run: python scripts/atlas/generate_atlas.py --write")
            return 1
        print("Atlas structural map is up to date.")
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    print(f"Wrote {relative(OUTPUT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
