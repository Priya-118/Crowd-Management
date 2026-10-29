import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { ArrowLeftRight, Info } from "lucide-react";

export default function FlowMetricsChart({ timeseriesData = [], loading = false }) {
  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
        <div className="h-6 w-48 bg-slate-200 rounded animate-pulse mb-4"></div>
        <div className="h-56 bg-slate-100 rounded-lg animate-pulse"></div>
      </div>
    );
  }

  const chartData = timeseriesData.map((d) => ({
    frame: `F${d.frame}`,
    inflow: d.total_inflow || 0,
    outflow: d.total_outflow || 0,
    net_flow: d.net_flow || 0,
  }));

  const hasFlowEvents = chartData.some((d) => d.inflow > 0 || d.outflow > 0);

  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
            <ArrowLeftRight className="w-4 h-4 text-brand-blue" />
            Inflow vs Outflow Dynamics
          </h3>
          <p className="text-xs text-slate-500">Zone transition rates and directional crowd currents</p>
        </div>
        <span className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
          Flow Analysis
        </span>
      </div>

      {!hasFlowEvents ? (
        <div className="h-56 flex flex-col items-center justify-center bg-slate-50 rounded-lg border border-dashed border-slate-200 p-4 text-center">
          <Info className="w-6 h-6 text-slate-400 mb-2" />
          <p className="text-xs font-semibold text-slate-700">No Zone Transitions Detected</p>
          <p className="text-[11px] text-slate-500 max-w-xs mt-1">
            People remained within their initial quadrants during this sequence, resulting in 0 net inter-zone transitions.
          </p>
        </div>
      ) : (
        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="frame" tick={{ fontSize: 11, fill: "#64748b" }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: "#64748b" }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0f172a",
                  borderColor: "#1e293b",
                  borderRadius: "8px",
                  color: "#fff",
                  fontSize: "12px",
                }}
              />
              <Legend wrapperStyle={{ fontSize: "12px" }} />
              <Bar dataKey="inflow" name="Inflow (Entering Zone)" fill="#10b981" radius={[4, 4, 0, 0]} />
              <Bar dataKey="outflow" name="Outflow (Leaving Zone)" fill="#f43f5e" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
