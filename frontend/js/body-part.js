requireAuth();

const state = { view: "front", region: null };

const frontBtn = document.getElementById("front-view-btn");
const backBtn = document.getElementById("back-view-btn");
const stateEl = document.getElementById("regions-state");
const wrapEl = document.getElementById("silhouette-wrap");
const frameFront = document.getElementById("frame-front");
const frameBack = document.getElementById("frame-back");
const selectedLabelEl = document.getElementById("selected-region-label");
const errorEl = document.getElementById("body-part-error");
const nextBtn = document.getElementById("next-step-btn");

// Approximate hotspot positions (percent of silhouette image bounds), read off the
// real illustration assets in assets/images/silhouette-{front,back}.png. Left/right
// pairs both map to the same backend region key.
const HOTSPOTS = {
  front: [
    { key: "scalp_face", x: 50, y: 10 },
    { key: "neck", x: 50, y: 19 },
    { key: "torso", x: 50, y: 37 },
    { key: "arms", x: 17, y: 40 },
    { key: "arms", x: 83, y: 40 },
    { key: "hands", x: 12, y: 55 },
    { key: "hands", x: 88, y: 55 },
    { key: "legs", x: 42, y: 73 },
    { key: "legs", x: 58, y: 73 },
    { key: "feet", x: 42, y: 94 },
    { key: "feet", x: 58, y: 94 },
  ],
  back: [
    { key: "scalp_face", x: 50, y: 6 },
    { key: "neck", x: 50, y: 15 },
    { key: "torso", x: 50, y: 35 },
    { key: "arms", x: 20, y: 38 },
    { key: "arms", x: 80, y: 38 },
    { key: "hands", x: 15, y: 54 },
    { key: "hands", x: 85, y: 54 },
    { key: "legs", x: 43, y: 72 },
    { key: "legs", x: 57, y: 72 },
    { key: "feet", x: 43, y: 93 },
    { key: "feet", x: 57, y: 93 },
  ],
};

let regions = [];
let regionLabel = {};

function labelFor(key) {
  // "torso" reads as "Back" once looking at the back view (matches the backend's
  // normalize_body_part: back + torso -> "back").
  if (state.view === "back" && key === "torso") return "Back";
  return regionLabel[key] || key;
}

function buildHotspots(view, frameEl) {
  frameEl.querySelectorAll(".hotspot").forEach((el) => el.remove());
  HOTSPOTS[view].forEach((spot) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "hotspot";
    btn.style.left = spot.x + "%";
    btn.style.top = spot.y + "%";
    btn.setAttribute("aria-label", labelFor(spot.key));
    btn.dataset.region = spot.key;
    if (state.view === view && state.region === spot.key) btn.classList.add("selected");
    btn.addEventListener("click", () => selectRegion(spot.key));
    frameEl.appendChild(btn);
  });
}

function selectRegion(key) {
  state.region = key;
  document.querySelectorAll(".hotspot").forEach((el) => {
    el.classList.toggle("selected", el.dataset.region === key);
  });
  selectedLabelEl.innerHTML = `Selected: <strong>${labelFor(key)}</strong> (${state.view} view)`;
  nextBtn.disabled = false;
  if (window.navigator.vibrate) window.navigator.vibrate(10);
}

function setView(view) {
  state.view = view;
  frontBtn.classList.toggle("active", view === "front");
  backBtn.classList.toggle("active", view === "back");
  frameFront.classList.toggle("hidden", view !== "front");
  frameBack.classList.toggle("hidden", view !== "back");
  buildHotspots("front", frameFront);
  buildHotspots("back", frameBack);
  if (state.region) {
    selectedLabelEl.innerHTML = `Selected: <strong>${labelFor(state.region)}</strong> (${state.view} view)`;
  }
}
frontBtn.addEventListener("click", () => setView("front"));
backBtn.addEventListener("click", () => setView("back"));

async function loadRegions() {
  try {
    const data = await Api.getBodyRegions();
    regions = data.regions;
    regionLabel = Object.fromEntries(regions.map((r) => [r.key, r.label]));
    stateEl.classList.add("hidden");
    wrapEl.classList.remove("hidden");
    setView("front");
  } catch (err) {
    stateEl.innerHTML = `
      <span class="material-symbols-outlined text-error">error</span>
      <h3>Couldn't load body regions</h3>
      <p>${err.message}</p>
      <button class="btn btn-outline" id="retry-regions">Try again</button>
    `;
    document.getElementById("retry-regions").addEventListener("click", loadRegions);
  }
}
loadRegions();

nextBtn.addEventListener("click", async () => {
  if (!state.region) return;
  errorEl.classList.add("hidden");
  setButtonBusy(nextBtn, true, "Saving…");
  try {
    const result = await Api.postBodyPart(state.view, state.region);
    sessionStorage.setItem(
      "dermalyze_body_part",
      JSON.stringify({
        view: state.view,
        region: state.region,
        normalized_region: result.normalized_region,
        label: labelFor(state.region),
      })
    );
    window.location.href = "upload.html";
  } catch (err) {
    showBanner(errorEl, err.message);
    setButtonBusy(nextBtn, false);
  }
});
