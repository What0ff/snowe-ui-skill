# Technical Illustration

Use when a page may need a drawn explanation of a system: servers, chips, buildings, data stores or agents joined by flow, usually isometric and often animated. The bundled `iso.py` owns projection, shading, occlusion, routing and label placement; composition stays your judgment.

## Earn Its Place

A technical illustration must explain a system, flow or mechanism the reader needs before deciding or acting: what connects to what, in which order, and where the work happens. Write its job with the visual-job sentence and the hero-visual table in [imagery-and-assets.md](imagery-and-assets.md#decide-whether-a-visual-exists), and compare the page without it. It is a tool, not a house style: a short list, a flat diagram or a real product screenshot often explains faster.

## Compose the Scene

- **One focal object** carries the most detail (a populated core, a chip with die and pins) and is the largest mass: the thing the page is about. Put it at the front, uncovered.
- **Three to seven satellites** sit along the real flow, in the order that data or work actually moves. A chevron (flow arriving along +x, leaving along −y) keeps the focal object at the front vertex.
- **Group tight.** Cluster satellites within one or two grid units of the focal object and keep whitespace around the cluster rather than inside it. A satellite that floats several units away reads as a separate picture. Upright cards in a row need about 0.6 grid units between them, or they read as dominoes.
- **Never cut into a platform.** An object in front may hide another's side, never the top of its platform: a monitor covering the edge of a core reads as a collision. 1.3 warns when an object cuts into the top of a slab, tile, core or flat card it does not stand on; move it, stand it on the platform, or declare `attach` when the contact is the point. No overlap may hide a label, port or arrow.
- **One level per link.** Connect objects on the same surface, or route on the ground and rise to a port (`route: "ground"`, `to_z`); flows toward the viewer enter back faces, so leave those ends unmarked.

## Draw Real Objects

Declare `"schema": "1.3"` for new scenes. It draws constructed objects (openings with depth, stepped buildings with lobbies, portals and rooftop plant, tree species built from overlapping volumes, banded databases, folded document stacks, bezelled screens on stands, rack bays) and gives them life:

- **Boards are wired.** Traces leave the package's lead rows in bundles of 3 to 5 at twice the lead pitch, bend only at 45 degrees and end on edge fingers, connector pads or vias, clear of every part and bundle. `detail` adds bundles and parts. Give the core room: a board too small for its package gets short stubs.
- **Buildings are inhabited.** Setbacks become terraces with railings, paving, planters and a parasol; glazing shows ceiling strips, blinds and a few warm lit windows; signage sits small on the entrance canopy or a plaque, so the building's name belongs in a label or page text.
- **Sites are furnished.** A slab carrying a building is paved with a walk to the entrance. Frame the building with tree groups, `hedge` rows and `shrub` clusters; add `street` lamps, benches or bollards sparingly. People are left out: at a 16 px floor a figure is clip-art.

**Recognition test.** Render with `--no-labels` and name every object from its shape alone. A slab you can only identify by its label is a placeholder: give it the features that make it that thing (a monitor's bezel and stand, a database's drum bands, a building's door and floors).

**Scale.** Size everything against the floor height; the generator warns outside these ranges:

| Object | Default | Plausible |
|---|---|---|
| Floor | 0.55 | 0.4–0.75; lobby 1.45 floors |
| Tree | 0.5 wide, 0.8 tall | 1–1.5 floors (0.9–2 accepted) |
| Source tile, agent card | 1.6 × 1.6 × 0.32; 1.0 × 3.2 × 0.42 | at most 1 floor thick and 40% of the largest building footprint |
| Focal core | 4.4 × 4.4 | larger than every tile and card |
| Dashboard | 3.2 × 2 on a 0.3 stand | no taller than the tallest building |

## Keep One System

Per page, keep one projection, one light, one stroke system and one corner language. Put the page's own icon family (`glyph.py`) on faces with `icon`. Mixing isometric with dimetric, perspective mockups or flat icons makes the drawing look assembled.

**Tone.** The light comes from the upper left. In 1.3 tops are lightest, left faces a clear light gray, right faces a denser mid gray; reveals, port walls, holes and the shaded side of canopies go darker still, and glass lies at half opacity over its wall so it follows the face. Keep it airy: light tops, gray sides, the one black accent on the focal object.

**Themes.** Paint resolves through the `--iso-*` custom properties. A 1.3 SVG carries its own dark ramp (same light, lower values, light strokes) through `light-dark()`: a page with `color-scheme: dark` gets it, and `colors` and `dark_colors` override either ramp. Never invert the light ramp for dark mode.

## Accent and Labels

Use the accent only for the active path or state: the request being followed, the running agent, the failing link. Everything else stays neutral, so the accent reads as meaning rather than as brand color.

Labels are short nouns of one or two words, set on the faces they name, and quieter than the drawing: details should carry the image, not text. Keep them at 11 px or more at the size the illustration actually renders and resolve every fit or collision warning. `labels: "upright"` suits square faces. Explanations belong in the adjacent page text.

## Motion

Animate what changes: flow along connectors, one pulse when a state changes, a stagger by `data-order`; never idle spinning. Reduced motion keeps a complete static frame that still shows the active path ([motion-and-interaction.md](motion-and-interaction.md#reduced-motion-is-a-design-variant)); animation pauses off-screen.

Hook contract: each connector is `g.iso-link` with `data-from`, `data-to`, `data-order` and one `path.iso-path` with `pathLength="1"`, so one dash pattern moves at the same relative speed on every link; append flow dots inside that group so objects in front still cover them. Objects are `g.iso-obj` with `data-role`; `.iso-accent` marks the active path.

```css
.iso-link .iso-path { stroke-dasharray: .05 .04; animation: iso-flow 2.4s linear infinite; }
@keyframes iso-flow { to { stroke-dashoffset: -.09; } }
@media (prefers-reduced-motion: reduce) { .iso-link .iso-path { animation: none; stroke-dasharray: none; } }
```

## Responsive

Do not shrink a wide scene into a phone column. Render a separate scene with the focal object, the active path and two or three satellites in a staircase that alternates +x and +y, readable at 390 px. Toggle the two inline SVGs with a media query; give each its own `id_prefix`.

## Accessibility

An informative illustration needs a title and a description that state the flow in words (`title` and `desc` emit `role="img"` and `aria-labelledby`). When adjacent text already explains it, omit the title so the SVG is `aria-hidden`. Never carry information only in color or motion.

## Workflow

1. Sketch the scene JSON: footprints in grid units, flow order, roles and the one accented path.
2. Render it with `iso.py` ([cli-reference.md](cli-reference.md#draw-an-isometric-illustration)) and fix every refusal and warning.
3. Inspect it at real size, at 1x and 2x and in dark mode: occlusion, crowding, tonal weight, label legibility and balance. Compare a 1x crop with the 2x one for muddy detail.
4. Run the recognition test with `--no-labels`.
5. Move coordinates and render again. Keep the scene JSON as the editable source.

## Image Generation

Image generation is optional and only for photographic or painterly assets ([imagery-and-assets.md](imagery-and-assets.md#generate-only-when-it-wins)); never ship a fake placeholder. Keep text out of raster images.
