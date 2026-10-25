"""Plots for analysing crowd movement and model results."""
from __future__ import annotations
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def plot_density_frames(dens, steps, path, title="Crowd density (people per cell)"):
    vmax = dens[steps].max()
    fig, ax = plt.subplots(1, len(steps), figsize=(3 * len(steps), 3.2))
    for a, s in zip(np.atleast_1d(ax), steps):
        im = a.imshow(dens[s], cmap="inferno", vmin=0, vmax=vmax)
        a.set_title(f"t = {s}s  (n={dens[s].sum():.0f})"); a.set_xticks([]); a.set_yticks([])
    fig.suptitle(title); fig.colorbar(im, ax=ax, shrink=.8); fig.savefig(path, dpi=130, bbox_inches="tight"); plt.close(fig)


def plot_zone_series(zone_df, path):
    fig, ax = plt.subplots(figsize=(10, 3.5))
    for z in [c for c in zone_df.columns if c not in ("time", "total")]:
        ax.plot(zone_df[z].to_numpy(), label=f"Zone {z}")
    ax.set_xlabel("time step (s)"); ax.set_ylabel("people"); ax.legend(ncol=4); ax.set_title("Zone-wise crowd over time")
    fig.savefig(path, dpi=130, bbox_inches="tight"); plt.close(fig)


def plot_transition_matrix(tm, path):
    fig, ax = plt.subplots(figsize=(4, 3.6))
    ax.imshow(tm.values, cmap="Blues")
    ax.set_xticks(range(len(tm.columns)), tm.columns); ax.set_yticks(range(len(tm.index)), tm.index)
    for i in range(tm.shape[0]):
        for j in range(tm.shape[1]):
            ax.text(j, i, int(tm.values[i, j]), ha="center", va="center")
    ax.set_xlabel("to zone"); ax.set_ylabel("from zone"); ax.set_title("Zone-to-zone movements")
    fig.savefig(path, dpi=130, bbox_inches="tight"); plt.close(fig)


def plot_horizon_error(results, path):
    fig, ax = plt.subplots(figsize=(6.5, 4))
    for name, r in results.items():
        h = r["per_horizon_mae"]
        ax.plot(range(1, len(h) + 1), h, marker="o", lw=2.5 if name == "ConvLSTM" else 1.2, label=name)
    ax.set_xlabel("steps ahead (s)"); ax.set_ylabel("MAE (people per cell)"); ax.legend(); ax.grid(alpha=.3)
    ax.set_title("Prediction error vs horizon (test set)")
    fig.savefig(path, dpi=130, bbox_inches="tight"); plt.close(fig)


def plot_prediction(x_last, y_true, preds: dict, path, horizons=(0, 4, 7)):
    names = ["Truth"] + list(preds)
    fig, ax = plt.subplots(len(horizons), len(names), figsize=(2.6 * len(names), 2.5 * len(horizons)))
    vmax = max(y_true.max(), 1e-6)
    for r, h in enumerate(horizons):
        for c, n in enumerate(names):
            m = y_true[h] if n == "Truth" else preds[n][h]
            ax[r, c].imshow(m, cmap="inferno", vmin=0, vmax=vmax); ax[r, c].set_xticks([]); ax[r, c].set_yticks([])
            if r == 0: ax[r, c].set_title(n)
            if c == 0: ax[r, c].set_ylabel(f"+{h+1}s")
    fig.savefig(path, dpi=130, bbox_inches="tight"); plt.close(fig)
