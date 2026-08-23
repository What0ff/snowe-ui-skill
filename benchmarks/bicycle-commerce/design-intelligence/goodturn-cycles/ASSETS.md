# Image and Custom-Asset Record

## Generated imagery

Built-in image generation was used for bitmap-native photography. Final files were converted to WebP and placed under `assets/images/`; source generations remain in Codex’s generated-image store.

| File | Job | In-layout requirement |
|---|---|---|
| `goodturn-hero.webp` | Prove human scale, upright city use, and desirability. | Rider/bicycle stay credible at wide, pressure, and 4:3 narrow crops; calm wall does not become empty filler. |
| `turn-one.webp` | Inspect the lightweight diamond-frame commuter. | Both wheels, rack, belt/drivetrain, fenders, and frame remain visible. |
| `turn-step.webp` | Inspect step-through access and everyday carrying. | Step-through geometry, basket, rack, lighting, and full wheels remain legible. |
| `turn-cargo.webp` | Inspect longtail load capacity. | Extended rack, supported crate, stand, drivetrain, and wheel geometry remain credible. |

All prompts prohibited text, logos, trademarks, additional subjects, and mechanically impossible bicycle artifacts. The benchmark explicitly labels the products and generated imagery as fictional concept content.

## Custom symbol family

```text
role: service evidence and Goodturn orientation
grid: 24 × 24; live area generally 2..22 with curve overshoot
mode: monochrome stroke; currentColor
stroke: 1.75; round caps/joins; small mechanical corners
primitives: wheels/circles, measured verticals, route turns, open tool geometry
detail budget: one primary object plus at most one semantic modifier at 16px
target sizes: 16, 20, 24, 28, and the implemented 32px service display
accessibility: owning labeled component; SVG decorative
```

The family must pass `asset_quality.py`, then be reviewed beside real labels and controls. A passing SVG result is not optical acceptance.

The fit, test-route, and workshop symbols remain repository-owned custom drawings. The former custom cargo/delivery glyph was rejected for `Right-ride exchange`: its crate-and-wheels silhouette described delivery, not exchange. The pinned Lucide `Repeat 2` glyph won at the real 32px service-card size and at 16/20/24px because its opposing directional paths preserve the familiar exchange metaphor. Its exact upstream source, SHA-256 binding, and ISC notice are stored beside `exchange.svg`. This external exception is intentionally not relabeled as custom work.
