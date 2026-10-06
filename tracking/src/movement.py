import math
import pandas as pd


INPUT_CSV = "tracking/outputs/tracked_detections.csv"
OUTPUT_CSV = "tracking/outputs/movement.csv"


def calculate_direction(dx, dy, threshold=2):
    """
    Determine movement direction from change in centroid.
    """

    if abs(dx) <= threshold and abs(dy) <= threshold:
        return "STATIONARY"

    if abs(dx) > abs(dy):
        if dx > 0:
            return "RIGHT"
        return "LEFT"

    if dy > 0:
        return "DOWN"

    return "UP"


def main():
    df = pd.read_csv(INPUT_CSV)

    # Sort by person and frame
    df = df.sort_values(["track_id", "frame"]).reset_index(drop=True)

    # Previous centroid for each person
    df["prev_cx"] = df.groupby("track_id")["cx"].shift(1)
    df["prev_cy"] = df.groupby("track_id")["cy"].shift(1)

    movement_rows = []

    for _, row in df.iterrows():

        # First observation of a person
        if pd.isna(row["prev_cx"]):
            dx = 0
            dy = 0
            distance = 0
            direction = "START"
        else:
            dx = row["cx"] - row["prev_cx"]
            dy = row["cy"] - row["prev_cy"]

            distance = math.sqrt(dx ** 2 + dy ** 2)

            direction = calculate_direction(dx, dy)

        movement_rows.append({
            "frame": int(row["frame"]),
            "track_id": int(row["track_id"]),
            "cx": row["cx"],
            "cy": row["cy"],
            "dx": round(dx, 2),
            "dy": round(dy, 2),
            "distance": round(distance, 2),
            "direction": direction
        })

    output_df = pd.DataFrame(movement_rows)

    output_df.to_csv(OUTPUT_CSV, index=False)

    print("Movement analysis completed.")
    print(f"Output saved to: {OUTPUT_CSV}")
    print()
    print(output_df)


if __name__ == "__main__":
    main()