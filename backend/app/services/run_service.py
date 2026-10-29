import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional, Tuple
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from backend.app.config import (
    ALLOWED_CSV_EXTENSIONS,
    ALLOWED_VIDEO_EXTENSIONS,
    MAX_UPLOAD_SIZE_BYTES,
    OUTPUT_DIR,
    SAMPLE_DETECTIONS_PATH,
    STORAGE_DIR,
    UPLOAD_DIR,
    ensure_directories,
    is_safe_path,
)
from backend.app.models import Run


def sanitize_filename(filename: str) -> str:
    """Strip dangerous characters to prevent path traversal."""
    clean = Path(filename).name
    return "".join(c for c in clean if c.isalnum() or c in (".", "_", "-")) or "unnamed_file"


def create_run_from_uploaded_file(
    db: Session,
    file: UploadFile,
    expected_type: str  # "csv" or "video"
) -> Run:
    """Save an uploaded file and register a new run."""
    ensure_directories()
    raw_name = file.filename or ("data.csv" if expected_type == "csv" else "video.mp4")
    safe_name = sanitize_filename(raw_name)
    ext = Path(safe_name).suffix.lower()

    if expected_type == "video":
        if ext not in ALLOWED_VIDEO_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported video format '{ext}'. Allowed: {sorted(ALLOWED_VIDEO_EXTENSIONS)}"
            )
    elif expected_type == "csv":
        if ext not in ALLOWED_CSV_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '{ext}'. Expected .csv"
            )

    run_id = str(uuid.uuid4())
    stored_filename = f"{run_id}_{safe_name}"
    target_path = UPLOAD_DIR / stored_filename

    # Read and validate file size
    bytes_written = 0
    with open(target_path, "wb") as buffer:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            bytes_written += len(chunk)
            if bytes_written > MAX_UPLOAD_SIZE_BYTES:
                buffer.close()
                if target_path.exists():
                    target_path.unlink()
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File exceeds maximum allowed size ({MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB)"
                )
            buffer.write(chunk)

    if bytes_written == 0:
        if target_path.exists():
            target_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    run = Run(
        id=run_id,
        status="uploaded",
        input_type=expected_type,
        original_filename=raw_name,
        stored_filename=stored_filename,
        input_file_path=str(target_path.resolve())
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def create_run_from_sample_csv(db: Session) -> Run:
    """Create a new run referencing the repository's sample detection CSV."""
    ensure_directories()
    if not SAMPLE_DETECTIONS_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sample detection file not found at {SAMPLE_DETECTIONS_PATH}"
        )

    run_id = str(uuid.uuid4())
    stored_filename = f"{run_id}_sample_detections.csv"
    target_path = UPLOAD_DIR / stored_filename

    shutil.copy(SAMPLE_DETECTIONS_PATH, target_path)

    run = Run(
        id=run_id,
        status="uploaded",
        input_type="csv",
        original_filename="test_detections.csv",
        stored_filename=stored_filename,
        input_file_path=str(target_path.resolve())
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_run(db: Session, run_id: str) -> Optional[Run]:
    """Retrieve run by ID."""
    return db.query(Run).filter(Run.id == run_id).first()


def list_runs(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[str] = None
) -> Tuple[List[Run], int]:
    """List runs with optional status filtering and pagination."""
    query = db.query(Run)
    if status_filter:
        query = query.filter(Run.status == status_filter)
    total = query.count()
    runs = query.order_by(Run.created_at.desc()).offset(skip).limit(limit).all()
    return runs, total


def delete_run(db: Session, run_id: str) -> bool:
    """Safely delete run database entry and associated files."""
    run = get_run(db, run_id)
    if not run:
        return False

    # Safe delete of input file
    if run.input_file_path:
        input_path = Path(run.input_file_path)
        if is_safe_path(UPLOAD_DIR, input_path) and input_path.is_file():
            try:
                input_path.unlink()
            except Exception:
                pass

    # Safe delete of output directory
    if run.output_dir:
        out_dir = Path(run.output_dir)
        if is_safe_path(OUTPUT_DIR, out_dir) and out_dir.is_dir():
            try:
                shutil.rmtree(out_dir)
            except Exception:
                pass

    db.delete(run)
    db.commit()
    return True
