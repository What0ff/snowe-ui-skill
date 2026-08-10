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
target sizes: 16, 20, 24, and 28px service display
accessibility: owning labeled component; SVG decorative
```

The family must pass `asset_quality.py`, then be reviewed beside real labels and controls. A passing SVG result is not optical acceptance.
