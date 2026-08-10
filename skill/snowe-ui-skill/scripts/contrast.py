#!/usr/bin/env python3
"""Deterministic contrast checks for exact opaque CSS colors.

Rendered gradients, images, opacity, blending, filters, video, and state
transitions still require contextual measurement. This helper intentionally
does not convert an example palette into a design selection.
"""

from __future__ import annotations

import argparse
import json
import re
from typing import Iterable


_HEX = re.compile(r"^#(?P<value>[0-9a-f]{3}|[0-9a-f]{6})$", re.IGNORECASE)
_RGB = re.compile(
    r"^rgb\(\s*(?P<r>\d{1,3})\s*[, ]\s*(?P<g>\d{1,3})\s*[, ]\s*(?P<b>\d{1,3})\s*\)$",
    re.IGNORECASE,
)


def parse_opaque_color(value: str) -> tuple[int, int, int]:
    """Parse #RGB, #RRGGBB, rgb(r,g,b), black, or white."""
    text = str(value or "").strip().casefold()
    named = {"black": (0, 0, 0), "white": (255, 255, 255)}
    if text in named:
        return named[text]
    hex_match = _HEX.fullmatch(text)
    if hex_match:
        raw = hex_match.group("value")
        if len(raw) == 3:
            raw = "".join(character * 2 for character in raw)
        return tuple(int(raw[index : index + 2], 16) for index in (0, 2, 4))
    rgb_match = _RGB.fullmatch(text)
    if rgb_match:
        channels = tuple(int(rgb_match.group(channel)) for channel in ("r", "g", "b"))
        if any(channel > 255 for channel in channels):
            raise ValueError(f"RGB channel outside 0..255: {value}")
        return channels
    raise ValueError(
        f"Unsupported or non-opaque color {value!r}; use #RGB, #RRGGBB, rgb(r,g,b), black, or white"
    )


def _linear_channel(channel: int) -> float:
    normalized = channel / 255
    return normalized / 12.92 if normalized <= 0.04045 else ((normalized + 0.055) / 1.055) ** 2.4


def relative_luminance(value: str | tuple[int, int, int]) -> float:
    red, green, blue = parse_opaque_color(value) if isinstance(value, str) else value
    return 0.2126 * _linear_channel(red) + 0.7152 * _linear_channel(green) + 0.0722 * _linear_channel(blue)


def contrast_ratio(foreground: str, background: str) -> float:
    light, dark = sorted(
        (relative_luminance(foreground), relative_luminance(background)), reverse=True
    )
    return (light + 0.05) / (dark + 0.05)


def check_contrast(foreground: str, background: str, minimum: float = 4.5) -> dict[str, object]:
    ratio = contrast_ratio(foreground, background)
    return {
        "foreground": foreground,
        "background": background,
        "ratio": round(ratio, 3),
        "minimum": minimum,
        "status": "PASS" if ratio >= minimum else "FAIL",
        "scope": "exact opaque color pair only",
    }


def best_foreground(
    background: str,
    candidates: Iterable[str] = ("#000000", "#FFFFFF"),
    minimum: float = 4.5,
) -> dict[str, object]:
    ranked = sorted(
        ((contrast_ratio(candidate, background), candidate) for candidate in candidates),
        reverse=True,
    )
    if not ranked:
        raise ValueError("At least one foreground candidate is required")
    _ratio, foreground = ranked[0]
    result = check_contrast(foreground, background, minimum)
    result["alternatives_checked"] = len(ranked)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Measure contrast for one exact opaque foreground/background pair"
    )
    parser.add_argument("foreground")
    parser.add_argument("background")
    parser.add_argument("--minimum", type=float, default=4.5)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = check_contrast(args.foreground, args.background, args.minimum)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(
            f"{result['status']}: {result['foreground']} on {result['background']} "
            f"= {result['ratio']}:1 (minimum {result['minimum']}:1; {result['scope']})"
        )
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
