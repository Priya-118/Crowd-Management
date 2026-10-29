import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base


def get_utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


class Run(Base):
    __tablename__ = "runs"

    id = Column(String(36), primary_key=True, index=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Status lifecycle: uploaded -> queued -> processing -> completed / failed
    status = Column(String(20), default="uploaded", nullable=False, index=True)
    input_type = Column(String(10), nullable=False)  # "csv" or "video"

    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    input_file_path = Column(String(500), nullable=False)

    output_dir = Column(String(500), nullable=True)
    annotated_video_path = Column(String(500), nullable=True)
    heatmap_image_path = Column(String(500), nullable=True)

    error_details = Column(Text, nullable=True)

    # Metadata & summary metrics (populated on completion)
    video_width = Column(Integer, nullable=True, default=832)
    video_height = Column(Integer, nullable=True, default=464)
    video_fps = Column(Float, nullable=True, default=30.0)

    total_frames = Column(Integer, nullable=True)
    peak_crowd_count = Column(Integer, nullable=True)
    average_crowd_count = Column(Float, nullable=True)
    total_unique_tracks = Column(Integer, nullable=True)

    # Relationships
    frame_metrics = relationship("FrameMetric", back_populates="run", cascade="all, delete-orphan")
    zone_metrics = relationship("ZoneMetric", back_populates="run", cascade="all, delete-orphan")


class FrameMetric(Base):
    __tablename__ = "frame_metrics"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    run_id = Column(String(36), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True)
    frame = Column(Integer, nullable=False, index=True)

    total_people = Column(Integer, default=0, nullable=False)
    moving_people = Column(Integer, default=0, nullable=False)
    movement_percentage = Column(Float, default=0.0, nullable=False)
    total_movement_distance = Column(Float, default=0.0, nullable=False)
    total_inflow = Column(Integer, default=0, nullable=False)
    total_outflow = Column(Integer, default=0, nullable=False)
    net_flow = Column(Integer, default=0, nullable=False)

    run = relationship("Run", back_populates="frame_metrics")


class ZoneMetric(Base):
    __tablename__ = "zone_metrics"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    run_id = Column(String(36), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True)
    frame = Column(Integer, nullable=False, index=True)
    zone = Column(String(50), nullable=False)  # "Zone_A", "Zone_B", "Zone_C", "Zone_D", "Outside"

    person_count = Column(Integer, default=0, nullable=False)
    inflow = Column(Integer, default=0, nullable=False)
    outflow = Column(Integer, default=0, nullable=False)
    net_flow = Column(Integer, default=0, nullable=False)

    run = relationship("Run", back_populates="zone_metrics")
