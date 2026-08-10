# The Morrow Review rendered QA

Status: passed after one responsive correction and live-browser confirmation on 10 August 2026.

## Coverage

- 1440×1000 wide, 900×900 pressure, and 390×844 narrow layouts;
- publication menu, reading-size control, saved-story state, and archive empty state;
- membership validation/result and focus restoration;
- reading progress, horizontal overflow, runtime exceptions, console errors, and reduced-motion emulation.

## Findings and response

The live 390 px pass found that a tablet grid placement for the membership control leaked into the phone header, producing `Contents · + · masthead`. The phone rule now clears that inherited grid position; the causal order is `Contents · masthead · membership`, with all three controls inside the content width. Smooth anchor scrolling was also removed so the implemented motion contract is genuinely reading progress only.

The corrected geometry, menu state, membership validation/result, and zero-overflow state were confirmed in the in-app browser. Final screenshots are in `screenshots/`.
