# Motion and Interaction

Use when a state change, transition, feedback, spatial continuity, gesture, scroll or story may benefit from time. Motion carries information and character; it is not a required polish layer.

## Begin With the Static Truth

Make outcome, hierarchy, controls, state, progress and recovery understandable without animation. Then ask what time makes clearer: cause and effect; continuity between locations or states; origin, destination or ownership; progress, completion, interruption or failure; attention at a meaningful moment; direct-manipulation feedback; a story whose sequence matters; brand character that earns its repetition. If motion carries none of these, omit it. A static experience can be the most expressive or professional answer.

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

The model may resolve to an immediate state change. Start from it, not from a library demo or a global intensity dial.

## Choose a Motion Posture

- **Immediate or static:** frequent tools, urgency, obvious state changes, strict performance budgets, or contexts where animation impedes scanning.
- **Functional continuity:** a state change, overlay origin, hierarchy, reordering, navigation or feedback needs clarifying.
- **Expressive sequence:** launch, campaign, editorial, product story, creative tool or spatial experience where time is an intentional identity carrier. Functional rules must not flatten such choreography into generic fades.

One product can mix postures by role: frequent controls stay immediate while a rare storytelling moment is expressive, scoped to its carrier, with the boundary documented.

## Derive a Motion Grammar

Make movement feel caused by the interface: direction from source and destination, duration from distance, complexity and frequency, easing that describes acceleration, arrival, resistance or connection, stagger only where sequence or grouping means something, and preserved object identity where continuity matters. Use opacity, transform, clipping, scale, blur or shape change only when each supports the state model; keep feedback near the action without delaying completion for choreography, and avoid simultaneous motion in competing regions unless the relationship is the point. Coherence means shared mechanics and role logic, not one duration everywhere.

Starting points to adjust against the rendered result:

| Motion | Starting duration | Easing |
|---|---|---|
| Hover, press, toggle, color or state feedback | 100–150 ms | ease-out |
| Small element entering (tooltip, menu, toast) | 150–200 ms | ease-out (decelerate into place) |
| Element leaving | about two-thirds of its entrance | ease-in (accelerate away) |
| Panel, sheet or dialog crossing a large distance | 250–350 ms | ease-in-out or a gentle spring |
| Page or view transition | 200–300 ms; keep the destination usable immediately | ease-in-out |
| Stagger between list items | 20–40 ms per item, capped so the whole sequence stays under about 300 ms | — |

Frequent interactions get the shortest timings. Animate `transform` and `opacity` rather than layout properties; the View Transitions API or FLIP preserves object identity across layout changes.

## Interaction Quality

- Keep native semantics, keyboard operation, focus order, activation, labels, selection and error recovery.
- Hover only enhances; essential information and actions never hide behind it, and no gesture is the only path to an essential action.
- Make press, drag, drop, reorder, zoom, pan, swipe and scrub reversible or safely recoverable where mistakes are costly.
- Keep focus synchronized with modal, route, disclosure and removal transitions, never animating focus into a disappearing node.
- Give interrupted, cancelled, rapid, repeated and concurrent input a clear result.
- Scroll-linked motion keeps navigation, reading position, responsiveness and direct control; no scroll hijacking.
- Content is visible by default. Default: static sections get no entrance animation. When a reveal earns its place, the content's base state is visible; script adds the hidden start state only when it can run the reveal, the reveal plays once, and reduced motion skips it, so anchor jumps, find-in-page, print and captures never meet hidden text.

## Reduced Motion Is a Design Variant

Respect platform and browser motion preferences, simplifying by the information each motion carries:

- remove decorative travel, parallax, looping, zoom, spin and large spatial movement (vestibular triggers);
- use an immediate update, a short opacity or state transition, or a static before/after cue where feedback stays useful;
- keep content, state, focus and task completion;
- give any movement that starts automatically and lasts more than 5 seconds beside other content a visible way to pause, stop or hide it (WCAG 2.2.2), whether or not it seems distracting;
- never flash more than three times per second (WCAG 2.3.1).

Implement it with `@media (prefers-reduced-motion: reduce)` or the platform equivalent, and test it as a complete state: setting every duration to zero can erase feedback or break event assumptions.

## Responsive and Input Adaptation

Motion may need another model when navigation, composition, input or content order changes: touch versus pointer and keyboard feedback, small-screen overlays versus wide adjacent panels, reflow continuity at pressure widths, orientation and viewport changes, coarse-pointer targets and gesture conflicts, and low-power, low-bandwidth, background-tab or interrupted rendering. A responsive transformation may remove an animation whose spatial premise no longer exists.

## Implementation and Performance

Prefer platform-native or compositor-friendly mechanisms; avoid animating layout on large or frequently changing regions when transform, opacity or an immediate update suffices; reserve space for media and animated regions; load animation libraries only when the behavior justifies their weight and the repository accepts the dependency; stop observers, timelines, video, canvas and event work when offscreen, hidden, destroyed or reduced; and keep the final state usable when scripts, media or animation fail. Performance traces and frame stability are evidence; a smooth demo on one machine is not.

## Rendered Comparison

Compare the static or reduced baseline with the motion candidate in the implemented interface at normal speed and in repeated use; slow playback diagnoses mechanics but is not the user experience. Mark motion `REJECT` when it delays intent, competes with content, obscures state, causes nausea or disorientation, breaks focus, tires rapid work, lacks a spatial cause, or costs more than its value; mark it `REVISE` when the information is useful but choreography, timing, interruption or reduction is wrong.

Deliver the event model, selected posture, role boundaries, reduced and static equivalents, tested inputs and states, performance evidence, and animations deliberately omitted.
