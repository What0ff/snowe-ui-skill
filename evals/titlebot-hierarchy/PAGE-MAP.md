# Title Bot: page hierarchy before components

## Task and reference

An operator monitors four kingdom titles, identifies the selected holder and next player, inspects its queue and durations, and performs permitted management actions. The reference is hierarchy in Cloudflare dashboards, specifically separation of resource context, navigation, actionable work and secondary tools. The public marketing homepage is not the target. Dark surfaces, orange interaction accent, Inter and the existing Title Bot symbol vocabulary remain the baseline.

The user-provided baseline screenshot is retained in `baseline.png`. The frontend was read only; `sources.json` records its contract snapshot. Fixtures are fictional, distinct per title, and the pilot has no production API connection. Experimental metadata stays in this document and the test report, outside the customer interface.

## Role map

| Role | User question / content | Relation and prominence |
| --- | --- | --- |
| Resource context | Which kingdom? | Small persistent kingdom label above the page heading. |
| Page identity / tools | Title Bot; VIP, blocked players, Settings | One concise heading; three distinct secondary operations aligned with this page. No duplicate Edit rules entry. |
| Local navigation | Justice, Duke, Architect, Scientist; holder preview and waiting count | Flat tabs under the header, visually below the page title and selected work. Four columns wide; narrow English uses two columns, while long Russian labels use full-width rows. |
| Selected object | Current holder, next player, regular/VIP duration | One shared assignment surface grouping related values; no separate card for each value. Identity values remain attached to their captions. |
| Current operation | Advance/release only when a holder and permission exist | One contextual primary action; confirmation identifies the actual affected title/players. |
| Primary data | Queue for the selected title | Full-width table/list under the summary; row actions identify their own players. Long queues scroll in their region. |
| Reference | Request-command aliases | Native disclosure labelled Commands, without permanent code-like text beside the title. |
| State/recovery | Loading, unavailable, view-only, empty, mutation failure | Short factual messages at the affected scope; one relevant retry and no raw exception/implementation text. |

The selected title controls holder, next player, durations, queue and action targets together. Justice has two waiting players, Duke is vacant, Architect has a holder with no successor, Scientist has a long queue. Distinct names/IDs expose cross-title data mistakes.

## Action and copy decisions

- Identity is operation + target object + outcome + context. Settings opens one settings dialog; VIP and blocked lists are separate outcomes. Removal buttons target different entries and are not duplicates.
- Retain title/kingdom/player IDs, policy, durations and command aliases. Remove the generic subtitle and redundant descriptions of an already labelled queue. One empty message is sufficient.
- Configuration supports global/per-title regular and VIP durations and VIP-only title scope. Lists support lookup/add/remove using local fixtures. Mutations are serialized, can fail without losing context, and preserve cancellation.
- At narrow widths, summaries and tools wrap by relation; no text is hidden to make the layout fit. Core context/holder/next remain reachable before the queue. The same Inter family and source drawing paths are used; this exercise does not claim a new palette or icon family.

## Proof and limits

Required-role visibility, names, clipping and sampled occlusion are checked separately from layout judgment. The action registry is verified through handlers/outcomes, including negative duplicates with different labels and valid per-row repeats. User acceptance is a separate disposition; no technical PASS or authored self-review establishes it.

## Complete-screen finish

The first technical render was not visually accepted. Implementer review and user feedback identified an overly conventional admin treatment: scattered summary values, stock-looking controls and undifferentiated dark separators. The revised candidate groups the assignment in one surface, uses a clearer value/caption hierarchy, draws checkboxes consistently with the existing controls and gives the queue a distinct reading rhythm. It retains Inter, dark colors, original title symbols and the orange interaction accent. These choices are a scoped proposal, not a native-control ban or user acceptance.
