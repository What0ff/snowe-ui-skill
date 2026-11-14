#!/usr/bin/env node
// Render a glyph.py contact sheet to PNG with headless Chrome over CDP.
//
//   node docs/glyph-examples/render.mjs <sheet.html> <out.png> [--scale 1|2] [--width 1400]
//                                       [--clip x,y,width,height]
//
// The capture covers the whole page (or the CSS-pixel clip) at the given
// device scale factor. Set CHROME_PATH to choose the browser executable.

import { spawn } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

function chromePath() {
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

function parseArgs(argv) {
  const [sheet, output, ...rest] = argv;
  if (!sheet || !output) throw new Error("usage: render.mjs <sheet.html> <out.png> [--scale 1|2] [--width N] [--clip x,y,w,h]");
  const options = { sheet: resolve(sheet), output: resolve(output), scale: 1, width: 1400, clip: null };
  for (let index = 0; index < rest.length; index += 2) {
    const [flag, value] = [rest[index], rest[index + 1]];
    if (flag === "--scale") options.scale = Number(value);
    else if (flag === "--width") options.width = Number(value);
    else if (flag === "--clip") options.clip = value.split(",").map(Number);
    else throw new Error(`unknown option ${flag}`);
  }
  return options;
}

const sleep = (ms) => new Promise((done) => setTimeout(done, ms));

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const profile = mkdtempSync(join(tmpdir(), "glyph-sheet-"));
  const child = spawn(chromePath(), [
    "--headless=new", "--remote-debugging-port=0", "--remote-allow-origins=*", `--user-data-dir=${profile}`,
    "--no-first-run", "--no-default-browser-check", "--disable-extensions", "--hide-scrollbars",
    "--force-color-profile=srgb", "--disable-lcd-text", "about:blank",
  ], { stdio: "ignore", windowsHide: true });
  try {
    let port = null;
    for (let attempt = 0; attempt < 150 && port === null; attempt += 1) {
      const file = join(profile, "DevToolsActivePort");
      if (existsSync(file)) port = Number(readFileSync(file, "utf8").split("\n")[0]);
      else await sleep(100);
    }
    if (!port) throw new Error("Chrome did not expose a DevTools port");
    const targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
    const page = targets.find((target) => target.type === "page");
    const socket = new WebSocket(page.webSocketDebuggerUrl);
    await new Promise((done, fail) => { socket.onopen = done; socket.onerror = fail; });
    let nextId = 0;
    const pending = new Map();
    const listeners = [];
    socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.id && pending.has(message.id)) {
        const { done, fail } = pending.get(message.id);
        pending.delete(message.id);
        message.error ? fail(new Error(message.error.message)) : done(message.result);
      } else if (message.method) {
        listeners.forEach((listener) => listener(message));
      }
    };
    const send = (method, params = {}) => new Promise((done, fail) => {
      nextId += 1;
      pending.set(nextId, { done, fail });
      socket.send(JSON.stringify({ id: nextId, method, params }));
    });
    await send("Page.enable");
    await send("Emulation.setDeviceMetricsOverride", { width: options.width, height: 900, deviceScaleFactor: options.scale, mobile: false });
    const loaded = new Promise((done) => listeners.push((message) => message.method === "Page.loadEventFired" && done()));
    await send("Page.navigate", { url: pathToFileURL(options.sheet).href });
    await loaded;
    await send("Runtime.evaluate", { expression: "document.fonts.ready", awaitPromise: true });
    const metrics = await send("Page.getLayoutMetrics");
    const height = Math.ceil(metrics.cssContentSize.height);
    await send("Emulation.setDeviceMetricsOverride", { width: options.width, height, deviceScaleFactor: options.scale, mobile: false });
    const [x, y, width, clipHeight] = options.clip ?? [0, 0, options.width, height];
    const shot = await send("Page.captureScreenshot", {
      format: "png", captureBeyondViewport: true, clip: { x, y, width, height: clipHeight, scale: 1 },
    });
    writeFileSync(options.output, Buffer.from(shot.data, "base64"));
    console.log(`${options.output} ${width}x${clipHeight} css px @${options.scale}x`);
    socket.close();
  } finally {
    child.kill();
    await sleep(300);
    rmSync(profile, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 });
  }
}

main().catch((error) => { console.error(error.message); process.exit(1); });
