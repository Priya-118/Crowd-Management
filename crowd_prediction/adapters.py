"""Convert tracker / detector output into density maps.

Agreed input contract (see docs/02_dataset_spec.md):
  tracking CSV  : frame, track_id, x, y            (pixels, foot point)
  detection CSV : frame, x1, y1, x2, y2 [, conf]   (pixels, one row per box)
Density maps do NOT need track IDs, so prediction is not blocked by tracking.
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def load_points_csv(path) -> pd.DataFrame:
    """Load a tracking or detection CSV into columns frame, x, y (+track_id)."""
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    if {"x1", "y1", "x2", "y2"} <= set(df.columns) and "x" not in df.columns:
        df["x"] = (df.x1 + df.x2) / 2          # horizontal centre of the box
        df["y"] = df.y2                        # bottom edge = foot point on ground
    missing = {"frame", "x", "y"} - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing columns: {sorted(missing)}")
    return df


def points_to_density(df: pd.DataFrame, frame_size, grid=(16, 16),
                      step_frames: int = 1, smooth_sigma: float = 0.0) -> np.ndarray:
    """Return (T, H, W) array: average number of people in each grid cell per time step.

    step_frames : video frames merged into one time step (e.g. fps -> 1 second).
    Units are 'people per cell', so the sum over cells = people in the scene.
    """
    W, Hpx = frame_size
    gh, gw = grid
    f0, f1 = int(df.frame.min()), int(df.frame.max())
    n_frames = f1 - f0 + 1
    T = int(np.ceil(n_frames / step_frames))
    t = ((df.frame.to_numpy() - f0) // step_frames).astype(int)
    col = np.clip((df.x.to_numpy() / W * gw).astype(int), 0, gw - 1)
    row = np.clip((df.y.to_numpy() / Hpx * gh).astype(int), 0, gh - 1)
    flat = np.bincount((t * gh + row) * gw + col, minlength=T * gh * gw)
    dens = flat.reshape(T, gh, gw).astype(np.float32)
    frames_in_bin = np.minimum(step_frames, n_frames - np.arange(T) * step_frames)
    dens /= frames_in_bin[:, None, None]
    if smooth_sigma > 0:                       # optional; mass is not exactly kept at borders
        from scipy.ndimage import gaussian_filter
        dens = np.stack([gaussian_filter(d, smooth_sigma, mode="nearest") for d in dens])
    return dens
