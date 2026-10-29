import React, { useState } from "react";
import { Flame, Image as ImageIcon, Grid, AlertTriangle, Crosshair } from "lucide-react";
import { api } from "../services/api";

export default function HeatmapPanel({ heatmapData, selectedRun, loading = false }) {
  const [activeTab, setActiveTab] = useState("image"); // "image" or "grid"
  const [imageError, setImageError] = useState(false);

  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-xs animate-pulse">
        <div className="h-6 w-48 bg-slate-200 rounded mb-4"></div>
        <div className="h-80 bg-slate-100 rounded-lg"></div>
      </div>
    );
  }

  if (!selectedRun) {
    return (
      <div className="bg-white rounded-xl border border-slate-200/80 p-12 text-center flex flex-col items-center justify-center min-h-[360px]">
        <div className="w-14 h-14 rounded-full bg-slate-100 flex items-center justify-center text-slate-400 mb-3">
          <Flame className="w-7 h-7" />
        </div>
        <h4 className="text-sm font-bold text-slate-700">No Run Selected</h4>
        <p className="text-xs text-slate-500 max-w-sm mt-1">
          Select or process a run to inspect accumulated spatial crowd density heatmaps.
        </p>
      </div>
    );
  }

  if (!heatmapData || heatmapData.status !== "available") {
    return (
      <div className="bg-white rounded-xl border border-slate-200/80 p-8 shadow-xs text-center flex flex-col items-center justify-center min-h-[360px]">
        <div className="w-12 h-12 rounded-full bg-amber-50 text-amber-500 flex items-center justify-center mb-3 border border-amber-200">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <h4 className="text-sm font-bold text-slate-700">Heatmap Data Unavailable</h4>
        <p className="text-xs text-slate-500 max-w-md mt-1">
          {heatmapData?.message ||
            "Heatmap data is only generated after pipeline processing finishes with valid tracking centroids."}
        </p>
      </div>
    );
  }

  const imageUrl = api.getHeatmapImageUrl(selectedRun.id);

  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
        <div>
          <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
            <Flame className="w-4 h-4 text-orange-500" />
            Accumulated Spatial Density Heatmap
          </h3>
          <p className="text-xs text-slate-500">2D Gaussian Kernel Density Estimation (KDE) over tracked coordinates</p>
        </div>

        {/* View Switcher */}
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg text-xs font-semibold">
          <button
            onClick={() => setActiveTab("image")}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md transition ${
              activeTab === "image"
                ? "bg-white text-orange-600 shadow-2xs font-bold"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <ImageIcon className="w-3.5 h-3.5" />
            Visual Heatmap
          </button>
          <button
            onClick={() => setActiveTab("grid")}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md transition ${
              activeTab === "grid"
                ? "bg-white text-orange-600 shadow-2xs font-bold"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Grid className="w-3.5 h-3.5" />
            Density Matrix
          </button>
        </div>
      </div>

      {/* Main Heatmap Visual */}
      <div className="bg-slate-950 rounded-xl overflow-hidden border border-slate-800 flex items-center justify-center min-h-[320px] p-2">
        {activeTab === "image" && !imageError ? (
          <img
            src={imageUrl}
            alt="Crowd Density Heatmap"
            onError={() => setImageError(true)}
            className="max-h-[420px] w-auto object-contain rounded-lg shadow-lg"
          />
        ) : (
          <div className="w-full overflow-x-auto p-4 flex flex-col items-center">
            <p className="text-xs text-slate-400 mb-3">
              Normalized Density Matrix ({heatmapData.grid_width} × {heatmapData.grid_height} grid cells)
            </p>
            <div
              className="grid gap-[2px] bg-slate-900 p-2 rounded-lg border border-slate-800"
              style={{
                gridTemplateColumns: `repeat(${heatmapData.grid_width || 40}, minmax(6px, 1fr))`,
              }}
            >
              {heatmapData.density_grid?.map((row, rIdx) =>
                row.map((val, cIdx) => {
                  const opacity = Math.min(Math.max(val, 0.05), 1);
                  return (
                    <div
                      key={`${rIdx}-${cIdx}`}
                      title={`Cell [${rIdx}, ${cIdx}]: Density ${val}`}
                      className="w-2.5 h-2.5 rounded-[1px] transition-transform hover:scale-150"
                      style={{
                        backgroundColor: val > 0.1 ? `rgba(249, 115, 22, ${opacity})` : "rgba(30, 41, 59, 0.5)",
                      }}
                    ></div>
                  );
                })
              )}
            </div>
          </div>
        )}
      </div>

      {/* Hotspots Section */}
      {heatmapData.hotspots && heatmapData.hotspots.length > 0 && (
        <div className="mt-5 pt-4 border-t border-slate-100">
          <h4 className="text-xs font-bold text-slate-700 flex items-center gap-1.5 mb-2.5">
            <Crosshair className="w-3.5 h-3.5 text-orange-500" />
            Detected Density Hotspots (Cluster Centroids)
          </h4>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2.5">
            {heatmapData.hotspots.map((hp, idx) => (
              <div
                key={idx}
                className="p-2.5 rounded-lg bg-orange-50/60 border border-orange-200/80 text-xs flex flex-col justify-between"
              >
                <div className="flex items-center justify-between font-bold text-orange-900">
                  <span>Hotspot #{idx + 1}</span>
                  <span className="text-[10px] bg-orange-200/60 px-1.5 py-0.5 rounded text-orange-800">
                    {(hp.intensity * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="mt-1 text-[11px] text-slate-600 font-mono">
                  X: {hp.cx}px, Y: {hp.cy}px
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Note */}
      <div className="mt-4 p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-500 leading-relaxed">
        <strong>Technical Note:</strong> Spatial crowd heatmaps reflect 2D Gaussian density estimation computed directly
        from persistent centroid positions. Calibrated physical density (people/m²) will be integrated in Semester 2 with camera homography matrices.
      </div>
    </div>
  );
}
