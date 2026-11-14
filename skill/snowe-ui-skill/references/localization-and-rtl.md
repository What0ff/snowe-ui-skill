# Localization and Right-to-Left

Use when an interface ships in several languages, supports a right-to-left script (Arabic, Hebrew, Persian, Urdu) or other non-Latin scripts, or formats locale data. Font proof for scripts lives in [typography coherence](quality-gates.md#typography-coherence).

## Set Language and Direction

- Put `lang` and `dir` on the root: `<html lang="ar" dir="rtl">`. Use the attribute, not CSS `direction`, so browser, assistive technology and form controls agree.
- Mark embedded languages with their own `lang`; it drives pronunciation, hyphenation and glyph choice (the same Han character differs under `lang="ja"` and `lang="zh"`).
- Isolate text of unknown or opposite direction: `<bdi>` or `dir="auto"` for user content, names and queries; in plain strings such as notifications, wrap the value in U+2068 FSI … U+2069 PDI. Without isolation, a Hebrew name followed by "(3)" in an English sentence renders with the count and parentheses displaced.
- Keep phone numbers, codes, URLs and email addresses left-to-right inside RTL text (`dir="ltr"` on the span or input).

## Use Logical Properties

| Physical | Logical |
|---|---|
| `margin-left`, `margin-right` | `margin-inline-start`, `margin-inline-end` |
| `padding-left`, `padding-right` | `padding-inline-start`, `padding-inline-end` |
| `left`, `right` | `inset-inline-start`, `inset-inline-end` |
| `text-align: left` | `text-align: start` |
| `border-top-left-radius` | `border-start-start-radius` |
| `width`, `height` (if writing mode can change) | `inline-size`, `block-size` |

Flex and grid follow `dir`; do not fake RTL with `row-reverse`. Transforms, `background-position`, shadow offsets and animation directions do not flip: override them under `:dir(rtl)`. Tailwind offers `ms-`, `me-`, `ps-`, `pe-`, `start-`, `end-` and the `rtl:` variant.

## Mirror by Meaning

| Mirror in RTL | Keep unmirrored |
|---|---|
| Layout and reading order: navigation, sidebars, columns | Media playback controls (play, rewind, fast-forward) |
| Back and forward arrows, chevrons, breadcrumb separators | Clocks and icons showing clockwise motion |
| Directional icons: send, reply, undo and redo, indent | Checkmarks |
| Progress bars, sliders, steppers, carousels and swipe order | Logos, brand marks, photos and real-world objects |
| | Digits; glyphs containing letters are localized, not mirrored |

Flag directional icons in the icon registry and flip them with `transform: scaleX(-1)` under `:dir(rtl)`. Then read the RTL render right to left: title, content, action.

## Fit Longer Text

- Allow 30–40% expansion over English; short labels grow more ("Save" becomes "Speichern"). Let buttons, tabs and headers size to content and allow two-line labels; never fix a translated control's width.
- Test with pseudo-localization (accents, about 40% padding, bracket markers such as `[Šàvé ····]`), then the longest real language and an RTL language.
- Never concatenate fragments ("You have " + n + " items"); word order differs. Use full messages with placeholders, such as ICU MessageFormat.
- Keep text out of images; if unavoidable, ship one image per locale with localized alt text.
- Truncate with CSS `text-overflow: ellipsis`, which follows direction, and expose the full value on focus or in detail. Code that must cut uses `Intl.Segmenter`, never a character count, which splits combining marks and emoji. Never truncate names, amounts or the primary action.
- Do not require separate first and last names or one address format.

## Scripts and Fonts

- Give scripts with tall stacks and diacritics (Arabic, Devanagari, Thai) a line height of about 1.6–1.8, and avoid fixed text heights that clip marks. CJK body text also reads well near 1.6–1.8.
- Arabic and Devanagari often need one size step above Latin to match its apparent size. Never letter-space connected scripts such as Arabic; it breaks joining. CJK has no true italic; emphasize with weight or color.
- Cover every required script with the chosen family, or assign per-script faces via `unicode-range` or `:lang()`, each with its own fallback stack. No glyph may render as a missing-character box.

## Format With `Intl`

| Data | API | What varies |
|---|---|---|
| Numbers | `Intl.NumberFormat` | 1,234.5 (en-US) or 1.234,5 (de-DE); some Arabic locales use Arabic-Indic digits |
| Currency | `Intl.NumberFormat`, `style: "currency"` | Symbol position and decimals (JPY has none); the currency comes from the data, not the viewer |
| Dates and times | `Intl.DateTimeFormat` with `dateStyle`, `timeStyle` | Field order (03/04 is ambiguous), 12- or 24-hour clock; state the time zone |
| Relative time | `Intl.RelativeTimeFormat` | "in 3 days", "vor 3 Tagen" |
| Plurals | `Intl.PluralRules` or ICU messages | English has 2 categories, Polish 4, Arabic 6 |
| Sorting | `Intl.Collator` | "ä" sorts with "a" in German, after "z" in Swedish |

Weeks start on Monday in most of Europe, Sunday in the United States and Saturday in parts of the Middle East; take it from locale data. Name languages in their own language ("Deutsch", "العربية"), not with flags.

## Check

- Root `lang` and `dir` are set; user content and mixed-direction strings are isolated.
- Layout uses logical properties; an RTL render mirrors directional icons but not media controls, clocks, checkmarks or logos.
- Pseudo-localized and longest-language renders show no clipping, overlap or hidden primary action at narrow width.
- Every script renders in its intended face, without missing glyphs or clipped marks.
- Numbers, dates, currency and plurals use `Intl`; no concatenated sentences or text in images remain.
