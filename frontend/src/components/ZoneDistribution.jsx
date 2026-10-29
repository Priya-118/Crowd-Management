import { Compass } from "lucide-react";

export default function ZoneDistribution({ zoneData, latestFrameZones, totalPeople = 0, loading = false }) {
  // Use latest frame zones if provided, fallback to summary zone_totals
  const counts = latestFrameZones || zoneData || { Zone_A: 0, Zone_B: 0, Zone_C: 0, Zone_D: 0 };
  const total = totalPeople || (Object.values(counts).reduce((a, b) => a + b, 0) || 1);

  const getPercentage = (count) => {
    if (!total || total === 0) return 0;
    return Math.round((count / total) * 100);
  };

  const zones = [
    {
      id: "Zone_A",
      name: "Zone A (Top-Left)",
      count: counts.Zone_A || 0,
      color: "border-sky-300 bg-sky-50/70 text-sky-800",
      badgeColor: "bg-sky-500",
      description: "North-West Quad (Concourse)",
    },
    {
      id: "Zone_B",
      name: "Zone B (Top-Right)",
      count: counts.Zone_B || 0,
      color: "border-teal-300 bg-teal-50/70 text-teal-800",
      badgeColor: "bg-teal-500",
      description: "North-East Quad (Platform Entry)",
    },
    {
      id: "Zone_C",
      name: "Zone C (Bottom-Left)",
      count: counts.Zone_C || 0,
      color: "border-emerald-300 bg-emerald-50/70 text-emerald-800",
      badgeColor: "bg-emerald-500",
      description: "South-West Quad (Exit Gate)",
    },
    {
      id: "Zone_D",
      name: "Zone D (Bottom-Right)",
      count: counts.Zone_D || 0,
      color: "border-indigo-300 bg-indigo-50/70 text-indigo-800",
      badgeColor: "bg-indigo-500",
      description: "South-East Quad (Escalator / Ramp)",
    },
  ];

  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
            <Compass className="w-4 h-4 text-teal-600" />
            4-Zone Scene Distribution
          </h3>
          <p className="text-xs text-slate-500">Spatial crowd allocation across monitored quadrants</p>
        </div>
        <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-600">
          Midpoint Split
        </span>
      </div>

      {loading ? (
        <div className="grid grid-cols-2 gap-3.5 h-48 animate-pulse">
          <div className="bg-slate-100 rounded-lg"></div>
          <div className="bg-slate-100 rounded-lg"></div>
          <div className="bg-slate-100 rounded-lg"></div>
          <div className="bg-slate-100 rounded-lg"></div>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3.5">
          {zones.map((zone) => {
            const pct = getPercentage(zone.count);
            return (
              <div
                key={zone.id}
                className={`p-4 rounded-xl border ${zone.color} flex flex-col justify-between transition-all hover:shadow-sm`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`w-2.5 h-2.5 rounded-full ${zone.badgeColor}`}></span>
                    <span className="font-bold text-xs uppercase tracking-wider">{zone.id.replace("_", " ")}</span>
                  </div>
                  <span className="text-xs font-bold bg-white/80 px-2 py-0.5 rounded-md text-slate-700 shadow-2xs">
                    {pct}%
                  </span>
                </div>

                <div className="my-2.5">
                  <div className="text-2xl font-black">{zone.count}</div>
                  <div className="text-[11px] opacity-80">{zone.description}</div>
                </div>

                {/* Mini progress bar */}
                <div className="w-full bg-black/10 rounded-full h-1.5 overflow-hidden">
                  <div
                    className={`h-full ${zone.badgeColor}`}
                    style={{ width: `${Math.min(pct, 100)}%` }}
                  ></div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
        <span>Coordinate boundaries: cx &lt; W/2, cy &lt; H/2</span>
        <span>Resolution: 832 × 464</span>
      </div>
    </div>
  );
}
