# Bundled catalog manifest

Last reviewed: 2026-11-12.

These CSV files are subordinate lexical evidence for explicitly requested lookups (`search.py --domain` or `--stack`). They do not classify a brief or choose layout, style, palette, typography, imagery, or motion. A row is a prompt to verify, not current truth.

`Rows` excludes the header. `Imported` is the date the file entered this repository; `Edited` is the latest content review. `No` values are stable row ids: removed rows leave gaps. `tests/test_catalogs.py` fails when a bundled CSV is missing from this table or its row count differs.

## Provenance

Most catalogs derive from the MIT-licensed [UI UX Pro Max skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) by Next Level Builder. That repository's history does not record which upstream commit was imported on 2026-08-10. On 2026-11-12 the files were compared with upstream `main` at `6ae86f61f520d6ca229d2f40e070410638c908c5` (2026-11-10): matching row names confirm the lineage noted below. Upstream does not record primary sources for its rows, so their original sources remain unknown unless a row carries its own URL or standard reference. Snowe has since deleted recipe columns and rows, rewritten rows against primary documentation, and added rows; those edits are Snowe's.

| Catalog | Rows | Source | Imported | Edited | License / notice |
|---|---:|---|---|---|---|
| `products.csv` | 192 | UI UX Pro Max `products.csv`; reduced to `Product Type` and `Keywords`; operations vocabulary added to rows 49, 102, 166, and 188 | 2026-08-10 | 2026-11-12 | MIT, Next Level Builder (notice below) |
| `google-fonts.csv` | 1961 | Rebuilt from the public Google Fonts metadata endpoint (`https://fonts.google.com/metadata/fonts`, fetched 2026-11-12, latest family update 2026-11-11); `License` from the google/fonts repository directory (`ofl`, `apache`, `ufl`) at tree `910961aa534362dcbdab88b83bd093bf978a6f44`, `unresolved` for 6 families whose directory names differ. Replaces the UI UX Pro Max keyword snapshot | 2026-08-10 | 2026-11-12 | Factual metadata; each family's own license is in its `License` column |
| `ux-guidelines.csv` | 91 | UI UX Pro Max `ux-guidelines.csv`; rows rewritten against WCAG 2.2 and platform guidance where cited; row 100 added from Nielsen Norman Group (2022) | 2026-08-10 | 2026-11-12 | MIT, Next Level Builder (notice below) |
| `app-interface.csv` | 30 | UI UX Pro Max `app-interface.csv` (iOS, Android, React Native) | 2026-08-10 | 2026-11-12 | MIT, Next Level Builder (notice below) |
| `react-performance.csv` | 44 | UI UX Pro Max `react-performance.csv`; upstream's own sources are not recorded | 2026-08-10 | 2026-08-10 | MIT, Next Level Builder (notice below) |
| `charts.csv` | 25 | UI UX Pro Max `charts.csv`; recipe columns deleted and accessibility notes rewritten against WCAG 2.2 | 2026-08-10 | 2026-11-12 | MIT, Next Level Builder (notice below) |
| `icons.csv` | 104 | UI UX Pro Max `icons.csv` (legacy familiar-action names) | 2026-08-10 | 2026-11-12 | MIT, Next Level Builder (notice below); icon artwork licenses belong to each icon library |
| `icon-families.csv` | 10 | Snowe-authored; `License` and `Official URL` per row | 2026-08-10 | 2026-08-10 | Repository MIT license; icon libraries keep their own licenses |
| `icon-concepts.csv` | 21 | Snowe-authored role and metaphor prompts | 2026-08-10 | 2026-08-10 | Repository MIT license |
| `icon-candidates.csv` | 70 | Snowe-authored; `Verified Version` and `Official URL` per row | 2026-08-10 | 2026-08-10 | Repository MIT license; icon libraries keep their own licenses |
| `stacks/angular.csv` | 50 | UI UX Pro Max stack catalog | 2026-08-10 | 2026-08-10 | MIT, Next Level Builder (notice below) |
| `stacks/astro.csv` | 53 | UI UX Pro Max stack catalog | 2026-08-10 | 2026-08-10 | MIT, Next Level Builder (notice below) |
| `stacks/avalonia.csv` | 56 | UI UX Pro Max stack catalog | 2026-08-10 | 2026-08-10 | MIT, Next Level Builder (notice below) |
| `stacks/flutter.csv` | 52 | UI UX Pro Max stack catalog; superseded APIs rewritten against docs.flutter.dev | 2026-08-10 | 2026-11-12 | MIT, Next Level Builder (notice below) |
| `stacks/html-tailwind.csv` | 55 | UI UX Pro Max stack catalog | 2026-08-10 | 2026-08-10 | MIT, Next Level Builder (notice below) |
| `stacks/javafx.csv` | 75 | UI UX Pro Max stack catalog | 2026-08-10 | 2026-08-10 | MIT, Next Level Builder (notice below) |
| `stacks/jetpack-compose.csv` | 43 | UI UX Pro Max stack catalog; rewritten against developer.android.com, unverifiable rows deleted | 2026-08-10 | 2026-11-12 | MIT, Next Level Builder (notice below) |
| `stacks/laravel.csv` | 50 | UI UX Pro Max stack catalog | 2026-08-10 | 2026-08-10 | MIT, Next Level Builder (notice below) |
| `stacks/nextjs.csv` | 52 | UI UX Pro Max stack catalog | 2026-08-10 | 2026-08-10 | MIT, Next Level Builder (notice below) |
| `stacks/nuxt-ui.csv` | 70 | UI UX Pro Max stack catalog | 2026-08-10 | 2026-08-10 | MIT, Next Level Builder (notice below) |
| `stacks/nuxtjs.csv` | 58 | UI UX Pro Max stack catalog | 2026-08-10 | 2026-08-10 | MIT, Next Level Builder (notice below) |
| `stacks/react-native.csv` | 51 | UI UX Pro Max stack catalog | 2026-08-10 | 2026-08-10 | MIT, Next Level Builder (notice below) |
| `stacks/react.csv` | 53 | UI UX Pro Max stack catalog | 2026-08-10 | 2026-08-10 | MIT, Next Level Builder (notice below) |
| `stacks/shadcn.csv` | 60 | UI UX Pro Max stack catalog | 2026-08-10 | 2026-08-10 | MIT, Next Level Builder (notice below) |
| `stacks/svelte.csv` | 53 | UI UX Pro Max stack catalog | 2026-08-10 | 2026-08-10 | MIT, Next Level Builder (notice below) |
| `stacks/swiftui.csv` | 50 | UI UX Pro Max stack catalog; Observation and deprecated APIs rewritten against developer.apple.com | 2026-08-10 | 2026-11-12 | MIT, Next Level Builder (notice below) |
| `stacks/threejs.csv` | 53 | UI UX Pro Max stack catalog | 2026-08-10 | 2026-08-10 | MIT, Next Level Builder (notice below) |
| `stacks/uno.csv` | 59 | UI UX Pro Max stack catalog | 2026-08-10 | 2026-08-10 | MIT, Next Level Builder (notice below) |
| `stacks/vue.csv` | 49 | UI UX Pro Max stack catalog | 2026-08-10 | 2026-08-10 | MIT, Next Level Builder (notice below) |
| `stacks/winui.csv` | 61 | UI UX Pro Max stack catalog; rows 60-61 folded from the retired `uwp.csv` and rewritten against Microsoft Learn | 2026-08-10 | 2026-11-12 | MIT, Next Level Builder (notice below) |
| `stacks/wpf.csv` | 56 | UI UX Pro Max stack catalog | 2026-08-10 | 2026-08-10 | MIT, Next Level Builder (notice below) |

Retired: `stacks/uwp.csv` (UI UX Pro Max lineage, 55 rows) was deleted on 2026-11-12; `--stack uwp` returns an error naming `winui`.

## Third-party notice

The catalogs marked above contain material derived from UI UX Pro Max, distributed under this license:

```text
MIT License

Copyright (c) 2024 Next Level Builder

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
