"""Train / validation / test preparation for sequence prediction."""
from __future__ import annotations
import numpy as np
import torch
from torch.utils.data import Dataset


def chronological_split(recordings, ratios=(.7, .15, .15)):
    """Split EACH recording in time order: first 70% train, next 15% val, last 15% test.

    Random shuffling of frames would leak the future into training, so we never
    shuffle before splitting. Windows are cut inside a segment, so no window
    ever straddles two splits.
    """
    out = {"train": [], "val": [], "test": []}
    for r in recordings:
        T = len(r); a = int(T * ratios[0]); b = int(T * (ratios[0] + ratios[1]))
        out["train"].append(r[:a]); out["val"].append(r[a:b]); out["test"].append(r[b:])
    return out


class Normalizer:
    """x_norm = x / scale, scale fitted on TRAIN data only (99.9th percentile)."""
    def __init__(self, scale=1.0): self.scale = float(scale)
    @classmethod
    def fit(cls, train_segments):
        return cls(max(np.percentile(np.concatenate([s.ravel() for s in train_segments]), 99.9), 1e-6))
    def transform(self, x): return x / self.scale
    def inverse(self, x): return x * self.scale


def make_windows(segments, t_in, t_out, stride=1):
    """Raw numpy windows: X (N,t_in,H,W), Y (N,t_out,H,W)."""
    X, Y = [], []
    for s in segments:
        for i in range(0, len(s) - t_in - t_out + 1, stride):
            X.append(s[i:i + t_in]); Y.append(s[i + t_in:i + t_in + t_out])
    return np.stack(X), np.stack(Y)


class WindowDataset(Dataset):
    """Returns (x, y) tensors shaped (T, 1, H, W) with values divided by `scale`."""
    def __init__(self, segments, t_in, t_out, stride=1, scale=1.0):
        self.X, self.Y = make_windows(segments, t_in, t_out, stride)
        self.X = torch.from_numpy(self.X / scale).float().unsqueeze(2)
        self.Y = torch.from_numpy(self.Y / scale).float().unsqueeze(2)
    def __len__(self): return len(self.X)
    def __getitem__(self, i): return self.X[i], self.Y[i]
