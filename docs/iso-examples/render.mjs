#!/usr/bin/env node
// Render the iso.py demo scenes in this directory to SVG and PNG.
//
// For every <name>.scene.json this script runs
//   python skill/snowe-ui-skill/scripts/iso.py render <name>.scene.json -o <name>.svg --manifest <name>.manifest.json
// then inlines the SVG into a page (so the CSS custom properties apply) and
// captures it with headless Chrome at 1x and 2x, in the light theme and in a
// dark theme that only redefines the --iso-* variables.
//
// Usage:
//   node docs/iso-examples/render.mjs            render every scene
//   node docs/iso-examples/render.mjs platform   render scenes whose name contains "platform"
// Set CHROME_PATH to choose the browser and PYTHON for the interpreter. Pages in this
// directory that embed a scene between <!-- iso-scene: <name> --> markers (animated.html)
// are refreshed with the newly generated SVG.

import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(HERE, "..", "..");
const ISO = join(REPO_ROOT, "skill", "snowe-ui-skill", "scripts", "iso.py");
const MARGIN = 24;

const THEMES = {
  light: { background: "#f6f7fb", vars: "" },
  dark: {
    background: "#0f131c",
    vars: `--iso-top:#232a3a;--iso-left:#1a2030;--iso-right:#141927;--iso-stroke:#c9d2e6;
           --iso-detail:#6f7a93;--iso-accent:#7c93ff;--iso-text:#e7ecf7;--iso-grid:#2a3244;--iso-shadow:#000000;`,
  },
};

function resolveChrome() {
  if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
  const candidates = {
    win32: [
      "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
      "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
      "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    ],
    darwin: ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"],
    linux: ["/usr/bin/google-chrome", "/usr/bin/google-chrome-stable", "/usr/bin/chromium", "/usr/bin/chromium-browser"],
  }[process.platform] ?? [];
  const found = candidates.find((candidate) => existsSync(candidate));
  if (!found) throw new Error("No Chrome executable found. Set CHROME_PATH.");
  return found;
}

function renderScene(name) {
  const python = process.env.PYTHON ?? (process.platform === "win32" ? "python" : "python3");
  const result = spawnSync(python, ["-I", ISO, "render", join(HERE, `${name}.scene.json`),
    "-o", join(HERE, `${name}.svg`), "--manifest", join(HERE, `${name}.manifest.json`)], { encoding: "utf8" });
  if (result.status !== 0) throw new Error(`iso.py failed for ${name}:\n${result.stderr}`);
  if (result.stderr.trim()) process.stderr.write(result.stderr);
  return JSON.parse(readFileSync(join(HERE, `${name}.manifest.json`), "utf8"));
}

function capture(chrome, html, width, height, scale, target) {
  const work = mkdtempSync(join(tmpdir(), "snowe-iso-"));
  try {
    const page = join(work, "page.html");
    writeFileSync(page, html);
    const result = spawnSync(chrome, [
      "--headless", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
      "--disable-extensions", "--disable-lcd-text", "--force-color-profile=srgb", "--host-resolver-rules=MAP * ~NOTFOUND",
      `--user-data-dir=${join(work, "profile")}`, `--force-device-scale-factor=${scale}`,
      `--window-size=${width},${height}`, "--virtual-time-budget=1000", `--screenshot=${target}`,
      pathToFileURL(page).href,
    ], { encoding: "utf8", windowsHide: true, timeout: 60_000 });
    if (result.status !== 0 || !existsSync(target)) throw new Error(`Chrome failed: ${result.stderr || result.error}`);
  } finally {
    rmSync(work, { recursive: true, force: true });
  }
}

const filter = process.argv[2] ?? "";
const scenes = readdirSync(HERE).filter((f) => f.endsWith(".scene.json") && f.includes(filter))
  .map((f) => f.slice(0, -".scene.json".length)).sort();
if (scenes.length === 0) throw new Error(`No scenes match "${filter}".`);
const chrome = resolveChrome();
for (const name of scenes) {
  const manifest = renderScene(name);
  const svg = readFileSync(join(HERE, `${name}.svg`), "utf8");
  const width = manifest.width + 2 * MARGIN;
  const height = manifest.height + 2 * MARGIN;
  for (const [theme, { background, vars }] of Object.entries(THEMES)) {
    const html = `<!doctype html><meta charset="utf-8"><style>html,body{margin:0;background:${background}}
      body{padding:${MARGIN}px;${vars}}svg{display:block}</style>${svg}`;
    for (const scale of [1, 2]) {
      const suffix = theme === "light" ? "" : `-${theme}`;
      const target = join(HERE, `${name}${suffix}@${scale}x.png`);
      capture(chrome, html, width, height, scale, target);
      console.log(`${name}${suffix}@${scale}x.png  ${width * scale}x${height * scale}`);
    }
  }
}

// Pages such as animated.html embed a generated SVG between
// <!-- iso-scene: <name> --> and <!-- /iso-scene -->; refresh them so they never drift.
for (const page of readdirSync(HERE).filter((f) => f.endsWith(".html")).sort()) {
  const file = join(HERE, page);
  const before = readFileSync(file, "utf8");
  const after = before.replace(/(<!-- iso-scene: ([a-z0-9-]+) -->\n)[\s\S]*?(<!-- \/iso-scene -->)/g,
    (whole, open, name, close) => {
      const source = join(HERE, `${name}.svg`);
      return scenes.includes(name) && existsSync(source) ? `${open}${readFileSync(source, "utf8")}${close}` : whole;
    });
  if (after !== before) {
    writeFileSync(file, after);
    console.log(`${page}  inlined the current SVG`);
  }
}
