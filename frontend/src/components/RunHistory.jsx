import { useState } from "react";
import {
  Layers,
  Play,
  Trash2,
  Clock,
  FileVideo,
  FileSpreadsheet,
  Loader2
} from "lucide-react";

export default function RunHistory({
  runs = [],
  selectedRun,
  onSelectRun,
  onProcessRun,
  onDeleteRun,
  onCreateSample,
  isProcessingId,
  loading = false,
}) {
  const [filter, setFilter] = useState("all");

  const filteredRuns = runs.filter((r) => {
    if (filter === "all") return true;
    return r.status === filter;
  });

  const getStatusBadge = (status) => {
    switch (status) {
      case "completed":
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">Completed</span>;
      case "processing":
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-blue-100 text-blue-800 border border-blue-200 animate-pulse flex items-center gap-1"><Loader2 className="w-3 h-3 animate-spin"/> Processing</span>;
      case "queued":
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-amber-100 text-amber-800 border border-amber-200">Queued</span>;
      case "failed":
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-rose-100 text-rose-800 border border-rose-200">Failed</span>;
      case "uploaded":
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-700 border border-slate-200">Uploaded</span>;
      default:
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-600">{status}</span>;
    }
  };

  const formatDate = (isoString) => {
    if (!isoString) return "--";
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }) + " (" + d.toLocaleDateString() + ")";
    } catch {
      return isoString;
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
            <Layers className="w-4 h-4 text-teal-600" />
            Analysis Run History ({runs.length})
          </h3>
          <p className="text-xs text-slate-500">Select an execution to display analytics, zones, and heatmaps</p>
        </div>

        {/* Status Filters */}
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg text-xs font-semibold">
          {["all", "completed", "uploaded", "failed"].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-2.5 py-1 rounded-md capitalize transition ${
                filter === f
                  ? "bg-white text-slate-900 shadow-2xs font-bold"
                  : "text-slate-500 hover:text-slate-900"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 bg-slate-100 rounded-lg animate-pulse"></div>
          ))}
        </div>
      ) : filteredRuns.length === 0 ? (
        <div className="p-8 text-center flex flex-col items-center justify-center bg-slate-50/70 rounded-xl border border-dashed border-slate-200">
          <Clock className="w-8 h-8 text-slate-400 mb-2" />
          <p className="text-xs font-bold text-slate-700">No Analysis Runs Found</p>
          <p className="text-[11px] text-slate-500 max-w-xs mt-1 mb-3">
            Get started by running the repository's sample detection CSV or uploading your own file.
          </p>
          <button
            onClick={onCreateSample}
            className="px-3.5 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-500 text-white text-xs font-semibold shadow-xs transition cursor-pointer"
          >
            Create Sample CSV Run
          </button>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-slate-400 font-semibold uppercase text-[10px] tracking-wider">
                <th className="pb-2.5">Input & File</th>
                <th className="pb-2.5">Status</th>
                <th className="pb-2.5">Frames / Stats</th>
                <th className="pb-2.5">Created At</th>
                <th className="pb-2.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredRuns.map((run) => {
                const isSelected = selectedRun?.id === run.id;
                const isProcessing = isProcessingId === run.id || run.status === "processing";

                return (
                  <tr
                    key={run.id}
                    onClick={() => onSelectRun(run)}
                    className={`cursor-pointer transition-colors ${
                      isSelected
                        ? "bg-teal-50/70 hover:bg-teal-50"
                        : "hover:bg-slate-50"
                    }`}
                  >
                    <td className="py-3">
                      <div className="flex items-center gap-2.5">
                        <div
                          className={`w-7 h-7 rounded-lg flex items-center justify-center ${
                            run.input_type === "video"
                              ? "bg-purple-100 text-purple-700"
                              : "bg-teal-100 text-teal-700"
                          }`}
                        >
                          {run.input_type === "video" ? (
                            <FileVideo className="w-3.5 h-3.5" />
                          ) : (
                            <FileSpreadsheet className="w-3.5 h-3.5" />
                          )}
                        </div>
                        <div>
                          <div className="font-bold text-slate-800 flex items-center gap-1.5">
                            {run.original_filename}
                            {isSelected && (
                              <span className="text-[10px] bg-teal-600 text-white px-1.5 py-0.2 rounded font-semibold">
                                Active
                              </span>
                            )}
                          </div>
                          <div className="text-[10px] font-mono text-slate-400">
                            {run.id.slice(0, 8)}...
                          </div>
                        </div>
                      </div>
                    </td>

                    <td className="py-3">
                      {getStatusBadge(run.status)}
                      {run.error_details && (
                        <p className="text-[10px] text-rose-600 max-w-xs truncate mt-0.5" title={run.error_details}>
                          {run.error_details}
                        </p>
                      )}
                    </td>

                    <td className="py-3">
                      {run.status === "completed" ? (
                        <div className="text-[11px] text-slate-600">
                          <span className="font-bold text-slate-800">{run.total_frames}</span> frames • Peak:{" "}
                          <span className="font-bold text-slate-800">{run.peak_crowd_count}</span>
                        </div>
                      ) : (
                        <span className="text-slate-400 text-[11px]">--</span>
                      )}
                    </td>

                    <td className="py-3 text-slate-500 text-[11px]">
                      {formatDate(run.created_at)}
                    </td>

                    <td className="py-3 text-right">
                      <div className="flex items-center justify-end gap-1.5" onClick={(e) => e.stopPropagation()}>
                        {run.status !== "completed" && run.status !== "processing" && (
                          <button
                            onClick={() => onProcessRun(run.id)}
                            disabled={isProcessing}
                            title="Run Tracking & Flow Pipeline"
                            className="p-1.5 rounded-md bg-teal-50 hover:bg-teal-100 text-teal-700 border border-teal-200 transition cursor-pointer disabled:opacity-50"
                          >
                            {isProcessing ? (
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            ) : (
                              <Play className="w-3.5 h-3.5" />
                            )}
                          </button>
                        )}

                        <button
                          onClick={() => onDeleteRun(run.id)}
                          title="Delete Run"
                          className="p-1.5 rounded-md hover:bg-rose-50 text-slate-400 hover:text-rose-600 transition cursor-pointer"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
