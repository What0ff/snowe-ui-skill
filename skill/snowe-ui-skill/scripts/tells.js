// Snowe tells: rendered checks for the mechanical tells of generic, dated or unfinished UI.
// Plain browser JavaScript with no imports or network use. `observe.mjs tells` evaluates this file
// in a real page; a host browser tool can evaluate it too and then call snoweTells({kind: 'app'}).
// It finds specific symptoms in the DOM and computed styles; it never judges taste.
function snoweTells(options = {}) {
  const REF = {
    generic: 'references/failure-patterns.md#generic-output',
    dated: 'references/failure-patterns.md#dated-output',
    controls: 'references/design-foundations.md#controls-and-components',
    copy: 'references/page-hierarchy.md#keep-marketing-copy-scannable',
    motion: 'references/motion-and-interaction.md#interaction-quality',
    narrow: 'references/quality-gates.md#narrow-screens',
  };
  // id: [severity, message, reference]. "tell" findings fail the check; "check" findings need a look.
  const TELLS = {
    'left-stripe': ['tell', 'Accent stripe on the left edge of a card, panel or interactive item; mark selection by tone, weight or an icon', REF.generic],
    'left-rule': ['check', 'Left edge rule on a plain block; fine for a timeline axis or quote, not as an importance marker', REF.generic],
    'native-control': ['tell', 'Browser-default control look (select, date, time, color, range or file input, inset field, outset button)', REF.controls],
    'native-checkbox': ['check', 'Browser-default checkbox or radio with no accent color; style it into the control family', REF.controls],
    'default-focus': ['tell', 'No :focus or :focus-visible rule in the page styles, so the browser default ring shows', REF.controls],
    'admin-chrome': ['tell', 'Admin-template chrome: a dark top bar and a dark sidebar around a light canvas', REF.dated],
    'serif-interface': ['check', 'Serif or typewriter face in navigation, buttons, fields or table cells; legitimate only when the direction chose a print period', REF.dated],
    'framework-defaults': ['check', 'Several elements use exact framework default colors or shadows; confirm each value is a decision', REF.generic],
    'purple-gradient': ['tell', 'Purple-to-blue gradient fill', REF.generic],
    'gradient-text': ['tell', 'Gradient text', REF.generic],
    'icon-tiles': ['tell', 'An icon in a tinted tile above three or more repeated feature cards', REF.generic],
    'emoji-icons': ['tell', 'Emoji used as interface icons in controls, navigation, lists or headings', REF.generic],
    'hidden-until-scroll': ['tell', 'Content below the fold is invisible until a scroll reveal runs', REF.motion],
    'eyebrow-every-heading': ['tell', 'An uppercase tracked eyebrow above nearly every heading', REF.generic],
    'section-numbers': ['check', 'Numbered section labels such as 01 or 02; keep them only for a real order', REF.generic],
    'prose-over-budget': ['tell', 'Marketing page prose outside product visuals is over about 1,200 words', REF.copy],
    'horizontal-overflow': ['tell', 'The page is wider than the viewport', REF.narrow],
    'viewport-meta': ['tell', 'No <meta name="viewport">, so phones render the page at desktop width and shrink it', REF.narrow],
    'low-contrast-text': ['tell', 'Body text below 4.5:1 against its background', REF.generic],
    'glass-default': ['check', 'Backdrop blur on several surfaces; keep glass only over media that matters', REF.generic],
  };
  const W = innerWidth, H = innerHeight;
  const found = new Map();
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = 1;
  const ctx = canvas.getContext('2d', {willReadFrequently: true});
  const colorCache = new Map();

  function color(value) {
    if (colorCache.has(value)) return colorCache.get(value);
    let result = {r: 0, g: 0, b: 0, a: 0};
    if (value && value !== 'transparent' && value !== 'none') {
      ctx.clearRect(0, 0, 1, 1);
      ctx.fillStyle = '#000';
      ctx.fillStyle = value;
      ctx.fillRect(0, 0, 1, 1);
      const [r, g, b, a] = ctx.getImageData(0, 0, 1, 1).data;
      result = {r, g, b, a: a / 255};
    }
    colorCache.set(value, result);
    return result;
  }
  function luminance({r, g, b}) {
    const channel = v => { v /= 255; return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
  }
  function contrast(a, b) {
    const [x, y] = [luminance(a), luminance(b)].sort((m, n) => n - m);
    return (x + 0.05) / (y + 0.05);
  }
  function hueSat({r, g, b}) {
    const [R, G, B] = [r / 255, g / 255, b / 255], max = Math.max(R, G, B), min = Math.min(R, G, B), d = max - min;
    if (!d) return {h: 0, s: 0};
    const h = max === R ? ((G - B) / d) % 6 : max === G ? (B - R) / d + 2 : (R - G) / d + 4;
    return {h: (h * 60 + 360) % 360, s: d / (1 - Math.abs(max + min - 1))};
  }
  function blend(top, bottom) {
    const a = top.a + bottom.a * (1 - top.a);
    if (!a) return {r: 255, g: 255, b: 255, a: 1};
    const mix = k => Math.round((top[k] * top.a + bottom[k] * bottom.a * (1 - top.a)) / a);
    return {r: mix('r'), g: mix('g'), b: mix('b'), a};
  }
  // The painted background behind an element, or null when an image or gradient makes it unknowable.
  function background(element) {
    const layers = [];
    for (let node = element; node && node.nodeType === 1; node = node.parentElement) {
      const style = getComputedStyle(node);
      if (style.backgroundImage !== 'none') return null;
      const c = color(style.backgroundColor);
      if (c.a > 0) layers.push(c);
      if (c.a >= 0.95) break;
    }
    return layers.reduceRight((under, over) => blend(over, under), {r: 255, g: 255, b: 255, a: 1});
  }
  function shown(element) {
    const r = element.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return false;
    return element.checkVisibility ? element.checkVisibility({opacityProperty: true, visibilityProperty: true}) : true;
  }
  function selector(element) {
    const parts = [];
    for (let node = element; node && node.nodeType === 1 && parts.length < 4; node = node.parentElement) {
      if (node.id) { parts.unshift('#' + CSS.escape(node.id)); break; }
      let part = node.tagName.toLowerCase();
      const classes = [...node.classList].slice(0, 2).map(c => '.' + CSS.escape(c)).join('');
      part += classes;
      const parent = node.parentElement;
      if (parent && !classes) {
        const same = [...parent.children].filter(c => c.tagName === node.tagName);
        if (same.length > 1) part += `:nth-of-type(${same.indexOf(node) + 1})`;
      }
      parts.unshift(part);
      if (node === document.body) break;
    }
    return parts.join(' > ');
  }
  function add(id, element, evidence = {}) {
    const entry = found.get(id) || {count: 0, examples: []};
    entry.count += 1;
    if (entry.examples.length < 5) {
      const r = element.getBoundingClientRect();
      entry.examples.push({selector: selector(element), rect: {x: Math.round(r.x + scrollX), y: Math.round(r.y + scrollY), width: Math.round(r.width), height: Math.round(r.height)}, ...evidence});
    }
    found.set(id, entry);
  }
  function words(text) { return (text.match(/[\p{L}\p{N}][\p{L}\p{N}'’.-]*/gu) || []).length; }
  function serifStack(stack) {
    for (const raw of stack.split(',')) {
      const name = raw.trim().replace(/^["']|["']$/g, '').toLowerCase();
      if (/sans|system-ui|-apple-system|blinkmacsystemfont|segoe|roboto|inter\b|helvetica|arial/.test(name)) return false;
      if (/^(serif|ui-serif)$|serif|georgia|times|garamond|baskerville|caslon|playfair|merriweather|lora\b|fraunces|newsreader|crimson|cormorant|literata|spectral|bodoni|didot|tiempos|charter|cambria|minion|freight|domine|alegreya|courier|typewriter|special elite/.test(name)) return true;
    }
    return false;
  }

  const all = [...document.body.querySelectorAll('*')].filter(e => !['SCRIPT', 'STYLE', 'TEMPLATE', 'NOSCRIPT', 'BR'].includes(e.tagName));
  const styles = new Map(all.map(e => [e, getComputedStyle(e)]));
  const style = e => styles.get(e) || getComputedStyle(e);

  // Kind: an app has a tall navigation column or a working surface of fields and tables.
  const sidebar = all.find(e => {
    const r = e.getBoundingClientRect();
    return r.left <= 1 && r.width >= 150 && r.width <= 380 && r.height >= H * 0.7 && e.querySelectorAll('a, button').length >= 4 && shown(e);
  });
  const fields = document.querySelectorAll('table, [role=grid], input:not([type=hidden]), select, textarea').length;
  const kind = ['app', 'marketing'].includes(options.kind) ? options.kind : (sidebar || fields >= 6 ? 'app' : 'marketing');

  // Left stripes: a border, an inset shadow or an absolutely placed pseudo bar on the left edge.
  const interactive = e => e.matches('a, button, summary, label, [role=button], [role=tab], [role=option], [role=menuitem], [role=link], [aria-current], [aria-selected=true]');
  for (const e of all) {
    if (e.closest('blockquote, pre, code, table') || !shown(e)) continue;
    const r = e.getBoundingClientRect();
    if (r.width < 24 || r.height < 16) continue;
    const s = style(e);
    let stripe = null;
    const left = parseFloat(s.borderLeftWidth), others = Math.max(parseFloat(s.borderTopWidth), parseFloat(s.borderRightWidth), parseFloat(s.borderBottomWidth));
    if (s.borderLeftStyle !== 'none' && left >= 2 && left >= others + 1.5 && color(s.borderLeftColor).a > 0.3) stripe = {source: 'border-left', width: left};
    if (!stripe && s.boxShadow !== 'none') {
      for (const shadow of s.boxShadow.split(/,(?![^(]*\))/)) {
        const lengths = (shadow.replace(/(rgba?|oklch|oklab|lab|lch|hsla?|color)\([^)]*\)/g, '').match(/-?[\d.]+px/g) || []).map(parseFloat);
        if (/inset/.test(shadow) && lengths[0] >= 2 && Math.abs(lengths[1] || 0) < 1 && !(lengths[2] > 0)) { stripe = {source: 'inset box-shadow', width: lengths[0]}; break; }
      }
    }
    if (!stripe) {
      for (const pseudo of ['::before', '::after']) {
        const p = getComputedStyle(e, pseudo);
        if (p.content === 'none' || p.content === 'normal' || !['absolute', 'fixed'].includes(p.position)) continue;
        const w = parseFloat(p.width), h = parseFloat(p.height), x = parseFloat(p.left);
        if (w >= 1.5 && w <= 8 && h >= r.height * 0.5 && Math.abs(x) <= 4 && (color(p.backgroundColor).a > 0.3 || p.backgroundImage !== 'none')) { stripe = {source: pseudo, width: w}; break; }
      }
    }
    if (!stripe) continue;
    const own = color(s.backgroundColor), behind = background(e.parentElement || document.body);
    const card = parseFloat(s.borderTopLeftRadius) >= 4 || s.boxShadow.replace(/inset[^,]*/g, '').match(/px/) || (own.a > 0.5 && behind && Math.abs(luminance(own) - luminance(behind)) > 0.01);
    add(interactive(e) || card ? 'left-stripe' : 'left-rule', e, stripe);
  }

  // Controls left in the browser's default look.
  for (const e of document.querySelectorAll('select, input, textarea, button')) {
    if (!shown(e)) continue;
    const r = e.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) continue;
    const s = style(e), type = (e.getAttribute('type') || '').toLowerCase(), appearance = s.appearance || s.webkitAppearance;
    if (e.tagName === 'SELECT' && appearance !== 'none') add('native-control', e, {control: 'select', appearance});
    else if (e.tagName === 'INPUT' && ['date', 'datetime-local', 'time', 'month', 'week', 'color', 'range'].includes(type) && appearance !== 'none') add('native-control', e, {control: type + ' input', appearance});
    else if (e.tagName === 'INPUT' && type === 'file') add('native-control', e, {control: 'file input'});
    else if (e.tagName === 'INPUT' && ['checkbox', 'radio'].includes(type)) { if (appearance !== 'none' && s.accentColor === 'auto') add('native-checkbox', e, {control: type}); }
    else if ((e.tagName === 'TEXTAREA' || e.tagName === 'INPUT') && s.borderTopStyle === 'inset') add('native-control', e, {control: (type || e.tagName.toLowerCase()) + ' field', border: 'inset'});
    else if (e.tagName === 'BUTTON' && s.borderTopStyle === 'outset') add('native-control', e, {control: 'button', border: 'outset'});
  }
  let focusRules = 0;
  const walk = rules => { for (const rule of rules || []) { if (rule.selectorText && /:focus/.test(rule.selectorText)) focusRules++; if (rule.cssRules) walk(rule.cssRules); } };
  for (const sheet of document.styleSheets) { try { walk(sheet.cssRules); } catch { /* cross-origin sheet */ } }
  const focusable = document.querySelectorAll('a[href], button, input:not([type=hidden]), select, textarea, [tabindex]:not([tabindex="-1"])').length;
  if (focusable && !focusRules) add('default-focus', document.documentElement, {focusable});

  // Admin-template chrome on a desktop width.
  if (W >= 1024) {
    const dark = e => { const c = color(style(e).backgroundColor); return c.a > 0.9 && luminance(c) < 0.06; };
    let bar = null, side = null;
    for (const e of all) {
      const r = e.getBoundingClientRect();
      if (!bar && r.top <= 1 && r.right >= W - 1 && r.width >= W * 0.6 && r.height >= 36 && r.height <= 110 && dark(e)) bar = e;
      if (!side && r.left <= 1 && r.top <= 120 && r.width >= 150 && r.width <= 380 && r.height >= H * 0.7 && dark(e)) side = e;
    }
    const probe = document.elementFromPoint(Math.min(W - 40, W * 0.65), Math.min(H - 40, H * 0.6));
    const canvasColor = probe && background(probe);
    if (bar && side && canvasColor && luminance(canvasColor) > 0.6) add('admin-chrome', side, {topBar: selector(bar)});
  }

  // Print faces in interface roles.
  for (const e of document.querySelectorAll('nav a, [role=navigation] a, aside a, button, [role=button], [role=tab], [role=menuitem], input, select, textarea, label, th, td')) {
    if (shown(e) && e.textContent.trim() && serifStack(style(e).fontFamily)) add('serif-interface', e, {fontFamily: style(e).fontFamily.slice(0, 80)});
  }

  // Exact framework default colors (Tailwind 3 hex and Tailwind 4 approximations) and shadows.
  const defaults = ['#6366f1', '#4f46e5', '#8b5cf6', '#7c3aed', '#a855f7', '#9333ea', '#9ca3af', '#6b7280', '#615fff', '#4f39f6', '#8e51ff', '#7f22fe', '#ad46ff', '#9810fa', '#99a1af', '#6a7282']
    .map(hex => ({hex, r: parseInt(hex.slice(1, 3), 16), g: parseInt(hex.slice(3, 5), 16), b: parseInt(hex.slice(5, 7), 16)}));
  const isDefault = value => { const c = color(value); return c.a > 0.5 && defaults.find(d => Math.abs(d.r - c.r) <= 2 && Math.abs(d.g - c.g) <= 2 && Math.abs(d.b - c.b) <= 2); };
  const defaultHits = [];
  for (const e of all) {
    if (!shown(e)) continue;
    const s = style(e);
    const hit = (e.textContent.trim() && isDefault(s.color)) || isDefault(s.backgroundColor) || (parseFloat(s.borderTopWidth) > 0 && isDefault(s.borderTopColor));
    const shadow = /0px 10px 15px -3px.*0px 4px 6px -4px|0px 4px 6px -1px.*0px 2px 4px -2px|0px 20px 25px -5px.*0px 8px 10px -6px/.test(s.boxShadow);
    if (hit || shadow) defaultHits.push([e, hit ? {value: hit.hex} : {value: 'framework shadow'}]);
  }
  if (defaultHits.length >= 3) for (const [e, evidence] of defaultHits) add('framework-defaults', e, evidence);

  // Gradients.
  for (const e of all) {
    if (!shown(e)) continue;
    const s = style(e);
    if (/gradient\(/.test(s.backgroundImage)) {
      const hues = (s.backgroundImage.match(/(rgba?|oklch|oklab|lab|lch|hsla?|color)\([^)]*\)|#[0-9a-f]{3,8}\b/gi) || [])
        .map(value => hueSat(color(value))).filter(c => c.s > 0.25).map(c => c.h);
      if (hues.some(h => h >= 255 && h <= 320) && hues.some(h => h >= 195 && h < 255)) add('purple-gradient', e, {backgroundImage: s.backgroundImage.slice(0, 120)});
      if ((s.backgroundClip === 'text' || s.webkitBackgroundClip === 'text') && e.textContent.trim()) add('gradient-text', e);
    }
  }

  // Icon tiles heading three or more repeated cards.
  const groups = new Map();
  for (const e of all) {
    const r = e.getBoundingClientRect();
    if (r.width < 24 || r.width > 88 || Math.abs(r.width - r.height) > 4 || !shown(e)) continue;
    const s = style(e);
    const tinted = color(s.backgroundColor).a > 0.12 || (parseFloat(s.borderTopWidth) > 0 && s.borderTopStyle !== 'none');
    const rounded = parseFloat(s.borderTopLeftRadius) >= 6 || /%/.test(s.borderTopLeftRadius);
    const glyph = e.querySelector('svg, img, i') || /^\p{Extended_Pictographic}/u.test(e.textContent.trim());
    if (!tinted || !rounded || !glyph || words(e.textContent) > 1) continue;
    let card = e.parentElement;
    for (let i = 0; i < 3 && card && !card.querySelector('h2, h3, h4, h5'); i++) card = card.parentElement;
    if (!card || !card.querySelector('h2, h3, h4, h5') || !card.parentElement) continue;
    const list = groups.get(card.parentElement) || [];
    if (!list.some(([c]) => c === card)) list.push([card, e]);
    groups.set(card.parentElement, list);
  }
  for (const list of groups.values()) if (list.length >= 3) for (const [, tile] of list) add('icon-tiles', tile);

  // Emoji as interface icons.
  const textWalker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let node = textWalker.nextNode(); node; node = textWalker.nextNode()) {
    const text = node.textContent.trim(), owner = node.parentElement;
    if (!text || !owner || !owner.closest('button, a, nav, li, h1, h2, h3, h4, h5, h6, th, label, summary, [role=tab], [role=menuitem]')) continue;
    if (/^(?![©®™‼⁉#*0-9])\p{Extended_Pictographic}/u.test(text) && shown(owner)) add('emoji-icons', owner, {text: text.slice(0, 24)});
  }

  // Content hidden until a scroll reveal runs.
  if (scrollY < 2) {
    const hidden = new Set();
    for (const e of all) {
      const r = e.getBoundingClientRect();
      if (r.top < H || r.width < 1 || r.height < 1 || words(e.textContent) < 3) continue;
      if (e.closest('[hidden], [inert], [aria-hidden=true], dialog:not([open]), details:not([open])')) continue;
      const s = style(e);
      if ((parseFloat(s.opacity) === 0 || s.visibility === 'hidden') && ![...hidden].some(h => h.contains(e))) hidden.add(e);
    }
    if (hidden.size >= 2) for (const e of hidden) add('hidden-until-scroll', e);
  }

  // Eyebrows above nearly every heading, and numbered section labels.
  const headings = [...document.querySelectorAll('h1, h2')].filter(shown);
  let eyebrows = 0, numbered = [];
  for (const h of headings) {
    const before = h.previousElementSibling;
    const hs = style(h);
    if (before && shown(before) && words(before.textContent) <= 6) {
      const s = style(before), text = before.textContent.trim();
      const upper = s.textTransform === 'uppercase' || (text.length >= 3 && text === text.toUpperCase() && /\p{L}/u.test(text));
      if (upper && parseFloat(s.letterSpacing) >= 0.04 * parseFloat(s.fontSize) && parseFloat(s.fontSize) <= 0.7 * parseFloat(hs.fontSize)) eyebrows++;
      if (/^\s*0\d\b|^\s*\d{2}\s*[./:—–-]/.test(text)) numbered.push(before);
    }
    if (/^\s*0\d\b|^\s*\d{2}\s*[./:—–-]/.test(h.textContent)) numbered.push(h);
  }
  if (eyebrows >= 3 && eyebrows / headings.length >= 0.6) add('eyebrow-every-heading', document.body, {headings: headings.length, eyebrows});
  if (numbered.length >= 2) for (const e of numbered) add('section-numbers', e, {text: e.textContent.trim().slice(0, 24)});

  // Prose outside product visuals, navigation, forms and tables.
  let prose = 0;
  for (const e of document.querySelectorAll('p, li, dd, blockquote, figcaption')) {
    if (!shown(e) || e.closest('nav, header, footer, form, figure, table, svg, pre, code, dialog, [role=img], [data-visual], [aria-hidden=true]')) continue;
    if (e.querySelector('p, li, dd, blockquote')) continue;
    prose += words(e.textContent);
  }
  if (kind === 'marketing' && prose > 1200) add('prose-over-budget', document.body, {words: prose});

  // Phone layout needs a viewport declaration; without it a phone lays the page out at desktop width.
  if (!document.querySelector('meta[name=viewport]')) add('viewport-meta', document.documentElement);

  // Horizontal overflow.
  if (document.documentElement.scrollWidth > W + 1) {
    const wide = all.filter(e => { const r = e.getBoundingClientRect(); return r.right > W + 1 && r.width > 0 && shown(e); });
    const outermost = wide.filter(e => !wide.some(o => o !== e && o.contains(e)));
    for (const e of outermost.length ? outermost : [document.documentElement]) add('horizontal-overflow', e, {scrollWidth: document.documentElement.scrollWidth, viewport: W});
  }

  // Low-contrast body text.
  for (const e of document.querySelectorAll('p, li, dd, td, label, figcaption, small')) {
    if (!shown(e) || words(e.textContent) < 3 || e.closest('[aria-disabled=true], :disabled')) continue;
    const s = style(e), size = parseFloat(s.fontSize), bold = parseInt(s.fontWeight, 10) >= 700;
    if (size >= 24 || (bold && size >= 18.66)) continue;
    const fg = color(s.color), bg = background(e);
    if (!bg || fg.a === 0) continue;
    const ratio = contrast(blend(fg, bg), bg);
    if (ratio < 4.5) add('low-contrast-text', e, {ratio: Math.round(ratio * 100) / 100, color: s.color});
  }

  // Glass by default.
  const glass = all.filter(e => /blur\(/.test(style(e).backdropFilter || style(e).webkitBackdropFilter || '') && shown(e));
  if (glass.length >= 3) for (const e of glass) add('glass-default', e);

  const findings = [...found.entries()].map(([id, entry]) => {
    const [severity, message, ref] = TELLS[id];
    return {id, severity, message, ref, count: entry.count, examples: entry.examples};
  }).sort((a, b) => (a.severity === b.severity ? a.id.localeCompare(b.id) : a.severity === 'tell' ? -1 : 1));
  return {
    version: '1.0',
    kind,
    viewport: {width: W, height: H},
    findings,
    metrics: {proseWords: prose, focusRules, elements: all.length},
    ids: Object.keys(TELLS),
  };
}
