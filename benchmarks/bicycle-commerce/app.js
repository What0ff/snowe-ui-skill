(() => {
  "use strict";

  const products = {
    "turn-one": {
      name: "Turn One",
      role: "Daily commuter",
      price: 1290,
      priceLabel: "€1,290",
      image: "assets/images/turn-one.webp",
      imageAlt: "Matte vermilion Turn One commuter bicycle in full side profile",
      description: "A quick, quiet city bike for daily distance. Its belt drive stays clean in work clothes; a ready-fitted rack, full fenders and integrated lights remove the usual accessory hunt.",
      specs: [
        ["Best for", "Regular commutes · mixed city streets"],
        ["Posture", "Neutral upright"],
        ["Weight", "11.4 kg"],
        ["Drive", "8-speed internal hub · belt"],
        ["Rider fit", "165–192 cm"],
        ["Ready", "2–4 days"]
      ],
      sizes: [["S", "165–174 cm"], ["M", "173–183 cm"], ["L", "182–192 cm"]],
      stock: "In stock · all sizes",
      finderReason: "You want an efficient everyday ride that stays light enough for stairs, trains, and the long way home."
    },
    "turn-step": {
      name: "Turn Step",
      role: "Easy-on all-rounder",
      price: 1490,
      priceLabel: "€1,490",
      image: "assets/images/turn-step.webp",
      imageAlt: "Deep olive Turn Step step-through bicycle with basket and rear rack in full side profile",
      description: "A low-entry city bike designed around frequent stops and ordinary clothes. Relaxed steering, a generous front basket and a clean internal drivetrain make errands feel unhurried.",
      specs: [
        ["Best for", "Errands · easy starts and stops"],
        ["Posture", "Relaxed upright"],
        ["Weight", "13.1 kg"],
        ["Drive", "7-speed internal hub · chain guard"],
        ["Rider fit", "155–185 cm"],
        ["Ready", "3–5 days"]
      ],
      sizes: [["S", "155–165 cm"], ["M", "164–175 cm"], ["L", "174–185 cm"]],
      stock: "In stock · S and M",
      finderReason: "Your week has plenty of stops, and easy entry, an upright view, and low everyday upkeep matter more than minimum weight."
    },
    "turn-cargo": {
      name: "Turn Cargo",
      role: "Small-car replacement",
      price: 2790,
      priceLabel: "€2,790",
      image: "assets/images/turn-cargo.webp",
      imageAlt: "Graphite Turn Cargo longtail bicycle carrying a citron crate in full side profile",
      description: "A compact longtail with the stable handling to carry a real week: groceries, work equipment, or one child seat. Its small rear wheel keeps the load low without turning the bike into a garage project.",
      specs: [
        ["Best for", "Loads · family errands · work gear"],
        ["Capacity", "80 kg rear load"],
        ["Weight", "21.8 kg"],
        ["Drive", "9-speed wide-range · hydraulic brakes"],
        ["Rider fit", "160–195 cm"],
        ["Ready", "5–7 days"]
      ],
      sizes: [["S/M", "160–176 cm"], ["M/L", "174–187 cm"], ["L/XL", "185–195 cm"]],
      stock: "Build slots this week",
      finderReason: "Capacity and planted handling are doing more work for you than low weight. This is the range’s practical car-replacement starting point."
    }
  };

  const state = {
    currentProduct: "turn-one",
    finderProduct: "turn-one",
    finderStep: 0,
    compare: new Set(),
    reservations: new Map()
  };

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const euro = new Intl.NumberFormat("en-IE", { style: "currency", currency: "EUR", maximumFractionDigits: 0 });
  let toastTimer;

  function openDialog(dialog) {
    const current = $("dialog[open]");
    if (current && current !== dialog) current.close();
    if (!dialog.open) dialog.showModal();
    document.body.classList.add("is-locked");
  }

  function closeMobileMenu() {
    const button = $(".menu-button");
    const menu = $("#mobile-menu");
    button.setAttribute("aria-expanded", "false");
    button.setAttribute("aria-label", "Open menu");
    menu.hidden = true;
  }

  function showToast(message) {
    const toast = $(".toast");
    window.clearTimeout(toastTimer);
    toast.textContent = message;
    toast.hidden = false;
    toastTimer = window.setTimeout(() => { toast.hidden = true; }, 3600);
  }

  function make(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  // Mobile navigation preserves the same journey without duplicating page state.
  const menuButton = $(".menu-button");
  menuButton.addEventListener("click", () => {
    const menu = $("#mobile-menu");
    const willOpen = menu.hidden;
    menu.hidden = !willOpen;
    menuButton.setAttribute("aria-expanded", String(willOpen));
    menuButton.setAttribute("aria-label", willOpen ? "Close menu" : "Open menu");
    if (willOpen) $("a", menu).focus();
  });
  $$("#mobile-menu a").forEach((link) => link.addEventListener("click", closeMobileMenu));
  window.addEventListener("resize", () => {
    if (window.innerWidth > 980) closeMobileMenu();
  });

  // Product filtering uses a short continuity cue, then removes irrelevant rows from navigation.
  const filterTimers = new WeakMap();
  $$("[data-filter]").forEach((button) => {
    button.addEventListener("click", () => {
      const filter = button.dataset.filter;
      let visible = 0;
      $$("[data-filter]").forEach((item) => {
        const active = item === button;
        item.classList.toggle("is-active", active);
        item.setAttribute("aria-pressed", String(active));
      });
      $$("[data-product-row]").forEach((row) => {
        window.clearTimeout(filterTimers.get(row));
        const show = filter === "all" || row.dataset.uses.split(" ").includes(filter);
        if (show) {
          visible += 1;
          row.hidden = false;
          row.classList.add("is-filtering");
          requestAnimationFrame(() => requestAnimationFrame(() => row.classList.remove("is-filtering")));
        } else if (reducedMotion.matches) {
          row.hidden = true;
          row.classList.remove("is-filtering");
        } else {
          row.classList.add("is-filtering");
          const timer = window.setTimeout(() => {
            row.hidden = true;
            row.classList.remove("is-filtering");
          }, 140);
          filterTimers.set(row, timer);
        }
      });
      $("[data-visible-count]").textContent = String(visible);
    });
  });

  // Product sheet: evidence, starting size, reservation, and test-ride paths stay together.
  const productDialog = $("#product-dialog");
  function fillProductDialog(id) {
    const product = products[id];
    state.currentProduct = id;
    $("[data-dialog-role]").textContent = product.role;
    $("[data-dialog-name]").textContent = product.name;
    $("[data-dialog-price]").textContent = product.priceLabel;
    $("[data-dialog-description]").textContent = product.description;
    $("[data-dialog-stock]").textContent = product.stock;
    const image = $("[data-dialog-image]");
    image.src = product.image;
    image.alt = product.imageAlt;

    const specs = $("[data-dialog-specs]");
    specs.replaceChildren();
    product.specs.forEach(([term, value]) => {
      const group = make("div");
      group.append(make("dt", "", term), make("dd", "", value));
      specs.append(group);
    });

    const sizeOptions = $("[data-size-options]");
    sizeOptions.replaceChildren();
    product.sizes.forEach(([size, range]) => {
      const label = make("label", "size-option");
      const input = make("input");
      input.type = "radio";
      input.name = "product-size";
      input.value = size;
      input.dataset.range = range;
      input.addEventListener("change", () => {
        $("[data-size-guidance]").textContent = `${size} is a starting point for riders around ${range}. We confirm reach and saddle position before payment.`;
        $("[data-selection-error]").textContent = "";
      });
      label.append(input, make("span", "", size));
      sizeOptions.append(label);
    });
    $("[data-size-guidance]").textContent = "We confirm size during your fit before payment.";
    $("[data-selection-error]").textContent = "";
  }

  function showProduct(id) {
    fillProductDialog(id);
    openDialog(productDialog);
  }

  $$('[data-open-product]').forEach((button) => {
    button.addEventListener("click", () => showProduct(button.dataset.openProduct));
  });

  $("[data-size-help]").addEventListener("click", () => {
    $("[data-size-guidance]").textContent = "Height starts the conversation; reach, mobility, footwear and load finish it. Choose the nearest range now and we will measure the final setup in the workshop.";
  });

  $("[data-reserve-product]").addEventListener("click", () => {
    const selected = $('input[name="product-size"]:checked', productDialog);
    if (!selected) {
      $("[data-selection-error]").textContent = "Choose a starting size before reserving.";
      $('input[name="product-size"]', productDialog).focus();
      return;
    }
    state.reservations.set(state.currentProduct, { size: selected.value });
    renderCart();
    const name = products[state.currentProduct].name;
    productDialog.close();
    showToast(`${name} ${selected.value} is held in your reservations. The €50 hold is refundable.`);
  });

  $("[data-dialog-book]").addEventListener("click", () => {
    const id = state.currentProduct;
    productDialog.close();
    window.setTimeout(() => showBooking(id), 0);
  });

  // Comparison supports one tentative selection while requiring two for a useful table.
  function renderCompareState() {
    const bar = $(".compare-bar");
    const count = state.compare.size;
    bar.hidden = count === 0;
    $("[data-compare-count]").textContent = String(count);
    const names = $("[data-compare-names]");
    names.replaceChildren(...[...state.compare].map((id) => make("li", "", products[id].name)));
    $("[data-open-compare]").disabled = count < 2;
    $$("[data-compare]").forEach((button) => {
      const selected = state.compare.has(button.dataset.compare);
      button.setAttribute("aria-pressed", String(selected));
      $("span", button).textContent = selected ? "✓" : "+";
      button.setAttribute("aria-label", `${selected ? "Remove" : "Add"} ${products[button.dataset.compare].name} ${selected ? "from" : "to"} comparison`);
    });
  }

  $$("[data-compare]").forEach((button) => {
    button.addEventListener("click", () => {
      const id = button.dataset.compare;
      if (state.compare.has(id)) state.compare.delete(id);
      else state.compare.add(id);
      renderCompareState();
    });
  });
  $("[data-clear-compare]").addEventListener("click", () => {
    state.compare.clear();
    renderCompareState();
  });

  function buildComparison() {
    const selected = [...state.compare].map((id) => products[id]);
    const table = make("table", "comparison-table");
    const head = make("thead");
    const headRow = make("tr");
    const attribute = make("th", "", "Attribute");
    attribute.scope = "col";
    headRow.append(attribute);
    selected.forEach((product) => {
      const th = make("th", "", product.name);
      th.scope = "col";
      headRow.append(th);
    });
    head.append(headRow);
    table.append(head);

    const rows = [
      ["Price", (p) => p.priceLabel],
      ["Role", (p) => p.role],
      ["Best for", (p) => p.specs[0][1]],
      ["Posture / capacity", (p) => p.specs[1][1]],
      ["Weight", (p) => p.specs[2][1]],
      ["Drive", (p) => p.specs[3][1]],
      ["Rider fit", (p) => p.specs[4][1]],
      ["Collection", (p) => p.specs[5][1]],
      ["Included", () => "Personal fit · 12-month workshop care"]
    ];
    const body = make("tbody");
    rows.forEach(([label, getValue]) => {
      const row = make("tr");
      const th = make("th", "", label);
      th.scope = "row";
      row.append(th, ...selected.map((product) => make("td", "", getValue(product))));
      body.append(row);
    });
    table.append(body);
    $("[data-comparison-table]").replaceChildren(table);
  }

  $("[data-open-compare]").addEventListener("click", () => {
    if (state.compare.size < 2) return;
    buildComparison();
    openDialog($("#compare-dialog"));
  });

  // Three answers create a reasoned starting point, never a forced checkout path.
  const finder = $("#ride-finder");
  function showFinderStep(index) {
    state.finderStep = index;
    $$("[data-step]", finder).forEach((step) => { step.hidden = Number(step.dataset.step) !== index; });
    $$("[data-progress]", finder).forEach((item) => {
      const itemIndex = Number(item.dataset.progress);
      item.classList.toggle("is-current", itemIndex === index);
      item.classList.toggle("is-complete", itemIndex < index);
    });
    $("[data-finder-back]").hidden = index === 0;
    $("[data-finder-next]").firstChild.textContent = index === 2 ? "Show my bike " : "Next question ";
    $("[data-finder-error]").textContent = "";
  }

  function finderChoice(name) {
    return $(`input[name="${name}"]:checked`, finder)?.value;
  }

  function finishFinder() {
    const day = finderChoice("day");
    const posture = finderChoice("posture");
    const priority = finderChoice("priority");
    let id = "turn-one";
    if (day === "carry" || priority === "capacity" || posture === "stable") id = "turn-cargo";
    else if (day === "errands" || posture === "relaxed" || priority === "simple") id = "turn-step";
    state.finderProduct = id;
    const product = products[id];
    $("[data-result-name]").textContent = product.name;
    $("[data-result-reason]").textContent = product.finderReason;
    $(".finder-progress").hidden = true;
    $$("[data-step]", finder).forEach((step) => { step.hidden = true; });
    $(".finder-actions").hidden = true;
    $("[data-finder-result]").hidden = false;
    $("[data-result-name]").focus();
  }

  $("[data-finder-next]").addEventListener("click", () => {
    const names = ["day", "posture", "priority"];
    const checked = $(`input[name="${names[state.finderStep]}"]:checked`, finder);
    if (!checked) {
      $("[data-finder-error]").textContent = "Choose one answer to continue.";
      $(`input[name="${names[state.finderStep]}"]`, finder).focus();
      return;
    }
    if (state.finderStep < 2) showFinderStep(state.finderStep + 1);
    else finishFinder();
  });
  $("[data-finder-back]").addEventListener("click", () => showFinderStep(Math.max(0, state.finderStep - 1)));
  $("[data-result-open]").addEventListener("click", () => showProduct(state.finderProduct));
  $("[data-finder-reset]").addEventListener("click", () => {
    finder.reset();
    $("[data-finder-result]").hidden = true;
    $(".finder-progress").hidden = false;
    $(".finder-actions").hidden = false;
    showFinderStep(0);
  });

  // Booking validates the shop's real operating days and keeps "not sure" a legitimate choice.
  const bookingDialog = $("#booking-dialog");
  const bookingForm = $("#booking-form");
  const dateInput = $('input[name="date"]', bookingForm);
  const today = new Date();
  const isoDate = (date) => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
  const latestDate = new Date(today);
  latestDate.setDate(latestDate.getDate() + 90);
  dateInput.min = isoDate(today);
  dateInput.max = isoDate(latestDate);

  function validateRideDate() {
    dateInput.setCustomValidity("");
    if (!dateInput.value) return;
    const day = new Date(`${dateInput.value}T12:00:00`).getDay();
    if (day === 0 || day === 1) dateInput.setCustomValidity("Choose Tuesday through Saturday, when the workshop is open.");
  }
  dateInput.addEventListener("input", validateRideDate);

  function showBooking(productId = "not-sure") {
    closeMobileMenu();
    bookingForm.reset();
    $('select[name="bike"]', bookingForm).value = products[productId] ? productId : "not-sure";
    $("[data-booking-form-view]").hidden = false;
    $("[data-booking-success]").hidden = true;
    openDialog(bookingDialog);
  }
  $$('[data-open-booking]').forEach((button) => {
    button.addEventListener("click", () => {
      const recommendation = button.closest("[data-finder-result]") ? state.finderProduct : "not-sure";
      showBooking(recommendation);
    });
  });

  bookingForm.addEventListener("submit", (event) => {
    event.preventDefault();
    validateRideDate();
    if (!bookingForm.reportValidity()) return;
    const data = new FormData(bookingForm);
    const bike = products[data.get("bike")]?.name || "a guided starting fit";
    const date = new Date(`${data.get("date")}T12:00:00`);
    const formatted = new Intl.DateTimeFormat("en-GB", { weekday: "long", day: "numeric", month: "long" }).format(date);
    $("[data-booking-summary]").textContent = `${data.get("name")}, your free ${bike} ride is held for ${formatted} at ${data.get("time")}. Bring your usual shoes and bag; no card is required.`;
    $("[data-booking-form-view]").hidden = true;
    $("[data-booking-success]").hidden = false;
    $("[data-booking-success] h2").focus();
  });

  // Reservations are explicit refundable holds, not a disguised full checkout.
  function renderCart() {
    const content = $("[data-cart-content]");
    const items = [...state.reservations.entries()];
    const count = items.length;
    $(".cart-count").textContent = String(count);
    $("[data-open-cart]").setAttribute("aria-label", `Open reservations, ${count} ${count === 1 ? "item" : "items"}`);
    content.replaceChildren();
    if (!count) {
      const empty = make("div", "cart-empty");
      empty.append(make("p", "", "No bikes are held yet. Choose a starting size from any bike, or book a free test ride first."));
      content.append(empty);
      return;
    }
    items.forEach(([id, reservation]) => {
      const product = products[id];
      const item = make("article", "cart-item");
      const image = make("img");
      image.src = product.image;
      image.alt = "";
      const copy = make("div");
      copy.append(make("h3", "", product.name), make("p", "", `${reservation.size} starting size · €50 refundable hold`));
      const remove = make("button", "", "Remove");
      remove.type = "button";
      remove.setAttribute("aria-label", `Remove ${product.name} from reservations`);
      remove.addEventListener("click", () => {
        state.reservations.delete(id);
        renderCart();
        showToast(`${product.name} removed from reservations.`);
      });
      item.append(image, copy, remove);
      content.append(item);
    });
    const total = make("div", "cart-total");
    total.append(make("span", "", "Refundable hold total"), make("span", "", euro.format(count * 50)));
    const followup = make("div", "cart-followup");
    followup.append(
      make("p", "", "The hold is deducted from the bike price and refundable before collection."),
      make("p", "", "We confirm final size, stock and collection date with you before any remaining payment.")
    );
    content.append(total, followup);
  }

  $("[data-open-cart]").addEventListener("click", () => {
    renderCart();
    openDialog($("#cart-dialog"));
  });

  // Native dialogs provide focus trapping and Escape; close buttons and backdrop clicks complete the model.
  $$("dialog").forEach((dialog) => {
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) dialog.close();
    });
    dialog.addEventListener("close", () => {
      if (!$("dialog[open]")) document.body.classList.remove("is-locked");
    });
  });
  $$('[data-close-dialog]').forEach((button) => {
    button.addEventListener("click", () => button.closest("dialog").close());
  });

  renderCompareState();
  renderCart();
  showFinderStep(0);
})();
