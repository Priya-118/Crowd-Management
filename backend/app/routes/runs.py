from pathlib import Path
from typing import Optional
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.config import (
    OUTPUT_DIR,
    UPLOAD_DIR,
    is_safe_path,
)
from backend.app.database import get_db
from backend.app.models import Run
from backend.app.schemas import (
    HeatmapResponse,
    MessageResponse,
    ProcessRunRequest,
    ProcessRunResponse,
    RunListResponse,
    RunResponse,
    RunSummaryMetrics,
    TimeSeriesResponse,
)
from backend.app.services import heatmap_service, metrics_service, run_service
from backend.app.services.pipeline_service import (
    execute_run_pipeline,
    validate_detection_csv,
)

router = APIRouter(prefix="/runs", tags=["Runs & Pipeline"])


def to_run_response(run: Run) -> RunResponse:
    """Helper to convert ORM Run to RunResponse schema with helper flags."""
    has_video = bool(run.annotated_video_path and Path(run.annotated_video_path).exists())
    has_heatmap = bool(run.heatmap_image_path and Path(run.heatmap_image_path).exists())
    has_raw_video = bool(run.input_file_path and Path(run.input_file_path).exists() and run.input_type == "video")
    return RunResponse(
        id=run.id,
        created_at=run.created_at,
        started_at=run.started_at,
        completed_at=run.completed_at,
        status=run.status,
        input_type=run.input_type,
        original_filename=run.original_filename,
        total_frames=run.total_frames,
        peak_crowd_count=run.peak_crowd_count,
        average_crowd_count=run.average_crowd_count,
        total_unique_tracks=run.total_unique_tracks,
        error_details=run.error_details,
        video_width=run.video_width,
        video_height=run.video_height,
        has_video=has_video,
        has_heatmap=has_heatmap,
        has_raw_video=has_raw_video,
        annotated_video_path=run.annotated_video_path,
        heatmap_image_path=run.heatmap_image_path,
    )


# -------------------------------------------------------------
# 1. Upload Video
# -------------------------------------------------------------
@router.post("/upload", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
def upload_video(
    file: UploadFile = File(..., description="Video file (.mp4, .avi, .mov, .mkv)"),
    db: Session = Depends(get_db)
):
    """Upload a crowd video for subsequent processing."""
    run = run_service.create_run_from_uploaded_file(db, file, expected_type="video")
    return to_run_response(run)


# -------------------------------------------------------------
# 2. Test CSV Mode
# -------------------------------------------------------------
@router.post("/test-csv", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
def upload_or_reference_test_csv(
    file: Optional[UploadFile] = File(None, description="Optional custom detections CSV"),
    use_sample: bool = Query(False, description="Set True to use repository sample test_detections.csv"),
    auto_process: bool = Query(False, description="Set True to immediately queue tracking pipeline"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Accepts either an uploaded detection CSV or uses the repository's sample detections.
    Validates the CSV columns and structure before registering the run.
    """
    if file is not None and file.filename:
        run = run_service.create_run_from_uploaded_file(db, file, expected_type="csv")
        # Validate uploaded CSV
        is_valid, error_msg = validate_detection_csv(Path(run.input_file_path))
        if not is_valid:
            run_service.delete_run(db, run.id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Malformed detection CSV: {error_msg}"
            )
    elif use_sample or file is None:
        run = run_service.create_run_from_sample_csv(db)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either provide a CSV file upload or specify use_sample=true"
        )

    if auto_process:
        run.status = "queued"
        db.commit()
        db.refresh(run)
        background_tasks.add_task(execute_run_pipeline, run.id)

    return to_run_response(run)


# -------------------------------------------------------------
# 3. Trigger Pipeline Processing
# -------------------------------------------------------------
@router.post("/{run_id}/process", response_model=ProcessRunResponse)
def process_run(
    run_id: str,
    background_tasks: BackgroundTasks,
    request: Optional[ProcessRunRequest] = None,
    sync: bool = Query(False, description="Set True for synchronous execution (useful in automated tests)"),
    db: Session = Depends(get_db)
):
    """
    Trigger tracking and flow pipeline for a registered run.
    Runs asynchronously by default or synchronously if sync=true.
    """
    run = run_service.get_run(db, run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run with ID '{run_id}' not found."
        )

    if run.status == "processing":
        return ProcessRunResponse(
            run_id=run.id,
            status=run.status,
            message="Pipeline is already currently processing this run."
        )

    width = request.width if request else None
    height = request.height if request else None

    if sync:
        execute_run_pipeline(run.id, width=width, height=height)
        db.refresh(run)
        return ProcessRunResponse(
            run_id=run.id,
            status=run.status,
            message=f"Pipeline execution completed with status: {run.status}"
        )

    run.status = "queued"
    db.commit()
    background_tasks.add_task(execute_run_pipeline, run.id, width, height)

    return ProcessRunResponse(
        run_id=run.id,
        status="queued",
        message="Pipeline processing has been queued."
    )


# -------------------------------------------------------------
# 4. List Runs
# -------------------------------------------------------------
@router.get("", response_model=RunListResponse)
def list_runs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    """List runs with pagination and optional status filter."""
    runs, total = run_service.list_runs(db, skip=skip, limit=limit, status_filter=status_filter)
    return RunListResponse(
        total=total,
        runs=[to_run_response(r) for r in runs]
    )


# -------------------------------------------------------------
# 5. Get Run by ID
# -------------------------------------------------------------
@router.get("/{run_id}", response_model=RunResponse)
def get_run(run_id: str, db: Session = Depends(get_db)):
    """Retrieve metadata and status of a specific run."""
    run = run_service.get_run(db, run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run with ID '{run_id}' not found."
        )
    return to_run_response(run)


# -------------------------------------------------------------
# 6. Get Metrics
# -------------------------------------------------------------
@router.get("/{run_id}/metrics", response_model=RunSummaryMetrics)
def get_run_metrics(run_id: str, db: Session = Depends(get_db)):
    """Retrieve high-level summary crowd counts, movement, and flow metrics."""
    return metrics_service.get_summary_metrics(db, run_id)


# -------------------------------------------------------------
# 7. Get Time-series
# -------------------------------------------------------------
@router.get("/{run_id}/timeseries", response_model=TimeSeriesResponse)
def get_run_timeseries(run_id: str, db: Session = Depends(get_db)):
    """Retrieve frame-by-frame time-series data for crowd trends."""
    return metrics_service.get_timeseries_metrics(db, run_id)


# -------------------------------------------------------------
# 8. Get Heatmap Data
# -------------------------------------------------------------
@router.get("/{run_id}/heatmap", response_model=HeatmapResponse)
def get_run_heatmap(run_id: str, db: Session = Depends(get_db)):
    """Retrieve 2D Gaussian crowd density heatmap data and hotspot coordinates."""
    return heatmap_service.get_heatmap_data(db, run_id)


# -------------------------------------------------------------
# 9. Get Heatmap Image
# -------------------------------------------------------------
@router.get("/{run_id}/heatmap/image")
def get_run_heatmap_image(run_id: str, db: Session = Depends(get_db)):
    """Stream the generated crowd density heatmap image."""
    run = run_service.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.")

    if not run.heatmap_image_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Heatmap image not available for this run.")

    img_path = Path(run.heatmap_image_path)
    if not is_safe_path(OUTPUT_DIR, img_path) or not img_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Heatmap image file does not exist on disk.")

    return FileResponse(img_path, media_type="image/png", filename=f"heatmap_{run.id}.png")


# -------------------------------------------------------------
# 10. Get Annotated Video
# -------------------------------------------------------------
@router.get("/{run_id}/video")
def get_run_video(run_id: str, db: Session = Depends(get_db)):
    """Stream the processed video for a run."""
    run = run_service.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.")

    if run.input_type == "csv":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No video available for this run (input was a detection CSV)."
        )

    if not run.annotated_video_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Annotated video has not been generated for this run."
        )

    video_path = Path(run.annotated_video_path)
    if not is_safe_path(OUTPUT_DIR, video_path) or not video_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Annotated video file not found on disk."
        )

    return FileResponse(video_path, media_type="video/mp4", filename=f"annotated_{run.id}.mp4")


# -------------------------------------------------------------
# 10b. Get Raw Uploaded Video
# -------------------------------------------------------------
@router.get("/{run_id}/raw-video")
def get_run_raw_video(run_id: str, db: Session = Depends(get_db)):
    """Stream the raw uploaded video for a run."""
    run = run_service.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.")

    if run.input_type != "video":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No raw video available for this run (input was not a video)."
        )

    if not run.input_file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Raw video file path not recorded for this run."
        )

    raw_path = Path(run.input_file_path)
    if not is_safe_path(UPLOAD_DIR, raw_path) or not raw_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Raw video file not found on disk."
        )

    return FileResponse(raw_path, media_type="video/mp4", filename=run.original_filename)


# -------------------------------------------------------------
# 11. Delete Run
# -------------------------------------------------------------
@router.delete("/{run_id}", response_model=MessageResponse)
def delete_run(run_id: str, db: Session = Depends(get_db)):
    """Delete a run, its database records, and its uploaded/generated files."""
    success = run_service.delete_run(db, run_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run with ID '{run_id}' not found."
        )
    return MessageResponse(
        message=f"Run '{run_id}' and all associated files have been deleted.",
        run_id=run_id
    )
