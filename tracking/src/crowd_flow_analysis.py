import pandas as pd

ZONE_COUNTS_CSV = "tracking/outputs/zone_counts.csv"
MOVEMENT_CSV = "tracking/outputs/movement.csv"
FLOW_CSV = "tracking/outputs/inflow_outflow.csv"

OUTPUT_CSV = "tracking/outputs/crowd_flow_metrics.csv"


def main():
    # Read existing outputs
    zone_counts = pd.read_csv(ZONE_COUNTS_CSV)
    movement = pd.read_csv(MOVEMENT_CSV)
    flow = pd.read_csv(FLOW_CSV)

    # -----------------------------------
    # 1. Total crowd occupancy per frame
    # -----------------------------------
    occupancy = zone_counts[["frame", "total_people"]].copy()

    # -----------------------------------
    # 2. Number of moving people
    # -----------------------------------
    moving = movement[movement["direction"] != "START"].copy()

    moving_people = (
        moving.groupby("frame")["track_id"]
        .nunique()
        .reset_index(name="moving_people")
    )

    # -----------------------------------
    # 3. Total movement distance
    # -----------------------------------
    movement_distance = (
        movement.groupby("frame")["distance"]
        .sum()
        .reset_index(name="total_movement_distance")
    )

    # -----------------------------------
    # 4. Total inflow and outflow
    # -----------------------------------
    if not flow.empty:
        total_flow = (
            flow.groupby("frame")
            .agg(
                total_inflow=("inflow", "sum"),
                total_outflow=("outflow", "sum"),
                net_flow=("net_flow", "sum"),
            )
            .reset_index()
        )
    else:
        total_flow = pd.DataFrame(
            columns=["frame", "total_inflow", "total_outflow", "net_flow"]
        )

    # -----------------------------------
    # 5. Combine all metrics
    # -----------------------------------
    metrics = occupancy.merge(
        moving_people,
        on="frame",
        how="left"
    )

    metrics = metrics.merge(
        movement_distance,
        on="frame",
        how="left"
    )

    metrics = metrics.merge(
        total_flow,
        on="frame",
        how="left"
    )

    # Fill missing values with zero
    metrics = metrics.fillna(0)

    # Convert count columns to integers
    for column in [
        "total_people",
        "moving_people",
        "total_inflow",
        "total_outflow",
    ]:
        metrics[column] = metrics[column].astype(int)

    # -----------------------------------
    # 6. Calculate movement percentage
    # -----------------------------------
    metrics["movement_percentage"] = (
        metrics["moving_people"]
        / metrics["total_people"].replace(0, pd.NA)
        * 100
    )

    metrics["movement_percentage"] = (
        metrics["movement_percentage"].fillna(0).round(2)
    )

    metrics.to_csv(OUTPUT_CSV, index=False)

    print("Crowd-flow analysis completed.")
    print(f"Output saved to: {OUTPUT_CSV}")
    print()
    print(metrics)


if __name__ == "__main__":
    main()