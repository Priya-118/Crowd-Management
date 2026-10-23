
import argparse
import pandas as pd

INPUT_CSV = "tracking/outputs/movement.csv"
OUTPUT_CSV = "tracking/outputs/zone_assignments.csv"

ZONE_COLUMNS = ["Zone_A", "Zone_B", "Zone_C", "Zone_D"]


def get_zone(cx, cy, width, height):
    """Assign a person's centroid to one of four zones."""

    if not (0 <= cx < width and 0 <= cy < height):
        return "Outside"

    mid_x = width / 2
    mid_y = height / 2

    if cx < mid_x and cy < mid_y:
        return "Zone_A"
    elif cx >= mid_x and cy < mid_y:
        return "Zone_B"
    elif cx < mid_x and cy >= mid_y:
        return "Zone_C"
    else:
        return "Zone_D"


def main():
    parser = argparse.ArgumentParser(
        description="Assign tracked people to frame zones."
    )
    parser.add_argument("--width", type=int, default=832)
    parser.add_argument("--height", type=int, default=464)
    args = parser.parse_args()

    if args.width <= 0 or args.height <= 0:
        parser.error("Width and height must be positive integers.")

    df = pd.read_csv(INPUT_CSV)

    required_columns = ["frame", "track_id", "cx", "cy", "direction"]
    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df["zone"] = df.apply(
        lambda row: get_zone(
            row["cx"], row["cy"], args.width, args.height
        ),
        axis=1
    )

    df.to_csv(OUTPUT_CSV, index=False)

    print("Zone assignment completed.")
    print(f"Frame dimensions: {args.width} x {args.height}")
    print(f"Zones generated: {', '.join(ZONE_COLUMNS)}")
    print(f"Output saved to: {OUTPUT_CSV}")
    print(df[required_columns + ["zone"]].head(10))


if __name__ == "__main__":
    main()
