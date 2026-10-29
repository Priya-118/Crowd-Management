import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  Users,
  Eye,
  TrendingUp,
  Activity,
  Layers,
  Settings as SettingsIcon,
  Server,
  AlertCircle,
  CheckCircle2,
  HelpCircle,
  ExternalLink,
  ShieldAlert
} from "lucide-react";

import { api } from "./services/api";
import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";
import StatCard from "./components/StatCard";
import ZoneDistribution from "./components/ZoneDistribution";
import CrowdTrendChart from "./components/CrowdTrendChart";
import FlowMetricsChart from "./components/FlowMetricsChart";
import HeatmapPanel from "./components/HeatmapPanel";
import VideoUploader from "./components/VideoUploader";
import RunHistory from "./components/RunHistory";
import VideoPlayerPanel from "./components/VideoPlayerPanel";

export default function App() {
  const [currentView, setCurrentView] = useState("overview");
  const [backendOnline, setBackendOnline] = useState(false);
  const [backendInfo, setBackendInfo] = useState(null);

  const [runs, setRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [timeseries, setTimeseries] = useState([]);
  const [heatmapData, setHeatmapData] = useState(null);

  const [isLoadingRuns, setIsLoadingRuns] = useState(false);
  const [isLoadingDetails, setIsLoadingDetails] = useState(false);
  const [isProcessingId, setIsProcessingId] = useState(null);
  const [isCreatingSample, setIsCreatingSample] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [notification, setNotification] = useState(null);

  const pollIntervalRef = useRef(null);

  // Show temporary toast notification
  const notify = (message, type = "info") => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 5000);
  };

  // 1. Check Backend Health
  const checkBackendHealth = useCallback(async () => {
    try {
      const data = await api.checkHealth();
      setBackendOnline(true);
      setBackendInfo(data);
      return true;
    } catch {
      setBackendOnline(false);
      setBackendInfo(null);
      return false;
    }
  }, []);

  // 2. Fetch Run List
  const fetchRuns = useCallback(async (selectFirst = false) => {
    setIsLoadingRuns(true);
    try {
      const res = await api.listRuns(0, 50);
      const fetchedRuns = res.runs || [];
      setRuns(fetchedRuns);

      if (selectFirst && fetchedRuns.length > 0) {
        setSelectedRun((prev) => prev || fetchedRuns[0]);
      } else if (fetchedRuns.length === 0) {
        setSelectedRun(null);
      }
    } catch {
      // Backend may be offline
    } finally {
      setIsLoadingRuns(false);
    }
  }, []);

  // 3. Fetch Details for Selected Run (Metrics, Timeseries, Heatmap)
  const fetchRunDetails = useCallback(async (run) => {
    if (!run || run.status !== "completed") {
      setMetrics(null);
      setTimeseries([]);
      setHeatmapData(null);
      return;
    }

    setIsLoadingDetails(true);
    try {
      const [m, ts, hm] = await Promise.allSettled([
        api.getRunMetrics(run.id),
        api.getRunTimeseries(run.id),
        api.getRunHeatmap(run.id),
      ]);

      if (m.status === "fulfilled") setMetrics(m.value);
      if (ts.status === "fulfilled") setTimeseries(ts.value.frames || []);
      if (hm.status === "fulfilled") setHeatmapData(hm.value);
    } catch (err) {
      console.error("Error fetching run details:", err);
    } finally {
      setIsLoadingDetails(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    let ignore = false;
    const init = async () => {
      const online = await checkBackendHealth();
      if (online && !ignore) {
        await fetchRuns(true);
      }
    };
    init();
    return () => {
      ignore = true;
    };
  }, [checkBackendHealth, fetchRuns]);

  // Load details when selectedRun changes
  useEffect(() => {
    let ignore = false;
    if (selectedRun && selectedRun.status === "completed") {
      setIsLoadingDetails(true);
      Promise.allSettled([
        api.getRunMetrics(selectedRun.id),
        api.getRunTimeseries(selectedRun.id),
        api.getRunHeatmap(selectedRun.id),
      ]).then(([m, ts, hm]) => {
        if (!ignore) {
          if (m.status === "fulfilled") setMetrics(m.value);
          if (ts.status === "fulfilled") setTimeseries(ts.value.frames || []);
          if (hm.status === "fulfilled") setHeatmapData(hm.value);
          setIsLoadingDetails(false);
        }
      });
    } else {
      setMetrics(null);
      setTimeseries([]);
      setHeatmapData(null);
    }
    return () => {
      ignore = true;
    };
  }, [selectedRun]);

  // Polling when a run is processing or queued
  useEffect(() => {
    const hasActiveJob = runs.some((r) => r.status === "processing" || r.status === "queued");

    if (hasActiveJob) {
      pollIntervalRef.current = setInterval(async () => {
        try {
          const res = await api.listRuns(0, 50);
          const updatedRuns = res.runs || [];
          setRuns(updatedRuns);

          if (selectedRun) {
            const updatedSelected = updatedRuns.find((r) => r.id === selectedRun.id);
            if (updatedSelected) {
              if (updatedSelected.status !== selectedRun.status) {
                setSelectedRun(updatedSelected);
                if (updatedSelected.status === "completed") {
                  fetchRunDetails(updatedSelected);
                  notify(`Pipeline run for ${updatedSelected.original_filename} completed!`, "success");
                }
              }
            }
          }
        } catch {
          // ignore transient poll error
        }
      }, 2500);
    } else {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    }

    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, [runs, selectedRun, fetchRunDetails]);

  // Actions
  const handleRefresh = async () => {
    setIsRefreshing(true);
    await checkBackendHealth();
    await fetchRuns(false);
    if (selectedRun) {
      try {
        const fresh = await api.getRun(selectedRun.id);
        setSelectedRun(fresh);
        await fetchRunDetails(fresh);
      } catch {
        // ignore
      }
    }
    setIsRefreshing(false);
    notify("Dashboard refreshed with latest backend data.", "info");
  };

  const handleSelectRun = (run) => {
    setSelectedRun(run);
  };

  const handleCreateSampleRun = async () => {
    setIsCreatingSample(true);
    try {
      // Create and automatically process the sample run synchronously for instant results
      const run = await api.createSampleCsvRun(false);
      notify(`Sample detection run created (${run.id.slice(0, 8)}). Starting pipeline...`, "info");

      setIsProcessingId(run.id);
      await api.processRun(run.id, true);
      const finishedRun = await api.getRun(run.id);

      await fetchRuns(false);
      setSelectedRun(finishedRun);
      await fetchRunDetails(finishedRun);
      notify(`Sample detection pipeline completed successfully!`, "success");
    } catch (err) {
      notify(`Failed to run sample test: ${err.message}`, "error");
    } finally {
      setIsCreatingSample(false);
      setIsProcessingId(null);
    }
  };

  const handleProcessRun = async (runId) => {
    setIsProcessingId(runId);
    try {
      notify("Tracking and flow pipeline queued...", "info");
      await api.processRun(runId, false);
      await fetchRuns(false);
      if (selectedRun && selectedRun.id === runId) {
        const fresh = await api.getRun(runId);
        setSelectedRun(fresh);
      }
    } catch (err) {
      notify(`Processing failed: ${err.response?.data?.detail || err.message}`, "error");
    } finally {
      setIsProcessingId(null);
    }
  };

  const handleDeleteRun = async (runId) => {
    try {
      await api.deleteRun(runId);
      notify("Run and associated outputs deleted.", "info");
      const res = await api.listRuns(0, 50);
      const remaining = res.runs || [];
      setRuns(remaining);
      if (selectedRun?.id === runId) {
        setSelectedRun(remaining.length > 0 ? remaining[0] : null);
      }
    } catch (err) {
      notify(`Delete failed: ${err.message}`, "error");
    }
  };

  const handleRunCreated = async (newRun) => {
    await fetchRuns(false);
    setSelectedRun(newRun);
    notify(`Registered ${newRun.original_filename}. You can now run the pipeline.`, "success");
  };

  // Derive latest frame data
  const latestFrame = timeseries.length > 0 ? timeseries[timeseries.length - 1] : null;
  const currentObservedCount = latestFrame ? latestFrame.total_people : (metrics?.peak_crowd_count ?? "--");
  const uniqueTracksCount = metrics?.total_unique_tracks ?? selectedRun?.total_unique_tracks ?? "--";
  const peakCount = metrics?.peak_crowd_count ?? selectedRun?.peak_crowd_count ?? "--";
  const avgMovementPct = metrics?.average_movement_percentage !== undefined ? `${metrics.average_movement_percentage}%` : "--";

  // Titles mapping
  const viewTitles = {
    overview: {
      title: "Crowd Intelligence Overview",
      subtitle: "Semester 1 — Person Detection, ByteTrack Tracking & Spatial Density",
    },
    runs: {
      title: "Analysis Runs & Pipelines",
      subtitle: "Manage video ingests, detection CSV tests, and execution history",
    },
    analytics: {
      title: "Crowd Analytics & Flow Dynamics",
      subtitle: "Frame-level time-series occupancy, movement percentage, and inflow/outflow",
    },
    heatmap: {
      title: "Accumulated Spatial Density Heatmap",
      subtitle: "2D Gaussian Kernel Density Estimation (KDE) over tracking centroids",
    },
    settings: {
      title: "System Configuration & Integration",
      subtitle: "API status, endpoints reference, and project roadmap",
    },
  };

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-800 font-sans">
      {/* Sidebar */}
      <Sidebar
        currentView={currentView}
        setCurrentView={setCurrentView}
        onCreateSample={handleCreateSampleRun}
        isCreatingSample={isCreatingSample}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        {/* Topbar */}
        <Topbar
          title={viewTitles[currentView]?.title || "Dashboard"}
          subtitle={viewTitles[currentView]?.subtitle || ""}
          backendOnline={backendOnline}
          selectedRun={selectedRun}
          onRefresh={handleRefresh}
          isRefreshing={isRefreshing}
        />

        {/* Global Toast Notification */}
        {notification && (
          <div className="fixed bottom-6 right-6 z-50 animate-bounce">
            <div
              className={`px-4 py-3 rounded-xl shadow-xl flex items-center gap-2.5 text-xs font-semibold border ${
                notification.type === "success"
                  ? "bg-emerald-900 text-emerald-100 border-emerald-700"
                  : notification.type === "error"
                  ? "bg-rose-900 text-rose-100 border-rose-700"
                  : "bg-slate-900 text-slate-100 border-slate-700"
              }`}
            >
              {notification.type === "success" && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
              {notification.type === "error" && <AlertCircle className="w-4 h-4 text-rose-400" />}
              {notification.type === "info" && <HelpCircle className="w-4 h-4 text-teal-400" />}
              <span>{notification.message}</span>
            </div>
          </div>
        )}

        {/* View Router */}
        <main className="p-6 max-w-7xl w-full mx-auto space-y-6">
          {/* Disconnected Notice if backend is offline */}
          {!backendOnline && (
            <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0" />
                <div>
                  <span className="font-bold">Backend Server Offline (http://127.0.0.1:8000).</span>
                  <span className="block text-amber-700 mt-0.5">
                    Start the FastAPI backend with:{" "}
                    <code className="bg-amber-100 px-1.5 py-0.5 rounded font-mono">
                      py -m uvicorn backend.app.main:app --port 8000
                    </code>
                  </span>
                </div>
              </div>
              <button
                onClick={handleRefresh}
                className="px-3 py-1.5 rounded-lg bg-amber-200 hover:bg-amber-300 font-bold transition text-amber-900 cursor-pointer"
              >
                Retry
              </button>
            </div>
          )}

          {/* VIEW: OVERVIEW */}
          {currentView === "overview" && (
            <>
              {/* KPI Cards Row */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                  title="Current Crowd Count"
                  value={currentObservedCount}
                  subtitle={latestFrame ? `At Frame #${latestFrame.frame}` : "Active people observed"}
                  icon={Users}
                  accent="teal"
                  loading={isLoadingDetails}
                />
                <StatCard
                  title="Unique Tracked IDs"
                  value={uniqueTracksCount}
                  subtitle="Persistent ByteTrack IDs"
                  icon={Activity}
                  accent="blue"
                  loading={isLoadingDetails}
                />
                <StatCard
                  title="Peak Observed Count"
                  value={peakCount}
                  subtitle="Maximum instantaneous density"
                  icon={TrendingUp}
                  accent="amber"
                  loading={isLoadingDetails}
                />
                <StatCard
                  title="Avg Movement Activity"
                  value={avgMovementPct}
                  subtitle="Mobile vs stationary ratio"
                  icon={Eye}
                  accent="emerald"
                  loading={isLoadingDetails}
                />
              </div>

              {/* Ingest and Quick Test Section */}
              <VideoUploader onRunCreated={handleRunCreated} onRunProcessed={handleRefresh} />

              {/* Middle Grid: 4-Zone Distribution & Crowd Trend Chart */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                <div className="lg:col-span-5">
                  <ZoneDistribution
                    zoneData={metrics?.zone_totals}
                    latestFrameZones={latestFrame?.zones}
                    totalPeople={latestFrame?.total_people || metrics?.peak_crowd_count}
                    loading={isLoadingDetails}
                  />
                </div>
                <div className="lg:col-span-7">
                  <CrowdTrendChart timeseriesData={timeseries} loading={isLoadingDetails} />
                </div>
              </div>

              {/* Flow Dynamics & Media Panel */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                <div className="lg:col-span-6">
                  <FlowMetricsChart timeseriesData={timeseries} loading={isLoadingDetails} />
                </div>
                <div className="lg:col-span-6">
                  <VideoPlayerPanel selectedRun={selectedRun} />
                </div>
              </div>

              {/* Heatmap Preview & Run History */}
              <HeatmapPanel heatmapData={heatmapData} selectedRun={selectedRun} loading={isLoadingDetails} />

              <RunHistory
                runs={runs}
                selectedRun={selectedRun}
                onSelectRun={handleSelectRun}
                onProcessRun={handleProcessRun}
                onDeleteRun={handleDeleteRun}
                onCreateSample={handleCreateSampleRun}
                isProcessingId={isProcessingId}
                loading={isLoadingRuns}
              />
            </>
          )}

          {/* VIEW: RUNS */}
          {currentView === "runs" && (
            <div className="space-y-6">
              <VideoUploader onRunCreated={handleRunCreated} onRunProcessed={handleRefresh} />
              <VideoPlayerPanel selectedRun={selectedRun} />
              <RunHistory
                runs={runs}
                selectedRun={selectedRun}
                onSelectRun={handleSelectRun}
                onProcessRun={handleProcessRun}
                onDeleteRun={handleDeleteRun}
                onCreateSample={handleCreateSampleRun}
                isProcessingId={isProcessingId}
                loading={isLoadingRuns}
              />
            </div>
          )}

          {/* VIEW: ANALYTICS */}
          {currentView === "analytics" && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                  title="Total Frames Analyzed"
                  value={metrics?.total_frames ?? selectedRun?.total_frames ?? "--"}
                  subtitle="Sequential frame count"
                  icon={Layers}
                  accent="slate"
                  loading={isLoadingDetails}
                />
                <StatCard
                  title="Average Crowd Size"
                  value={metrics?.average_crowd_count ?? selectedRun?.average_crowd_count ?? "--"}
                  subtitle="Mean observed persons"
                  icon={Users}
                  accent="teal"
                  loading={isLoadingDetails}
                />
                <StatCard
                  title="Total Inflow Events"
                  value={metrics?.total_inflow ?? "--"}
                  subtitle="Aggregated entries into zones"
                  icon={TrendingUp}
                  accent="emerald"
                  loading={isLoadingDetails}
                />
                <StatCard
                  title="Total Outflow Events"
                  value={metrics?.total_outflow ?? "--"}
                  subtitle="Aggregated exits from zones"
                  icon={Activity}
                  accent="amber"
                  loading={isLoadingDetails}
                />
              </div>

              <CrowdTrendChart timeseriesData={timeseries} loading={isLoadingDetails} />

              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                <div className="lg:col-span-5">
                  <ZoneDistribution
                    zoneData={metrics?.zone_totals}
                    latestFrameZones={latestFrame?.zones}
                    totalPeople={latestFrame?.total_people || metrics?.peak_crowd_count}
                    loading={isLoadingDetails}
                  />
                </div>
                <div className="lg:col-span-7">
                  <FlowMetricsChart timeseriesData={timeseries} loading={isLoadingDetails} />
                </div>
              </div>
            </div>
          )}

          {/* VIEW: HEATMAP */}
          {currentView === "heatmap" && (
            <div className="space-y-6">
              <HeatmapPanel heatmapData={heatmapData} selectedRun={selectedRun} loading={isLoadingDetails} />
            </div>
          )}

          {/* VIEW: SETTINGS & ROADMAP */}
          {currentView === "settings" && (
            <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-xs space-y-6">
              <div>
                <h3 className="text-base font-bold text-slate-800 flex items-center gap-2">
                  <SettingsIcon className="w-5 h-5 text-teal-600" />
                  CrowdAhead System Architecture & Settings
                </h3>
                <p className="text-xs text-slate-500 mt-1">
                  Project configuration, backend REST endpoints, and Semester 1 vs Semester 2 roadmap
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-2">
                  <h4 className="font-bold text-slate-700 flex items-center gap-1.5">
                    <Server className="w-4 h-4 text-teal-600" />
                    Backend API Connection
                  </h4>
                  <div className="font-mono text-[11px] text-slate-600 space-y-1">
                    <div>Base URL: http://127.0.0.1:8000</div>
                    <div>Database: SQLite (backend/storage/crowdahead.db)</div>
                    <div>Swagger Docs: http://127.0.0.1:8000/docs</div>
                    <div>
                      Tracking Algorithm:{" "}
                      <span className="text-teal-700 font-bold">{backendInfo?.tracking_engine || "ByteTrack"}</span>
                    </div>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-2">
                  <h4 className="font-bold text-slate-700 flex items-center gap-1.5">
                    <ShieldAlert className="w-4 h-4 text-amber-600" />
                    Semester Phasing
                  </h4>
                  <p className="text-slate-600 leading-relaxed text-[11px]">
                    <strong>Semester 1 (Current Active):</strong> Video upload, YOLO person detection, ByteTrack tracking,
                    current crowd counts, 4-zone quadrant analysis, and 2D spatial density heatmaps.
                  </p>
                  <p className="text-slate-400 text-[10px]">
                    Semester 2 (Future): ConvLSTM spatiotemporal prediction model, risk assessment categories (Low, Medium,
                    High, Critical), and automated alert generation.
                  </p>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
                <span>Member 4: Backend, Risk Assessment, Dashboard, and Integration</span>
                <a
                  href="http://127.0.0.1:8000/docs"
                  target="_blank"
                  rel="noreferrer"
                  className="text-teal-600 hover:text-teal-700 font-semibold flex items-center gap-1"
                >
                  Interactive Swagger Docs <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
