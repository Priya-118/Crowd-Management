"""Baseline predictors. All take X (N, t_in, H, W) raw counts and return
predictions (N, t_out, H, W). Any ML model must beat these to be worth using."""
from __future__ import annotations
import numpy as np


def persistence(X, t_out, **_):
    """Future = last observed frame (hardest simple baseline for short horizons)."""
    return np.repeat(X[:, -1:], t_out, axis=1)


def moving_average(X, t_out, k=5, **_):
    """Future = mean of the last k frames."""
    return np.repeat(X[:, -k:].mean(1, keepdims=True), t_out, axis=1)


def linear_trend(X, t_out, k=5, damping=.9, **_):
    """Fit a straight line per cell over the last k frames and extrapolate,
    with damping so the trend fades out instead of exploding."""
    t = np.arange(k) - (k - 1) / 2
    last = X[:, -k:]
    slope = (last * t[None, :, None, None]).sum(1) / (t ** 2).sum()
    level = last.mean(1) + slope * (k - 1) / 2          # value at the last frame
    steps = np.cumsum(damping ** np.arange(1, t_out + 1))
    return np.clip(level[:, None] + slope[:, None] * steps[None, :, None, None], 0, None)


def historical_mean(X, t_out, mean_map=None, **_):
    """Future = average crowd map seen in training (ignores the input entirely)."""
    return np.broadcast_to(mean_map, (len(X), t_out) + mean_map.shape).copy()


BASELINES = {
    "persistence": persistence,
    "moving_avg_5": lambda X, t_out, **kw: moving_average(X, t_out, k=5),
    "linear_trend_5": lambda X, t_out, **kw: linear_trend(X, t_out, k=5),
    "historical_mean": historical_mean,
}
