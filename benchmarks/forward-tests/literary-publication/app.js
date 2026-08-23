const issueToggle = document.querySelector("#issue-toggle");
const publicationNav = document.querySelector("#publication-nav");
const progress = document.querySelector("#reading-progress");
const story = document.querySelector("#lead-story");
const saveStory = document.querySelector("#save-story");
const archiveSearch = document.querySelector("#archive-search");
const archiveItems = [...document.querySelectorAll("#archive-list article")];
const archiveEmpty = document.querySelector("#archive-empty");
const membershipDialog = document.querySelector("#membership-dialog");
const membershipForm = document.querySelector("#membership-form");
const membershipError = document.querySelector("#membership-error");
const membershipResult = document.querySelector("#membership-result");
const membershipOpeners = [...document.querySelectorAll(".membership-open")];
let lastMembershipOpener = membershipOpeners[0];

function closePublicationNavigation({ restoreFocus = false } = {}) {
  const focusInside = publicationNav.contains(document.activeElement);
  issueToggle.setAttribute("aria-expanded", "false");
  issueToggle.textContent = "Contents";
  publicationNav.dataset.open = "false";
  const navIsHidden = getComputedStyle(publicationNav).display === "none";
  if ((restoreFocus || (focusInside && navIsHidden)) && document.activeElement !== issueToggle) issueToggle.focus();
}

issueToggle.addEventListener("click", () => {
  const open = issueToggle.getAttribute("aria-expanded") !== "true";
  if (!open) {
    closePublicationNavigation({ restoreFocus: true });
    return;
  }
  issueToggle.setAttribute("aria-expanded", "true");
  issueToggle.textContent = "Close";
  publicationNav.dataset.open = "true";
  publicationNav.querySelector("a")?.focus();
});
publicationNav.querySelectorAll("a").forEach((link) => link.addEventListener("click", () => closePublicationNavigation()));

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && issueToggle.getAttribute("aria-expanded") === "true") closePublicationNavigation({ restoreFocus: true });
});

window.addEventListener("resize", () => {
  if (window.innerWidth > 640 && issueToggle.getAttribute("aria-expanded") === "true") closePublicationNavigation();
});

function updateProgress() {
  const rect = story.getBoundingClientRect();
  const total = Math.max(story.offsetHeight - window.innerHeight, 1);
  const consumed = Math.min(Math.max(-rect.top, 0), total);
  progress.style.width = `${(consumed / total) * 100}%`;
}
document.addEventListener("scroll", updateProgress, { passive: true });
updateProgress();

document.querySelectorAll("[data-size]").forEach((button) => button.addEventListener("click", () => {
  const large = button.dataset.size === "large";
  document.documentElement.style.setProperty("--reading-size", large ? "1.3rem" : "1.12rem");
  document.querySelectorAll("[data-size]").forEach((item) => item.setAttribute("aria-pressed", String(item === button)));
}));

saveStory.addEventListener("click", () => {
  const saved = saveStory.getAttribute("aria-pressed") !== "true";
  saveStory.setAttribute("aria-pressed", String(saved)); saveStory.textContent = saved ? "Saved to reading list" : "Save this story";
});

archiveSearch.addEventListener("input", () => {
  const query = archiveSearch.value.trim().toLowerCase();
  let shown = 0;
  archiveItems.forEach((item) => { item.hidden = Boolean(query) && !`${item.dataset.search} ${item.textContent}`.toLowerCase().includes(query); if (!item.hidden) shown += 1; });
  archiveEmpty.hidden = shown !== 0;
});

membershipOpeners.forEach((button) => button.addEventListener("click", () => { lastMembershipOpener = button; membershipDialog.showModal(); }));
membershipDialog.addEventListener("close", () => lastMembershipOpener.focus());
membershipForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (event.submitter?.value === "cancel") { membershipDialog.close(); return; }
  const plan = membershipForm.querySelector("input:checked");
  const email = document.querySelector("#member-email");
  const problems = [];
  if (!plan) problems.push("Choose a membership.");
  if (!email.validity.valid || !email.value.trim()) problems.push("Enter a valid email address.");
  if (problems.length) { membershipError.textContent = problems.join(" "); membershipError.hidden = false; membershipResult.hidden = true; membershipError.focus(); return; }
  membershipError.hidden = true; membershipResult.hidden = false; membershipResult.focus();
});

window.__benchmarkReady = true;
