#!/usr/bin/env node

import { spawn, spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { createServer } from "node:http";
import { mkdir, readFile, rm, stat, writeFile } from "node:fs/promises";
import { existsSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { inspectUiContract } from "./ui-proof.mjs";
import { runTitleBotPilot } from "./titlebot-pilot.mjs";
import { runVisualJudgment } from "./visual-judgment.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const CAPTURE = process.argv.includes("--capture");
const CAPTURE_SODA = process.argv.includes("--capture-soda");
const CAPTURE_SODA_MOTION = process.argv.includes("--soda-motion-frames");
const CAPTURE_GOODTURN = process.argv.includes("--capture-goodturn-workshop");
const CAPTURE_VISUAL_ACCEPTANCE = process.argv.includes("--capture-visual-acceptance");
const CAPTURE_CORRECTION_TRANSFER = process.argv.includes("--capture-correction-transfer");
const CAPTURE_ACCEPTANCE = process.argv.includes("--capture-acceptance-cases");
const CAPTURE_DENSITY = process.argv.includes("--capture-density");
const CAPTURE_TITLEBOT = process.argv.includes("--capture-titlebot");
const CAPTURE_JUDGMENT = process.argv.includes("--capture-visual-judgment");
const CHECKS_ONLY = process.argv.includes("--smoke") || (!CAPTURE && !CAPTURE_SODA && !CAPTURE_SODA_MOTION && !CAPTURE_GOODTURN && !CAPTURE_VISUAL_ACCEPTANCE && !CAPTURE_CORRECTION_TRANSFER && !CAPTURE_ACCEPTANCE && !CAPTURE_DENSITY && !CAPTURE_TITLEBOT && !CAPTURE_JUDGMENT);
const SCENARIO_OPTION_INDEX = process.argv.indexOf("--scenario");
const REQUESTED_SCENARIO = SCENARIO_OPTION_INDEX >= 0 ? process.argv[SCENARIO_OPTION_INDEX + 1] : null;
if (SCENARIO_OPTION_INDEX >= 0 && (!REQUESTED_SCENARIO || REQUESTED_SCENARIO.startsWith("--"))) {
  throw new Error("--scenario requires one benchmark slug or icon-decisions");
}
const DEFAULT_VIEWPORT = { width: 1440, height: 1000 };
const MIME = new Map([
  [".css", "text/css; charset=utf-8"],
  [".html", "text/html; charset=utf-8"],
  [".js", "text/javascript; charset=utf-8"],
  [".json", "application/json; charset=utf-8"],
  [".jpg", "image/jpeg"],
  [".jpeg", "image/jpeg"],
  [".png", "image/png"],
  [".svg", "image/svg+xml"],
  [".gif", "image/gif"],
  [".webp", "image/webp"],
  [".woff2", "font/woff2"],
]);

const scenarios = [
  {
    name: "Goodturn bicycle commerce",
    slug: "bicycle-commerce",
    route: "/benchmarks/bicycle-commerce/index.html",
    requiresReadyMarker: false,
    interact: interactGoodturn,
  },
  {
    name: "Doppler soda campaign",
    slug: "soda-campaign",
    route: "/benchmarks/soda-campaign/index.html",
    requiresReadyMarker: true,
    interact: interactSoda,
    reduced: auditSodaReduced,
  },
  {
    name: "Larkhaven municipal service",
    slug: "municipal-service",
    route: "/benchmarks/forward-tests/municipal-service/index.html",
    requiresReadyMarker: true,
    interact: interactMunicipal,
  },
  {
    name: "Relay North warehouse operations",
    slug: "warehouse-operations",
    route: "/benchmarks/forward-tests/warehouse-operations/index.html",
    requiresReadyMarker: true,
    interact: interactWarehouse,
  },
  {
    name: "Morrow literary publication",
    slug: "literary-publication",
    route: "/benchmarks/forward-tests/literary-publication/index.html",
    requiresReadyMarker: true,
    interact: interactLiterary,
  },
];

const failures = [];
const passes = [];

function check(condition, message) {
  if (!condition) throw new Error(message);
}

function sleep(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

function formatError(error) {
  const primary = error?.stack || error?.message || String(error);
  if (!(error instanceof AggregateError)) return primary;
  const details = Array.from(error.errors || [], (item, index) => {
    const message = item?.stack || item?.message || String(item);
    return `Cleanup cause ${index + 1}: ${message}`;
  });
  return [primary, ...details].join("\n");
}

function waitForChildExit(child, timeoutMilliseconds) {
  if (!child || child.exitCode !== null || child.signalCode !== null) return Promise.resolve(true);
  return new Promise((resolve) => {
    const onExit = () => {
      clearTimeout(timer);
      resolve(true);
    };
    const timer = setTimeout(() => {
      child.off("exit", onExit);
      resolve(false);
    }, timeoutMilliseconds);
    child.once("exit", onExit);
  });
}

async function stopBrowserProcess(browser) {
  const child = browser?.child;
  if (!child || await waitForChildExit(child, 5_000)) return;
  child.kill("SIGKILL");
  if (!await waitForChildExit(child, 10_000)) {
    throw new Error(`Chrome process ${child.pid} did not exit after forced termination.`);
  }
}

async function removeTemporaryProfile(profile) {
  await rm(profile, {
    recursive: true,
    force: true,
    maxRetries: 12,
    retryDelay: 100,
  });
}

function resolveChrome() {
  const configured = process.env.CHROME_PATH;
  const directCandidates = configured ? [configured] : [];
  if (process.platform === "win32") {
    directCandidates.push(
      "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
      "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
      "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
      "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
    );
  } else if (process.platform === "darwin") {
    directCandidates.push(
      "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
      "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    );
  } else {
    directCandidates.push("/usr/bin/google-chrome", "/usr/bin/google-chrome-stable", "/usr/bin/chromium", "/usr/bin/chromium-browser");
  }

  for (const candidate of directCandidates) {
    if (candidate && existsSync(candidate)) return candidate;
  }

  if (process.platform !== "win32") {
    for (const name of ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge"]) {
      const result = spawnSync("which", [name], { encoding: "utf8" });
      if (result.status === 0 && result.stdout.trim()) return result.stdout.trim();
    }
  }
  throw new Error("No Chrome/Chromium executable found. Set CHROME_PATH to run browser smoke checks.");
}

function reservePort() {
  return new Promise((resolve, reject) => {
    const probe = createServer();
    probe.once("error", reject);
    probe.listen(0, "127.0.0.1", () => {
      const { port } = probe.address();
      probe.close((error) => error ? reject(error) : resolve(port));
    });
  });
}

async function startStaticServer() {
  const server = createServer(async (request, response) => {
    try {
      const url = new URL(request.url || "/", "http://127.0.0.1");
      if (url.pathname === "/favicon.ico") {
        response.writeHead(204);
        response.end();
        return;
      }
      const relative = decodeURIComponent(url.pathname).replace(/^\/+/, "");
      let filename = path.resolve(ROOT, relative || "index.html");
      if (filename !== ROOT && !filename.startsWith(`${ROOT}${path.sep}`)) {
        response.writeHead(403);
        response.end("Forbidden");
        return;
      }
      const details = await stat(filename);
      if (details.isDirectory()) filename = path.join(filename, "index.html");
      const body = await readFile(filename);
      response.writeHead(200, {
        "Cache-Control": "no-store",
        "Content-Type": MIME.get(path.extname(filename).toLowerCase()) || "application/octet-stream",
      });
      response.end(body);
    } catch (error) {
      response.writeHead(error?.code === "ENOENT" ? 404 : 500, { "Content-Type": "text/plain; charset=utf-8" });
      response.end(error?.code === "ENOENT" ? "Not found" : "Server error");
    }
  });
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  return { server, port: server.address().port };
}

class CdpClient {
  constructor(url) {
    this.url = url;
    this.id = 0;
    this.pending = new Map();
    this.listeners = new Map();
  }

  async connect() {
    this.socket = new WebSocket(this.url);
    await new Promise((resolve, reject) => {
      this.socket.addEventListener("open", resolve, { once: true });
      this.socket.addEventListener("error", reject, { once: true });
    });
    this.socket.addEventListener("message", (event) => {
      const message = JSON.parse(event.data);
      if (message.id) {
        const pending = this.pending.get(message.id);
        if (!pending) return;
        this.pending.delete(message.id);
        if (message.error) pending.reject(new Error(`${pending.method}: ${message.error.message}`));
        else pending.resolve(message.result || {});
        return;
      }
      for (const listener of this.listeners.get(message.method) || []) listener(message.params || {});
    });
    this.socket.addEventListener("close", () => {
      for (const pending of this.pending.values()) pending.reject(new Error("Chrome DevTools connection closed"));
      this.pending.clear();
    });
  }

  send(method, params = {}) {
    const id = ++this.id;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject, method });
      this.socket.send(JSON.stringify({ id, method, params }));
    });
  }

  on(method, listener) {
    const group = this.listeners.get(method) || [];
    group.push(listener);
    this.listeners.set(method, group);
  }

  once(method, timeout = 10_000) {
    return new Promise((resolve, reject) => {
      const listener = (params) => {
        clearTimeout(timer);
        const group = this.listeners.get(method) || [];
        this.listeners.set(method, group.filter((candidate) => candidate !== listener));
        resolve(params);
      };
      const timer = setTimeout(() => {
        const group = this.listeners.get(method) || [];
        this.listeners.set(method, group.filter((candidate) => candidate !== listener));
        reject(new Error(`Timed out waiting for ${method}`));
      }, timeout);
      this.on(method, listener);
    });
  }

  close() {
    this.socket?.close();
  }
}

async function launchBrowser(chrome, debugPort, profile) {
  const args = [
    "--headless=new",
    `--remote-debugging-port=${debugPort}`,
    "--remote-debugging-address=127.0.0.1",
    "--remote-allow-origins=*",
    `--user-data-dir=${profile}`,
    "--disable-background-networking",
    "--disable-component-update",
    "--disable-default-apps",
    "--disable-extensions",
    "--disable-features=Translate,BackForwardCache,MediaRouter",
    "--hide-scrollbars",
    "--disable-sync",
    "--metrics-recording-only",
    "--mute-audio",
    "--no-default-browser-check",
    "--no-first-run",
    "--no-sandbox",
    "--window-size=1440,1000",
    "about:blank",
  ];
  const child = spawn(chrome, args, { stdio: "ignore", windowsHide: true });
  const deadline = Date.now() + 15_000;
  let targets;
  while (Date.now() < deadline) {
    if (child.exitCode !== null) throw new Error(`Chrome exited before CDP became available (code ${child.exitCode}).`);
    try {
      const response = await fetch(`http://127.0.0.1:${debugPort}/json/list`);
      if (response.ok) {
        targets = await response.json();
        if (targets.some((target) => target.type === "page" && target.webSocketDebuggerUrl)) break;
      }
    } catch {
      // Chrome is still starting.
    }
    await sleep(100);
  }
  const target = targets?.find((candidate) => candidate.type === "page" && candidate.webSocketDebuggerUrl);
  if (!target) throw new Error("Chrome did not expose a page target within 15 seconds.");
  return { child, target };
}

let diagnostics = null;

async function configureClient(client, origin) {
  diagnostics = { exceptions: [], consoleErrors: [], failedRequests: [], badResponses: [] };
  const requests = new Map();
  client.on("Network.requestWillBeSent", ({requestId, request}) => {
    requests.set(requestId, `${request.method} ${request.url}`);
    if (requests.size > 2000) requests.delete(requests.keys().next().value);
  });
  client.on("Runtime.exceptionThrown", ({ exceptionDetails }) => {
    diagnostics.exceptions.push(exceptionDetails?.exception?.description || exceptionDetails?.text || "Unknown runtime exception");
  });
  client.on("Runtime.consoleAPICalled", ({ type, args }) => {
    if (type !== "error" && type !== "assert") return;
    diagnostics.consoleErrors.push(args.map((arg) => arg.value ?? arg.description ?? "").join(" "));
  });
  client.on("Network.loadingFailed", ({ canceled, errorText, requestId }) => {
    if (!canceled && errorText !== "net::ERR_ABORTED") diagnostics.failedRequests.push(`${requests.get(requestId) || requestId}: ${errorText}`);
    requests.delete(requestId);
  });
  client.on("Network.responseReceived", ({ response }) => {
    if (response.url.startsWith(origin) && response.status >= 400) diagnostics.badResponses.push(`${response.status} ${response.url}`);
  });
  await Promise.all([
    client.send("Page.enable"),
    client.send("Runtime.enable"),
    client.send("Network.enable"),
  ]);
}

async function evaluate(client, expression) {
  const result = await client.send("Runtime.evaluate", {
    expression,
    awaitPromise: true,
    returnByValue: true,
    userGesture: true,
  });
  if (result.exceptionDetails) {
    throw new Error(result.exceptionDetails.exception?.description || result.exceptionDetails.text || "Evaluation failed");
  }
  return result.result?.value;
}

async function waitFor(client, expression, description, timeout = 5_000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    if (await evaluate(client, `Boolean(${expression})`)) return;
    await sleep(50);
  }
  throw new Error(`Timed out waiting for ${description}`);
}

async function waitForOwningDialogMotionToSettle(client, targetSelector, description, timeout = 5_000) {
  const serializedTargetSelector = JSON.stringify(targetSelector);
  const deadline = Date.now() + timeout;
  let previousBounds = null;
  let stableSamples = 0;

  while (Date.now() < deadline) {
    const state = await evaluate(client, `(() => {
      const target = document.querySelector(${serializedTargetSelector});
      const element = target?.closest("dialog[open]");
      if (!element) return null;
      void getComputedStyle(element).transform;
      const bounds = element.getBoundingClientRect();
      return {
        bounds: [bounds.x, bounds.y, bounds.width, bounds.height],
        activeMotion: element.getAnimations().some((animation) =>
          animation.pending || animation.playState === "running" || animation.playState === "paused"
        ),
      };
    })()`);
    check(state, `Missing owning dialog while waiting for ${description}: ${targetSelector}`);
    const boundsStable = previousBounds !== null
      && state.bounds.every((value, index) => Math.abs(value - previousBounds[index]) < 0.01);
    stableSamples = !state.activeMotion && boundsStable ? stableSamples + 1 : 0;
    if (stableSamples >= 2) return;
    previousBounds = state.bounds;
    await sleep(50);
  }
  throw new Error(`Timed out waiting for ${description}`);
}

async function setViewport(client, { width, height }, reducedMotion = false) {
  await client.send("Emulation.setDeviceMetricsOverride", {
    width,
    height,
    deviceScaleFactor: 1,
    mobile: width <= 480,
    screenWidth: width,
    screenHeight: height,
  });
  await client.send("Emulation.setEmulatedMedia", {
    media: "screen",
    features: [
      { name: "prefers-reduced-motion", value: reducedMotion ? "reduce" : "no-preference" },
      { name: "forced-colors", value: "none" },
    ],
  });
}

async function setForcedColors(client, active) {
  await client.send("Emulation.setEmulatedMedia", {
    media: "screen",
    features: [
      { name: "prefers-reduced-motion", value: "no-preference" },
      { name: "forced-colors", value: active ? "active" : "none" },
    ],
  });
  await sleep(40);
}

async function movePointerToSelector(client, selector) {
  const rect = await evaluate(client, `(() => {
    const node = document.querySelector(${JSON.stringify(selector)});
    if (!node) return null;
    const bounds = node.getBoundingClientRect();
    return { x: bounds.left + bounds.width / 2, y: bounds.top + bounds.height / 2, width: bounds.width, height: bounds.height };
  })()`);
  check(rect && rect.width > 0 && rect.height > 0, `Missing or invisible hover target ${selector}`);
  await client.send("Input.dispatchMouseEvent", { type: "mouseMoved", x: rect.x, y: rect.y });
  await sleep(40);
}

async function movePointerAway(client) {
  await client.send("Input.dispatchMouseEvent", { type: "mouseMoved", x: 1, y: 1 });
  await sleep(20);
}

async function navigate(client, origin, scenario, viewport = DEFAULT_VIEWPORT, reducedMotion = false) {
  diagnostics = { exceptions: [], consoleErrors: [], failedRequests: [], badResponses: [] };
  await setViewport(client, viewport, reducedMotion);
  const loaded = client.once("Page.loadEventFired");
  const url = new URL(scenario.route, origin);
  url.searchParams.set("smoke", String(Date.now()));
  await client.send("Page.navigate", { url: url.href });
  await loaded;
  await evaluate(client, `(async () => {
    if (document.fonts?.ready) await document.fonts.ready;
    return document.readyState;
  })()`);
  await waitFor(client, "document.readyState === 'complete'", "document ready state");
  if (scenario.requiresReadyMarker) await waitFor(client, "window.__benchmarkReady === true", "benchmark ready marker");
  await sleep(80);
}

async function commonAudit(client, scenario, viewport, reducedMotion) {
  const report = await evaluate(client, `(() => {
    const duplicateIds = [...document.querySelectorAll("[id]")]
      .map((node) => node.id)
      .filter((id, index, all) => id && all.indexOf(id) !== index);
    const buttonName = (button) => {
      const labelledBy = button.getAttribute("aria-labelledby");
      const labelledText = labelledBy ? labelledBy.split(/\\s+/).map((id) => document.getElementById(id)?.textContent || "").join(" ") : "";
      return button.getAttribute("aria-label") || labelledText || button.textContent || button.title || "";
    };
    const unlabeledButtons = [...document.querySelectorAll("button")]
      .filter((button) => !buttonName(button).trim())
      .map((button) => button.outerHTML.slice(0, 160));
    const invalidDialogs = [...document.querySelectorAll("dialog")].filter((dialog) => {
      const labelledBy = dialog.getAttribute("aria-labelledby");
      const label = dialog.getAttribute("aria-label");
      return !(label?.trim() || (labelledBy && document.getElementById(labelledBy)?.textContent.trim()));
    }).map((dialog) => dialog.id || dialog.outerHTML.slice(0, 80));
    const brokenImages = [...document.images]
      .filter((image) => image.complete && image.naturalWidth === 0)
      .map((image) => image.currentSrc || image.src);
    const activeAnimations = document.getAnimations()
      .filter((animation) => animation.playState === "running" || animation.playState === "pending")
      .map((animation) => animation.effect?.target?.className || animation.effect?.target?.tagName || "unknown");
    return {
      title: document.title,
      readyState: document.readyState,
      benchmarkReady: window.__benchmarkReady,
      duplicateIds,
      unlabeledButtons,
      invalidDialogs,
      brokenImages,
      activeAnimations,
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      reducedMotion: matchMedia("(prefers-reduced-motion: reduce)").matches,
      bodyTextLength: document.body.innerText.trim().length,
    };
  })()`);
  check(report.title.trim(), `${scenario.name}: missing document title`);
  check(report.readyState === "complete", `${scenario.name}: document did not finish loading`);
  check(!scenario.requiresReadyMarker || report.benchmarkReady === true, `${scenario.name}: benchmark JS did not initialize`);
  check(report.bodyTextLength > 300, `${scenario.name}: page content is unexpectedly empty`);
  check(report.duplicateIds.length === 0, `${scenario.name}: duplicate IDs: ${report.duplicateIds.join(", ")}`);
  check(report.unlabeledButtons.length === 0, `${scenario.name}: unnamed buttons: ${report.unlabeledButtons.join(" | ")}`);
  check(report.invalidDialogs.length === 0, `${scenario.name}: unlabeled dialogs: ${report.invalidDialogs.join(", ")}`);
  check(report.brokenImages.length === 0, `${scenario.name}: broken images: ${report.brokenImages.join(", ")}`);
  check(report.overflow <= 1, `${scenario.name}: ${report.overflow}px horizontal overflow at ${viewport.width}px`);
  check(diagnostics.exceptions.length === 0, `${scenario.name}: runtime exceptions: ${diagnostics.exceptions.join(" | ")}`);
  check(diagnostics.consoleErrors.length === 0, `${scenario.name}: console errors: ${diagnostics.consoleErrors.join(" | ")}`);
  check(diagnostics.failedRequests.length === 0, `${scenario.name}: failed network requests: ${diagnostics.failedRequests.join(" | ")}`);
  check(diagnostics.badResponses.length === 0, `${scenario.name}: HTTP failures: ${diagnostics.badResponses.join(" | ")}`);
  if (reducedMotion) {
    check(report.reducedMotion, `${scenario.name}: reduced-motion emulation did not reach the page`);
    check(report.activeAnimations.length === 0, `${scenario.name}: active animations under reduced motion: ${report.activeAnimations.join(", ")}`);
  }
}

async function click(client, selector) {
  const found = await evaluate(client, `(() => { const node = document.querySelector(${JSON.stringify(selector)}); if (!node) return false; node.click(); return true; })()`);
  check(found, `Missing click target ${selector}`);
  await sleep(40);
}

async function waitForExpression(client, expression, timeoutMilliseconds = 1_000) {
  const deadline = Date.now() + timeoutMilliseconds;
  while (Date.now() < deadline) {
    if (await evaluate(client, expression)) return true;
    await sleep(25);
  }
  return false;
}

async function dragHorizontally(client, selector, distance) {
  const rect = await evaluate(client, `(() => {
    const node = document.querySelector(${JSON.stringify(selector)});
    if (!node) return null;
    const bounds = node.getBoundingClientRect();
    return { x: bounds.left + bounds.width / 2, y: bounds.top + bounds.height / 2 };
  })()`);
  check(rect, `Missing drag target ${selector}`);
  await client.send("Input.dispatchMouseEvent", { type: "mouseMoved", x: rect.x, y: rect.y });
  await client.send("Input.dispatchMouseEvent", { type: "mousePressed", x: rect.x, y: rect.y, button: "left", buttons: 1, clickCount: 1 });
  for (let step = 1; step <= 4; step += 1) {
    await client.send("Input.dispatchMouseEvent", { type: "mouseMoved", x: rect.x + distance * step / 4, y: rect.y, button: "left", buttons: 1 });
    await sleep(20);
  }
  await client.send("Input.dispatchMouseEvent", { type: "mouseReleased", x: rect.x + distance, y: rect.y, button: "left", buttons: 0, clickCount: 1 });
  await sleep(500);
}

async function setValue(client, selector, value) {
  const found = await evaluate(client, `(() => {
    const node = document.querySelector(${JSON.stringify(selector)});
    if (!node) return false;
    const descriptor = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(node), "value");
    if (descriptor?.set) descriptor.set.call(node, ${JSON.stringify(value)}); else node.value = ${JSON.stringify(value)};
    node.dispatchEvent(new Event("input", { bubbles: true }));
    node.dispatchEvent(new Event("change", { bubbles: true }));
    return true;
  })()`);
  check(found, `Missing input target ${selector}`);
  await sleep(30);
}

async function key(client, keyValue, code = keyValue) {
  const keyCodes = {End:35,Home:36,Escape:27,Tab:9,Enter:13,ArrowLeft:37,ArrowRight:39};
  const nativeCode = keyCodes[keyValue] ? {windowsVirtualKeyCode:keyCodes[keyValue]} : {};
  await client.send("Input.dispatchKeyEvent", { type: "keyDown", key: keyValue, code, ...nativeCode, ...(keyValue === "Enter" ? {text:"\r",unmodifiedText:"\r"} : {}) });
  await client.send("Input.dispatchKeyEvent", { type: "keyUp", key: keyValue, code, ...nativeCode });
  await sleep(30);
}

async function interactGoodturn(client) {
  const iconState = await evaluate(client, `(() => {
    const articles = [...document.querySelectorAll(".service-grid article")];
    const exchange = articles.find((article) => article.querySelector("h3")?.textContent.trim() === "Right-ride exchange");
    const icon = exchange?.querySelector(".service-icon--exchange");
    const rect = icon?.getBoundingClientRect();
    const style = icon ? getComputedStyle(icon) : null;
    return {
      count: document.querySelectorAll(".service-icon").length,
      exchangeClass: Boolean(icon),
      width: rect?.width || 0,
      height: rect?.height || 0,
      mask: style?.maskImage || style?.webkitMaskImage || "",
    };
  })()`);
  check(
    iconState.count === 4 && iconState.exchangeClass && iconState.width >= 31 && iconState.height >= 31 && iconState.mask.includes("exchange.svg"),
    `Goodturn: rendered exchange icon is missing, mis-sized, or unbound (${JSON.stringify(iconState)})`,
  );
  await click(client, "[data-finder-next]");
  let result = await evaluate(client, `({ error: document.querySelector("[data-finder-error]").textContent.trim(), step: document.querySelector("[data-step]:not([hidden])")?.dataset.step })`);
  check(result.error && result.step === "0", "Goodturn: finder did not preserve the unanswered step");
  for (const selector of [
    'input[name="day"][value="commute"]',
    'input[name="posture"][value="neutral"]',
    'input[name="priority"][value="light"]',
  ]) {
    await click(client, selector);
    await click(client, "[data-finder-next]");
  }
  result = await evaluate(client, `({ hidden: document.querySelector("[data-finder-result]").hidden, focus: document.activeElement?.getAttribute("data-result-name") !== null })`);
  check(!result.hidden && result.focus, "Goodturn: finder result or focus handoff failed");
  await click(client, '[data-compare="turn-one"]');
  await click(client, '[data-compare="turn-step"]');
  await click(client, "[data-open-compare]");
  result = await evaluate(client, `({ open: document.querySelector("#compare-dialog").open, rows: document.querySelectorAll("[data-comparison-table] tbody tr").length })`);
  check(result.open && result.rows >= 2, "Goodturn: comparison dialog failed");
  await click(client, "#compare-dialog [data-close-dialog]");
}

async function interactSoda(client) {
  await evaluate(client, `document.querySelector("#interactive-can").focus()`);
  const beforeYaw = await evaluate(client, `document.querySelector("[data-can-object]").style.getPropertyValue("--yaw")`);
  await key(client, "ArrowRight");
  await sleep(300);
  const afterYaw = await evaluate(client, `document.querySelector("[data-can-object]").style.getPropertyValue("--yaw")`);
  check(beforeYaw !== afterYaw, "Doppler: keyboard can rotation did not update the product orientation");

  const beforeDragYaw = await evaluate(client, `document.querySelector("[data-can-object]").style.getPropertyValue("--yaw")`);
  await dragHorizontally(client, "#interactive-can", 84);
  const afterDragYaw = await evaluate(client, `document.querySelector("[data-can-object]").style.getPropertyValue("--yaw")`);
  check(beforeDragYaw !== afterDragYaw, "Doppler: pointer drag did not rotate the product");

  await click(client, '.flavor-button[data-flavor-button="pink"]');
  await sleep(760);
  let result = await evaluate(client, `({
    flavor: document.body.dataset.flavor,
    pressed: document.querySelector('.flavor-button[data-flavor-button="pink"]').getAttribute("aria-pressed"),
    synced: document.querySelector('.signal-row[data-flavor-button="pink"]').getAttribute("aria-pressed"),
    label: document.querySelector("#interactive-can").getAttribute("aria-label"),
    live: document.querySelector("[data-flavor-status]").textContent,
    yaw: Number.parseFloat(document.querySelector("[data-can-object]").style.getPropertyValue("--yaw")),
  })`);
  check(result.flavor === "pink" && result.pressed === "true" && result.synced === "true", "Doppler: flavor state did not synchronize");
  check(result.label.includes("Pink Noise") && result.live.includes("Grapefruit"), "Doppler: selected product name/blend was not announced");
  check(Math.abs(result.yaw % 360) < 0.2, `Doppler: flavor rotation did not settle on the package face (${result.yaw})`);

  await click(client, '[data-pack-row="sun"] [data-pack-action="decrease"]');
  result = await evaluate(client, `({ total: document.querySelector("[data-pack-total]").textContent, disabled: document.querySelector("[data-pack-submit]").disabled, guidance: document.querySelector("[data-pack-guidance]").textContent })`);
  check(result.total === "5" && result.disabled && result.guidance.includes("1 space"), "Doppler: pack removal/validation state failed");
  await click(client, '[data-pack-row="pink"] [data-pack-action="increase"]');
  await click(client, "[data-pack-submit]");
  result = await evaluate(client, `({
    total: document.querySelector("[data-pack-total]").textContent,
    disabled: document.querySelector("[data-pack-submit]").disabled,
    status: document.querySelector("[data-pack-status]").textContent,
    pink: document.querySelector('[data-pack-count="pink"]').textContent,
  })`);
  check(result.total === "6" && !result.disabled && result.pink === "3", "Doppler: pack composition did not return to six cans");
  check(result.status.includes("Signal packed") && result.status.includes("no order or payment"), "Doppler: honest conversion confirmation failed");
  await sleep(260);
  result = await evaluate(client, `({
    active: document.getAnimations().filter((animation) => animation.playState === "running" || animation.playState === "pending").length,
    bubbles: document.querySelectorAll(".bubble").length,
  })`);
  check(result.active === 0 && result.bubbles === 0, `Doppler: transient motion did not stop (animations ${result.active}, bubbles ${result.bubbles})`);
}

async function auditSodaReduced(client) {
  let result = await evaluate(client, `(() => {
    const threeD = document.querySelector(".can-3d");
    const staticCan = document.querySelector(".static-can");
    return {
      reduced: matchMedia("(prefers-reduced-motion: reduce)").matches,
      threeD: getComputedStyle(threeD).display,
      staticCan: getComputedStyle(staticCan).display,
      staticLabel: document.querySelector("[data-static-label]").getAttribute("src"),
    };
  })()`);
  check(result.reduced && result.threeD === "none" && result.staticCan !== "none", "Doppler: reduced mode did not select the static product composition");
  result = await evaluate(client, `(() => {
    const button = document.querySelector('.flavor-button[data-flavor-button="night"]');
    button.click();
    return {
      flavor: document.body.dataset.flavor,
      label: document.querySelector("[data-static-label]").getAttribute("src"),
      pressed: button.getAttribute("aria-pressed"),
      active: document.getAnimations().filter((animation) => animation.playState === "running" || animation.playState === "pending").length,
    };
  })()`);
  check(result.flavor === "night" && result.label.endsWith("night-signal.svg") && result.pressed === "true", "Doppler: reduced flavor state lost product identity");
  check(result.active === 0, `Doppler: reduced flavor interaction immediately started ${result.active} animations`);
  await sleep(40);
  const settledAnimations = await evaluate(client, `document.getAnimations().filter((animation) => animation.playState === "running" || animation.playState === "pending").length`);
  check(settledAnimations === 0, `Doppler: reduced flavor interaction started ${settledAnimations} animations`);
}

async function interactMunicipal(client) {
  await click(client, "#language-toggle");
  check(await evaluate(client, `document.documentElement.lang === "ro" && document.querySelector("#language-toggle").textContent.trim() === "EN"`), "Municipal: language switch failed");
  await click(client, "#language-toggle");
  await click(client, '#eligibility-form button[type="submit"]');
  let result = await evaluate(client, `({ hidden: document.querySelector("#eligibility-errors").hidden, focus: document.activeElement?.id, errors: document.querySelectorAll("#eligibility-errors li").length })`);
  check(!result.hidden && result.focus === "eligibility-errors" && result.errors === 3, "Municipal: eligibility validation/focus failed");
  for (const selector of [
    'input[name="property"][value="yes"]',
    'input[name="structure"][value="yes"]',
    'input[name="emergency"][value="no"]',
  ]) await click(client, selector);
  await click(client, '#eligibility-form button[type="submit"]');
  result = await evaluate(client, `({ hidden: document.querySelector("#eligibility-result").hidden, focus: document.activeElement?.id })`);
  check(!result.hidden && result.focus === "eligibility-result", "Municipal: result/focus handoff failed");
  await click(client, "#status-open");
  check(await evaluate(client, `document.querySelector("#status-dialog").open`), "Municipal: status dialog failed to open");
  await setValue(client, "#request-reference", "invalid");
  await click(client, '#status-form button[value="default"]');
  result = await evaluate(client, `({ invalid: document.querySelector("#request-reference").getAttribute("aria-invalid"), focus: document.activeElement?.id, hidden: document.querySelector("#reference-error").hidden })`);
  check(result.invalid === "true" && result.focus === "request-reference" && !result.hidden, "Municipal: status validation/focus failed");
  await setValue(client, "#request-reference", "LH-24017");
  await click(client, '#status-form button[value="default"]');
  result = await evaluate(client, `({ hidden: document.querySelector("#status-result").hidden, focus: document.activeElement?.id })`);
  check(!result.hidden && result.focus === "status-result", "Municipal: status result/focus failed");
  await click(client, '#status-form button[value="cancel"]');
  check(await evaluate(client, `!document.querySelector("#status-dialog").open && document.activeElement?.id === "status-open"`), "Municipal: dialog close/focus restoration failed");
}

async function interactWarehouse(client) {
  await click(client, '#queue-body tr[data-id="EX-1838"]');
  check(await evaluate(client, `document.querySelector("#detail-id").textContent === "EX-1838"`), "Warehouse: row-to-inspector selection failed");
  await evaluate(client, `document.querySelector("#refresh-queue").focus()`);
  await key(client, "/", "Slash");
  check(await evaluate(client, `document.activeElement?.id === "queue-search"`), "Warehouse: slash shortcut did not focus search");
  await setValue(client, "#queue-search", "seal");
  let searchState = await evaluate(client, `({
    value: document.querySelector("#queue-search").value,
    visible: [...document.querySelectorAll("#queue-body tr")].filter((row) => !row.hidden).map((row) => row.dataset.id),
    filters: [...document.querySelectorAll("[data-filter]")].map((button) => ({ filter: button.dataset.filter, pressed: button.getAttribute("aria-pressed") })),
    rows: [...document.querySelectorAll("#queue-body tr")].map((row) => ({ id: row.dataset.id, filter: row.dataset.filter, hasSeal: row.textContent.toLowerCase().includes("seal"), hidden: row.hidden })),
  })`);
  check(searchState.value === "seal" && searchState.visible.length === 1 && searchState.visible[0] === "EX-1838", `Warehouse: queue search failed (${JSON.stringify(searchState)})`);
  await setValue(client, "#queue-search", "");
  await click(client, '[data-filter="critical"]');
  check(await evaluate(client, `document.querySelector('[data-filter="critical"]').getAttribute("aria-pressed") === "true" && [...document.querySelectorAll("#queue-body tr:not([hidden])")].length === 3`), "Warehouse: priority filter failed");
  await click(client, '#queue-body tr[data-id="EX-1842"]');
  await click(client, "#resolve-open");
  await click(client, '#resolve-form button[value="default"]');
  let result = await evaluate(client, `({ hidden: document.querySelector("#resolve-error").hidden, focus: document.activeElement?.id, open: document.querySelector("#resolve-dialog").open })`);
  check(!result.hidden && result.focus === "resolve-error" && result.open, "Warehouse: resolution validation/focus failed");
  await click(client, 'input[name="resolution"][value="replenish"]');
  await setValue(client, "#resolution-note", "Replenishment released from reserve stock.");
  await click(client, '#resolve-form button[value="default"]');
  result = await evaluate(client, `({ open: document.querySelector("#resolve-dialog").open, toast: document.querySelector("#toast").textContent, hidden: document.querySelector('[data-id="EX-1842"]').hidden, focus: document.activeElement?.id })`);
  check(!result.open && result.hidden && result.toast.includes("audit log") && result.focus === "resolve-open", `Warehouse: resolution commit/audit feedback failed (${JSON.stringify(result)})`);
}

async function interactLiterary(client) {
  await click(client, '[data-size="large"]');
  check(await evaluate(client, `document.querySelector('[data-size="large"]').getAttribute("aria-pressed") === "true" && getComputedStyle(document.documentElement).getPropertyValue("--reading-size").trim() === "1.3rem"`), "Literary: reading-size control failed");
  await click(client, "#save-story");
  check(await evaluate(client, `document.querySelector("#save-story").getAttribute("aria-pressed") === "true"`), "Literary: save state failed");
  await setValue(client, "#archive-search", "no such issue phrase");
  check(await evaluate(client, `!document.querySelector("#archive-empty").hidden && [...document.querySelectorAll("#archive-list article")].every((item) => item.hidden)`), "Literary: empty archive state failed");
  await setValue(client, "#archive-search", "");
  await click(client, ".membership-open");
  await click(client, '#membership-form button[value="default"]');
  let result = await evaluate(client, `({ hidden: document.querySelector("#membership-error").hidden, focus: document.activeElement?.id, open: document.querySelector("#membership-dialog").open })`);
  check(!result.hidden && result.focus === "membership-error" && result.open, "Literary: membership validation/focus failed");
  await click(client, 'input[name="plan"][value="digital"]');
  await setValue(client, "#member-email", "reader@example.com");
  await click(client, '#membership-form button[value="default"]');
  result = await evaluate(client, `({ hidden: document.querySelector("#membership-result").hidden, focus: document.activeElement?.id })`);
  check(!result.hidden && result.focus === "membership-result", "Literary: membership result/focus failed");
  await click(client, '#membership-form button[value="cancel"]');
  check(await evaluate(client, `!document.querySelector("#membership-dialog").open && document.activeElement?.classList.contains("membership-open")`), "Literary: dialog close/focus restoration failed");
}

async function exerciseMobileNavigation(client, scenario) {
  const definitions = {
    "bicycle-commerce": [".menu-button", "#mobile-menu", "hidden", ".cart-button"],
    "soda-campaign": ["#nav-toggle", "#site-nav", "data"],
    "municipal-service": ["#nav-toggle", "#service-nav", "data", "#language-toggle"],
    "warehouse-operations": ["#rail-toggle", "#app-rail", "data", "#refresh-queue"],
    "literary-publication": ["#issue-toggle", "#publication-nav", "data", ".membership-open"],
  };
  const [toggle, target, mode, outside] = definitions[scenario.slug];
  await click(client, toggle);
  const state = await evaluate(client, `(() => {
    const button = document.querySelector(${JSON.stringify(toggle)});
    const target = document.querySelector(${JSON.stringify(target)});
    return { expanded: button.getAttribute("aria-expanded"), visible: ${JSON.stringify(mode)} === "hidden" ? !target.hidden : target.dataset.open === "true" };
  })()`);
  check(state.expanded === "true" && state.visible, `${scenario.name}: mobile navigation did not open`);
  if (scenario.slug === "soda-campaign") {
    check(
      await waitForExpression(client, `document.activeElement === document.querySelector("#site-nav a")`),
      "Doppler: mobile navigation did not hand focus to the first destination",
    );
    await key(client, "Escape");
    check(await evaluate(client, `document.querySelector("#nav-toggle").getAttribute("aria-expanded") === "false" && document.activeElement?.id === "nav-toggle"`), "Doppler: mobile navigation Escape/focus restoration failed");
    return;
  }

  check(
    await evaluate(client, `document.querySelector(${JSON.stringify(target)}).contains(document.activeElement)`),
    `${scenario.name}: opening mobile navigation did not focus its first destination`,
  );
  await key(client, "Escape");
  const closed = await evaluate(client, `(() => {
    const button = document.querySelector(${JSON.stringify(toggle)});
    const target = document.querySelector(${JSON.stringify(target)});
    return {
      expanded: button.getAttribute("aria-expanded"),
      visible: ${JSON.stringify(mode)} === "hidden" ? !target.hidden : target.dataset.open === "true",
      focusRestored: document.activeElement === button,
      focusInside: target.contains(document.activeElement),
    };
  })()`);
  check(closed.expanded === "false" && !closed.visible && closed.focusRestored && !closed.focusInside, `${scenario.name}: mobile navigation Escape/focus restoration failed (${JSON.stringify(closed)})`);

  await click(client, toggle);
  await click(client, `${target} a`);
  const activated = await evaluate(client, `(() => {
    const button = document.querySelector(${JSON.stringify(toggle)});
    const target = document.querySelector(${JSON.stringify(target)});
    return {
      expanded: button.getAttribute("aria-expanded"),
      visible: ${JSON.stringify(mode)} === "hidden" ? !target.hidden : target.dataset.open === "true",
      focusInsideHiddenNavigation: target.contains(document.activeElement) && getComputedStyle(target).display === "none",
    };
  })()`);
  check(activated.expanded === "false" && !activated.visible && !activated.focusInsideHiddenNavigation, `${scenario.name}: destination activation left mobile navigation open or focus hidden (${JSON.stringify(activated)})`);

  await click(client, toggle);
  check(
    await evaluate(client, `document.querySelector(${JSON.stringify(target)}).contains(document.activeElement)`),
    `${scenario.name}: could not establish focus inside mobile navigation before breakpoint transition`,
  );
  if (scenario.slug === "bicycle-commerce") {
    check(
      await evaluate(client, `(() => {
        const target = document.querySelector(${JSON.stringify(target)});
        const active = document.activeElement;
        if (!target.contains(active)) return false;
        active.blur();
        return document.activeElement === document.body;
      })()`),
      "Goodturn: could not model user-agent focus invalidation before breakpoint closure",
    );
  }
  await setViewport(client, DEFAULT_VIEWPORT);
  await waitForExpression(client, `document.querySelector(${JSON.stringify(toggle)}).getAttribute("aria-expanded") === "false"`);
  const insideBreakpoint = await evaluate(client, `(() => {
    const target = document.querySelector(${JSON.stringify(target)});
    const active = document.activeElement;
    const rect = active?.getBoundingClientRect?.();
    return {
      activeTag: active?.tagName,
      activeHref: active?.closest?.("a")?.getAttribute("href"),
      activeVisible: Boolean(rect && rect.width > 0 && rect.height > 0),
      focusInside: target.contains(active),
      focusInPrimaryNavigation: Boolean(document.querySelector(".primary-nav")?.contains(active)),
    };
  })()`);
  check(insideBreakpoint.activeTag !== "BODY" && insideBreakpoint.activeVisible, `${scenario.name}: focus inside mobile navigation was lost at the desktop breakpoint (${JSON.stringify(insideBreakpoint)})`);
  if (scenario.slug === "bicycle-commerce") {
    check(
      insideBreakpoint.focusInPrimaryNavigation && insideBreakpoint.activeHref === "#bikes",
      `Goodturn: breakpoint closure did not preserve the focused destination (${JSON.stringify(insideBreakpoint)})`,
    );
  }

  await setViewport(client, { width: 390, height: 844 });
  await click(client, toggle);
  const focusedOutside = await evaluate(client, `(() => {
    const outside = document.querySelector(${JSON.stringify(outside)});
    outside?.focus();
    return document.activeElement === outside;
  })()`);
  check(focusedOutside, `${scenario.name}: could not establish focus outside mobile navigation`);
  await setViewport(client, DEFAULT_VIEWPORT);
  await waitForExpression(client, `document.querySelector(${JSON.stringify(toggle)}).getAttribute("aria-expanded") === "false"`);
  const breakpoint = await evaluate(client, `(() => {
    const button = document.querySelector(${JSON.stringify(toggle)});
    const target = document.querySelector(${JSON.stringify(target)});
    const outside = document.querySelector(${JSON.stringify(outside)});
    return {
      expanded: button.getAttribute("aria-expanded"),
      focusOutside: document.activeElement === outside,
      focusInside: target.contains(document.activeElement),
    };
  })()`);
  check(breakpoint.expanded === "false" && breakpoint.focusOutside && !breakpoint.focusInside, `${scenario.name}: desktop breakpoint closure stole focus or left it in navigation (${JSON.stringify(breakpoint)})`);
}

async function inspectIconCellContainment(client) {
  return evaluate(client, `(() => {
    const failures = [];
    for (const cell of document.querySelectorAll('.state-cell')) {
      const boundary = cell.getBoundingClientRect();
      const fits = rect => rect.left >= boundary.left - 1 && rect.right <= boundary.right + 1
        && rect.top >= boundary.top - 1 && rect.bottom <= boundary.bottom + 1;
      const nodes = [...cell.querySelectorAll('.preview, .icon, .copy, .copy strong, .copy small, .preview > span:not(.sr-only)')];
      for (const node of nodes) {
        const range = document.createRange();
        range.selectNodeContents(node);
        const textRects = node.matches('.copy strong, .copy small, .preview > span:not(.sr-only):not(.icon):not(.copy)')
          ? [...range.getClientRects()] : [];
        if (!fits(node.getBoundingClientRect()) || textRects.some(rect => !fits(rect))
          || node.scrollWidth > node.clientWidth + 1) {
          failures.push({candidate: cell.closest('.candidate').dataset.candidate,
            state: cell.querySelector('.state-label').textContent, node: node.className || node.tagName});
        }
      }
    }
    return failures;
  })()`);
}

async function inspectRenderedType(client, selector) {
  await evaluate(client, `(async () => {
    document.querySelector(${JSON.stringify(selector)})?.getBoundingClientRect();
    await document.fonts.ready;
    await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  })()`);
  const { root } = await client.send("DOM.getDocument");
  const { nodeId } = await client.send("DOM.querySelector", { nodeId: root.nodeId, selector });
  check(nodeId > 0, `Typography: missing owner ${selector}`);
  const { fonts } = await client.send("CSS.getPlatformFontsForNode", { nodeId });
  const requested = await evaluate(client, `(() => {
    const node = document.querySelector(${JSON.stringify(selector)}), style = getComputedStyle(node);
    const size = parseFloat(style.fontSize);
    return { family: style.fontFamily, weight: style.fontWeight, style: style.fontStyle,
      lineHeight: style.lineHeight === 'normal' ? 'normal' : parseFloat(style.lineHeight)/size,
      tracking: style.letterSpacing === 'normal' ? 0 : parseFloat(style.letterSpacing)/size,
      axes: style.fontVariationSettings };
  })()`);
  return { selector, requested, rendered: fonts.filter(font => font.glyphCount > 0) };
}

async function auditGoodturnTypography(client, probe) {
  // Explicit roles from Goodturn's accepted --display/--body owners, not a global font-count rule.
  await client.send("DOM.enable");
  await client.send("CSS.enable");
  const contract = JSON.parse(await readFile(path.join(ROOT, 'evals/typography/goodturn.json'), 'utf8'));
  const width = await evaluate(client, 'innerWidth');
  const roles = contract.roles.filter(role => (!role.minWidth || width >= role.minWidth) && (!role.maxWidth || width <= role.maxWidth))
    .map(role => role.narrow && width <= role.narrow.maxWidth ? {...role,...role.narrow} : role);
  // The bundled variable Manrope face is reported as "Manrope ExtraLight" by Windows Chrome.
  // Its internal family name is not evidence that a requested 400 weight renders at 200.
  const renderedNames = contract.families;
  const familyMatches = (report, family) => report.requested.family.includes(family)
    && report.rendered.length > 0
    && report.rendered.every(font => font.isCustomFont && renderedNames[family].includes(font.familyName));
  const matches = (report, role) => familyMatches(report, role.family)
    && ['weight','style','axes'].every(key => report.requested[key] === role[key])
    && (report.requested.lineHeight === role.lineHeight || Math.abs(report.requested.lineHeight-role.lineHeight) < .01)
    && Math.abs(report.requested.tracking-role.tracking) < .001;
  const faces = await evaluate(client, `Array.from(document.styleSheets).flatMap(sheet => Array.from(sheet.cssRules)).filter(rule => rule.type === CSSRule.FONT_FACE_RULE).map(rule=>({family:rule.style.fontFamily.replaceAll('"',''),weight:rule.style.fontWeight,style:rule.style.fontStyle,src:rule.style.src}))`);
  for (const font of contract.fonts) {
    check(createHash('sha256').update(await readFile(path.join(ROOT,font.path))).digest('hex') === font.sha256, `Typography: changed font file ${font.path}`);
    check(faces.some(face=>face.family===font.family && face.weight===font.weight && face.style===font.style && face.src.includes(path.basename(font.path))), `Typography: font-face mapping mismatch ${font.path}`);
  }
  for (const state of ['default','menu','booking','product']) {
    const current = roles.filter(role => role.state === state);
    if (!current.length) continue;
    if (state === 'menu') await click(client,'.menu-button');
    if (state === 'booking') { await click(client,'[data-open-booking]'); await waitForOwningDialogMotionToSettle(client,'#booking-dialog','Typography booking'); await setValue(client,'#booking-form input[name="name"]','Alex'); }
    if (state === 'product') { await click(client,'[data-open-product="turn-one"]'); await waitForOwningDialogMotionToSettle(client,'#product-dialog','Typography product'); }
    try {
      for (const role of current) {
        const report = await inspectRenderedType(client, role.selector);
        check(matches(report, role), `Typography role drift (${role.state}): ${JSON.stringify(report)}`);
        if (probe && role.selector === '#booking-form input[name="name"]') {
          const originalStyle = await evaluate(client, `document.querySelector(${JSON.stringify(role.selector)}).getAttribute('style')`);
          try {
            await evaluate(client, `document.querySelector(${JSON.stringify(role.selector)}).style.fontFamily='serif'`);
            check(!matches(await inspectRenderedType(client,role.selector),role),'Typography: native control inheritance mutation missed');
          } finally {
            await evaluate(client, `(()=>{const n=document.querySelector(${JSON.stringify(role.selector)});if(${JSON.stringify(originalStyle)}===null)n.removeAttribute('style');else n.setAttribute('style',${JSON.stringify(originalStyle)})})()`);
          }
        }
      }
    } finally {
      if (state === 'menu') await click(client,'.menu-button');
      if (state === 'booking' || state === 'product') await key(client,'Escape');
    }
  }
  if (!probe) return;
  const original = await evaluate(client, `(() => {
    const node = document.querySelector('.hero-lede');
    return { text: node.textContent, style: node.getAttribute('style') };
  })()`);
  try {
    const role = roles.find(role=>role.selector === '.hero-lede');
    for (const [property,value] of Object.entries({fontFamily:'Georgia,serif',fontWeight:'800',fontStyle:'italic',lineHeight:'2.5',letterSpacing:'0.2em',fontVariationSettings:'"wght" 800'})) {
      await evaluate(client, `document.querySelector('.hero-lede').setAttribute('style',''); document.querySelector('.hero-lede').style[${JSON.stringify(property)}]=${JSON.stringify(value)}`);
      check(!matches(await inspectRenderedType(client,'.hero-lede'),role), `Typography: missed ${property} mutation`);
    }
    await evaluate(client, `(() => {
      const node = document.querySelector('.hero-lede');
      node.removeAttribute('style');
      node.style.fontFamily = 'Manrope, sans-serif';
      node.textContent = 'Workspace Привет';
    })()`);
    const partial = await inspectRenderedType(client, ".hero-lede");
    check(partial.requested.family.includes("Manrope") && !familyMatches(partial, "Manrope")
      && partial.rendered.some(font => font.isCustomFont && renderedNames.Manrope.includes(font.familyName))
      && partial.rendered.some(font => !font.isCustomFont),
    `Typography: missed per-glyph fallback behind a correct family declaration (${JSON.stringify(partial)})`);
  } finally {
    await evaluate(client, `(() => {
      const node = document.querySelector('.hero-lede'), original = ${JSON.stringify(original)};
      node.textContent = original.text;
      if (original.style === null) node.removeAttribute('style'); else node.setAttribute('style', original.style);
    })()`);
  }
  check(matches(await inspectRenderedType(client, ".hero-lede"), roles.find(role=>role.selector === '.hero-lede')), "Typography: failed to restore the original role after probes");
}

async function runSmoke(client, origin) {
  const available = new Set([...scenarios.map((scenario) => scenario.slug), "icon-decisions", "acceptance-cases", "density", "titlebot-hierarchy", "visual-judgment"]);
  if (REQUESTED_SCENARIO && !available.has(REQUESTED_SCENARIO)) {
    throw new Error(`Unknown --scenario ${REQUESTED_SCENARIO}; expected one of: ${[...available].join(", ")}`);
  }
  const activeScenarios = REQUESTED_SCENARIO
    ? scenarios.filter((scenario) => scenario.slug === REQUESTED_SCENARIO)
    : scenarios;
  for (const scenario of activeScenarios) {
    process.stdout.write(`CHECK ${scenario.name}\n`);
    try {
      for (const viewport of [DEFAULT_VIEWPORT, { width: 900, height: 900 }, { width: 390, height: 844 }]) {
        await navigate(client, origin, scenario, viewport);
        await commonAudit(client, scenario, viewport, false);
        if (scenario.slug === "bicycle-commerce") {
          await auditGoodturnTypography(client, viewport.width === 1440);
          // Font-state probes open dialogs and fill native fields; isolate the interaction suite.
          await navigate(client, origin, scenario, viewport);
        }
        if (scenario.slug === "soda-campaign") {
          const expectedPanels = viewport.width === 1440 ? 48 : viewport.width === 900 ? 40 : 32;
          check(await evaluate(client, `document.querySelectorAll(".can-panel").length === ${expectedPanels}`), `Doppler: expected ${expectedPanels} can segments at ${viewport.width}px`);
          const lid = await evaluate(client, `(() => {
            const can = document.querySelector("#interactive-can");
            const rim = document.querySelector(".can-lid-visual");
            return {
              topLayers: document.querySelectorAll(".can-lid-visual, .can-disc--top").length,
              widthDelta: Math.abs(can.offsetWidth - rim.offsetWidth),
              leftDelta: Math.abs(can.offsetLeft - rim.offsetLeft),
              attached: rim.offsetTop <= 1 && rim.offsetTop + rim.offsetHeight > 0,
            };
          })()`);
          check(lid.topLayers === 1 && lid.widthDelta < 2 && lid.leftDelta < 2 && lid.attached, `Doppler: product lid layer is duplicated, detached, or misaligned at ${viewport.width}px`);
        }
        if (viewport.width === 390) await exerciseMobileNavigation(client, scenario);
      }
      await navigate(client, origin, scenario, DEFAULT_VIEWPORT);
      await scenario.interact(client);
      await commonAudit(client, scenario, DEFAULT_VIEWPORT, false);
      await navigate(client, origin, scenario, { width: 390, height: 844 }, true);
      await commonAudit(client, scenario, { width: 390, height: 844 }, true);
      if (scenario.reduced) await scenario.reduced(client);
      passes.push(`${scenario.name}: wide/intermediate/mobile, interactions, reduced motion`);
    } catch (error) {
      failures.push(`${scenario.name}: ${error.message}`);
    }
  }

  async function loadIconManifest(client) {
    return evaluate(client, `(async () => {
      const manifestUrl = new URL("/evals/icon-decisions/manifest.json", location.origin);
      const response = await fetch(manifestUrl);
      if (!response.ok) throw new Error("icon decision manifest returned HTTP " + response.status);
      if (response.url !== manifestUrl.href) throw new Error("icon decision manifest followed an unexpected redirect");
      return response.json();
    })()`);
  }

  async function inspectIconContextSource(client, context) {
    return evaluate(client, `(async () => {
      const context = ${JSON.stringify(context)};
      const manifestUrl = new URL("/evals/icon-decisions/manifest.json", location.origin);
      const sourceUrl = new URL(context.context_evidence.source, manifestUrl);
      const response = await fetch(sourceUrl);
      const buffer = await response.arrayBuffer();
      const source = new TextDecoder().decode(buffer);
      const digestBytes = new Uint8Array(await crypto.subtle.digest("SHA-256", buffer));
      const digest = [...digestBytes].map((value) => value.toString(16).padStart(2, "0")).join("");
      let contextFound = false;
      let hostFound = false;
      let selectorError = "";
      let label = "";
      let visibleLabel = "";
      try {
        const parsed = new DOMParser().parseFromString(source, "text/html");
        const contextNode = parsed.querySelector(context.context_evidence.selector);
        const hostNode = parsed.querySelector(context.host_proof.target_selector);
        contextFound = Boolean(contextNode);
        hostFound = Boolean(hostNode);
        const labelNode = context.host_proof.label_selector === "self"
          ? hostNode
          : hostNode?.querySelector(context.host_proof.label_selector);
        label = hostNode?.getAttribute("aria-label")?.trim() || labelNode?.textContent?.trim() || "";
        visibleLabel = hostNode?.textContent?.trim() || "";
      } catch (error) {
        selectorError = error.message;
      }
      return {
        id: context.id,
        source: sourceUrl.pathname,
        responseUrl: response.url,
        route: context.host_proof.route,
        status: response.status,
        responseBound: response.url === sourceUrl.href,
        contextFound,
        hostFound,
        selector: context.context_evidence.selector,
        hostSelector: context.host_proof.target_selector,
        digest,
        expectedDigest: context.context_evidence.source_sha256,
        label,
        expectedLabel: context.host_proof.expected_label,
        visibleLabel,
        expectedVisibleLabel: context.host_proof.expected_visible_label || "",
        selectorError,
      };
    })()`);
  }

  async function inspectIconCandidateBytes(client, candidate) {
    return evaluate(client, `(async () => {
      const candidate = ${JSON.stringify({
        id: candidate.id,
        kind: candidate.kind,
        asset: candidate.asset || "",
        metadata: candidate.metadata || "",
        asset_sha256: candidate.asset_sha256 || "",
        source: candidate.source,
        license: candidate.license,
      })};
      if (candidate.kind === "none") {
        return { candidate: candidate.id, kind: candidate.kind, valid: true, painted: null, paintError: "" };
      }
      const manifestUrl = new URL("/evals/icon-decisions/manifest.json", location.origin);
      const assetUrl = new URL(candidate.asset, manifestUrl);
      const metadataUrl = new URL(candidate.metadata, manifestUrl);
      const [assetResponse, metadataResponse] = await Promise.all([fetch(assetUrl), fetch(metadataUrl)]);
      const responseBound = assetResponse.url === assetUrl.href && metadataResponse.url === metadataUrl.href;
      if (!assetResponse.ok || !metadataResponse.ok || !responseBound) {
        return {
          candidate: candidate.id,
          kind: candidate.kind,
          valid: false,
          assetStatus: assetResponse.status,
          metadataStatus: metadataResponse.status,
          assetPath: assetUrl.pathname,
          metadataPath: metadataUrl.pathname,
          responseBound,
          assetResponseUrl: assetResponse.url,
          metadataResponseUrl: metadataResponse.url,
          paintError: "candidate asset or metadata did not return HTTP 2xx without a redirect",
        };
      }
      const assetBuffer = await assetResponse.arrayBuffer();
      const digestBytes = new Uint8Array(await crypto.subtle.digest("SHA-256", assetBuffer));
      const digest = [...digestBytes].map((value) => value.toString(16).padStart(2, "0")).join("");
      let metadata = null;
      let metadataError = "";
      try {
        metadata = JSON.parse(await metadataResponse.text());
      } catch (error) {
        metadataError = error.message;
      }
      let painted = false;
      let paintError = "";
      let paintMethod = "";
      try {
        const blob = new Blob([assetBuffer], { type: "image/svg+xml" });
        const objectUrl = URL.createObjectURL(blob);
        try {
          const image = new Image();
          image.decoding = "async";
          image.src = objectUrl;
          await image.decode();
          const canvas = document.createElement("canvas");
          canvas.width = 64;
          canvas.height = 64;
          const context2d = canvas.getContext("2d", { willReadFrequently: true });
          if (!context2d) throw new Error("2D canvas context unavailable");
          context2d.clearRect(0, 0, canvas.width, canvas.height);
          context2d.drawImage(image, 0, 0, canvas.width, canvas.height);
          const pixels = context2d.getImageData(0, 0, canvas.width, canvas.height).data;
          painted = Array.from({ length: pixels.length / 4 }, (_, index) => pixels[index * 4 + 3]).some((alpha) => alpha > 0);
          paintMethod = "same-origin SVG decoded into a cleared canvas; at least one alpha channel is nonzero";
        } finally {
          URL.revokeObjectURL(objectUrl);
        }
      } catch (error) {
        paintError = error.message;
      }
      const metadataProvenance = metadata?.provenance || {};
      const metadataMatches = Boolean(
        metadata
        && metadata.name === candidate.id
        && metadata.source === candidate.source
        && metadata.license === candidate.license
        && metadataProvenance.sha256 === digest
        && metadataProvenance.kind === (candidate.kind === "custom" ? "original" : metadataProvenance.kind)
      );
      const valid = Boolean(
        digest === candidate.asset_sha256
        && metadataMatches
        && !metadataError
        && painted
        && !paintError
      );
      return {
        candidate: candidate.id,
        kind: candidate.kind,
        valid,
        assetPath: assetUrl.pathname,
        metadataPath: metadataUrl.pathname,
        responseBound,
        assetResponseUrl: assetResponse.url,
        metadataResponseUrl: metadataResponse.url,
        assetStatus: assetResponse.status,
        metadataStatus: metadataResponse.status,
        digest,
        expectedManifestDigest: candidate.asset_sha256,
        metadataDigest: metadataProvenance.sha256 || "",
        metadataMatches,
        metadataError,
        painted,
        paintMethod,
        paintError,
      };
    })()`);
  }

  async function inspectIconHost(client, context) {
    return evaluate(client, `(() => {
      const proof = ${JSON.stringify(context.host_proof)};
      const target = document.querySelector(proof.target_selector);
      const labelNode = proof.label_selector === "self" ? target : target?.querySelector(proof.label_selector);
      const label = target?.getAttribute("aria-label")?.trim() || labelNode?.textContent?.trim() || "";
      const icon = target?.querySelector(proof.icon_selector);
      const iconBounds = icon?.getBoundingClientRect();
      const targetBounds = target?.getBoundingClientRect();
      const style = icon ? getComputedStyle(icon) : null;
      const targetStyle = target ? getComputedStyle(target) : null;
      const styleSignature = targetStyle ? {
        opacity: targetStyle.opacity,
        cursor: targetStyle.cursor,
        color: targetStyle.color,
        backgroundColor: targetStyle.backgroundColor,
        borderColor: targetStyle.borderColor,
        outlineColor: targetStyle.outlineColor,
        filter: targetStyle.filter,
      } : null;
      const darkSurface = proof.dark_surface_selector ? target?.closest(proof.dark_surface_selector) : null;
      const maskValue = style?.maskImage || style?.webkitMaskImage || "none";
      const maskMatch = String(maskValue).match(/url\\((?:["']?)([^"')]+)(?:["']?)\\)/);
      let maskPath = "";
      if (maskMatch) {
        try { maskPath = new URL(maskMatch[1], location.href).pathname; } catch { maskPath = maskMatch[1]; }
      }
      return {
        found: Boolean(target),
        label,
        visibleText: target?.textContent?.trim() || "",
        styleSignature,
        targetWidth: targetBounds?.width || 0,
        targetHeight: targetBounds?.height || 0,
        iconWidth: iconBounds?.width || 0,
        iconHeight: iconBounds?.height || 0,
        iconVisible: Boolean(icon && style?.display !== "none" && iconBounds?.width > 0 && iconBounds?.height > 0),
        vectorChildren: target?.querySelectorAll("svg, img, picture").length ?? -1,
        mask: maskValue,
        maskPath,
        backgroundImage: targetStyle?.backgroundImage || "none",
        darkSurfaceFound: Boolean(darkSurface),
        darkSurfaceBackground: darkSurface ? getComputedStyle(darkSurface).backgroundColor : "",
      };
    })()`);
  }

  async function renderIconHostCandidate(client, context, candidate, state) {
    const candidateUrl = candidate.asset
      ? new URL(candidate.asset, "http://icon-review.invalid/evals/icon-decisions/manifest.json").pathname
      : "";
    if (state === "hover") await movePointerToSelector(client, context.host_proof.target_selector);
    return evaluate(client, `(async () => {
      const proof = ${JSON.stringify(context.host_proof)};
      const candidate = ${JSON.stringify({ id: candidate.id, kind: candidate.kind, visible_label: candidate.visible_label || "" })};
      const state = ${JSON.stringify(state)};
      const candidatePath = ${JSON.stringify(candidateUrl)};
      const target = document.querySelector(proof.target_selector);
      const frame = () => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
      const maskPath = (value) => {
        const match = String(value || "").match(/url\\((?:["']?)([^"')]+)(?:["']?)\\)/);
        if (!match) return "";
        try { return new URL(match[1], location.href).pathname; } catch { return match[1]; }
      };
      if (!target) return { found: false, candidate: candidate.id, kind: candidate.kind };
      if (candidatePath) {
        const assetResponse = await fetch(candidatePath);
        if (!assetResponse.ok) return { found: true, candidate: candidate.id, kind: candidate.kind, assetStatus: assetResponse.status };
      }
      if (proof.strategy === "service-mask" || proof.strategy === "icon-owner") {
        const icon = target.querySelector(proof.icon_selector);
        if (!icon) return { found: true, candidate: candidate.id, kind: candidate.kind, iconFound: false };
        const priorStyle = icon.getAttribute("style");
        let addedText = null;
        if (candidate.kind === "none") {
          icon.style.display = "none";
          if (proof.strategy === "icon-owner") {
            addedText = document.createTextNode(candidate.visible_label || "");
            target.appendChild(addedText);
          }
        } else {
          icon.style.display = "block";
          icon.style.maskImage = \`url("\${candidatePath}")\`;
          icon.style.webkitMaskImage = \`url("\${candidatePath}")\`;
        }
        await frame();
        const bounds = icon.getBoundingClientRect();
        const style = getComputedStyle(icon);
        const result = {
          found: true,
          candidate: candidate.id,
          kind: candidate.kind,
          iconFound: true,
          iconVisible: style.display !== "none" && bounds.width > 0 && bounds.height > 0,
          width: bounds.width,
          height: bounds.height,
          overflow: 0,
          maskPath: maskPath(style.maskImage || style.webkitMaskImage),
          expectedPath: candidatePath,
          visibleText: target.textContent.trim(),
        };
        if (addedText) addedText.remove();
        if (priorStyle === null) icon.removeAttribute("style"); else icon.setAttribute("style", priorStyle);
        return result;
      }
      const clone = target.cloneNode(true);
      clone.removeAttribute("id");
      clone.dataset.iconReviewCandidate = candidate.id;
      clone.querySelectorAll("svg, img, picture").forEach((node) => node.remove());
      if (candidate.kind === "none") {
        clone.replaceChildren(document.createTextNode(candidate.visible_label || clone.textContent.trim() || ""));
      } else {
        const icon = document.createElement("span");
        icon.className = "icon-review-host-icon";
        icon.setAttribute("aria-hidden", "true");
        icon.style.cssText = "display:inline-block;flex:none;width:1.25rem;height:1.25rem;background:currentColor;-webkit-mask:center / contain no-repeat;mask:center / contain no-repeat;";
        icon.style.maskImage = \`url("\${candidatePath}")\`;
        icon.style.webkitMaskImage = \`url("\${candidatePath}")\`;
        if (proof.strategy === "dialog-clone") clone.replaceChildren(icon, document.createTextNode("Close"));
        else clone.prepend(icon);
      }
      target.parentElement.appendChild(clone);
      if (state === "focus") clone.focus();
      await frame();
      const bounds = clone.getBoundingClientRect();
      const icon = clone.querySelector(".icon-review-host-icon");
      const iconBounds = icon?.getBoundingClientRect();
      const result = {
        found: true,
        candidate: candidate.id,
        kind: candidate.kind,
        iconFound: Boolean(icon),
        iconVisible: Boolean(icon && iconBounds.width > 0 && iconBounds.height > 0),
        width: bounds.width,
        height: bounds.height,
        iconWidth: iconBounds?.width || 0,
        iconHeight: iconBounds?.height || 0,
        overflow: Math.max(0, bounds.left * -1, bounds.right - innerWidth),
        maskPath: maskPath(icon ? getComputedStyle(icon).maskImage || getComputedStyle(icon).webkitMaskImage : ""),
        expectedPath: candidatePath,
        text: clone.textContent.trim(),
        visibleText: clone.textContent.trim(),
        focused: document.activeElement === clone,
        disabled: clone.matches(":disabled"),
        styleSignature: (() => {
          const style = getComputedStyle(clone);
          return {
            opacity: style.opacity,
            cursor: style.cursor,
            color: style.color,
            backgroundColor: style.backgroundColor,
            borderColor: style.borderColor,
            outlineColor: style.outlineColor,
            filter: style.filter,
          };
        })(),
      };
      clone.remove();
      return result;
    })()`);
  }

  async function runIconHostProof(client, origin, context) {
    const proof = context.host_proof;
    const scenario = scenarios.find((item) => item.slug === proof.scenario);
    check(scenario && scenario.route === proof.route, `Icon review: host proof route is not bound to scenario ${proof.scenario}`);
    const comparisonStates = new Set(context.states);
    const mappedComparisonStates = new Set(Object.keys(proof.state_map || {}));
    const exercisedHostStates = new Set(proof.states);
    const expectedStateMap = Object.fromEntries(
      context.states.map((state) => [state, state === "high-contrast" ? "forced-colors" : state]),
    );
    check(
      mappedComparisonStates.size === comparisonStates.size
        && [...comparisonStates].every((state) => mappedComparisonStates.has(state))
        && exercisedHostStates.size === Object.keys(proof.state_map || {}).length
        && [...exercisedHostStates].every((state) => Object.values(proof.state_map || {}).includes(state))
        && (!Object.prototype.hasOwnProperty.call(proof.state_map || {}, "high-contrast") || proof.state_map["high-contrast"] === "forced-colors"),
      `Icon review: ${context.id} comparison states are not mapped one-to-one to exercised host states`,
    );
    check(
      Object.keys(expectedStateMap).length === Object.keys(proof.state_map || {}).length
        && Object.entries(expectedStateMap).every(([comparisonState, hostState]) => proof.state_map[comparisonState] === hostState),
      `Icon review: ${context.id} comparison states do not use canonical host-state bindings`,
    );
    const candidatesById = new Map(context.candidates.map((candidate) => [candidate.id, candidate]));
    const hostCandidates = [context.selected, ...proof.challenger_ids].map((id) => candidatesById.get(id));
    check(hostCandidates.every(Boolean), `Icon review: host proof names an unknown candidate in ${context.id}`);
    const candidateProofs = new Map();
    for (const candidate of hostCandidates) {
      const candidateProof = await inspectIconCandidateBytes(client, candidate);
      check(candidateProof.valid, `Icon review: ${context.id} candidate bytes/metadata/paint proof failed for ${candidate.id} (${JSON.stringify(candidateProof)})`);
      candidateProofs.set(candidate.id, candidateProof);
    }
    const styleChanged = (before, after) => {
      const keys = ["opacity", "cursor", "color", "backgroundColor", "borderColor", "outlineColor", "filter"];
      return Boolean(before && after && keys.some((key) => before[key] !== after[key]));
    };
    for (const viewport of proof.viewports) {
      await navigate(client, origin, scenario, { width: viewport.width, height: viewport.height });
      if (proof.open_selector) {
        await click(client, proof.open_selector);
        const serializedTargetSelector = JSON.stringify(proof.target_selector);
        await waitFor(
          client,
          `document.querySelector(${serializedTargetSelector})?.closest("dialog[open]")`,
          `${context.id} owning host dialog`,
        );
        await waitForOwningDialogMotionToSettle(client, proof.target_selector, `${context.id} owning host dialog motion`);
      }
      const baseline = await inspectIconHost(client, context);
      check(baseline.found && baseline.label === proof.expected_label, `Icon review: ${context.id} host target/label mismatch at ${viewport.name} (${JSON.stringify(baseline)})`);
      if (proof.strategy === "button-clone") {
        check(baseline.visibleText === proof.expected_visible_label,
          `Icon review: ${context.id} visible action text is not bound to the owning control at ${viewport.name} (${JSON.stringify(baseline)})`);
      }
      if (viewport.expected_icon_size != null && context.selected) {
        const selected = candidatesById.get(context.selected);
        if (selected?.kind === "custom" || selected?.kind === "existing") {
          check(Math.abs(baseline.iconWidth - viewport.expected_icon_size) < 0.2 && Math.abs(baseline.iconHeight - viewport.expected_icon_size) < 0.2,
            `Icon review: ${context.id} selected host icon size mismatch at ${viewport.name} (${JSON.stringify(baseline)})`);
        }
      }
      const selected = candidatesById.get(context.selected);
      if ((proof.strategy === "service-mask" || proof.strategy === "icon-owner") && selected?.kind !== "none") {
        const expectedPath = new URL(selected.asset, "http://icon-review.invalid/evals/icon-decisions/manifest.json").pathname;
        check(baseline.maskPath === expectedPath, `Icon review: ${context.id} selected host mask is not bound to its manifest asset at ${viewport.name} (${JSON.stringify(baseline)})`);
      }
      if (selected?.kind === "none" && proof.strategy !== "dialog-clone") {
        check(baseline.vectorChildren === 0 && baseline.mask === "none" && baseline.backgroundImage === "none",
          `Icon review: ${context.id} selected no-icon host is not actually text-only at ${viewport.name} (${JSON.stringify(baseline)})`);
      }
      for (const state of proof.states) {
        if (state === "forced-colors") await setForcedColors(client, true);
        else await setForcedColors(client, false);
        if (state === "hover") await movePointerToSelector(client, proof.target_selector);
        else await movePointerAway(client);
        if (state === "focus") {
          const focused = await evaluate(client, `(() => { const node = document.querySelector(${JSON.stringify(proof.target_selector)}); node?.focus(); return { focused: Boolean(node && document.activeElement === node), same: document.activeElement === node, matches: Boolean(node?.matches(":focus")), active: document.activeElement?.outerHTML?.slice(0, 180) || "", target: node?.outerHTML?.slice(0, 180) || "" }; })()`);
          check(focused.focused, `Icon review: ${context.id} host focus state did not focus its target at ${viewport.name} (${JSON.stringify(focused)})`);
        }
        if (state === "disabled") {
          const disabled = await evaluate(client, `(() => { const node = document.querySelector(${JSON.stringify(proof.target_selector)}); if (!(node instanceof HTMLButtonElement)) return false; node.disabled = true; return node.matches(":disabled"); })()`);
          check(disabled, `Icon review: ${context.id} host disabled state is not represented by the owning button at ${viewport.name}`);
        }
        const stateView = await inspectIconHost(client, context);
        check(stateView.found && stateView.label === proof.expected_label, `Icon review: ${context.id} host ${state} state lost its target/label at ${viewport.name} (${JSON.stringify(stateView)})`);
        if (proof.strategy === "button-clone" && state !== "forced-colors") {
          check(stateView.visibleText === proof.expected_visible_label,
            `Icon review: ${context.id} visible action text changed in ${state} at ${viewport.name} (${JSON.stringify(stateView)})`);
        }
        if (state === "disabled") {
          check(styleChanged(baseline.styleSignature, stateView.styleSignature),
            `Icon review: ${context.id} disabled state has no observable style treatment at ${viewport.name} (${JSON.stringify({ baseline: baseline.styleSignature, disabled: stateView.styleSignature })})`);
        }
        if (state === "dark") {
          check(stateView.darkSurfaceFound && stateView.darkSurfaceBackground === proof.expected_dark_background,
            `Icon review: ${context.id} dark-state proof is not bound to the declared host surface at ${viewport.name} (${JSON.stringify(stateView)})`);
        }
        for (const candidate of hostCandidates) {
          const rendered = await renderIconHostCandidate(client, context, candidate, state);
          check(rendered.found && rendered.assetStatus === undefined, `Icon review: ${context.id} host candidate could not load ${candidate.id} in ${state} at ${viewport.name} (${JSON.stringify(rendered)})`);
          if (candidate.kind === "none") {
            check(!rendered.iconVisible && rendered.overflow <= 1, `Icon review: ${context.id} no-icon candidate is not text-only/contained in ${state} at ${viewport.name} (${JSON.stringify(rendered)})`);
            if (proof.strategy === "button-clone") {
              check(rendered.visibleText === proof.expected_visible_label,
                `Icon review: ${context.id} no-icon candidate ${candidate.id} changed the owning control text in ${state} at ${viewport.name} (${JSON.stringify(rendered)})`);
            }
          } else {
            check(rendered.iconVisible && rendered.maskPath === rendered.expectedPath && rendered.overflow <= 1,
              `Icon review: ${context.id} host candidate ${candidate.id} did not render its exact local asset in ${state} at ${viewport.name} (${JSON.stringify(rendered)})`);
          }
          if (state === "focus" && proof.strategy !== "service-mask" && proof.strategy !== "icon-owner") {
            check(rendered.focused, `Icon review: ${context.id} candidate ${candidate.id} did not render in focus state at ${viewport.name}`);
          }
          if (state === "disabled" && proof.strategy !== "service-mask" && proof.strategy !== "icon-owner") {
            check(rendered.disabled, `Icon review: ${context.id} candidate ${candidate.id} did not render in disabled state at ${viewport.name}`);
            check(styleChanged(baseline.styleSignature, rendered.styleSignature),
              `Icon review: ${context.id} candidate ${candidate.id} disabled clone has no observable style treatment at ${viewport.name} (${JSON.stringify({ baseline: baseline.styleSignature, disabled: rendered.styleSignature })})`);
          }
          if (candidate.kind === "none" && proof.strategy === "icon-owner") {
            check(rendered.visibleText === candidate.visible_label,
              `Icon review: ${context.id} no-icon owner candidate ${candidate.id} did not render its visible label at ${viewport.name}`);
          }
        }
        if (state === "disabled") {
          await evaluate(client, `(() => { const node = document.querySelector(${JSON.stringify(proof.target_selector)}); if (node instanceof HTMLButtonElement) node.disabled = false; })()`);
        }
        await movePointerAway(client);
      }
      await setForcedColors(client, false);
      check(diagnostics.exceptions.length === 0 && diagnostics.consoleErrors.length === 0 && diagnostics.failedRequests.length === 0 && diagnostics.badResponses.length === 0,
        `Icon review: ${context.id} host proof emitted diagnostics at ${viewport.name} (${JSON.stringify(diagnostics)})`);
    }
  }

  if (!REQUESTED_SCENARIO || REQUESTED_SCENARIO === "icon-decisions") {
    process.stdout.write("CHECK Icon decision comparison\n");
    try {
      const comparisonScenario = {
        name: "Icon decision comparison",
        route: "/evals/icon-decisions/comparison.html",
        requiresReadyMarker: false,
      };
      await navigate(client, origin, comparisonScenario, DEFAULT_VIEWPORT);
      const iconManifest = await loadIconManifest(client);
      const expectedSelected = iconManifest.contexts.map((context) => context.selected).filter(Boolean).sort();
      const expectedNoIconIds = iconManifest.contexts.flatMap((context) => context.candidates.filter((candidate) => candidate.kind === "none").map((candidate) => candidate.id));
      const expectedCandidateCount = iconManifest.contexts.reduce((total, context) => total + context.candidates.length, 0);
      const closeTextId = iconManifest.contexts[0]?.candidates.find((candidate) => candidate.kind === "none")?.id || "";
      for (const viewport of [DEFAULT_VIEWPORT, { width: 900, height: 1000 }, { width: 390, height: 844 }]) {
        await navigate(client, origin, comparisonScenario, viewport);
        const report = await evaluate(client, `(() => {
          const selected = [...document.querySelectorAll(".candidate--selected")].map((node) => node.dataset.candidate);
          const iconSizes = [...document.querySelectorAll(".icon")].map((node) => {
            const expected = Number.parseFloat(getComputedStyle(node).getPropertyValue("--icon-size"));
            const bounds = node.getBoundingClientRect();
            const svg = node.querySelector("svg")?.getBoundingClientRect();
            return { expected, width: bounds.width, height: bounds.height, svgWidth: svg?.width || 0, svgHeight: svg?.height || 0 };
          });
          const unnamedButtons = [...document.querySelectorAll("button")].filter((button) =>
            !(button.getAttribute("aria-label") || button.textContent || "").trim()
          ).length;
          const resources = performance.getEntriesByType("resource").map((entry) => entry.name);
          const noIconIds = ${JSON.stringify(expectedNoIconIds)};
          const noIconCards = [...document.querySelectorAll("article.candidate")].filter((card) => noIconIds.includes(card.dataset.candidate));
          const closeText = document.querySelector('[data-candidate="${closeTextId}"] button')?.innerText.trim();
          const stateCoverage = ${JSON.stringify(iconManifest.contexts)}.every((context) => {
            const section = document.getElementById(context.id);
            const states = new Set([...section.querySelectorAll(".state-label")].map((node) => node.textContent.trim()));
            return context.states.every((state) => states.has(state));
          });
          return {
            title: document.title,
            contexts: document.querySelectorAll("section.context").length,
            candidates: document.querySelectorAll("article.candidate").length,
            selected,
            iconSizes,
            unnamedButtons,
            noIconCardsWithoutSvg: noIconCards.length === noIconIds.length && noIconCards.every((card) => !card.querySelector("svg")),
            closeText,
            stateCoverage,
            scripts: document.querySelectorAll("script").length,
            externalResources: resources.filter((url) => !url.startsWith(location.origin)),
            overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
          };
        })()`);
        check(report.title.includes("representative controls"), "Icon review: evidence boundary is missing from the title");
        check(report.contexts === iconManifest.contexts.length && report.candidates === expectedCandidateCount, `Icon review: manifest/comparison counts differ (${JSON.stringify(report)})`);
        check(JSON.stringify(report.selected.sort()) === JSON.stringify(expectedSelected), `Icon review: selected decisions do not match the checked manifest (${report.selected.join(", ")})`);
        check(report.iconSizes.length > 0 && report.iconSizes.every((size) =>
          Number.isFinite(size.expected)
          && Math.abs(size.width - size.expected) < 0.2
          && Math.abs(size.height - size.expected) < 0.2
          && Math.abs(size.svgWidth - size.expected) < 0.2
          && Math.abs(size.svgHeight - size.expected) < 0.2
        ), "Icon review: one or more SVGs did not render at the declared target size");
        check(report.unnamedButtons === 0 && report.noIconCardsWithoutSvg && report.closeText === "Close" && report.stateCoverage, "Icon review: a no-icon, accessible-name, or declared-state comparison is misleading");
        check(report.scripts === 0 && report.externalResources.length === 0, `Icon review: generated evidence is not self-contained (${report.externalResources.join(", ")})`);
        check(report.overflow <= 1, `Icon review: ${report.overflow}px horizontal overflow at ${viewport.width}px`);
        const cellOverflow = await inspectIconCellContainment(client);
        check(cellOverflow.length === 0, `Icon review: content escapes its comparison cell at ${viewport.width}px (${JSON.stringify(cellOverflow)})`);
        if (viewport.width === DEFAULT_VIEWPORT.width) {
          await evaluate(client, `(() => {
            const style = document.createElement('style'); style.id = 'cell-overflow-regression-probe';
            style.textContent = '.state-row--service-item { grid-template-columns:repeat(3,minmax(0,1fr)) } .preview--service-item { min-width:170px }';
            document.head.append(style);
          })()`);
          try {
            check((await inspectIconCellContainment(client)).length > 0, "Icon review: containment check missed the original narrow-cell regression");
          } finally {
            await evaluate(client, "document.getElementById('cell-overflow-regression-probe').remove()");
          }
        }
        check(diagnostics.exceptions.length === 0, `Icon review: runtime exceptions: ${diagnostics.exceptions.join(" | ")}`);
        check(diagnostics.consoleErrors.length === 0, `Icon review: console errors: ${diagnostics.consoleErrors.join(" | ")}`);
        check(diagnostics.failedRequests.length === 0, `Icon review: failed requests: ${diagnostics.failedRequests.join(" | ")}`);
        check(diagnostics.badResponses.length === 0, `Icon review: HTTP failures: ${diagnostics.badResponses.join(" | ")}`);
      }

      const contextBindings = await Promise.all(iconManifest.contexts.map((context) => inspectIconContextSource(client, context)));
      check(
        contextBindings.length === iconManifest.contexts.length
          && contextBindings.every((binding) => binding.status === 200 && binding.contextFound && binding.hostFound
            && binding.selector === binding.hostSelector && binding.source === binding.route
            && binding.responseBound
            && binding.digest === binding.expectedDigest && binding.label === binding.expectedLabel
            && (!binding.expectedVisibleLabel || binding.visibleLabel === binding.expectedVisibleLabel)
            && !binding.selectorError),
        `Icon review: repository-derived context source/digest/selector/label binding failed (${JSON.stringify(contextBindings)})`,
      );
      for (const context of iconManifest.contexts) await runIconHostProof(client, origin, context);
      await runIconStress(client, origin);
      passes.push(`Icon decision comparison: ${iconManifest.contexts.length} contexts, ${expectedCandidateCount} candidates, digest-bound host selectors and candidate bytes/metadata, nontransparent asset paint, selected and rejected candidates rendered in owning hosts, declared states, exact wide/mobile viewports, containment`);
    } catch (error) {
      failures.push(`Icon decision comparison: ${error.message}`);
    }
  }
  if (!REQUESTED_SCENARIO || REQUESTED_SCENARIO === 'acceptance-cases') await runAcceptanceCases(client, origin);
  if (!REQUESTED_SCENARIO || REQUESTED_SCENARIO === 'density') await runDensityCases(client, origin);
  if (!REQUESTED_SCENARIO || REQUESTED_SCENARIO === 'titlebot-hierarchy') await runPilot(client, origin);
  if (!REQUESTED_SCENARIO || REQUESTED_SCENARIO === 'visual-judgment') await runJudgment(client, origin);
}

async function runJudgment(client, origin, capture=false) {
  passes.push(await runVisualJudgment({client,origin,root:ROOT,navigate,evaluate,check,click,key,diagnostics:()=>diagnostics},capture));
}

async function runPilot(client, origin, capture=false) {
  const auditDiagnostics=()=>{
    for(const [kind,items] of Object.entries(diagnostics)) check(items.length===0,`Title Bot ${kind}: ${items.join(' | ')}`);
  };
  passes.push(await runTitleBotPilot({client,origin,root:ROOT,navigate,evaluate,waitFor,setValue,key,check,auditDiagnostics,visibilityRegressions:runVisibilityRegressions},capture));
}

async function runDensityCases(client, origin, capture=false) {
  const dir=path.join(ROOT,'evals/density/captures');
  if(capture) await mkdir(dir,{recursive:true});
  const evidence=[];
  for(const width of [1280,820,390]) {
    const afterQueueAnchors=[];
    for(const state of ['empty','sparse','populated']) {
      let baseline;
      for(const version of ['before','after']) {
        const viewport={width,height:width===390?844:900};
        await navigate(client,origin,{name:'Queue density',route:`/evals/density/fixture.html?v=${version}&state=${state}`,requiresReadyMarker:false},viewport);
        await waitFor(client,'window.__densityReady===true','density fixture');
        const report=await evaluate(client, `(() => {
          const queue=document.querySelector('.queue'),rect=queue.getBoundingClientRect();
          const choices=[...document.querySelectorAll('.choice')];
          const walker=document.createTreeWalker(document.querySelector('.app'),NodeFilter.SHOW_TEXT),content=[];
          while(walker.nextNode()){const value=walker.currentNode.textContent.trim();if(value)content.push(value)}
          const label=document.querySelector('.holder span').getBoundingClientRect(),value=document.querySelector('#holder').getBoundingClientRect();
          return {width:innerWidth,height:innerHeight,dpr:devicePixelRatio,state:document.body.dataset.state,version:document.body.dataset.v,
            text:document.querySelector('.app').innerText,content:content.sort(),overflow:document.documentElement.scrollWidth-innerWidth,
            queueTop:rect.top,queueHeight:rect.height,queueScrollHeight:queue.scrollHeight,
            rowHeights:choices.map(n=>n.getBoundingClientRect().height),labelSizes:choices.map(n=>getComputedStyle(n.querySelector('strong')).fontSize),
            settingsHeight:document.querySelector('.settings').getBoundingClientRect().height,
            holderGap:Math.max(0,value.left-label.right,label.left-value.right,value.top-label.bottom,label.top-value.bottom),
            contentRows:queue.querySelectorAll('.entry').length,
            placeholderSize:document.body.dataset.state==='empty'?getComputedStyle(document.querySelector('#holder')).fontSize:null};
        })()`);
        check(report.width===width && report.state===state && report.version===version && report.overflow<=1,'Density: wrong viewport/state or unexpected horizontal overflow');
        const visibleContract = {required:[{id:'current-holder',selector:'#holder',kind:'text'}]};
        const visible = await evaluate(client, `(${inspectUiContract.toString()})(${JSON.stringify(visibleContract)})`);
        check(!visible.findings.length, `Density: required information is unavailable ${JSON.stringify(visible.findings)}`);
        if(version==='before') baseline=report;
        else {
          afterQueueAnchors.push(report.queueTop);
          check(JSON.stringify(report.content)===JSON.stringify(baseline.content),'Density: challenger removed or changed content');
          check(JSON.stringify(report.labelSizes)===JSON.stringify(baseline.labelSizes) && report.settingsHeight===baseline.settingsHeight,'Density: global shrinking disguised the layout issue');
          check(report.rowHeights.every(h=>h>=44 && h<=68),`Density: declared operator row contract failed ${width}/${state}: ${JSON.stringify(report.rowHeights)}`);
          check(report.holderGap<=16,'Density: related label/value remain scattered across the panel');
          check(report.queueTop<=baseline.queueTop-40 && report.queueTop<viewport.height*.7,'Density: fixed chrome still displaces the working content');
          if(state==='empty') check(report.queueHeight<80 && report.placeholderSize==='14px','Density: empty state retained oversized well/emphasis');
          if(state==='sparse') check(report.contentRows===2 && report.queueHeight<120,'Density: sparse state has unexplained reserved height');
          if(state==='populated') {
            check(report.contentRows===24 && report.queueHeight<=241 && report.queueScrollHeight>report.queueHeight,'Density: populated queue lost internal scrolling');
            await evaluate(client,`document.querySelector('.queue').focus()`);await key(client,'End');
            await waitFor(client,`(()=>{const q=document.querySelector('.queue');return q.scrollTop+q.clientHeight>=q.scrollHeight-1})()`,'density queue keyboard scroll');
            await evaluate(client,`document.querySelector('.queue').scrollTop=0`);
          }
        }
        if(capture) {
          const file=`${version}-${state}-${width}.png`;await screenshotPng(client,path.join(dir,file));
          evidence.push({file,sha256:createHash('sha256').update(await readFile(path.join(dir,file))).digest('hex'),report});
        }
        if(version==='after' && state==='empty' && width===1280) await runVisibilityRegressions(client,visibleContract);
      }
    }
    check(Math.max(...afterQueueAnchors)-Math.min(...afterQueueAnchors)<=8,'Density: state changes destabilized the working-content anchor');
  }
  if(capture) await writeFile(path.join(dir,'evidence.json'),JSON.stringify({fixtureSha256:createHash('sha256').update(await readFile(path.join(ROOT,'evals/density/fixture.html'))).digest('hex'),fontSha256:createHash('sha256').update(await readFile(path.join(ROOT,'benchmarks/bicycle-commerce/assets/fonts/manrope-latin.woff2'))).digest('hex'),captures:evidence},null,2)+'\n');
  passes.push('Operator density: identical empty/sparse/populated content, fixed chrome, preserved label/target sizes and long-queue keyboard scrolling at 1280/820/390; authored contract, not aesthetic certification');
}

async function runVisibilityRegressions(client, contract) {
  const selector = contract.required[0].selector;
  const original = await evaluate(client,`document.querySelector(${JSON.stringify(selector)}).getAttribute('style')`);
  for (const mutation of ['opacity','clip','cover']) {
    try {
      await evaluate(client,`(() => {
        const node=document.querySelector(${JSON.stringify(selector)});
        if(${JSON.stringify(mutation)}==='opacity')node.style.opacity='0';
        if(${JSON.stringify(mutation)}==='clip'){node.style.display='inline-block';node.style.maxWidth='8px';node.style.overflow='hidden';node.style.whiteSpace='nowrap';}
        if(${JSON.stringify(mutation)}==='cover'){const b=node.getBoundingClientRect(),overlay=document.createElement('div');overlay.id='proof-occlusion';overlay.style.cssText='position:fixed;z-index:2147483647;background:#000;left:'+b.left+'px;top:'+b.top+'px;width:'+b.width+'px;height:'+b.height+'px';document.body.append(overlay);}
      })()`);
      const result = await evaluate(client,`(${inspectUiContract.toString()})(${JSON.stringify(contract)})`);
      check(result.findings.some(item=>item.id===contract.required[0].id),`Visibility checker missed ${mutation}`);
    } finally {
      await evaluate(client,`(() => {const node=document.querySelector(${JSON.stringify(selector)});if(${JSON.stringify(original)}===null)node.removeAttribute('style');else node.setAttribute('style',${JSON.stringify(original)});document.querySelector('#proof-occlusion')?.remove()})()`);
    }
  }
  check(!(await evaluate(client,`(${inspectUiContract.toString()})(${JSON.stringify(contract)})`)).findings.length,'Visibility mutations were not restored');
}

async function runIconStress(client, origin) {
  for (const width of [320,390,900,1440]) {
    for (const scale of [1,2]) {
      await navigate(client,origin,{name:'Multilingual icon stress',route:'/evals/icon-decisions/stress.html',requiresReadyMarker:false},{width,height:1000});
      await evaluate(client, `(() => {
        const style=document.createElement('style');
        style.textContent=${JSON.stringify('body{font-size:calc(15px * SCALE)}.state-label,.size-label,.eyebrow,.decision,.kind{font-size:calc(11px * SCALE)}.candidate h3{font-size:calc(22px * SCALE)}dl{font-size:calc(12px * SCALE)}')}.replaceAll('SCALE',${JSON.stringify(String(scale))});
        document.head.append(style);
      })()`);
      const cells=await inspectIconCellContainment(client);
      const result=await evaluate(client, `(() => {
        const failures=[];
        for(const candidate of document.querySelectorAll('.candidate')) {
          const outer=candidate.getBoundingClientRect();
          const header=candidate.querySelector('header'), hb=header.getBoundingClientRect();
          for(const node of candidate.querySelectorAll('h3,.decision,dt,dd')) {
            const b=node.getBoundingClientRect();
            if(b.right>outer.right-1 || b.left<outer.left+1 || node.scrollWidth>node.clientWidth+1) failures.push(node.textContent);
          }
          for(const node of header.querySelectorAll('h3,.decision')) {const b=node.getBoundingClientRect(); if(b.bottom>hb.bottom+1) failures.push('header collision');}
          for(const node of candidate.querySelectorAll('.state--focus')) {const b=node.getBoundingClientRect(),o=node.closest('.state-cell').getBoundingClientRect(),s=getComputedStyle(node),extra=parseFloat(s.outlineWidth)+parseFloat(s.outlineOffset);if(b.left-extra<o.left || b.right+extra>o.right)failures.push('clipped focus');}
        }
        const lang=[...document.querySelectorAll('.context')].map(c=>{const p=c.querySelector('.preview');return [p.lang,p.dir]});
        return {failures,lang,overflow:document.documentElement.scrollWidth-innerWidth};
      })()`);
      check(!cells.length && !result.failures.length && result.overflow<=1, `Icon stress ${width}/${scale}: ${JSON.stringify({cells,...result})}`);
      check(JSON.stringify(result.lang)===JSON.stringify([['ru','auto'],['de','ltr'],['ar','rtl']]),'Icon stress: wrong preview language/direction');
    }
  }
}

async function runAcceptanceCases(client, origin, capture=false) {
  const dir=path.join(ROOT,'evals/acceptance-cases/captures');
  if(capture) await mkdir(dir,{recursive:true});
  const evidence=[];
  for(const name of ['coherent','typography','custom','backings','workspace','resume']) {
    for(const width of [900,390]) {
      for(const version of ['before','after']) {
        await navigate(client,origin,{name,route:`/evals/acceptance-cases/fixture.html?case=${name}&v=${version}`,requiresReadyMarker:false},{width,height:844});
        await waitFor(client,'window.__acceptanceReady===true','acceptance fixture');
        const report=await evaluate(client, `(() => {
          const panel=document.querySelector('.bounded'), list=document.querySelector('.list'),button=document.querySelector('.panel-foot .primary');
          const b=button?.getBoundingClientRect(),p=panel?.getBoundingClientRect();
          return {width:innerWidth,case:document.body.dataset.case,version:document.body.dataset.version,overflow:document.documentElement.scrollWidth-innerWidth,
            bounded:!!list && list.scrollHeight>list.clientHeight && panel.getBoundingClientRect().height<=440.5,
            aligned:!!b && Math.abs((b.left+b.right-p.left-p.right)/2)<1,
            bodyFamilies:[...document.querySelectorAll('.row')].map(n=>getComputedStyle(n).fontFamily),
            backings:[...document.querySelectorAll('.panel .mark')].map(n=>getComputedStyle(n).backgroundColor),
            svg:[...document.querySelectorAll('svg')].map(n=>({width:n.getBoundingClientRect().width,height:n.getBoundingClientRect().height}))};
        })()`);
        check(report.case===name && report.version===version && report.width===width,'Acceptance: incorrect target state');
        check(report.overflow<=1,'Acceptance: unexpected horizontal page overflow');
        if(name==='workspace') {
          check(report.bounded===(version==='after') && report.aligned===(version==='after'),'Acceptance: bounded list/placement regression not distinguished');
          if(version==='after') {
            await evaluate(client,`document.querySelector('.list').focus()`); await key(client,'End');
            await waitFor(client,`(()=>{const list=document.querySelector('.list');return list.scrollTop+list.clientHeight>=list.scrollHeight-1})()`,'keyboard internal scroll end');
            await evaluate(client,`document.querySelector('.list').scrollTop=0`);
          }
        }
        if(name==='typography') check((new Set(report.bodyFamilies).size===1)===(version==='after'),'Acceptance: role drift not distinguished');
        if(['backings','resume'].includes(name)) check(report.backings.every(color=>color==='rgba(0, 0, 0, 0)')===(version==='after'),'Acceptance: passive backings not distinguished');
        if(capture) {
          const file=`${name}-${version}-${width}.png`;await screenshotPng(client,path.join(dir,file));
          evidence.push({file,sha256:createHash('sha256').update(await readFile(path.join(dir,file))).digest('hex'),report});
        }
        if(name==='workspace' && version==='after') {
          for(const state of ['empty','loading']) {
            await navigate(client,origin,{name,route:`/evals/acceptance-cases/fixture.html?case=workspace&v=after&state=${state}`,requiresReadyMarker:false},{width,height:844});
            const valid=await evaluate(client,`(()=>{const list=document.querySelector('.list'),p=document.querySelector('.bounded').getBoundingClientRect(),button=document.querySelector('.panel-foot .primary').getBoundingClientRect();return list.scrollHeight===list.clientHeight && p.height<=440.5 && button.bottom<=innerHeight && !!list.querySelector('[role=status]')})()`);
            check(valid,`Acceptance: ${state} bounded-list state failed`);
          }
        }
      }
    }
  }
  if(capture) await writeFile(path.join(dir,'evidence.json'),JSON.stringify({fixtureSha256:createHash('sha256').update(await readFile(path.join(ROOT,'evals/acceptance-cases/fixture.html'))).digest('hex'),captures:evidence},null,2)+'\n');
  passes.push('Six authored acceptance cases: role preservation/drift, contextual icons, backings, multilingual bounded lists/placement, continuation; technical evidence only');
}

async function screenshot(client, filename, fullPage = false) {
  let clip;
  if (fullPage) {
    const metrics = await client.send("Page.getLayoutMetrics");
    const size = metrics.cssContentSize || metrics.contentSize;
    clip = { x: 0, y: 0, width: size.width, height: size.height, scale: 1 };
  }
  const { data } = await client.send("Page.captureScreenshot", {
    format: "jpeg",
    quality: 88,
    captureBeyondViewport: fullPage,
    fromSurface: true,
    ...(clip ? { clip } : {}),
  });
  await writeFile(filename, Buffer.from(data, "base64"));
}

async function screenshotPng(client, filename) {
  const { data } = await client.send("Page.captureScreenshot", {
    format: "png",
    captureBeyondViewport: false,
    fromSurface: true,
    optimizeForSpeed: true,
  });
  await writeFile(filename, Buffer.from(data, "base64"));
}

async function captureMunicipal(client, origin, scenario) {
  const dir = path.join(ROOT, "benchmarks/forward-tests/municipal-service/screenshots");
  await navigate(client, origin, scenario, DEFAULT_VIEWPORT);
  await screenshot(client, path.join(dir, "desktop-home.jpg"), true);
  for (const selector of ['input[name="property"][value="yes"]', 'input[name="structure"][value="yes"]', 'input[name="emergency"][value="no"]']) await click(client, selector);
  await click(client, '#eligibility-form button[type="submit"]');
  await screenshot(client, path.join(dir, "desktop-result.jpg"));
  await navigate(client, origin, scenario, { width: 900, height: 900 });
  await screenshot(client, path.join(dir, "intermediate-home.jpg"), true);
  await navigate(client, origin, scenario, { width: 390, height: 844 });
  await screenshot(client, path.join(dir, "mobile-home.jpg"), true);
  await click(client, "#nav-toggle");
  await screenshot(client, path.join(dir, "mobile-menu.jpg"));
  await click(client, "#status-open");
  await setValue(client, "#request-reference", "LH-24017");
  await click(client, '#status-form button[value="default"]');
  await screenshot(client, path.join(dir, "mobile-status-dialog.jpg"));
}

async function captureWarehouse(client, origin, scenario) {
  const dir = path.join(ROOT, "benchmarks/forward-tests/warehouse-operations/screenshots");
  await navigate(client, origin, scenario, DEFAULT_VIEWPORT);
  await screenshot(client, path.join(dir, "desktop-queue.jpg"), true);
  await click(client, "#resolve-open");
  await screenshot(client, path.join(dir, "desktop-resolution.jpg"));
  await navigate(client, origin, scenario, { width: 900, height: 900 });
  await screenshot(client, path.join(dir, "intermediate-queue.jpg"), true);
  await navigate(client, origin, scenario, { width: 390, height: 844 });
  await screenshot(client, path.join(dir, "mobile-queue.jpg"), true);
  await click(client, "#rail-toggle");
  await screenshot(client, path.join(dir, "mobile-navigation.jpg"));
  await click(client, "#resolve-open");
  await screenshot(client, path.join(dir, "mobile-resolution.jpg"));
}

async function captureLiterary(client, origin, scenario) {
  const dir = path.join(ROOT, "benchmarks/forward-tests/literary-publication/screenshots");
  await navigate(client, origin, scenario, DEFAULT_VIEWPORT);
  await screenshot(client, path.join(dir, "desktop-issue.jpg"), true);
  await evaluate(client, `document.querySelector("#lead-story").scrollIntoView()`);
  await screenshot(client, path.join(dir, "desktop-reading.jpg"));
  await navigate(client, origin, scenario, { width: 900, height: 900 });
  await screenshot(client, path.join(dir, "intermediate-issue.jpg"), true);
  await navigate(client, origin, scenario, { width: 390, height: 844 });
  await screenshot(client, path.join(dir, "mobile-issue.jpg"), true);
  await click(client, "#issue-toggle");
  await screenshot(client, path.join(dir, "mobile-contents.jpg"));
  await click(client, ".membership-open");
  await screenshot(client, path.join(dir, "mobile-membership.jpg"));
}

async function captureSoda(client, origin, scenario) {
  const dir = path.join(ROOT, "benchmarks/soda-campaign/screenshots");
  await mkdir(dir, { recursive: true });

  await navigate(client, origin, scenario, DEFAULT_VIEWPORT);
  await sleep(1_100);
  await commonAudit(client, scenario, DEFAULT_VIEWPORT, false);
  await screenshot(client, path.join(dir, "wide-overview.jpg"), true);
  await screenshot(client, path.join(dir, "wide-hero.jpg"));

  await click(client, '.flavor-button[data-flavor-button="pink"]');
  await sleep(780);
  await screenshot(client, path.join(dir, "wide-flavor.jpg"));

  await navigate(client, origin, scenario, { width: 900, height: 1000 });
  await sleep(1_100);
  await commonAudit(client, scenario, { width: 900, height: 1000 }, false);
  await screenshot(client, path.join(dir, "intermediate.jpg"));

  await navigate(client, origin, scenario, { width: 390, height: 844 });
  await sleep(1_100);
  await commonAudit(client, scenario, { width: 390, height: 844 }, false);
  await screenshot(client, path.join(dir, "mobile-hero.jpg"));
  await evaluate(client, `document.querySelector(".product-stage").scrollIntoView({ block: "start" })`);
  await click(client, '.flavor-button[data-flavor-button="night"]');
  await sleep(780);
  await screenshot(client, path.join(dir, "mobile-interaction.jpg"));

  await navigate(client, origin, scenario, DEFAULT_VIEWPORT, true);
  await commonAudit(client, scenario, DEFAULT_VIEWPORT, true);
  await screenshot(client, path.join(dir, "reduced-motion.jpg"));
}

async function captureSodaMotionFrames(client, origin, scenario) {
  const configured = process.env.SODA_MOTION_DIR;
  check(configured, "Set SODA_MOTION_DIR to an empty temporary directory for --soda-motion-frames");
  const dir = path.resolve(configured);
  await mkdir(dir, { recursive: true });
  await navigate(client, origin, scenario, { width: 900, height: 700 });
  await sleep(1_100);
  await commonAudit(client, scenario, { width: 900, height: 700 }, false);

  const fps = 12;
  const frameCount = 72;
  const started = Date.now();
  for (let frame = 0; frame < frameCount; frame += 1) {
    if (frame === 6) await click(client, '.flavor-button[data-flavor-button="pink"]');
    if (frame === 26) await click(client, '.flavor-button[data-flavor-button="night"]');
    if (frame === 46) await click(client, '.flavor-button[data-flavor-button="sun"]');
    await screenshotPng(client, path.join(dir, `frame-${String(frame).padStart(3, "0")}.png`));
    const target = started + ((frame + 1) * 1000 / fps);
    await sleep(Math.max(0, target - Date.now()));
  }
  passes.push(`${frameCount} Doppler motion frames captured from the live browser implementation`);
}

async function captureGoodturnWorkshop(client, origin, scenario) {
  const viewport = { width: 1425, height: 990 };
  await navigate(client, origin, scenario, viewport);
  await commonAudit(client, scenario, viewport, false);
  await evaluate(client, `(() => {
    document.documentElement.style.scrollBehavior = "auto";
    document.querySelector("#workshop").scrollIntoView({ block: "start", behavior: "instant" });
  })()`);
  await waitFor(client, `(() => {
    const top = document.querySelector("#workshop").getBoundingClientRect().top;
    return top >= 0 && top < 100;
  })()`, "Goodturn workshop capture position");
  const exchange = await evaluate(client, `(() => {
    const icon = document.querySelector(".service-icon--exchange");
    const bounds = icon?.getBoundingClientRect();
    const style = icon ? getComputedStyle(icon) : null;
    return {
      bound: Boolean(icon),
      width: bounds?.width || 0,
      height: bounds?.height || 0,
      mask: style?.maskImage || style?.webkitMaskImage || "",
    };
  })()`);
  check(exchange.bound && exchange.width >= 31 && exchange.height >= 31 && exchange.mask.includes("exchange.svg"), `Goodturn capture: exchange icon is not rendered (${JSON.stringify(exchange)})`);
  await screenshot(client, path.join(ROOT, "benchmarks/bicycle-commerce/screenshots/desktop-workshop.jpg"));
  passes.push("Goodturn workshop screenshot captured from the validated 1425 × 990 host state");
}

async function runCaptures(client, origin) {
  await Promise.all([
    "municipal-service",
    "warehouse-operations",
    "literary-publication",
  ].map((slug) => mkdir(path.join(ROOT, "benchmarks/forward-tests", slug, "screenshots"), { recursive: true })));
  const bySlug = new Map(scenarios.map((scenario) => [scenario.slug, scenario]));
  await captureMunicipal(client, origin, bySlug.get("municipal-service"));
  await captureWarehouse(client, origin, bySlug.get("warehouse-operations"));
  await captureLiterary(client, origin, bySlug.get("literary-publication"));
  await captureSoda(client, origin, bySlug.get("soda-campaign"));
  passes.push("18 forward-test and 7 Doppler screenshots captured from validated browser states");
}

async function captureVisualAcceptance(client, origin, fixture = "visual-acceptance") {
  const dir = path.join(ROOT, `evals/${fixture}/captures`);
  const fixtureSha256 = createHash("sha256").update(await readFile(path.join(ROOT, `evals/${fixture}/fixture.html`))).digest("hex");
  await mkdir(dir, { recursive: true });
  const proof = [];
  for (const version of ["A", "B", "C"]) {
    const scenario = { name: `${fixture} ${version}`, route: `/evals/${fixture}/fixture.html?v=${version}`, requiresReadyMarker: false };
    for (const viewport of [{ width: 1280, height: 1200 }, { width: 820, height: 1000 }, { width: 390, height: 844 }]) {
      await navigate(client, origin, scenario, viewport);
      const geometry = await evaluate(client, `({ width: innerWidth, height: innerHeight, scrollWidth: document.documentElement.scrollWidth, version: document.body.dataset.version })`);
      check(geometry.width === viewport.width && geometry.height === viewport.height, `${scenario.name}: capture viewport mismatch`);
      check(geometry.version === version, `${scenario.name}: wrong rendered variant`);
      check(geometry.scrollWidth <= viewport.width, `${scenario.name}: unexpected capture overflow`);
      const filename = `${version}-${viewport.width}.jpg`;
      await screenshot(client, path.join(dir, filename), true);
      const sha256 = createHash("sha256").update(await readFile(path.join(dir, filename))).digest("hex");
      proof.push({ file: filename, sha256, viewport, geometry });
    }
  }
  await writeFile(path.join(dir, "geometry.json"), `${JSON.stringify({ fixtureSha256, captures: proof }, null, 2)}\n`);
  passes.push(`9 ${fixture} fixture captures with verified viewport geometry; static evidence only, no task behavior or aesthetic certification`);
}

async function main() {
  const chrome = resolveChrome();
  const profile = mkdtempSync(path.join(tmpdir(), "snowe-browser-smoke-"));
  let server;
  let browser;
  let client;
  try {
    const debugPort = await reservePort();
    const started = await startStaticServer();
    server = started.server;
    const origin = `http://127.0.0.1:${started.port}`;
    browser = await launchBrowser(chrome, debugPort, profile);
    client = new CdpClient(browser.target.webSocketDebuggerUrl);
    await client.connect();
    await configureClient(client, origin);
    if (CHECKS_ONLY) await runSmoke(client, origin);
    if (CAPTURE && failures.length === 0) await runCaptures(client, origin);
    if (CAPTURE_SODA && failures.length === 0) {
      await captureSoda(client, origin, scenarios.find((scenario) => scenario.slug === "soda-campaign"));
      passes.push("7 Doppler screenshots captured from validated browser states");
    }
    if (CAPTURE_SODA_MOTION && failures.length === 0) {
      await captureSodaMotionFrames(client, origin, scenarios.find((scenario) => scenario.slug === "soda-campaign"));
    }
    if (CAPTURE_GOODTURN && failures.length === 0) {
      await captureGoodturnWorkshop(client, origin, scenarios.find((scenario) => scenario.slug === "bicycle-commerce"));
    }
    if (CAPTURE_VISUAL_ACCEPTANCE && failures.length === 0) await captureVisualAcceptance(client, origin);
    if (CAPTURE_CORRECTION_TRANSFER && failures.length === 0) await captureVisualAcceptance(client, origin, "correction-transfer");
    if (CAPTURE_ACCEPTANCE && failures.length === 0) await runAcceptanceCases(client, origin, true);
    if (CAPTURE_DENSITY && failures.length === 0) await runDensityCases(client, origin, true);
    if (CAPTURE_TITLEBOT && failures.length === 0) await runPilot(client, origin, true);
    if (CAPTURE_JUDGMENT && failures.length === 0) await runJudgment(client, origin, true);
  } finally {
    if (client) {
      try {
        await Promise.race([
          client.send("Browser.close"),
          sleep(3_000).then(() => { throw new Error("Timed out requesting Browser.close"); }),
        ]);
      } catch {
        // The browser may already be closing after a failed run.
      }
    }
    client?.close();
    const cleanupErrors = [];
    try {
      await stopBrowserProcess(browser);
    } catch (error) {
      cleanupErrors.push(error);
    }
    try {
      if (server) {
        server.closeAllConnections?.();
        await new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
      }
    } catch (error) {
      cleanupErrors.push(error);
    }
    try {
      await removeTemporaryProfile(profile);
    } catch (error) {
      cleanupErrors.push(error);
    }
    if (cleanupErrors.length) {
      throw new AggregateError(cleanupErrors, "Browser smoke cleanup failed.");
    }
  }

  for (const message of passes) process.stdout.write(`PASS ${message}\n`);
  for (const message of failures) process.stderr.write(`FAIL ${message}\n`);
  if (failures.length) process.exitCode = 1;
}

main().catch((error) => {
  process.stderr.write(`Browser smoke infrastructure failed: ${formatError(error)}\n`);
  process.exitCode = 1;
});
