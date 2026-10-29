import { RefreshCw, AlertCircle, CheckCircle2, Clock } from "lucide-react";

export default function Topbar({
  title,
  subtitle,
  backendOnline,
  selectedRun,
  onRefresh,
  isRefreshing,
}) {
  const getStatusBadge = (status) => {
    switch (status) {
      case "completed":
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">Completed</span>;
      case "processing":
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-blue-100 text-blue-800 border border-blue-300 animate-pulse">Processing</span>;
      case "queued":
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-amber-100 text-amber-800 border border-amber-300">Queued</span>;
      case "failed":
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-rose-100 text-rose-800 border border-rose-300">Failed</span>;
      case "uploaded":
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-700 border border-slate-300">Uploaded</span>;
      default:
        return null;
    }
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between sticky top-0 z-20 shadow-xs">
      {/* Title & Context */}
      <div>
        <h2 className="text-lg font-bold text-slate-800">{title}</h2>
        <p className="text-xs text-slate-500 font-medium">{subtitle}</p>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-4">
        {/* Active Run Indicator */}
        {selectedRun ? (
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs">
            <span className="text-slate-500 font-medium">Selected Run:</span>
            <span className="font-semibold text-slate-700 font-mono" title={selectedRun.id}>
              {selectedRun.original_filename} ({selectedRun.id.slice(0, 8)}...)
            </span>
            {getStatusBadge(selectedRun.status)}
          </div>
        ) : (
          <div className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-400">
            <Clock className="w-3.5 h-3.5" />
            No run selected
          </div>
        )}

        {/* Backend Status Indicator */}
        <div
          className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${
            backendOnline
              ? "bg-emerald-50 text-emerald-700 border-emerald-200"
              : "bg-rose-50 text-rose-700 border-rose-200"
          }`}
        >
          {backendOnline ? (
            <>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
              <span>FastAPI Connected</span>
            </>
          ) : (
            <>
              <AlertCircle className="w-3.5 h-3.5 text-rose-500" />
              <span>FastAPI Offline</span>
            </>
          )}
        </div>

        {/* Refresh Action */}
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 active:bg-slate-200 text-slate-600 text-xs font-medium transition cursor-pointer disabled:opacity-50"
          title="Refresh runs and metrics"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin text-teal-600" : ""}`} />
          <span className="hidden sm:inline">Refresh</span>
        </button>
      </div>
    </header>
  );
}
