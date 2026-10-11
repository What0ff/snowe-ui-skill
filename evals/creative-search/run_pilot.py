#!/usr/bin/env python3
"""Opt-in real Codex runs. Never scores taste or runs a model during unit tests."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
BRIEFS = Path(__file__).with_name("briefs.json")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root: Path) -> list[dict]:
    result = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("Redirected evidence is unsupported")
        if path.is_file() and "__pycache__" not in path.parts:
            result.append({"path": path.relative_to(root).as_posix(), "sha256": digest(path)})
    return result


def write(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def fresh(path: Path) -> Path:
    path = path.resolve()
    path.mkdir(parents=True, exist_ok=False)
    return path


def snapshot(destination: Path) -> None:
    if destination.resolve().is_relative_to((ROOT / "skill/snowe-ui-skill").resolve()):
        raise ValueError("Snapshot destination must stay outside the installed product")
    destination = fresh(destination)
    shutil.copytree(ROOT / "skill/snowe-ui-skill", destination / "snowe",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copy2(BRIEFS, destination / "briefs.json")
    write(destination / "snapshot.json", {
        "schema": "1.0", "files": inventory(destination / "snowe"),
        "briefs_sha256": digest(destination / "briefs.json"),
    })


def validate_snapshot(root: Path) -> dict:
    record = json.loads((root / "snapshot.json").read_text(encoding="utf-8"))
    if inventory(root / "snowe") != record["files"]:
        raise ValueError("Skill snapshot changed")
    if digest(root / "briefs.json") != record["briefs_sha256"]:
        raise ValueError("Frozen briefs changed")
    return record


def prompt_for(case: dict) -> str:
    return f"""Use the explicitly selected local Snowe skill: read snowe/SKILL.md and only its relevant references. Use that copy rather than any installed version. Work only in this workspace; do not inspect other projects, benchmarks, evaluations or previous runs. Do not delegate or spawn agents.

{case['brief']}

Implement the finished page under site/index.html, with main, a meaningful h1 and native labelled buttons. You may use additional local files under site/. All visible interface text is English. Assets must be self-contained or local; do not fetch external assets, install packages, or use external services. Do not expose internal design/evaluation notes in the page.

Use your selected skill's proportional process and retain your concise working decisions under notes/. Do not ask the user to select reversible design details. Inspect rendered output using the local optional snowe/scripts/observe.mjs when available; record precisely what you actually inspected and any unavailable proof. Create the real artifact, not just a plan. Finish with paths, the selected design and material evidence limitations.
"""


def usage(events: Path) -> dict:
    totals = {}
    for line in events.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "turn.completed":
            for name, value in event.get("usage", {}).items():
                if isinstance(value, int):
                    totals[name] = totals.get(name, 0) + value
    return totals


def generate(snapshot_root: Path, case_id: str, repeat: int, destination: Path,
             timeout: int = 1200) -> None:
    snapshot_root = snapshot_root.resolve()
    frozen = validate_snapshot(snapshot_root)
    cases = json.loads((snapshot_root / "briefs.json").read_text(encoding="utf-8"))["cases"]
    case = next((item for item in cases if item["id"] == case_id), None)
    if case is None or repeat < 1:
        raise ValueError("Select an existing case and positive repetition")
    command = shutil.which("codex.cmd" if os.name == "nt" else "codex")
    if not command:
        raise ValueError("Codex CLI unavailable; no model evidence was collected")
    destination = fresh(destination)
    prompt = prompt_for(case)
    (destination / "prompt.txt").write_text(prompt, encoding="utf-8")
    # Each subject receives a neutral workspace with no condition label or ancestor repo.
    with tempfile.TemporaryDirectory(prefix="snowe-subject-") as directory:
        workspace = Path(directory).resolve()
        if workspace.parent != Path(tempfile.gettempdir()).resolve():
            raise ValueError("Unexpected temporary workspace parent")
        shutil.copytree(snapshot_root / "snowe", workspace / "snowe")
        (workspace / "site").mkdir()
        (workspace / "notes").mkdir()
        (workspace / "AGENTS.md").write_text(
            "The user explicitly selected snowe/SKILL.md for this task. Use only that local skill copy. "
            "Keep all writes inside this workspace. Do not read another run or delegate work.\n",
            encoding="utf-8")
        arguments = [command, "exec", "--ephemeral", "--skip-git-repo-check", "--json",
                     "--color", "never", "--cd", str(workspace),
                     "--output-last-message", str(workspace / "FINAL.md"), "-"]
        started = time.monotonic()
        timed_out = False
        with (destination / "events.jsonl").open("wb") as out, (destination / "stderr.txt").open("wb") as err:
            try:
                result = subprocess.run(arguments, input=prompt.encode("utf-8"), stdout=out,
                                        stderr=err, timeout=timeout, check=False)
                exit_code = result.returncode
            except subprocess.TimeoutExpired:
                exit_code, timed_out = None, True
        elapsed = time.monotonic() - started
        for name in ("site", "notes"):
            shutil.copytree(workspace / name, destination / name)
        if (workspace / "FINAL.md").is_file():
            shutil.copy2(workspace / "FINAL.md", destination / "FINAL.md")
        changed_skill = inventory(workspace / "snowe") != frozen["files"]
    record = {
        "schema": "1.0", "case": case_id, "repeat": repeat,
        "snapshot": str(snapshot_root), "snapshot_sha256": digest(snapshot_root / "snapshot.json"),
        "briefs_sha256": frozen["briefs_sha256"], "prompt_sha256": digest(destination / "prompt.txt"),
        "exit_code": exit_code, "timed_out": timed_out, "elapsed_seconds": round(elapsed, 3),
        "usage": usage(destination / "events.jsonl"), "skill_modified_by_subject": changed_skill,
        "site_files": inventory(destination / "site"),
        "evidence_boundary": "Observed CLI generation; no automatic visual verdict or user acceptance. Model configuration is inherited, not independently attested.",
    }
    record["status"] = "GENERATED" if exit_code == 0 and not changed_skill and (destination / "site/index.html").is_file() else "INCOMPLETE"
    write(destination / "run.json", record)
    print(json.dumps({k: record[k] for k in ("case", "repeat", "status", "elapsed_seconds", "usage")}))
    if record["status"] != "GENERATED":
        raise ValueError("Generation incomplete; preserve and inspect raw evidence")


def validate_run(root: Path) -> dict:
    record = json.loads((root / "run.json").read_text(encoding="utf-8"))
    if record["status"] != "GENERATED":
        raise ValueError("Incomplete generation")
    source = Path(record["snapshot"])
    validate_snapshot(source)
    if digest(source / "snapshot.json") != record["snapshot_sha256"]:
        raise ValueError("Snapshot record changed")
    if inventory(root / "site") != record["site_files"]:
        raise ValueError("Generated artifact changed; do not silently repair a subject")
    if digest(root / "prompt.txt") != record["prompt_sha256"]:
        raise ValueError("Subject prompt changed")
    return record


def capture(root: Path) -> None:
    root = root.resolve()
    record = validate_run(root)
    frozen = Path(record["snapshot"])
    cases = json.loads((frozen / "briefs.json").read_text(encoding="utf-8"))["cases"]
    case = next(item for item in cases if item["id"] == record["case"])
    plan = {"schema": "1.0", "scope": case["id"], "sourceRoots": ["site"], "cases": []}
    for width in (1440, 820, 390):
        plan["cases"].append({
            "id": f"default-{width}", "state": "default", "viewport": f"{width}x1000@1",
            "theme": "light", "input": "pointer", "motion": "reduced", "context": "page",
            "route": "/site/index.html", "steps": [],
            "expect": [{"selector": "body", "property": "text", "includes": case["name"]}],
            "probes": [{"selector": "main", "pseudo": ""}, {"selector": "h1", "pseudo": ""}, {"selector": "button", "pseudo": ""}],
            "details": [{"id": "heading", "selector": "h1", "padding": 0, "scale": 1}],
        })
    write(root / "plan.json", plan)
    observer = frozen / "snowe/scripts/observe.mjs"
    result = subprocess.run(["node", str(observer), "capture", str(root), "plan.json", "captures"],
                            capture_output=True, text=True, encoding="utf-8", timeout=120, check=False)
    (root / "capture-log.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        raise ValueError("Capture unavailable; inspect capture-log.txt")
    print(result.stdout.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    freeze = sub.add_parser("snapshot"); freeze.add_argument("destination", type=Path)
    run = sub.add_parser("generate")
    run.add_argument("snapshot", type=Path); run.add_argument("case")
    run.add_argument("repeat", type=int); run.add_argument("destination", type=Path)
    run.add_argument("--timeout", type=int, default=1200)
    render = sub.add_parser("capture"); render.add_argument("run", type=Path)
    check = sub.add_parser("check"); check.add_argument("run", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "snapshot": snapshot(args.destination)
        elif args.command == "generate": generate(args.snapshot, args.case, args.repeat, args.destination, args.timeout)
        elif args.command == "capture": capture(args.run)
        else: print(json.dumps(validate_run(args.run), indent=2))
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        parser.exit(1, str(error) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
