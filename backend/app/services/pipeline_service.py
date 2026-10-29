import datetime
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import supervision as sv
from sqlalchemy.orm import Session

from backend.app.config import (
    DEFAULT_FRAME_HEIGHT,
    DEFAULT_FRAME_WIDTH,
    OUTPUT_DIR,
    is_safe_path,
)
from backend.app.database import SessionLocal
from backend.app.models import FrameMetric, Run, ZoneMetric
from backend.app.services.detector_adapter import execute_person_detection


# ---------------------------------------------------------------------------
# CSV Validation
# ---------------------------------------------------------------------------
REQUIRED_DETECTION_COLUMNS = ["frame", "x1", "y1", "x2", "y2", "confidence"]


def validate_detection_csv(csv_path: Path) -> Tuple[bool, Optional[str]]:
    """
    Validate that the CSV file exists, is readable, contains required columns,
    and has valid numeric rows.
    """
    if not csv_path.exists():
        return False, f"File not found: {csv_path}"

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        return False, f"Unable to parse CSV file: {str(e)}"

    if df.empty:
        return False, "CSV file is empty (contains no data rows)."

    missing_cols = [c for c in REQUIRED_DETECTION_COLUMNS if c not in df.columns]
    if missing_cols:
        return False, f"Missing required CSV columns: {missing_cols}. Expected: {REQUIRED_DETECTION_COLUMNS}"

    # Verify data types and numeric validity
    for col in REQUIRED_DETECTION_COLUMNS:
        if not pd.to_numeric(df[col], errors="coerce").notnull().all():
            return False, f"Column '{col}' contains non-numeric or NaN values."

    # Validate coordinate sanity
    if not (df["x2"] >= df["x1"]).all():
        return False, "Invalid bounding box detected: x2 must be greater than or equal to x1."
    if not (df["y2"] >= df["y1"]).all():
        return False, "Invalid bounding box detected: y2 must be greater than or equal to y1."

    return True, None


# ---------------------------------------------------------------------------
# Algorithmic Steps Reusing Member 2's Logic with Dynamic Paths
# ---------------------------------------------------------------------------
def calculate_direction(dx: float, dy: float, threshold: float = 2.0) -> str:
    """Direction determination matching tracking/src/movement.py."""
    if abs(dx) <= threshold and abs(dy) <= threshold:
        return "STATIONARY"
    if abs(dx) > abs(dy):
        return "RIGHT" if dx > 0 else "LEFT"
    return "DOWN" if dy > 0 else "UP"


def get_zone(cx: float, cy: float, width: int, height: int) -> str:
    """4-zone quadrant split matching tracking/src/zones.py."""
    if not (0 <= cx < width and 0 <= cy < height):
        return "Outside"
    mid_x = width / 2.0
    mid_y = height / 2.0

    if cx < mid_x and cy < mid_y:
        return "Zone_A"
    elif cx >= mid_x and cy < mid_y:
        return "Zone_B"
    elif cx < mid_x and cy >= mid_y:
        return "Zone_C"
    else:
        return "Zone_D"


def run_tracking_pipeline(
    input_csv_path: Path,
    out_dir: Path,
    width: int = DEFAULT_FRAME_WIDTH,
    height: int = DEFAULT_FRAME_HEIGHT,
) -> Dict[str, Path]:
    """
    Executes the ByteTrack tracking and analytics pipeline into out_dir.
    Returns a dictionary of generated CSV paths.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. ByteTrack Tracking
    detections_df = pd.read_csv(input_csv_path)

    tracker = sv.ByteTrack(frame_rate=30)
    tracked_rows = []

    if not detections_df.empty and "frame" in detections_df.columns:
        detections_df["frame"] = detections_df["frame"].astype(int)
        first_frame = int(detections_df["frame"].min())
        last_frame = int(detections_df["frame"].max())
    else:
        first_frame = 1
        last_frame = 0  # loop will not execute

    for frame_number in range(first_frame, last_frame + 1):
        frame_data = detections_df[detections_df["frame"] == frame_number]

        if frame_data.empty:
            detections = sv.Detections.empty()
        else:
            xyxy = frame_data[["x1", "y1", "x2", "y2"]].to_numpy(dtype=float)
            confidence = frame_data["confidence"].to_numpy(dtype=float)
            detections = sv.Detections(xyxy=xyxy, confidence=confidence)

        tracked_detections = tracker.update_with_detections(detections)

        if tracked_detections.tracker_id is None:
            continue

        for i in range(len(tracked_detections)):
            x1, y1, x2, y2 = tracked_detections.xyxy[i]
            track_id = tracked_detections.tracker_id[i]
            confidence = tracked_detections.confidence[i]
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0

            tracked_rows.append({
                "frame": frame_number,
                "track_id": int(track_id),
                "x1": int(round(x1)),
                "y1": int(round(y1)),
                "x2": int(round(x2)),
                "y2": int(round(y2)),
                "confidence": round(float(confidence), 4) if confidence is not None else 1.0,
                "cx": round(float(cx), 2),
                "cy": round(float(cy), 2),
            })

    tracked_df = pd.DataFrame(
        tracked_rows,
        columns=["frame", "track_id", "x1", "y1", "x2", "y2", "confidence", "cx", "cy"]
    )
    tracked_csv = out_dir / "tracked_detections.csv"
    tracked_df.to_csv(tracked_csv, index=False)

    # 2. Movement Analysis
    if not tracked_df.empty:
        tracked_df = tracked_df.sort_values(["track_id", "frame"]).reset_index(drop=True)
        tracked_df["prev_cx"] = tracked_df.groupby("track_id")["cx"].shift(1)
        tracked_df["prev_cy"] = tracked_df.groupby("track_id")["cy"].shift(1)

        movement_rows = []
        for _, row in tracked_df.iterrows():
            if pd.isna(row["prev_cx"]):
                dx, dy, distance, direction = 0.0, 0.0, 0.0, "START"
            else:
                dx = row["cx"] - row["prev_cx"]
                dy = row["cy"] - row["prev_cy"]
                distance = math.sqrt(dx ** 2 + dy ** 2)
                direction = calculate_direction(dx, dy)

            movement_rows.append({
                "frame": int(row["frame"]),
                "track_id": int(row["track_id"]),
                "cx": row["cx"],
                "cy": row["cy"],
                "dx": round(dx, 2),
                "dy": round(dy, 2),
                "distance": round(distance, 2),
                "direction": direction,
            })
        movement_df = pd.DataFrame(movement_rows)
    else:
        movement_df = pd.DataFrame(columns=["frame", "track_id", "cx", "cy", "dx", "dy", "distance", "direction"])

    movement_csv = out_dir / "movement.csv"
    movement_df.to_csv(movement_csv, index=False)

    # 3. Zones Assignment
    if not movement_df.empty:
        movement_df["zone"] = movement_df.apply(
            lambda row: get_zone(row["cx"], row["cy"], width, height), axis=1
        )
    else:
        movement_df["zone"] = pd.Series(dtype=str)

    zone_assign_csv = out_dir / "zone_assignments.csv"
    movement_df.to_csv(zone_assign_csv, index=False)

    # 4. Zone Counts
    if not movement_df.empty:
        zc = (
            movement_df.groupby(["frame", "zone"])["track_id"]
            .nunique()
            .reset_index(name="person_count")
        )
        zone_counts = zc.pivot(index="frame", columns="zone", values="person_count").fillna(0).reset_index()
        zone_counts.columns.name = None

        for col in ["Zone_A", "Zone_B", "Zone_C", "Zone_D", "Outside"]:
            if col not in zone_counts.columns:
                zone_counts[col] = 0

        zone_cols = [c for c in zone_counts.columns if c != "frame"]
        for col in zone_cols:
            zone_counts[col] = zone_counts[col].astype(int)

        zone_counts["total_people"] = zone_counts[zone_cols].sum(axis=1)
    else:
        zone_counts = pd.DataFrame(columns=["frame", "Zone_A", "Zone_B", "Zone_C", "Zone_D", "total_people"])

    zone_counts_csv = out_dir / "zone_counts.csv"
    zone_counts.to_csv(zone_counts_csv, index=False)

    # 5. Zone Flow (Transitions)
    if not movement_df.empty:
        movement_df = movement_df.sort_values(["track_id", "frame"]).copy()
        movement_df["previous_zone"] = movement_df.groupby("track_id")["zone"].shift(1)
        transitions = movement_df[
            movement_df["previous_zone"].notna() & (movement_df["zone"] != movement_df["previous_zone"])
        ].copy()

        flow_records = []
        for _, row in transitions.iterrows():
            flow_records.append({
                "frame": int(row["frame"]),
                "track_id": int(row["track_id"]),
                "from_zone": row["previous_zone"],
                "to_zone": row["zone"],
            })
        flow_df = pd.DataFrame(flow_records)
    else:
        flow_df = pd.DataFrame(columns=["frame", "track_id", "from_zone", "to_zone"])

    zone_flow_csv = out_dir / "zone_flow.csv"
    flow_df.to_csv(zone_flow_csv, index=False)

    # 6. Inflow / Outflow
    flow_columns = ["frame", "zone", "inflow", "outflow", "net_flow"]
    if not flow_df.empty:
        inflow = flow_df.groupby(["frame", "to_zone"]).size().reset_index(name="inflow").rename(columns={"to_zone": "zone"})
        outflow = flow_df.groupby(["frame", "from_zone"]).size().reset_index(name="outflow").rename(columns={"from_zone": "zone"})
        inflow_outflow = pd.merge(inflow, outflow, on=["frame", "zone"], how="outer")
        inflow_outflow[["inflow", "outflow"]] = inflow_outflow[["inflow", "outflow"]].fillna(0).astype(int)
        inflow_outflow["net_flow"] = inflow_outflow["inflow"] - inflow_outflow["outflow"]
        inflow_outflow = inflow_outflow[flow_columns].sort_values(["frame", "zone"])
    else:
        inflow_outflow = pd.DataFrame(columns=flow_columns)

    inflow_outflow_csv = out_dir / "inflow_outflow.csv"
    inflow_outflow.to_csv(inflow_outflow_csv, index=False)

    # 7. Crowd Flow Metrics
    occupancy = zone_counts[["frame", "total_people"]].copy() if not zone_counts.empty else pd.DataFrame(columns=["frame", "total_people"])

    if not movement_df.empty:
        moving = movement_df[~movement_df["direction"].isin(["START", "STATIONARY"])]
        moving_people = moving.groupby("frame")["track_id"].nunique().reset_index(name="moving_people")
        movement_dist = movement_df.groupby("frame")["distance"].sum().reset_index(name="total_movement_distance")
    else:
        moving_people = pd.DataFrame(columns=["frame", "moving_people"])
        movement_dist = pd.DataFrame(columns=["frame", "total_movement_distance"])

    if not inflow_outflow.empty:
        total_flow = inflow_outflow.groupby("frame").agg(
            total_inflow=("inflow", "sum"),
            total_outflow=("outflow", "sum"),
            net_flow=("net_flow", "sum")
        ).reset_index()
    else:
        total_flow = pd.DataFrame(columns=["frame", "total_inflow", "total_outflow", "net_flow"])

    metrics = occupancy.merge(moving_people, on="frame", how="left")
    metrics = metrics.merge(movement_dist, on="frame", how="left")
    metrics = metrics.merge(total_flow, on="frame", how="left")
    metrics = metrics.fillna(0)

    for col in ["total_people", "moving_people", "total_inflow", "total_outflow", "net_flow"]:
        if col in metrics.columns:
            metrics[col] = metrics[col].astype(int)

    if not metrics.empty:
        metrics["movement_percentage"] = (
            metrics["moving_people"] / metrics["total_people"].replace(0, pd.NA) * 100
        ).fillna(0).round(2)
    else:
        metrics["movement_percentage"] = pd.Series(dtype=float)

    crowd_metrics_csv = out_dir / "crowd_flow_metrics.csv"
    metrics.to_csv(crowd_metrics_csv, index=False)

    return {
        "tracked_detections": tracked_csv,
        "movement": movement_csv,
        "zone_assignments": zone_assign_csv,
        "zone_counts": zone_counts_csv,
        "zone_flow": zone_flow_csv,
        "inflow_outflow": inflow_outflow_csv,
        "crowd_flow_metrics": crowd_metrics_csv,
    }


# ---------------------------------------------------------------------------
# Background Process Execution & DB Persistence
# ---------------------------------------------------------------------------
def execute_run_pipeline(run_id: str, width: Optional[int] = None, height: Optional[int] = None):
    """
    Executes the pipeline for run_id in an isolated session, updating run status
    and persisting frame/zone metrics.
    """
    db = SessionLocal()
    try:
        run = db.query(Run).filter(Run.id == run_id).first()
        if not run:
            return

        run.status = "processing"
        run.started_at = datetime.datetime.now(datetime.timezone.utc)
        db.commit()

        w = width or run.video_width or DEFAULT_FRAME_WIDTH
        h = height or run.video_height or DEFAULT_FRAME_HEIGHT

        out_dir = OUTPUT_DIR / run.id
        out_dir.mkdir(parents=True, exist_ok=True)
        run.output_dir = str(out_dir.resolve())
        run.video_width = w
        run.video_height = h

        # Handle input source (Video detection or CSV input)
        if run.input_type == "video":
            video_path = Path(run.input_file_path)
            if not video_path.exists():
                run.status = "failed"
                run.error_details = f"Input video file not found on disk at '{video_path}'."
                run.completed_at = datetime.datetime.now(datetime.timezone.utc)
                db.commit()
                return

            det_csv_path = out_dir / "detections.csv"
            annotated_video_path = out_dir / "annotated_video.mp4"

            # Execute person detection via adapter
            success, err_msg = execute_person_detection(
                video_path=video_path,
                output_csv_path=det_csv_path,
                output_video_path=annotated_video_path,
            )

            if not success:
                run.status = "failed"
                run.error_details = err_msg
                run.completed_at = datetime.datetime.now(datetime.timezone.utc)
                db.commit()
                return

            if annotated_video_path.exists():
                run.annotated_video_path = str(annotated_video_path.resolve())

            input_csv = det_csv_path
        else:
            # CSV detection input
            input_csv = Path(run.input_file_path)
            is_valid, err_msg = validate_detection_csv(input_csv)
            if not is_valid:
                run.status = "failed"
                run.error_details = f"CSV Validation Failed: {err_msg}"
                run.completed_at = datetime.datetime.now(datetime.timezone.utc)
                db.commit()
                return

        # Run pipeline
        output_files = run_tracking_pipeline(input_csv, out_dir, width=w, height=h)

        # Read results for persistence
        metrics_df = pd.read_csv(output_files["crowd_flow_metrics"])
        zone_counts_df = pd.read_csv(output_files["zone_counts"])
        flow_df = pd.read_csv(output_files["inflow_outflow"])
        tracked_df = pd.read_csv(output_files["tracked_detections"])

        # Persist Frame Metrics
        for _, row in metrics_df.iterrows():
            fm = FrameMetric(
                run_id=run.id,
                frame=int(row["frame"]),
                total_people=int(row.get("total_people", 0)),
                moving_people=int(row.get("moving_people", 0)),
                movement_percentage=float(row.get("movement_percentage", 0.0)),
                total_movement_distance=float(row.get("total_movement_distance", 0.0)),
                total_inflow=int(row.get("total_inflow", 0)),
                total_outflow=int(row.get("total_outflow", 0)),
                net_flow=int(row.get("net_flow", 0)),
            )
            db.add(fm)

        # Persist Zone Metrics
        zone_names = ["Zone_A", "Zone_B", "Zone_C", "Zone_D", "Outside"]
        for _, row in zone_counts_df.iterrows():
            f = int(row["frame"])
            for zn in zone_names:
                if zn in row:
                    cnt = int(row[zn])
                    # Check flow for this frame & zone
                    matching_flow = flow_df[(flow_df["frame"] == f) & (flow_df["zone"] == zn)] if not flow_df.empty else pd.DataFrame()
                    inf = int(matching_flow["inflow"].iloc[0]) if not matching_flow.empty else 0
                    outf = int(matching_flow["outflow"].iloc[0]) if not matching_flow.empty else 0
                    netf = int(matching_flow["net_flow"].iloc[0]) if not matching_flow.empty else 0

                    zm = ZoneMetric(
                        run_id=run.id,
                        frame=f,
                        zone=zn,
                        person_count=cnt,
                        inflow=inf,
                        outflow=outf,
                        net_flow=netf,
                    )
                    db.add(zm)

        # Generate Heatmap image and data
        from backend.app.services.heatmap_service import generate_heatmap_for_run
        heatmap_path = generate_heatmap_for_run(run.id, out_dir, w, h)
        if heatmap_path:
            run.heatmap_image_path = str(heatmap_path.resolve())

        # Update run summary
        run.total_frames = int(metrics_df["frame"].nunique()) if not metrics_df.empty else 0
        run.peak_crowd_count = int(metrics_df["total_people"].max()) if not metrics_df.empty else 0
        run.average_crowd_count = float(round(metrics_df["total_people"].mean(), 2)) if not metrics_df.empty else 0.0
        run.total_unique_tracks = int(tracked_df["track_id"].nunique()) if not tracked_df.empty else 0

        run.status = "completed"
        run.completed_at = datetime.datetime.now(datetime.timezone.utc)
        run.error_details = None
        db.commit()

    except Exception as e:
        db.rollback()
        try:
            run = db.query(Run).filter(Run.id == run_id).first()
            if run:
                run.status = "failed"
                run.error_details = f"Processing Error: {str(e)}"
                run.completed_at = datetime.datetime.now(datetime.timezone.utc)
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
