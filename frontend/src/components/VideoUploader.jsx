import React, { useState, useRef } from "react";
import { UploadCloud, FileVideo, FileSpreadsheet, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { api } from "../services/api";

export default function VideoUploader({ onRunCreated }) {
  const [activeMode, setActiveMode] = useState("video"); // "video" or "csv"
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errorMsg, setErrorMsg] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    await processFile(file);
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (!file) return;
    await processFile(file);
  };

  const processFile = async (file) => {
    setIsUploading(true);
    setUploadProgress(0);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      if (activeMode === "video") {
        const run = await api.uploadVideo(file, (progressEvent) => {
          const percent = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1));
          setUploadProgress(percent);
        });
        setSuccessMsg(`Video "${file.name}" uploaded successfully (Run ID: ${run.id.slice(0, 8)}).`);
        if (onRunCreated) onRunCreated(run);
      } else {
        const run = await api.uploadCustomCsv(file, false);
        setSuccessMsg(`Detection CSV "${file.name}" validated and registered.`);
        if (onRunCreated) onRunCreated(run);
      }
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || "Upload failed. Please check the file format.";
      setErrorMsg(msg);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
            <UploadCloud className="w-4 h-4 text-teal-600" />
            Ingest & Run Pipeline
          </h3>
          <p className="text-xs text-slate-500">Upload recorded CCTV footage or detection coordinates</p>
        </div>

        {/* Upload Mode Selector */}
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg text-xs font-semibold">
          <button
            onClick={() => { setActiveMode("video"); setErrorMsg(null); setSuccessMsg(null); }}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md transition ${
              activeMode === "video"
                ? "bg-white text-teal-700 shadow-2xs font-bold"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <FileVideo className="w-3.5 h-3.5" />
            Video File
          </button>
          <button
            onClick={() => { setActiveMode("csv"); setErrorMsg(null); setSuccessMsg(null); }}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md transition ${
              activeMode === "csv"
                ? "bg-white text-teal-700 shadow-2xs font-bold"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <FileSpreadsheet className="w-3.5 h-3.5" />
            Custom CSV
          </button>
        </div>
      </div>

      {/* Drag & Drop Area */}
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className="border-2 border-dashed border-slate-200 hover:border-teal-400 bg-slate-50/60 hover:bg-teal-50/20 rounded-xl p-6 text-center cursor-pointer transition-all flex flex-col items-center justify-center min-h-[140px]"
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={activeMode === "video" ? ".mp4,.avi,.mov,.mkv" : ".csv"}
          onChange={handleFileChange}
          className="hidden"
        />

        {isUploading ? (
          <div className="w-full max-w-xs flex flex-col items-center gap-2">
            <Loader2 className="w-8 h-8 text-teal-600 animate-spin" />
            <p className="text-xs font-semibold text-slate-700">Uploading {uploadProgress}%...</p>
            <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
              <div
                className="bg-teal-500 h-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
          </div>
        ) : (
          <>
            <div className="w-10 h-10 rounded-full bg-teal-100/70 text-teal-600 flex items-center justify-center mb-2">
              <UploadCloud className="w-5 h-5" />
            </div>
            <p className="text-xs font-bold text-slate-700">
              Drag & Drop your {activeMode === "video" ? "crowd video" : "detections CSV"} here
            </p>
            <p className="text-[11px] text-slate-400 mt-1">
              or <span className="text-teal-600 underline font-medium">browse local files</span> (Max 100 MB)
            </p>
            <p className="text-[10px] text-slate-400 mt-0.5">
              Supported: {activeMode === "video" ? ".mp4, .avi, .mov, .mkv" : "CSV columns: frame, x1, y1, x2, y2, confidence"}
            </p>
          </>
        )}
      </div>

      {/* Messages */}
      {successMsg && (
        <div className="mt-3 p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div className="mt-3 p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}
    </div>
  );
}
