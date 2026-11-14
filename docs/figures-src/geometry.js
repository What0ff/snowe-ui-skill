// Draw dashed guides from the idle state so that any movement of the button
// or the card edge in the other states is visible against them.
const states = [...document.querySelectorAll(".state")];
const idleCard = states[0].querySelector(".card").getBoundingClientRect();
const idleButton = states[0].querySelector(".btn").getBoundingClientRect();
const lowestCard = Math.max(...states.map((state) => state.querySelector(".card").getBoundingClientRect().bottom));

function guide(kind, style) {
  const element = document.createElement("div");
  element.className = `guide ${kind}`;
  Object.assign(element.style, style);
  document.body.append(element);
}

guide("h", { top: `${Math.round(idleButton.top)}px` });
guide("h", { top: `${Math.round(idleCard.bottom)}px` });
for (const state of states) {
  const card = state.querySelector(".card").getBoundingClientRect();
  guide("v", {
    left: `${Math.round(card.left + (idleButton.right - idleCard.left))}px`,
    top: `${Math.round(idleCard.top - 6)}px`,
    height: `${Math.round(lowestCard - idleCard.top + 12)}px`,
  });
}
