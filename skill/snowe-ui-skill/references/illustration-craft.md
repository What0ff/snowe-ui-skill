# Technical Illustration

Use when a page may need a drawn explanation of a system: servers, chips, buildings, data stores or agents joined by flow, usually isometric and often animated. The bundled `iso.py` owns projection, shading, occlusion, routing and label placement; composition stays your judgment.

## Earn Its Place

A technical illustration must explain a system, flow or mechanism the reader needs before deciding or acting: what connects to what, in which order, and where the work happens. Write its job with the visual-job sentence and the hero-visual table in [imagery-and-assets.md](imagery-and-assets.md#decide-whether-a-visual-exists), and compare the page without it. Decoration or an empty hero to fill do not count. It is a tool, not a house style: a short list, a flat diagram or a real product screenshot often explains faster.

## Compose the Scene

- **One focal object** carries the most detail (a populated core, a chip with die and pins) and is the largest mass: the thing the page is about. Put it at the front, uncovered.
- **Three to seven satellites** sit along the real flow, in the order that data or work actually moves. A chevron (flow arriving along +x, leaving along −y) keeps the focal object at the front vertex.
- **Group tight.** Cluster satellites within one or two grid units of the focal object, let groups touch or partly overlap (a site plaza against the core, a screen in front of its corner), and keep whitespace around the cluster rather than inside it. A satellite that floats several units away reads as a separate picture. Overlaps may hide geometry, never a label, port or arrow: the 1.2 collision check warns when one does. Upright cards in a row need about 0.6 grid units between them, or they read as dominoes.
- **Mind hidden markers.** Flows toward the viewer enter back faces. Since 1.1, automatic sides reroute to a visible face and a hidden marker on an explicit side is refused; an unmarked end may plug into a back face.
- **One level per link.** Connect objects on the same surface, or route on the ground and rise to a port (`route: "ground"`, `to_z`).

## Draw Real Objects

Declare `"schema": "1.2"` for new scenes. It draws constructed objects: openings with depth, stepped buildings with lobbies, portals, parapets and rooftop plant, tree species built from overlapping volumes, populated boards (`detail`), banded databases, folded document stacks, bezelled screens on stands and rack bays.

**Recognition test.** Render with `--no-labels` and name every object from its shape alone. A slab you can only identify by its label is a placeholder: give it the features that make it that thing (a monitor's bezel and stand, a database's drum bands, a document's folded corner, a card's socket port, a building's door and floors).

**Scale.** Size everything against the floor height; 1.2 warns when a scene leaves these ranges:

| Object | Default | Plausible |
|---|---|---|
| Floor | 0.55 | 0.4–0.75; lobby 1.45 floors |
| Tree | 0.5 wide, 0.8 tall | 1–1.5 floors (0.9–2 accepted) |
| Source tile, agent card | 1.6 × 1.6 × 0.32; 1.0 × 3.2 × 0.42 | at most 1 floor thick and 40% of the largest building footprint |
| Focal core | 4.4 × 4.4 | larger than every tile and card |
| Dashboard | 3.2 × 2 on a 0.3 stand | no taller than the tallest building |

## Keep One System

Per page, keep one projection, one light direction (top lightest, left middle, right darkest), one stroke system and one corner language. `style: technical` gives the hairline system; in 1.2 every stroke is at least 1 px, detail differs from outlines by tone, and vertical hairlines snap to pixel centers so the 1x render stays crisp. Put the page's own icon family (`glyph.py`) on faces with `icon`. Mixing isometric with dimetric, perspective mockups or flat icons makes the drawing look assembled. Theme through the `--iso-*` custom properties; dark mode redefines only the variables.

## Accent and Labels

Use the accent only for the active path or state: the request being followed, the running agent, the failing link. Everything else stays neutral, so the accent reads as meaning rather than as brand color.

Labels are short nouns of one or two words, set on the faces they name, and quieter than the drawing: details should carry the image, not text. Keep them at 11 px or more at the size the illustration actually renders and resolve every fit or collision warning. `labels: "upright"` sets them unsheared for crisper 1x text on square faces; long or tilted faces keep face labels. Explanations belong in the adjacent page text.

## Motion

Animate what changes: flow along connectors, one pulse when a state changes, a stagger by `data-order`; never idle spinning. Reduced motion keeps a complete static frame that still shows the active path ([motion-and-interaction.md](motion-and-interaction.md#reduced-motion-is-a-design-variant)); animation pauses off-screen.

Hook contract: each connector is `g.iso-link` with `data-from`, `data-to`, `data-order` and one `path.iso-path` with `pathLength="1"`, so one dash pattern moves at the same relative speed on every link; append flow dots inside that group so objects in front still cover them. Objects are `g.iso-obj` with `data-role`; `.iso-accent` marks the active path.

```css
.iso-link .iso-path { stroke-dasharray: .05 .04; animation: iso-flow 2.4s linear infinite; }
@keyframes iso-flow { to { stroke-dashoffset: -.09; } }
@media (prefers-reduced-motion: reduce) { .iso-link .iso-path { animation: none; stroke-dasharray: none; } }
```

## Responsive

Do not shrink a wide scene into a phone column: labels and objects become unreadable. Render a separate scene with the focal object, the active path and two or three satellites in a staircase that alternates +x and +y, readable at 390 px. Toggle the two inline SVGs with a media query; give each its own `id_prefix`.

## Accessibility

An informative illustration needs a title and a description that state the flow in words (`title` and `desc` emit `role="img"` and `aria-labelledby`). When adjacent text already explains it, omit the title so the SVG is `aria-hidden`. Never carry information only in color or motion.

## Workflow

1. Sketch the scene JSON: footprints in grid units, flow order, roles and the one accented path.
2. Render it with `iso.py` ([cli-reference.md](cli-reference.md#draw-an-isometric-illustration)) and fix every refusal and warning.
3. Inspect it at real size, at 1x and 2x and in dark mode: occlusion, crowding, hidden markers, label legibility and balance. Compare a 1x crop with the 2x one: muddy 1x detail means too many sub-pixel features.
4. Run the recognition test with `--no-labels`.
5. Move coordinates and render again. Keep the scene JSON as the editable source.

## Image Generation

Image generation is optional and only for photographic or painterly assets ([imagery-and-assets.md](imagery-and-assets.md#generate-only-when-it-wins)). Without a tool, draw with code or use supplied assets; never ship a fake placeholder. Keep text out of raster images.
