# 02 – Dataset structure, storage, and hand-off contract

## Canonical representation
| Item | Value |
|---|---|
| One recording | `float32` array `(T, H, W)`, **people per cell** (raw counts, not normalised) |
| Grid | default 16×16 over the full camera frame (configurable) |
| Time step | `dt` seconds; default 1 s (`--step-frames` = fps for real video) |
| Zones | rectangles in normalised image coords, default 2×2 quadrants A,B (top), C,D (bottom) |
| Model tensors | `(batch, T, 1, H, W)`, values divided by a train-fitted scale |

## On-disk layout (`storage.py`)
```
crowd_prediction/outputs/dataset/
    meta.json        grid, dt_s, frame_size, zones, source (synthetic seeds or CSV files)
    rec_000.npy …    one file per recording / camera session
zone_counts_rec0.csv   Time | A | B | C | D | total          (Semester-2 table)
zone_transition_events_rec0.csv   track_id | frame | from_zone | to_zone
```
Large generated files stay out of git (see `.gitignore`).

## Splits (`windows.py`)
* **Chronological per recording:** first 70 % train, next 15 % validation, last 15 % test. Never shuffled before splitting (shuffling would leak the future).
* Windows (`t_in=8` past → `t_out=8` future, stride 1) are cut *inside* a split, so no window straddles train/val/test.
* Normalisation scale (99.9th percentile of train) is fitted on **train only**, saved to `normalizer.json`.
* With several recordings, hold out whole recordings for a stricter test of generalisation (recommended once real data exists).

## Hand-off contract with the other members
**From Member 1/2 → Member 3.** Any ONE of these CSVs is enough:

1. Tracking (preferred): `frame, track_id, x, y` – pixel coordinates of the foot point
   (bottom-centre of the box).
2. Detections only: `frame, x1, y1, x2, y2[, conf]` – IDs not required for prediction.

Also needed: frame width × height, video fps. Then:
```
python -m crowd_prediction.run_pipeline --tracks a.csv b.csv --frame-size 1920 1080 --step-frames 30
```
(`step-frames` = fps → one density map per second.)

**From Member 3 → Member 4 (Risk):** predicted `(t_out, H, W)` maps and the derived
zone-count table, via `train.predict(...)` + `zones.zone_counts_from_density(...)`.

## Known limitations
* Grid is in **image** space; perspective makes far cells cover more ground. A homography to a ground plane would fix this; the grid code would not change.
* Synthetic data has a clean repeating schedule – real data will be noisier, so real-data numbers will be worse than the synthetic ones.
* Camera must be fixed (no pan/zoom).
