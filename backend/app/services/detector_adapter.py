import os
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional, Tuple

from backend.app.config import REPO_ROOT

# Environment variable for overriding detector Python interpreter
DETECTOR_PYTHON_ENV_VAR = "CROWDAHEAD_DETECTOR_PYTHON"

# Default Paths for YOLOv5 detection module
DEFAULT_DETECT_SCRIPT = REPO_ROOT / "person_detection" / "src" / "detect_people.py"
DEFAULT_YOLOV5_DIR = REPO_ROOT / "person_detection" / "yolov5"
DEFAULT_WEIGHTS_PATH = DEFAULT_YOLOV5_DIR / "yolov5s.pt"

# Mockable runner hook for unit testing
_custom_detector_runner: Optional[Callable] = None


def set_detector_runner(runner_fn: Optional[Callable]):
    """Set a custom runner function for testing/mocking detector execution."""
    global _custom_detector_runner
    _custom_detector_runner = runner_fn


def get_detector_python_path(override_path: Optional[Path] = None) -> Path:
    """
    Resolve the Python interpreter to use for running the YOLOv5 detector.

    Priority:
    1. Direct override parameter (if provided and non-empty).
    2. Environment variable 'CROWDAHEAD_DETECTOR_PYTHON' (if set and non-empty).
    3. Dedicated project-root virtual environment (.venv-yolo):
       - Windows: REPO_ROOT / ".venv-yolo" / "Scripts" / "python.exe"
       - Posix:   REPO_ROOT / ".venv-yolo" / "bin" / "python"
       (used when it exists on disk).
    4. Fallback to sys.executable if the dedicated interpreter is unavailable.
    """
    if override_path is not None:
        return Path(override_path)

    env_val = os.getenv(DETECTOR_PYTHON_ENV_VAR)
    if env_val and env_val.strip():
        return Path(env_val.strip())

    venv_dir = REPO_ROOT / ".venv-yolo"
    win_py = venv_dir / "Scripts" / "python.exe"
    posix_py = venv_dir / "bin" / "python"

    if sys.platform == "win32" and win_py.is_file():
        return win_py
    elif posix_py.is_file():
        return posix_py
    elif win_py.is_file():
        return win_py

    return Path(sys.executable)


def check_detector_prerequisites(
    video_path: Optional[Path] = None,
    yolov5_dir: Optional[Path] = None,
    weights_path: Optional[Path] = None,
    python_path: Optional[Path] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Verify all required libraries, files, and directories exist before running detection.
    Verifies that 'torch' and 'cv2' are importable in the selected detector interpreter.
    Returns (True, None) if prerequisites are met, or (False, error_message).
    """
    # 1. Resolve & verify detector Python interpreter
    py_path = Path(python_path or get_detector_python_path())
    if not py_path.is_file():
        return (
            False,
            f"Prerequisite missing: Detector Python interpreter not found at '{py_path}'."
        )

    # 2. Check that 'torch' and 'cv2' are importable in the selected interpreter
    check_script = (
        "import sys\n"
        "try:\n"
        "    import torch\n"
        "except Exception as e:\n"
        "    sys.stderr.write(f'TORCH_ERROR: {e}')\n"
        "    sys.exit(101)\n"
        "try:\n"
        "    import cv2\n"
        "except Exception as e:\n"
        "    sys.stderr.write(f'CV2_ERROR: {e}')\n"
        "    sys.exit(102)\n"
        "sys.exit(0)\n"
    )

    try:
        proc = subprocess.run(
            [str(py_path), "-c", check_script],
            capture_output=True,
            text=True,
            timeout=15,
        )

        if proc.returncode == 101:
            err_detail = proc.stderr.strip()
            return (
                False,
                f"Prerequisite missing: PyTorch ('torch') is not importable in detector Python '{py_path}'. "
                f"{err_detail}. Please install PyTorch compatible with your system (e.g. 'pip install torch torchvision')."
            )

        if proc.returncode == 102:
            err_detail = proc.stderr.strip()
            return (
                False,
                f"Prerequisite missing: OpenCV ('cv2' / opencv-python) is not importable in detector Python '{py_path}'. "
                f"{err_detail}. Please install OpenCV using: 'pip install opencv-python'."
            )

        if proc.returncode != 0:
            err_detail = proc.stderr.strip() or proc.stdout.strip() or f"Process exited with code {proc.returncode}"
            return (
                False,
                f"Prerequisite missing: Detector Python environment '{py_path}' failed module check: {err_detail}"
            )

    except subprocess.TimeoutExpired:
        return (
            False,
            f"Prerequisite check timed out while verifying modules in detector Python '{py_path}'."
        )
    except Exception as e:
        return (
            False,
            f"Prerequisite missing: Unable to execute detector Python '{py_path}': {str(e)}"
        )

    # 3. Check YOLOv5 repository directory
    ydir = Path(yolov5_dir or DEFAULT_YOLOV5_DIR)
    if not ydir.exists() or not ydir.is_dir():
        return (
            False,
            f"Prerequisite missing: Local YOLOv5 repository not found at '{ydir}'. "
            "To set up detection, clone YOLOv5 into that location: "
            "'git clone https://github.com/ultralytics/yolov5.git person_detection/yolov5'"
        )

    # 4. Check model weights
    wpath = Path(weights_path or DEFAULT_WEIGHTS_PATH)
    if not wpath.exists() or not wpath.is_file():
        return (
            False,
            f"Prerequisite missing: YOLOv5 model weights not found at '{wpath}'. "
            "Please download 'yolov5s.pt' and place it inside the 'person_detection/yolov5/' directory."
        )

    # 5. Check video existence
    if video_path is not None:
        vpath = Path(video_path)
        if not vpath.exists():
            return False, f"Input video file not found at '{vpath}'."
        if vpath.stat().st_size == 0:
            return False, f"Input video file at '{vpath}' is empty (0 bytes)."

    return True, None


def execute_person_detection(
    video_path: Path,
    output_csv_path: Path,
    output_video_path: Path,
    yolov5_dir: Optional[Path] = None,
    weights_path: Optional[Path] = None,
    python_path: Optional[Path] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Executes the person detection module for the given video file.
    Writes detection CSV (frame, x1, y1, x2, y2, confidence) and annotated MP4 video.
    Returns (True, None) on success or (False, error_details).
    """
    video_path = Path(video_path)
    output_csv_path = Path(output_csv_path)
    output_video_path = Path(output_video_path)
    ydir = Path(yolov5_dir or DEFAULT_YOLOV5_DIR)
    wpath = Path(weights_path or DEFAULT_WEIGHTS_PATH)
    detector_python = Path(python_path or get_detector_python_path())

    # If a custom/mock runner is registered, invoke it directly
    if _custom_detector_runner is not None:
        try:
            return _custom_detector_runner(
                video_path=video_path,
                output_csv_path=output_csv_path,
                output_video_path=output_video_path,
                yolov5_dir=ydir,
                weights_path=wpath,
            )
        except Exception as e:
            return False, f"Mock Detector Execution Error: {str(e)}"

    # 1. Validate prerequisites
    prereq_ok, prereq_err = check_detector_prerequisites(
        video_path=video_path,
        yolov5_dir=ydir,
        weights_path=wpath,
        python_path=detector_python,
    )
    if not prereq_ok:
        return False, prereq_err

    # 2. Ensure destination folders exist
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    output_video_path.parent.mkdir(parents=True, exist_ok=True)

    # 3. Execute detect_people.py via subprocess to isolate C-extensions & memory
    script_path = DEFAULT_DETECT_SCRIPT
    if not script_path.exists():
        return False, f"Detection script not found at '{script_path}'."

    cmd = [
        str(detector_python.resolve()),
        str(script_path.resolve()),
        "--input", str(video_path.resolve()),
        "--output-video", str(output_video_path.resolve()),
        "--output-csv", str(output_csv_path.resolve()),
        "--yolov5-dir", str(ydir.resolve()),
        "--weights", str(wpath.resolve()),
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout for long videos
        )

        if proc.returncode != 0:
            err_msg = proc.stderr.strip() or proc.stdout.strip() or f"Process exited with code {proc.returncode}"
            return False, f"Detection process failed: {err_msg}"

        if not output_csv_path.exists():
            return False, "Detection completed but detection CSV output was not created."

        return True, None

    except subprocess.TimeoutExpired:
        return False, "Video detection timed out after 300 seconds."
    except Exception as e:
        return False, f"Failed to execute detection subprocess: {str(e)}"
