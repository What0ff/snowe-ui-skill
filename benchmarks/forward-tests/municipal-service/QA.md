# Larkhaven rendered QA

Status: passed after automated and live-browser review on 10 August 2026.

## Coverage

- 1440×1000 wide, 900×900 pressure, and 390×844 narrow layouts;
- mobile navigation and Romanian/English language state;
- incomplete and complete eligibility paths;
- invalid and valid request-reference states;
- dialog opening/closing and focus restoration;
- horizontal overflow, local assets, runtime exceptions, console errors, and reduced-motion emulation.

## Findings and response

The first visual capture pass exposed a capture-runner error: state screenshots were being expanded to the full document, which misplaced fixed skip/menu elements in the evidence image even though the live viewport was correct. State captures now use viewport bounds while overview captures remain full-page. No material Larkhaven layout or interaction defect remained after live review.

Final screenshots are in `screenshots/`; the status-dialog and eligibility-result captures are tied to states exercised by `scripts/browser-smoke.mjs`.
