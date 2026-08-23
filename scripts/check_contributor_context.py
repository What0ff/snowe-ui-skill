#!/usr/bin/env python3
"""Validate Snowe's public contributor context and private local-state boundary."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath


REPO_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PUBLIC_PATHS = (
    ".agents/skills/atlas-maintainer/SKILL.md",
    ".github/workflows/ci.yml",
    ".gitignore",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "README.md",
    "docs/atlas/00_README.md",
    "docs/atlas/01_ARCHITECTURE.md",
    "docs/atlas/02_DOMAIN_MODEL.md",
    "docs/atlas/03_CRITICAL_FLOWS.md",
    "docs/atlas/04_STATE_SOURCES_OF_TRUTH.md",
    "docs/atlas/05_EXTERNAL_DEPENDENCIES.md",
    "docs/atlas/06_GOTCHAS.md",
    "docs/atlas/07_TEST_MATRIX.md",
    "docs/atlas/repo-map.md",
    "evals/designer-behavior/HOST-PROBES.md",
    "evals/icon-decisions/README.md",
    "evals/icon-decisions/comparison.html",
    "evals/icon-decisions/manifest.json",
    "scripts/atlas/generate_atlas.py",
    "scripts/check_contributor_context.py",
    "skill/snowe-ui-skill/scripts/icon_review.py",
    "tests/test_icon_workflow.py",
    "tests/test_runtime_hardening.py",
    "tests/test_scope_contract.py",
)

PUBLIC_IGNORE_PROBES = (
    "AGENTS.md",
    "docs/example/AGENTS.md",
    ".agents/skills/atlas-maintainer/SKILL.md",
    "docs/atlas/00_README.md",
    "scripts/atlas/generate_atlas.py",
    ".github/copilot-instructions.md",
    "skill/snowe-ui-skill/agents/openai.yaml",
)

PRIVATE_IGNORE_PROBES = (
    ".agents/personal/SKILL.md",
    ".aider.conf.yml",
    ".claude/settings.local.json",
    ".codex/CURRENT_TASK.md",
    ".continue/config.json",
    ".cursor/rules/local.mdc",
    ".gemini/settings.json",
    ".openai/local.json",
    ".roo/config.json",
    ".windsurf/rules/local.md",
    "CLAUDE.md",
    "CODEX.md",
    "GEMINI.md",
    "CURRENT_TASK.md",
    "agents/local.yaml",
    "generated_context/summary.md",
    "work/notes.md",
    "outputs/result.md",
    "logs/session.txt",
    "generated-context/summary.md",
    "PROJECT-MEMORY.md",
    "HANDOFF.md",
    "session.log",
)

AGENT_REQUIRED_REFERENCES = (
    "docs/atlas/00_README.md",
    "docs/atlas/07_TEST_MATRIX.md",
    ".agents/skills/atlas-maintainer/SKILL.md",
    "scripts/check_contributor_context.py",
    "scripts/atlas/generate_atlas.py",
)

ALLOWED_AGENTS_PREFIX = ".agents/skills/atlas-maintainer/"


def run_git(*arguments: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ("git", "-C", str(REPO_ROOT), *arguments),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def git_paths(*arguments: str) -> set[str]:
    result = run_git(*arguments)
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git {' '.join(arguments)} failed: {detail}")
    return {
        PurePosixPath(raw.decode("utf-8", errors="surrogateescape")).as_posix()
        for raw in result.stdout.split(b"\0")
        if raw
    }


def is_ignored(path: str) -> bool:
    result = run_git("check-ignore", "--no-index", "--quiet", "--", path)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    detail = result.stderr.decode("utf-8", errors="replace").strip()
    raise RuntimeError(f"git check-ignore failed for {path}: {detail}")


def private_tracked_reason(path: str) -> str | None:
    parts = PurePosixPath(path).parts
    if not parts:
        return None
    private_directory_names = {
        ".claude",
        ".codex",
        ".continue",
        ".cursor",
        ".gemini",
        ".openai",
        ".roo",
        ".windsurf",
        "generated-context",
        "generated_context",
        "logs",
        "outputs",
        "work",
    }
    for part in parts:
        if part in private_directory_names:
            return f"private directory {part}"
        if part.startswith(".aider"):
            return "private Aider configuration"
    if PurePosixPath(path).name in {
        "CLAUDE.md",
        "CODEX.md",
        "CURRENT_TASK.md",
        "GEMINI.md",
        "PROJECT-MEMORY.md",
        "HANDOFF.md",
    }:
        return "private task/memory/agent file"
    if parts[0] == ".agents" and not path.startswith(ALLOWED_AGENTS_PREFIX):
        return "non-allowlisted .agents content"
    if "agents" in parts and not path.startswith("skill/snowe-ui-skill/agents/"):
        return "non-product agents directory"
    return None


def paragraph_containing(text: str, marker: str) -> str:
    for paragraph in re.split(r"\n\s*\n", text):
        if marker in paragraph:
            return paragraph
    return ""


def validate(require_tracked: bool) -> list[str]:
    errors: list[str] = []
    tracked = git_paths("ls-files", "-z", "--cached")
    visible = git_paths(
        "ls-files", "-z", "--cached", "--others", "--exclude-standard"
    )

    for path in REQUIRED_PUBLIC_PATHS:
        if not (REPO_ROOT / Path(*PurePosixPath(path).parts)).is_file():
            errors.append(f"required public file is absent: {path}")
        if path not in visible:
            errors.append(f"required public file is not Git-visible: {path}")
        if require_tracked and path not in tracked:
            errors.append(f"required public file is not tracked: {path}")

    for path in PUBLIC_IGNORE_PROBES:
        if is_ignored(path):
            errors.append(f"public repository path is ignored: {path}")

    for path in PRIVATE_IGNORE_PROBES:
        if not is_ignored(path):
            errors.append(f"private local-state probe is not ignored: {path}")

    for path in sorted(tracked):
        reason = private_tracked_reason(path)
        if reason:
            errors.append(f"tracked private path ({reason}): {path}")

    agents = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    for reference in AGENT_REQUIRED_REFERENCES:
        if reference not in agents:
            errors.append(f"AGENTS.md omits required public reference: {reference}")

    checkpoint_paragraph = paragraph_containing(agents, ".codex/CURRENT_TASK.md")
    checkpoint_words = checkpoint_paragraph.casefold()
    if not checkpoint_paragraph:
        errors.append("AGENTS.md does not classify .codex/CURRENT_TASK.md")
    elif "optional" not in checkpoint_words or "absence" not in checkpoint_words:
        errors.append(
            "AGENTS.md must state that .codex/CURRENT_TASK.md is optional and its absence is normal"
        )

    atlas_index = (REPO_ROOT / "docs" / "atlas" / "00_README.md").read_text(
        encoding="utf-8"
    )
    index_checkpoint = paragraph_containing(atlas_index, ".codex/CURRENT_TASK.md")
    index_words = index_checkpoint.casefold()
    if not index_checkpoint or "optional" not in index_words or "absence" not in index_words:
        errors.append(
            "atlas index must classify .codex/CURRENT_TASK.md as optional and absent from fresh clones"
        )

    repo_map = (REPO_ROOT / "docs" / "atlas" / "repo-map.md").read_text(
        encoding="utf-8"
    )
    for private_marker in (
        ".codex/",
        "CURRENT_TASK.md",
        "PROJECT-MEMORY.md",
        "HANDOFF.md",
    ):
        if private_marker in repo_map:
            errors.append(f"generated public repo map exposes local marker: {private_marker}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the public contributor context and private local-state boundary"
    )
    parser.add_argument(
        "--require-tracked",
        action="store_true",
        help="require every durable public context file to be present in the Git index",
    )
    args = parser.parse_args()

    try:
        errors = validate(args.require_tracked)
        tracked = git_paths("ls-files", "-z", "--cached")
    except (OSError, RuntimeError) as error:
        print(f"Contributor context validation could not run: {error}", file=sys.stderr)
        return 2

    if errors:
        print("Contributor context boundary is invalid:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    pending = sum(path not in tracked for path in REQUIRED_PUBLIC_PATHS)
    print(
        "Contributor context boundary is valid: "
        f"{len(REQUIRED_PUBLIC_PATHS)} required public files, "
        f"{len(PRIVATE_IGNORE_PROBES)} private probes ignored, "
        f"{pending} public additions pending tracking."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
