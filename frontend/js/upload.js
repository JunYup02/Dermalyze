requireAuth();

const bodyPartRaw = sessionStorage.getItem("dermalyze_body_part");
if (!bodyPartRaw) {
  window.location.href = "body-part.html";
}
const bodyPart = bodyPartRaw ? JSON.parse(bodyPartRaw) : null;

document.getElementById("region-chip-label").textContent = bodyPart?.label || "—";
document.getElementById("region-chip-label-2").textContent = bodyPart?.label || "—";

const MAX_BYTES = 10 * 1024 * 1024;

const dropzone = document.getElementById("dropzone");
const previewWrap = document.getElementById("preview-wrap");
const previewImg = document.getElementById("preview-img");
const removeBtn = document.getElementById("remove-photo");
const analyzeBtn = document.getElementById("analyze-btn");
const errorEl = document.getElementById("upload-error");
const cameraInput = document.getElementById("camera-input");
const fileInput = document.getElementById("file-input");

let selectedFile = null;
let selectedDataUrl = null;

function handleFile(file) {
  errorEl.classList.add("hidden");
  if (!file) return;
  if (!file.type.startsWith("image/")) {
    showBanner(errorEl, "Please choose an image file (JPG or PNG).");
    return;
  }
  if (file.size > MAX_BYTES) {
    showBanner(errorEl, "That image is over the 10MB limit — please choose a smaller file.");
    return;
  }

  selectedFile = file;
  const reader = new FileReader();
  reader.onload = () => {
    selectedDataUrl = reader.result;
    previewImg.src = selectedDataUrl;
    dropzone.classList.add("hidden");
    previewWrap.classList.remove("hidden");
    analyzeBtn.disabled = false;
  };
  reader.readAsDataURL(file);
}

cameraInput.addEventListener("change", (e) => handleFile(e.target.files[0]));
fileInput.addEventListener("change", (e) => handleFile(e.target.files[0]));

removeBtn.addEventListener("click", () => {
  selectedFile = null;
  selectedDataUrl = null;
  cameraInput.value = "";
  fileInput.value = "";
  previewWrap.classList.add("hidden");
  dropzone.classList.remove("hidden");
  analyzeBtn.disabled = true;
});

// Drag-and-drop onto the dropzone (desktop convenience)
["dragover", "dragleave", "drop"].forEach((evt) => {
  dropzone.addEventListener(evt, (e) => e.preventDefault());
});
dropzone.addEventListener("dragover", () => dropzone.classList.add("dragover"));
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
dropzone.addEventListener("drop", (e) => {
  dropzone.classList.remove("dragover");
  const file = e.dataTransfer.files?.[0];
  if (file) handleFile(file);
});

analyzeBtn.addEventListener("click", async () => {
  if (!selectedFile) return;
  errorEl.classList.add("hidden");
  setButtonBusy(analyzeBtn, true, "Analyzing photo…");

  try {
    const result = await Api.createGeminiReport(selectedFile);
    const payload = { ...result, bodyPart };

    try {
      sessionStorage.setItem("dermalyze_result", JSON.stringify({ ...payload, imageDataUrl: selectedDataUrl }));
    } catch {
      // Image too large for sessionStorage quota — still proceed without the preview.
      sessionStorage.setItem("dermalyze_result", JSON.stringify(payload));
    }
    window.location.href = "results.html";
  } catch (err) {
    if (err.status === 503) {
      // Vertex env vars aren't set at all yet — expected until a model is deployed.
      // Rather than dead-ending the flow here, continue to the results screen with
      // clearly-labeled placeholder data so the rest of the app stays walkable.
      const demoPayload = {
        bodyPart,
        isDemo: true,
        predictions: [
          { id: "demo-nv", name: "nv", probability: 0.82 },
          { id: "demo-bkl", name: "bkl", probability: 0.11 },
          { id: "demo-mel", name: "mel", probability: 0.07 },
        ],
        report:
          "실제 분석 모델(Vertex AI)이 아직 연결되지 않아 이 결과는 예시(데모) 데이터입니다. 엔드포인트가 배포되고 나면 실제 분석 결과가 표시됩니다.",
        texture_note: "데모 데이터 — 실제 이미지 분석 결과가 아닙니다.",
        pigment_note: "데모 데이터 — 실제 이미지 분석 결과가 아닙니다.",
      };
      try {
        sessionStorage.setItem("dermalyze_result", JSON.stringify({ ...demoPayload, imageDataUrl: selectedDataUrl }));
      } catch {
        sessionStorage.setItem("dermalyze_result", JSON.stringify(demoPayload));
      }
      window.location.href = "results.html";
      return;
    } else if (err.status === 502) {
      // Env vars are set, but the actual Vertex AI call failed (bad endpoint, auth, quota, etc).
      showBanner(errorEl, "The analysis model is connected but the prediction failed: " + err.message);
    } else {
      showBanner(errorEl, err.message);
    }
    setButtonBusy(analyzeBtn, false);
  }
});
