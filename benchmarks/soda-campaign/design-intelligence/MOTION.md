# Doppler Soda — Motion Architecture

## Motion job

Time must establish Doppler as a pressurized physical soda, preserve one can across flavor changes, and make direct manipulation feel causal. It must not delay category comprehension, hide actions, or become a page-wide ambient layer.

## Technology comparison and selection

The visual job was defined before technology. A dependency-free hybrid won:

- **HTML/CSS 3D:** segmented cylindrical label, shadow, specular light, condensation, entrance, drag rotation, and responsive geometry. One screen-aligned aluminum top rim masks the rotating panel edge while its small lid hardware tracks yaw; this avoids unreliable cross-plane occlusion without faking a second package surface.
- **Local SVG:** precise editable package textures shared by animated and static cans.
- **Small JavaScript state machine:** interruption-safe rotation, flavor state, finite bubble construction, navigation focus, and pack-builder feedback.
- **DOM/CSS fizz:** one finite pressure release rather than perpetual canvas work.

Canvas was unnecessary because a finite bubble family can be composited by the browser without a frame loop. WebGL would materially improve shader lighting but not the required product/category/flavor/action hierarchy enough to justify a renderer, model pipeline, and separately maintained fallback. Video/frame sequences fail direct flavor manipulation and responsive crop ownership.

## Event model

### M1 — Product establishment

```text
trigger: document ready with no reduced-motion preference
before -> after: front-recognizable static layout -> elevated/rotated physical can at rest
information: package is cylindrical aluminum under pressure; Doppler's signal compresses around it
hierarchy/focus: copy and controls are usable immediately; motion remains behind/alongside them
frequency/control: once per page load; pointer input immediately cancels the authored entrance
continuity: can rises on its vertical axis, rotates around its cylinder, settles into contact shadow
choreography: 900 ms can arrival + finite 1.6 s fizz release; no loop
interruption: pointerdown/flavor selection removes intro state and starts from current computed orientation
cost: transform/opacity composites; finite DOM bubbles removed/hidden after completion
reduced/static: already-composed front can, fixed arcs, no travel/fizz/rotation
reject: product/category unavailable during animation, broken rim axis, exhausting replay, or active reduced animation
```

### M2 — Direct can rotation

```text
trigger: horizontal pointer drag on the product stage
before -> after: current yaw -> yaw proportional to horizontal travel
information: label wraps one physical container; product can be inspected
hierarchy/focus: no content or action moves; cursor/touch hint reports optional manipulation
frequency/control: user-controlled, reversible; flavor buttons remain equivalent
continuity: cylinder rotates around fixed vertical axis with bounded release easing
interruption: new pointer takes ownership; pointercancel stops safely; vertical touch remains page scroll
cost: one transform update per animation frame only during active drag/short release
reduced/static: drag disabled; flavor buttons update the front face directly
reject: scroll hijack, unbounded spin, text selection, input latency, or mechanical wobble
```

### M3 — Flavor signal change

```text
trigger: named flavor button, keyboard activation, or pack-row product shortcut
before -> after: selected flavor/copy/color/label A -> selected state B plus one bounded product revolution
information: a flavor change is the same product receiving a different signal/label
hierarchy/focus: activated button keeps focus and aria-pressed; polite live status names the new blend
frequency/control: repeatable and reversible
continuity: label, field, copy, and selected controls update directly; the same can then completes one controlled revolution and settles front-facing at a yaw divisible by 360 degrees
interruption: latest selection wins; stale completion timer is cancelled
cost: one bounded can transform plus short color/poster-opacity transitions; no layout animation or persistent frame loop
reduced/static: immediate label/color/copy update with a short opacity confirmation only
reject: state is ambiguous without color/motion, focus changes, rapid input shows stale content, or action waits for choreography
```

### M4 — Mobile navigation

```text
trigger: native menu button at narrow width
before -> after: collapsed links -> visible section panel
information: destination availability and open/closed state
hierarchy/focus: first link receives focus; Escape/outside/link close restores trigger as appropriate
frequency/control: frequent, restrained 160 ms opacity/vertical continuity
reduced/static: immediate visibility change; focus behavior identical
reject: focus escapes into hidden links, body overflow locks incorrectly, or transition delays navigation
```

### M5 — Six-pack confirmation

```text
trigger: quantity adjustment or Add this mix
before -> after: valid six-count state / pending message -> local success state
information: quantities, remaining/excess count, and fictional demo completion
hierarchy/focus: button remains focus owner; role=status announces concise result
frequency/control: direct and repeatable
continuity: quantity/slot fill changes immediately; success mark receives a short scale/opacity response
reduced/static: immediate text/icon state with no scale travel
reject: quantity can exceed constraints silently, success impersonates payment, or feedback is animation-only
```

## Role boundaries

- Expressive: M1 and user-owned M2 only.
- Functional: M3–M5; short, local, and non-blocking.
- Still: long-form copy, product facts, flavor descriptions, ingredients/sensory sequence, footer, and routine hover outside direct affordance feedback.
- Deliberately omitted: global scroll reveals, looping particles, autoplay rotation, parallax sections, text-marquee loops, scroll hijack, and animation on every card/heading.

## Performance and lifecycle

- No runtime dependency, model, video, remote media, or persistent canvas loop.
- Layout reserves the product stage before JS and font completion.
- Pointer rendering starts only during active manipulation and stops after a bounded release.
- Intro bubbles are finite, hidden after completion, fewer at pressure/narrow widths, and absent in reduced mode.
- `visibilitychange`, viewport change, pointer cancellation, and preference changes stop transient work and commit a stable final state.
- JS/media failure leaves a front-facing static can, content, anchors, flavor names, and a valid initial six-pack visible.

## Reduced-motion composition

Reduced mode is selected by `prefers-reduced-motion: reduce`, not by a user-facing intensity control. It removes the 3D entrance, rotation, fizz travel, pointer tilt, release easing, and spatial navigation motion. A separate front-facing can surface preserves aluminum silhouette, selected label, static pressure arcs, flavor color, category, and condensation details. Flavor buttons still update text, package face, button state, pack relationship, and live status directly; the CTA and conversion path are unchanged.
