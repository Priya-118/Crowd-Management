import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
});

export const api = {
  // Health
  checkHealth: async () => {
    const res = await apiClient.get("/api/health");
    return res.data;
  },

  // Runs
  listRuns: async (skip = 0, limit = 50, status = null) => {
    const params = { skip, limit };
    if (status) params.status = status;
    const res = await apiClient.get("/api/runs", { params });
    return res.data;
  },

  getRun: async (runId) => {
    const res = await apiClient.get(`/api/runs/${runId}`);
    return res.data;
  },

  uploadVideo: async (file, onUploadProgress) => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await apiClient.post("/api/runs/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress,
    });
    return res.data;
  },

  createSampleCsvRun: async (autoProcess = false) => {
    const res = await apiClient.post(`/api/runs/test-csv?use_sample=true&auto_process=${autoProcess}`);
    return res.data;
  },

  uploadCustomCsv: async (file, autoProcess = false) => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await apiClient.post(`/api/runs/test-csv?auto_process=${autoProcess}`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return res.data;
  },

  processRun: async (runId, sync = false) => {
    const res = await apiClient.post(`/api/runs/${runId}/process?sync=${sync}`);
    return res.data;
  },

  deleteRun: async (runId) => {
    const res = await apiClient.delete(`/api/runs/${runId}`);
    return res.data;
  },

  // Metrics & Visualizations
  getRunMetrics: async (runId) => {
    const res = await apiClient.get(`/api/runs/${runId}/metrics`);
    return res.data;
  },

  getRunTimeseries: async (runId) => {
    const res = await apiClient.get(`/api/runs/${runId}/timeseries`);
    return res.data;
  },

  getRunHeatmap: async (runId) => {
    const res = await apiClient.get(`/api/runs/${runId}/heatmap`);
    return res.data;
  },

  getHeatmapImageUrl: (runId) => {
    return `${BASE_URL}/api/runs/${runId}/heatmap/image?t=${Date.now()}`;
  },

  getVideoStreamUrl: (runId) => {
    return `${BASE_URL}/api/runs/${runId}/video`;
  },
};

export default api;
