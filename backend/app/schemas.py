import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# -------------------------------------------------------------
# Health Schema
# -------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str = "ok"
    app_name: str = "CrowdAhead API"
    version: str = "1.0.0"
    database: str
    tracking_engine: str = "supervision.ByteTrack"
    semester_phase: str = "Semester 1 — Current Crowd Analysis"


# -------------------------------------------------------------
# Run Schemas
# -------------------------------------------------------------
class RunBase(BaseModel):
    input_type: str
    original_filename: str


class RunResponse(BaseModel):
    id: str
    created_at: datetime.datetime
    started_at: Optional[datetime.datetime] = None
    completed_at: Optional[datetime.datetime] = None
    status: str
    input_type: str
    original_filename: str
    total_frames: Optional[int] = None
    peak_crowd_count: Optional[int] = None
    average_crowd_count: Optional[float] = None
    total_unique_tracks: Optional[int] = None
    error_details: Optional[str] = None
    video_width: Optional[int] = None
    video_height: Optional[int] = None
    has_video: bool = False
    has_heatmap: bool = False
    has_raw_video: bool = False
    annotated_video_path: Optional[str] = None
    heatmap_image_path: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RunListResponse(BaseModel):
    total: int
    runs: List[RunResponse]


class ProcessRunRequest(BaseModel):
    width: Optional[int] = None
    height: Optional[int] = None


class ProcessRunResponse(BaseModel):
    run_id: str
    status: str
    message: str


# -------------------------------------------------------------
# Metrics & Summary Schemas
# -------------------------------------------------------------
class ZoneBreakdown(BaseModel):
    Zone_A: int = 0
    Zone_B: int = 0
    Zone_C: int = 0
    Zone_D: int = 0
    Outside: int = 0


class RunSummaryMetrics(BaseModel):
    run_id: str
    status: str
    total_frames: int
    total_unique_tracks: int
    peak_crowd_count: int
    average_crowd_count: float
    zone_totals: Dict[str, int]
    average_movement_percentage: float
    total_movement_distance: float
    total_inflow: int
    total_outflow: int
    net_flow: int
    crowd_density_note: str = (
        "Note: People counts represent detected and tracked person instances, "
        "not physical density per square meter."
    )


# -------------------------------------------------------------
# Time-series Schemas
# -------------------------------------------------------------
class FrameTimeSeriesItem(BaseModel):
    frame: int
    total_people: int
    moving_people: int
    movement_percentage: float
    total_movement_distance: float
    zones: Dict[str, int]
    total_inflow: int
    total_outflow: int
    net_flow: int


class TimeSeriesResponse(BaseModel):
    run_id: str
    total_frames: int
    frames: List[FrameTimeSeriesItem]


# -------------------------------------------------------------
# Heatmap Schemas
# -------------------------------------------------------------
class HotspotPoint(BaseModel):
    cx: float
    cy: float
    intensity: float


class HeatmapResponse(BaseModel):
    run_id: str
    status: str  # "available" or "unavailable"
    message: Optional[str] = None
    grid_width: Optional[int] = None
    grid_height: Optional[int] = None
    max_density: Optional[float] = None
    density_grid: Optional[List[List[float]]] = None
    hotspots: Optional[List[HotspotPoint]] = None
    heatmap_image_url: Optional[str] = None


# -------------------------------------------------------------
# Standard Action & Message Schemas
# -------------------------------------------------------------
class MessageResponse(BaseModel):
    message: str
    run_id: Optional[str] = None
