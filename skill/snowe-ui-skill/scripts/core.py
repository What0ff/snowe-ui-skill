#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Snowe UI Skill Core: BM25 retrieval over explicitly selected evidence catalogs."""

import csv
import re
from pathlib import Path
from math import log
from collections import defaultdict

# ============ CONFIGURATION ============
DATA_DIR = Path(__file__).parent.parent / "data"
MAX_RESULTS = 3

ICON_CANDIDATE_FAMILY_ALIASES = {
    "lucide": "Lucide",
    "tabler": "Tabler Icons",
    "iconoir": "Iconoir",
    "phosphor": "Phosphor",
    "radix": "Radix Icons",
    "remix": "Remix Icon",
    "hugeicons": "Hugeicons Free",
}

CSV_CONFIG = {
    "chart": {
        "file": "charts.csv",
        "search_cols": ["Data Type", "Keywords", "Best Chart Type", "When to Use", "When NOT to Use", "Accessibility Notes"],
        "output_cols": ["Data Type", "Keywords", "Best Chart Type", "Secondary Options", "When to Use", "When NOT to Use", "Data Volume Threshold", "Color Guidance", "Accessibility Grade", "Accessibility Notes", "A11y Fallback", "Library Recommendation", "Interactive Level"]
    },
    "product": {
        "file": "products.csv",
        "search_cols": ["Product Type", "Keywords"],
        "output_cols": ["Product Type", "Keywords"]
    },
    "ux": {
        "file": "ux-guidelines.csv",
        "search_cols": ["Category", "Issue", "Description", "Platform"],
        "output_cols": ["Category", "Issue", "Platform", "Description", "Do", "Don't", "Code Example Good", "Code Example Bad", "Severity"]
    },
    "icons": {
        "file": "icons.csv",
        "search_cols": ["Category", "Icon Name", "Keywords", "Best For"],
        "output_cols": ["Category", "Icon Name", "Keywords", "Library", "Import Code", "Usage", "Best For", "Style"]
    },
    "icon-families": {
        "file": "icon-families.csv",
        "search_cols": ["Family", "Platforms", "Visual Character", "Best For", "Avoid When", "Keywords"],
        "output_cols": ["Family", "Platforms", "Visual Character", "Best For", "Avoid When", "Grid and Modes", "Package Hint", "License", "Official URL"]
    },
    "icon-concepts": {
        "file": "icon-concepts.csv",
        "search_cols": ["Concept", "Role", "Preferred Mapping", "Candidates to Explore", "Avoid as Default", "Allowed When", "Keywords"],
        "output_cols": ["Concept", "Role", "Preferred Mapping", "Candidates to Explore", "Avoid as Default", "Allowed When", "Label Policy"]
    },
    "icon-candidates": {
        "file": "icon-candidates.csv",
        "search_cols": ["Concept", "Role", "Family", "Icon Name", "Metaphor", "Use When", "Avoid When", "Keywords"],
        "output_cols": ["Concept", "Role", "Family", "Icon Name", "Package", "Import Hint", "Metaphor", "Use When", "Avoid When", "Verified Version", "Official URL"]
    },
    "react": {
        "file": "react-performance.csv",
        "search_cols": ["Category", "Issue", "Keywords", "Description"],
        "output_cols": ["Category", "Issue", "Platform", "Description", "Do", "Don't", "Code Example Good", "Code Example Bad", "Severity"]
    },
    "web": {
        "file": "app-interface.csv",
        "search_cols": ["Category", "Issue", "Keywords", "Description"],
        "output_cols": ["Category", "Issue", "Platform", "Description", "Do", "Don't", "Code Example Good", "Code Example Bad", "Severity"]
    },
    "google-fonts": {
        "file": "google-fonts.csv",
        "search_cols": ["Family", "Category", "Stroke", "Classifications", "Keywords", "Subsets", "Designers"],
        "output_cols": ["Family", "Category", "Stroke", "Classifications", "Styles", "Variable Axes", "Subsets", "Designers", "Popularity Rank", "Google Fonts URL"]
    }
}

# These labels make the epistemic role of bundled snapshots explicit.  The
# catalogs help an agent discover vocabulary, constraints, and analogs; they do
# not classify the current product or select a design on the agent's behalf.
DOMAIN_SOURCE_ROLES = {
    "product": (
        "analogy evidence",
        "Treat matches as unverified analogs. Reuse relevant concerns only; do not inherit product identity, layout, style, palette, or landing recipe.",
    ),
    "google-fonts": (
        "font catalog snapshot",
        "Confirm current official metadata and actual files before choosing or loading a family.",
    ),
    "icon-families": (
        "icon-source discovery snapshot",
        "Verify the current official catalog, license, package, platform support, and rendered drawing-language fit.",
    ),
    "icon-candidates": (
        "named-glyph discovery snapshot",
        "Confirm the exact export in the selected current version and compare it at the real optical size and surface.",
    ),
    "icon-concepts": (
        "metaphor prompts",
        "Use the real object, action, mechanism, or consequence; a catalog metaphor is never mandatory.",
    ),
    "icons": (
        "legacy universal-icon lookup",
        "Use only for familiar system actions and verify the repository's actual source. Product-specific symbols require broader reasoning.",
    ),
    "chart": (
        "visualization guidance snapshot",
        "Choose an encoding from the user's analytical question and representative data, then verify accessibility and edge states.",
    ),
    "ux": (
        "general UX guidance",
        "Reconcile with the real journey, current standards, repository behavior, and user evidence.",
    ),
    "web": (
        "web implementation guidance",
        "Reconcile with current standards, browser support, and the repository's actual semantics and behavior.",
    ),
    "react": (
        "React performance guidance",
        "Verify against the current framework version, official documentation, and measured runtime behavior.",
    ),
}

STACK_CONFIG = {
    "react":            {"file": "stacks/react.csv"},
    "nextjs":           {"file": "stacks/nextjs.csv"},
    "vue":              {"file": "stacks/vue.csv"},
    "svelte":           {"file": "stacks/svelte.csv"},
    "astro":            {"file": "stacks/astro.csv"},
    "swiftui":          {"file": "stacks/swiftui.csv"},
    "react-native":     {"file": "stacks/react-native.csv"},
    "flutter":          {"file": "stacks/flutter.csv"},
    "nuxtjs":           {"file": "stacks/nuxtjs.csv"},
    "nuxt-ui":          {"file": "stacks/nuxt-ui.csv"},
    "html-tailwind":    {"file": "stacks/html-tailwind.csv"},
    "shadcn":           {"file": "stacks/shadcn.csv"},
    "jetpack-compose":  {"file": "stacks/jetpack-compose.csv"},
    "threejs":          {"file": "stacks/threejs.csv"},
    "angular":          {"file": "stacks/angular.csv"},
    "laravel":          {"file": "stacks/laravel.csv"},
    "javafx":           {"file": "stacks/javafx.csv"},
    "wpf":              {"file": "stacks/wpf.csv"},
    "winui":            {"file": "stacks/winui.csv"},
    "avalonia":         {"file": "stacks/avalonia.csv"},
    "uno":              {"file": "stacks/uno.csv"},
    "uwp":              {"file": "stacks/uwp.csv"},
}

# Common columns for all stacks
_STACK_COLS = {
    "search_cols": ["Category", "Guideline", "Description", "Do", "Don't"],
    "output_cols": ["Category", "Guideline", "Description", "Do", "Don't", "Code Good", "Code Bad", "Severity", "Docs URL"]
}

AVAILABLE_STACKS = list(STACK_CONFIG.keys())
STACK_SOURCE_ROLE = "caller-selected bundled stack implementation-guidance snapshot"
STACK_WARNING = (
    "Treat results as advisory prompts, not current platform or API truth. "
    "Verify material and version-sensitive claims against the target repository and current primary documentation. "
    "A returned Docs URL is a discovery pointer, not proof of source primacy or freshness."
)


# ============ BM25 IMPLEMENTATION ============
class BM25:
    """BM25 ranking algorithm for text search"""

    def __init__(self, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.corpus = []
        self.doc_lengths = []
        self.avgdl = 0
        self.idf = {}
        self.doc_freqs = defaultdict(int)
        self.N = 0

    def tokenize(self, text):
        """Lowercase, split, remove punctuation, filter short words"""
        text = re.sub(r'[^\w\s]', ' ', str(text).lower())
        return [w for w in text.split() if len(w) >= 2]

    def fit(self, documents):
        """Build BM25 index from documents"""
        self.corpus = [self.tokenize(doc) for doc in documents]
        self.N = len(self.corpus)
        if self.N == 0:
            return
        self.doc_lengths = [len(doc) for doc in self.corpus]
        self.avgdl = sum(self.doc_lengths) / self.N

        for doc in self.corpus:
            seen = set()
            for word in doc:
                if word not in seen:
                    self.doc_freqs[word] += 1
                    seen.add(word)

        for word, freq in self.doc_freqs.items():
            self.idf[word] = log((self.N - freq + 0.5) / (freq + 0.5) + 1)

    def score(self, query):
        """Score all documents against query"""
        query_tokens = self.tokenize(query)
        scores = []

        for idx, doc in enumerate(self.corpus):
            score = 0
            doc_len = self.doc_lengths[idx]
            term_freqs = defaultdict(int)
            for word in doc:
                term_freqs[word] += 1

            for token in query_tokens:
                if token in self.idf:
                    tf = term_freqs[token]
                    idf = self.idf[token]
                    numerator = tf * (self.k1 + 1)
                    denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
                    score += idf * numerator / denominator

            scores.append((idx, score))

        return sorted(scores, key=lambda x: x[1], reverse=True)


# ============ SEARCH FUNCTIONS ============
def _load_csv(filepath):
    """Load CSV and return list of dicts"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def _search_csv(filepath, search_cols, output_cols, query, max_results, row_filter=None):
    """Core search function using BM25"""
    if not filepath.exists():
        return []

    data = _load_csv(filepath)
    if row_filter is not None:
        data = [row for row in data if row_filter(row)]

    # Build documents from search columns
    documents = [" ".join(str(row.get(col, "")) for col in search_cols) for row in data]

    # BM25 search
    bm25 = BM25()
    bm25.fit(documents)
    ranked = bm25.score(query)

    # Get top results with score > 0
    results = []
    for idx, score in ranked[:max_results]:
        if score > 0:
            row = data[idx]
            results.append({col: row.get(col, "") for col in output_cols if col in row})

    return results


def search(query, domain=None, max_results=MAX_RESULTS):
    """Search one caller-selected evidence domain without semantic inference."""
    if domain is None:
        return {
            "error": "An explicit evidence domain is required; automatic semantic domain detection is intentionally unavailable",
            "query": query,
            "available_domains": list(CSV_CONFIG),
        }
    if domain not in CSV_CONFIG:
        return {
            "error": f"Unknown evidence domain: {domain}",
            "domain": domain,
            "query": query,
            "available_domains": list(CSV_CONFIG),
        }

    config = CSV_CONFIG[domain]
    filepath = DATA_DIR / config["file"]

    if not filepath.exists():
        return {"error": f"File not found: {filepath}", "domain": domain}

    candidate_family = None
    retrieval_query = query
    if domain == "icon-candidates":
        requested_families = {
            family
            for alias, family in ICON_CANDIDATE_FAMILY_ALIASES.items()
            if re.search(r"\b" + re.escape(alias) + r"\b", query.casefold())
        }
        if len(requested_families) != 1:
            return {
                "error": "icon-candidates requires exactly one source family per lookup: Lucide, Tabler, Iconoir, Phosphor, Radix, Remix, or Hugeicons; run separate lookups when comparing justified sources",
                "domain": domain,
                "query": query,
                "file": config["file"],
            }
        candidate_family = next(iter(requested_families))
        for alias, family in ICON_CANDIDATE_FAMILY_ALIASES.items():
            if family == candidate_family:
                retrieval_query = re.sub(r"\b" + re.escape(alias) + r"\b", " ", retrieval_query, flags=re.IGNORECASE)
        retrieval_query = re.sub(
            r"\b(?:icon|icons|glyph|glyphs|candidate|candidates|export|exports|name|named)\b",
            " ",
            retrieval_query,
            flags=re.IGNORECASE,
        )
        if not re.search(r"\w{2,}", retrieval_query, flags=re.UNICODE):
            return {
                "error": "icon-candidates also requires a real subject, mechanism, output, or concept after the source family",
                "domain": domain,
                "query": query,
                "file": config["file"],
            }

    retrieval_limit = max_results
    if domain == "icons":
        # Historical icon data includes style recipes that promoted neon glow
        # and circular wrappers. Retrieve extra concrete symbols, then exclude
        # those recipes so direct lookup cannot reintroduce obsolete policy.
        retrieval_limit = max(max_results * 4, 12)
    row_filter = None
    if candidate_family:
        row_filter = lambda row: row.get("Family", "") == candidate_family
    results = _search_csv(
        filepath,
        config["search_cols"],
        config["output_cols"],
        retrieval_query,
        retrieval_limit,
        row_filter=row_filter,
    )

    if domain == "icons":
        results = [
            result
            for result in results
            if result.get("Category", "").casefold() not in {"style config", "guideline"}
        ][:max_results]

    source_role, source_warning = DOMAIN_SOURCE_ROLES.get(
        domain,
        (
            "retrieval evidence",
            "Treat the bundled result as a snapshot and verify current facts and contextual fit before use.",
        ),
    )
    return {
        "domain": domain,
        "query": query,
        "file": config["file"],
        "source_role": source_role,
        "warning": source_warning,
        "count": len(results),
        "results": results
    }


def search_stack(query, stack, max_results=MAX_RESULTS):
    """Search stack-specific guidelines"""
    if stack not in STACK_CONFIG:
        return {"error": f"Unknown stack: {stack}. Available: {', '.join(AVAILABLE_STACKS)}"}

    filepath = DATA_DIR / STACK_CONFIG[stack]["file"]

    if not filepath.exists():
        return {"error": f"Stack file not found: {filepath}", "stack": stack}

    results = _search_csv(filepath, _STACK_COLS["search_cols"], _STACK_COLS["output_cols"], query, max_results)
    docs_urls_present = sum(bool(str(row.get("Docs URL", "")).strip()) for row in results)
    docs_urls_missing = len(results) - docs_urls_present
    warning = STACK_WARNING
    if docs_urls_missing:
        warning += (
            f" {docs_urls_missing} of {len(results)} returned row(s) have no Docs URL and remain unsourced "
            "bundled guidance until independently verified."
        )

    return {
        "domain": "stack",
        "stack": stack,
        "query": query,
        "file": STACK_CONFIG[stack]["file"],
        "source_role": STACK_SOURCE_ROLE,
        "warning": warning,
        "documentation_coverage": {
            "returned_rows": len(results),
            "docs_urls_present": docs_urls_present,
            "docs_urls_missing": docs_urls_missing,
        },
        "count": len(results),
        "results": results
    }
