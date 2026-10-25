"""Synthetic spatio-temporal crowd generator.

Stand-in for Member 2's tracker until real data exists. It simulates people
who enter the scene, walk to a destination zone (A/B/C/D), dwell there, then
leave. Destination preferences change over a repeating cycle (an "event" pulls
people towards Zone B), so crowd density really does move around over time.

The output is a *tracking table* in exactly the format the real tracker should
export (frame, track_id, x, y in pixels), so the same adapters are used for
synthetic and real data.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd

ZONE_CENTERS = np.array([[.25, .25], [.75, .25], [.25, .75], [.75, .75]])  # A,B,C,D


@dataclass
class SceneConfig:
    duration: int = 3600          # number of time steps (1 step = 1 second)
    frame_size: tuple = (1280, 720)   # (width, height) in pixels
    base_rate: float = 1.2        # mean arrivals per step
    dwell_mean: float = 90.0      # mean dwell time (steps) at the destination
    speed: float = 0.03           # walking speed, fraction of scene per step
    cycle: int = 900              # length of the repeating behaviour cycle
    seed: int = 0


def simulate(cfg: SceneConfig) -> pd.DataFrame:
    rng = np.random.default_rng(cfg.seed)
    W, H = cfg.frame_size
    offset = int(rng.integers(0, cfg.cycle))
    # destination probabilities per phase (A,B,C,D) + arrival-rate multiplier
    probs = np.array([[.40, .20, .20, .20],     # phase 0: A is popular
                      [.10, .70, .10, .10],     # phase 1: event at B
                      [.15, .15, .35, .35]])    # phase 2: C/D popular
    probs = probs * rng.uniform(.85, 1.15, probs.shape)
    probs /= probs.sum(1, keepdims=True)
    mult = np.array([1.0, 1.6, 0.8]) * rng.uniform(.9, 1.1, 3)

    pos = np.zeros((0, 2)); anchor = np.zeros((0, 2)); target = np.zeros((0, 2))
    state = np.zeros(0, int); dwell = np.zeros(0); ids = np.zeros(0, int)
    spd = np.zeros(0)
    next_id = 0
    out = []
    for t in range(cfg.duration):
        phase = ((t + offset) // (cfg.cycle // 3)) % 3
        n_new = rng.poisson(cfg.base_rate * mult[phase] * rng.lognormal(0, .15))
        if n_new:
            left = rng.random(n_new) < .5
            p = np.where(left[:, None],
                         np.c_[np.zeros(n_new), rng.uniform(.3, .7, n_new)],
                         np.c_[rng.uniform(.3, .7, n_new), np.ones(n_new) - 1e-3])
            dest = rng.choice(4, size=n_new, p=probs[phase])
            a = np.clip(ZONE_CENTERS[dest] + rng.normal(0, .07, (n_new, 2)), .02, .98)
            pos = np.vstack([pos, p]); anchor = np.vstack([anchor, a])
            target = np.vstack([target, a])
            state = np.r_[state, np.zeros(n_new, int)]
            dwell = np.r_[dwell, np.zeros(n_new)]
            ids = np.r_[ids, np.arange(next_id, next_id + n_new)]
            spd = np.r_[spd, cfg.speed * rng.uniform(.7, 1.3, n_new)]
            next_id += n_new
        if len(pos):
            vec = target - pos
            dist = np.linalg.norm(vec, axis=1)
            arrived = dist < spd
            move = (vec / np.maximum(dist, 1e-9)[:, None]) * spd[:, None]
            walking = (state != 1)
            pos = np.where(walking[:, None],
                           np.where(arrived[:, None], target, pos + move)
                           + rng.normal(0, .003, pos.shape), pos)
            # arrive at destination -> start dwelling
            s0 = (state == 0) & arrived
            state[s0] = 1
            dwell[s0] = rng.geometric(1 / cfg.dwell_mean, s0.sum())
            # dwelling: jitter around anchor
            d = state == 1
            pos[d] += rng.normal(0, .006, (d.sum(), 2)) + .1 * (anchor[d] - pos[d])
            dwell[d] -= 1
            leave = d & (dwell <= 0)
            if leave.any():
                state[leave] = 2
                q = pos[leave]
                edges = np.c_[q[:, 0], q[:, 1], 1 - q[:, 0], 1 - q[:, 1]]
                k = edges.argmin(1)
                tgt = q.copy()
                tgt[k == 0, 0] = 0; tgt[k == 1, 1] = 0
                tgt[k == 2, 0] = 1; tgt[k == 3, 1] = 1
                target[leave] = tgt
            pos = np.clip(pos, 0, 1 - 1e-6)
            out.append(np.c_[np.full(len(pos), t), ids, pos[:, 0] * W, pos[:, 1] * H])
            gone = (state == 2) & arrived
            keep = ~gone
            pos, anchor, target, state, dwell, ids, spd = (
                pos[keep], anchor[keep], target[keep], state[keep],
                dwell[keep], ids[keep], spd[keep])
    df = pd.DataFrame(np.vstack(out), columns=["frame", "track_id", "x", "y"])
    return df.astype({"frame": int, "track_id": int})
