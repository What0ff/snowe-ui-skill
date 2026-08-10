(() => {
  "use strict";

  const flavors = {
    sun: {
      index: "01 / 03",
      name: "Sun Shift",
      blend: "Tangerine · juniper",
      description: "Tangerine arrives bright; juniper pulls the finish somewhere greener.",
      label: "assets/labels/sun-shift.svg",
      color: "#f6df34",
    },
    pink: {
      index: "02 / 03",
      name: "Pink Noise",
      blend: "Grapefruit · hibiscus",
      description: "Grapefruit cuts in tart; hibiscus lets the signal bloom on the way out.",
      label: "assets/labels/pink-noise.svg",
      color: "#ff5d88",
    },
    night: {
      index: "03 / 03",
      name: "Night Signal",
      blend: "Black cherry · toasted spice",
      description: "Black cherry lands dark and round; toasted spice keeps the last note warm.",
      label: "assets/labels/night-signal.svg",
      color: "#9a84ff",
    },
  };
  const flavorOrder = Object.keys(flavors);
  const root = document.documentElement;
  const body = document.body;
  const motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
  const productStage = document.querySelector(".product-stage");
  const canRig = document.querySelector(".can-rig");
  const interactiveCan = document.querySelector("#interactive-can");
  const canObject = document.querySelector("[data-can-object]");
  const canBody = document.querySelector("[data-can-body]");
  const staticCan = document.querySelector("[data-static-can]");
  const staticLabel = document.querySelector("[data-static-label]");
  const poster = document.querySelector(".signal-poster");
  const posterLabel = document.querySelector("[data-poster-label]");
  const flavorStatus = document.querySelector("[data-flavor-status]");
  const bubbleField = document.querySelector("[data-bubbles]");
  const themeMeta = document.querySelector('meta[name="theme-color"]');
  const panelRecords = [];

  let currentFlavor = "sun";
  let reducedMotion = motionQuery.matches;
  let yaw = 0;
  let yawFrame = 0;
  let posterTimer = 0;
  let bubbleTimer = 0;
  let resizeTimer = 0;
  let dragging = null;

  const clamp = (value, minimum, maximum) => Math.min(maximum, Math.max(minimum, value));
  const easeOut = (value) => 1 - Math.pow(1 - value, 4);
  const normalizeAngle = (value) => ((value + 180) % 360 + 360) % 360 - 180;

  function setCanYaw(nextYaw) {
    yaw = nextYaw;
    canObject.style.setProperty("--yaw", `${yaw}deg`);
    canRig.style.setProperty("--lid-yaw", `${yaw}deg`);
    const yawRadians = yaw * Math.PI / 180;
    canObject.style.setProperty("--dew-opacity", String(Math.max(0.08, Math.cos(yawRadians)) * 0.78));
    for (const record of panelRecords) {
      const relative = normalizeAngle(record.angle + yaw);
      const radians = relative * Math.PI / 180;
      const facing = Math.max(0, Math.cos(radians));
      const shade = 0.48 + (0.52 * facing);
      const glint = Math.max(0, 1 - (Math.abs(relative + 24) / 18)) * 0.46;
      record.node.style.setProperty("--shade", shade.toFixed(3));
      record.node.style.setProperty("--glint", glint.toFixed(3));
    }
  }

  function stopYawAnimation() {
    if (yawFrame) cancelAnimationFrame(yawFrame);
    yawFrame = 0;
  }

  function animateYaw(target, duration = 500, onComplete) {
    stopYawAnimation();
    if (reducedMotion || duration <= 0) {
      setCanYaw(target);
      onComplete?.();
      return;
    }
    const start = performance.now();
    const from = yaw;
    const distance = target - from;
    const frame = (now) => {
      const progress = clamp((now - start) / duration, 0, 1);
      setCanYaw(from + distance * easeOut(progress));
      if (progress < 1) yawFrame = requestAnimationFrame(frame);
      else {
        yawFrame = 0;
        onComplete?.();
      }
    };
    yawFrame = requestAnimationFrame(frame);
  }

  function panelCountForViewport() {
    if (window.innerWidth <= 480) return 32;
    if (window.innerWidth <= 1000) return 40;
    return 48;
  }

  function buildCan() {
    canBody.replaceChildren();
    panelRecords.length = 0;
    if (reducedMotion) return;

    const rect = interactiveCan.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    const count = panelCountForViewport();
    const radius = (rect.width / 2) - 0.5;
    const circumference = 2 * Math.PI * radius;
    const arcWidth = circumference / count;
    const panelWidth = arcWidth + 1.25;

    const fragment = document.createDocumentFragment();
    for (let index = 0; index < count; index += 1) {
      const angle = index * (360 / count);
      const panel = document.createElement("div");
      panel.className = "can-panel";
      panel.style.setProperty("--panel-w", `${panelWidth}px`);
      panel.style.setProperty("--panel-angle", `${angle}deg`);
      panel.style.setProperty("--radius", `${radius}px`);

      for (const flavor of flavorOrder) {
        const layer = document.createElement("span");
        layer.className = "label-layer";
        layer.dataset.layer = flavor;
        layer.style.backgroundImage = `url("${flavors[flavor].label}")`;
        layer.style.backgroundSize = `${circumference}px ${rect.height}px`;
        layer.style.backgroundPosition = `${-(circumference / 2 + index * arcWidth - panelWidth / 2)}px 0`;
        panel.append(layer);
      }

      fragment.append(panel);
      panelRecords.push({ node: panel, angle });
    }
    canBody.append(fragment);
    setCanYaw(yaw);
  }

  function seededRandom(seed) {
    let value = seed >>> 0;
    return () => {
      value = (value * 1664525 + 1013904223) >>> 0;
      return value / 4294967296;
    };
  }

  function clearBubbles() {
    window.clearTimeout(bubbleTimer);
    bubbleTimer = 0;
    bubbleField.replaceChildren();
  }

  function createBubbles() {
    clearBubbles();
    if (reducedMotion || document.hidden) return;
    const count = window.innerWidth <= 480 ? 13 : window.innerWidth <= 1000 ? 20 : 30;
    const random = seededRandom(20260811);
    const fragment = document.createDocumentFragment();
    for (let index = 0; index < count; index += 1) {
      const bubble = document.createElement("i");
      bubble.className = "bubble";
      bubble.style.setProperty("--bubble-x", `${26 + random() * 49}%`);
      bubble.style.setProperty("--bubble-size", `${4 + random() * 17}px`);
      bubble.style.setProperty("--bubble-delay", `${0.1 + random() * 0.65}s`);
      bubble.style.setProperty("--bubble-duration", `${0.95 + random() * 0.9}s`);
      bubble.style.setProperty("--bubble-rise", `${130 + random() * 250}px`);
      bubble.style.setProperty("--bubble-drift", `${-65 + random() * 130}px`);
      fragment.append(bubble);
    }
    bubbleField.append(fragment);
    bubbleTimer = window.setTimeout(clearBubbles, 2600);
  }

  function cancelIntro() {
    body.classList.add("intro-cancelled");
    stopYawAnimation();
    clearBubbles();
  }

  function replayIntro() {
    if (reducedMotion) return false;
    stopYawAnimation();
    clearBubbles();
    body.classList.remove("is-ready", "intro-cancelled");
    setCanYaw(-205);
    void document.body.offsetWidth;
    requestAnimationFrame(() => {
      body.classList.add("is-ready");
      createBubbles();
      animateYaw(0, 980);
    });
    return true;
  }

  function updateFlavorContent(flavor) {
    const details = flavors[flavor];
    body.dataset.flavor = flavor;
    interactiveCan.dataset.flavor = flavor;
    interactiveCan.setAttribute("aria-label", `Doppler ${details.name} carbonated soft-drink can. Drag left or right, or use the arrow keys, to rotate it.`);
    staticCan.setAttribute("aria-label", `Doppler ${details.name} carbonated soft-drink can`);
    staticLabel.src = details.label;
    posterLabel.src = details.label;
    themeMeta.content = details.color;

    document.querySelectorAll("[data-selected-name]").forEach((node) => { node.textContent = details.name; });
    document.querySelectorAll("[data-selected-blend]").forEach((node) => { node.textContent = details.blend; });
    document.querySelectorAll("[data-selected-index]").forEach((node) => { node.textContent = details.index; });
    document.querySelectorAll("[data-selected-description]").forEach((node) => { node.textContent = details.description; });
    document.querySelectorAll("[data-flavor-button]").forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.flavorButton === flavor));
    });
  }

  function selectFlavor(flavor, announce = true) {
    if (!flavors[flavor]) return false;
    const changed = flavor !== currentFlavor;
    currentFlavor = flavor;
    window.clearTimeout(posterTimer);
    if (changed) poster.classList.add("is-changing");
    updateFlavorContent(flavor);
    if (announce) flavorStatus.textContent = `${flavors[flavor].name} selected: ${flavors[flavor].blend}.`;
    if (changed && !reducedMotion) {
      cancelIntro();
      let targetYaw = Math.ceil(yaw / 360) * 360;
      if (targetYaw - yaw < 210) targetYaw += 360;
      animateYaw(targetYaw, 720);
    }
    posterTimer = window.setTimeout(() => poster.classList.remove("is-changing"), reducedMotion ? 0 : 170);
    return changed;
  }

  document.querySelectorAll("[data-flavor-button]").forEach((button) => {
    button.addEventListener("click", () => selectFlavor(button.dataset.flavorButton));
  });

  interactiveCan.addEventListener("pointerdown", (event) => {
    if (reducedMotion || event.button !== 0 || !event.isPrimary) return;
    cancelIntro();
    dragging = {
      pointerId: event.pointerId,
      startX: event.clientX,
      startYaw: yaw,
      lastX: event.clientX,
      lastTime: performance.now(),
      velocity: 0,
    };
    interactiveCan.setPointerCapture(event.pointerId);
    productStage.classList.add("is-dragging");
  });

  interactiveCan.addEventListener("pointermove", (event) => {
    if (!dragging || event.pointerId !== dragging.pointerId) return;
    const now = performance.now();
    const elapsed = Math.max(1, now - dragging.lastTime);
    dragging.velocity = (event.clientX - dragging.lastX) / elapsed;
    dragging.lastX = event.clientX;
    dragging.lastTime = now;
    setCanYaw(dragging.startYaw + (event.clientX - dragging.startX) * 0.42);
  });

  function finishDrag(event, useInertia) {
    if (!dragging || event.pointerId !== dragging.pointerId) return;
    const velocity = dragging.velocity;
    dragging = null;
    productStage.classList.remove("is-dragging");
    if (interactiveCan.hasPointerCapture(event.pointerId)) interactiveCan.releasePointerCapture(event.pointerId);
    if (useInertia && Math.abs(velocity) > 0.02) {
      animateYaw(yaw + clamp(velocity * 145, -48, 48), 430);
    }
  }

  interactiveCan.addEventListener("pointerup", (event) => finishDrag(event, true));
  interactiveCan.addEventListener("pointercancel", (event) => finishDrag(event, false));

  interactiveCan.addEventListener("keydown", (event) => {
    if (reducedMotion) return;
    let target = null;
    if (event.key === "ArrowLeft") target = yaw - 18;
    if (event.key === "ArrowRight") target = yaw + 18;
    if (event.key === "Home") target = 0;
    if (target === null) return;
    event.preventDefault();
    cancelIntro();
    animateYaw(target, 260);
  });

  const navToggle = document.querySelector("#nav-toggle");
  const siteNav = document.querySelector("#site-nav");
  const navLinks = [...siteNav.querySelectorAll("a")];

  function setNavigation(open, restoreFocus = false) {
    siteNav.dataset.open = String(open);
    navToggle.setAttribute("aria-expanded", String(open));
    navToggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    if (open) requestAnimationFrame(() => navLinks[0]?.focus());
    else if (restoreFocus) navToggle.focus();
  }

  navToggle.addEventListener("click", () => setNavigation(navToggle.getAttribute("aria-expanded") !== "true", false));
  navLinks.forEach((link) => link.addEventListener("click", () => setNavigation(false, false)));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && navToggle.getAttribute("aria-expanded") === "true") setNavigation(false, true);
  });
  document.addEventListener("pointerdown", (event) => {
    if (navToggle.getAttribute("aria-expanded") !== "true") return;
    if (siteNav.contains(event.target) || navToggle.contains(event.target)) return;
    setNavigation(false, false);
  });

  const packForm = document.querySelector("#pack-form");
  const packStatus = document.querySelector("[data-pack-status]");
  const packSubmit = document.querySelector("[data-pack-submit]");
  const packTotal = document.querySelector("[data-pack-total]");
  const packGuidance = document.querySelector("[data-pack-guidance]");
  const packSlots = [...document.querySelectorAll("[data-pack-slots] li")];
  const packCounts = { sun: 2, pink: 2, night: 2 };

  function renderPack() {
    const total = flavorOrder.reduce((sum, flavor) => sum + packCounts[flavor], 0);
    const order = flavorOrder.flatMap((flavor) => Array(packCounts[flavor]).fill(flavor));
    packTotal.textContent = String(total);
    packGuidance.textContent = total === 6 ? "Your mix is ready." : `${6 - total} ${6 - total === 1 ? "space" : "spaces"} left.`;
    packSubmit.disabled = total !== 6;

    for (const flavor of flavorOrder) {
      document.querySelector(`[data-pack-count="${flavor}"]`).textContent = String(packCounts[flavor]);
      const row = document.querySelector(`[data-pack-row="${flavor}"]`);
      row.querySelector('[data-pack-action="decrease"]').disabled = packCounts[flavor] === 0;
      row.querySelector('[data-pack-action="increase"]').disabled = total >= 6;
    }

    packSlots.forEach((slot, index) => {
      const flavor = order[index];
      slot.dataset.slot = flavor || "empty";
      slot.hidden = !flavor;
    });
  }

  document.querySelectorAll("[data-pack-action]").forEach((button) => {
    button.addEventListener("click", () => {
      const row = button.closest("[data-pack-row]");
      const flavor = row.dataset.packRow;
      const total = flavorOrder.reduce((sum, item) => sum + packCounts[item], 0);
      if (button.dataset.packAction === "decrease" && packCounts[flavor] > 0) packCounts[flavor] -= 1;
      if (button.dataset.packAction === "increase" && total < 6) packCounts[flavor] += 1;
      packStatus.textContent = "";
      renderPack();
    });
  });

  packForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const total = flavorOrder.reduce((sum, flavor) => sum + packCounts[flavor], 0);
    if (total !== 6) {
      packStatus.textContent = `Choose ${6 - total} more ${6 - total === 1 ? "can" : "cans"} before adding the mix.`;
      return;
    }
    const parts = flavorOrder.filter((flavor) => packCounts[flavor] > 0).map((flavor) => `${packCounts[flavor]} ${flavors[flavor].name}`);
    packStatus.textContent = `Signal packed: ${parts.join(", ")}. Fictional demo only—no order or payment was sent.`;
  });

  function applyMotionPreference() {
    reducedMotion = motionQuery.matches;
    root.classList.toggle("is-reduced", reducedMotion);
    if (reducedMotion) {
      cancelIntro();
      canBody.replaceChildren();
      panelRecords.length = 0;
      setCanYaw(0);
    } else {
      body.classList.add("intro-cancelled", "is-ready");
      buildCan();
      setCanYaw(0);
    }
  }

  motionQuery.addEventListener?.("change", applyMotionPreference);
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      stopYawAnimation();
      clearBubbles();
    }
  });
  window.addEventListener("resize", () => {
    window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(() => {
      if (window.innerWidth > 980 && navToggle.getAttribute("aria-expanded") === "true") setNavigation(false, false);
      buildCan();
    }, 140);
  });

  updateFlavorContent(currentFlavor);
  renderPack();
  root.classList.toggle("is-reduced", reducedMotion);
  if (!reducedMotion) {
    buildCan();
    replayIntro();
  } else {
    setCanYaw(0);
  }

  window.__doppler = {
    replayIntro,
    selectFlavor,
    setYaw(value) {
      cancelIntro();
      setCanYaw(Number(value) || 0);
    },
    getState() {
      return {
        flavor: currentFlavor,
        yaw,
        reducedMotion,
        pack: { ...packCounts },
        panels: panelRecords.length,
      };
    },
  };
  window.__benchmarkReady = true;
})();
