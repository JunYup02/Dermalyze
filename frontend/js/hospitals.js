requireAuth();

const stateEl = document.getElementById("clinics-state");
const listEl = document.getElementById("clinics-list");
const bannerEl = document.getElementById("location-banner");
const mapFrameEl = document.getElementById("map-frame");
const searchInput = document.getElementById("search-input");
const openNowChip = document.getElementById("open-now-chip");
const topRatedChip = document.getElementById("top-rated-chip");
const radiusChips = document.querySelectorAll(".filter-chip[data-radius]");

let coords = null;
let radiusM = 3000;
let allHospitals = [];
let filters = { search: "", openNow: false, topRated: false };

// Contextual "urgent" banner if the user arrived here right after a higher-risk result.
// Mirrors the risk tiering + labels in results.js; duplicated here to keep pages independent.
const CLASS_LABEL = {
  mel: "Melanoma", bcc: "Basal Cell Carcinoma", akiec: "Actinic Keratosis / Intraepithelial Carcinoma",
  bkl: "Benign Keratosis-like Lesion", nv: "Melanocytic Nevus", vasc: "Vascular Lesion", df: "Dermatofibroma",
};
const HIGH_RISK_CLASSES = ["mel"];
const MODERATE_RISK_CLASSES = ["bcc", "akiec"];

(function showUrgentContextIfAny() {
  const raw = sessionStorage.getItem("dermalyze_result");
  if (!raw) return;
  try {
    const data = JSON.parse(raw);
    const top = [...(data.predictions || [])].sort((a, b) => b.probability - a.probability)[0];
    if (!top) return;
    const key = (top.name || top.id || "").toLowerCase();
    const risk = HIGH_RISK_CLASSES.includes(key) ? "high" : MODERATE_RISK_CLASSES.includes(key) ? "moderate" : null;
    if (!risk) return;

    const bg = risk === "high" ? "var(--error-container)" : "var(--risk-moderate-bg)";
    const fg = risk === "high" ? "var(--on-error-container)" : "var(--risk-moderate-fg)";
    const banner = document.getElementById("urgent-banner");
    banner.style.background = bg;
    banner.classList.remove("hidden");
    ["urgent-banner-icon", "urgent-banner-eyebrow", "urgent-banner-title", "urgent-banner-sub"].forEach((id) => {
      document.getElementById(id).style.color = fg;
    });
    document.getElementById("urgent-banner-icon").textContent = risk === "high" ? "emergency" : "priority_high";
    document.getElementById("urgent-banner-eyebrow").textContent = risk === "high" ? "Urgent attention needed" : "Attention recommended";
    document.getElementById("urgent-banner-title").textContent = `Possible ${CLASS_LABEL[key] || "finding"} — ${risk === "high" ? "High" : "Moderate"} risk`;
    document.getElementById("urgent-banner-sub").textContent =
      risk === "high"
        ? "We recommend seeing a dermatologist within 1-2 weeks."
        : "Professional evaluation is recommended when convenient.";
  } catch {
    /* ignore malformed session data */
  }
})();

function setLoading(message) {
  listEl.innerHTML = "";
  stateEl.classList.remove("hidden");
  stateEl.innerHTML = `
    <div class="spinner" style="border-color: color-mix(in srgb, var(--outline) 30%, transparent); border-top-color: var(--outline);"></div>
    <p>${message}</p>
  `;
}

function formatDistance(meters) {
  if (meters < 1000) return `${Math.round(meters)} m`;
  return `${(meters / 1000).toFixed(1)} km`;
}

function statusPill(hospital) {
  if (hospital.open_now === true) return `<span class="status-pill status-open">Open now</span>`;
  if (hospital.open_now === false) return `<span class="status-pill status-closed">Closed</span>`;
  if (!hospital.business_status) return "";
  const open = hospital.business_status === "OPERATIONAL";
  const label = hospital.business_status.replaceAll("_", " ").toLowerCase().replace(/^\w/, (c) => c.toUpperCase());
  return `<span class="status-pill ${open ? "status-open" : "status-closed"}">${label}</span>`;
}

function starsMarkup(hospital) {
  if (!hospital.rating) return "";
  return `
    <span class="stars">
      <span class="material-symbols-outlined icon-filled">star</span>
      <span class="rating-value">${hospital.rating.toFixed(1)}</span>
      ${hospital.user_rating_count ? `<span class="rating-count">(${hospital.user_rating_count})</span>` : ""}
    </span>
  `;
}

function todayHoursLine(hospital) {
  if (!hospital.weekday_hours || !hospital.weekday_hours.length) return "";
  const dayIndex = (new Date().getDay() + 6) % 7; // API lists Monday first; JS getDay() is Sunday-first
  return hospital.weekday_hours[dayIndex] || "";
}

function applyFilters(hospitals) {
  let result = hospitals;
  if (filters.search.trim()) {
    const q = filters.search.trim().toLowerCase();
    result = result.filter((h) => h.name.toLowerCase().includes(q));
  }
  if (filters.openNow) {
    result = result.filter((h) => h.open_now === true);
  }
  result = [...result].sort((a, b) =>
    filters.topRated ? (b.rating || 0) - (a.rating || 0) : a.distance_m - b.distance_m
  );
  return result;
}

function renderClinics() {
  stateEl.classList.add("hidden");
  listEl.innerHTML = "";

  const hospitals = applyFilters(allHospitals);

  if (!hospitals.length) {
    stateEl.classList.remove("hidden");
    stateEl.innerHTML = `
      <span class="material-symbols-outlined">search_off</span>
      <h3>No clinics match</h3>
      <p>Try a wider radius or clearing filters.</p>
    `;
    return;
  }

  hospitals.forEach((h) => {
    const card = document.createElement("article");
    card.className = "card clinic-card";
    card.innerHTML = `
      <div class="clinic-head">
        <div>
          <h4>${h.name}</h4>
          ${starsMarkup(h)}
        </div>
        ${statusPill(h)}
      </div>
      <div class="clinic-meta">
        <span><span class="material-symbols-outlined" style="font-size:18px;">near_me</span>${formatDistance(h.distance_m)}</span>
        ${todayHoursLine(h) ? `<span><span class="material-symbols-outlined" style="font-size:18px;">schedule</span>${todayHoursLine(h)}</span>` : ""}
      </div>
      <p class="text-body-md text-on-surface-variant" style="margin:0;">${h.address}</p>
      <div style="display:flex; gap:8px;">
        ${h.phone ? `<a class="btn btn-outline" style="flex:1;" href="tel:${h.phone}"><span class="material-symbols-outlined" style="font-size:18px;">call</span>Call</a>` : ""}
        <a class="btn btn-primary" style="flex:1;" href="${h.google_maps_url}" target="_blank" rel="noopener">
          <span class="material-symbols-outlined" style="font-size:18px;">directions</span>
          Directions
        </a>
      </div>
    `;
    listEl.appendChild(card);
  });
}

async function loadClinics() {
  if (!coords) return;
  setLoading("Finding nearby dermatology clinics…");
  mapFrameEl.classList.remove("hidden");
  mapFrameEl.innerHTML = `<iframe src="https://www.google.com/maps?q=${coords.lat},${coords.lng}&z=13&output=embed" loading="lazy" title="Map of nearby clinics"></iframe>`;
  try {
    allHospitals = await Api.getNearbyHospitals(coords.lat, coords.lng, radiusM);
    renderClinics();
  } catch (err) {
    stateEl.classList.remove("hidden");
    stateEl.innerHTML = `
      <span class="material-symbols-outlined text-error">error</span>
      <h3>Couldn't load clinics</h3>
      <p>${err.message}</p>
      <button class="btn btn-outline" id="retry-clinics">Try again</button>
    `;
    document.getElementById("retry-clinics").addEventListener("click", loadClinics);
  }
}

radiusChips.forEach((chip) => {
  chip.addEventListener("click", () => {
    radiusChips.forEach((c) => c.classList.remove("active"));
    chip.classList.add("active");
    radiusM = Number(chip.dataset.radius);
    loadClinics();
  });
});

searchInput.addEventListener("input", () => {
  filters.search = searchInput.value;
  renderClinics();
});

openNowChip.addEventListener("click", () => {
  filters.openNow = !filters.openNow;
  openNowChip.classList.toggle("active", filters.openNow);
  renderClinics();
});

topRatedChip.addEventListener("click", () => {
  filters.topRated = !filters.topRated;
  topRatedChip.classList.toggle("active", filters.topRated);
  renderClinics();
});

function requestLocation() {
  if (!navigator.geolocation) {
    bannerEl.classList.remove("hidden");
    bannerEl.querySelector("span:last-child").textContent =
      "This browser doesn't support location lookup. Try a different browser to find nearby clinics.";
    stateEl.classList.add("hidden");
    return;
  }

  navigator.geolocation.getCurrentPosition(
    (position) => {
      coords = { lat: position.coords.latitude, lng: position.coords.longitude };
      loadClinics();
    },
    () => {
      bannerEl.classList.remove("hidden");
      bannerEl.querySelector("span:last-child").textContent =
        "Location access was denied. Enable location permissions for this site to see nearby clinics.";
      stateEl.classList.add("hidden");
    },
    { enableHighAccuracy: false, timeout: 10000 }
  );
}

requestLocation();
