import os
from pathlib import Path
from typing import List

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
REPO_ROOT = BASE_DIR
BACKEND_DIR = BASE_DIR / "backend"

# Storage Settings
STORAGE_DIR = Path(os.getenv("CROWDAHEAD_STORAGE_DIR", str(BACKEND_DIR / "storage")))
UPLOAD_DIR = STORAGE_DIR / "uploads"
OUTPUT_DIR = STORAGE_DIR / "outputs"

# Database Settings
DATABASE_URL = os.getenv("CROWDAHEAD_DATABASE_URL", f"sqlite:///{STORAGE_DIR / 'crowdahead.db'}")

# File Validation Settings
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "100"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}
ALLOWED_CSV_EXTENSIONS = {".csv"}

# Security & CORS
CORS_ORIGINS_RAW = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,http://localhost:8501,http://127.0.0.1:3000,http://127.0.0.1:5173,http://127.0.0.1:8501,*")
CORS_ORIGINS: List[str] = [origin.strip() for origin in CORS_ORIGINS_RAW.split(",") if origin.strip()]

# Default Video / Zone Dimensions
DEFAULT_FRAME_WIDTH = int(os.getenv("DEFAULT_FRAME_WIDTH", "832"))
DEFAULT_FRAME_HEIGHT = int(os.getenv("DEFAULT_FRAME_HEIGHT", "464"))

# Reference to Repository Sample Detections CSV
SAMPLE_DETECTIONS_PATH = REPO_ROOT / "tracking" / "data" / "test_detections.csv"


def ensure_directories():
    """Ensure that runtime storage directories exist."""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def is_safe_path(base_dir: Path, target_path: Path) -> bool:
    """Prevent path traversal by verifying target is inside base_dir."""
    try:
        resolved_base = base_dir.resolve()
        resolved_target = target_path.resolve()
        return resolved_base == resolved_target or resolved_base in resolved_target.parents
    except Exception:
        return False
