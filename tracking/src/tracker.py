
import pandas as pd
import supervision as sv

import argparse
from pathlib import Path

INPUT_CSV = "tracking/data/test_detections.csv"
OUTPUT_CSV = "tracking/outputs/tracked_detections.csv"

OUTPUT_COLUMNS = [
    "frame", "track_id",
    "x1", "y1", "x2", "y2",
    "confidence", "cx", "cy"
]


def main():
    parser = argparse.ArgumentParser(
        description="Track people using a detections CSV file."
    )
    parser.add_argument(
        "--input",
        default=INPUT_CSV,
        help="Path to the input detections CSV file."
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    detections_df = pd.read_csv(input_path)

    required_columns = [
        "frame", "x1", "y1", "x2", "y2", "confidence"
    ]

    missing_columns = [
        col for col in required_columns
        if col not in detections_df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    if detections_df.empty:
        raise ValueError("Input detections CSV is empty.")

    detections_df["frame"] = detections_df["frame"].astype(int)

    tracker = sv.ByteTrack(frame_rate=30)
    tracked_rows = []

    first_frame = int(detections_df["frame"].min())
    last_frame = int(detections_df["frame"].max())

    # Process EVERY frame, even if it has no detections.
    for frame_number in range(first_frame, last_frame + 1):
        frame_data = detections_df[
            detections_df["frame"] == frame_number
        ]

        if frame_data.empty:
            detections = sv.Detections.empty()
        else:
            xyxy = frame_data[
                ["x1", "y1", "x2", "y2"]
            ].to_numpy(dtype=float)

            confidence = frame_data[
                "confidence"
            ].to_numpy(dtype=float)

            detections = sv.Detections(
                xyxy=xyxy,
                confidence=confidence
            )

        tracked_detections = tracker.update_with_detections(
            detections
        )

        if tracked_detections.tracker_id is None:
            continue

        for i in range(len(tracked_detections)):
            x1, y1, x2, y2 = tracked_detections.xyxy[i]

            track_id = tracked_detections.tracker_id[i]
            confidence = tracked_detections.confidence[i]

            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2

            tracked_rows.append({
                "frame": frame_number,
                "track_id": int(track_id),
                "x1": int(x1),
                "y1": int(y1),
                "x2": int(x2),
                "y2": int(y2),
                "confidence": (
                    round(float(confidence), 4)
                    if confidence is not None else None
                ),
                "cx": round(float(cx), 2),
                "cy": round(float(cy), 2)
            })

    output_df = pd.DataFrame(
        tracked_rows,
        columns=OUTPUT_COLUMNS
    )

    output_df.to_csv(OUTPUT_CSV, index=False)

    print("Tracking completed.")
    print(f"Frames processed: {last_frame - first_frame + 1}")
    print(f"Tracked detections: {len(output_df)}")
    print(f"Output saved to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
