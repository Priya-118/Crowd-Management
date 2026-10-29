import argparse
import csv
from pathlib import Path
import cv2
import torch

# -----------------------------
# Default Paths (Backward Compatible)
# -----------------------------

# person_detection/
BASE_DIR = Path(__file__).resolve().parent.parent

VIDEO_PATH = BASE_DIR / "input" / "testvideo.mp4"
YOLOV5_DIR = BASE_DIR / "yolov5"
MODEL_PATH = YOLOV5_DIR / "yolov5s.pt"

OUTPUT_PATH = BASE_DIR / "output" / "detected_test.mp4"
CSV_PATH = BASE_DIR / "output" / "detections.csv"


def run_detection(
    video_path=VIDEO_PATH,
    output_video_path=OUTPUT_PATH,
    output_csv_path=CSV_PATH,
    yolov5_dir=YOLOV5_DIR,
    model_path=MODEL_PATH,
):
    """
    Detect people in video frames using YOLOv5 and output both an annotated video
    and a detection CSV (frame, x1, y1, x2, y2, confidence).
    """
    video_path = Path(video_path)
    output_video_path = Path(output_video_path)
    output_csv_path = Path(output_csv_path)
    yolov5_dir = Path(yolov5_dir)
    model_path = Path(model_path)

    # Ensure parent output directories exist
    output_video_path.parent.mkdir(parents=True, exist_ok=True)
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)

    print("Loading YOLOv5...")

    model = torch.hub.load(
        str(yolov5_dir),
        "custom",
        path=str(model_path),
        source="local"
    )

    # Class 0 = person
    model.classes = [0]

    print("Model loaded.")

    # -----------------------------
    # Open input video
    # -----------------------------

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        print(f"Error: Could not open video: {video_path}")
        return False

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print("FPS:", fps)
    print("Width:", width)
    print("Height:", height)
    print("Total frames:", total_frames)

    # -----------------------------
    # Create output video
    # -----------------------------

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")

    out = cv2.VideoWriter(
        str(output_video_path),
        fourcc,
        fps,
        (width, height)
    )

    if not out.isOpened():
        print("Error: Could not create output video.")
        cap.release()
        return False

    # -----------------------------
    # Create CSV file
    # -----------------------------

    csv_file = open(str(output_csv_path), "w", newline="")
    csv_writer = csv.writer(csv_file)

    csv_writer.writerow([
        "frame",
        "x1",
        "y1",
        "x2",
        "y2",
        "confidence"
    ])

    # -----------------------------
    # Process entire video
    # -----------------------------

    frame_number = 0

    while True:
        ret, frame = cap.read()

        # Stop when video ends
        if not ret:
            break

        frame_number += 1

        # -------------------------
        # Run YOLOv5
        # -------------------------

        results = model(frame)

        # Get detections
        detections = results.xyxy[0]

        person_count = len(detections)

        # -------------------------
        # Process detections
        # -------------------------

        for detection in detections:
            x1, y1, x2, y2, confidence, class_id = detection.tolist()

            x1 = int(x1)
            y1 = int(y1)
            x2 = int(x2)
            y2 = int(y2)

            confidence = float(confidence)

            # Save detection information
            csv_writer.writerow([
                frame_number,
                x1,
                y1,
                x2,
                y2,
                round(confidence, 4)
            ])

            # Draw bounding box
            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            # Person label
            label = f"Person {confidence:.2f}"

            cv2.putText(
                frame,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

        # -------------------------
        # Display person count
        # -------------------------

        cv2.putText(
            frame,
            f"Persons: {person_count}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 255),
            2
        )

        # -------------------------
        # Save processed frame
        # -------------------------

        out.write(frame)

        # -------------------------
        # Progress
        # -------------------------

        print(
            f"Frame {frame_number}/{total_frames}: "
            f"{person_count} persons detected"
        )

    # -----------------------------
    # Release resources
    # -----------------------------

    cap.release()
    out.release()
    csv_file.close()

    # -----------------------------
    # Completion message
    # -----------------------------

    print()
    print("Detection completed.")
    print("Frames processed:", frame_number)
    print("Output video saved to:")
    print(output_video_path)
    print("Detection CSV saved to:")
    print(output_csv_path)
    return True


def parse_args():
    parser = argparse.ArgumentParser(description="Detect people in video using YOLOv5")
    parser.add_argument("--input", default=str(VIDEO_PATH), help="Path to input video")
    parser.add_argument("--output-video", default=str(OUTPUT_PATH), help="Path to output video")
    parser.add_argument("--output-csv", default=str(CSV_PATH), help="Path to output CSV")
    parser.add_argument("--yolov5-dir", default=str(YOLOV5_DIR), help="Path to local YOLOv5 repo")
    parser.add_argument("--weights", default=str(MODEL_PATH), help="Path to YOLOv5 model weights")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_detection(
        video_path=args.input,
        output_video_path=args.output_video,
        output_csv_path=args.output_csv,
        yolov5_dir=args.yolov5_dir,
        model_path=args.weights,
    )