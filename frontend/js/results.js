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
  high: {
    pill: "Higher-risk pattern",
    icon: "warning",
    subtitle: "High risk of malignancy detected. Immediate specialist consultation is recommended.",
    ctaVariant: "btn-danger",
    ctaIcon: "emergency",
    ctaLabel: "Urgent: Find nearest specialist",
    printLabel: "Download urgent clinical report",
  },
  moderate: {
    pill: "Moderate-risk pattern",
    icon: "priority_high",
    subtitle: "We recommend a professional evaluation for this finding.",
    ctaVariant: "btn-primary",
    ctaIcon: "calendar_month",
    ctaLabel: "Book a professional review",
    printLabel: "Download PDF report",
  },
  low: {
    pill: "Lower-risk pattern",
    icon: "check_circle",
    subtitle: "Non-concerning visual patterns detected.",
    ctaVariant: "btn-outline",
    ctaIcon: "calendar_month",
    ctaLabel: "Find a clinic near you",
    printLabel: "Download PDF report",
  },
};

function makeRefCode() {
  return "DZ-" + Date.now().toString(36).toUpperCase();
}

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

  if (data.isDemo) {
    const demoBanner = document.createElement("div");
    demoBanner.className = "banner";
    demoBanner.style.background = "var(--risk-moderate-bg)";
    demoBanner.style.color = "var(--risk-moderate-fg)";
    demoBanner.innerHTML = `
      <span class="material-symbols-outlined">science</span>
      <span>Demo data — the Vertex AI model isn't connected yet, so this is placeholder output, not a real analysis.</span>
    `;
    contentEl.prepend(demoBanner);
  }

  const sorted = [...data.predictions].sort((a, b) => b.probability - a.probability);
  const top = sorted[0];
  const info = classInfo(top);
  const pct = Math.round(top.probability * 100);
  const risk = info.risk;
  const refCode = data.refCode || makeRefCode();

  if (data.imageDataUrl) {
    document.getElementById("image-section").classList.remove("hidden");
    document.getElementById("result-img").src = data.imageDataUrl;
    // High-risk findings get a pulsing alert border + "enlarged view" badge on the
    // photo itself, matching the urgency treatment the low/moderate tiers don't use.
    document.getElementById("preview-frame").classList.toggle("risk-high", risk === "high");
    document.getElementById("preview-alert-badge").classList.toggle("hidden", risk !== "high");
  }
  document.getElementById("result-region-label").textContent = data.bodyPart?.label || "—";

  document.getElementById("result-classification").textContent = `${info.label} — ${pct}%`;
  document.getElementById("result-subtitle").textContent = RISK_COPY[risk].subtitle;
  document.getElementById("result-ref").textContent = `Ref: #${refCode}`;

  const badge = document.getElementById("risk-badge");
  badge.classList.add(risk);
  badge.innerHTML = `
    <span class="material-symbols-outlined icon-filled" style="font-size:16px;">${RISK_COPY[risk].icon}</span>
    <span>${RISK_COPY[risk].pill}</span>
  `;

  document.getElementById("result-success").classList.toggle("hidden", risk !== "low");

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

  // Clinic CTA: red/urgent for high risk, teal for moderate, outline for low.
  const cta = document.getElementById("clinic-cta");
  cta.classList.remove("hidden", "btn-danger", "btn-primary", "btn-outline");
  cta.classList.add(RISK_COPY[risk].ctaVariant);
  document.getElementById("clinic-cta-icon").textContent = RISK_COPY[risk].ctaIcon;
  document.getElementById("clinic-cta-label").textContent = RISK_COPY[risk].ctaLabel;

  if (risk === "high") {
    // High risk: also search automatically instead of waiting for a click, in
    // addition to the urgent CTA above.
    document.getElementById("auto-clinics").classList.remove("hidden");
    autoFetchNearbyClinics();
  }

  document.getElementById("print-btn-label").textContent = RISK_COPY[risk].printLabel;
  document.getElementById("print-btn").addEventListener("click", () => downloadPdfReport(data, { info, pct, risk, refCode }));

  // Save this completed analysis into the (local, per-browser) scan history so it
  // shows up on the dashboard — see js/history.js for why this isn't backend-persisted.
  // Demo results (no Vertex endpoint connected) are deliberately not saved, since
  // they aren't a real analysis.
  if (!data.isDemo) {
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
}

/* ------------------------------------------------------------------ */
/* High risk: search nearby clinics automatically, no click required.  */
/* ------------------------------------------------------------------ */
function autoFetchNearbyClinics() {
  const stateEl = document.getElementById("auto-clinics-state");
  const listEl = document.getElementById("auto-clinics-list");

  function fail(message) {
    stateEl.innerHTML = `
      <span class="material-symbols-outlined">location_off</span>
      <p>${message}</p>
      <a href="hospitals.html" class="btn btn-outline">
        <span class="material-symbols-outlined">medical_services</span>
        Search clinics manually
      </a>
    `;
  }

  if (!navigator.geolocation) {
    fail("This browser doesn't support location lookup — open Clinics to search manually.");
    return;
  }

  // The clinic lookup runs against a free, shared community service (no API key) that
  // can be slow or briefly rate-limited under load. Auto-search is a nicety, not the
  // only path to clinics, so time out and hand off to the manual Clinics tab instead
  // of leaving a spinner running forever.
  const AUTO_SEARCH_TIMEOUT_MS = 12000;

  navigator.geolocation.getCurrentPosition(
    async (position) => {
      try {
        const hospitals = await Promise.race([
          Api.getNearbyHospitals(position.coords.latitude, position.coords.longitude, 5000),
          new Promise((_, reject) => setTimeout(() => reject(new Error("timed out")), AUTO_SEARCH_TIMEOUT_MS)),
        ]);
        stateEl.classList.add("hidden");
        if (!hospitals.length) {
          listEl.innerHTML = `<p class="text-body-md text-outline">No clinics found nearby — try the Clinics tab for a wider search.</p>`;
          return;
        }
        hospitals.slice(0, 3).forEach((h) => {
          const distanceText = h.distance_m < 1000 ? `${Math.round(h.distance_m)} m` : `${(h.distance_m / 1000).toFixed(1)} km`;
          const row = document.createElement("a");
          row.className = "card";
          row.style.cssText = "display:flex; align-items:center; gap:12px; text-decoration:none; padding:14px 16px;";
          row.href = h.google_maps_url;
          row.target = "_blank";
          row.rel = "noopener";
          row.innerHTML = `
            <span class="material-symbols-outlined text-primary">location_on</span>
            <span style="flex:1; min-width:0;">
              <span style="display:block; font-weight:600; font-size:14px; color:var(--on-surface); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${h.name}</span>
              <span style="display:block; font-size:12.5px; color:var(--outline);">${distanceText} away</span>
            </span>
            <span class="material-symbols-outlined text-outline">chevron_right</span>
          `;
          listEl.appendChild(row);
        });
        const viewAll = document.createElement("a");
        viewAll.href = "hospitals.html";
        viewAll.className = "btn btn-outline";
        viewAll.innerHTML = `<span class="material-symbols-outlined">medical_services</span>View all nearby clinics`;
        listEl.appendChild(viewAll);
      } catch (err) {
        fail(
          err.message === "timed out"
            ? "This is taking longer than expected."
            : `Couldn't load nearby clinics: ${err.message}`
        );
      }
    },
    () => fail("Location access was denied — open Clinics to search manually."),
    { enableHighAccuracy: false, timeout: 10000 }
  );
}

/* ------------------------------------------------------------------ */
/* Real PDF report: vector text (a Korean font is embedded for jsPDF),  */
/* built from the same Gemini-generated fields shown on screen -- not   */
/* a screenshot of the page.                                            */
/* ------------------------------------------------------------------ */
let pdfLibsPromise = null;
function loadPdfLibs() {
  if (pdfLibsPromise) return pdfLibsPromise;
  function loadScript(src) {
    return new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = src;
      s.onload = resolve;
      s.onerror = () => reject(new Error(`Failed to load ${src}`));
      document.head.appendChild(s);
    });
  }
  pdfLibsPromise = loadScript("https://cdn.jsdelivr.net/npm/jspdf@2.5.2/dist/jspdf.umd.min.js").then(() =>
    loadScript("assets/fonts/NotoSansKR-normal.js")
  );
  return pdfLibsPromise;
}

async function downloadPdfReport(data, { info, pct, risk, refCode }) {
  const btn = document.getElementById("print-btn");
  setButtonBusy(btn, true, "Preparing PDF…");
  try {
    await loadPdfLibs();
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({ unit: "pt", format: "a4" });
    // Registered on the instance (not the API prototype) -- this is the reliable path
    // in jsPDF v2.x; the old addFileToVFS/addFont-before-instantiation pattern from
    // jsPDF's fontconverter tool throws internally on recent versions.
    doc.addFileToVFS("NotoSansKR-Regular.ttf", window.__NOTO_SANS_KR_BASE64__);
    doc.addFont("NotoSansKR-Regular.ttf", "NotoSansKR", "normal");
    doc.setFont("NotoSansKR", "normal");

    const margin = 48;
    const pageWidth = doc.internal.pageSize.getWidth();
    const contentWidth = pageWidth - margin * 2;
    let y = margin;

    function heading(text, size) {
      doc.setFontSize(size);
      doc.text(text, margin, y);
      y += size * 1.4;
    }
    function paragraph(text, size = 11) {
      doc.setFontSize(size);
      const lines = doc.splitTextToSize(text, contentWidth);
      doc.text(lines, margin, y);
      y += lines.length * size * 1.5 + 10;
    }
    function rule() {
      doc.setDrawColor(220, 220, 220);
      doc.line(margin, y, pageWidth - margin, y);
      y += 18;
    }

    heading("Dermalyze Analysis Report", 20);
    doc.setFontSize(10);
    doc.setTextColor(120, 120, 120);
    doc.text(`${new Date().toLocaleString()}  ·  Ref: #${refCode}`, margin, y);
    doc.setTextColor(0, 0, 0);
    y += 24;
    rule();

    paragraph(`Region: ${data.bodyPart?.label || "—"}`, 12);
    paragraph(`Classification: ${info.label} (${pct}%)`, 12);
    paragraph(`Risk tier: ${risk.charAt(0).toUpperCase() + risk.slice(1)} risk`, 12);
    if (data.isDemo) {
      doc.setTextColor(180, 100, 20);
      paragraph("This is placeholder demo output — no Vertex AI model was connected when it was generated.", 10);
      doc.setTextColor(0, 0, 0);
    }
    rule();

    heading("Summary", 13);
    paragraph(data.report || "No written summary was returned for this analysis.");

    heading("Texture", 13);
    paragraph(data.texture_note || "Not available.");

    heading("Pigment", 13);
    paragraph(data.pigment_note || "Not available.");

    rule();
    doc.setFontSize(9);
    doc.setTextColor(120, 120, 120);
    const disclaimer = doc.splitTextToSize(
      "This AI-generated analysis is for informational purposes only and is not a clinical diagnosis. Always consult a licensed dermatologist for medical advice before making any health-related decisions.",
      contentWidth
    );
    doc.text(disclaimer, margin, y);

    const stamp = new Date().toISOString().slice(0, 10);
    doc.save(`dermalyze-report-${stamp}.pdf`);
  } catch (err) {
    alert("Couldn't generate the PDF: " + err.message);
  } finally {
    setButtonBusy(btn, false);
  }
}
