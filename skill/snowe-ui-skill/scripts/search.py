#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Snowe UI Skill Search - local evidence retrieval and design decision packets
Usage: python search.py "<query>" --domain <domain> [--max-results 3]
       python search.py "<brief>" --decision-packet [-p "Project Name"]
       python search.py "<brief>" --decision-packet --analog-query "<explicit lexical query>"
       python search.py "<brief>" --decision-packet --declared-context context.json
       python search.py "<brief>" --decision-packet --persist -p "Project Name" [--page "catalog"]

Domains: chart, product, ux, icons, icon-families, icon-concepts, icon-candidates, react, web, google-fonts
Stacks: react, nextjs, vue, svelte, astro, swiftui, react-native, flutter, nuxtjs, nuxt-ui, html-tailwind, shadcn, jetpack-compose, threejs, angular, laravel, javafx, wpf, winui, avalonia, uno, uwp

Decision packets are explicit Portfolio/open-inquiry workbenches; bounded
Direct corrections and ordinary Focused work skip them. They preserve the
brief without semantic classification and keep
architecture, art direction, imagery, custom graphics, motion, and responsive
behavior open until an agent resolves pressures and compares real candidates.
The historical --design-system spelling remains an alias, but no recipe-based
design system is selected.

Persistence:
  --persist    With an explicit project identity, save PROJECT.json and
               BRIEF.md, then initialize a non-overwritten DECISIONS.md
  --page       Also create a page inquiry without prescribing a page type or section order
"""

import argparse
import sys
import io
import os

# Isolated interpreters (python -I, PYTHONSAFEPATH) drop the script directory
# from sys.path; the sibling modules below belong to this skill.
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import json

from checked_evidence import read_selected_json
from core import CSV_CONFIG, AVAILABLE_STACKS, MAX_RESULTS, search, search_stack
from decision_packet import generate_decision_packet_with_persistence


def _force_utf8_console():
    """Force UTF-8 for stdout/stderr to handle emojis on Windows (cp1252 default)."""
    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def format_output(result):
    """Format results for agent consumption (token-optimized)."""
    if "error" in result:
        return f"Error: {result['error']}"

    output = []
    if result.get("stack"):
        output.append(f"## Snowe UI Skill Stack Guidelines")
        output.append(f"**Stack:** {result['stack']} | **Query:** {result['query']}")
    else:
        output.append(f"## Snowe UI Skill Search Results")
        output.append(f"**Domain:** {result['domain']} | **Query:** {result['query']}")
    output.append(f"**Source:** {result['file']} | **Found:** {result['count']} results\n")
    if result.get("source_role"):
        output.append(f"**Source role:** {result['source_role']}")
    if result.get("warning"):
        output.append(f"**Use boundary:** {result['warning']}\n")

    for i, row in enumerate(result['results'], 1):
        output.append(f"### Result {i}")
        for key, value in row.items():
            value_str = str(value)
            if len(value_str) > 300:
                value_str = value_str[:300] + "..."
            output.append(f"- **{key}:** {value_str}")
        output.append("")

    return "\n".join(output)


def positive_int(value):
    """argparse converter matching the public retrieval API contract."""
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise argparse.ArgumentTypeError("must be a positive integer") from None
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


# Human labels for files reported by persist_decision_packet.
_PERSISTED_ROLES = (
    ("PROJECT.json", "stable identity manifest"),
    ("BRIEF.md", "project brief"),
    ("DECISIONS.md", "accepted decisions ledger; never regenerated"),
)


def _persisted_role(path):
    name = os.path.basename(path)
    for filename, role in _PERSISTED_ROLES:
        if name == filename:
            return role
    if os.path.basename(os.path.dirname(path)) == "pages" and name.endswith(".md"):
        return "open page inquiry"
    if name.startswith("PROJECT.json.corrupt-"):
        return "quarantined incomplete identity manifest"
    if name.startswith(".PROJECT.json.tmp-"):
        return "unpublished manifest from an interrupted run"
    return "persisted state"


def print_persistence_summary(persisted, stream):
    """Report the files persist_decision_packet actually wrote or preserved."""
    project_dir = persisted["design_intelligence_dir"]
    rows = [("written", path) for path in persisted["created_or_updated_files"]]
    rows += [("preserved", path) for path in persisted["preserved_files"]]
    print("\n" + "=" * 60, file=stream)
    print(f"Design intelligence persisted to {project_dir}", file=stream)
    for status, path in rows:
        shown = os.path.relpath(path, project_dir)
        if shown.startswith(".."):
            shown = path
        print(f"   {status:<10} {shown} ({_persisted_role(path)})", file=stream)
    print("", file=stream)
    print("Usage: Read accepted decisions, then the brief and any relevant page inquiry.", file=stream)
    print("=" * 60, file=stream)
    markers = persisted.get("sensitive_content") or []
    if markers:
        print(
            "WARNING: the brief is stored verbatim and appears to contain: "
            + ", ".join(markers)
            + f". Remove those values from {project_dir}, or keep that directory out of version control.",
            file=sys.stderr,
        )


def load_declared_context(path):
    """Read caller declarations; the runtime never derives them from the brief.

    Known fields are type-checked so a malformed file fails instead of being
    coerced. Other keys pass through to situation.other_declared_context.
    """
    value = read_selected_json(path)
    if not isinstance(value, dict):
        raise ValueError(f"must be a JSON object, not {type(value).__name__}")
    work_mode = value.get("work_mode")
    if "work_mode" in value and (not isinstance(work_mode, str) or not work_mode.strip()):
        raise ValueError("work_mode must be nonempty text")
    for field in ("platforms", "facts", "pressures"):
        items = value.get(field)
        if field in value and (
            not isinstance(items, list) or any(not isinstance(item, str) or not item.strip() for item in items)
        ):
            raise ValueError(f"{field} must be an array of nonempty strings")
    return value


def build_parser():
    parser = argparse.ArgumentParser(prog="search.py", description="Snowe UI Skill Search")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--domain", "-d", choices=list(CSV_CONFIG.keys()), help="Search domain")
    parser.add_argument("--stack", "-s", choices=AVAILABLE_STACKS, help=f"Stack-specific search. Available: {', '.join(AVAILABLE_STACKS)}")
    parser.add_argument("--max-results", "-n", type=positive_int, default=None, help="Max results (positive integer; default: 3; search modes only)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    # Explicit open-inquiry packet. --design-system remains a compatibility
    # alias but no longer chooses a recipe-based design system.
    parser.add_argument(
        "--decision-packet",
        "--design-system",
        "-dp",
        "-ds",
        dest="decision_packet",
        action="store_true",
        help="Open a Portfolio/open-inquiry workbench (skip bounded Direct and ordinary Focused work); does not select a design recipe",
    )
    parser.add_argument("--project-name", "-p", type=str, default=None, help="Project name; required as the stable identity when --persist is used")
    parser.add_argument("--format", "-f", choices=["markdown", "json"], default=None, help="Decision-packet output format (default: markdown)")
    parser.add_argument(
        "--analog-query",
        type=str,
        default=None,
        help="Optional caller-chosen lexical query for subordinate product analogs; the brief is never expanded or classified automatically",
    )
    parser.add_argument(
        "--declared-context",
        metavar="FILE.json",
        default=None,
        help="UTF-8 JSON object of caller-declared work_mode, platforms, facts, pressures and other context for the packet; never inferred from the brief",
    )
    # Persistence (Brief + durable decisions + page inquiries)
    parser.add_argument("--persist", action="store_true", help="Create identity-bound PROJECT.json/BRIEF.md and initialize a durable non-overwritten DECISIONS.md")
    parser.add_argument("--page", type=str, default=None, help="Create a page inquiry without prescribing a page type or section order")
    parser.add_argument("--output-dir", "-o", type=str, default=None, help="Output directory for persisted files (default: current directory)")
    return parser


def main(argv=None):
    """Run the CLI and return its exit status; argparse usage errors exit 2 directly."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.domain and args.stack:
        parser.error("--domain and --stack are mutually exclusive")
    if args.decision_packet and (args.domain or args.stack):
        parser.error("--decision-packet cannot be combined with --domain or --stack")
    if args.analog_query and not args.decision_packet:
        parser.error("--analog-query requires --decision-packet")
    if args.declared_context and not args.decision_packet:
        parser.error("--declared-context requires --decision-packet")
    if args.page and not args.persist:
        parser.error("--page requires --persist")
    if args.output_dir and not args.persist:
        parser.error("--output-dir requires --persist")
    packet_only_values = (args.persist, args.page, args.output_dir)
    if not args.decision_packet and any(value is not None and value is not False for value in packet_only_values):
        parser.error("--persist, --page, and --output-dir require --decision-packet")
    if args.decision_packet and args.json:
        parser.error("--json is available for domain and stack searches; use --format json for decision packets")
    if args.decision_packet and args.max_results is not None:
        parser.error("--max-results is available only for domain and stack searches")
    if not args.decision_packet and args.project_name is not None:
        parser.error("--project-name requires --decision-packet")
    if not args.decision_packet and args.format is not None:
        parser.error("--format requires --decision-packet; use --json for domain or stack search")

    # Decision packet takes priority
    if args.decision_packet:
        packet_format = args.format or "markdown"
        declared_context = None
        if args.declared_context:
            try:
                declared_context = load_declared_context(args.declared_context)
            except (OSError, ValueError) as error:
                parser.error(f"--declared-context {args.declared_context}: {error}")
        try:
            result, persisted = generate_decision_packet_with_persistence(
                args.query,
                args.project_name,
                packet_format,
                persist=args.persist,
                page=args.page,
                output_dir=args.output_dir,
                page_brief=args.query if args.page else None,
                declared_context=declared_context,
                analog_query=args.analog_query,
            )
        except (OSError, ValueError) as error:
            parser.error(str(error))
        except RuntimeError as error:
            # Lock contention is not a usage error: report it once, without a traceback.
            parser.exit(1, f"{parser.prog}: error: {error}\n")
        print(result)

        if persisted is not None:
            # Keep documented JSON stdout machine-readable. Human persistence
            # diagnostics belong on stderr in structured mode.
            print_persistence_summary(persisted, sys.stderr if packet_format == "json" else sys.stdout)
        return 0

    if args.stack:
        result = search_stack(args.query, args.stack, args.max_results or MAX_RESULTS)
    else:
        if not args.domain:
            parser.error("--domain is required for local evidence search; automatic semantic domain detection is intentionally unavailable")
        result = search(args.query, args.domain, args.max_results or MAX_RESULTS)
    if args.json:
        # JSON stays on stdout, error object included, so tooling can parse it.
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif "error" in result:
        print(format_output(result), file=sys.stderr)
    else:
        print(format_output(result))
    return 1 if "error" in result else 0


if __name__ == "__main__":
    _force_utf8_console()
    raise SystemExit(main())
