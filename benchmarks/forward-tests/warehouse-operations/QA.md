# Relay North rendered QA

Status: passed after two implementation fixes and live-browser confirmation on 10 August 2026.

## Coverage

- 1440×1000 wide, 900×900 pressure, and 390×844 narrow layouts;
- queue row selection, text search, priority filter, J/K/E and slash keyboard paths;
- resolution dialog validation, successful audit feedback, and focus restoration;
- structured mobile records and on-demand command rail;
- horizontal overflow, runtime exceptions, console errors, and reduced-motion emulation.

## Findings and response

1. Filter listeners used the broad `[data-filter]` selector, which also matched queue rows. Selecting a multi-tag row therefore created an impossible active filter and hid the queue. Listeners and pressed-state updates are now scoped to `.queue-tabs`.
2. A committed resolution set `hidden`, but the next filter pass made the row visible again. Resolution is now explicit object state (`data-resolved`), and filtering consistently excludes resolved records.

Both failures were discovered by the browser smoke rather than static tests. The live in-app browser then confirmed slash-to-search focus, invalid-resolution focus, successful commit feedback, row removal, and opener focus restoration. Final screenshots are in `screenshots/`.
