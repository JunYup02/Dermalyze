export default function UploadPanel({ previewUrl, onFileChange, onAnalyze, status }) {
  return (
    <section className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-4">
      <label className="block">
        <span className="text-sm font-semibold text-slate-700">피부 병변 사진 업로드</span>
        <input
          type="file"
          accept="image/*"
          capture="environment"
          onChange={(e) => onFileChange(e.target.files?.[0] ?? null)}
          className="mt-2 block w-full text-sm text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-indigo-50 file:text-indigo-700 file:font-medium hover:file:bg-indigo-100"
        />
      </label>

      {previewUrl && (
        <img
          src={previewUrl}
          alt="업로드한 병변 미리보기"
          className="max-h-72 rounded-lg border border-slate-200 object-contain mx-auto"
        />
      )}

      {status === "error" && (
        <p className="text-sm text-red-600">분석 요청 중 오류가 발생했습니다. 다시 시도해주세요.</p>
      )}

      <button
        onClick={onAnalyze}
        disabled={!previewUrl || status === "loading"}
        className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-semibold rounded-lg py-3 transition"
      >
        {status === "loading" ? "분석 중..." : "분석하기"}
      </button>
    </section>
  );
}
