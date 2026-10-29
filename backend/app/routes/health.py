from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint confirming API and database operational status."""
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return HealthResponse(
        status="ok",
        app_name="CrowdAhead API",
        version="1.0.0",
        database=db_status,
        tracking_engine="supervision.ByteTrack",
        semester_phase="Semester 1 — Current Crowd Analysis"
    )
