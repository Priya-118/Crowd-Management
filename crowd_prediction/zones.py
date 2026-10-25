"""Zone layout, zone-wise crowd counts and zone-to-zone movement."""
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
import pandas as pd


@dataclass
class ZoneLayout:
    """Zones as rectangles in normalised image coords (x0, y0, x1, y1) in [0,1]."""
    zones: dict = field(default_factory=lambda: {
        "A": (0, 0, .5, .5), "B": (.5, 0, 1, .5),
        "C": (0, .5, .5, 1), "D": (.5, .5, 1, 1)})

    @property
    def names(self):
        return list(self.zones)

    def masks(self, grid):
        """(n_zones, H, W) boolean masks; a cell belongs to a zone if its centre does."""
        gh, gw = grid
        cy = (np.arange(gh) + .5) / gh
        cx = (np.arange(gw) + .5) / gw
        m = np.zeros((len(self.zones), gh, gw), bool)
        for i, (x0, y0, x1, y1) in enumerate(self.zones.values()):
            m[i] = ((cy[:, None] >= y0) & (cy[:, None] < y1)
                    & (cx[None, :] >= x0) & (cx[None, :] < x1))
        return m

    def assign(self, xn, yn):
        """Zone name per point (normalised coords); '' if outside every zone."""
        out = np.full(len(xn), "", dtype=object)
        for name, (x0, y0, x1, y1) in self.zones.items():
            out[(xn >= x0) & (xn < x1) & (yn >= y0) & (yn < y1)] = name
        return out


def zone_counts_from_density(dens, layout: ZoneLayout, start="10:00:00", dt_s=1.0):
    """Table like  Time | Zone A | Zone B ...  from (T,H,W) density maps."""
    m = layout.masks(dens.shape[-2:]).reshape(len(layout.zones), -1)
    counts = dens.reshape(len(dens), -1) @ m.T.astype(np.float32)
    t0 = pd.Timedelta(start)
    df = pd.DataFrame(counts, columns=layout.names)
    df.insert(0, "time", [str(t0 + pd.Timedelta(seconds=i * dt_s)).split(" ")[-1]
                          for i in range(len(df))])
    df["total"] = counts.sum(1)
    return df


def zone_transitions(tracks: pd.DataFrame, layout: ZoneLayout, frame_size, min_stay=5):
    """Detect zone changes per tracked person  ("Person #17: A -> B at frame 4").

    A zone only counts once the person stays in it for >= min_stay frames, which
    removes flicker when someone stands on a zone border.
    """
    W, H = frame_size
    t = tracks.sort_values(["track_id", "frame"]).copy()
    t["zone"] = layout.assign(t.x.to_numpy() / W, t.y.to_numpy() / H)
    rows = []
    for tid, g in t.groupby("track_id", sort=False):
        z = g.zone.to_numpy(); fr = g.frame.to_numpy()
        change = np.r_[True, z[1:] != z[:-1]]
        starts = np.flatnonzero(change)
        ends = np.r_[starts[1:], len(z)]
        runs = [(z[s], fr[s]) for s, e in zip(starts, ends)
                if z[s] != "" and (e - s) >= min_stay]
        for (za, _), (zb, fb) in zip(runs[:-1], runs[1:]):
            if za != zb:
                rows.append((tid, int(fb), za, zb))
    return pd.DataFrame(rows, columns=["track_id", "frame", "from_zone", "to_zone"])


def transition_matrix(events: pd.DataFrame, layout: ZoneLayout):
    m = pd.crosstab(events.from_zone, events.to_zone)
    return m.reindex(index=layout.names, columns=layout.names, fill_value=0)
