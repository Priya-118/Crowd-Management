import pytest


def test_metrics_endpoints_before_processing(client):
    """Test metrics and timeseries endpoints return 400 when run is not completed."""
    create_resp = client.post("/api/runs/test-csv?use_sample=true")
    run_id = create_resp.json()["id"]

    # Metrics before completion
    m_resp = client.get(f"/api/runs/{run_id}/metrics")
    assert m_resp.status_code == 400
    assert "only available for 'completed' runs" in m_resp.json()["detail"]

    # Timeseries before completion
    ts_resp = client.get(f"/api/runs/{run_id}/timeseries")
    assert ts_resp.status_code == 400

    # Heatmap before completion returns explicit unavailable status
    hm_resp = client.get(f"/api/runs/{run_id}/heatmap")
    assert hm_resp.status_code == 200
    assert hm_resp.json()["status"] == "unavailable"


def test_metrics_and_timeseries_after_processing(client):
    """Test summary metrics and time-series endpoints after pipeline completes."""
    create_resp = client.post("/api/runs/test-csv?use_sample=true")
    run_id = create_resp.json()["id"]

    # Process synchronously
    proc_resp = client.post(f"/api/runs/{run_id}/process?sync=true")
    assert proc_resp.status_code == 200
    assert proc_resp.json()["status"] == "completed"

    # 1. Summary Metrics
    m_resp = client.get(f"/api/runs/{run_id}/metrics")
    assert m_resp.status_code == 200
    metrics = m_resp.json()
    assert metrics["run_id"] == run_id
    assert metrics["total_frames"] == 5
    assert metrics["peak_crowd_count"] == 2
    assert metrics["total_unique_tracks"] == 2
    assert metrics["zone_totals"]["Zone_A"] == 10  # 2 people * 5 frames in Zone A
    assert "crowd_density_note" in metrics

    # 2. Time-series
    ts_resp = client.get(f"/api/runs/{run_id}/timeseries")
    assert ts_resp.status_code == 200
    ts_data = ts_resp.json()
    assert ts_data["total_frames"] == 5
    assert len(ts_data["frames"]) == 5
    first_frame = ts_data["frames"][0]
    assert first_frame["frame"] == 1
    assert first_frame["total_people"] == 2
    assert first_frame["zones"]["Zone_A"] == 2


def test_heatmap_data_and_image(client):
    """Test heatmap JSON and image streaming endpoints."""
    create_resp = client.post("/api/runs/test-csv?use_sample=true")
    run_id = create_resp.json()["id"]

    client.post(f"/api/runs/{run_id}/process?sync=true")

    # Heatmap JSON data
    hm_resp = client.get(f"/api/runs/{run_id}/heatmap")
    assert hm_resp.status_code == 200
    hm_data = hm_resp.json()
    assert hm_data["status"] == "available"
    assert hm_data["grid_width"] == 40
    assert hm_data["grid_height"] == 24
    assert len(hm_data["density_grid"]) == 24
    assert len(hm_data["density_grid"][0]) == 40
    assert len(hm_data["hotspots"]) > 0

    # Heatmap Image Stream
    img_resp = client.get(f"/api/runs/{run_id}/heatmap/image")
    assert img_resp.status_code == 200
    assert img_resp.headers["content-type"] == "image/png"
    assert len(img_resp.content) > 1000  # Valid PNG image bytes


def test_video_endpoint_on_csv_run(client):
    """Test requesting video on a CSV run returns 404 with clear explanatory message."""
    create_resp = client.post("/api/runs/test-csv?use_sample=true")
    run_id = create_resp.json()["id"]

    v_resp = client.get(f"/api/runs/{run_id}/video")
    assert v_resp.status_code == 404
    assert "input was a detection CSV" in v_resp.json()["detail"]
