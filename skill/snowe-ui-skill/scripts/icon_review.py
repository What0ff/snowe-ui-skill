#!/usr/bin/env python3
"""Generate a deterministic, self-contained representative-control icon sheet.

The helper validates every SVG candidate structurally, then renders existing,
custom, and no-icon alternatives with identical labels, sizes, and states. It
does not choose a winner or claim optical quality; any recorded decision and
rationale are explicitly human-review evidence supplied by the manifest. The
sheet is comparison evidence, not a pixel-identical host-component render.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import os
import re
import stat
import sys
import uuid
from pathlib import Path
from typing import Any

from asset_quality import AssetValidationError, validate_svg_asset


SCHEMA_VERSION = "1.0"
KINDS = {"existing", "custom", "none"}
COMPONENTS = {"icon-button", "labeled-button", "service-item"}
STATES = {"default", "hover", "focus", "selected", "disabled", "dark", "high-contrast"}
VERDICTS = {"KEEP", "REVISE", "REJECT", "UNKNOWN"}
CONTEXT_BASES = {"representative", "repository-derived"}
HOST_PROOF_STRATEGIES = {"icon-owner", "dialog-clone", "service-mask", "button-clone"}
HOST_PROOF_STATES = {"default", "hover", "dark", "focus", "disabled", "forced-colors"}
MAX_JSON_BYTES = 1_000_000
MAX_JSON_DEPTH = 128
LOCAL_ROUTE_RE = re.compile(r"/[A-Za-z0-9._~!$&'()*+,;=:@/-]+")


class ManifestError(ValueError):
    """Raised when icon comparison evidence violates the manifest contract."""


def _is_reparse_path(path: Path) -> bool:
    try:
        information = os.lstat(path)
    except FileNotFoundError:
        return False
    except (OSError, ValueError) as error:
        raise ManifestError(f"Path cannot be inspected safely: {path}: {error}") from error
    attributes = getattr(information, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return stat.S_ISLNK(information.st_mode) or bool(attributes & reparse_flag)


def _reject_reparse_chain(path: Path, label: str) -> None:
    try:
        current = Path(os.path.abspath(os.fspath(path)))
    except (OSError, ValueError) as error:
        raise ManifestError(f"{label} cannot be inspected safely: {path}: {error}") from error
    while True:
        if _is_reparse_path(current):
            raise ManifestError(f"{label} must not contain a symlink, junction, or reparse point: {current}")
        parent = current.parent
        if parent == current:
            return
        current = parent


def _atomic_write_text(path: Path, content: str) -> None:
    temporary = path.with_name(f".{path.name}.tmp-{uuid.uuid4().hex}")
    try:
        # The repository declares LF for text artifacts. Disable platform
        # newline translation so regeneration is byte-identical everywhere.
        with temporary.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except UnicodeError as error:
        raise ManifestError(f"Output contains invalid Unicode text: {error}") from error
    finally:
        if temporary.exists():
            temporary.unlink()


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{field} must be a non-empty string")
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise ManifestError(f"{field} contains unpaired Unicode surrogate code points")
    return value.strip()


def _safe_float(value: Any, field: str) -> float:
    try:
        return float(value)
    except (OverflowError, ValueError) as error:
        raise ManifestError(f"{field} must be a finite number") from error


def _json_tree_error(value: Any, label: str) -> str | None:
    pending: list[tuple[Any, int]] = [(value, 0)]
    while pending:
        current, depth = pending.pop()
        if depth > MAX_JSON_DEPTH:
            return f"{label} exceeds the deterministic {MAX_JSON_DEPTH}-level JSON nesting limit"
        if isinstance(current, str):
            if any(0xD800 <= ord(character) <= 0xDFFF for character in current):
                return f"{label} contains unpaired Unicode surrogate code points"
        elif isinstance(current, float) and not math.isfinite(current):
            return f"{label} contains a non-finite JSON number"
        elif isinstance(current, dict):
            for key, child in current.items():
                if any(0xD800 <= ord(character) <= 0xDFFF for character in key):
                    return f"{label} contains unpaired Unicode surrogate code points"
                pending.append((child, depth + 1))
        elif isinstance(current, list):
            pending.extend((child, depth + 1) for child in current)
    return None


def _served_route(value: Any, field: str) -> str:
    route = _text(value, field)
    if (
        route.startswith("//")
        or "//" in route
        or not LOCAL_ROUTE_RE.fullmatch(route)
        or any(segment in {".", ".."} for segment in route.split("/"))
    ):
        raise ManifestError(f"{field} must be a canonical local served route")
    return route


def _positive_sizes(value: Any, field: str) -> list[float]:
    if not isinstance(value, list) or not value:
        raise ManifestError(f"{field} must be a non-empty array")
    sizes: list[float] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise ManifestError(f"{field} values must be positive finite numbers")
        try:
            number = _safe_float(item, f"{field} values")
        except ManifestError as error:
            raise ManifestError(f"{field} values must be positive finite numbers") from error
        if not math.isfinite(number) or number <= 0:
            raise ManifestError(f"{field} values must be positive finite numbers")
        sizes.append(number)
    if len(set(sizes)) != len(sizes):
        raise ManifestError(f"{field} must not contain duplicates")
    return sizes


def _local_file(root: Path, value: Any, field: str) -> Path:
    text = _text(value, field)
    if "://" in text:
        raise ManifestError(f"{field} must be a local file, not a URL")
    path = Path(text)
    try:
        lexical = Path(os.path.abspath(os.fspath(path if path.is_absolute() else root / path)))
    except (OSError, ValueError) as error:
        raise ManifestError(f"{field} cannot be inspected safely: {text}: {error}") from error
    _reject_reparse_chain(lexical, field)
    try:
        resolved = lexical.resolve()
    except (OSError, RuntimeError, ValueError) as error:
        raise ManifestError(f"{field} cannot be resolved safely: {lexical}: {error}") from error
    if not resolved.is_file():
        raise ManifestError(f"{field} file not found: {resolved}")
    return resolved


def _manifest_file(path: str | Path) -> Path:
    try:
        lexical = Path(os.path.abspath(os.fspath(Path(path).expanduser())))
    except (TypeError, ValueError, OSError) as error:
        raise ManifestError(f"Manifest path is invalid: {error}") from error
    _reject_reparse_chain(lexical, "Manifest path")
    try:
        resolved = lexical.resolve(strict=True)
    except FileNotFoundError as error:
        raise ManifestError(f"manifest not found: {lexical}") from error
    except (OSError, RuntimeError, ValueError) as error:
        raise ManifestError(f"Manifest path cannot be resolved safely: {lexical}: {error}") from error
    if not resolved.is_file():
        raise ManifestError(f"manifest is not a file: {resolved}")
    return resolved


def _sha256_text(value: Any, field: str) -> str:
    digest = _text(value, field)
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ManifestError(f"{field} must be a 64-character lowercase SHA-256 digest")
    return digest


def _host_proof(
    value: Any,
    context_prefix: str,
    context_selector: str,
    comparison_states: list[str],
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ManifestError(f"{context_prefix}.host_proof must be an object for repository-derived evidence")
    for field in ("scenario", "route", "target_selector", "label_selector", "icon_selector", "strategy", "expected_label"):
        _text(value.get(field), f"{context_prefix}.host_proof.{field}")
    if value["target_selector"] != context_selector:
        raise ManifestError(f"{context_prefix}.host_proof.target_selector must exactly match context_evidence.selector")
    value["route"] = _served_route(value.get("route"), f"{context_prefix}.host_proof.route")
    if value["strategy"] not in HOST_PROOF_STRATEGIES:
        raise ManifestError(
            f"{context_prefix}.host_proof.strategy must be one of: {', '.join(sorted(HOST_PROOF_STRATEGIES))}"
        )
    if value["strategy"] == "button-clone":
        _text(value.get("expected_visible_label"), f"{context_prefix}.host_proof.expected_visible_label")
    states = value.get("states")
    if not isinstance(states, list) or not states or any(not isinstance(state, str) or state not in HOST_PROOF_STATES for state in states):
        raise ManifestError(f"{context_prefix}.host_proof.states must use only: {', '.join(sorted(HOST_PROOF_STATES))}")
    if len(set(states)) != len(states):
        raise ManifestError(f"{context_prefix}.host_proof.states must not contain duplicates")
    state_map = value.get("state_map")
    if (
        not isinstance(state_map, dict)
        or any(not isinstance(key, str) or not isinstance(host_state, str) for key, host_state in state_map.items())
        or set(state_map) != set(comparison_states)
    ):
        raise ManifestError(
            f"{context_prefix}.host_proof.state_map must map every comparison state exactly once"
        )
    if set(state_map.values()) != set(states):
        raise ManifestError(
            f"{context_prefix}.host_proof.state_map values must exactly match exercised host states"
        )
    expected_state_map = {
        comparison_state: "forced-colors" if comparison_state == "high-contrast" else comparison_state
        for comparison_state in comparison_states
    }
    if state_map != expected_state_map:
        raise ManifestError(
            f"{context_prefix}.host_proof.state_map must use canonical comparison-to-host state bindings"
        )
    for comparison_state, host_state in state_map.items():
        if not isinstance(comparison_state, str) or comparison_state not in STATES:
            raise ManifestError(
                f"{context_prefix}.host_proof.state_map keys must use declared comparison states"
            )
        if not isinstance(host_state, str) or host_state not in HOST_PROOF_STATES:
            raise ManifestError(
                f"{context_prefix}.host_proof.state_map values must use exercised host states"
            )
        if comparison_state == "high-contrast" and host_state != "forced-colors":
            raise ManifestError(
                f"{context_prefix}.host_proof.state_map must map high-contrast to forced-colors"
            )
    if "dark" in states:
        for field in ("dark_surface_selector", "expected_dark_background"):
            _text(value.get(field), f"{context_prefix}.host_proof.{field}")
    viewports = value.get("viewports")
    if not isinstance(viewports, list) or len(viewports) < 2:
        raise ManifestError(f"{context_prefix}.host_proof.viewports must contain wide and mobile host targets")
    viewport_names: set[str] = set()
    for index, viewport in enumerate(viewports):
        prefix = f"{context_prefix}.host_proof.viewports[{index}]"
        if not isinstance(viewport, dict):
            raise ManifestError(f"{prefix} must be an object")
        name = _text(viewport.get("name"), f"{prefix}.name")
        if name in viewport_names:
            raise ManifestError(f"duplicate host viewport name: {name}")
        viewport_names.add(name)
        for field in ("width", "height"):
            number = viewport.get(field)
            if isinstance(number, bool) or not isinstance(number, (int, float)):
                raise ManifestError(f"{prefix}.{field} must be a positive finite number")
            number = _safe_float(number, f"{prefix}.{field}")
            if not math.isfinite(number) or number <= 0:
                raise ManifestError(f"{prefix}.{field} must be a positive finite number")
        if "expected_icon_size" in viewport:
            number = viewport["expected_icon_size"]
            if number is not None:
                if isinstance(number, bool) or not isinstance(number, (int, float)):
                    raise ManifestError(f"{prefix}.expected_icon_size must be null or a positive finite number")
                number = _safe_float(number, f"{prefix}.expected_icon_size")
                if not math.isfinite(number) or number <= 0:
                    raise ManifestError(f"{prefix}.expected_icon_size must be null or a positive finite number")
    if not {"wide", "mobile"}.issubset(viewport_names):
        raise ManifestError(f"{context_prefix}.host_proof.viewports must include wide and mobile names")
    challengers = value.get("challenger_ids")
    if not isinstance(challengers, list) or not challengers or any(not isinstance(item, str) or not item.strip() for item in challengers):
        raise ManifestError(f"{context_prefix}.host_proof.challenger_ids must be a non-empty array of candidate IDs")
    if len(set(challengers)) != len(challengers):
        raise ManifestError(f"{context_prefix}.host_proof.challenger_ids must not contain duplicates")
    if value["strategy"] == "dialog-clone" and not value.get("open_selector"):
        raise ManifestError(f"{context_prefix}.host_proof.open_selector is required for dialog-clone evidence")
    if value.get("open_selector") is not None:
        _text(value.get("open_selector"), f"{context_prefix}.host_proof.open_selector")
    return value


def _paths_alias(left: Path, right: Path) -> bool:
    try:
        left_absolute = Path(os.path.abspath(os.fspath(left)))
        right_absolute = Path(os.path.abspath(os.fspath(right)))
    except (OSError, ValueError) as error:
        raise ManifestError(f"Path alias check cannot be performed safely: {error}") from error
    try:
        if left_absolute.resolve() == right_absolute.resolve():
            return True
    except (OSError, RuntimeError, ValueError) as error:
        raise ManifestError(f"Path alias check cannot be performed safely: {error}") from error
    if left_absolute.exists() and right_absolute.exists():
        try:
            return left_absolute.samefile(right_absolute)
        except OSError:
            return False
    return False


def load_review_manifest(path: str | Path) -> dict[str, Any]:
    manifest_path = _manifest_file(path)
    try:
        if manifest_path.stat().st_size > MAX_JSON_BYTES:
            raise ManifestError(f"manifest exceeds the deterministic {MAX_JSON_BYTES}-byte safety limit")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ManifestError(f"manifest is not valid JSON: {error}") from error
    except ValueError as error:
        raise ManifestError(f"manifest JSON cannot be parsed safely: {error}") from error
    except (OSError, UnicodeDecodeError) as error:
        raise ManifestError(f"manifest cannot be read as UTF-8 JSON: {manifest_path}: {error}") from error
    except RecursionError as error:
        raise ManifestError(f"manifest exceeds the deterministic {MAX_JSON_DEPTH}-level JSON nesting limit") from error
    tree_error = _json_tree_error(manifest, "manifest JSON")
    if tree_error:
        raise ManifestError(tree_error)
    if not isinstance(manifest, dict):
        raise ManifestError("manifest root must be an object")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ManifestError(f"schema_version must be {SCHEMA_VERSION!r}")
    _text(manifest.get("title"), "title")
    contexts = manifest.get("contexts")
    if not isinstance(contexts, list) or not contexts:
        raise ManifestError("contexts must be a non-empty array")

    root = manifest_path.parent
    context_ids: set[str] = set()
    for context_index, context in enumerate(contexts):
        prefix = f"contexts[{context_index}]"
        if not isinstance(context, dict):
            raise ManifestError(f"{prefix} must be an object")
        context_id = _text(context.get("id"), f"{prefix}.id")
        if context_id in context_ids:
            raise ManifestError(f"duplicate context id: {context_id}")
        context_ids.add(context_id)
        for field in ("role", "label", "decision_evidence"):
            _text(context.get(field), f"{prefix}.{field}")
        component = context.get("component")
        if not isinstance(component, str) or component not in COMPONENTS:
            raise ManifestError(f"{prefix}.component must be one of: {', '.join(sorted(COMPONENTS))}")
        sizes = _positive_sizes(context.get("sizes"), f"{prefix}.sizes")
        context["_sizes"] = sizes
        states = context.get("states")
        if not isinstance(states, list) or not states or any(not isinstance(state, str) or state not in STATES for state in states):
            raise ManifestError(f"{prefix}.states must use only: {', '.join(sorted(STATES))}")
        if len(set(states)) != len(states):
            raise ManifestError(f"{prefix}.states must not contain duplicates")
        verdict = context.get("verdict")
        if not isinstance(verdict, str) or verdict not in VERDICTS:
            raise ManifestError(f"{prefix}.verdict must be KEEP, REVISE, REJECT, or UNKNOWN")
        selected_value = context.get("selected")
        if verdict in {"REJECT", "UNKNOWN"}:
            if selected_value is not None:
                raise ManifestError(f"{prefix}.selected must be null while verdict is {verdict}")
        else:
            _text(selected_value, f"{prefix}.selected")

        context_evidence = context.get("context_evidence")
        if not isinstance(context_evidence, dict):
            raise ManifestError(f"{prefix}.context_evidence must be an object")
        for field in ("basis", "source", "selector", "viewport"):
            _text(context_evidence.get(field), f"{prefix}.context_evidence.{field}")
        if context_evidence["basis"] not in CONTEXT_BASES:
            raise ManifestError(f"{prefix}.context_evidence.basis must be representative or repository-derived")
        if context_evidence["basis"] == "repository-derived":
            source_file = _local_file(root, context_evidence["source"], f"{prefix}.context_evidence.source")
            source_digest = _sha256_text(context_evidence.get("source_sha256"), f"{prefix}.context_evidence.source_sha256")
            actual_source_digest = hashlib.sha256(source_file.read_bytes()).hexdigest()
            if source_digest != actual_source_digest:
                raise ManifestError(
                    f"{prefix}.context_evidence.source_sha256 does not match the exact context source bytes"
                )
            context_evidence["_source_file"] = str(source_file)
            context_evidence["_source_sha256"] = source_digest
            if context["selected"] is None:
                raise ManifestError(
                    f"{prefix} repository-derived host proof requires a selected candidate; use representative evidence for REJECT/UNKNOWN"
                )
            host_proof = _host_proof(
                context.get("host_proof"), prefix, context_evidence["selector"], states
            )
            context["_host_proof"] = host_proof
        elif context.get("host_proof") is not None:
            raise ManifestError(f"{prefix}.host_proof is only allowed for repository-derived context evidence")

        candidates = context.get("candidates")
        if not isinstance(candidates, list) or len(candidates) < 2:
            raise ManifestError(f"{prefix}.candidates must contain at least two real alternatives")
        candidate_ids: set[str] = set()
        kinds: set[str] = set()
        candidate_digests: set[str] = set()
        for candidate_index, candidate in enumerate(candidates):
            candidate_prefix = f"{prefix}.candidates[{candidate_index}]"
            if not isinstance(candidate, dict):
                raise ManifestError(f"{candidate_prefix} must be an object")
            candidate_id = _text(candidate.get("id"), f"{candidate_prefix}.id")
            if candidate_id in candidate_ids:
                raise ManifestError(f"duplicate candidate id in {context_id}: {candidate_id}")
            candidate_ids.add(candidate_id)
            for field in ("name", "source", "license", "rationale"):
                _text(candidate.get(field), f"{candidate_prefix}.{field}")
            if candidate.get("visible_label") is not None:
                _text(candidate.get("visible_label"), f"{candidate_prefix}.visible_label")
            kind = candidate.get("kind")
            if not isinstance(kind, str) or kind not in KINDS:
                raise ManifestError(f"{candidate_prefix}.kind must be existing, custom, or none")
            kinds.add(kind)
            if kind == "none":
                if candidate.get("asset") or candidate.get("metadata"):
                    raise ManifestError(f"{candidate_prefix} no-icon candidate must not declare asset files")
                candidate["_svg"] = ""
                candidate["_validation"] = None
            else:
                asset = _local_file(root, candidate.get("asset"), f"{candidate_prefix}.asset")
                metadata = _local_file(root, candidate.get("metadata"), f"{candidate_prefix}.metadata")
                try:
                    result = validate_svg_asset(asset, metadata)
                except AssetValidationError as error:
                    raise ManifestError(
                        f"{candidate_prefix} failed structural SVG validation safely: {error}"
                    ) from error
                if not result["valid"]:
                    raise ManifestError(
                        f"{candidate_prefix} failed structural SVG validation: " + "; ".join(result["errors"])
                    )
                svg_bytes = asset.read_bytes()
                digest = hashlib.sha256(svg_bytes).hexdigest()
                manifest_digest = _sha256_text(
                    candidate.get("asset_sha256"), f"{candidate_prefix}.asset_sha256"
                )
                if manifest_digest != digest:
                    raise ManifestError(
                        f"{candidate_prefix}.asset_sha256 does not match the exact asset bytes"
                    )
                if digest in candidate_digests:
                    raise ManifestError(f"{candidate_prefix} reuses identical SVG bytes under another candidate label")
                candidate_digests.add(digest)
                try:
                    if metadata.stat().st_size > MAX_JSON_BYTES:
                        raise ManifestError(
                            f"{candidate_prefix}.metadata exceeds the deterministic {MAX_JSON_BYTES}-byte safety limit"
                        )
                    metadata_value = json.loads(metadata.read_text(encoding="utf-8"))
                except ManifestError:
                    raise
                except json.JSONDecodeError as error:
                    raise ManifestError(f"{candidate_prefix}.metadata is not valid JSON: {error}") from error
                except ValueError as error:
                    raise ManifestError(
                        f"{candidate_prefix}.metadata JSON cannot be parsed safely: {error}"
                    ) from error
                except RecursionError as error:
                    raise ManifestError(
                        f"{candidate_prefix}.metadata exceeds the deterministic {MAX_JSON_DEPTH}-level JSON nesting limit"
                    ) from error
                except (OSError, UnicodeDecodeError) as error:
                    raise ManifestError(f"{candidate_prefix}.metadata cannot be read as UTF-8 JSON: {error}") from error
                metadata_tree_error = _json_tree_error(metadata_value, f"{candidate_prefix}.metadata JSON")
                if metadata_tree_error:
                    raise ManifestError(metadata_tree_error)
                if not isinstance(metadata_value, dict):
                    raise ManifestError(f"{candidate_prefix}.metadata root must be a JSON object")
                if metadata_value.get("name") != candidate_id:
                    raise ManifestError(
                        f"{candidate_prefix}.id must exactly match metadata name {metadata_value.get('name')!r}"
                    )
                provenance_kind = metadata_value.get("provenance", {}).get("kind")
                if kind == "custom" and provenance_kind != "original":
                    raise ManifestError(f"{candidate_prefix} custom candidates require original provenance")
                for field in ("source", "license"):
                    if candidate.get(field) != metadata_value.get(field):
                        raise ManifestError(
                            f"{candidate_prefix}.{field} must exactly match validated metadata {field}"
                        )
                declared_sizes = {
                    _safe_float(size, f"{candidate_prefix}.metadata.target_sizes")
                    for size in metadata_value.get("target_sizes", [])
                }
                missing_sizes = [size for size in sizes if size not in declared_sizes]
                if missing_sizes:
                    raise ManifestError(
                        f"{candidate_prefix} metadata omits context target sizes: "
                        + ", ".join(f"{size:g}" for size in missing_sizes)
                    )
                candidate["_svg"] = svg_bytes.decode("utf-8")
                candidate["_validation"] = result
                candidate["_digest"] = digest
                candidate["_manifest_digest"] = manifest_digest
                candidate["_asset_file"] = str(asset)
                candidate["_metadata_file"] = str(metadata)
        if "_host_proof" in context:
            host_proof = context["_host_proof"]
            challenger_ids = set(host_proof["challenger_ids"])
            if challenger_ids != candidate_ids - {context["selected"]}:
                raise ManifestError(
                    f"{prefix}.host_proof.challenger_ids must cover every non-selected candidate"
                )
        if context["selected"] not in candidate_ids:
            if context["selected"] is not None:
                raise ManifestError(f"{prefix}.selected must name a candidate in the same context")
        if "_host_proof" in context and context["_host_proof"]["strategy"] == "button-clone":
            expected_visible_label = context["_host_proof"]["expected_visible_label"]
            for candidate in candidates:
                if candidate["kind"] != "none":
                    continue
                visible_label = _text(candidate.get("visible_label"), f"{prefix}.candidate {candidate['id']}.visible_label")
                if visible_label != expected_visible_label:
                    raise ManifestError(
                        f"{prefix}.candidate {candidate['id']}.visible_label must exactly match "
                        f"host_proof.expected_visible_label"
                    )
        if len(kinds) < 2:
            raise ManifestError(f"{prefix} must compare materially different candidate kinds")
    manifest["_path"] = str(manifest_path)
    return manifest


def _candidate_icon(candidate: dict[str, Any], size: float) -> str:
    if candidate["kind"] == "none":
        return ""
    return (
        f'<span class="icon" aria-hidden="true" style="--icon-size:{size:g}px">'
        f'{candidate["_svg"]}</span>'
    )


def _component(context: dict[str, Any], candidate: dict[str, Any], size: float, state: str) -> str:
    label = html.escape(context["label"])
    detail = html.escape(str(context.get("detail", "")))
    icon = _candidate_icon(candidate, size)
    classes = f"preview preview--{context['component']} state--{state}"
    disabled = " disabled" if state == "disabled" else ""
    selected = ' aria-pressed="true"' if state == "selected" and context["component"] != "service-item" else ""
    if context["component"] == "icon-button":
        if candidate["kind"] == "none":
            visible_label = html.escape(str(candidate.get("visible_label", context["label"])))
            return f'<button class="{classes} preview--text-button" aria-label="{label}"{disabled}{selected}><span>{visible_label}</span></button>'
        return f'<button class="{classes}" aria-label="{label}"{disabled}{selected}>{icon}<span class="sr-only">{label}</span></button>'
    if context["component"] == "labeled-button":
        return f'<button class="{classes}"{disabled}{selected}>{icon}<span>{label}</span></button>'
    return f'<div class="{classes}">{icon}<span class="copy"><strong>{label}</strong><small>{detail}</small></span></div>'


def render_review_html(manifest: dict[str, Any]) -> str:
    sections: list[str] = []
    for context in manifest["contexts"]:
        cards: list[str] = []
        for candidate in context["candidates"]:
            selected = context["selected"] is not None and candidate["id"] == context["selected"]
            matrices: list[str] = []
            matrix_sizes: list[tuple[float, str]]
            if candidate["kind"] == "none":
                matrix_sizes = [(context["_sizes"][0], "No icon")]
            else:
                matrix_sizes = [(size, f"{size:g}px") for size in context["_sizes"]]
            for size, size_label in matrix_sizes:
                states = "".join(
                    f'<div class="state-cell state-cell--{state}"><span class="state-label">{html.escape(state)}</span>{_component(context, candidate, size, state)}</div>'
                    for state in context["states"]
                )
                matrices.append(f'<div class="size-row"><div class="size-label">{size_label}</div><div class="state-row state-row--{context["component"]}">{states}</div></div>')
            validation = candidate.get("_validation")
            contract = "not applicable — no SVG" if validation is None else "structural SVG contract: PASS"
            asset_digest = "not applicable — no SVG" if validation is None else candidate["asset_sha256"]
            cards.append(
                f'<article class="candidate{" candidate--selected" if selected else ""}" data-candidate="{html.escape(candidate["id"])}">'
                f'<header><div><span class="kind">{html.escape(candidate["kind"])}</span><h3>{html.escape(candidate["name"])}</h3></div>'
                f'<span class="decision">{"SELECTED" if selected else "NOT SELECTED"}</span></header>'
                f'<p>{html.escape(candidate["rationale"])}</p><dl><dt>Source</dt><dd>{html.escape(candidate["source"])}</dd>'
                f'<dt>License</dt><dd>{html.escape(candidate["license"])}</dd><dt>Asset SHA-256</dt><dd>{html.escape(asset_digest)}</dd>'
                f'<dt>Deterministic check</dt><dd>{contract}</dd></dl>'
                f'{"".join(matrices)}</article>'
            )
        host_proof = context.get("_host_proof")
        host_detail = ""
        if host_proof:
            host_detail = (
                f'<p class="host-proof"><strong>Host proof:</strong> '
                f'{html.escape(host_proof["scenario"])} · {html.escape(host_proof["route"])} · '
                f'{html.escape(host_proof["target_selector"])} · {html.escape(host_proof["strategy"])} · '
                f'{html.escape(", ".join(host_proof["states"]))} · '
                f'{html.escape(", ".join(item["name"] for item in host_proof["viewports"]))} · '
                f'selected and rejected candidates rendered in host</p>'
            )
        sections.append(
            f'<section class="context" id="{html.escape(context["id"])}"><div class="context-heading">'
            f'<span class="eyebrow">{html.escape(context["component"])}</span><h2>{html.escape(context["role"])}</h2>'
            f'<p><strong>{html.escape(context["verdict"])}</strong> · Human visual judgment: {html.escape(context["decision_evidence"])}</p>'
            f'<p class="context-source"><strong>Context evidence:</strong> {html.escape(context["context_evidence"]["basis"])} · '
            f'{html.escape(context["context_evidence"]["source"])} · {html.escape(context["context_evidence"]["selector"])} · '
            f'{html.escape(context["context_evidence"]["viewport"])}</p>'
            f'{host_detail}'
            f'</div><div class="candidate-grid">{"".join(cards)}</div></section>'
        )
    title = html.escape(manifest["title"])
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>
:root{{--paper:#f5f1e8;--ink:#171918;--muted:#62665f;--line:#c9c5bb;--accent:#c8422d;--dark:#171a18;--light:#fffdf7}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.45 system-ui,sans-serif}}
main{{max-width:1500px;margin:auto;padding:40px 28px 80px}}h1,h2,h3,p{{margin-top:0}}h1{{font-size:clamp(30px,4vw,58px);line-height:1;max-width:950px}}
.lede{{max-width:900px;color:var(--muted)}}.evidence{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:28px 0 42px}}
.evidence p{{padding:14px;border:1px solid var(--line);background:rgba(255,255,255,.45);margin:0}}.context{{border-top:2px solid var(--ink);padding:28px 0 44px}}
.context-heading{{max-width:950px}}.context-source{{font-size:12px;color:var(--muted)}}.eyebrow,.kind,.state-label,.size-label,.decision{{font-size:11px;letter-spacing:.08em;text-transform:uppercase;font-weight:750}}
.candidate-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr));gap:18px}}.candidate{{border:1px solid var(--line);background:var(--light);padding:18px;min-width:0}}
.candidate--selected{{border:2px solid var(--accent);box-shadow:4px 4px 0 var(--accent)}}.candidate header{{display:flex;justify-content:space-between;gap:16px;border-bottom:1px solid var(--line);margin-bottom:12px}}
.candidate h3{{font-size:22px;margin:4px 0 12px}}.decision{{color:var(--muted)}}.candidate--selected .decision{{color:var(--accent)}}dl{{display:grid;grid-template-columns:110px 1fr;gap:4px 10px;font-size:12px;color:var(--muted)}}dt{{font-weight:700;color:var(--ink)}}dd{{margin:0;overflow-wrap:anywhere}}.host-proof{{font-size:12px;color:var(--muted)}}
.size-row{{border-top:1px solid var(--line);padding-top:12px;margin-top:14px}}.size-label{{margin-bottom:8px}}.state-row{{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:8px}}
.state-row--service-item,.state-row--labeled-button{{grid-template-columns:1fr}}.state-cell{{min-width:0;min-height:96px;padding:8px;border:1px dashed var(--line);display:flex;flex-direction:column;gap:12px;align-items:flex-start;justify-content:space-between}}
.state-cell--dark{{background:var(--dark);color:var(--light)}}.state-cell--high-contrast{{background:#000;color:#fff;border-color:#fff}}.state-label{{opacity:.68}}
.preview{{font:inherit;color:inherit}}button.preview{{border:1px solid currentColor;background:transparent;min-height:42px;cursor:pointer}}.preview--icon-button{{width:42px;height:42px;padding:0;display:grid;place-items:center}}.preview--icon-button.preview--text-button{{width:auto;padding:8px 12px}}
.preview--labeled-button{{display:inline-flex;align-items:center;gap:8px;padding:8px 12px;font-weight:700;max-width:100%}}.preview--service-item{{display:flex;align-items:center;gap:10px;padding:8px;min-width:0;width:100%}}
.copy{{display:grid;text-align:left;min-width:0}}.copy,.preview--labeled-button>span{{overflow-wrap:anywhere;min-width:0}}.copy small{{color:var(--muted)}}.state-cell--dark .copy small,.state-cell--high-contrast .copy small{{color:inherit;opacity:.75}}
.state--hover{{background:#e6dfd2}}.state--focus{{outline:3px solid #1769e0;outline-offset:2px}}.state--selected{{background:var(--ink);color:var(--light)}}.state--disabled{{opacity:.38;cursor:not-allowed}}
.icon{{width:var(--icon-size);height:var(--icon-size);display:inline-grid;place-items:center;flex:none}}.icon svg{{width:100%;height:100%;display:block}}.sr-only{{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}}
@media(max-width:700px){{main{{padding:24px 14px 50px}}.evidence{{grid-template-columns:1fr}}.state-row--icon-button{{grid-template-columns:repeat(2,minmax(0,1fr))}}dl{{grid-template-columns:90px 1fr}}}}
@media(forced-colors:active){{.candidate--selected{{border:3px solid Highlight;box-shadow:none}}.state--focus{{outline-color:Highlight}}}}
</style></head><body><main><header><span class="eyebrow">Operational icon comparison evidence</span><h1>{title}</h1>
<p class="lede">Every SVG shown here passed deterministic safety, geometry, paint, metadata-schema, and declared-provenance byte-binding checks. Repository-derived context source bytes and declared selectors are bound to the manifest; external source and license truth still require current primary-source verification. Host candidate/state checks are reported separately by browser smoke. The selected outcomes and optical rationales remain human visual judgments from the manifest; this sheet cannot certify recognition or taste.</p>
<div class="evidence"><p><strong>Deterministic contracts</strong><br>Same labels and states; SVG candidates use the same target sizes and structural validator. Declared source/license text is bound to companion metadata, and repository-derived source bytes are digest-bound. No-icon alternatives render once because an icon size does not apply.</p><p><strong>Human visual judgment</strong><br>Silhouette, balance, recognition, family fit, and the selected/rejected outcome. Browser host candidate renders prove technical placement, not the winner.</p></div></header>{''.join(sections)}</main></body></html>'''


def generate_review(manifest_path: str | Path, output_path: str | Path) -> dict[str, Any]:
    manifest = load_review_manifest(manifest_path)
    try:
        output = Path(os.path.abspath(os.fspath(Path(output_path).expanduser())))
    except (TypeError, ValueError, OSError) as error:
        raise ManifestError(f"Output path is invalid: {error}") from error
    _reject_reparse_chain(output.parent, "Output path")
    output.parent.mkdir(parents=True, exist_ok=True)
    _reject_reparse_chain(output, "Output path")
    inputs: list[tuple[str, Path]] = [("manifest", Path(manifest["_path"]))]
    for context in manifest["contexts"]:
        source_file = context.get("context_evidence", {}).get("_source_file")
        if source_file:
            inputs.append((f"context {context['id']} source", Path(source_file)))
        for candidate in context["candidates"]:
            if candidate.get("_asset_file"):
                inputs.append((f"candidate {candidate['id']} asset", Path(candidate["_asset_file"])))
            if candidate.get("_metadata_file"):
                inputs.append((f"candidate {candidate['id']} metadata", Path(candidate["_metadata_file"])))
    for label, input_path in inputs:
        if _paths_alias(output, input_path):
            raise ManifestError(f"Output path must not alias {label}: {output}")
    _atomic_write_text(output, render_review_html(manifest))
    return {
        "manifest": manifest["_path"],
        "output": str(output),
        "contexts": len(manifest["contexts"]),
        "candidates": sum(len(context["candidates"]) for context in manifest["contexts"]),
        "evidence_boundary": "SVG structure, declared metadata, byte-digest binding, repository-derived source digests, and manifest host-proof shape are deterministic; external source/license truth is not independently verified; the sheet is comparison evidence while browser smoke supplies declared host candidate/state/viewport checks; selected/rejected optical outcomes remain manifest-supplied human judgment.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a self-contained representative-control icon candidate comparison sheet")
    parser.add_argument("manifest", help="Path to icon review manifest JSON")
    parser.add_argument("--output", "-o", required=True, help="Output HTML path")
    parser.add_argument("--json", action="store_true", help="Print machine-readable summary")
    args = parser.parse_args()
    try:
        result = generate_review(args.manifest, args.output)
    except (ManifestError, OSError) as error:
        print(f"Icon review generation failed: {error}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"PASS: {result['contexts']} contexts / {result['candidates']} candidates -> {result['output']}")
        print(f"BOUNDARY: {result['evidence_boundary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
