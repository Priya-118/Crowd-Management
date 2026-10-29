import io
import pytest


def test_create_run_with_sample_csv(client):
    """Test creating a run referencing the repository sample detection CSV."""
    response = client.post("/api/runs/test-csv?use_sample=true")
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "uploaded"
    assert data["input_type"] == "csv"
    assert data["original_filename"] == "test_detections.csv"
    assert "id" in data


def test_create_run_with_custom_valid_csv(client):
    """Test creating a run by uploading a custom valid detections CSV."""
    csv_content = (
        "frame,x1,y1,x2,y2,confidence\n"
        "1,100,100,180,300,0.95\n"
        "2,105,102,185,302,0.92\n"
    )
    files = {"file": ("my_detections.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    response = client.post("/api/runs/test-csv", files=files)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "uploaded"
    assert data["original_filename"] == "my_detections.csv"


def test_create_run_with_missing_columns(client):
    """Test uploading a CSV with missing required columns returns 400 Bad Request."""
    invalid_csv = (
        "frame,x1,y1\n"
        "1,100,100\n"
    )
    files = {"file": ("bad_headers.csv", io.BytesIO(invalid_csv.encode("utf-8")), "text/csv")}
    response = client.post("/api/runs/test-csv", files=files)
    assert response.status_code == 400
    assert "Missing required CSV columns" in response.json()["detail"]


def test_create_run_with_non_numeric_data(client):
    """Test uploading a CSV with non-numeric coordinate values returns 400 Bad Request."""
    invalid_csv = (
        "frame,x1,y1,x2,y2,confidence\n"
        "1,one_hundred,100,180,300,0.95\n"
    )
    files = {"file": ("corrupt.csv", io.BytesIO(invalid_csv.encode("utf-8")), "text/csv")}
    response = client.post("/api/runs/test-csv", files=files)
    assert response.status_code == 400
    assert "non-numeric" in response.json()["detail"].lower()


def test_upload_video_invalid_format(client):
    """Test uploading an unsupported file format to video endpoint returns 400."""
    fake_txt = io.BytesIO(b"Hello world")
    files = {"file": ("notes.txt", fake_txt, "text/plain")}
    response = client.post("/api/runs/upload", files=files)
    assert response.status_code == 400
    assert "Unsupported video format" in response.json()["detail"]


def test_upload_video_valid_format(client):
    """Test uploading a valid video format registers an uploaded video run."""
    dummy_mp4 = io.BytesIO(b"\x00\x00\x00 ftypisom\x00\x00\x02\x00isomiso2mp41")
    files = {"file": ("crowd_sample.mp4", dummy_mp4, "video/mp4")}
    response = client.post("/api/runs/upload", files=files)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "uploaded"
    assert data["input_type"] == "video"
    assert data["original_filename"] == "crowd_sample.mp4"


def test_list_runs_and_get_by_id(client):
    """Test listing runs and querying a single run by ID."""
    # Create run
    create_resp = client.post("/api/runs/test-csv?use_sample=true")
    run_id = create_resp.json()["id"]

    # List
    list_resp = client.get("/api/runs")
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["total"] >= 1
    assert any(r["id"] == run_id for r in list_data["runs"])

    # Get by ID
    get_resp = client.get(f"/api/runs/{run_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == run_id

    # Get non-existent
    bad_resp = client.get("/api/runs/non-existent-id")
    assert bad_resp.status_code == 404


def test_process_csv_run_synchronous(client):
    """Test processing a sample CSV run and checking completion state."""
    create_resp = client.post("/api/runs/test-csv?use_sample=true")
    run_id = create_resp.json()["id"]

    process_resp = client.post(f"/api/runs/{run_id}/process?sync=true")
    assert process_resp.status_code == 200
    data = process_resp.json()
    assert data["status"] == "completed"

    # Verify run details updated
    get_resp = client.get(f"/api/runs/{run_id}")
    run_data = get_resp.json()
    assert run_data["status"] == "completed"
    assert run_data["total_frames"] == 5
    assert run_data["peak_crowd_count"] == 2
    assert run_data["total_unique_tracks"] == 2
    assert run_data["has_heatmap"] is True


def test_delete_run(client):
    """Test deleting a run cleans up record and storage."""
    create_resp = client.post("/api/runs/test-csv?use_sample=true")
    run_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/runs/{run_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["run_id"] == run_id

    # Query should now return 404
    get_resp = client.get(f"/api/runs/{run_id}")
    assert get_resp.status_code == 404

    # Delete non-existent
    del_non_existent = client.delete(f"/api/runs/{run_id}")
    assert del_non_existent.status_code == 404
