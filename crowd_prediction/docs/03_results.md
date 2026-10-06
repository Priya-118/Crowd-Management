# 03 – Baseline vs ConvLSTM results (synthetic data)

Setup: 3 synthetic recordings × 3600 s, 16×16 grid, 8 s of history → 8 s forecast.
Chronological 70/15/15 split per recording; 1575 test windows. ConvLSTM: 2 layers × 16
channels (56,721 parameters), 22 epochs, 1 CPU (~12 min). Reproduce with
`python -m crowd_prediction.run_pipeline --epochs 22`.

| Model | MAE ↓ (people/cell) | RMSE ↓ | Zone-count MAE ↓ | Total-count MAE ↓ | Hottest-zone acc ↑ |
|---|---|---|---|---|---|
| Persistence (copy last map) | **0.343** | 0.726 | 1.98 | **3.15** | 0.974 |
| Moving average (5) | 0.351 | 0.659 | 2.37 | 3.87 | 0.967 |
| Linear trend (5, damped) | 0.505 | 1.035 | 6.49 | 25.4 | 0.943 |
| Historical mean | 0.548 | 1.021 | 15.3 | 34.5 | 0.572 |
| **ConvLSTM** | 0.350 | **0.597** | **1.88** | 3.62 | **0.977** |

## Honest reading
* ConvLSTM has the **lowest RMSE** (−18 % vs persistence), the **lowest zone-count error** (−5 %) and the best hottest-zone accuracy.
* Persistence is still **better on MAE and total count**, and clearly better at +1 s (0.22 vs 0.26). At +8 s the two are almost equal (0.394 vs 0.392). So the model's advantage is modest on this data.
* Why: density maps are mostly near-zero with a few hot cells. Persistence keeps sharp peaks (good for MAE when the crowd barely moves); a model trained with MSE predicts a smoother, hedged map (good for RMSE, see `figures/prediction_example.png`).
* Linear trend and historical mean are poor, which confirms the data has real structure (movement + event cycle) that simple extrapolation cannot capture.
* Only an 8 s horizon with a 16-channel model was tested. Longer horizons (30–60 s, where persistence degrades), a larger model, and extra inputs (time-of-day) are the obvious next experiments.

**Caveat:** synthetic data from our own simulator. These numbers show the *pipeline works and is comparable*, not how it will perform on real CCTV. Re-run on Member 2's real tracks as soon as available.

Figures: `outputs/figures/` (`density_frames`, `zone_counts`, `zone_transitions`, `horizon_error`, `prediction_example`).
