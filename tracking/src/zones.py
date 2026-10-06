import pandas as pd


INPUT_CSV = "tracking/outputs/movement.csv"
OUTPUT_CSV = "tracking/outputs/zone_assignments.csv"


# -------------------------------------------------
# Zone definitions
# -------------------------------------------------
# These coordinates are temporary for our test data.
# They can be changed later for the actual video.

ZONES = {
    "Zone_A": {
        "x_min": 0,
        "x_max": 200,
        "y_min": 0,
        "y_max": 160
    },
    "Zone_B": {
        "x_min": 200,
        "x_max": 400,
        "y_min": 0,
        "y_max": 160
    },
    "Zone_C": {
        "x_min": 0,
        "x_max": 200,
        "y_min": 160,
        "y_max": 320
    },
    "Zone_D": {
        "x_min": 200,
        "x_max": 400,
        "y_min": 160,
        "y_max": 320
    }
}


def get_zone(cx, cy):
    """
    Determine which zone contains a person's centroid.
    """

    for zone_name, zone in ZONES.items():

        if (
            zone["x_min"] <= cx < zone["x_max"]
            and zone["y_min"] <= cy < zone["y_max"]
        ):
            return zone_name

    return "Outside"


def main():

    # Load movement data
    df = pd.read_csv(INPUT_CSV)

    # Assign a zone to every tracked detection
    df["zone"] = df.apply(
        lambda row: get_zone(row["cx"], row["cy"]),
        axis=1
    )

    # Save zone assignments
    df.to_csv(OUTPUT_CSV, index=False)

    print("Zone assignment completed.")
    print(f"Output saved to: {OUTPUT_CSV}")
    print()

    print(
        df[
            [
                "frame",
                "track_id",
                "cx",
                "cy",
                "direction",
                "zone"
            ]
        ]
    )


if __name__ == "__main__":
    main()