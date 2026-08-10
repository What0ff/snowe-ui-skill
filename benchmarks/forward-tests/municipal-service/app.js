const navToggle = document.querySelector("#nav-toggle");
const serviceNav = document.querySelector("#service-nav");
const languageToggle = document.querySelector("#language-toggle");
const eligibilityForm = document.querySelector("#eligibility-form");
const eligibilityErrors = document.querySelector("#eligibility-errors");
const eligibilityResult = document.querySelector("#eligibility-result");
const statusDialog = document.querySelector("#status-dialog");
const statusOpen = document.querySelector("#status-open");
const statusForm = document.querySelector("#status-form");
const referenceInput = document.querySelector("#request-reference");
const referenceError = document.querySelector("#reference-error");
const statusResult = document.querySelector("#status-result");

const ro = {
  navServices: "Servicii", navRequests: "Cererile mele", navHelp: "Ajutor", category: "Construcții și străzi",
  home: "Acasă", permits: "Autorizații", shortTitle: "Modificări locuință", eyebrow: "Înainte să modificați o locuință",
  title: "Autorizație pentru modificarea locuinței", lede: "Verificați dacă lucrarea necesită autorizație, pregătiți dovezile corecte și urmăriți o singură cerere până la decizie.",
  formTime: "Durata formularului", decisionTime: "Decizie", workingDays: "10 zile lucrătoare", fee: "Taxă", noFee: "Fără taxă",
  beforeStart: "Înainte de a începe", beforeCopy: "Aveți nevoie de adresa proprietății, o descriere scurtă a lucrării și o schiță sau un plan al constructorului.",
  address: "Adresa proprietății", addressNote: "Includeți apartamentul și numărul cadastral dacă este cunoscut", workPlan: "Planul lucrării", workPlanNote: "PDF, JPG sau PNG; maximum 15 MB", consent: "Acordul proprietarului", consentNote: "Doar dacă solicitantul este chiriaș",
  firstCheck: "Mai întâi, verificați eligibilitatea", checkNeed: "Aveți nevoie de această autorizație?", checkCopy: "Răspundeți la trei întrebări. Răspunsurile nu sunt trimise.", fixAnswers: "Verificați răspunsurile",
  qProperty: "Proprietatea se află în limitele municipiului Larkhaven?", qStructure: "Lucrarea va modifica pereți, ferestre, accesul sau acoperișul?", qEmergency: "Este o lucrare urgentă pentru eliminarea unui risc imediat?", yes: "Da", no: "Nu", unsure: "Nu sunt sigur", checkButton: "Verifică și continuă",
  resultLabel: "Rezultatul verificării", seeSteps: "Vezi etapele cererii", applicationPath: "Parcursul cererii", oneRequest: "O cerere, patru etape vizibile", stageStart: "Începeți și identificați proprietatea", stageStartCopy: "Salvați imediat după validarea adresei.", stageEvidence: "Adăugați detalii și dovezi", stageEvidenceCopy: "Fișierele sunt verificate înainte de trimitere.", stageReview: "Revizuiți și trimiteți", stageReviewCopy: "Vedeți toate răspunsurile și anexele împreună.", stageTrack: "Urmăriți și răspundeți", stageTrackCopy: "Solicitările de dovezi rămân în aceeași cronologie.", startApplication: "Începe cererea",
  yourJourney: "Parcursul serviciului", knowNext: "Aflați ce urmează", journeyCheck: "Verificare", journeyCheckCopy: "Eligibilitate și dovezi", journeyApply: "Cerere", journeyApplyCopy: "Salvare și trimitere", journeyRespond: "Răspuns", journeyRespondCopy: "Informații lipsă", journeyDecision: "Decizie", journeyDecisionCopy: "Document descărcabil",
  needHelp: "Aveți nevoie de ajutor?", talkPerson: "Discutați cu o persoană", helpCopy: "Echipa poate explica procesul, poate organiza un interpret sau o programare asistată.", hours: "Lun–Vin, 08:30–16:30", fictional: "Prototip fictiv pentru evaluarea Snowe", accessibility: "Accesibilitate", privacy: "Confidențialitate",
  existingRequest: "Cerere existentă", checkStatus: "Verifică starea cererii", statusCopy: "Introduceți referința din e-mail. Prototipul acceptă LH-24017.", reference: "Referința cererii", referenceHint: "Format: LH urmat de cinci cifre", findRequest: "Găsește cererea", currentStatus: "Starea curentă", evidenceReceived: "Dovezi primite", statusResultCopy: "Trimisă la 6 august. Atribuită Mirei Petrescu. Următoarea actualizare: 14 august."
};
const english = new Map([...document.querySelectorAll("[data-i18n]")].map((node) => [node.dataset.i18n, node.textContent]));

navToggle.addEventListener("click", () => {
  const open = navToggle.getAttribute("aria-expanded") !== "true";
  navToggle.setAttribute("aria-expanded", String(open));
  navToggle.textContent = open ? "Close" : "Menu";
  serviceNav.dataset.open = String(open);
});

languageToggle.addEventListener("click", () => {
  const next = document.documentElement.lang === "en" ? "ro" : "en";
  document.documentElement.lang = next;
  for (const node of document.querySelectorAll("[data-i18n]")) {
    node.textContent = next === "ro" ? ro[node.dataset.i18n] || english.get(node.dataset.i18n) : english.get(node.dataset.i18n);
  }
  languageToggle.textContent = next === "ro" ? "EN" : "RO";
  languageToggle.setAttribute("aria-label", next === "ro" ? "Switch language to English" : "Schimbă limba în română");
});

eligibilityForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const missing = [...eligibilityForm.querySelectorAll("fieldset")].filter((fieldset) => !fieldset.querySelector("input:checked"));
  const list = eligibilityErrors.querySelector("ul");
  list.replaceChildren();
  if (missing.length) {
    for (const fieldset of missing) {
      const input = fieldset.querySelector("input");
      const item = document.createElement("li");
      const link = document.createElement("a");
      link.href = `#${input.id || input.name}`;
      link.textContent = fieldset.querySelector("legend").textContent.trim();
      link.addEventListener("click", (clickEvent) => { clickEvent.preventDefault(); input.focus(); });
      item.append(link); list.append(item);
    }
    eligibilityErrors.hidden = false;
    eligibilityResult.hidden = true;
    eligibilityErrors.focus();
    return;
  }
  eligibilityErrors.hidden = true;
  const values = new FormData(eligibilityForm);
  const title = document.querySelector("#result-title");
  const copy = document.querySelector("#result-copy");
  if (values.get("property") === "no") {
    title.textContent = "Use the authority for the property's location";
    copy.textContent = "Larkhaven cannot decide this address. We will direct you to the correct local authority without starting an application.";
  } else if (values.get("emergency") === "yes") {
    title.textContent = "Call before starting an online request";
    copy.textContent = "Urgent safety work follows a faster assisted route. Call 021 555 0144 so an officer can record the risk and next safe action.";
  } else if (values.get("structure") === "no") {
    title.textContent = "A permit may not be required";
    copy.textContent = "Cosmetic work usually does not need this permit. Keep a record of the work and check protected-building rules before proceeding.";
  } else {
    title.textContent = "You can use this service";
    copy.textContent = "Your answers indicate that a permit review is likely. You can begin now and save before uploading evidence.";
  }
  eligibilityResult.hidden = false;
  eligibilityResult.focus();
});

document.querySelector("#save-demo").addEventListener("click", () => {
  document.querySelector("#save-note").textContent = "Prototype only: a production service would create a saved draft before requesting evidence.";
});

statusOpen.addEventListener("click", () => statusDialog.showModal());
statusDialog.addEventListener("close", () => statusOpen.focus());
statusForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (event.submitter?.value === "cancel") { statusDialog.close(); return; }
  if (!/^LH-\d{5}$/i.test(referenceInput.value.trim())) {
    referenceError.textContent = "Enter a reference such as LH-24017.";
    referenceError.hidden = false;
    statusResult.hidden = true;
    referenceInput.setAttribute("aria-invalid", "true");
    referenceInput.focus();
    return;
  }
  referenceError.hidden = true;
  referenceInput.removeAttribute("aria-invalid");
  statusResult.hidden = false;
  statusResult.focus();
});

window.__benchmarkReady = true;
