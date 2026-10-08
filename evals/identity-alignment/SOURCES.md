# Source and usage review

Reviewed 2026-10-08. These are external identities in a repository evaluation,
not Snowe-owned logos or an endorsement. No asset is installed with the skill.

## Telegram

- Owner source: https://telegram.org/tour/screenshots
- Download linked by that page: https://telegram.org/file/464001088/1/bI7AJLo7oX4.287931.zip/374fe3b0a59dc60005
- `assets/telegram.svg` is the exact `Logo.svg` member, extracted in memory;
  archive paths were not used for filesystem extraction. No paths/colors changed.
- The owner permits illustrative and sharing-button use while requiring that
  the context not suggest official representation. Screenshot CC0 language on
  that page concerns screenshots; it is not asserted as the logo's license.
- The retained SVG uses gradients/IDs and is outside the strict local validator.
  It is rendered as an external image asset in a labeled link to the owner.

## Bluesky

- Owner kit: https://bsky.social/about/support/icons
- Exact black variant: https://bsky.social/about/brand-assets/butterfly/bluesky_media_kit_logo_transparent_4.svg
- Usage guidelines: https://bsky.social/about/support/branding
- Trademark policy: https://bsky.social/about/support/trademark
- The black butterfly is an approved variant for social-profile links. The
  example links to a profile, preserves proportions and supplies clear space.
  The artwork remains the owner's trademark, subject to its usage policy.
  This record is a review summary, not a new license or automated permission.
- `assets/bluesky-black.svg` and `upstream/bluesky-black.svg` are identical
  unmodified downloaded bytes. Metadata binds both plus this usage record.
- The downloaded blue variant used #006AFF while the reviewed guideline named
  #0560FF. That discrepancy was not silently recolored: the approved black
  variant was selected. No claim of resolved blue-variant suitability is made.
- The initial Python download received HTTP 403; a normal curl request with a
  browser user agent retrieved the public asset. No authentication was used.

## Original interface glyphs

`assets/span-before.svg` and `assets/span.svg` are original repository evaluation
drawings under this repository's MIT license. The intended meaning is distance
between two mounting boundaries, with no safety/completion assertion. The
authored revision removes inner ruler ticks while retaining endpoints and
dimension arrows. It must be assessed at the actual 16/20/24 px slots.

This fixture proves source/geometry contracts and supports implementer visual
review. It is not a representative-user recognition study, a model baseline
experiment, or evidence that Snowe acquired general intelligence.
