# 01 – Research notes: crowd prediction, spatial/temporal data, ConvLSTM

> Member 3, Semester 1. Citations are from memory of well-known papers – verify
> titles/years before putting them in a report.

## 1. What problem are we solving?
Given the last `t_in` crowd-density maps, predict the next `t_out` maps.
A **crowd-density map** is a grid laid over the camera view where each cell holds
the number of people in it. Total people = sum of cells.

## 2. Families of crowd-prediction methods
| Family | Idea | Pros | Cons |
|---|---|---|---|
| Statistical time series (ARIMA, exponential smoothing) | Forecast each zone's count separately | Simple, fast, interpretable | Ignores space: cannot see people walking from Zone A to B |
| Trajectory-based (Social Force, Social-LSTM – Alahi et al. 2016) | Predict each person's path | Individual-level detail | Breaks in dense crowds, needs perfect tracking/ID continuity |
| **Grid / density-map based (ConvLSTM, ST-ResNet – Zhang et al. 2017)** | Treat the crowd as an image sequence | Works with imperfect tracking, scales to dense crowds, outputs exactly what Risk module needs | Needs enough data; loses individual identities |
| Graph-based (ST-GCN, DCRNN-style) | Zones are nodes, edges = walkways | Natural for zone networks | Needs a graph definition; more engineering |

**Decision:** density-map + Encoder–Decoder ConvLSTM, as in the project README.
Zone-level counts (Time | Zone A | Zone B …) are *derived* from the predicted maps
by summing cells, so one model serves both the map and the zone table.

## 3. Spatial vs temporal data
* **Spatial:** neighbouring cells are correlated (a crowd occupies a blob, not random cells). A plain LSTM on flattened maps throws this structure away.
* **Temporal:** crowd at *t+1* depends on *t, t-1…* (momentum, queues, event schedules, daily cycles).
* A video of density maps is a tensor `(T, H, W)`; for the model `(batch, T, channels, H, W)`.

## 4. ConvLSTM in plain words
A normal LSTM has gates computed with matrix multiplications on vectors. **ConvLSTM
(Shi et al., NeurIPS 2015, developed for rain "nowcasting")** computes the same
gates with **convolutions**, so memory `c` and hidden state `h` are *maps*.

```
i = σ(W_i * [x, h] + b_i)     input gate
f = σ(W_f * [x, h] + b_f)     forget gate
o = σ(W_o * [x, h] + b_o)     output gate
g = tanh(W_g * [x, h] + b_g)  candidate
c' = f ⊙ c + i ⊙ g            cell memory (a map)
h' = o ⊙ tanh(c')             hidden state (a map)       (* = convolution)
```
Because kernels are local, the model learns *motion*: "mass at the left edge of
Zone A tends to appear one cell further right next second".

**Encoder–Decoder:** encoder consumes the past; its final `(h, c)` initialise the
decoder, which rolls out the future one step at a time, feeding its own output
back. (Our `convlstm.py`: 2 layers, 3×3 kernels, 1×1 conv head, residual output –
the net predicts the *change* from the previous map, which is much easier than
re-drawing the whole map.)

**Known weaknesses to mention in the report:** blurry long-horizon predictions
(MSE averages possible futures), error accumulation in autoregressive rollout
(mitigated by teacher forcing during training), needs lots of data. Possible
upgrades: PredRNN/ST-LSTM, attention, adding time-of-day as an extra channel.

## 5. Related: how density maps are obtained
Real systems either (a) place detected/tracked foot points on a grid (what we do,
works with the YOLO + ByteTrack output) or (b) regress density maps directly from
images (MCNN, CSRNet) – better for very dense crowds where detection fails.
Option (b) can be swapped in later without changing anything downstream, because
the interface is just a `(T, H, W)` array.

## 6. Evaluation thinking
* Per-cell **MAE/RMSE** – map accuracy.
* **Zone-count MAE** and **total-count MAE** – what operators/Risk module care about.
* **Per-horizon error** – prediction always gets worse further ahead; report the curve.
* **Hottest-zone accuracy** – does the model flag the right zone to worry about?
* Always compare with baselines; a deep model that loses to "copy the last frame"
  is not useful.
