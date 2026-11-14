# Technical Illustration

Use when a page may need a drawn explanation of a system: servers, chips, buildings, data stores or agents joined by flow, usually isometric and often animated. The bundled `iso.py` owns projection, shading, occlusion, routing and label placement; composition stays your judgment.

## Earn Its Place

A technical illustration must explain a system, flow or mechanism that the reader needs before deciding or acting: what connects to what, in which order, and where the active work happens. Write its job with the visual-job sentence in [imagery-and-assets.md](imagery-and-assets.md#decide-whether-a-visual-exists) and compare the page without it. Decoration, a "techy" atmosphere or an empty hero to fill do not count. It is a tool, not a house style: most pages need none, and a short list, a plain diagram or a real product screenshot often explains faster.

## Compose the Scene

- **One focal object** carries the most detail (a chip with die and pins, a platform with an inset): the thing the page is about. Put it at the front, where it is largest and nothing covers it.
- **Three to seven satellites** carry less detail and sit along the real flow, in the order that data or work actually moves. A chevron (flow arriving along +x, leaving along −y) keeps the focal object at the front vertex.
- **Group by role** with shared platforms or spacing, and leave whitespace between groups. Upright cards in a row need about 0.6 grid units between them, or they read as dominoes.
- **Mind hidden arrows.** Flows toward the viewer enter back faces, where arrowheads hide behind the target. Schema 1.1 reroutes automatic sides to a visible face and refuses a hidden marker on an explicit side; under 1.0, choose sides yourself.
- **One level per link.** Connect objects that stand on the same surface, or route on the ground and rise to a port on the face (`route: "ground"`, `to_z`). Route to a platform's side instead of floating a line between heights.

## Keep One System

Per page, keep one projection, one light direction (top lightest, left middle, right darkest), one stroke system (outlines heavier than detail, constant at the rendered size) and one corner language. `style: technical` gives the hairline system: 1 px outlines, finer detail, white tops, soft shadows. Put the page's own icon family (`glyph.py`) on faces with `icon`, so the drawing and the interface share one icon voice. Mixing isometric with dimetric, perspective mockups or flat icons makes the drawing look assembled. Theme through the `--iso-*` custom properties; dark mode redefines the variables and leaves the geometry alone.

## Accent and Labels

Use the accent only for the active path or state: the request being followed, the running agent, the failing link. Everything else stays neutral, so the accent reads as meaning rather than as brand color.

Labels are short nouns of one or two words, set on the faces they name. Keep them at 11 px or more at the size the illustration actually renders, and resolve every label-fit warning by shortening the text or enlarging the object. Explanations belong in the adjacent page text.

## Motion

Animate what changes: flow along connectors, one pulse when a state changes, a stagger by `data-order`. Never add idle spinning or looping decoration. Reduced motion keeps a complete static frame that still shows the active path ([motion-and-interaction.md](motion-and-interaction.md#reduced-motion-is-a-design-variant)), and animation pauses off-screen.

Hook contract: each connector is `g.iso-link` with `data-from`, `data-to`, `data-order` and one `path.iso-path` with `pathLength="1"`, so one dash pattern moves at the same relative speed on every link; append flow dots inside that group so objects in front still cover them. Objects are `g.iso-obj` with `data-role`; `.iso-accent` marks the active path.

```css
.iso-link .iso-path { stroke-dasharray: .05 .04; animation: iso-flow 2.4s linear infinite; }
@keyframes iso-flow { to { stroke-dashoffset: -.09; } }
@media (prefers-reduced-motion: reduce) { .iso-link .iso-path { animation: none; stroke-dasharray: none; } }
```

## Responsive

Do not shrink a wide scene into a phone column: the strokes stay crisp, but the labels and objects become unreadable. At narrow widths, render a separate, simplified scene with the focal object, the active path and two or three satellites, arranged as a staircase that alternates +x and +y so it stays taller than wide. Labels must stay readable at 390 px. Toggle two inline SVGs with a media query, and give each one its own `id_prefix`.

## Accessibility

An informative illustration is an image with a title and a description that state the flow in words; `title` and `desc` in the scene emit `role="img"` and `aria-labelledby`. When adjacent text already carries the same explanation, omit the title so the SVG renders `aria-hidden`, and check that the text exists. Never carry information only in color or motion.

## Workflow

1. Sketch the scene JSON: footprints in grid units, flow order, roles and the one accented path.
2. Render it with `iso.py` ([cli-reference.md](cli-reference.md#draw-an-isometric-illustration)) and fix every refusal and warning.
3. Inspect it at real size, at 1x and 2x and in dark mode: occlusion, crowding, hidden arrows, label legibility and balance.
4. Move coordinates and render again. Keep the scene JSON as the editable source.

## Image Generation

Image generation is optional. When the host offers an image tool, use it only for photographic or painterly assets, under the rules in [imagery-and-assets.md](imagery-and-assets.md#generate-only-when-it-wins). When it does not, draw with code (SVG, CSS 3D or canvas) or use supplied assets. Never block the work, ship a fake placeholder or claim an image exists because a tool is missing. Keep text out of raster images and set it as live text.
