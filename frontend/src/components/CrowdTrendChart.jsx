import React, { useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  LineChart,
  Line,
} from "recharts";
import { TrendingUp } from "lucide-react";

export default function CrowdTrendChart({ timeseriesData = [], loading = false }) {
  const [viewMode, setViewMode] = useState("occupancy"); // "occupancy" or "zones"

  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
        <div className="h-6 w-48 bg-slate-200 rounded animate-pulse mb-4"></div>
        <div className="h-72 bg-slate-100 rounded-lg animate-pulse"></div>
      </div>
    );
  }

  if (!timeseriesData || timeseriesData.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200/80 p-8 shadow-xs text-center flex flex-col items-center justify-center min-h-[320px]">
        <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-slate-400 mb-3">
          <TrendingUp className="w-6 h-6" />
        </div>
        <h4 className="text-sm font-bold text-slate-700">No Time-Series Data Available</h4>
        <p className="text-xs text-slate-500 max-w-sm mt-1">
          Process a video or run the sample CSV detection test to visualize frame-by-frame crowd dynamics.
        </p>
      </div>
    );
  }

  // Format data for chart
  const chartData = timeseriesData.map((d) => ({
    frame: `F${d.frame}`,
    rawFrame: d.frame,
    total_people: d.total_people,
    moving_people: d.moving_people,
    stationary_people: Math.max(0, d.total_people - d.moving_people),
    movement_pct: d.movement_percentage,
    Zone_A: d.zones?.Zone_A || 0,
    Zone_B: d.zones?.Zone_B || 0,
    Zone_C: d.zones?.Zone_C || 0,
    Zone_D: d.zones?.Zone_D || 0,
  }));

  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
        <div>
          <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-teal-600" />
            Crowd Dynamics Over Time
          </h3>
          <p className="text-xs text-slate-500">Frame-by-frame people count and movement activity</p>
        </div>

        {/* View Toggle */}
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg text-xs font-semibold">
          <button
            onClick={() => setViewMode("occupancy")}
            className={`px-3 py-1 rounded-md transition ${
              viewMode === "occupancy"
                ? "bg-white text-teal-700 shadow-2xs font-bold"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Occupancy & Motion
          </button>
          <button
            onClick={() => setViewMode("zones")}
            className={`px-3 py-1 rounded-md transition ${
              viewMode === "zones"
                ? "bg-white text-teal-700 shadow-2xs font-bold"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Zone Breakdown
          </button>
        </div>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          {viewMode === "occupancy" ? (
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="totalGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0d9488" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#0d9488" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="movingGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#2563eb" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#2563eb" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="frame" tick={{ fontSize: 11, fill: "#64748b" }} axisLine={{ stroke: "#e2e8f0" }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: "#64748b" }} axisLine={{ stroke: "#e2e8f0" }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0f172a",
                  borderColor: "#1e293b",
                  borderRadius: "8px",
                  color: "#fff",
                  fontSize: "12px",
                }}
              />
              <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "10px" }} />
              <Area
                type="monotone"
                dataKey="total_people"
                name="Total Observed People"
                stroke="#0d9488"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#totalGrad)"
              />
              <Area
                type="monotone"
                dataKey="moving_people"
                name="Moving People"
                stroke="#2563eb"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#movingGrad)"
              />
            </AreaChart>
          ) : (
            <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="frame" tick={{ fontSize: 11, fill: "#64748b" }} axisLine={{ stroke: "#e2e8f0" }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: "#64748b" }} axisLine={{ stroke: "#e2e8f0" }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0f172a",
                  borderColor: "#1e293b",
                  borderRadius: "8px",
                  color: "#fff",
                  fontSize: "12px",
                }}
              />
              <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "10px" }} />
              <Line type="monotone" dataKey="Zone_A" stroke="#0284c7" strokeWidth={2} name="Zone A (NW)" dot={{ r: 3 }} />
              <Line type="monotone" dataKey="Zone_B" stroke="#0d9488" strokeWidth={2} name="Zone B (NE)" dot={{ r: 3 }} />
              <Line type="monotone" dataKey="Zone_C" stroke="#10b981" strokeWidth={2} name="Zone C (SW)" dot={{ r: 3 }} />
              <Line type="monotone" dataKey="Zone_D" stroke="#6366f1" strokeWidth={2} name="Zone D (SE)" dot={{ r: 3 }} />
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>

      <div className="mt-2 text-right">
        <span className="text-[11px] text-slate-400">
          Showing {chartData.length} sequential frame observations
        </span>
      </div>
    </div>
  );
}
