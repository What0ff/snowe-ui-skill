#!/usr/bin/env python3
"""Schema 3 unresolved-first decision support for Snowe UI Skill.

The runtime preserves the brief verbatim. It does not detect its language,
classify vocabulary, infer work mode, platform, facts, or pressures, or query
product analogs unless the caller explicitly supplies ``analog_query``. Only
``declared_context`` can populate semantic situation fields. The packet adds a
generic inquiry and proof workbench; the agent derives project pressures from
verified evidence and performs the actual design synthesis.
"""

from __future__ import annotations

import json
import math
import os
import re
import stat
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from core import search


SCHEMA_VERSION = "3.0"
PROJECT_MANIFEST_FILENAME = "PROJECT.json"
PROJECT_MANIFEST_VERSION = "1"
PROJECT_MANIFEST_MAX_BYTES = 1_000_000
PROJECT_MANIFEST_MAX_DEPTH = 128
DEFAULT_PROJECT_NAME = "Untitled design inquiry"


class ProjectManifestCorrupt(ValueError):
    """An interrupted manifest has no complete identity claim."""


def _absolute_lexical_path(path: str | Path) -> Path:
    return Path(os.path.abspath(os.fspath(Path(path).expanduser())))


def _is_reparse_path(path: Path) -> bool:
    """Detect symlinks and Windows junction/reparse points without following them."""
    try:
        information = os.lstat(path)
    except FileNotFoundError:
        return False
    attributes = getattr(information, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return stat.S_ISLNK(information.st_mode) or bool(attributes & reparse_flag)


def _reject_reparse_chain(path: Path, label: str) -> None:
    current = _absolute_lexical_path(path)
    while True:
        if _is_reparse_path(current):
            raise ValueError(f"{label} must not contain a symlink, junction, or reparse point: {current}")
        parent = current.parent
        if parent == current:
            return
        current = parent


def _windows_long_path_name(path: Path, label: str) -> Path:
    """Expand Windows short names without resolving a reparse target."""
    import ctypes
    from ctypes import wintypes

    get_long_path_name = ctypes.WinDLL("kernel32", use_last_error=True).GetLongPathNameW
    get_long_path_name.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
    get_long_path_name.restype = wintypes.DWORD
    requested = os.fspath(path)
    size = int(get_long_path_name(requested, None, 0))
    if size == 0:
        error = ctypes.get_last_error()
        raise ValueError(f"{label} aliases cannot be inspected safely: {path} (Windows error {error})")
    for _ in range(2):
        buffer = ctypes.create_unicode_buffer(size)
        written = int(get_long_path_name(requested, buffer, size))
        if written == 0:
            error = ctypes.get_last_error()
            raise ValueError(f"{label} aliases cannot be inspected safely: {path} (Windows error {error})")
        if written < size:
            return Path(buffer.value)
        size = written
    raise ValueError(f"{label} aliases changed while they were being inspected: {path}")


def _normalize_lexical_aliases(path: Path, label: str) -> Path:
    """Normalize lexical aliases while preserving every reparse component."""
    absolute = _absolute_lexical_path(path)
    if os.name != "nt":
        return absolute

    existing = absolute
    suffix: list[str] = []
    while True:
        try:
            os.lstat(existing)
            break
        except FileNotFoundError:
            parent = existing.parent
            if parent == existing:
                raise ValueError(f"{label} has no inspectable existing ancestor: {path}")
            suffix.append(existing.name)
            existing = parent
        except OSError as error:
            raise ValueError(f"{label} aliases cannot be inspected safely: {existing}") from error

    normalized = _windows_long_path_name(existing, label)
    return normalized.joinpath(*reversed(suffix))


def _stat_identity(information: os.stat_result) -> tuple[int, int] | None:
    try:
        device = int(information.st_dev)
        inode = int(information.st_ino)
    except (AttributeError, TypeError, ValueError):
        return None
    return None if inode == 0 else (device, inode)


def _shared_regular_file(path: Path) -> bool:
    try:
        information = os.lstat(path)
    except FileNotFoundError:
        return False
    return stat.S_ISREG(information.st_mode) and int(getattr(information, "st_nlink", 1)) > 1


def _project_manifest_tree_error(value: Any) -> str | None:
    """Return a deterministic safety error for decoded manifest values."""
    pending: list[tuple[Any, int]] = [(value, 0)]
    while pending:
        current, depth = pending.pop()
        if depth > PROJECT_MANIFEST_MAX_DEPTH:
            return (
                "Project identity manifest exceeds the deterministic "
                f"{PROJECT_MANIFEST_MAX_DEPTH}-level JSON nesting limit"
            )
        if isinstance(current, str):
            if any(0xD800 <= ord(character) <= 0xDFFF for character in current):
                return "Project identity manifest contains unpaired Unicode surrogate code points"
        elif isinstance(current, float) and not math.isfinite(current):
            return "Project identity manifest contains a non-finite JSON number"
        elif isinstance(current, dict):
            for key, child in current.items():
                if any(0xD800 <= ord(character) <= 0xDFFF for character in key):
                    return "Project identity manifest contains unpaired Unicode surrogate code points"
                pending.append((child, depth + 1))
        elif isinstance(current, list):
            pending.extend((child, depth + 1) for child in current)
    return None


@contextmanager
def _persistence_lock(root: Path, project_slug: str):
    """Serialize all state changes for one persisted project identity."""
    storage_root = root / "design-intelligence"
    storage_root.mkdir(parents=True, exist_ok=True)
    _reject_reparse_chain(storage_root, "Persistence state path")
    lock_path = storage_root / f".{project_slug}.persist.lock"
    if _is_reparse_path(lock_path):
        raise ValueError(f"Persistence lock must not be a symlink, junction, or reparse point: {lock_path}")
    flags = os.O_CREAT | os.O_RDWR
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    existing_identity = None
    try:
        existing_information = os.lstat(lock_path)
    except FileNotFoundError:
        existing_information = None
    if existing_information is not None:
        if _is_reparse_path(lock_path):
            raise ValueError(f"Persistence lock must not be a symlink, junction, or reparse point: {lock_path}")
        if not stat.S_ISREG(existing_information.st_mode):
            raise ValueError(f"Persistence lock must be a regular file: {lock_path}")
        if int(getattr(existing_information, "st_nlink", 1)) > 1:
            raise ValueError(f"Persistence lock must not be a shared hardlink: {lock_path}")
        existing_identity = _stat_identity(existing_information)
    descriptor = os.open(lock_path, flags, 0o600)
    handle = os.fdopen(descriptor, "r+b", buffering=0)
    locked = False
    try:
        opened_information = os.fstat(handle.fileno())
        if _is_reparse_path(lock_path):
            raise ValueError(f"Persistence lock must not be a symlink, junction, or reparse point: {lock_path}")
        if not stat.S_ISREG(opened_information.st_mode):
            raise ValueError(f"Persistence lock must be a regular file: {lock_path}")
        if int(getattr(opened_information, "st_nlink", 1)) > 1:
            raise ValueError(f"Persistence lock must not be a shared hardlink: {lock_path}")
        if existing_identity is not None and _stat_identity(opened_information) != existing_identity:
            raise ValueError(f"Persistence lock changed identity before it could be opened safely: {lock_path}")
        if os.name == "nt":
            import msvcrt

            if os.fstat(handle.fileno()).st_size == 0:
                handle.write(b"\0")
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            except OSError as error:
                raise RuntimeError(f"Another persistence operation is active for {project_slug!r}") from error
        else:
            import fcntl

            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            except OSError as error:
                raise RuntimeError(f"Another persistence operation is active for {project_slug!r}") from error
        locked = True
        yield
    finally:
        if locked:
            if os.name == "nt":
                import msvcrt

                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def _write_complete_temp(path: Path, content: str) -> Path:
    _reject_reparse_chain(path.parent, "Persisted output path")
    temporary = path.with_name(f".{path.name}.tmp-{uuid.uuid4().hex}")
    created = False
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as handle:
            created = True
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        return temporary
    except BaseException:
        if created:
            try:
                # unlink() removes the temporary directory entry itself and
                # does not follow a path that was replaced with a symlink.
                temporary.unlink()
            except FileNotFoundError:
                pass
            except OSError as cleanup_error:
                raise OSError(
                    f"Temporary persistence output could not be cleaned safely: {temporary}"
                ) from cleanup_error
        raise


def _atomic_write_text(path: Path, content: str) -> None:
    """Replace a generated inquiry without following a target hardlink."""
    _reject_reparse_chain(path, "Persisted output path")
    temporary = _write_complete_temp(path, content)
    try:
        _reject_reparse_chain(path, "Persisted output path")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _atomic_create_text(path: Path, content: str) -> bool:
    """Publish complete bytes only when the identity/ledger path is absent."""
    _reject_reparse_chain(path, "Persisted output path")
    temporary = _write_complete_temp(path, content)
    try:
        _reject_reparse_chain(path, "Persisted output path")
        try:
            os.link(temporary, path, follow_symlinks=False)
        except FileExistsError:
            return False
        return True
    finally:
        if temporary.exists():
            temporary.unlink()


def _as_string_list(value: Any, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise TypeError(f"declared_context.{field} must be a list of strings")
    items = [str(item).strip() for item in value if str(item).strip()]
    return items


def _normalize_declared_context(value: dict[str, Any] | None) -> dict[str, Any]:
    """Pass through explicit caller declarations without interpreting the brief."""
    context = dict(value or {})
    work_mode = str(context.pop("work_mode", "")).strip()
    platforms = _as_string_list(context.pop("platforms", None), "platforms")
    facts = _as_string_list(context.pop("facts", None), "facts")
    pressures = _as_string_list(context.pop("pressures", None), "pressures")
    other = {str(key): child for key, child in context.items()}
    declared = bool(work_mode or platforms or facts or pressures or other)
    return {
        "status": "CALLER_DECLARED" if declared else "NOT_PROVIDED",
        "work_mode": work_mode or "UNRESOLVED — determine from the requested change and verified repository state",
        "platforms": platforms or ["UNRESOLVED — verify target surfaces, environments, and input modes"],
        "facts": facts,
        "pressures": pressures,
        "other": other,
        "provenance": "Values in this block come only from the caller; the runtime never derives them from brief vocabulary.",
    }


def _pressure_inquiry() -> list[dict[str, str]]:
    return [
        {
            "dimension": "user outcome and context",
            "question": "What outcome is each primary actor trying to reach, in what situation, frequency, environment, and level of consequence?",
        },
        {
            "dimension": "business or organizational outcome",
            "question": "Which outcome, transaction, adoption, efficiency, trust, learning, or relationship matters—and what evidence would show progress without harming the user outcome?",
        },
        {
            "dimension": "objects, content, and state",
            "question": "Which real objects, attributes, relationships, content types, lifecycle states, exceptions, and provenance shape the experience?",
        },
        {
            "dimension": "journey and decision structure",
            "question": "Which decisions, dependencies, entry points, return visits, recovery paths, assisted routes, and cross-channel steps determine the architecture?",
        },
        {
            "dimension": "risk and exclusion",
            "question": "Which errors, ambiguity, language needs, access barriers, performance limits, or policy constraints could cause material harm or failure?",
        },
        {
            "dimension": "identity and perception",
            "question": "Which verified product, brand, audience, place, material, content, or behavioral truths should the experience make perceptible?",
        },
    ]


def _research_plan() -> dict[str, Any]:
    return {
        "posture": "targeted, decision-led research; never a mandatory moodboard",
        "triggers": [
            {
                "activate_when": "Current standards, law, policy, safety, accessibility, localization, or platform behavior could change a material constraint.",
                "question": "What current primary guidance or verified policy governs the unresolved decision?",
                "sources": "Official standards, regulator or organizational policy, primary platform documentation, and current accessibility guidance",
                "stop": "The constraint is verified, safely bounded, or explicitly left UNKNOWN with a recovery path.",
            },
            {
                "activate_when": "Real products, category behavior, culture, or audience expectations could reveal a material alternative or risk.",
                "question": "Which current examples widen the architecture, content, interaction, or identity space without becoming a template?",
                "sources": "Real current products, first-party product material, credible domain research, and direct observation",
                "stop": "New examples repeat known approaches and no longer change a candidate or risk.",
            },
            {
                "activate_when": "A font, icon family, package, browser technique, image generator, or other dependency is a live candidate.",
                "question": "Which current official asset, capability, license, version, and integration constraints affect the choice?",
                "sources": "Official documentation, authoritative registries, licenses, release notes, and real target-platform renders",
                "stop": "Viable candidates and their constraints are verified; speculative dependencies are not installed.",
            },
        ],
        "activation_rule": "The agent activates only checks that can change a material decision. Brief vocabulary never activates research automatically.",
        "synthesis_rule": "Extract transferable principles, tensions, and counterexamples. Do not copy a competitor's composition, brand codes, imagery, or interaction signature.",
        "evidence_record": "decision | source | observed fact | implication | confidence | freshness | candidate changed?",
    }


def _local_analogs(analog_query: str | None) -> dict[str, Any]:
    query = str(analog_query or "").strip()
    if not query:
        return {
            "status": "NOT_REQUESTED",
            "query": None,
            "product_analogs": [],
        }

    result = search(query, "product", 3)
    analogs = [
        {
            "status": "UNVERIFIED_ANALOG",
            "label": item.get("Product Type", "Unlabelled analog"),
            "catalog_terms": item.get("Keywords", ""),
            "warning": "The caller chose this lexical query. BM25 rank is not semantic confidence; use the row only to widen questions or alternatives.",
        }
        for item in result.get("results", [])
    ]
    return {
        "status": "REQUESTED_BY_CALLER",
        "query": query,
        "product_analogs": analogs,
    }


def _unknowns() -> list[str]:
    return [
        "What in the brief is verified fact, what is a stakeholder claim, what is an assumption, and what evidence is missing?",
        "What would make the current framing wrong, incomplete, or too narrow?",
        "Which important pressure may be absent from every bundled vocabulary or familiar product category?",
        "Which parts of the problem require domain, language, cultural, legal, or operational expertise the runtime does not possess?",
    ]


def _identity_sources() -> list[str]:
    return [
        "The product's real objects, construction, workflow, state transitions, or information relationships",
        "Audience language, culture, habits, access needs, and context of use",
        "Verified brand history, voice, assets, materials, place, and behavior",
        "The form, authorship, provenance, and quality of real content—not placeholder volume or trend labels",
        "Physical, service, operational, editorial, commercial, or community realities discovered in the project",
    ]


class DecisionPacketGenerator:
    """Wrap a verbatim brief and caller declarations in an open inquiry."""

    def generate(
        self,
        brief: str,
        project_name: str | None = None,
        *,
        declared_context: dict[str, Any] | None = None,
        analog_query: str | None = None,
    ) -> dict[str, Any]:
        context = _normalize_declared_context(declared_context)
        pressure_status = (
            "CALLER_DECLARED — verify provenance and causal relevance"
            if context["pressures"]
            else "UNRESOLVED — derive from verified project evidence; do not classify from brief keywords"
        )
        evidence = _local_analogs(analog_query)

        return {
            "schema_version": SCHEMA_VERSION,
            "project_name": project_name or DEFAULT_PROJECT_NAME,
            "brief": brief,
            "situation": {
                "framing_status": "UNRESOLVED" if context["status"] == "NOT_PROVIDED" else "PARTIALLY_DECLARED",
                "mode": context["work_mode"],
                "platforms": context["platforms"],
                "declared_facts": context["facts"],
                "other_declared_context": context["other"],
                "declaration_provenance": context["provenance"],
                "pressure_status": pressure_status,
                "design_pressures": context["pressures"],
                "pressure_inquiry": _pressure_inquiry(),
                "extension_rule": "Add any evidence-backed pressure the project reveals, even when it has no name or precedent in Snowe's local vocabulary.",
                "unknowns": _unknowns(),
                "language_policy": "The runtime preserves the brief verbatim and does not detect language, translate, classify intent, or privilege English vocabulary.",
                "ambiguity_policy": "Ambiguous terms such as service, platform, audit, history, store, and application remain unresolved until surrounding evidence establishes their role.",
                "fact_policy": "The original brief and verified repository or external evidence are facts. Retrieved analogs, inferred audiences, market assumptions, and generated directions remain hypotheses until verified.",
            },
            "decision_graph": {
                "purpose": "Keep freedom causal: every material move traces back to a real driver and forward to an observable consequence.",
                "record": "driver → design move → expected user/business consequence → evidence → risk → revisit trigger",
                "layers": [
                    "Outcomes and constraints",
                    "Whole journey, actors, objects, content, decisions, and states",
                    "Site/service topology, navigation, page jobs, and conversion paths",
                    "Art direction, type, color/material, imagery, graphics, and motion language",
                    "Components, interactions, responsive transformations, and implementation",
                    "Rendered evidence, behavioral evidence, learning, and accepted decisions",
                ],
                "rule": "A downstream choice may be novel or absent from every local catalog. Keep it when its causal chain is stronger than the alternatives and it survives real-content and rendered tests.",
            },
            "research": _research_plan(),
            "architecture": {
                "status": "OPEN — synthesize after the whole journey and content model are understood",
                "inputs": [
                    "Actors, contexts, frequency, stakes, and input modes",
                    "User jobs, decision moments, dependencies, failure/recovery, and re-entry",
                    "Business model, conversion, trust obligations, and success evidence",
                    "Content and product objects, attributes, relationships, quantities, lifecycle, and ownership",
                    "Entry points, search/discovery behavior, navigation depth, and cross-channel steps",
                ],
                "synthesis": [
                    "Map the whole journey and object/content relationships before naming pages or sections.",
                    "Define the site or product boundary around outcomes; do not mirror the organization, database, or a familiar template.",
                    "Generate enough structurally different candidates to cover the live trade-offs. Change the organizing principle, sequence, navigation, disclosure, or conversion model—not only visual styling.",
                    "Include a synthesized candidate when the strongest answer is not represented by retrieved patterns. Local data is evidence and analogy, never the candidate boundary.",
                    "Prototype the riskiest page slice or journey transition with real content before selecting the complete architecture.",
                ],
                "candidate_record": {
                    "thesis": "How this architecture organizes the user's world",
                    "site_scope": "What belongs, what does not, and how cross-channel steps join up",
                    "topology": "Destinations or product areas and the relationships that justify them",
                    "navigation": "How users orient, move, search, compare, return, and recover",
                    "page_jobs": "For every key page: what the user should understand, decide, or do",
                    "content_sequence": "Questions and dependencies that determine order; no hero or section type is mandatory",
                    "conversion_path": "Where intent becomes ready and what proof precedes the action",
                    "responsive_transformation": "What stays invariant and what reorders, collapses, changes control, or changes medium",
                    "risk": "The assumption most likely to invalidate this candidate",
                },
                "selection_rule": "Select by causal fit, clarity, content resilience, identity potential, accessibility, and feasibility. Hybridize only compatible moves that form one coherent organizing logic.",
            },
            "art_direction": {
                "status": "OPEN — architecture and real content constrain the visual language before styling begins",
                "identity_sources": _identity_sources(),
                "direction_method": [
                    "Frame directions as perceptual and behavioral theses, not style labels or mood adjectives.",
                    "Make finalists differ in composition, typographic voice, image/graphic logic, material behavior, or interaction character where those differences express a real product trade-off.",
                    "Choose one primary identity carrier and define its repetition boundary. The carrier may be architecture, type, content behavior, imagery, graphics, data, or motion; decoration is optional.",
                    "Use typography, color, shape, and material as a coherent system derived from content, scripts, platform, and desired perception. A dataset pairing or palette is only a candidate.",
                ],
                "direction_record": "thesis | perception | product-specific source | dominant composition | type voice | color/material logic | imagery/graphic logic | interaction/motion character | signature boundary | strongest risk",
            },
            "assets": {
                "visual_need_decision": {
                    "status": "OPEN",
                    "question": "What must a visual explain, prove, orient, reveal, or make desirable that type, layout, real product UI, or no image cannot do better?",
                    "eligible_outcomes": [
                        "No image",
                        "Verified existing or brand asset",
                        "Product photography or commissioned photography",
                        "Illustration",
                        "Diagram or data-led graphic",
                        "3D/product composition",
                        "Generated artwork or photography",
                        "Repository-owned custom graphic",
                    ],
                    "selection_rule": "Choose by communicative job, truthfulness, provenance, art-direction fit, responsive crop, performance, and maintenance—not by novelty or tool availability.",
                },
                "image_generation": {
                    "use_when": "Generation can produce a needed, truthful, ownable composition that is unavailable from real product, brand, licensed, commissioned, or diagrammatic sources inside scope.",
                    "brief": "page role | communicative job | exact aspect/crop | subject and action | camera/perspective | subject placement and negative space | light/material/palette | continuity with type and surfaces | required truth | prohibited artifacts/cliches | responsive variants",
                    "loop": [
                        "Generate a small set of meaningfully different compositions, not prompt paraphrases.",
                        "Place finalists in the actual layout at target crops and widths before judging them.",
                        "Inspect anatomy, product truth, text-like artifacts, edge quality, focal competition, crop resilience, loading cost, and provenance disclosure.",
                        "Regenerate, edit, or reject the asset when the real layout is weaker than the no-image or non-generated alternative.",
                    ],
                },
                "custom_graphics": {
                    "family_spec": "role | grid/viewBox | live area/keylines | stroke or fill model | caps/joins/corners | curvature | optical overshoot | counter/negative-space minimum | detail budget by size | color modes | source/provenance",
                    "workflow": [
                        "Decide whether visible text, an existing symbol, a compatible external family, or a custom graphic gives the clearest and most ownable result.",
                        "For open product-specific icon decisions, develop a feasible custom candidate before settling for an approximate library match; preserve accepted conventional actions and quality over frequency.",
                        "Derive a semantic brief from actual feature behavior, label, state, nearest sibling meanings and the smallest real slot; do not imply an unverified capability or outcome.",
                        "Sketch materially different silhouettes and compound constructions before polishing paths.",
                        "Draw to the family specification; use optical compensation rather than mechanically identical bounds.",
                        "Run structural SVG/provenance validation, then render at 16, 20, and 24px and at every actual interface size beside neighboring icons.",
                        "Test default, selected, disabled, dark, high-contrast, and labelled contexts where applicable.",
                        "Inspect native-size glyph recognition, optical family fit, host scaling and painted backings separately; bind current asset/context evidence and keep missing proof UNKNOWN.",
                    ],
                    "reject_when": "Reject or redraw when recognition depends on explanation, counters close, stroke/area feels heavier than neighbors, the metaphor conflicts with the action, the silhouette collapses, or an existing asset is visibly stronger.",
                },
            },
            "motion": {
                "status": "OPEN — the static and reduced-motion experience is the baseline",
                "decision_question": "Does motion clarify cause, continuity, hierarchy, spatial relationship, progress, feedback, or story—and is that benefit worth its repetition and runtime cost?",
                "eligible_outcomes": [
                    "No animation",
                    "State feedback only",
                    "Continuity or explanatory motion",
                    "Expressive motion with an earned narrative or identity role",
                ],
                "record": "trigger/state change | information motion carries | affected hierarchy | frequency | choreography | interruption | performance budget | reduced/static equivalent | reject condition",
                "rules": [
                    "Use immediate restrained feedback for frequent controls; reserve expressive choreography for low-frequency moments whose narrative or spatial role earns it.",
                    "Motion must be interruptible and must not delay task completion, hide required state, or create a gesture-only path.",
                    "Test repeated use and `prefers-reduced-motion`; reduction may preserve a short opacity/state transition when removing all feedback would weaken comprehension.",
                    "Choose no animation when the static state change is clearer, faster, calmer, or more accessible.",
                ],
            },
            "responsive": {
                "principle": "Design transformations, not three screenshots. Preserve outcome, priority, reading order, state, and conversion while changing composition and controls when space or input mode changes.",
                "contract": "invariants | reorder/collapse rules | navigation transition | content disclosure | media crop/substitution | comparison behavior | sticky/fixed behavior | pointer/touch/keyboard differences | long-content and localization stress",
                "proof": "Render narrow, at least one pressure width between planned breakpoints, and wide; include zoom/text scaling, long real content, focus, open overlays, selected/disabled/error states, and reduced motion.",
            },
            "evaluation": {
                "verdicts": "KEEP | REVISE | REJECT | UNKNOWN",
                "criteria": [
                    "Causal fit: important moves trace to real user, business, content, brand, or platform drivers.",
                    "Structural range: candidates change organizing logic where the brief contains a real trade-off; cosmetic variants do not count.",
                    "Synthesis: the chosen answer may exceed every local recipe and does not inherit an analog's identity by accident.",
                    "Coherence: architecture, visual language, assets, interactions, and motion reinforce one thesis without uniformity for its own sake.",
                    "Discretion: imagery, generation, custom graphics, and animation appear only when they outperform simpler alternatives.",
                    "UX resilience: task clarity, accessibility, localization, content variation, performance, and responsive behavior survive the direction.",
                    "Rendered proof: visible hierarchy and interaction quality are evaluated in the real product, not certified by policy prose or code tokens.",
                    "Visual acceptance: distinguish controls, semantic tokens, and passive content; compare disputed wrappers/effects against a credible same-content subtraction render. Preserve justified brand/native forms rather than banning shapes.",
                    "Specified-reference conformance: when the user provides a definite target, compare implementation against that target, including control dimensions and corner shape. Do not reopen supplied visual decisions or silently redesign; isolate unspecified states and unresolved deviations.",
                ],
                "finding_record": "verdict | viewport/state | visible or behavioral evidence | consequence | correction or acceptance reason | rerender/retest",
                "stop": "Resolve every REJECT and material REVISE finding and inspect the current rerender before visual acceptance. Build success cannot override a blocking visual finding. Stop when further change no longer improves a stated driver; if required evidence cannot be obtained, finish verifiable work with those claims UNKNOWN and no visual acceptance claim.",
            },
            "local_evidence": {
                "status": evidence["status"],
                "role": "caller-requested lexical analogs only—never classification, pressure inference, direction, or architecture",
                "query": evidence["query"],
                "product_analogs": evidence["product_analogs"],
                "absence_rule": "NOT_REQUESTED, no match, or removal of the local dataset changes no framing or design obligation.",
                "limitations": "Bundled catalogs are optional English-oriented snapshots. They may widen vocabulary after the question is known; they cannot establish current truth or bound synthesis.",
            },
        }


def _append_list(lines: list[str], items: Iterable[Any]) -> None:
    for item in items:
        lines.append(f"- {item}")


def format_packet_markdown(packet: dict[str, Any]) -> str:
    """Format a decision packet as a compact working document."""
    situation = packet["situation"]
    lines = [
        "# Snowe Design Decision Packet",
        "",
        f"**Project:** {packet['project_name']}",
        f"**Schema:** {packet['schema_version']}",
        f"**Brief:** {packet['brief']}",
        "",
        "> This packet opens decisions; it does not select a layout, style, palette, font, image, icon family, or motion recipe.",
        "",
        "## Design situation",
        "",
        f"- **Framing:** {situation['framing_status']}",
        f"- **Mode:** {situation['mode']}",
        f"- **Platforms:** {', '.join(situation['platforms'])}",
        f"- **Pressure status:** {situation['pressure_status']}",
        f"- **Language policy:** {situation['language_policy']}",
        f"- **Ambiguity policy:** {situation['ambiguity_policy']}",
        f"- **Fact policy:** {situation['fact_policy']}",
        "",
        "### Caller-declared facts",
        "",
    ]
    _append_list(lines, situation["declared_facts"] or ["UNKNOWN — no structured facts were supplied"])
    lines.extend(
        (
            "",
        "### Design pressures",
        "",
        )
    )
    _append_list(lines, situation["design_pressures"] or ["UNRESOLVED — establish from evidence before architecture"])
    lines.extend(("", "### Pressure inquiry", ""))
    for item in situation["pressure_inquiry"]:
        lines.append(f"- **{item['dimension'].title()}:** {item['question']}")
    lines.append(f"- **Extension rule:** {situation['extension_rule']}")
    lines.extend(("", "### Resolve before architecture", ""))
    _append_list(lines, situation["unknowns"])

    graph = packet["decision_graph"]
    lines.extend(
        (
            "",
            "## Decision graph",
            "",
            f"- **Purpose:** {graph['purpose']}",
            f"- **Record:** `{graph['record']}`",
            f"- **Freedom rule:** {graph['rule']}",
            "",
        )
    )
    _append_list(lines, graph["layers"])

    research = packet["research"]
    lines.extend(("", "## External research", "", f"- **Posture:** {research['posture']}", f"- **Activation:** {research['activation_rule']}", f"- **Synthesis:** {research['synthesis_rule']}", ""))
    for trigger in research["triggers"]:
        lines.append(f"- **Activate when:** {trigger['activate_when']}")
        lines.append(f"- **Question:** {trigger['question']}")
        lines.append(f"  - Sources: {trigger['sources']}")
        lines.append(f"  - Stop: {trigger['stop']}")
    lines.append(f"- **Record:** `{research['evidence_record']}`")

    architecture = packet["architecture"]
    lines.extend(("", "## Experience architecture", "", f"- **Status:** {architecture['status']}", "", "### Inputs", ""))
    _append_list(lines, architecture["inputs"])
    lines.extend(("", "### Synthesis", ""))
    _append_list(lines, architecture["synthesis"])
    lines.extend(("", "### Candidate record", ""))
    for key, value in architecture["candidate_record"].items():
        lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
    lines.append(f"- **Selection:** {architecture['selection_rule']}")

    art = packet["art_direction"]
    lines.extend(("", "## Art direction", "", f"- **Status:** {art['status']}", "", "### Identity sources", ""))
    _append_list(lines, art["identity_sources"])
    lines.extend(("", "### Direction method", ""))
    _append_list(lines, art["direction_method"])
    lines.append(f"- **Record:** `{art['direction_record']}`")

    assets = packet["assets"]
    visual = assets["visual_need_decision"]
    lines.extend(("", "## Imagery and custom assets", "", f"- **Visual decision:** {visual['status']} — {visual['question']}", f"- **Selection:** {visual['selection_rule']}", "", "### Eligible outcomes", ""))
    _append_list(lines, visual["eligible_outcomes"])
    generation = assets["image_generation"]
    lines.extend(("", "### Generated imagery", "", f"- **Use when:** {generation['use_when']}", f"- **Art-direction brief:** `{generation['brief']}`", ""))
    _append_list(lines, generation["loop"])
    custom = assets["custom_graphics"]
    lines.extend(("", "### Custom graphics and icons", "", f"- **Family specification:** `{custom['family_spec']}`", ""))
    _append_list(lines, custom["workflow"])
    lines.append(f"- **Reject when:** {custom['reject_when']}")

    motion = packet["motion"]
    lines.extend(("", "## Motion", "", f"- **Status:** {motion['status']}", f"- **Decision:** {motion['decision_question']}", f"- **Record:** `{motion['record']}`", "", "### Eligible outcomes", ""))
    _append_list(lines, motion["eligible_outcomes"])
    lines.extend(("", "### Rules", ""))
    _append_list(lines, motion["rules"])

    responsive = packet["responsive"]
    lines.extend(
        (
            "",
            "## Responsive behavior",
            "",
            f"- **Principle:** {responsive['principle']}",
            f"- **Contract:** `{responsive['contract']}`",
            f"- **Proof:** {responsive['proof']}",
        )
    )

    evaluation = packet["evaluation"]
    lines.extend(("", "## Evaluation", "", f"- **Verdicts:** `{evaluation['verdicts']}`", ""))
    _append_list(lines, evaluation["criteria"])
    lines.append(f"- **Finding record:** `{evaluation['finding_record']}`")
    lines.append(f"- **Stop:** {evaluation['stop']}")

    evidence = packet["local_evidence"]
    lines.extend(("", "## Local evidence", "", f"- **Status:** {evidence['status']}", f"- **Role:** {evidence['role']}", f"- **Query:** {evidence['query'] or 'none'}", f"- **Absence rule:** {evidence['absence_rule']}", f"- **Limitations:** {evidence['limitations']}", ""))
    for analog in evidence["product_analogs"]:
        lines.append(f"- **{analog['label']}** — `{analog['status']}`")
        if analog["catalog_terms"]:
            lines.append(f"  - Catalog terms: {analog['catalog_terms']}")
        lines.append(f"  - Warning: {analog['warning']}")
    return "\n".join(lines) + "\n"


def format_packet_json(packet: dict[str, Any]) -> str:
    return json.dumps(packet, indent=2, ensure_ascii=False) + "\n"


def slugify_name(value: str, fallback: str = "default") -> str:
    normalized = re.sub(r"[^\w]+", "-", str(value or "").casefold(), flags=re.UNICODE)
    normalized = re.sub(r"_+", "-", normalized)
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized[:80] or fallback


_WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


def _persisted_slug(value: str, fallback: str, label: str) -> str:
    """Return a portable persisted component, rejecting Windows device names."""
    slug = slugify_name(value, fallback)
    if slug.split(".", 1)[0].upper() in _WINDOWS_RESERVED_NAMES:
        raise ValueError(
            f"{label} identity produces the Windows-reserved path component {slug!r}; choose another identity."
        )
    return slug


def format_decision_journal(project_name: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return (
        "# Accepted Design Decisions\n\n"
        f"Project: {project_name}\n"
        f"Initialized: {timestamp} UTC\n\n"
        "This file is durable and is never overwritten by packet regeneration.\n"
        "Record only evidence-backed decisions; keep experiments in disposable working notes.\n\n"
        "## Decision record\n\n"
        "| Status | Scope | Driver | Decision | Expected consequence | Evidence | Revisit trigger |\n"
        "|---|---|---|---|---|---|---|\n"
        "| PROPOSED | project |  |  |  |  |  |\n\n"
        "Allowed statuses: `PROPOSED`, `ACCEPTED`, `SUPERSEDED`.\n"
        "\n## Scoped corrections (when applicable)\n\n"
        "Append material user corrections to this ledger or the project's existing finding record.\n"
        "Keep source, scope/owner/states, cause/change, implementation/proof status, "
        "confirming evidence, and applicability/revisit conditions together.\n"
        "An accepted requirement is not proof of a verified implementation. "
        "Current explicit instructions can supersede older scoped decisions; preserve their history.\n"
        "Transfer verified causes, not blanket style preferences. "
        "Missing memory or rendered evidence must not be replaced with inferred acceptance.\n"
    )


def format_page_inquiry(page_name: str, page_brief: str | None = None) -> str:
    identity = _page_identity(page_name)
    title = _page_title(identity)
    brief = page_brief or "UNKNOWN — derive from the verified project brief and journey"
    return (
        f"# {title} — Page Inquiry\n\n"
        f"**Page identity:** {json.dumps(identity, ensure_ascii=False)}\n\n"
        f"**Page brief:** {brief}\n\n"
        "> This file does not prescribe a page type or section order. Resolve the page job from the journey and real content.\n\n"
        "## Page job\n\n"
        "- What must the user understand, decide, or do here?\n"
        "- Which entry states and prior knowledge must the page support?\n"
        "- What is the next useful outcome, and what evidence must precede it?\n\n"
        "## Content and interaction dependencies\n\n"
        "- Required objects, attributes, relationships, states, and real content:\n"
        "- Search, comparison, navigation, recovery, and re-entry behavior:\n"
        "- Loading, empty, partial, error, success, and permission states:\n\n"
        "## Architecture candidates\n\n"
        "Create enough structurally different candidates to cover the live trade-offs. For each, record the organizing principle, content sequence, focal hierarchy, conversion or task action, responsive transformation, and main invalidating risk.\n\n"
        "## Rendered proof\n\n"
        "Test real content at narrow, pressure/intermediate, and wide widths plus applicable focus, open, selected, disabled, loading, error, and reduced-motion states.\n"
    )


def _page_identity(page_name: str) -> str:
    identity = str(page_name or "").strip() or "Untitled page"
    if not identity.isprintable():
        raise ValueError("Page identity must contain printable characters only.")
    return identity


def _page_title(page_name: str) -> str:
    return page_name.replace("-", " ").replace("_", " ").strip().title() or "Page"


def _project_identity(packet: dict[str, Any], explicit_identity: str | None = None) -> str:
    """Resolve an explicit, stable identity for persisted project state.

    The packet's fallback title is useful for ephemeral output, but it is not
    an identity. Persistence must never derive a project directory from the
    brief because that can silently reuse another project's durable ledger.
    """
    candidate = explicit_identity if explicit_identity is not None else packet.get("project_name")
    if not isinstance(candidate, str) or not candidate.strip():
        raise ValueError(
            "Persistence requires an explicit project identity; provide --project-name (or packet project_name)."
        )
    identity = candidate.strip()
    if not identity.isprintable():
        raise ValueError("Persisted project identity must contain printable characters only.")
    if explicit_identity is None and identity == DEFAULT_PROJECT_NAME:
        raise ValueError(
            "Persistence requires an explicit project identity; provide --project-name."
        )

    packet_name = packet.get("project_name")
    if packet_name is not None and (
        not isinstance(packet_name, str) or packet_name.strip() != identity
    ):
        raise ValueError(
            "Packet project_name does not match the requested persisted project identity."
        )
    return identity


def _project_manifest(identity: str, project_slug: str) -> dict[str, str]:
    return {
        "schema_version": PROJECT_MANIFEST_VERSION,
        "project_name": identity,
        "project_slug": project_slug,
    }


def _read_project_manifest(manifest_path: Path, identity: str, project_slug: str) -> None:
    """Validate an existing manifest without modifying any project files."""
    if _is_reparse_path(manifest_path) or not manifest_path.is_file():
        raise ValueError(
            f"Project identity manifest is not a regular file: {manifest_path}"
        )
    if _shared_regular_file(manifest_path):
        raise ValueError(
            f"Project identity manifest must not be a shared hardlink/inode: {manifest_path}"
        )
    try:
        if manifest_path.stat().st_size > PROJECT_MANIFEST_MAX_BYTES:
            raise ProjectManifestCorrupt(
                "Project identity manifest exceeds the deterministic "
                f"{PROJECT_MANIFEST_MAX_BYTES}-byte safety limit: {manifest_path}"
            )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except ProjectManifestCorrupt:
        raise
    except RecursionError as error:
        raise ProjectManifestCorrupt(
            "Project identity manifest exceeds the deterministic "
            f"{PROJECT_MANIFEST_MAX_DEPTH}-level JSON nesting limit: {manifest_path}"
        ) from error
    # ``json.loads`` also raises a plain ValueError when CPython's bounded
    # integer-string conversion rejects an oversized numeric token. Treat all
    # parser ValueErrors as corrupt persisted bytes; identity collisions are
    # checked only after parsing and therefore remain fail-closed below.
    except (ValueError, UnicodeError) as error:
        raise ProjectManifestCorrupt(
            f"Project identity manifest is unreadable or invalid: {manifest_path}"
        ) from error
    except OSError as error:
        raise ValueError(f"Project identity manifest cannot be read safely: {manifest_path}") from error
    tree_error = _project_manifest_tree_error(manifest)
    if tree_error:
        raise ProjectManifestCorrupt(f"{tree_error}: {manifest_path}")
    expected = _project_manifest(identity, project_slug)
    if manifest != expected:
        recorded_name = manifest.get("project_name") if isinstance(manifest, dict) else None
        raise ValueError(
            "Project identity collision: "
            f"slug '{project_slug}' is already owned by {recorded_name!r}; "
            f"refusing to overwrite {manifest_path.parent / 'BRIEF.md'} or inherit its DECISIONS.md."
        )


def _legacy_project_identity_matches(project_dir: Path, identity: str) -> bool:
    """Recognize only explicit metadata when upgrading pre-manifest state."""
    decisions_path = project_dir / "DECISIONS.md"
    if decisions_path.is_symlink() or not decisions_path.is_file() or _shared_regular_file(decisions_path):
        return False
    try:
        decisions = decisions_path.read_text(encoding="utf-8")
    except OSError:
        return False
    match = re.search(r"(?m)^Project:\s*(.*?)\s*$", decisions)
    if not match:
        return False
    recorded_identity = match.group(1).strip()
    if recorded_identity != identity:
        raise ValueError(
            "Project identity collision: existing DECISIONS.md records "
            f"{recorded_identity!r}, not {identity!r}."
        )

    brief_path = project_dir / "BRIEF.md"
    if brief_path.exists() or brief_path.is_symlink():
        if brief_path.is_symlink() or not brief_path.is_file():
            raise ValueError(f"Cannot validate legacy project identity from {brief_path}")
        try:
            brief = brief_path.read_text(encoding="utf-8")
        except OSError as error:
            raise ValueError(f"Cannot validate legacy project identity from {brief_path}") from error
        brief_match = re.search(r"(?m)^\*\*Project:\*\*\s*(.*?)\s*$", brief)
        if not brief_match or brief_match.group(1).strip() != identity:
            raise ValueError(
                "Project identity collision: existing BRIEF.md does not record "
                f"{identity!r}; refusing to replace it."
            )
    return True


def _prepare_project_manifest(
    project_dir: Path,
    identity: str,
    project_slug: str,
    root: Path,
) -> tuple[Path, bool, list[Path]]:
    """Validate project ownership before the first replaceable file write.

    A non-empty directory from an older/unmanaged writer is intentionally not
    guessed at. Refusing it is safer than treating a brief or ledger as proof
    of identity. Empty directories can be claimed by creating the manifest.
    """
    _reject_reparse_chain(project_dir, "Persisted project path")
    _reject_reparse_chain(root, "Selected output directory")
    lexical_project_dir = _absolute_lexical_path(project_dir)
    lexical_root = _absolute_lexical_path(root)
    if not lexical_project_dir.is_relative_to(lexical_root):
        raise ValueError("Persisted project path must remain inside the selected output directory.")
    if project_dir.is_symlink():
        raise ValueError(f"Refusing to persist through a project-directory symlink: {project_dir}")

    manifest_path = project_dir / PROJECT_MANIFEST_FILENAME
    def runtime_artifact(entry: Path) -> bool:
        name = entry.name
        recognized = bool(
            re.fullmatch(r"\.PROJECT\.json\.tmp-[0-9a-f]{32}", name)
            or re.fullmatch(r"PROJECT\.json\.corrupt-[0-9a-f]{32}", name)
        )
        return recognized and entry.is_file() and not _is_reparse_path(entry)

    if manifest_path.exists() or manifest_path.is_symlink():
        try:
            _read_project_manifest(manifest_path, identity, project_slug)
        except ProjectManifestCorrupt:
            runtime_artifacts = [
                entry for entry in project_dir.iterdir()
                if entry != manifest_path and runtime_artifact(entry)
            ]
            other_entries = [
                entry for entry in project_dir.iterdir()
                if entry != manifest_path and not runtime_artifact(entry)
            ]
            legacy_match = _legacy_project_identity_matches(project_dir, identity)
            if other_entries and not legacy_match:
                raise
            quarantined = manifest_path.with_name(
                f"{manifest_path.name}.corrupt-{uuid.uuid4().hex}"
            )
            manifest_path.rename(quarantined)
            recovered = [quarantined, *runtime_artifacts]
        else:
            return manifest_path, False, []
    else:
        recovered = []

    if project_dir.exists() and not recovered:
        if not project_dir.is_dir():
            raise ValueError(f"Project path is not a directory: {project_dir}")
        # Exact project metadata in the old durable ledger is sufficient for
        # a one-time manifest claim; no brief vocabulary is inferred.
        legacy_identity_matches = _legacy_project_identity_matches(project_dir, identity)
        if not legacy_identity_matches:
            try:
                entries = list(project_dir.iterdir())
            except OSError as error:
                raise ValueError(f"Cannot inspect existing project directory: {project_dir}") from error
            recovery_artifacts = [entry for entry in entries if runtime_artifact(entry)]
            existing = next((entry for entry in entries if entry not in recovery_artifacts), None)
            if existing is not None:
                raise ValueError(
                    f"Project directory lacks {PROJECT_MANIFEST_FILENAME}; refusing to overwrite existing state: {project_dir}"
                )
            recovered.extend(recovery_artifacts)

    # Creation is intentionally exclusive. If another process claims the
    # slug between validation and this write, validate its identity rather
    # than overwrite it.
    project_dir.mkdir(parents=True, exist_ok=True)
    _reject_reparse_chain(project_dir, "Persisted project path")
    manifest = _project_manifest(identity, project_slug)
    manifest_content = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if not _atomic_create_text(manifest_path, manifest_content):
        _read_project_manifest(manifest_path, identity, project_slug)
        return manifest_path, False, recovered
    return manifest_path, True, recovered


def _validate_project_outputs(project_dir: Path, page: str | None) -> None:
    """Reject symlinked output targets before replacing any inquiry file."""
    _reject_reparse_chain(project_dir, "Persisted project path")
    paths = [project_dir / "BRIEF.md", project_dir / "DECISIONS.md"]
    if page:
        pages_dir = project_dir / "pages"
        _validate_pages_parent(project_dir, pages_dir)
        page_path = pages_dir / f"{_persisted_slug(page, 'page', 'Page')}.md"
        paths.append(page_path)
    for path in paths:
        if _is_reparse_path(path):
            raise ValueError(f"Refusing to replace a symlinked or reparse-point persisted file: {path}")
        if path.exists() and path.is_dir():
            raise ValueError(f"Persisted output path is a directory, not a file: {path}")
        if path.name == "DECISIONS.md" and _shared_regular_file(path):
            raise ValueError(f"DECISIONS.md must not be a shared hardlink/inode: {path}")
    if page and page_path.exists():
        # This is deliberately part of the preflight, before BRIEF.md can be
        # regenerated. A rejected page claim must not partially update a project.
        _validate_page_identity(page_path, page)


def _validate_page_identity(page_path: Path, page_name: str) -> None:
    """Prevent two exact page identities from sharing one normalized slug."""
    if not page_path.exists():
        return
    identity = _page_identity(page_name)
    expected_heading = f"# {_page_title(identity)} — Page Inquiry"
    try:
        lines = page_path.read_text(encoding="utf-8").splitlines()
        first_line = lines[0]
    except (OSError, UnicodeDecodeError, IndexError) as error:
        raise ValueError(f"Existing page inquiry cannot prove its identity: {page_path}") from error
    marker = next((line.removeprefix("**Page identity:** ") for line in lines if line.startswith("**Page identity:** ")), None)
    recorded_identity: str | None = None
    if marker is not None:
        try:
            parsed = json.loads(marker)
        except json.JSONDecodeError as error:
            raise ValueError(f"Existing page inquiry has invalid identity metadata: {page_path}") from error
        if isinstance(parsed, str):
            recorded_identity = parsed
    elif first_line == expected_heading and identity == _page_title(identity):
        # One-time compatibility for the old friendly-title format. Slug-like,
        # case-variant, and punctuation-variant inputs cannot safely claim it.
        recorded_identity = identity
    if first_line != expected_heading or recorded_identity != identity:
        raise ValueError(
            f"Page identity collision: slug '{page_path.stem}' is already owned by another page; "
            f"refusing to overwrite {page_path}."
        )


def _validate_pages_parent(project_dir: Path, pages_dir: Path) -> None:
    """Revalidate the page parent immediately before any page publication."""
    _reject_reparse_chain(pages_dir, "Persisted pages path")
    if _is_reparse_path(pages_dir) or (pages_dir.exists() and not pages_dir.is_dir()):
        raise ValueError(f"Refusing to persist through an invalid pages path: {pages_dir}")
    lexical_project = _absolute_lexical_path(project_dir)
    lexical_pages = _absolute_lexical_path(pages_dir)
    if not lexical_pages.is_relative_to(lexical_project):
        raise ValueError(f"Persisted pages path must remain inside the project directory: {pages_dir}")


@contextmanager
def locked_project_state(output_dir: str | Path, project_identity: str, *, create: bool = False):
    """Share the existing identity/locking contract without generating an inquiry."""
    lexical = _absolute_lexical_path(output_dir)
    _reject_reparse_chain(lexical, "Selected output directory")
    root = _normalize_lexical_aliases(lexical, "Selected output directory")
    _reject_reparse_chain(root, "Selected output directory")
    identity = _project_identity({}, project_identity)
    slug = _persisted_slug(identity, "project", "Project")
    project = root / "design-intelligence" / slug
    _reject_reparse_chain(project, "Project state")
    if not create and not project.exists():
        yield None
        return
    with _persistence_lock(root, slug):
        _reject_reparse_chain(project, "Project state")
        if create:
            _prepare_project_manifest(project, identity, slug, root)
        _read_project_manifest(project / PROJECT_MANIFEST_FILENAME, identity, slug)
        yield project
        _read_project_manifest(project / PROJECT_MANIFEST_FILENAME, identity, slug)


def persist_decision_packet(
    packet: dict[str, Any],
    page: str | None = None,
    output_dir: str | None = None,
    page_brief: str | None = None,
    project_identity: str | None = None,
) -> dict[str, Any]:
    root_lexical = _absolute_lexical_path(output_dir or ".")
    _reject_reparse_chain(root_lexical, "Selected output directory")
    root = _normalize_lexical_aliases(root_lexical, "Selected output directory")
    # Alias expansion must never erase a redirect inserted during inspection.
    _reject_reparse_chain(root_lexical, "Selected output directory")
    _reject_reparse_chain(root, "Selected output directory")
    identity = _project_identity(packet, project_identity)
    project_slug = _persisted_slug(identity, "default", "Project")
    page_slug = _persisted_slug(page, "page", "Page") if page else None
    # Validate all caller-provided text before claiming a project directory or
    # publishing its manifest. This keeps an encoding failure from looking
    # like a successfully persisted, but incomplete, identity.
    brief_content = format_packet_markdown(packet)
    brief_content.encode("utf-8")
    decisions_content = format_decision_journal(identity)
    decisions_content.encode("utf-8")
    if isinstance(page_brief, str):
        page_brief.encode("utf-8")
    project_dir = root / "design-intelligence" / project_slug
    with _persistence_lock(root, project_slug):
        # All identity and parent checks happen before BRIEF publication.  The
        # project lock also makes corrupt-manifest recovery and page claims
        # deterministic across concurrent callers in this process tree.
        _validate_project_outputs(project_dir, page)
        page_content: str | None = None
        if page:
            # Formatting is caller-controlled and may execute hooks in an
            # embedding host. Complete and encode it before claiming the
            # project manifest so a hook or Unicode failure cannot publish
            # shared state without its page inquiry.
            page_content = format_page_inquiry(page, page_brief)
            page_content.encode("utf-8")
            _validate_pages_parent(project_dir, project_dir / "pages")
            _validate_project_outputs(project_dir, page)
        manifest_path, manifest_created, recovered_manifests = _prepare_project_manifest(
            project_dir, identity, project_slug, root
        )
        # Revalidate the identity inode after the claim boundary; a path swap
        # between preparation and output publication must not turn a shared
        # PROJECT.json into an accepted project owner.
        _read_project_manifest(manifest_path, identity, project_slug)
        _validate_project_outputs(project_dir, page)

        created_or_updated: list[str] = []
        preserved: list[str] = []
        if manifest_created:
            created_or_updated.append(str(manifest_path))
        else:
            preserved.append(str(manifest_path))
        preserved.extend(str(path) for path in recovered_manifests)

        brief_path = project_dir / "BRIEF.md"
        _atomic_write_text(brief_path, brief_content)
        created_or_updated.append(str(brief_path))

        decisions_path = project_dir / "DECISIONS.md"
        if _atomic_create_text(decisions_path, decisions_content):
            created_or_updated.append(str(decisions_path))
        else:
            # The exclusive link claim can race a foreign writer. Recheck the
            # ledger inode before treating it as preserved state.
            if _shared_regular_file(decisions_path):
                raise ValueError(f"DECISIONS.md must not be a shared hardlink/inode: {decisions_path}")
            preserved.append(str(decisions_path))

        if page:
            pages_dir = project_dir / "pages"
            pages_dir.mkdir(parents=True, exist_ok=True)
            _validate_pages_parent(project_dir, pages_dir)
            page_path = pages_dir / f"{page_slug}.md"
            if page_content is None:  # pragma: no cover - page preflight is unconditional
                raise RuntimeError("Page inquiry was not prepared before publication.")
            # The formatter already ran during preflight. Revalidate the
            # parent/output after all intervening work and immediately before
            # atomic publication.
            _validate_pages_parent(project_dir, pages_dir)
            _validate_project_outputs(project_dir, page)
            if page_path.exists():
                _validate_page_identity(page_path, page)
                _atomic_write_text(page_path, page_content)
            elif not _atomic_create_text(page_path, page_content):
                # Another process claimed the normalized slug after our absence
                # check. Its complete identity record must agree before update.
                _validate_page_identity(page_path, page)
                _atomic_write_text(page_path, page_content)
            created_or_updated.append(str(page_path))

        return {
            "design_intelligence_dir": str(project_dir),
            "created_or_updated_files": created_or_updated,
            "preserved_files": preserved,
        }


def generate_decision_packet(
    brief: str,
    project_name: str | None = None,
    output_format: str = "markdown",
    persist: bool = False,
    page: str | None = None,
    output_dir: str | None = None,
    page_brief: str | None = None,
    declared_context: dict[str, Any] | None = None,
    analog_query: str | None = None,
) -> str:
    """Format a schema 3 packet without semantically interpreting ``brief``."""
    packet = DecisionPacketGenerator().generate(
        brief,
        project_name,
        declared_context=declared_context,
        analog_query=analog_query,
    )
    if persist:
        persist_decision_packet(
            packet,
            page=page,
            output_dir=output_dir,
            page_brief=page_brief,
            project_identity=project_name,
        )
    if output_format == "json":
        return format_packet_json(packet)
    return format_packet_markdown(packet)
