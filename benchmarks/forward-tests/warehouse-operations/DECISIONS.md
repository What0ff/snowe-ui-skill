# Relay North exception workspace — causal decisions

## Brief

Dispatchers repeatedly detect, inspect, and resolve live inventory exceptions. Keyboard speed, state continuity, object history, and auditability matter more than product explanation or acquisition.

## Chosen architecture

An application shell exposes a persistent operational topology. The exception queue, affected object, history, and resolution action share one workspace so the operator never reconstructs context across pages. Keyboard movement and direct filters follow the detect → inspect → act loop.

## Strongest rejected alternative

A dashboard landing page with KPI cards, charts, and links into separate exception detail pages was rejected. It optimizes overview theatre while adding navigation and memory cost to the repeated command path.

## Art direction and assets

The visual carrier is operational state: dense alignment, monospace identifiers, priority fields, object balances, and a dark control-room surface. Generated imagery and custom graphics were rejected because they consume scan space without increasing object truth. Existing text abbreviations and labels outperform a novel icon system.

## Motion

Practically none. Selection, filtering, dialog, validation, and toast feedback are immediate state changes. There are no reveals, panel slides, number animations, or ambient loops. Reduced motion explicitly preserves the same complete state.

## Responsive transformation

Wide screens keep queue and inspector adjacent. At pressure width the inspector becomes a two-column detail region below the queue. Narrow screens turn rows into structured records and the navigation into an on-demand rail; the object/action sequence remains intact rather than becoming a marketing mobile homepage.
