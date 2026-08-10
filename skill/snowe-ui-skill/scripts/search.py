#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Snowe UI Skill Search - local evidence retrieval and design decision packets
Usage: python search.py "<query>" [--domain <domain>] [--stack <stack>] [--max-results 3]
       python search.py "<brief>" --decision-packet [-p "Project Name"]
       python search.py "<brief>" --decision-packet --persist [-p "Project Name"] [--page "catalog"]

Domains: style, color, chart, landing, product, ux, typography, icons, icon-families, icon-concepts, icon-candidates, gsap, react, web, google-fonts
Stacks: react, nextjs, vue, svelte, astro, swiftui, react-native, flutter, nuxtjs, nuxt-ui, html-tailwind, shadcn, jetpack-compose, threejs, angular, laravel, javafx, wpf, winui, avalonia, uno, uwp

Decision packets keep architecture, art direction, imagery, custom graphics,
motion, and responsive behavior open until an agent compares real candidates.
The historical --design-system spelling remains an alias, but no recipe-based
design system is selected.

Persistence:
  --persist    Save design-intelligence/<project>/BRIEF.md and initialize a
               non-overwritten DECISIONS.md
  --page       Also create a page inquiry without prescribing a page type or section order
"""

import argparse
import sys
import io
from core import CSV_CONFIG, AVAILABLE_STACKS, MAX_RESULTS, search, search_stack
from decision_packet import generate_decision_packet, slugify_name

# Force UTF-8 for stdout/stderr to handle emojis on Windows (cp1252 default)
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Snowe UI Skill Search")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--domain", "-d", choices=list(CSV_CONFIG.keys()), help="Search domain")
    parser.add_argument("--stack", "-s", choices=AVAILABLE_STACKS, help=f"Stack-specific search. Available: {', '.join(AVAILABLE_STACKS)}")
    parser.add_argument("--max-results", "-n", type=int, default=MAX_RESULTS, help="Max results (default: 3)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    # Architecture-first design decision packet. --design-system remains a
    # compatibility alias but no longer chooses a recipe-based design system.
    parser.add_argument(
        "--decision-packet",
        "--design-system",
        "-dp",
        "-ds",
        dest="decision_packet",
        action="store_true",
        help="Open an architecture-first design decision packet; does not select a layout, style, palette, font, imagery, or motion recipe",
    )
    parser.add_argument("--project-name", "-p", type=str, default=None, help="Project name for decision-packet output")
    parser.add_argument("--format", "-f", choices=["markdown", "json"], default="markdown", help="Decision-packet output format")
    # Persistence (Brief + durable decisions + page inquiries)
    parser.add_argument("--persist", action="store_true", help="Save BRIEF.md and initialize a durable non-overwritten DECISIONS.md")
    parser.add_argument("--page", type=str, default=None, help="Create a page inquiry without prescribing a page type or section order")
    parser.add_argument("--output-dir", "-o", type=str, default=None, help="Output directory for persisted files (default: current directory)")

    args = parser.parse_args()

    if args.domain and args.stack:
        parser.error("--domain and --stack are mutually exclusive")
    if args.decision_packet and (args.domain or args.stack):
        parser.error("--decision-packet cannot be combined with --domain or --stack")
    if args.page and not args.persist:
        parser.error("--page requires --persist")
    if args.output_dir and not args.persist:
        parser.error("--output-dir requires --persist")
    packet_only_values = (args.persist, args.page, args.output_dir)
    if not args.decision_packet and any(value is not None and value is not False for value in packet_only_values):
        parser.error("--persist, --page, and --output-dir require --decision-packet")
    if args.decision_packet and args.json:
        parser.error("--json is available for domain and stack searches; use --format json for decision packets")

    # Decision packet takes priority
    if args.decision_packet:
        result = generate_decision_packet(
            args.query,
            args.project_name,
            args.format,
            persist=args.persist,
            page=args.page,
            output_dir=args.output_dir,
            page_brief=args.query if args.page else None,
        )
        print(result)

        # Print persistence confirmation
        if args.persist:
            project_slug = slugify_name(args.project_name or "untitled-design-inquiry")
            print("\n" + "=" * 60)
            print(f"Design intelligence persisted to design-intelligence/{project_slug}/")
            print(f"   design-intelligence/{project_slug}/BRIEF.md (Regenerated decision packet)")
            print(f"   design-intelligence/{project_slug}/DECISIONS.md (Durable accepted decisions; preserved on regeneration)")
            if args.page:
                page_filename = slugify_name(args.page, "page")
                print(f"   design-intelligence/{project_slug}/pages/{page_filename}.md (Open page inquiry)")
            print("")
            print(f"Usage: Read accepted decisions, then the brief and any relevant page inquiry.")
            print("=" * 60)
    # Stack search
    elif args.stack:
        result = search_stack(args.query, args.stack, args.max_results)
        if args.json:
            import json
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(format_output(result))
    # Domain search
    else:
        result = search(args.query, args.domain, args.max_results)
        if args.json:
            import json
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(format_output(result))
