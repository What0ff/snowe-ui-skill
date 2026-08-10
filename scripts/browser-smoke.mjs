#!/usr/bin/env node

import { spawn, spawnSync } from "node:child_process";
import { createServer } from "node:http";
import { mkdir, readFile, rm, stat, writeFile } from "node:fs/promises";
import { existsSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const CAPTURE = process.argv.includes("--capture");
const CHECKS_ONLY = process.argv.includes("--smoke") || !CAPTURE;
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
  client.on("Runtime.exceptionThrown", ({ exceptionDetails }) => {
    diagnostics.exceptions.push(exceptionDetails?.exception?.description || exceptionDetails?.text || "Unknown runtime exception");
  });
  client.on("Runtime.consoleAPICalled", ({ type, args }) => {
    if (type !== "error" && type !== "assert") return;
    diagnostics.consoleErrors.push(args.map((arg) => arg.value ?? arg.description ?? "").join(" "));
  });
  client.on("Network.loadingFailed", ({ canceled, errorText, requestId }) => {
    if (!canceled && errorText !== "net::ERR_ABORTED") diagnostics.failedRequests.push(`${requestId}: ${errorText}`);
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
    features: [{ name: "prefers-reduced-motion", value: reducedMotion ? "reduce" : "no-preference" }],
  });
}

async function navigate(client, origin, scenario, viewport = DEFAULT_VIEWPORT, reducedMotion = false) {
  diagnostics = { exceptions: [], consoleErrors: [], failedRequests: [], badResponses: [] };
  await setViewport(client, viewport, reducedMotion);
  const loaded = client.once("Page.loadEventFired");
  await client.send("Page.navigate", { url: `${origin}${scenario.route}?smoke=${Date.now()}` });
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
  await client.send("Input.dispatchKeyEvent", { type: "keyDown", key: keyValue, code });
  await client.send("Input.dispatchKeyEvent", { type: "keyUp", key: keyValue, code });
  await sleep(30);
}

async function interactGoodturn(client) {
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
    "bicycle-commerce": [".menu-button", "#mobile-menu", "hidden"],
    "municipal-service": ["#nav-toggle", "#service-nav", "data"],
    "warehouse-operations": ["#rail-toggle", "#app-rail", "data"],
    "literary-publication": ["#issue-toggle", "#publication-nav", "data"],
  };
  const [toggle, target, mode] = definitions[scenario.slug];
  await click(client, toggle);
  const state = await evaluate(client, `(() => {
    const button = document.querySelector(${JSON.stringify(toggle)});
    const target = document.querySelector(${JSON.stringify(target)});
    return { expanded: button.getAttribute("aria-expanded"), visible: ${JSON.stringify(mode)} === "hidden" ? !target.hidden : target.dataset.open === "true" };
  })()`);
  check(state.expanded === "true" && state.visible, `${scenario.name}: mobile navigation did not open`);
}

async function runSmoke(client, origin) {
  for (const scenario of scenarios) {
    process.stdout.write(`CHECK ${scenario.name}\n`);
    try {
      for (const viewport of [DEFAULT_VIEWPORT, { width: 900, height: 900 }, { width: 390, height: 844 }]) {
        await navigate(client, origin, scenario, viewport);
        await commonAudit(client, scenario, viewport, false);
        if (viewport.width === 390) await exerciseMobileNavigation(client, scenario);
      }
      await navigate(client, origin, scenario, DEFAULT_VIEWPORT);
      await scenario.interact(client);
      await commonAudit(client, scenario, DEFAULT_VIEWPORT, false);
      await navigate(client, origin, scenario, { width: 390, height: 844 }, true);
      await commonAudit(client, scenario, { width: 390, height: 844 }, true);
      passes.push(`${scenario.name}: wide/intermediate/mobile, interactions, reduced motion`);
    } catch (error) {
      failures.push(`${scenario.name}: ${error.message}`);
    }
  }
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
  passes.push("18 forward-test screenshots captured from validated browser states");
}

async function main() {
  const chrome = resolveChrome();
  const profile = mkdtempSync(path.join(tmpdir(), "snowe-browser-smoke-"));
  const debugPort = await reservePort();
  const { server, port } = await startStaticServer();
  const origin = `http://127.0.0.1:${port}`;
  let browser;
  let client;
  try {
    browser = await launchBrowser(chrome, debugPort, profile);
    client = new CdpClient(browser.target.webSocketDebuggerUrl);
    await client.connect();
    await configureClient(client, origin);
    if (CHECKS_ONLY) await runSmoke(client, origin);
    if (CAPTURE && failures.length === 0) await runCaptures(client, origin);
  } finally {
    if (client) {
      try {
        await client.send("Browser.close");
      } catch {
        // The browser may already be closing after a failed run.
      }
    }
    client?.close();
    if (browser?.child && browser.child.exitCode === null) {
      await Promise.race([
        new Promise((resolve) => browser.child.once("exit", resolve)),
        sleep(1_000),
      ]);
      if (browser.child.exitCode === null) browser.child.kill();
    }
    server.closeAllConnections?.();
    await new Promise((resolve) => server.close(resolve));
    await rm(profile, { recursive: true, force: true });
  }

  for (const message of passes) process.stdout.write(`PASS ${message}\n`);
  for (const message of failures) process.stderr.write(`FAIL ${message}\n`);
  if (failures.length) process.exitCode = 1;
}

main().catch((error) => {
  process.stderr.write(`Browser smoke infrastructure failed: ${error.stack || error.message}\n`);
  process.exitCode = 1;
});
