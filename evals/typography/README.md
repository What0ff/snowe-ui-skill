# Declared typography roles

`goodturn.json` records accepted role metrics separately from browser observations. Values were inspected against the existing CSS and native rendered baseline, then committed as expectations; smoke never regenerates them from the page under test.

The contract covers display/body text, repeated card titles, filter and purchase actions, desktop/mobile navigation, booking fields/select and open dialog text. Each role declares state, applicable width range, family, weight, style, line-height ratio, tracking in em and variable settings. Font files are hash-bound and their CSS face declarations are checked. Internal face names are explicitly separate from CSS aliases and requested weights.

Browser mutations exercise family, weight 400→800, italic, line-height, tracking, variable settings and mixed-script fallback. Metrics tolerate only small CSS rounding (0.01 line-height ratio, 0.001em tracking). These checks protect accepted roles and file/face mapping; they do not choose a font pairing or infer aesthetics from a face count. Loading/paint settling precedes glyph inspection. Dialog field probes are isolated from the independent interaction suite by navigation.
