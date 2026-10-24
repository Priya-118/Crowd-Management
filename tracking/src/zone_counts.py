import pandas as pd


INPUT_CSV = "tracking/outputs/zone_assignments.csv"
OUTPUT_CSV = "tracking/outputs/zone_counts.csv"


def main():

    # Load zone assignment data
    df = pd.read_csv(INPUT_CSV)

    # Count unique tracked people in each zone for every frame
    zone_counts = (
        df.groupby(["frame", "zone"])["track_id"]
        .nunique()
        .reset_index(name="person_count")
    )

    # Convert zones into columns
    zone_counts = (
        zone_counts
        .pivot(
            index="frame",
            columns="zone",
            values="person_count"
        )
        .fillna(0)
        .reset_index()
    )

    # Remove column name created by pivot
    zone_counts.columns.name = None

    # Make counts integers
    for column in zone_counts.columns:
        if column != "frame":
            zone_counts[column] = zone_counts[column].astype(int)

    # Add total crowd count
    zone_columns = [
        column for column in zone_counts.columns
        if column != "frame"
    ]

    zone_counts["total_people"] = zone_counts[zone_columns].sum(axis=1)

    # Save result
    zone_counts.to_csv(OUTPUT_CSV, index=False)

    print("Zone-wise counting completed.")
    print(f"Output saved to: {OUTPUT_CSV}")
    print()

    print(zone_counts)


if __name__ == "__main__":
    main()