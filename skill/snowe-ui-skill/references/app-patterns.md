# Application Patterns

Use for app screens, dashboards, admin and internal tools, and mobile apps: any work built for repeated use of objects rather than a single read. These are behavioral defaults; visual style stays open. Where each task lives is decided with [surfaces-and-disclosure.md](surfaces-and-disclosure.md).

## Navigation Shell

| Situation | Default |
|---|---|
| 3–5 top-level destinations on mobile | Bottom tab bar with visible labels; the current tab shows a filled icon and emphasized label |
| More destinations, or a desktop work tool | Left sidebar with grouped items, collapsing to icons at medium widths; the current item is highlighted |
| A content site with few sections | Top navigation |
| Deep hierarchy | Breadcrumbs above the page title, and a predictable back path |
| Dense tool used all day | Add a command palette (Ctrl/Cmd+K) for search and actions |

## Collections and Detail

- **List and detail.** When people switch items often on desktop, show the list and an inspector side by side. For occasional detail, use a detail route. On mobile, push a detail screen with back.
- **Search.** Keep the field at the top of the collection. Update results as people type when that is cheap, and show the query and result count.
- **Filters.** Up to about four: inline selects or segmented controls. More: a filter panel or popover, with applied filters shown as removable chips plus "Clear all". Counts reflect the active filters.
- **Sort.** A control in the collection header that shows the current order.
- **Long collections.** Use pagination for tables and data people need to find again. Use "Load more" for browsing. Use infinite scroll only for endless feeds with nothing below them. Returning from a detail view restores the scroll position.
- **Bulk actions.** Selection reveals a contextual action bar with the selected count. "Select all on this page" and "select all results" are separate, explicit choices.

## States Every Collection Needs

- **Loading.** First load longer than about 300 ms: a skeleton in the final layout. A refresh: a quiet inline indicator that keeps current data visible. Never a blank region.
- **Empty.** Say which kind of empty it is (first use, no results, everything filtered out) and offer the next action. A first-use empty state may teach the feature.
- **Error.** State what failed in the user's terms, keep the last good data where possible, and offer retry. Scope a partial failure to its region rather than failing the whole page.
- **Stale or offline.** Show when data was last updated. Disable actions that need a connection and say why.

Keep the frame stable across all of these: see [stable geometry](design-foundations.md#stable-geometry-across-states).

## Actions and Feedback

- **Undo before confirm.** For reversible actions (archive, move, delete to trash), act immediately and offer Undo in a toast for 5–10 seconds. Reserve confirmation dialogs for irreversible, costly or high-consequence actions, and name the consequence in the dialog.
- **Optimistic updates** fit fast, likely-successful actions, with visible rollback on failure. Wait for confirmation on payments and irreversible operations.
- **Saving.** Autosave with a visible status ("Saved 14:02") suits documents and frequently edited settings. An explicit Save suits forms with validation or consequences. Warn before leaving with unsaved changes.
- **Toasts** are brief, non-blocking and one at a time, announced through a live region. They never carry an error that needs action, and never hold the only record of something important.
- Field errors stay at the field; system conditions go in a page banner.

## Flows

- **Create.** A few fields: inline or a dialog. Long: its own page. Use multiple steps only when they are genuinely separate decisions; show progress and allow going back without losing data.
- **Onboarding.** Deliver value first. Prefer useful empty states and contextual hints over multi-screen tours, and keep any tour skippable.
- **Settings.** Group by how users think, not by implementation. Offer search when there are many settings. A toggle applies immediately with a clear state; a group with dependencies gets an explicit save.
- **Destructive flows.** Make them reversible where possible. Reserve typed confirmation for catastrophic actions.

## Keyboard and Power Use

- Every action is reachable by keyboard.
- Frequent actions get shortcuts, shown in tooltips and menus.
- `/` focuses search, and Escape closes the topmost layer.
- Arrow keys move within lists and grids; J/K suit review queues.

## Mobile

- Put primary actions within thumb reach, near the bottom. Use bottom sheets for contextual choices.
- Follow platform touch targets (44 pt on iOS, 48 dp on Android) even though WCAG's minimum is 24 px.
- Respect safe areas and platform gestures; use pull-to-refresh where the platform expects it.
- Nothing depends on hover.
