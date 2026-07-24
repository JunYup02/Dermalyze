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
// real illustration assets in assets/images/silhouette-{front,back}.png. Every
// left/right pair carries a `side` so each half can be selected (and labeled)
// separately, even though the backend's BodyRegion enum only knows the bare key
// ("arms"/"hands"/"legs"/"feet") -- side is frontend-only display metadata, not
// sent to the API.
//
// Side convention (confirmed against the Stitch "Select Location - Left/Right
// Split" mockup): screen-left is always labeled "Left X" and screen-right "Right
// X", on both front and back views -- not anatomically mirrored for the front view.
//
// silhouette-front.png and silhouette-back.png are the same pose/layout at the
// same aspect ratio (just different source resolutions), so one coordinate set
// lines up correctly on both -- front and back share this single array instead
// of keeping two hand-calibrated (and easily-drifting) copies in sync.
const SHARED_HOTSPOTS = [
  { key: "scalp_face", x: 50, y: 10 },
  { key: "neck", x: 50, y: 19 },
  { key: "torso", x: 50, y: 37 },
  { key: "arms", side: "left", x: 21, y: 34 },
  { key: "arms", side: "right", x: 79, y: 34 },
  { key: "hands", side: "left", x: 16, y: 50 },
  { key: "hands", side: "right", x: 84, y: 50 },
  { key: "legs", side: "left", x: 42, y: 73 },
  { key: "legs", side: "right", x: 58, y: 73 },
  { key: "feet", side: "left", x: 42, y: 94 },
  { key: "feet", side: "right", x: 58, y: 94 },
];

const HOTSPOTS = {
  front: SHARED_HOTSPOTS,
  back: SHARED_HOTSPOTS,
};

let regions = [];
let regionLabel = {};

// Regular pluralization (Arms -> Arm, Hands -> Hand, Legs -> Leg) doesn't cover
// "Feet", the one irregular plural among the backend's region labels.
function singularize(label) {
  if (label === "Feet") return "Foot";
  return label.replace(/s$/, "");
}

function labelFor(key, side) {
  // "torso" reads as "Back" once looking at the back view (matches the backend's
  // normalize_body_part: back + torso -> "back").
  if (state.view === "back" && key === "torso") return "Back";
  const base = regionLabel[key] || key;
  if (side === "left") return `Left ${singularize(base)}`;
  if (side === "right") return `Right ${singularize(base)}`;
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
