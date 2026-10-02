import cv2
import torch
import csv

from pathlib import Path

# -----------------------------
# Paths
# -----------------------------

# person_detection/
BASE_DIR = Path(__file__).resolve().parent.parent

VIDEO_PATH = BASE_DIR / "input" / "testvideo.mp4"
YOLOV5_DIR = BASE_DIR / "yolov5"
MODEL_PATH = YOLOV5_DIR / "yolov5s.pt"

OUTPUT_PATH = BASE_DIR / "output" / "detected_test.mp4"
CSV_PATH = BASE_DIR / "output" / "detections.csv"


# -----------------------------
# Load YOLOv5
# -----------------------------

print("Loading YOLOv5...")

model = torch.hub.load(
    str(YOLOV5_DIR),
    "custom",
    path=MODEL_PATH,
    source="local"
)

# Class 0 = person
model.classes = [0]

print("Model loaded.")


# -----------------------------
# Open input video
# -----------------------------

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    print("Error: Could not open video.")
    exit()

# Get video properties
fps = cap.get(cv2.CAP_PROP_FPS)
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
    OUTPUT_PATH,
    fourcc,
    fps,
    (width, height)
)

if not out.isOpened():
    print("Error: Could not create output video.")
    cap.release()
    exit()


# -----------------------------
# Create CSV file
# -----------------------------

csv_file = open(CSV_PATH, "w", newline="")
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
print(OUTPUT_PATH)

print("Detection CSV saved to:")
print(CSV_PATH)