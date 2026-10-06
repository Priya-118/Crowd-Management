from __future__ import annotations
import numpy as np


def evaluate_predictions(Y, Yhat, layout, grid):
    """Y, Yhat: (N, t_out, H, W) raw counts. Returns a dict of metrics.

    mae/rmse         : per cell (people per cell)
    per_horizon_mae  : error as the prediction looks further ahead
    zone_mae         : error of the people count of each zone (what the risk
                       module and the Time|ZoneA|ZoneB table care about)
    total_mae        : error of the total people in the scene
    hottest_zone_acc : how often the most crowded future zone is identified
    """
    Yhat = np.clip(Yhat, 0, None)
    err = Yhat - Y
    m = layout.masks(grid).reshape(len(layout.zones), -1).astype(np.float64)
    zy = Y.reshape(*Y.shape[:2], -1) @ m.T          # (N, t_out, Z)
    zp = Yhat.reshape(*Yhat.shape[:2], -1) @ m.T
    return {
        "mae": float(np.abs(err).mean()),
        "rmse": float(np.sqrt((err ** 2).mean())),
        "per_horizon_mae": np.abs(err).mean((0, 2, 3)).tolist(),
        "zone_mae": float(np.abs(zp - zy).mean()),
        "zone_mae_by_zone": dict(zip(layout.names, np.abs(zp - zy).mean((0, 1)).tolist())),
        "total_mae": float(np.abs(zp.sum(2) - zy.sum(2)).mean()),
        "hottest_zone_acc": float((zp.argmax(2) == zy.argmax(2)).mean()),
    }
