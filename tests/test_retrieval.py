"""Lexical retrieval quality: normalization, field weighting, name matching, honesty."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "skill" / "snowe-ui-skill" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from core import CSV_CONFIG, search, search_stack, stem, tokenize  # noqa: E402


class NormalizationTests(unittest.TestCase):
    def test_inflections_and_hyphen_compounds_meet(self):
        self.assertEqual(["rerender"], tokenize("rerenders"))
        self.assertEqual(["rerender"], tokenize("rerendering"))
        self.assertIn("rerender", tokenize("re-render"))
        self.assertEqual(tokenize("lists"), tokenize("list"))
        self.assertEqual(tokenize("categories"), tokenize("category"))
        self.assertEqual(tokenize("caching"), tokenize("cache"))
        self.assertEqual(tokenize("embedded"), tokenize("embed"))

    def test_short_and_base_words_are_not_mangled(self):
        for word in ("string", "speed", "class", "status", "analysis", "ios"):
            self.assertEqual(word, stem(word), word)

    def test_stopwords_do_not_score(self):
        self.assertEqual([], tokenize("for the vs of a"))
        self.assertEqual(["dashboard", "operation", "team"], tokenize("dashboard for the operations team"))

    def test_non_english_text_passes_through_unstemmed(self):
        self.assertEqual(["магазины"], tokenize("магазины"))


class RankingTests(unittest.TestCase):
    def test_inflected_query_reaches_rerender_rows(self):
        result = search("list rerenders", "react", 5)
        self.assertGreater(result["count"], 0)
        categories = {row["Category"] for row in result["results"]}
        self.assertIn("Rerender", categories)

    def test_specific_row_beats_incidental_single_term_matches(self):
        result = search("infinite scroll vs pagination", "ux", 5)
        self.assertEqual("Infinite Scroll vs Pagination", result["results"][0]["Issue"])
        self.assertNotIn("Smooth Scroll", {row["Issue"] for row in result["results"]})

    def test_query_coverage_outranks_a_rare_single_term(self):
        result = search("dashboard for the operations team", "product", 5)
        self.assertNotEqual("Sports Team/Club", result["results"][0]["Product Type"])
        self.assertIn("Dashboard", result["results"][0]["Product Type"])

    def test_exact_name_ranks_first_then_name_prefixes(self):
        result = search("IBM Plex Sans", "google-fonts", 5)
        families = [row["Family"] for row in result["results"]]
        self.assertEqual("IBM Plex Sans", families[0])
        self.assertTrue(all(name.startswith("IBM Plex Sans") for name in families))

    def test_ux_do_column_is_searched(self):
        self.assertIn("Do", CSV_CONFIG["ux"]["search_cols"])
        result = search("tabindex", "ux", 3)
        self.assertEqual("Keyboard Navigation", result["results"][0]["Issue"])

    def test_stack_guideline_names_weigh_most(self):
        result = search_stack("x:Bind binding", "winui", 3)
        self.assertIn("x:Bind", result["results"][0]["Guideline"])


class HonestyTests(unittest.TestCase):
    def test_unrepresentable_terms_are_reported_not_silently_ignored(self):
        result = search("geometric sans cyrillic", "google-fonts", 5)
        self.assertEqual(["geometric"], result["unmatched_terms"])
        self.assertIn("geometric", result["warning"])
        self.assertTrue(result["results"])
        self.assertTrue(all("cyrillic" in row["Subsets"] for row in result["results"]))

    def test_every_response_lists_unmatched_terms(self):
        self.assertEqual([], search("touch target", "mobile", 1)["unmatched_terms"])
        self.assertEqual(["zzzz"], search_stack("zzzz", "flutter", 1)["unmatched_terms"])
        self.assertEqual(0, search_stack("zzzz", "flutter", 1)["count"])

    def test_cli_text_output_shows_the_unmatched_warning(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPTS / "search.py"), "geometric sans cyrillic", "--domain", "google-fonts"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("did not affect ranking: geometric", completed.stdout)
        payload = json.loads(
            subprocess.run(
                [sys.executable, str(SCRIPTS / "search.py"), "IBM Plex Sans", "--domain", "google-fonts", "--json"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            ).stdout
        )
        self.assertEqual("IBM Plex Sans", payload["results"][0]["Family"])
        self.assertEqual([], payload["unmatched_terms"])


if __name__ == "__main__":
    unittest.main()
