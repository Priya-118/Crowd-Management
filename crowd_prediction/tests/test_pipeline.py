import numpy as np, pandas as pd, torch
from crowd_prediction.synthetic import SceneConfig, simulate
from crowd_prediction.adapters import points_to_density, load_points_csv
from crowd_prediction.zones import ZoneLayout, zone_counts_from_density, zone_transitions
from crowd_prediction.windows import chronological_split, make_windows, Normalizer
from crowd_prediction.baselines import BASELINES
from crowd_prediction.metrics import evaluate_predictions
from crowd_prediction.convlstm import ConvLSTMEncoderDecoder
from crowd_prediction.storage import save_dataset, load_dataset

FS = (1280, 720)


def tracks():
    return simulate(SceneConfig(duration=300, seed=1))


def test_density_preserves_people_count():
    df = tracks(); d = points_to_density(df, FS)
    per_frame = df.groupby("frame").size().reindex(range(len(d)), fill_value=0).to_numpy()
    assert np.allclose(d.sum((1, 2)), per_frame)


def test_step_frames_averages():
    df = pd.DataFrame({"frame": [0, 1, 2, 3], "x": [10] * 4, "y": [10] * 4})
    d = points_to_density(df, FS, step_frames=2)
    assert d.shape[0] == 2 and np.isclose(d[0].sum(), 1.0)


def test_detection_csv(tmp_path):
    p = tmp_path / "det.csv"
    pd.DataFrame({"Frame": [0], "x1": [100], "y1": [100], "x2": [200], "y2": [300]}).to_csv(p, index=False)
    df = load_points_csv(p)
    assert df.x[0] == 150 and df.y[0] == 300      # foot point


def test_zone_counts_sum_to_total():
    d = points_to_density(tracks(), FS); z = zone_counts_from_density(d, ZoneLayout())
    assert np.allclose(z[["A", "B", "C", "D"]].sum(1), d.sum((1, 2)))


def test_person_moves_a_to_b():
    rows = [(f, 17, 100 + (f >= 10) * 700, 100) for f in range(20)]   # Zone A then Zone B
    ev = zone_transitions(pd.DataFrame(rows, columns=["frame", "track_id", "x", "y"]), ZoneLayout(), FS, min_stay=3)
    assert ev.iloc[0].tolist() == [17, 10, "A", "B"]


def test_split_is_chronological_and_windows_stay_inside():
    r = [np.arange(100)[:, None, None].repeat(2, 1).repeat(2, 2).astype(np.float32)]
    sp = chronological_split(r)
    assert sp["train"][0].max() < sp["val"][0].min() and sp["val"][0].max() < sp["test"][0].min()
    X, Y = make_windows(sp["val"], 5, 3)
    assert X.shape[1:] == (5, 2, 2) and Y.shape[1:] == (3, 2, 2)
    assert X.min() >= sp["val"][0].min() and Y.max() <= sp["val"][0].max()


def test_normalizer_fit_on_train_only():
    assert np.isclose(Normalizer.fit([np.ones((10, 2, 2))]).scale, 1.0)


def test_baselines_and_metrics_shapes():
    X = np.random.rand(4, 8, 16, 16).astype(np.float32); Y = np.random.rand(4, 6, 16, 16).astype(np.float32)
    for f in BASELINES.values():
        assert f(X, 6, mean_map=X.mean((0, 1))).shape == Y.shape
    r = evaluate_predictions(Y, Y, ZoneLayout(), (16, 16))
    assert r["mae"] == 0 and r["hottest_zone_acc"] == 1


def test_convlstm_shapes_and_gradients():
    m = ConvLSTMEncoderDecoder(hidden=(4, 4)); x = torch.rand(2, 5, 1, 16, 16)
    y = m(x, 3); assert y.shape == (2, 3, 1, 16, 16)
    y.sum().backward(); assert all(p.grad is not None for p in m.parameters())


def test_storage_roundtrip(tmp_path):
    r = [np.random.rand(10, 4, 4).astype(np.float32)]
    save_dataset(tmp_path, r, {"grid": [4, 4]}); r2, meta = load_dataset(tmp_path)
    assert np.array_equal(r[0], r2[0]) and meta["n_recordings"] == 1
