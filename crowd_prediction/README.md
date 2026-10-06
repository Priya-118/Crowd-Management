# Future Crowd Prediction (Member 3)

Branch: `member3-crowd-prediction`.  Run everything from the repository root.

```bash
pip install -r crowd_prediction/requirements.txt
python -m pytest crowd_prediction/tests                 # 10 tests
python -m crowd_prediction.run_pipeline                 # synthetic data, ~6 min on 1 CPU
python -m crowd_prediction.run_pipeline --tracks t.csv --frame-size 1920 1080 --step-frames 30   # real data
```

| File | Purpose | Semester |
|---|---|---|
| `docs/01_research_notes.md` | prediction techniques, spatial/temporal data, ConvLSTM | 1 |
| `docs/02_dataset_spec.md` | dataset structure, storage, splits, hand-off contract | 1 |
| `docs/03_results.md` | baseline vs ConvLSTM results | 1/2 |
| `windows.py`, `storage.py` | storage + train/val/test preparation (chronological, no leakage) | 1 |
| `baselines.py`, `metrics.py` | persistence, moving average, linear trend, historical mean; MAE/RMSE/zone/horizon | 1 |
| `convlstm.py`, `train.py` | Encoder–Decoder ConvLSTM and training loop | 1 (design) / 2 |
| `synthetic.py` | spatio-temporal crowd generator (stand-in for tracker) | 2 |
| `adapters.py` | tracking/detection CSV → density maps | 2 |
| `zones.py`, `analysis.py` | Time\|Zone A\|Zone B table, zone-to-zone movements, plots | 2 |

Generated data/weights go to `crowd_prediction/outputs/` (git-ignored, except figures and results).
