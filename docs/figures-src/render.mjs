#!/usr/bin/env node
// Render the reference-figure sources in this directory to
// skill/snowe-ui-skill/references/figures/*.png with headless Chrome.
//
// Each source page declares its output in one tag:
//   <meta name="figure" content="attention-weak.png 900x1000@1">
// meaning file name, CSS viewport width x height, and device scale factor.
//
// Usage:
//   node docs/figures-src/render.mjs              render every source
//   node docs/figures-src/render.mjs icon-style   render sources whose name contains "icon-style"
// Set CHROME_PATH to choose the browser executable.

import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, readdirSync, rmSync, statSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const SOURCE_DIR = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(SOURCE_DIR, "..", "..");
const OUTPUT_DIR = join(REPO_ROOT, "skill", "snowe-ui-skill", "references", "figures");
const SIZE_BUDGET = 120 * 1024;
const META = /<meta\s+name="figure"\s+content="([a-z0-9-]+\.png)\s+(\d+)x(\d+)@([12])"\s*>/;

function resolveChrome() {
  if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
  const candidates = {
    win32: [
      "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
      "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    ],
    darwin: ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"],
    linux: ["/usr/bin/google-chrome", "/usr/bin/google-chrome-stable", "/usr/bin/chromium", "/usr/bin/chromium-browser"],
  }[process.platform] ?? [];
  const found = candidates.find((candidate) => existsSync(candidate));
  if (!found) throw new Error("No Chrome executable found. Set CHROME_PATH.");
  return found;
}

function readSpec(file) {
  const match = readFileSync(file, "utf8").match(META);
  if (!match) throw new Error(`${basename(file)} has no <meta name="figure" content="name.png WxH@S">`);
  const [, output, width, height, scale] = match;
  return { output, width: Number(width), height: Number(height), scale: Number(scale) };
}

function render(chrome, file, spec) {
  const profile = mkdtempSync(join(tmpdir(), "snowe-figure-"));
  const target = join(OUTPUT_DIR, spec.output);
  try {
    const result = spawnSync(chrome, [
      "--headless",
      "--disable-gpu",
      "--hide-scrollbars",
      "--no-first-run",
      "--no-default-browser-check",
      "--disable-extensions",
      "--disable-lcd-text",
      "--force-color-profile=srgb",
      "--host-resolver-rules=MAP * ~NOTFOUND",
      `--user-data-dir=${profile}`,
      `--force-device-scale-factor=${spec.scale}`,
      `--window-size=${spec.width},${spec.height}`,
      "--virtual-time-budget=1500",
      `--screenshot=${target}`,
      pathToFileURL(file).href,
    ], { encoding: "utf8", windowsHide: true, timeout: 60_000 });
    if (result.status !== 0 || !existsSync(target)) {
      throw new Error(`Chrome failed for ${basename(file)}: ${result.stderr || result.error}`);
    }
  } finally {
    rmSync(profile, { recursive: true, force: true });
  }
  return statSync(target).size;
}

const filter = process.argv[2] ?? "";
const sources = readdirSync(SOURCE_DIR)
  .filter((name) => name.endsWith(".html") && name.includes(filter))
  .sort();
if (sources.length === 0) throw new Error(`No figure sources match "${filter}".`);

const chrome = resolveChrome();
let total = 0;
let overBudget = 0;
for (const name of sources) {
  const spec = readSpec(join(SOURCE_DIR, name));
  const bytes = render(chrome, join(SOURCE_DIR, name), spec);
  total += bytes;
  const flag = bytes > SIZE_BUDGET ? "  OVER BUDGET" : "";
  if (flag) overBudget += 1;
  console.log(`${spec.output.padEnd(34)} ${String(spec.width * spec.scale).padStart(5)}x${String(spec.height * spec.scale).padEnd(5)} ${String(bytes).padStart(7)} B${flag}`);
}
console.log(`${sources.length} figure(s), ${total} B`);
if (overBudget) process.exitCode = 1;
