requireAuth();

const state = { view: "front", region: null, side: null };

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
// real illustration assets in assets/images/silhouette-{front,back}.png. Arms carry a
// `side` so left/right can be selected (and labeled) separately, even though the
// backend's BodyRegion enum only knows the bare "arms" key -- side is frontend-only
// display metadata, not sent to the API. Other left/right pairs still share one key.
//
// silhouette-back.png used to be a 500x500 canvas with the figure only filling a
// small centered box (this file was re-cropped to its content bounding box so it
// fills the frame like the front asset does) -- hotspot percentages below are
// calibrated against that cropped image.
const HOTSPOTS = {
  front: [
    { key: "scalp_face", x: 50, y: 10 },
    { key: "neck", x: 50, y: 19 },
    { key: "torso", x: 50, y: 37 },
    { key: "arms", side: "left", x: 83, y: 40 },
    { key: "arms", side: "right", x: 17, y: 40 },
    { key: "hands", x: 12, y: 55 },
    { key: "hands", x: 88, y: 55 },
    { key: "legs", x: 42, y: 73 },
    { key: "legs", x: 58, y: 73 },
    { key: "feet", x: 42, y: 94 },
    { key: "feet", x: 58, y: 94 },
  ],
  back: [
    { key: "scalp_face", x: 50, y: 8 },
    { key: "neck", x: 50, y: 17 },
    { key: "torso", x: 50, y: 36 },
    { key: "arms", side: "left", x: 18, y: 42 },
    { key: "arms", side: "right", x: 82, y: 42 },
    { key: "hands", x: 12, y: 57 },
    { key: "hands", x: 88, y: 57 },
    { key: "legs", x: 43, y: 73 },
    { key: "legs", x: 57, y: 73 },
    { key: "feet", x: 43, y: 96 },
    { key: "feet", x: 57, y: 96 },
  ],
};

let regions = [];
let regionLabel = {};

function labelFor(key, side) {
  // "torso" reads as "Back" once looking at the back view (matches the backend's
  // normalize_body_part: back + torso -> "back").
  if (state.view === "back" && key === "torso") return "Back";
  const base = regionLabel[key] || key;
  if (side === "left") return `Left ${base.replace(/s$/, "")}`;
  if (side === "right") return `Right ${base.replace(/s$/, "")}`;
  return base;
}

function buildHotspots(view, frameEl) {
  frameEl.querySelectorAll(".hotspot").forEach((el) => el.remove());
  HOTSPOTS[view].forEach((spot) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "hotspot";
    btn.style.left = spot.x + "%";
    btn.style.top = spot.y + "%";
    btn.setAttribute("aria-label", labelFor(spot.key, spot.side));
    btn.dataset.region = spot.key;
    if (spot.side) btn.dataset.side = spot.side;
    if (state.view === view && state.region === spot.key && state.side === (spot.side || null)) {
      btn.classList.add("selected");
    }
    btn.addEventListener("click", () => selectRegion(spot.key, spot.side || null));
    frameEl.appendChild(btn);
  });
}

function selectRegion(key, side) {
  state.region = key;
  state.side = side || null;
  document.querySelectorAll(".hotspot").forEach((el) => {
    el.classList.toggle("selected", el.dataset.region === key && (el.dataset.side || null) === state.side);
  });
  selectedLabelEl.innerHTML = `Selected: <strong>${labelFor(key, side)}</strong> (${state.view} view)`;
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
    selectedLabelEl.innerHTML = `Selected: <strong>${labelFor(state.region, state.side)}</strong> (${state.view} view)`;
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
        side: state.side,
        normalized_region: result.normalized_region,
        label: labelFor(state.region, state.side),
      })
    );
    window.location.href = "upload.html";
  } catch (err) {
    showBanner(errorEl, err.message);
    setButtonBusy(nextBtn, false);
  }
});
