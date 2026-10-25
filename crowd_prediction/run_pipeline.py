"""End-to-end: data -> storage -> zone tables -> splits -> baselines -> ConvLSTM -> report.

    python -m crowd_prediction.run_pipeline                # synthetic data
    python -m crowd_prediction.run_pipeline --tracks my_tracking.csv --frame-size 1920 1080 --step-frames 30
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import torch
from .synthetic import SceneConfig, simulate
from .adapters import load_points_csv, points_to_density
from .zones import ZoneLayout, zone_counts_from_density, zone_transitions, transition_matrix
from .storage import save_dataset, load_dataset
from .windows import chronological_split, Normalizer, make_windows, WindowDataset
from .baselines import BASELINES
from .metrics import evaluate_predictions
from .convlstm import ConvLSTMEncoderDecoder
from .train import train_model, predict
from . import analysis


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tracks", nargs="*", help="tracking/detection CSV(s); omit for synthetic data")
    p.add_argument("--frame-size", nargs=2, type=int, default=[1280, 720])
    p.add_argument("--step-frames", type=int, default=1, help="video frames per time step")
    p.add_argument("--grid", type=int, default=16)
    p.add_argument("--n-recordings", type=int, default=3)
    p.add_argument("--duration", type=int, default=3600)
    p.add_argument("--t-in", type=int, default=8)
    p.add_argument("--t-out", type=int, default=8)
    p.add_argument("--stride", type=int, default=4, help="window stride for training")
    p.add_argument("--epochs", type=int, default=8)
    p.add_argument("--hidden", type=int, default=16)
    p.add_argument("--out", default="crowd_prediction/outputs")
    a = p.parse_args()
    out = Path(out_dir := a.out); (out / "figures").mkdir(parents=True, exist_ok=True)
    grid = (a.grid, a.grid); fsize = tuple(a.frame_size); layout = ZoneLayout()
    data_dir = out / "dataset"

    # 1. data ---------------------------------------------------------------
    recs, tracks_list = [], []
    if a.tracks:
        for f in a.tracks:
            df = load_points_csv(f); tracks_list.append(df)
            recs.append(points_to_density(df, fsize, grid, a.step_frames))
        source = {"type": "csv", "files": a.tracks, "step_frames": a.step_frames}
    else:
        for s in range(a.n_recordings):
            df = simulate(SceneConfig(duration=a.duration, seed=s)); tracks_list.append(df)
            recs.append(points_to_density(df, fsize, grid))
        source = {"type": "synthetic", "seeds": list(range(a.n_recordings))}
    save_dataset(data_dir, recs, {"grid": list(grid), "dt_s": 1.0 if not a.tracks else a.step_frames,
                                  "frame_size": list(fsize), "zones": layout.zones, "source": source})
    recs, meta = load_dataset(data_dir)       # prove the round trip works
    print(f"saved {len(recs)} recordings, shape {recs[0].shape}")

    # 2. zone-wise tables + movement analysis (Semester 2) -------------------
    zt = zone_counts_from_density(recs[0], layout)
    zt.to_csv(out / "zone_counts_rec0.csv", index=False); print(zt.iloc[::600].head(5).to_string(index=False))
    ev = zone_transitions(tracks_list[0], layout, fsize); tm = transition_matrix(ev, layout)
    ev.to_csv(out / "zone_transition_events_rec0.csv", index=False)
    analysis.plot_density_frames(recs[0], [100, 400, 700, 1000], out / "figures/density_frames.png")
    analysis.plot_zone_series(zt, out / "figures/zone_counts.png")
    analysis.plot_transition_matrix(tm, out / "figures/zone_transitions.png")

    # 3. splits -------------------------------------------------------------
    sp = chronological_split(recs)
    norm = Normalizer.fit(sp["train"])
    mean_map = np.concatenate(sp["train"]).mean(0)
    Xte, Yte = make_windows(sp["test"], a.t_in, a.t_out, 1)
    print({k: sum(len(s) for s in v) for k, v in sp.items()}, "test windows:", len(Xte), "scale:", round(norm.scale, 2))

    # 4. baselines ----------------------------------------------------------
    results = {}
    for name, fn in BASELINES.items():
        results[name] = evaluate_predictions(Yte, fn(Xte, a.t_out, mean_map=mean_map), layout, grid)

    # 5. ConvLSTM -----------------------------------------------------------
    torch.set_num_threads(max(1, torch.get_num_threads()))
    tr = WindowDataset(sp["train"], a.t_in, a.t_out, a.stride, norm.scale)
    va = WindowDataset(sp["val"], a.t_in, a.t_out, 3, norm.scale)
    model = ConvLSTMEncoderDecoder(hidden=(a.hidden, a.hidden))
    print(f"ConvLSTM params: {sum(p.numel() for p in model.parameters())}, train windows {len(tr)}")
    model, hist = train_model(model, tr, va, a.t_out, epochs=a.epochs, out_dir=out / "convlstm")
    Yhat = predict(model, Xte, a.t_out, norm.scale)
    results["ConvLSTM"] = evaluate_predictions(Yte, Yhat, layout, grid)
    json.dump({"scale": norm.scale}, open(out / "convlstm/normalizer.json", "w"))

    # 6. report -------------------------------------------------------------
    (out / "results.json").write_text(json.dumps(results, indent=1))
    analysis.plot_horizon_error(results, out / "figures/horizon_error.png")
    i = len(Xte) // 2
    analysis.plot_prediction(Xte[i, -1], Yte[i], {"Persistence": BASELINES["persistence"](Xte[i:i+1], a.t_out)[0],
                                                  "ConvLSTM": Yhat[i]}, out / "figures/prediction_example.png",
                             horizons=(0, a.t_out // 2, a.t_out - 1))
    print(f"\n{'model':18s} {'MAE':>7s} {'RMSE':>7s} {'zoneMAE':>8s} {'totMAE':>7s} {'hotZone':>8s}")
    for n, r in results.items():
        print(f"{n:18s} {r['mae']:7.4f} {r['rmse']:7.4f} {r['zone_mae']:8.3f} {r['total_mae']:7.3f} {r['hottest_zone_acc']:8.3f}")


if __name__ == "__main__":
    main()
