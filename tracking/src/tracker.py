import pandas as pd
import supervision as sv


INPUT_CSV = "tracking/data/test_detections.csv"
OUTPUT_CSV = "tracking/outputs/tracked_detections.csv"


def main():
    # Load YOLO detection data
    detections_df = pd.read_csv(INPUT_CSV)

    # Create ByteTrack tracker
    tracker = sv.ByteTrack()

    tracked_rows = []

    # Process one frame at a time
    for frame_number, frame_data in detections_df.groupby("frame"):

        # Convert bounding boxes to NumPy array
        xyxy = frame_data[["x1", "y1", "x2", "y2"]].to_numpy()

        # Convert confidence values to NumPy array
        confidence = frame_data["confidence"].to_numpy()

        # Create Supervision detections
        detections = sv.Detections(
            xyxy=xyxy,
            confidence=confidence
        )

        # Run ByteTrack
        tracked_detections = tracker.update_with_detections(detections)

        # Store tracking results
        for i in range(len(tracked_detections)):
            x1, y1, x2, y2 = tracked_detections.xyxy[i]
            track_id = tracked_detections.tracker_id[i]
            conf = tracked_detections.confidence[i]

            # Calculate center point
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2

            tracked_rows.append({
                "frame": frame_number,
                "track_id": int(track_id),
                "x1": int(x1),
                "y1": int(y1),
                "x2": int(x2),
                "y2": int(y2),
                "confidence": round(float(conf), 4),
                "cx": round(float(cx), 2),
                "cy": round(float(cy), 2)
            })

    # Create output dataframe
    output_df = pd.DataFrame(tracked_rows)

    # Save tracking results
    output_df.to_csv(OUTPUT_CSV, index=False)

    print("Tracking completed.")
    print(f"Output saved to: {OUTPUT_CSV}")
    print()
    print(output_df)


if __name__ == "__main__":
    main()