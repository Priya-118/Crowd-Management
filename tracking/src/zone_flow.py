import pandas as pd

INPUT_CSV = "tracking/outputs/zone_assignments.csv"
OUTPUT_CSV = "tracking/outputs/zone_flow.csv"


def main():
    df = pd.read_csv(INPUT_CSV)

    # Sort each person by frame
    df = df.sort_values(["track_id", "frame"]).copy()

    # Get the person's previous zone
    df["previous_zone"] = df.groupby("track_id")["zone"].shift(1)

    # Detect zone changes
    transitions = df[
        df["previous_zone"].notna()
        & (df["zone"] != df["previous_zone"])
    ].copy()

    # Create transition labels
    transitions["transition"] = (
        transitions["previous_zone"]
        + " -> "
        + transitions["zone"]
    )

    # Count transitions
    transition_counts = (
        transitions.groupby(["frame", "transition"])
        .size()
        .reset_index(name="people_count")
    )

    # Calculate inflow and outflow
    flow_records = []

    for _, row in transitions.iterrows():
        flow_records.append({
            "frame": row["frame"],
            "track_id": row["track_id"],
            "from_zone": row["previous_zone"],
            "to_zone": row["zone"],
        })

    flow_df = pd.DataFrame(flow_records)

    flow_df.to_csv(OUTPUT_CSV, index=False)

    print("Zone flow analysis completed.")
    print(f"Output saved to: {OUTPUT_CSV}")
    print()

    if flow_df.empty:
        print("No zone transitions detected in the current test data.")
    else:
        print(flow_df)


if __name__ == "__main__":
    main()