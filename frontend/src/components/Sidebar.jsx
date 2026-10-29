import React from "react";
import {
  LayoutDashboard,
  Layers,
  BarChart3,
  Flame,
  Settings,
  Activity,
  FileSpreadsheet
} from "lucide-react";

export default function Sidebar({ currentView, setCurrentView, onCreateSample, isCreatingSample }) {
  const navItems = [
    { id: "overview", label: "Overview", icon: LayoutDashboard },
    { id: "runs", label: "Analysis Runs", icon: Layers },
    { id: "analytics", label: "Crowd Analytics", icon: BarChart3 },
    { id: "heatmap", label: "Heatmap", icon: Flame },
    { id: "settings", label: "Settings", icon: Settings },
  ];

  return (
    <aside className="w-64 bg-navy-950 text-slate-300 flex flex-col justify-between border-r border-navy-800 select-none flex-shrink-0 min-h-screen">
      {/* Top Header & Branding */}
      <div>
        <div className="p-5 border-b border-navy-800 flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-tr from-brand-teal to-brand-emerald flex items-center justify-center text-white shadow-lg shadow-teal-900/40">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-white font-bold text-lg tracking-wide flex items-center gap-1.5">
              CrowdAhead
            </h1>
            <p className="text-xs text-teal-400 font-medium">Railway Crowd Intelligence</p>
          </div>
        </div>

        {/* Phase Pill */}
        <div className="mx-4 mt-4 p-2.5 rounded-lg bg-navy-900/80 border border-teal-500/20 text-xs">
          <div className="flex items-center gap-1.5 text-teal-300 font-semibold mb-1">
            <span className="w-2 h-2 rounded-full bg-teal-400 animate-pulse"></span>
            Semester 1 Active
          </div>
          <p className="text-slate-400 text-[11px] leading-tight">
            Current crowd detection, tracking & zone analysis.
          </p>
        </div>

        {/* Navigation Items */}
        <nav className="mt-5 px-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = currentView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentView(item.id)}
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  active
                    ? "bg-teal-500/15 text-teal-300 border-l-4 border-teal-400 font-semibold"
                    : "text-slate-400 hover:text-slate-100 hover:bg-navy-900/60"
                }`}
              >
                <Icon className={`w-4 h-4 ${active ? "text-teal-400" : "text-slate-400"}`} />
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* Quick Test Action */}
        <div className="mt-6 px-4">
          <button
            onClick={onCreateSample}
            disabled={isCreatingSample}
            className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg bg-teal-600 hover:bg-teal-500 disabled:opacity-50 text-white text-xs font-semibold shadow-md transition-all cursor-pointer"
          >
            <FileSpreadsheet className="w-4 h-4" />
            {isCreatingSample ? "Running Test..." : "Run Sample CSV Test"}
          </button>
        </div>
      </div>

      {/* Footer Info */}
      <div className="p-4 border-t border-navy-800 text-xs text-slate-400 space-y-1">
        <div className="flex items-center justify-between text-[11px]">
          <span>Role: Member 4</span>
          <span className="text-teal-400 font-medium">Backend & UI</span>
        </div>
        <p className="text-[10px] text-slate-500">
          ByteTrack + 4-Zone Flow Analysis
        </p>
      </div>
    </aside>
  );
}
