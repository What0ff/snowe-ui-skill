const rows = [...document.querySelectorAll("#queue-body tr")];
const inspector = document.querySelector("#inspector");
const search = document.querySelector("#queue-search");
const resolveDialog = document.querySelector("#resolve-dialog");
const resolveForm = document.querySelector("#resolve-form");
const resolveOpen = document.querySelector("#resolve-open");
const resolveError = document.querySelector("#resolve-error");
const toast = document.querySelector("#toast");
const rail = document.querySelector("#app-rail");
const railToggle = document.querySelector("#rail-toggle");
let selected = 0;
let activeFilter = "all";

function visibleRows() {
  return rows.filter((row) => !row.hidden);
}

function setDetail(row, focus = false) {
  rows.forEach((item) => { item.classList.toggle("selected", item === row); item.setAttribute("aria-selected", String(item === row)); });
  selected = rows.indexOf(row);
  document.querySelector("#detail-id").textContent = row.dataset.id;
  document.querySelector("#inspector-title").textContent = row.dataset.title;
  document.querySelector("#detail-age").textContent = row.dataset.age;
  document.querySelector("#detail-due").textContent = row.dataset.due;
  document.querySelector("#detail-owner").textContent = row.dataset.owner;
  document.querySelector("#object-title").textContent = row.dataset.object;
  document.querySelector("#detail-location").textContent = row.dataset.location;
  document.querySelector("#detail-available").textContent = row.dataset.available;
  document.querySelector("#detail-required").textContent = row.dataset.required;
  document.querySelector("#detail-inbound").textContent = row.dataset.inbound;
  document.querySelector("#resolve-title span").textContent = row.dataset.id;
  const priority = row.querySelector(".priority");
  const detailPriority = document.querySelector("#detail-priority");
  detailPriority.textContent = priority.textContent;
  detailPriority.className = priority.className;
  if (focus) row.focus();
}

function applyFilters() {
  const query = search.value.trim().toLowerCase();
  for (const row of rows) {
    const filterMatch = row.dataset.resolved !== "true" && (activeFilter === "all" || row.dataset.filter.split(" ").includes(activeFilter));
    const textMatch = !query || row.textContent.toLowerCase().includes(query);
    row.hidden = !(filterMatch && textMatch);
  }
  const visible = visibleRows();
  document.querySelector("#visible-count").textContent = `${visible.length} visible of 18 open`;
  if (visible.length && !visible.includes(rows[selected])) setDetail(visible[0]);
}

rows.forEach((row) => {
  row.addEventListener("click", () => setDetail(row));
  row.addEventListener("keydown", (event) => {
    if (event.key === "Enter") { event.preventDefault(); setDetail(row); inspector.setAttribute("tabindex", "-1"); inspector.focus(); }
  });
});

search.addEventListener("input", applyFilters);
document.querySelectorAll(".queue-tabs [data-filter]").forEach((button) => button.addEventListener("click", () => {
  activeFilter = button.dataset.filter;
  document.querySelectorAll(".queue-tabs [data-filter]").forEach((item) => {
    const on = item === button; item.classList.toggle("selected", on); item.setAttribute("aria-pressed", String(on));
  });
  applyFilters();
}));

document.querySelector("#refresh-queue").addEventListener("click", () => {
  toast.textContent = "Queue refreshed · no new critical exceptions";
  toast.hidden = false;
});

document.querySelector("#assign-self").addEventListener("click", () => {
  const row = rows[selected]; row.dataset.owner = "M. Popescu"; document.querySelector("#detail-owner").textContent = "M. Popescu";
  toast.textContent = `${row.dataset.id} assigned to M. Popescu`; toast.hidden = false;
});

resolveOpen.addEventListener("click", () => resolveDialog.showModal());
resolveDialog.addEventListener("close", () => resolveOpen.focus());
resolveForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (event.submitter?.value === "cancel") { resolveDialog.close(); return; }
  const resolution = resolveForm.querySelector("input:checked");
  const note = document.querySelector("#resolution-note");
  const problems = [];
  if (!resolution) problems.push("Choose a resolution.");
  if (note.value.trim().length < 12) problems.push("Add an operator note of at least 12 characters.");
  if (problems.length) {
    resolveError.textContent = problems.join(" "); resolveError.hidden = false; resolveError.focus(); return;
  }
  const row = rows[selected];
  resolveError.hidden = true;
  resolveDialog.close();
  row.dataset.resolved = "true";
  toast.textContent = `${row.dataset.id} resolved and written to the audit log`; toast.hidden = false;
  applyFilters();
});

railToggle.addEventListener("click", () => {
  const open = railToggle.getAttribute("aria-expanded") !== "true";
  railToggle.setAttribute("aria-expanded", String(open)); railToggle.textContent = open ? "Close" : "Nav"; rail.dataset.open = String(open);
});

document.addEventListener("keydown", (event) => {
  if (event.target.matches("input, textarea") || resolveDialog.open) return;
  const visible = visibleRows();
  const current = visible.indexOf(rows[selected]);
  if (event.key === "/") { event.preventDefault(); search.focus(); }
  if (event.key.toLowerCase() === "j" && visible.length) { event.preventDefault(); setDetail(visible[Math.min(current + 1, visible.length - 1)], true); }
  if (event.key.toLowerCase() === "k" && visible.length) { event.preventDefault(); setDetail(visible[Math.max(current - 1, 0)], true); }
  if (event.key.toLowerCase() === "e") { event.preventDefault(); resolveDialog.showModal(); }
});

setDetail(rows[0]);
window.__benchmarkReady = true;
