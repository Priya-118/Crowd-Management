"""How historical crowd maps are stored on disk.

  data/processed/<name>/
      meta.json          grid, dt_s, units, zone layout, source info
      rec_000.npy ...    float32 array (T, H, W) per recording, raw people-per-cell
      zone_counts_000.csv  (optional) Time | A | B | C | D | total
Raw counts are stored; normalisation is applied later and fitted on train only.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np


def save_dataset(root, recordings, meta: dict):
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    for i, r in enumerate(recordings):
        np.save(root / f"rec_{i:03d}.npy", r.astype(np.float32))
    meta = dict(meta, n_recordings=len(recordings),
                shape_per_recording=[list(r.shape) for r in recordings],
                array_layout="(T, H, W) people per cell")
    (root / "meta.json").write_text(json.dumps(meta, indent=2))


def load_dataset(root):
    root = Path(root)
    meta = json.loads((root / "meta.json").read_text())
    recs = [np.load(root / f"rec_{i:03d}.npy") for i in range(meta["n_recordings"])]
    return recs, meta
