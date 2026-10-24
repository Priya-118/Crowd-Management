import pandas as pd

ZONE_ASSIGNMENTS_CSV = "tracking/outputs/zone_assignments.csv"
ZONE_COUNTS_CSV = "tracking/outputs/zone_counts.csv"
FLOW_METRICS_CSV = "tracking/outputs/crowd_flow_metrics.csv"

OUTPUT_CSV = "tracking/outputs/spatiotemporal_dataset.csv"


def main():
    # -----------------------------------
    # 1. Person-level tracking data
    # -----------------------------------
    person_data = pd.read_csv(ZONE_ASSIGNMENTS_CSV)

    person_data = person_data[
        [
            "frame",
            "track_id",
            "cx",
            "cy",
            "zone",
            "direction",
            "distance",
        ]
    ].copy()

    # -----------------------------------
    # 2. Zone-level crowd counts
    # -----------------------------------
    zone_counts = pd.read_csv(ZONE_COUNTS_CSV)

    # -----------------------------------
    # 3. Crowd-flow metrics
    # -----------------------------------
    flow_metrics = pd.read_csv(FLOW_METRICS_CSV)

    # -----------------------------------
    # 4. Combine zone counts + flow data
    # -----------------------------------
    frame_data = zone_counts.merge(
        flow_metrics,
        on="frame",
        how="left",
        suffixes=("", "_flow")
    )

    # Remove duplicate total_people if created
    if "total_people_flow" in frame_data.columns:
        frame_data = frame_data.drop(columns=["total_people_flow"])

    # -----------------------------------
    # 5. Add frame-level information
    # to every person observation
    # -----------------------------------
    spatiotemporal = person_data.merge(
        frame_data,
        on="frame",
        how="left"
    )

    # -----------------------------------
    # 6. Sort the final dataset
    # -----------------------------------
    spatiotemporal = spatiotemporal.sort_values(
        ["frame", "track_id"]
    ).reset_index(drop=True)

    # -----------------------------------
    # 7. Save
    # -----------------------------------
    spatiotemporal.to_csv(
        OUTPUT_CSV,
        index=False
    )

    print("Spatio-temporal dataset created.")
    print(f"Output saved to: {OUTPUT_CSV}")
    print()
    print(spatiotemporal)
    print()
    print(f"Rows: {len(spatiotemporal)}")
    print(f"Columns: {len(spatiotemporal.columns)}")


if __name__ == "__main__":
    main()