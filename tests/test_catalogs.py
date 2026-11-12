"""Bundled evidence-catalog hygiene and recipe-leakage regressions.

The catalogs are subordinate lexical evidence.  These tests keep them
well-formed and stop solution-shaped values (exact colors, motion durations,
color utilities, numbered layout templates, frame-rate claims) from
re-entering any shipped CSV cell, including columns that retrieval does not
return: an installed file is readable by any agent regardless of
``CSV_CONFIG``.
"""

from __future__ import annotations

import csv
import io
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skill" / "snowe-ui-skill"
DATA_DIR = SKILL_ROOT / "data"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from core import AVAILABLE_STACKS, CSV_CONFIG, STACK_CONFIG, _STACK_COLS, search_stack  # noqa: E402


RECIPE_PATTERNS = {
    "hex color": re.compile(r"(?<![\w&])#(?:[0-9A-Fa-f]{8}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{3,4})\b"),
    "millisecond duration": re.compile(
        r"\b\d+(?:\.\d+)?\s*(?:[-–]\s*\d+(?:\.\d+)?\s*)?(?:ms|milliseconds?)\b",
        re.IGNORECASE,
    ),
    "Tailwind color utility": re.compile(
        r"\b(?:[a-z0-9-]+:)*"
        r"(?:bg|text|from|via|to|border(?:-[trblxy])?|ring(?:-offset)?|fill|stroke|outline|decoration|shadow|accent|caret|divide|placeholder)-"
        r"(?:slate|gray|grey|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose|white|black)"
        r"(?:-\d{2,3})?(?:/\d{1,3})?\b"
    ),
    "numbered template prescription": re.compile(
        r"\b(?:dashboard|sidebar|login|signup|otp|calendar|hero|pricing|features?|footer|header|navbar|cta|"
        r"testimonials?|blog|contact|faq|stats|team|landing|auth)-\d{2}\b",
        re.IGNORECASE,
    ),
    "frame-rate claim": re.compile(r"\b\d+\s*fps\b|\bframes per second\b", re.IGNORECASE),
}

# Findings in stack catalogs owned by a parallel rewrite (or not yet owned by
# any cleanup).  They are listed exactly -- file, row id, pattern, matched
# text -- so a new occurrence anywhere still fails.  Each entry must be
# deleted when its row is cleaned; a stale entry fails
# ``test_pending_allowlist_entries_still_match`` so the list cannot rot.
PENDING_OUTSIDE_THIS_CLEANUP = {
    ("stacks/angular.csv", "43", "hex color", "#6200ee"),
    ("stacks/astro.csv", "18", "hex color", "#3b82f6"),
    ("stacks/avalonia.csv", "51", "hex color", "#FF0078D4"),
    ("stacks/html-tailwind.csv", "4", "Tailwind color utility", "hover:bg-gray-100"),
    ("stacks/html-tailwind.csv", "20", "Tailwind color utility", "bg-black"),
    ("stacks/html-tailwind.csv", "20", "Tailwind color utility", "bg-black/50"),
    ("stacks/html-tailwind.csv", "20", "Tailwind color utility", "text-white/80"),
    ("stacks/html-tailwind.csv", "21", "Tailwind color utility", "dark:bg-gray-900"),
    ("stacks/html-tailwind.csv", "21", "Tailwind color utility", "dark:text-white"),
    ("stacks/html-tailwind.csv", "22", "Tailwind color utility", "bg-blue-500"),
    ("stacks/html-tailwind.csv", "26", "Tailwind color utility", "focus:ring-blue-500"),
    ("stacks/html-tailwind.csv", "29", "Tailwind color utility", "placeholder:text-gray-400"),
    ("stacks/html-tailwind.csv", "49", "Tailwind color utility", "group-hover:text-blue-500"),
    ("stacks/html-tailwind.csv", "52", "Tailwind color utility", "from-blue-500"),
    ("stacks/html-tailwind.csv", "52", "Tailwind color utility", "to-purple-500"),
    ("stacks/javafx.csv", "9", "hex color", "#2563eb"),
    ("stacks/javafx.csv", "10", "hex color", "#2563eb"),
    ("stacks/javafx.csv", "36", "millisecond duration", "150-250ms"),
    ("stacks/javafx.csv", "49", "hex color", "#2563eb"),
    ("stacks/javafx.csv", "49", "hex color", "#dc2626"),
    ("stacks/laravel.csv", "27", "hex color", "#1a2b3c"),
    ("stacks/laravel.csv", "31", "Tailwind color utility", "bg-blue-600"),
    ("stacks/laravel.csv", "36", "Tailwind color utility", "text-red-500"),
    ("stacks/laravel.csv", "43", "millisecond duration", "200ms"),
    ("stacks/nuxt-ui.csv", "5", "Tailwind color utility", "bg-green-500"),
    ("stacks/nuxt-ui.csv", "10", "Tailwind color utility", "bg-blue-500"),
    ("stacks/nuxt-ui.csv", "11", "hex color", "#ef4444"),
    ("stacks/shadcn.csv", "4", "Tailwind color utility", "bg-blue-500"),
    ("stacks/shadcn.csv", "4", "Tailwind color utility", "text-white"),
    ("stacks/shadcn.csv", "7", "Tailwind color utility", "bg-blue-500"),
    ("stacks/shadcn.csv", "7", "Tailwind color utility", "bg-red-500"),
    ("stacks/shadcn.csv", "48", "hex color", "#2563eb"),
    ("stacks/shadcn.csv", "50", "numbered template prescription", "dashboard-01"),
    ("stacks/shadcn.csv", "50", "numbered template prescription", "login-01"),
    ("stacks/shadcn.csv", "51", "numbered template prescription", "dashboard-01"),
    ("stacks/threejs.csv", "line 9", "hex color", "#0d0d0d"),
    ("stacks/threejs.csv", "line 45", "frame-rate claim", "60fps"),
    ("stacks/threejs.csv", "line 45", "frame-rate claim", "8fps"),
    ("stacks/uno.csv", "21", "hex color", "#FFFFFF"),
    ("stacks/uno.csv", "56", "hex color", "#005A9E"),
    ("stacks/uno.csv", "56", "hex color", "#3A96DD"),
    ("stacks/wpf.csv", "18", "hex color", "#0078D4"),
    ("stacks/wpf.csv", "44", "hex color", "#333333"),
}


def bundled_csv_paths():
    return sorted(DATA_DIR.rglob("*.csv"))


def read_rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.reader(handle))


def scan_recipe_values():
    findings = set()
    for path in bundled_csv_paths():
        rows = read_rows(path)
        header, body = rows[0], rows[1:]
        has_id = bool(header) and header[0] == "No"
        relative = path.relative_to(DATA_DIR).as_posix()
        for offset, row in enumerate(body, start=2):
            row_id = row[0] if has_id else f"line {offset}"
            for cell in row:
                for kind, pattern in RECIPE_PATTERNS.items():
                    for match in pattern.finditer(cell):
                        findings.add((relative, row_id, kind, match.group(0)))
    return findings


def configured_catalogs():
    for domain, config in CSV_CONFIG.items():
        yield domain, config["file"], config["search_cols"], config["output_cols"]
    for stack, config in STACK_CONFIG.items():
        yield f"stack:{stack}", config["file"], _STACK_COLS["search_cols"], _STACK_COLS["output_cols"]


class CatalogHygieneTests(unittest.TestCase):
    def test_every_bundled_csv_is_strict_utf8_lf_and_rectangular(self):
        for path in bundled_csv_paths():
            relative = path.relative_to(DATA_DIR).as_posix()
            with self.subTest(catalog=relative):
                raw = path.read_bytes()
                self.assertFalse(raw.startswith(b"\xef\xbb\xbf"), "UTF-8 BOM")
                self.assertNotIn(b"\r", raw, "CR or CRLF line ending")
                self.assertTrue(raw.endswith(b"\n"), "missing final newline")
                text = raw.decode("utf-8")
                rows = list(csv.reader(io.StringIO(text, newline="")))
                header = rows[0]
                self.assertTrue(all(name.strip() == name and name for name in header), header)
                self.assertEqual(len(header), len(set(header)), "duplicate header")
                widths = {len(row) for row in rows}
                self.assertEqual({len(header)}, widths, "ragged rows")
                if header[0] == "No":
                    ids = [row[0] for row in rows[1:]]
                    self.assertEqual(len(ids), len(set(ids)), "duplicate row id")

    def test_configured_columns_exist_in_catalog_headers(self):
        for name, filename, search_cols, output_cols in configured_catalogs():
            path = DATA_DIR / filename
            with self.subTest(catalog=name):
                self.assertTrue(path.is_file(), filename)
                header = set(read_rows(path)[0])
                # A row id is returned wherever the schema has one; it is not
                # required of catalogs that identify rows by a name column.
                required = (set(search_cols) | set(output_cols)) - {"No"}
                self.assertLessEqual(required, header, f"{filename} lacks {sorted(required - header)}")


class RecipeLeakageTests(unittest.TestCase):
    def test_bundled_csvs_contain_no_recipe_values(self):
        unexpected = sorted(scan_recipe_values() - PENDING_OUTSIDE_THIS_CLEANUP)
        self.assertEqual([], unexpected)

    def test_pending_allowlist_entries_still_match(self):
        stale = sorted(PENDING_OUTSIDE_THIS_CLEANUP - scan_recipe_values())
        self.assertEqual([], stale, "remove cleaned rows from PENDING_OUTSIDE_THIS_CLEANUP")

    def test_patterns_detect_each_recipe_shape(self):
        samples = {
            "hex color": "Primary: #0080FF",
            "millisecond duration": "Use 150-300ms for micro-interactions",
            "Tailwind color utility": "bg-gradient-to-r from-blue-500 to-purple-500",
            "numbered template prescription": "npx shadcn add dashboard-01",
            "frame-rate claim": "smooth at 60fps",
        }
        for kind, sample in samples.items():
            with self.subTest(kind=kind):
                self.assertRegex(sample, RECIPE_PATTERNS[kind])
        for harmless in ("C# and F#", "#section anchor", "WCAG 2.2 SC 2.5.8", "h-20 spacing", "utf-8"):
            with self.subTest(harmless=harmless):
                self.assertFalse(any(p.search(harmless) for p in RECIPE_PATTERNS.values()))


class ChartCatalogTests(unittest.TestCase):
    def test_chart_catalog_holds_only_returned_columns(self):
        header = read_rows(DATA_DIR / "charts.csv")[0]
        returned = set(CSV_CONFIG["chart"]["output_cols"]) | {"No"}
        self.assertEqual(returned, set(header))
        for withheld in (
            "When to Use",
            "When NOT to Use",
            "Data Volume Threshold",
            "Color Guidance",
            "Accessibility Grade",
            "Library Recommendation",
            "Interactive Level",
        ):
            self.assertNotIn(withheld, header)

    def test_accessibility_notes_do_not_misstate_wcag(self):
        text = (DATA_DIR / "charts.csv").read_text(encoding="utf-8")
        # WCAG has no chart-type rule: color-only meaning is SC 1.4.1.
        self.assertNotRegex(text, re.compile(r"\bfails?\s+WCAG\b", re.IGNORECASE))
        self.assertNotIn("Limit axes to", text)
        self.assertIn("SC 1.4.1", text)


class UxCatalogTests(unittest.TestCase):
    def rows(self, filename):
        with (DATA_DIR / filename).open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_target_size_separates_wcag_minimum_from_platform_guidance(self):
        row = next(item for item in self.rows("ux-guidelines.csv") if item["Issue"] == "Touch Target Size")
        self.assertIn("2.5.8", row["Description"])
        self.assertIn("24 by 24 CSS pixels", row["Description"])
        self.assertIn("44 by 44 pt", row["Description"])
        self.assertIn("48 by 48 dp", row["Description"])

    def test_obsolete_duplicate_and_preset_rows_are_gone(self):
        rows = self.rows("ux-guidelines.csv")
        text = (DATA_DIR / "ux-guidelines.csv").read_text(encoding="utf-8").casefold()
        self.assertNotIn("fastclick", text)
        self.assertNotIn("glass material", text)
        self.assertNotIn("key elements per view maximum", text)
        self.assertNotIn("ease-out for entering", text)
        issues = [row["Issue"].casefold() for row in rows]
        self.assertEqual(len(issues), len(set(issues)), "duplicate issue names")
        for removed in ("25", "54", "73", "75", "76", "78", "83", "99"):
            self.assertNotIn(removed, {row["No"] for row in rows})


class NativeStackTests(unittest.TestCase):
    """Recommended columns must not teach APIs the platform has superseded."""

    RECOMMENDING = ("Guideline", "Do", "Code Good")

    def rows(self, stack):
        with (DATA_DIR / STACK_CONFIG[stack]["file"]).open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def recommended_text(self, stack):
        return [
            (row["No"], " ".join(row[column] for column in self.RECOMMENDING))
            for row in self.rows(stack)
        ]

    def assert_not_recommended(self, stack, pattern):
        offenders = [number for number, text in self.recommended_text(stack) if re.search(pattern, text)]
        self.assertEqual([], offenders, f"{stack} recommends {pattern!r}")

    def test_flutter_recommends_current_apis(self):
        for superseded in (
            r"\btextScaleFactor\b",
            r"\bonPopInvoked\b(?!WithResult)",
            r"\bWillPopScope\b",
            r"\bpushNamed\b",
            r"\bprimaryColor\b",
            r"FutureBuilder\(future:\s*\w+\(",
        ):
            self.assert_not_recommended("flutter", superseded)
        text = " ".join(" ".join(row.values()) for row in self.rows("flutter"))
        self.assertIn("onPopInvokedWithResult", text)
        self.assertIn("textScalerOf", text)

    def test_swiftui_recommends_current_apis_and_observation(self):
        for superseded in (
            r"\.animation\(\.[A-Za-z]+(?:\([^)]*\))?\)",
            r"\bforegroundColor\(",
            r"\bcornerRadius\(",
            r"\bNavigationView\b(?! in new code)",
            r"\bpresentationMode\b",
        ):
            self.assert_not_recommended("swiftui", superseded)
        high = [row for row in self.rows("swiftui") if row["Severity"] == "High"]
        self.assertFalse(
            [row["No"] for row in high if "ObservableObject" in row["Do"] and "@Observable" not in row["Do"]],
            "a High-severity row makes ObservableObject the default",
        )
        modifier_order = next(row for row in self.rows("swiftui") if row["Guideline"] == "Order modifiers correctly")
        self.assertIn("padding before background", modifier_order["Do"])
        self.assertTrue(modifier_order["Code Good"].startswith(".padding().background"))

    def test_compose_rows_carry_code_and_current_guidance(self):
        rows = self.rows("jetpack-compose")
        self.assertFalse([row["No"] for row in rows if " ? " in " ".join(row.values())], "mangled arrows")
        codeish = re.compile(r"[(){}=:]")
        self.assertFalse(
            # Tooling rows (Layout Inspector) describe a procedure, not code.
            [row["No"] for row in rows if row["Category"] != "Debug" and not codeish.search(row["Code Good"])],
            "Code Good must contain code, not a slogan",
        )
        self.assert_not_recommended("jetpack-compose", r"\bChannel\b|receiveAsFlow")
        self.assert_not_recommended("jetpack-compose", r"collectAsState\(\)")
        self.assertTrue(all(row["Docs URL"].startswith("https://") for row in rows if row["Docs URL"]))


class RetiredStackTests(unittest.TestCase):
    def test_uwp_catalog_is_gone_and_winui_carries_migration_rows(self):
        self.assertFalse((DATA_DIR / "stacks" / "uwp.csv").exists())
        self.assertNotIn("uwp", STACK_CONFIG)
        self.assertNotIn("uwp", list(AVAILABLE_STACKS))
        with (DATA_DIR / "stacks" / "winui.csv").open(encoding="utf-8", newline="") as handle:
            guidelines = {row["Guideline"] for row in csv.DictReader(handle)}
        self.assertIn("Migrate UWP code by feature area", guidelines)
        self.assertIn("Choose WinUI 3 for new native Windows XAML apps", guidelines)

    def test_retired_stack_lookup_names_the_replacement(self):
        result = search_stack("dialog", "uwp")
        self.assertEqual("winui", result["replacement"])
        self.assertIn("retired", result["error"])
        self.assertIn("--stack winui", result["error"])
        self.assertNotIn("results", result)

    def test_cli_reports_the_retirement_instead_of_a_generic_choice_error(self):
        completed = subprocess.run(
            [sys.executable, str(SKILL_ROOT / "scripts" / "search.py"), "dialog", "--stack", "uwp", "--json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertNotIn("invalid choice", completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual("winui", payload["replacement"])
        self.assertIn("--stack winui", payload["error"])
        help_text = subprocess.run(
            [sys.executable, str(SKILL_ROOT / "scripts" / "search.py"), "--help"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        ).stdout
        self.assertNotIn("uwp", help_text)


if __name__ == "__main__":
    unittest.main()
