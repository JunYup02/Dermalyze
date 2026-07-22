/**
 * Real, per-browser scan history — no backend model/endpoint exists for this yet,
 * so it's derived entirely from analyses actually completed in this browser
 * (namespaced per logged-in username so switching accounts on the same device
 * doesn't mix histories). Nothing here is fabricated.
 */
const MAX_HISTORY = 20;

function historyKey() {
  return `dermalyze_scan_history_${currentUsername() || "anon"}`;
}

function getScanHistory() {
  try {
    return JSON.parse(localStorage.getItem(historyKey()) || "[]");
  } catch {
    return [];
  }
}

/** record: { region_label, risk, top_label, top_probability, finding_text, imageDataUrl, resultPayload } */
function saveScanRecord(record) {
  const entry = { id: crypto.randomUUID(), timestamp: Date.now(), ...record };
  const list = [entry, ...getScanHistory()].slice(0, MAX_HISTORY);
  try {
    localStorage.setItem(historyKey(), JSON.stringify(list));
  } catch {
    // Quota exceeded (likely from embedded images) — retry once without image data.
    const trimmed = list.map((r) => ({ ...r, imageDataUrl: undefined, resultPayload: { ...r.resultPayload, imageDataUrl: undefined } }));
    try {
      localStorage.setItem(historyKey(), JSON.stringify(trimmed));
    } catch {
      /* give up silently; history is a nice-to-have, not critical path */
    }
  }
}

function relativeTime(timestamp) {
  const diffMs = Date.now() - timestamp;
  const mins = Math.round(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  if (days < 30) return `${days}d ago`;
  const months = Math.round(days / 30);
  return `${months}mo ago`;
}
