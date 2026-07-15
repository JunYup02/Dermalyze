import { CLASS_LABELS_KO, RISK_LABEL_KO, RISK_STYLES } from "../classes";

function findNearbyDermatology() {
  const openMaps = (query) => window.open(`https://www.google.com/maps/search/${query}`, "_blank");
  if (!navigator.geolocation) {
    openMaps("피부과");
    return;
  }
  navigator.geolocation.getCurrentPosition(
    (pos) => openMaps(`피부과/@${pos.coords.latitude},${pos.coords.longitude},14z`),
    () => openMaps("피부과")
  );
}

export default function ResultPanel({ result, onDownloadReport, reportStatus }) {
  const style = RISK_STYLES[result.risk_level] ?? RISK_STYLES.medium;
  const sortedProbs = Object.entries(result.probabilities).sort((a, b) => b[1] - a[1]);

  return (
    <section className={`bg-white rounded-2xl shadow-sm border border-slate-200 ring-4 ${style.ring} p-6 space-y-6`}>
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <p className="text-sm text-slate-500">예측 결과</p>
          <p className="text-2xl font-bold text-slate-900">{result.label_ko}</p>
          <p className="text-sm text-slate-400">{result.label_en}</p>
        </div>
        <span className={`px-4 py-2 rounded-full text-sm font-semibold ${style.badge}`}>
          {RISK_LABEL_KO[result.risk_level]} · 신뢰도 {(result.confidence * 100).toFixed(1)}%
        </span>
      </div>

      {result.risk_upgraded_low_confidence && (
        <p className="text-sm text-amber-600 bg-amber-50 rounded-lg px-3 py-2">
          예측 신뢰도가 낮아 안전을 위해 위험도를 상향 조정했습니다.
        </p>
      )}

      {result.quality_warnings.length > 0 && (
        <div className="space-y-1">
          {result.quality_warnings.map((w, i) => (
            <p key={i} className="text-sm text-amber-600 bg-amber-50 rounded-lg px-3 py-2">
              ⚠️ {w}
            </p>
          ))}
        </div>
      )}

      <div>
        <h3 className="text-sm font-semibold text-slate-700 mb-2">클래스별 확률</h3>
        <div className="space-y-2">
          {sortedProbs.map(([code, prob]) => (
            <div key={code}>
              <div className="flex justify-between text-xs text-slate-500 mb-0.5">
                <span>{CLASS_LABELS_KO[code]}</span>
                <span>{(prob * 100).toFixed(1)}%</span>
              </div>
              <div className="w-full h-1.5 rounded-full bg-slate-100 overflow-hidden">
                <div className={`h-full ${style.bar}`} style={{ width: `${prob * 100}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      <p className="text-sm text-slate-600">{result.guidance}</p>

      <div className="flex flex-wrap gap-3">
        {result.risk_level === "high" && (
          <button
            onClick={findNearbyDermatology}
            className="bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg px-4 py-2 transition"
          >
            내 주변 피부과 찾기
          </button>
        )}
        <button
          onClick={onDownloadReport}
          disabled={reportStatus === "loading"}
          className="bg-slate-100 hover:bg-slate-200 disabled:opacity-50 text-slate-700 text-sm font-medium rounded-lg px-4 py-2 transition"
        >
          {reportStatus === "loading" ? "리포트 생성 중..." : "PDF 리포트 다운로드"}
        </button>
      </div>
    </section>
  );
}
