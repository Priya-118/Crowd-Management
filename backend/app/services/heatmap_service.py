import math
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from backend.app.config import (
    DEFAULT_FRAME_HEIGHT,
    DEFAULT_FRAME_WIDTH,
    OUTPUT_DIR,
    is_safe_path,
)
from backend.app.models import Run
from backend.app.schemas import HeatmapResponse, HotspotPoint


def compute_gaussian_density_grid(
    centroids: np.ndarray,
    frame_width: int,
    frame_height: int,
    grid_cols: int = 50,
    grid_rows: int = 30,
    sigma: float = 30.0
) -> Tuple[np.ndarray, float, List[Dict[str, float]]]:
    """
    Computes a 2D Gaussian kernel density grid over frame dimensions.
    Returns: (density_matrix, max_density, top_hotspots)
    """
    if len(centroids) == 0:
        return np.zeros((grid_rows, grid_cols)), 0.0, []

    x_coords = np.linspace(0, frame_width, grid_cols)
    y_coords = np.linspace(0, frame_height, grid_rows)
    xx, yy = np.meshgrid(x_coords, y_coords)

    grid = np.zeros((grid_rows, grid_cols), dtype=float)
    two_sigma_sq = 2.0 * (sigma ** 2)

    for cx, cy in centroids:
        # Distance squared from (cx, cy) to all grid points
        dist_sq = (xx - cx) ** 2 + (yy - cy) ** 2
        # Gaussian kernel
        kernel = np.exp(-dist_sq / two_sigma_sq)
        grid += kernel

    max_val = float(grid.max()) if grid.size > 0 else 0.0
    if max_val > 0:
        norm_grid = grid / max_val
    else:
        norm_grid = grid

    # Identify top hotspot clusters
    hotspots = []
    flat_indices = np.argsort(grid.ravel())[::-1][:5]
    for idx in flat_indices:
        r, c = np.unravel_index(idx, grid.shape)
        if norm_grid[r, c] > 0.05:
            hotspots.append({
                "cx": round(float(x_coords[c]), 1),
                "cy": round(float(y_coords[r]), 1),
                "intensity": round(float(norm_grid[r, c]), 4)
            })

    return norm_grid, max_val, hotspots


def generate_heatmap_for_run(
    run_id: str,
    out_dir: Path,
    width: int = DEFAULT_FRAME_WIDTH,
    height: int = DEFAULT_FRAME_HEIGHT
) -> Optional[Path]:
    """
    Generates a heatmap image (PNG) for the run if centroid data is present.
    Returns the path to the saved PNG or None.
    """
    tracked_csv = out_dir / "tracked_detections.csv"
    if not tracked_csv.exists():
        return None

    try:
        df = pd.read_csv(tracked_csv)
    except Exception:
        return None

    if df.empty or "cx" not in df.columns or "cy" not in df.columns:
        return None

    centroids = df[["cx", "cy"]].dropna().to_numpy(dtype=float)
    if len(centroids) == 0:
        return None

    # Compute grid
    norm_grid, _, _ = compute_gaussian_density_grid(centroids, width, height, grid_cols=80, grid_rows=50)

    # Save PNG using matplotlib
    try:
        import matplotlib
        matplotlib.use("Agg")  # Non-interactive backend
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
        ax.imshow(
            norm_grid,
            extent=[0, width, height, 0],
            cmap="inferno",
            alpha=0.85,
            interpolation="bilinear"
        )
        # Draw 4-zone dividing lines
        ax.axvline(x=width / 2, color="cyan", linestyle="--", linewidth=1.2, label="Zone Boundary X")
        ax.axhline(y=height / 2, color="cyan", linestyle="--", linewidth=1.2, label="Zone Boundary Y")

        # Label quadrants
        ax.text(width * 0.25, height * 0.25, "Zone A", color="white", fontsize=12, fontweight="bold", ha="center")
        ax.text(width * 0.75, height * 0.25, "Zone B", color="white", fontsize=12, fontweight="bold", ha="center")
        ax.text(width * 0.25, height * 0.75, "Zone C", color="white", fontsize=12, fontweight="bold", ha="center")
        ax.text(width * 0.75, height * 0.75, "Zone D", color="white", fontsize=12, fontweight="bold", ha="center")

        ax.set_title("CrowdAhead — Accumulated Spatial Crowd Density Heatmap", fontsize=13, fontweight="bold")
        ax.set_xlabel("Width (px)")
        ax.set_ylabel("Height (px)")
        fig.colorbar(ax.images[0], ax=ax, label="Relative Density (Normalized)")

        plt.tight_layout()
        img_path = out_dir / "heatmap.png"
        fig.savefig(img_path, format="png", bbox_inches="tight")
        plt.close(fig)
        return img_path
    except Exception:
        return None


def get_heatmap_data(db: Session, run_id: str) -> HeatmapResponse:
    """
    Retrieves or calculates heatmap JSON data for a completed run.
    """
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        return HeatmapResponse(
            run_id=run_id,
            status="unavailable",
            message="Run not found."
        )

    if run.status != "completed":
        return HeatmapResponse(
            run_id=run_id,
            status="unavailable",
            message=f"Heatmap data is unavailable because run status is '{run.status}' (expected 'completed')."
        )

    if not run.output_dir:
        return HeatmapResponse(
            run_id=run_id,
            status="unavailable",
            message="Output directory not recorded for this run."
        )

    out_dir = Path(run.output_dir)
    tracked_csv = out_dir / "tracked_detections.csv"

    if not tracked_csv.exists():
        return HeatmapResponse(
            run_id=run_id,
            status="unavailable",
            message="Tracking detections CSV not found in run output."
        )

    try:
        df = pd.read_csv(tracked_csv)
    except Exception as e:
        return HeatmapResponse(
            run_id=run_id,
            status="unavailable",
            message=f"Failed to read tracking detections: {str(e)}"
        )

    if df.empty or "cx" not in df.columns or "cy" not in df.columns:
        return HeatmapResponse(
            run_id=run_id,
            status="unavailable",
            message="No centroid tracking points available to construct density heatmap."
        )

    centroids = df[["cx", "cy"]].dropna().to_numpy(dtype=float)
    if len(centroids) == 0:
        return HeatmapResponse(
            run_id=run_id,
            status="unavailable",
            message="Zero valid centroid coordinates found."
        )

    w = run.video_width or DEFAULT_FRAME_WIDTH
    h = run.video_height or DEFAULT_FRAME_HEIGHT
    grid_cols = 40
    grid_rows = 24

    norm_grid, max_density, hotspots = compute_gaussian_density_grid(
        centroids, w, h, grid_cols=grid_cols, grid_rows=grid_rows
    )

    # Rounded 2D list for clean JSON
    density_matrix = [[round(float(val), 4) for val in row] for row in norm_grid]
    hotspot_objects = [HotspotPoint(**hp) for hp in hotspots]

    img_url = f"/api/runs/{run_id}/heatmap/image" if run.heatmap_image_path and Path(run.heatmap_image_path).exists() else None

    return HeatmapResponse(
        run_id=run_id,
        status="available",
        message="Spatial crowd density heatmap calculated successfully.",
        grid_width=grid_cols,
        grid_height=grid_rows,
        max_density=round(max_density, 4),
        density_grid=density_matrix,
        hotspots=hotspot_objects,
        heatmap_image_url=img_url
    )
