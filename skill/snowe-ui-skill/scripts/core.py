#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Snowe UI Skill Core: BM25 retrieval over explicitly selected evidence catalogs."""

import csv
import re
from collections import Counter
from math import log
from pathlib import Path

# ============ CONFIGURATION ============
DATA_DIR = Path(__file__).parent.parent / "data"
MAX_RESULTS = 3


def validate_max_results(value):
    """Return a valid result limit or reject an unsafe slicing value.

    ``bool`` is deliberately rejected even though it subclasses ``int``.  A
    non-positive limit is not a useful empty-result request here: passing it
    through to a slice can turn a caller mistake into an unbounded or
    surprising evidence lookup (for example, ``ranked[:-1]``).
    """
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("max_results must be a positive integer")
    return value

# Result dictionaries map catalog column names to cell values.  Catalogs that
# number their rows return that id as the first key, ``No``; deleted rows leave
# gaps so an id cited earlier keeps pointing at the same guidance.  Catalogs
# without a ``No`` column (fonts, icon families/concepts/candidates) identify
# rows by their name column.
#
# ``name_cols`` are the columns that name a row.  They weigh most in ranking
# and drive exact/prefix name matching; ``Keywords`` and ``Category`` weigh
# next; every other searched column counts once.

ICON_CANDIDATE_FAMILY_ALIASES = {
    "lucide": "Lucide",
    "tabler": "Tabler Icons",
    "iconoir": "Iconoir",
    "phosphor": "Phosphor",
    "radix": "Radix Icons",
    "remix": "Remix Icon",
    "hugeicons": "Hugeicons Free",
}

_MOBILE_APP_INTERFACE = {
    "file": "app-interface.csv",
    "name_cols": ["Issue"],
    "search_cols": ["Category", "Issue", "Keywords", "Description", "Do"],
    "output_cols": ["No", "Category", "Issue", "Platform", "Description", "Do", "Don't", "Code Example Good", "Code Example Bad", "Severity"],
}

CSV_CONFIG = {
    "chart": {
        "file": "charts.csv",
        "name_cols": ["Data Type", "Best Chart Type"],
        "search_cols": ["Data Type", "Keywords", "Best Chart Type", "Secondary Options", "Accessibility Notes"],
        # The bundled catalog holds only discovery prompts it can support.
        # Exact data-volume thresholds, threshold-bearing use/avoid prose,
        # palette values, accessibility grades, library recommendations, and
        # interaction prescriptions were deleted from charts.csv (not merely
        # hidden): none of those time-sensitive or context-dependent claims
        # carried a primary-source citation.
        "output_cols": [
            "No",
            "Data Type",
            "Keywords",
            "Best Chart Type",
            "Secondary Options",
            "Accessibility Notes",
            "A11y Fallback",
        ]
    },
    "product": {
        "file": "products.csv",
        "name_cols": ["Product Type"],
        "search_cols": ["Product Type", "Keywords"],
        "output_cols": ["No", "Product Type", "Keywords"]
    },
    "ux": {
        "file": "ux-guidelines.csv",
        "name_cols": ["Issue"],
        "search_cols": ["Category", "Issue", "Description", "Do", "Platform"],
        "output_cols": ["No", "Category", "Issue", "Platform", "Description", "Do", "Don't", "Code Example Good", "Code Example Bad", "Severity"]
    },
    "icons": {
        "file": "icons.csv",
        "name_cols": ["Icon Name"],
        "search_cols": ["Category", "Icon Name", "Keywords", "Best For"],
        "output_cols": ["No", "Category", "Icon Name", "Keywords", "Library", "Import Code", "Usage", "Best For", "Style"]
    },
    "icon-families": {
        "file": "icon-families.csv",
        "name_cols": ["Family"],
        "search_cols": ["Family", "Platforms", "Visual Character", "Best For", "Avoid When", "Keywords"],
        "output_cols": ["Family", "Platforms", "Visual Character", "Best For", "Avoid When", "Grid and Modes", "Package Hint", "License", "Official URL"]
    },
    "icon-concepts": {
        "file": "icon-concepts.csv",
        "name_cols": ["Concept"],
        "search_cols": ["Concept", "Role", "Preferred Mapping", "Candidates to Explore", "Avoid as Default", "Allowed When", "Keywords"],
        "output_cols": ["Concept", "Role", "Preferred Mapping", "Candidates to Explore", "Avoid as Default", "Allowed When", "Label Policy"]
    },
    "icon-candidates": {
        "file": "icon-candidates.csv",
        "name_cols": ["Icon Name", "Concept"],
        "search_cols": ["Concept", "Role", "Family", "Icon Name", "Metaphor", "Use When", "Avoid When", "Keywords"],
        "output_cols": ["Concept", "Role", "Family", "Icon Name", "Package", "Import Hint", "Metaphor", "Use When", "Avoid When", "Verified Version", "Official URL"]
    },
    "react": {
        "file": "react-performance.csv",
        "name_cols": ["Issue"],
        "search_cols": ["Category", "Issue", "Keywords", "Description", "Do"],
        "output_cols": ["No", "Category", "Issue", "Platform", "Description", "Do", "Don't", "Code Example Good", "Code Example Bad", "Severity"]
    },
    # Every app-interface row targets iOS, Android, or React Native apps.
    # ``mobile`` is the accurate name; ``web`` is kept as a compatibility alias
    # for callers of the original domain name.
    "mobile": _MOBILE_APP_INTERFACE,
    "web": _MOBILE_APP_INTERFACE,
    # A slim, dated metadata index: no generated keywords, mood words, or
    # popularity ranks, which acted as an adjective-to-font mapping.
    "google-fonts": {
        "file": "google-fonts.csv",
        "name_cols": ["Family"],
        "search_cols": ["Family", "Category", "Stroke", "Classifications", "Subsets", "Primary Script", "Designers"],
        "output_cols": ["Family", "Category", "Stroke", "Classifications", "Subsets", "Primary Script", "Axes", "Styles", "Designers", "License", "Last Modified", "Google Fonts URL"]
    }
}

# These labels make the epistemic role of bundled snapshots explicit.  The
# catalogs help an agent discover vocabulary, constraints, and analogs; they do
# not classify the current product or select a design on the agent's behalf.
DOMAIN_SOURCE_ROLES = {
    "product": (
        "analogy evidence",
        "Treat matches as unverified analogs: each row is only a product-category label and lexical terms. Use a match to widen questions about the real product; do not inherit product identity, layout, style, palette, or landing recipe.",
    ),
    "google-fonts": (
        "font metadata index (Google Fonts public metadata, snapshot 2026-11-12)",
        "Facts only: family, category, stroke, subsets, primary script, variable-axis ranges, styles, designers, license, and last-modified date. "
        "Category and stroke cannot express construction or mood, so terms such as geometric, humanist, grotesque, elegant, or friendly match nothing here; "
        "judge them from specimens with representative content. "
        "License comes from the google/fonts repository directory at snapshot time. "
        "Confirm current official metadata, the license file, and the actual font files before choosing or loading a family.",
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
        "unsourced visualization-discovery snapshot",
        "Treat returned encodings, limitations, and accessibility notes as prompts only. "
        "Choose from the user's analytical question and representative data; verify semantics, accessibility, performance, edge states, and current library support with the target implementation and primary sources. "
        "Unsupported exact thresholds, palette values, accessibility grades, library recommendations, and interaction prescriptions are intentionally not part of the bundled catalog.",
    ),
    "ux": (
        "general UX guidance",
        "Reconcile with the real journey, current standards, repository behavior, and user evidence.",
    ),
    "mobile": (
        "mobile app-interface guidance (iOS, Android, React Native)",
        "Every row targets native mobile apps or React Native, not web or browser behavior. "
        "Reconcile with current platform guidance (Apple Human Interface Guidelines, Material Design), "
        "the repository's framework version, and its actual semantics and behavior.",
    ),
    "web": (
        "mobile app-interface guidance (legacy domain name)",
        "`web` is a compatibility alias of `mobile`: every row targets iOS, Android, or React Native apps, not web or browser behavior. "
        "Reconcile with current platform guidance (Apple Human Interface Guidelines, Material Design), "
        "the repository's framework version, and its actual semantics and behavior.",
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
}

# Stacks whose bundled catalogs were removed.  A lookup by a retired name
# returns an explicit error that names the replacement instead of silently
# falling back to it.
RETIRED_STACKS = {
    "uwp": {
        "replacement": "winui",
        "reason": (
            "its guidance targeted UWP (Windows.UI.Xaml) and retired device families such as Windows 10 Mobile; "
            "WinUI 3 on the Windows App SDK is Microsoft's current native XAML framework, and the winui catalog "
            "includes rows on migrating UWP code"
        ),
    },
}

# Common columns for all stacks
_STACK_COLS = {
    "name_cols": ["Guideline"],
    "search_cols": ["Category", "Guideline", "Description", "Do", "Don't"],
    "output_cols": ["No", "Category", "Guideline", "Description", "Do", "Don't", "Code Good", "Code Bad", "Severity", "Docs URL"]
}

class _StackChoices(list):
    """Live stack names in configuration order.

    Iteration (help text, listings) yields only live stacks.  Membership also
    admits retired names so an ``argparse`` ``choices`` check lets them through
    to ``search_stack``, which answers with an explicit retirement error naming
    the replacement instead of a generic invalid-choice listing.
    """

    def __contains__(self, name):
        return list.__contains__(self, name) or name in RETIRED_STACKS


AVAILABLE_STACKS = _StackChoices(STACK_CONFIG)
STACK_SOURCE_ROLE = "caller-selected bundled stack implementation-guidance snapshot"
STACK_WARNING = (
    "Treat results as advisory prompts, not current platform or API truth. "
    "Verify material and version-sensitive claims against the target repository and current primary documentation. "
    "A returned Docs URL is a discovery pointer, not proof of source primacy or freshness."
)


# ============ LEXICAL NORMALIZATION ============
# Query and rows pass through the same normalization: case folding, apostrophe
# removal, hyphen compounds indexed both split and joined (``re-render`` also
# yields ``rerender``), a small English stopword list, and light suffix
# stemming.  This is deterministic lexical normalization, not a synonym table,
# query expansion, or classifier; non-English text passes through unstemmed.
STOPWORDS = frozenset(
    """a an and are as at be by can do does for from has have how i in into is it its me my of on or our
    should so than that the their them then there these this those to us vs versus via was we what when
    where which while who why will with without you your""".split()
)

_APOSTROPHE = re.compile(r"(?<=\w)['\u2019](?=\w)")
_WORD = re.compile(r"[^\W_]+(?:-[^\W_]+)*")
_NO_DOUBLE_DROP = set("lsz")


def stem(token):
    """Strip common English inflections so plural and verb forms meet."""
    if len(token) <= 3 or not token.isascii():
        return token
    if token.endswith("ies") and len(token) > 4:
        token = token[:-3] + "y"
    elif token.endswith(("sses", "shes", "ches", "xes", "zes")):
        token = token[:-2]
    elif token.endswith("s") and not token.endswith(("ss", "us", "is")):
        token = token[:-1]
    for suffix in ("ing", "ed"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 4:
            token = token[: -len(suffix)]
            if len(token) >= 4 and token[-1] == token[-2] and token[-1] not in _NO_DOUBLE_DROP:
                token = token[:-1]
            break
    if token.endswith("e") and len(token) > 4:
        token = token[:-1]
    return token


def tokenize(text):
    """Return normalized index terms for ``text`` in reading order."""
    text = _APOSTROPHE.sub("", str(text).casefold())
    terms = []
    for word in _WORD.findall(text):
        parts = word.split("-")
        forms = parts if len(parts) == 1 else [part for part in parts if len(part) >= 3] + ["".join(parts)]
        for form in forms:
            if len(form) >= 2 and form not in STOPWORDS:
                terms.append(stem(form))
    return terms


def _field_weight(column, name_cols):
    if column in name_cols:
        return 3
    if column in ("Keywords", "Category"):
        return 2
    return 1


def _contains_run(haystack, needle):
    width = len(needle)
    return 0 < width <= len(haystack) and any(
        haystack[index:index + width] == needle for index in range(len(haystack) - width + 1)
    )


def _name_tier(query_terms, row, name_cols):
    """Rank tier from row names: 3 exact, 2 name starts with the query, 1 overlap run, 0 none.

    A name such as ``Sports Team/Club`` is matched per ``/``-separated part.
    """
    best = 0
    for column in name_cols:
        for part in re.split(r"\s*/\s*", str(row.get(column, ""))):
            name_terms = tokenize(part)
            if not name_terms:
                continue
            if name_terms == query_terms:
                return 3
            if name_terms[: len(query_terms)] == query_terms:
                best = max(best, 2)
            elif _contains_run(name_terms, query_terms) or _contains_run(query_terms, name_terms):
                best = max(best, 1)
    return best


# ============ BM25 IMPLEMENTATION ============
class BM25:
    """BM25 ranking over pre-tokenized documents."""

    def __init__(self, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.corpus = []
        self.term_freqs = []
        self.doc_lengths = []
        self.avgdl = 0
        self.idf = {}
        self.N = 0

    def tokenize(self, text):
        return tokenize(text)

    def fit(self, documents):
        """Index documents given as strings or as lists of normalized terms."""
        self.corpus = [doc if isinstance(doc, list) else tokenize(doc) for doc in documents]
        self.N = len(self.corpus)
        if self.N == 0:
            return
        self.term_freqs = [Counter(doc) for doc in self.corpus]
        self.doc_lengths = [len(doc) for doc in self.corpus]
        self.avgdl = (sum(self.doc_lengths) / self.N) or 1
        doc_freqs = Counter()
        for freqs in self.term_freqs:
            doc_freqs.update(freqs.keys())
        self.idf = {term: log((self.N - freq + 0.5) / (freq + 0.5) + 1) for term, freq in doc_freqs.items()}

    def score_terms(self, query_terms):
        """Return ``(index, score, matched distinct terms)`` for every document."""
        terms = [term for term in dict.fromkeys(query_terms) if term in self.idf]
        scored = []
        for index, freqs in enumerate(self.term_freqs):
            score = 0.0
            matched = 0
            length_norm = 1 - self.b + self.b * self.doc_lengths[index] / self.avgdl
            for term in terms:
                tf = freqs.get(term, 0)
                if tf:
                    matched += 1
                    score += self.idf[term] * tf * (self.k1 + 1) / (tf + self.k1 * length_norm)
            scored.append((index, score, matched))
        return scored

    def score(self, query):
        """Score all documents against a query string, best first."""
        ranked = [(index, score) for index, score, _ in self.score_terms(tokenize(query))]
        return sorted(ranked, key=lambda item: item[1], reverse=True)


# ============ SEARCH FUNCTIONS ============
def _load_csv(filepath):
    """Load CSV and return list of dicts"""
    with open(filepath, 'r', encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def _unmatched_terms(query, vocabulary):
    """Query words whose normalized form occurs nowhere in the searched columns."""
    missing = []
    for word in _WORD.findall(_APOSTROPHE.sub("", str(query).casefold())):
        terms = tokenize(word)
        if terms and not any(term in vocabulary for term in terms) and word not in missing:
            missing.append(word)
    return missing


def _search_csv(filepath, search_cols, output_cols, query, max_results, row_filter=None, name_cols=(), diagnostics=None):
    """Rank rows lexically and return output-column dictionaries.

    Ranking: weighted-field BM25 (name columns x3, Keywords/Category x2,
    others x1), multiplied by the share of distinct query terms a row
    matches.  Rows whose names equal, start with, or overlap the query rank
    ahead of others in that order.  When some row matches several query
    terms, rows matching fewer than half as many distinct terms are dropped
    as incidental.  Rows that match nothing are never returned.
    """
    validate_max_results(max_results)
    if not filepath.exists():
        return []

    data = _load_csv(filepath)
    if row_filter is not None:
        data = [row for row in data if row_filter(row)]

    documents = []
    for row in data:
        terms = []
        for column in search_cols:
            terms.extend(tokenize(row.get(column, "")) * _field_weight(column, name_cols))
        documents.append(terms)

    bm25 = BM25()
    bm25.fit(documents)
    query_terms = tokenize(query)
    present = [term for term in dict.fromkeys(query_terms) if term in bm25.idf]
    if diagnostics is not None:
        diagnostics["unmatched_terms"] = _unmatched_terms(query, bm25.idf)
    if not present:
        return []

    candidates = [(index, score, matched) for index, score, matched in bm25.score_terms(query_terms) if score > 0]
    if not candidates:
        return []
    best_matched = max(matched for _, _, matched in candidates)
    ranked = []
    for index, score, matched in candidates:
        if matched * 2 < best_matched:
            continue
        tier = _name_tier(query_terms, data[index], name_cols) if name_cols else 0
        ranked.append((-tier, -(score * matched / len(present)), index))
    ranked.sort()

    results = []
    for _, _, index in ranked[:max_results]:
        row = data[index]
        results.append({col: row.get(col, "") for col in output_cols if col in row})
    return results


def _with_unmatched_terms(result, unmatched):
    result["unmatched_terms"] = unmatched
    if unmatched:
        result["warning"] += (
            " These query terms match no searched column in this catalog and did not affect ranking: "
            + ", ".join(unmatched)
            + "."
        )
    return result


def search(query, domain=None, max_results=MAX_RESULTS):
    """Search one caller-selected evidence domain without semantic inference."""
    validate_max_results(max_results)
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
    diagnostics = {}
    results = _search_csv(
        filepath,
        config["search_cols"],
        config["output_cols"],
        retrieval_query,
        retrieval_limit,
        row_filter=row_filter,
        name_cols=config.get("name_cols", ()),
        diagnostics=diagnostics,
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
    return _with_unmatched_terms({
        "domain": domain,
        "query": query,
        "file": config["file"],
        "source_role": source_role,
        "warning": source_warning,
        "count": len(results),
        "results": results
    }, diagnostics.get("unmatched_terms", []))


def search_stack(query, stack, max_results=MAX_RESULTS):
    """Search stack-specific guidelines"""
    validate_max_results(max_results)
    if stack in RETIRED_STACKS:
        retired = RETIRED_STACKS[stack]
        replacement = retired["replacement"]
        return {
            "error": (
                f"The {stack} stack catalog was retired: {retired['reason']}. "
                f"Use --stack {replacement} instead."
            ),
            "stack": stack,
            "replacement": replacement,
        }
    if stack not in STACK_CONFIG:
        return {"error": f"Unknown stack: {stack}. Available: {', '.join(AVAILABLE_STACKS)}"}

    filepath = DATA_DIR / STACK_CONFIG[stack]["file"]

    if not filepath.exists():
        return {"error": f"Stack file not found: {filepath}", "stack": stack}

    diagnostics = {}
    results = _search_csv(
        filepath,
        _STACK_COLS["search_cols"],
        _STACK_COLS["output_cols"],
        query,
        max_results,
        name_cols=_STACK_COLS["name_cols"],
        diagnostics=diagnostics,
    )
    docs_urls_present = sum(bool(str(row.get("Docs URL", "")).strip()) for row in results)
    docs_urls_missing = len(results) - docs_urls_present
    warning = STACK_WARNING
    if docs_urls_missing:
        warning += (
            f" {docs_urls_missing} of {len(results)} returned row(s) have no Docs URL and remain unsourced "
            "bundled guidance until independently verified."
        )

    return _with_unmatched_terms({
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
    }, diagnostics.get("unmatched_terms", []))
