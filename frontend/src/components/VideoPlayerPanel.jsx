import { Video, FileSpreadsheet, AlertCircle } from "lucide-react";
import { api } from "../services/api";

export default function VideoPlayerPanel({ selectedRun }) {
  if (!selectedRun) return null;

  const isVideo = selectedRun.input_type === "video";
  const hasVideoFile = selectedRun.has_video;

  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
            <Video className="w-4 h-4 text-teal-600" />
            Media & Tracking Stream
          </h3>
          <p className="text-xs text-slate-500">Visual footage and bounding box annotations</p>
        </div>
        <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
          {isVideo ? "Video Input" : "CSV Detections"}
        </span>
      </div>

      <div className="bg-slate-950 rounded-xl overflow-hidden border border-slate-800 min-h-[260px] flex items-center justify-center p-3">
        {isVideo && hasVideoFile ? (
          <video
            controls
            className="w-full max-h-[380px] rounded-lg shadow-lg"
            src={api.getVideoStreamUrl(selectedRun.id)}
          >
            Your browser does not support the video tag.
          </video>
        ) : isVideo ? (
          <div className="text-center p-6 max-w-md">
            <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 text-amber-400 flex items-center justify-center mx-auto mb-3">
              <AlertCircle className="w-6 h-6" />
            </div>
            <h4 className="text-sm font-bold text-slate-200">Raw Video Ingested</h4>
            <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
              Detection model weights (YOLO) and PyTorch are required to generate the annotated bounding-box video stream.
            </p>
            <p className="text-[11px] text-teal-400 mt-2">
              For active testing of the tracking and flow analytics, use the CSV detection interface.
            </p>
          </div>
        ) : (
          <div className="text-center p-6 max-w-md">
            <div className="w-12 h-12 rounded-full bg-teal-950/80 border border-teal-800/60 text-teal-400 flex items-center justify-center mx-auto mb-3">
              <FileSpreadsheet className="w-6 h-6" />
            </div>
            <h4 className="text-sm font-bold text-slate-200">Detection Coordinates Stream</h4>
            <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
              This run was executed using frame coordinates from detection interface (
              <span className="font-mono text-teal-300">{selectedRun.original_filename}</span>).
            </p>
            <div className="mt-3 p-2.5 rounded bg-slate-900 border border-slate-800 text-[11px] text-slate-300 text-left font-mono">
              <div>Schema: [frame, x1, y1, x2, y2, confidence]</div>
              <div>Tracking: ByteTrack (30 FPS)</div>
              <div>Scene Boundaries: {selectedRun.video_width || 832} × {selectedRun.video_height || 464}</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
