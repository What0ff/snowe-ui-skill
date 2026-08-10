# Motion and Interaction

Use this reference when state change, transition, feedback, spatial continuity, gesture, scroll, or storytelling may benefit from time. Motion is a carrier of information and character, not a required polish layer.

## Begin With the Static Truth

Make the outcome, hierarchy, controls, state, progress, and recovery understandable without animation. Then ask what information becomes clearer through time:

- cause and effect;
- continuity between locations or states;
- origin, destination, ownership, or spatial relationship;
- progress, completion, interruption, or failure;
- hierarchy and attention at a meaningful moment;
- direct-manipulation feedback;
- a story whose sequence matters;
- brand character that earns its repetition.

If motion carries none of these, omit it. A static experience can be the most expressive or professional answer.

## Model Events Before Effects

For each consequential transition, record:

```text
trigger and input mode
before state -> after state
information motion must carry
affected hierarchy and focus
frequency and user control
spatial model or continuity rule
enter / change / exit choreography
interruption, reversal, and rapid-repeat behavior
runtime and media cost
reduced-motion and static equivalent
reject condition
```

This model may resolve to an immediate state change. Do not start from a library demo or global intensity dial.

## Choose a Motion Posture

Compare only postures that express a live trade-off:

- **Immediate/static:** frequent tools, high urgency, already-obvious state changes, strict performance budgets, or contexts where animation impedes scanning.
- **Functional continuity:** state change, overlay origin, hierarchy, reordering, navigation, or feedback needs clarification.
- **Expressive sequence:** launch, campaign, editorial, product story, creative tool, or spatial experience where time is an intentional identity carrier.

One product can use different postures by role. Keep frequent controls immediate while a rare storytelling moment is expressive. Document the boundary.

## Derive a Motion Grammar

Make timing and movement feel caused by the interface:

- derive direction from source and destination rather than arbitrary entrance sides;
- relate duration to distance, complexity, and frequency rather than one global value;
- use easing to describe acceleration, arrival, resistance, or physical connection;
- stagger only when sequence or grouping is meaningful;
- preserve object identity across transitions when continuity matters;
- use opacity, transform, clipping, scale, blur, or shape change only when each supports the state model;
- keep feedback close to the action and do not delay task completion for choreography;
- avoid simultaneous motion in competing regions unless the relationship is the point.

Motion coherence means shared mechanics and role logic, not identical duration everywhere.

## Interaction Quality

- Preserve native semantics, keyboard operation, focus order, activation behavior, labels, selection, and error recovery.
- Show hover only as an enhancement; do not hide essential information or actions behind it.
- Make pressed, drag, drop, reorder, zoom, pan, swipe, and scrub behavior reversible or safely recoverable where users can make costly mistakes.
- Keep focus synchronized with modal, route, disclosure, and removal transitions. Do not animate focus into a disappearing node.
- Provide a clear result for interrupted, cancelled, rapid, repeated, and concurrent input.
- Avoid scroll hijacking. Scroll-linked motion must preserve navigation, reading position, input responsiveness, and direct user control.
- Do not make a gesture the only path to an essential action.

## Reduced Motion Is a Design Variant

Respect platform and browser motion preferences. Replace or simplify motion according to the information it carries:

- remove decorative travel, parallax, looping, zoom, spin, and large spatial movement;
- use an immediate update, short opacity/state transition, or static before/after cue when some feedback remains useful;
- preserve content, state, focus, and task completion;
- avoid autoplay movement that cannot be paused when it distracts or affects comprehension.

Do not treat reduced motion as merely setting every duration to zero; that can erase feedback or break event assumptions. Test it as a complete state.

## Responsive and Input Adaptation

Motion may need a different model when navigation, composition, input, or content order changes. Check:

- touch versus pointer/keyboard feedback;
- small-screen overlays versus wide-screen adjacent panels;
- reflow/reorder continuity at pressure widths;
- orientation and viewport changes;
- coarse-pointer targets and gesture conflicts;
- low-power, low-bandwidth, background-tab, and interrupted rendering behavior.

The responsive transformation may remove an animation because its spatial premise no longer exists.

## Implementation and Performance

- Prefer platform-native or compositor-friendly mechanisms when they express the design.
- Avoid animating layout properties on large or frequently changing regions when transform/opacity or an immediate update is sufficient.
- Reserve space for media and animated regions to prevent unintended layout shifts.
- Load animation libraries only when selected behavior justifies their weight and the repository accepts the dependency.
- Stop observers, timelines, video, canvas, and event work when offscreen, hidden, destroyed, or reduced.
- Maintain final state and control usability when scripts, media, or animation fail.

Performance traces and frame stability are evidence; a smooth demo on one machine is not.

## Rendered Comparison

Compare the static/reduced baseline with the motion candidate in the implemented interface. Review normal speed and repeated use; slow playback can diagnose mechanics but is not the user experience.

Mark motion `REJECT` when it delays intent, competes with content, obscures state, causes nausea or disorientation, breaks focus, makes rapid work tiring, lacks a coherent spatial cause, or costs more than its user/brand value. Mark it `REVISE` when the information is useful but choreography, timing, interruption, or reduction is wrong.

Deliver the event model, selected posture, role boundaries, reduced/static equivalents, tested inputs and states, performance evidence, and animations deliberately omitted.
