# HTML Email

Use when designing or building an HTML email: transactional, account or campaign. Email clients are not browsers; design inside their limits, then prove the result in real clients. Copy follows the [user-facing text audit](page-hierarchy.md#audit-user-facing-text).

## Build Within Client Limits

| Concern | Default | Why, and when to deviate |
|---|---|---|
| Layout | Nested `<table role="presentation">`, zero cellpadding, cellspacing and border; one column | Classic Outlook for Windows renders with Word's engine: no flexbox, grid, floats or reliable `max-width`. Two columns only for short paired content that stacks on phones |
| Width | 600 px container (560–640), centered: `width: 100%; max-width: 600px`, plus a fixed-width table inside `<!--[if mso]>` | Wider layouts crop in preview panes |
| CSS | Inline every style needed to read the email; a `<style>` block only for media queries, dark mode and resets | Some clients and forwards strip `<style>` |
| Spacing | Padding on `<td>`; reset `<p>` and heading margins inline | Outlook ignores many margins |
| Size | HTML under about 100 KB after inlining and link tracking | Gmail clips above 102 KB, hiding the footer and unsubscribe link |
| Images | Absolute HTTPS URLs, `width` and `height` attributes, `display: block`, 2× sources | Several clients block images until allowed; the email must work without them |
| Fonts | Web font as enhancement over a full fallback stack (Arial, Helvetica, Georgia), forced for Outlook in an `[if mso]` style | Gmail and Outlook ignore most web fonts; classic Outlook falls back to Times New Roman |
| Interaction | Links only | No JavaScript; forms are unreliable; `:hover` is an enhancement |

## Bulletproof Buttons

Build buttons from HTML, never images, so they survive image blocking and dark mode:

```html
<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>
  <td bgcolor="#1d4ed8" style="border-radius:6px;padding:12px 24px;">
    <a href="https://example.com/orders/1042" style="font:600 16px/20px Arial,sans-serif;color:#ffffff;text-decoration:none;">View your order</a>
  </td>
</tr></table>
```

The cell carries background and padding, so every client shows the whole button. In classic Outlook only the label is clickable and corners are square unless you add a VML `v:roundrect` fallback. Keep the button at least 44 px tall, the label specific ("View your order", not "Click here") and its contrast at 4.5:1.

## Dark Mode

Clients either leave colors alone, partially invert light backgrounds and dark text, or invert every color. Apple Mail applies your own dark styles; Gmail's apps and several Outlook versions invert by themselves and largely ignore them. Make every outcome readable:

- Declare `<meta name="color-scheme" content="light dark">` and `<meta name="supported-color-schemes" content="light dark">`, then add `@media (prefers-color-scheme: dark)` styles. Outlook.com and the Outlook apps also read `[data-ogsc]` (text) and `[data-ogsb]` (background) selectors.
- Export logos and dark artwork as transparent PNGs with a light outline, or set them on a fixed light tile.
- Keep text out of images: clients can recolor live text, not pixels.
- Check contrast in the inverted result, not only in the light design.

## Content and Accessibility

- Set `<html lang="…">` and `<title>`. Give every layout table `role="presentation"` so screen readers skip its rows and columns, and use real `<h1>` and `<p>` elements in reading order.
- Informative images get `alt` stating their message; decorative ones get `alt=""`. Style alt text (font, size, color) so a blocked image still reads.
- Body text 16 px (14 px minimum), line height in pixels with `mso-line-height-rule: exactly`; iOS enlarges text below 13 px on its own. Left-align paragraphs, underline body links, and meet the [contrast thresholds](quality-gates.md#accessibility-and-interaction).
- Put the key fact and action near the top: the order number, the code, the one button. On phones the layout becomes one column; below 600 px, make buttons full width.
- **Preheader**: previews show roughly 40–130 characters after the subject. Write one that extends the subject, hide it with `display:none; max-height:0; overflow:hidden; mso-hide:all`, and pad it with `&zwnj;&nbsp;` so body text does not leak into the preview.
- **Plain-text part**: send `multipart/alternative` with a written text version and spelled-out links.
- Marketing email carries a visible unsubscribe link, a one-click `List-Unsubscribe` header for bulk senders (required by Gmail and Yahoo since 2024) and the sender details the law requires, such as a postal address under US CAN-SPAM.

## Test in Real Clients

- Render through a preview service or real devices: classic Outlook for Windows, Outlook.com or new Outlook, Gmail on web, Android and iOS, and Apple Mail on macOS and iOS. Add clients your audience uses.
- Cover light and dark mode, images on and off, and phone width.
- Measure HTML size after the sending platform inlines styles and rewrites links.
- Send real tests: click every link and the unsubscribe flow, read the plain-text part, and listen once with a screen reader such as VoiceOver.
- A browser preview is not client proof; record untested clients as `UNKNOWN` ([dispositions](quality-gates.md#verdicts)).

## Check

- Presentation tables, 600 px or narrower, readable with `<style>` stripped.
- HTML under about 100 KB after inlining and tracking.
- With images off, message, action and alt text still work.
- HTML buttons; web fonts degrade to a declared fallback in Outlook.
- Logos and text survive at least one inverting dark-mode client.
- Preheader, plain-text part, and unsubscribe and sender details where required.
- Rendered in classic Outlook, Gmail and Apple Mail, light and dark.
