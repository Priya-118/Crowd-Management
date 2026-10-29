import io
import os
import subprocess
import sys
from pathlib import Path
import pytest

from backend.app.config import REPO_ROOT
from backend.app.services.detector_adapter import (
    check_detector_prerequisites,
    execute_person_detection,
    get_detector_python_path,
    set_detector_runner,
)


@pytest.fixture(autouse=True)
def cleanup_detector_runner(monkeypatch):
    """Ensure detector runner and environment variables are reset after every test."""
    yield
    set_detector_runner(None)
    monkeypatch.delenv("CROWDAHEAD_DETECTOR_PYTHON", raising=False)


# ---------------------------------------------------------------------------
# 1. Interpreter Selection Tests
# ---------------------------------------------------------------------------

def test_get_detector_python_path_env_override(monkeypatch):
    """Test that CROWDAHEAD_DETECTOR_PYTHON overrides all default paths."""
    custom_python = "C:\\CustomEnv\\Scripts\\python.exe"
    monkeypatch.setenv("CROWDAHEAD_DETECTOR_PYTHON", custom_python)
    selected = get_detector_python_path()
    assert selected == Path(custom_python)


def test_get_detector_python_path_prefers_venv(monkeypatch):
    """Test that project-root .venv-yolo is preferred when it exists."""
    monkeypatch.delenv("CROWDAHEAD_DETECTOR_PYTHON", raising=False)
    expected_venv = REPO_ROOT / ".venv-yolo" / "Scripts" / "python.exe"
    if expected_venv.is_file():
        selected = get_detector_python_path()
        assert selected == expected_venv


def test_get_detector_python_path_fallback_when_venv_missing(monkeypatch, tmp_path):
    """Test fallback to sys.executable when .venv-yolo is unavailable."""
    monkeypatch.setattr("backend.app.services.detector_adapter.REPO_ROOT", tmp_path)
    monkeypatch.delenv("CROWDAHEAD_DETECTOR_PYTHON", raising=False)
    selected = get_detector_python_path()
    assert selected == Path(sys.executable)


# ---------------------------------------------------------------------------
# 2. Prerequisite Check Tests
# ---------------------------------------------------------------------------

def test_check_detector_prerequisites_missing_interpreter(tmp_path):
    """Test prerequisite check flags a non-existent Python interpreter."""
    non_existent = tmp_path / "missing_python.exe"
    ok, err = check_detector_prerequisites(python_path=non_existent)
    assert ok is False
    assert err is not None
    assert "Detector Python interpreter not found" in err


def test_check_detector_prerequisites_missing_torch_in_interpreter():
    """Test prerequisite check flags missing PyTorch in the current host interpreter."""
    # Current host Python 3.14 does not have torch installed
    ok, err = check_detector_prerequisites(python_path=Path(sys.executable))
    assert ok is False
    assert err is not None
    assert "PyTorch ('torch') is not importable" in err


def test_check_detector_prerequisites_success_with_yolo_env():
    """Test prerequisite check succeeds when .venv-yolo and model weights are present."""
    venv_py = REPO_ROOT / ".venv-yolo" / "Scripts" / "python.exe"
    weights = REPO_ROOT / "person_detection" / "yolov5" / "yolov5s.pt"
    yolo_dir = REPO_ROOT / "person_detection" / "yolov5"

    if venv_py.is_file() and weights.is_file() and yolo_dir.is_dir():
        ok, err = check_detector_prerequisites(
            python_path=venv_py,
            yolov5_dir=yolo_dir,
            weights_path=weights,
        )
        assert ok is True
        assert err is None


def test_check_detector_prerequisites_missing_files(tmp_path):
    """Test prerequisite checking flags missing weights or yolov5 dir."""
    non_existent_yolo = tmp_path / "yolov5"
    non_existent_weights = tmp_path / "yolov5s.pt"
    dummy_video = tmp_path / "test.mp4"
    dummy_video.write_bytes(b"dummy video data")

    # Pass python_path pointing to venv if it exists, otherwise sys.executable
    venv_py = REPO_ROOT / ".venv-yolo" / "Scripts" / "python.exe"
    target_py = venv_py if venv_py.is_file() else Path(sys.executable)

    ok, err = check_detector_prerequisites(
        video_path=dummy_video,
        yolov5_dir=non_existent_yolo,
        weights_path=non_existent_weights,
        python_path=target_py,
    )
    assert ok is False
    assert err is not None
    assert any(term in err for term in ["PyTorch", "OpenCV", "YOLOv5", "weights"])


def test_check_detector_prerequisites_missing_video(tmp_path):
    """Test prerequisite checking when video does not exist."""
    missing_video = tmp_path / "does_not_exist.mp4"
    venv_py = REPO_ROOT / ".venv-yolo" / "Scripts" / "python.exe"
    weights = REPO_ROOT / "person_detection" / "yolov5" / "yolov5s.pt"
    yolo_dir = REPO_ROOT / "person_detection" / "yolov5"

    if venv_py.is_file() and weights.is_file() and yolo_dir.is_dir():
        ok, err = check_detector_prerequisites(
            video_path=missing_video,
            python_path=venv_py,
            yolov5_dir=yolo_dir,
            weights_path=weights,
        )
        assert ok is False
        assert err is not None
        assert "Input video file not found" in err


# ---------------------------------------------------------------------------
# 3. Subprocess Execution & Pipeline Tests
# ---------------------------------------------------------------------------

def test_execute_person_detection_invokes_selected_interpreter(monkeypatch, tmp_path):
    """Test that execute_person_detection passes the selected interpreter as cmd[0]."""
    recorded_cmd = []

    def mock_subprocess_run(cmd, *args, **kwargs):
        recorded_cmd.extend(cmd)
        # Create output files so it considers detection successful
        out_csv = Path(cmd[cmd.index("--output-csv") + 1])
        out_csv.write_text("frame,x1,y1,x2,y2,confidence\n", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, stdout="Detection completed.", stderr="")

    # Mock prerequisite check to return success
    monkeypatch.setattr(
        "backend.app.services.detector_adapter.check_detector_prerequisites",
        lambda **kwargs: (True, None)
    )
    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)

    custom_py = tmp_path / "custom_python.exe"
    custom_py.touch()

    vid_path = tmp_path / "video.mp4"
    vid_path.write_bytes(b"video")
    out_csv = tmp_path / "detections.csv"
    out_vid = tmp_path / "annotated.mp4"

    ok, err = execute_person_detection(
        video_path=vid_path,
        output_csv_path=out_csv,
        output_video_path=out_vid,
        python_path=custom_py,
    )

    assert ok is True
    assert err is None
    assert recorded_cmd[0] == str(custom_py.resolve())
    assert "--input" in recorded_cmd
    assert "--output-video" in recorded_cmd
    assert "--output-csv" in recorded_cmd


def test_video_run_fails_gracefully_when_prerequisites_missing(client, monkeypatch):
    """Test that video processing fails gracefully and preserves raw video when YOLO prerequisites are missing."""
    # Force use of sys.executable where PyTorch is not installed
    monkeypatch.setenv("CROWDAHEAD_DETECTOR_PYTHON", str(sys.executable))

    dummy_mp4 = io.BytesIO(b"\x00\x00\x00 ftypisom\x00\x00\x02\x00isomiso2mp41")
    files = {"file": ("test_surveillance.mp4", dummy_mp4, "video/mp4")}

    upload_resp = client.post("/api/runs/upload", files=files)
    assert upload_resp.status_code == 201
    run_id = upload_resp.json()["id"]

    # Process synchronously without mock runner
    proc_resp = client.post(f"/api/runs/{run_id}/process?sync=true")
    assert proc_resp.status_code == 200
    assert proc_resp.json()["status"] == "failed"

    # Query run status
    run_resp = client.get(f"/api/runs/{run_id}")
    run_data = run_resp.json()
    assert run_data["status"] == "failed"
    assert run_data["has_video"] is False
    assert run_data["has_raw_video"] is True
    assert "Prerequisite missing" in run_data["error_details"]

    # Raw video endpoint should succeed because raw uploaded video is preserved
    raw_resp = client.get(f"/api/runs/{run_id}/raw-video")
    assert raw_resp.status_code == 200
    assert len(raw_resp.content) > 0

    # Annotated video endpoint should return 404 because detection never finished
    annotated_resp = client.get(f"/api/runs/{run_id}/video")
    assert annotated_resp.status_code == 404


def test_video_run_success_with_mocked_detector(client):
    """Test complete video processing pipeline when detector produces detections and annotated video."""
    def mock_runner(video_path, output_csv_path, output_video_path, yolov5_dir, weights_path):
        output_csv_path.parent.mkdir(parents=True, exist_ok=True)
        output_video_path.parent.mkdir(parents=True, exist_ok=True)
        # Write 5 frames of detections
        csv_content = (
            "frame,x1,y1,x2,y2,confidence\n"
            "1,100,100,180,300,0.95\n"
            "1,400,200,480,400,0.91\n"
            "2,105,102,185,302,0.94\n"
            "2,402,205,482,405,0.89\n"
            "3,110,105,190,305,0.96\n"
            "4,115,108,195,308,0.93\n"
            "5,120,110,200,310,0.95\n"
        )
        output_csv_path.write_text(csv_content, encoding="utf-8")
        output_video_path.write_bytes(b"\x00\x00\x00 fake_annotated_mp4")
        return True, None

    set_detector_runner(mock_runner)

    # Upload video
    dummy_mp4 = io.BytesIO(b"\x00\x00\x00 ftypisom\x00\x00\x02\x00isomiso2mp41")
    files = {"file": ("camera_ch01.mp4", dummy_mp4, "video/mp4")}
    upload_resp = client.post("/api/runs/upload", files=files)
    assert upload_resp.status_code == 201
    run_id = upload_resp.json()["id"]

    # Process synchronously
    proc_resp = client.post(f"/api/runs/{run_id}/process?sync=true")
    assert proc_resp.status_code == 200
    assert proc_resp.json()["status"] == "completed"

    # Verify run state
    get_resp = client.get(f"/api/runs/{run_id}")
    run_data = get_resp.json()
    assert run_data["status"] == "completed"
    assert run_data["total_frames"] == 5
    assert run_data["peak_crowd_count"] == 2
    assert run_data["total_unique_tracks"] == 2
    assert run_data["has_video"] is True
    assert run_data["has_raw_video"] is True
    assert run_data["has_heatmap"] is True
    assert run_data["annotated_video_path"] is not None

    # Verify video streaming endpoints
    annotated_resp = client.get(f"/api/runs/{run_id}/video")
    assert annotated_resp.status_code == 200
    assert annotated_resp.content == b"\x00\x00\x00 fake_annotated_mp4"

    raw_resp = client.get(f"/api/runs/{run_id}/raw-video")
    assert raw_resp.status_code == 200

    # Verify metrics
    metrics_resp = client.get(f"/api/runs/{run_id}/metrics")
    assert metrics_resp.status_code == 200
    metrics = metrics_resp.json()
    assert metrics["peak_crowd_count"] == 2
    assert "Zone_A" in metrics["zone_totals"]


def test_video_run_empty_detections_mock(client):
    """Test video processing when detector produces 0 detections (empty CSV with headers)."""
    def mock_empty_runner(video_path, output_csv_path, output_video_path, yolov5_dir, weights_path):
        output_csv_path.parent.mkdir(parents=True, exist_ok=True)
        output_video_path.parent.mkdir(parents=True, exist_ok=True)
        # 0 detections
        output_csv_path.write_text("frame,x1,y1,x2,y2,confidence\n", encoding="utf-8")
        output_video_path.write_bytes(b"\x00\x00\x00 empty_video")
        return True, None

    set_detector_runner(mock_empty_runner)

    dummy_mp4 = io.BytesIO(b"\x00\x00\x00 ftypisom\x00\x00\x02\x00isomiso2mp41")
    files = {"file": ("empty_scene.mp4", dummy_mp4, "video/mp4")}
    upload_resp = client.post("/api/runs/upload", files=files)
    run_id = upload_resp.json()["id"]

    proc_resp = client.post(f"/api/runs/{run_id}/process?sync=true")
    assert proc_resp.status_code == 200
    assert proc_resp.json()["status"] == "completed"

    get_resp = client.get(f"/api/runs/{run_id}")
    run_data = get_resp.json()
    assert run_data["status"] == "completed"
    assert run_data["total_frames"] == 0
    assert run_data["peak_crowd_count"] == 0
    assert run_data["total_unique_tracks"] == 0
    assert run_data["has_video"] is True


def test_raw_video_endpoint_csv_run_returns_404(client):
    """Test that requesting raw video for a CSV run returns 404."""
    create_resp = client.post("/api/runs/test-csv?use_sample=true")
    run_id = create_resp.json()["id"]

    raw_resp = client.get(f"/api/runs/{run_id}/raw-video")
    assert raw_resp.status_code == 404
    assert "No raw video available" in raw_resp.json()["detail"]
