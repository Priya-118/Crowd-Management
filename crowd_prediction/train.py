from __future__ import annotations
import json, time
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import DataLoader


def train_model(model, train_ds, val_ds, t_out, epochs=12, lr=2e-3, batch=32,
                patience=4, out_dir="runs/convlstm", log=print, seed=0):
    torch.manual_seed(seed)
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, factor=.5, patience=1)
    tl = DataLoader(train_ds, batch_size=batch, shuffle=True)   # shuffling windows is fine:
    vl = DataLoader(val_ds, batch_size=64)                      # the split itself was chronological
    hist, best, bad = [], 1e9, 0
    for ep in range(epochs):
        t0 = time.time(); model.train(); tr = []
        tf = max(0.0, .5 * (1 - ep / max(epochs - 1, 1)))        # teacher forcing fades out
        for x, y in tl:
            opt.zero_grad()
            loss = torch.nn.functional.mse_loss(model(x, t_out, y, tf), y)
            loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step(); tr.append(loss.item())
        model.eval(); va = []
        with torch.no_grad():
            for x, y in vl:
                va.append(torch.nn.functional.mse_loss(model(x, t_out), y).item())
        tr_l, va_l = float(np.mean(tr)), float(np.mean(va)); sched.step(va_l)
        hist.append({"epoch": ep + 1, "train_mse": tr_l, "val_mse": va_l})
        log(f"epoch {ep+1:02d}  train {tr_l:.5f}  val {va_l:.5f}  ({time.time()-t0:.0f}s)")
        if va_l < best - 1e-6:
            best, bad = va_l, 0; torch.save(model.state_dict(), out / "best.pt")
        else:
            bad += 1
            if bad >= patience: log("early stop"); break
    model.load_state_dict(torch.load(out / "best.pt"))
    (out / "history.json").write_text(json.dumps(hist, indent=1))
    return model, hist


@torch.no_grad()
def predict(model, X_raw, t_out, scale, batch=64):
    """X_raw (N,t_in,H,W) raw counts -> (N,t_out,H,W) raw counts (clipped >= 0)."""
    model.eval(); res = []
    for i in range(0, len(X_raw), batch):
        x = torch.from_numpy(X_raw[i:i + batch] / scale).float().unsqueeze(2)
        res.append(model(x, t_out).squeeze(2).numpy())
    return np.clip(np.concatenate(res) * scale, 0, None)
