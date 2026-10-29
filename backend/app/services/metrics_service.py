from typing import Dict, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from backend.app.models import FrameMetric, Run, ZoneMetric
from backend.app.schemas import (
    FrameTimeSeriesItem,
    RunSummaryMetrics,
    TimeSeriesResponse,
)


def get_summary_metrics(db: Session, run_id: str) -> RunSummaryMetrics:
    """Computes high-level aggregated crowd metrics for a completed run."""
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run with ID '{run_id}' not found."
        )

    if run.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Run is currently in '{run.status}' state. Summary metrics are only available for 'completed' runs."
        )

    frame_metrics = (
        db.query(FrameMetric)
        .filter(FrameMetric.run_id == run_id)
        .order_by(FrameMetric.frame.asc())
        .all()
    )

    if not frame_metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No frame metrics recorded for this run."
        )

    total_frames = len(frame_metrics)
    people_counts = [fm.total_people for fm in frame_metrics]
    peak_count = max(people_counts) if people_counts else 0
    avg_count = round(sum(people_counts) / total_frames, 2) if total_frames > 0 else 0.0

    movement_pcts = [fm.movement_percentage for fm in frame_metrics]
    avg_move_pct = round(sum(movement_pcts) / total_frames, 2) if total_frames > 0 else 0.0
    total_dist = round(sum(fm.total_movement_distance for fm in frame_metrics), 2)

    total_inflow = sum(fm.total_inflow for fm in frame_metrics)
    total_outflow = sum(fm.total_outflow for fm in frame_metrics)
    net_flow = total_inflow - total_outflow

    # Zone distribution totals (sum of observations per zone across frames)
    zone_metrics = db.query(ZoneMetric).filter(ZoneMetric.run_id == run_id).all()
    zone_totals: Dict[str, int] = {"Zone_A": 0, "Zone_B": 0, "Zone_C": 0, "Zone_D": 0, "Outside": 0}
    for zm in zone_metrics:
        if zm.zone in zone_totals:
            zone_totals[zm.zone] += zm.person_count
        else:
            zone_totals[zm.zone] = zm.person_count

    return RunSummaryMetrics(
        run_id=run.id,
        status=run.status,
        total_frames=total_frames,
        total_unique_tracks=run.total_unique_tracks or 0,
        peak_crowd_count=peak_count,
        average_crowd_count=avg_count,
        zone_totals=zone_totals,
        average_movement_percentage=avg_move_pct,
        total_movement_distance=total_dist,
        total_inflow=total_inflow,
        total_outflow=total_outflow,
        net_flow=net_flow,
    )


def get_timeseries_metrics(db: Session, run_id: str) -> TimeSeriesResponse:
    """Retrieves frame-by-frame time-series crowd and flow statistics."""
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run with ID '{run_id}' not found."
        )

    if run.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Run is currently in '{run.status}' state. Time-series metrics are only available for 'completed' runs."
        )

    frame_metrics = (
        db.query(FrameMetric)
        .filter(FrameMetric.run_id == run_id)
        .order_by(FrameMetric.frame.asc())
        .all()
    )

    zone_metrics = (
        db.query(ZoneMetric)
        .filter(ZoneMetric.run_id == run_id)
        .order_by(ZoneMetric.frame.asc())
        .all()
    )

    # Group zone metrics by frame
    frame_zones: Dict[int, Dict[str, int]] = {}
    for zm in zone_metrics:
        if zm.frame not in frame_zones:
            frame_zones[zm.frame] = {}
        frame_zones[zm.frame][zm.zone] = zm.person_count

    items: List[FrameTimeSeriesItem] = []
    for fm in frame_metrics:
        zones = frame_zones.get(fm.frame, {"Zone_A": 0, "Zone_B": 0, "Zone_C": 0, "Zone_D": 0})
        items.append(
            FrameTimeSeriesItem(
                frame=fm.frame,
                total_people=fm.total_people,
                moving_people=fm.moving_people,
                movement_percentage=fm.movement_percentage,
                total_movement_distance=fm.total_movement_distance,
                zones=zones,
                total_inflow=fm.total_inflow,
                total_outflow=fm.total_outflow,
                net_flow=fm.net_flow,
            )
        )

    return TimeSeriesResponse(
        run_id=run.id,
        total_frames=len(items),
        frames=items,
    )
