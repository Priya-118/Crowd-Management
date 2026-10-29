import React from "react";

export default function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  accent = "teal",
  loading = false,
}) {
  const accentClasses = {
    teal: {
      bg: "bg-teal-50",
      border: "border-teal-200",
      text: "text-teal-700",
      iconBg: "bg-teal-100 text-teal-600",
    },
    emerald: {
      bg: "bg-emerald-50",
      border: "border-emerald-200",
      text: "text-emerald-700",
      iconBg: "bg-emerald-100 text-emerald-600",
    },
    blue: {
      bg: "bg-blue-50",
      border: "border-blue-200",
      text: "text-blue-700",
      iconBg: "bg-blue-100 text-blue-600",
    },
    amber: {
      bg: "bg-amber-50",
      border: "border-amber-200",
      text: "text-amber-700",
      iconBg: "bg-amber-100 text-amber-600",
    },
    slate: {
      bg: "bg-slate-50",
      border: "border-slate-200",
      text: "text-slate-700",
      iconBg: "bg-slate-100 text-slate-600",
    },
  }[accent] || {
    bg: "bg-teal-50",
    border: "border-teal-200",
    text: "text-teal-700",
    iconBg: "bg-teal-100 text-teal-600",
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
          {title}
        </span>
        {Icon && (
          <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${accentClasses.iconBg}`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      <div className="mt-3">
        {loading ? (
          <div className="h-8 w-24 bg-slate-200 rounded animate-pulse"></div>
        ) : (
          <div className="text-3xl font-extrabold text-slate-800 tracking-tight">
            {value !== undefined && value !== null ? value : "--"}
          </div>
        )}
      </div>

      {subtitle && (
        <p className="mt-1 text-xs text-slate-500 font-medium">{subtitle}</p>
      )}
    </div>
  );
}
