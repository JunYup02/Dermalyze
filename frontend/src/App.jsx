import { useState } from "react";
import UploadPanel from "./components/UploadPanel";
import ResultPanel from "./components/ResultPanel";
import { analyzeImage, downloadReport } from "./api";

export default function App() {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | loading | error
  const [reportStatus, setReportStatus] = useState("idle");

  const handleFileChange = (selected) => {
    setFile(selected);
    setResult(null);
    setPreviewUrl(selected ? URL.createObjectURL(selected) : null);
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setStatus("loading");
    try {
      const data = await analyzeImage(file);
      setResult(data);
      setStatus("idle");
    } catch {
      setStatus("error");
    }
  };

  const handleDownloadReport = async () => {
    if (!file) return;
    setReportStatus("loading");
    try {
      const blob = await downloadReport(file);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "skin-analysis-report.pdf";
      a.click();
      URL.revokeObjectURL(url);
      setReportStatus("idle");
    } catch {
      setReportStatus("error");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-2xl mx-auto px-4 py-6">
          <h1 className="text-2xl font-bold text-slate-900">🩺 Skin Cancer Detector (Demo)</h1>
          <p className="text-sm text-slate-500 mt-1">
            피부 병변 사진을 업로드하면 AI가 7가지 병변 유형 중 하나로 분류하고, 위험도에 따른 안내를 제공합니다.
          </p>
          <p className="text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2 mt-3 font-medium">
            ⚠️ 본 서비스는 데모용이며 실제 의료 진단이 아닙니다. 결과는 참고용으로만 사용하고,
            중요한 판단은 반드시 피부과 전문의와 상담하세요.
          </p>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-8 space-y-6">
        <UploadPanel
          previewUrl={previewUrl}
          onFileChange={handleFileChange}
          onAnalyze={handleAnalyze}
          status={status}
        />

        {result && (
          <ResultPanel result={result} onDownloadReport={handleDownloadReport} reportStatus={reportStatus} />
        )}
      </main>

      <footer className="max-w-2xl mx-auto px-4 pb-8 text-xs text-slate-400">
        본 서비스의 분류 모델은 합성 데이터로 학습된 데모 모델이며, 실제 임상 데이터로 검증되지 않았습니다.
        의학적 진단을 대체할 수 없습니다.
      </footer>
    </div>
  );
}
