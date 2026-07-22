requireAuth();

/**
 * Risk tiering for the HAM10000 classes the Vertex AI AutoML model was
 * trained on (see Dermalyze_data/undersampling). Keyed by the lowercased
 * class `name` the backend returns (ClassPrediction.name = AutoML displayName).
 *
 * mel (melanoma) is the acutely dangerous one -> high.
 * bcc (basal cell carcinoma) and akiec (actinic keratosis / early
 * intraepithelial carcinoma) are malignant/pre-malignant but typically
 * slower-growing and rarely fatal if caught -> moderate.
 * nv, bkl, vasc, df are benign -> low.
 */
const CLASS_INFO = {
  mel: { label: "Melanoma", risk: "high" },
  bcc: { label: "Basal Cell Carcinoma", risk: "moderate" },
  akiec: { label: "Actinic Keratosis / Intraepithelial Carcinoma", risk: "moderate" },
  bkl: { label: "Benign Keratosis-like Lesion", risk: "low" },
  nv: { label: "Melanocytic Nevus", risk: "low" },
  vasc: { label: "Vascular Lesion", risk: "low" },
  df: { label: "Dermatofibroma", risk: "low" },
};

const RISK_COPY = {
  high: { pill: "Higher-risk pattern", icon: "warning" },
  moderate: { pill: "Moderate-risk pattern", icon: "priority_high" },
  low: { pill: "Lower-risk pattern", icon: "check_circle" },
};

function classInfo(prediction) {
  const key = (prediction.name || prediction.id || "").toLowerCase();
  return CLASS_INFO[key] || { label: prediction.name || prediction.id || "Unknown", risk: "low" };
}

const raw = sessionStorage.getItem("dermalyze_result");

const contentEl = document.getElementById("result-content");
const emptyEl = document.getElementById("empty-state");
const unavailableEl = document.getElementById("model-unavailable");

if (!raw) {
  emptyEl.classList.remove("hidden");
} else {
  const data = JSON.parse(raw);
  if (!data.predictions || data.predictions.length === 0) {
    unavailableEl.classList.remove("hidden");
  } else {
    render(data);
  }
}

function render(data) {
  contentEl.classList.remove("hidden");

  if (data.imageDataUrl) {
    document.getElementById("image-section").classList.remove("hidden");
    document.getElementById("result-img").src = data.imageDataUrl;
  }
  document.getElementById("result-region-label").textContent = data.bodyPart?.label || "—";

  const sorted = [...data.predictions].sort((a, b) => b.probability - a.probability);
  const top = sorted[0];
  const info = classInfo(top);
  const pct = Math.round(top.probability * 100);
  const risk = info.risk;

  document.getElementById("gauge-percent").textContent = `${pct}%`;
  document.getElementById("gauge-label").textContent = info.label;

  const fill = document.getElementById("gauge-fill");
  fill.setAttribute("stroke-dasharray", `${pct}, 100`);
  fill.classList.add(risk === "high" ? "error" : risk === "moderate" ? "moderate" : "ok");

  const badge = document.getElementById("risk-badge");
  badge.classList.add(risk);
  badge.innerHTML = `
    <span class="material-symbols-outlined icon-filled" style="font-size:16px;">${RISK_COPY[risk].icon}</span>
    <span>${RISK_COPY[risk].pill}</span>
  `;

  document.getElementById("gemini-report").textContent =
    data.report || "No written summary was returned for this analysis.";
  document.getElementById("texture-note").textContent = data.texture_note || "Not available.";
  document.getElementById("pigment-note").textContent = data.pigment_note || "Not available.";

  const others = sorted.slice(1, 5);
  if (others.length) {
    document.getElementById("rank-section").style.display = "flex";
    const list = document.getElementById("rank-list");
    others.forEach((p) => {
      const otherInfo = classInfo(p);
      const otherPct = Math.round(p.probability * 100);
      const row = document.createElement("div");
      row.className = "rank-row";
      row.innerHTML = `
        <span class="rank-name">${otherInfo.label}</span>
        <span class="rank-bar-track"><span class="rank-bar-fill" style="width:${otherPct}%;"></span></span>
        <span class="rank-pct">${otherPct}%</span>
      `;
      list.appendChild(row);
    });
  }

  if (risk === "high" || risk === "moderate") {
    const cta = document.getElementById("clinic-cta");
    cta.classList.remove("hidden");
    // High risk reads as urgent (red); moderate is a calmer prompt (teal), matching
    // how the two tiers are framed everywhere else on this page.
    cta.classList.toggle("btn-danger", risk === "high");
    cta.classList.toggle("btn-primary", risk === "moderate");
    document.getElementById("clinic-cta-label").textContent =
      risk === "high" ? "Find a dermatologist nearby" : "Book a professional review";
  }

  document.getElementById("print-btn").addEventListener("click", () => window.print());

  // Save this completed analysis into the (local, per-browser) scan history so it
  // shows up on the dashboard — see js/history.js for why this isn't backend-persisted.
  saveScanRecord({
    region_label: data.bodyPart?.label || "—",
    risk,
    top_label: info.label,
    top_probability: top.probability,
    finding_text: data.texture_note || data.report?.slice(0, 100) || "",
    imageDataUrl: data.imageDataUrl,
    resultPayload: data,
  });
}
