import pandas as pd

INPUT_CSV = "tracking/outputs/zone_flow.csv"
OUTPUT_CSV = "tracking/outputs/inflow_outflow.csv"


def main():
    df = pd.read_csv(INPUT_CSV)

    if df.empty:
        print("No zone transitions found.")
        return

    # Inflow: person enters the destination zone
    inflow = (
        df.groupby(["frame", "to_zone"])
        .size()
        .reset_index(name="inflow")
        .rename(columns={"to_zone": "zone"})
    )

    # Outflow: person leaves the source zone
    outflow = (
        df.groupby(["frame", "from_zone"])
        .size()
        .reset_index(name="outflow")
        .rename(columns={"from_zone": "zone"})
    )

    # Combine inflow and outflow
    flow = pd.merge(
        inflow,
        outflow,
        on=["frame", "zone"],
        how="outer"
    ).fillna(0)

    flow["inflow"] = flow["inflow"].astype(int)
    flow["outflow"] = flow["outflow"].astype(int)

    # Net flow = people entering - people leaving
    flow["net_flow"] = flow["inflow"] - flow["outflow"]

    flow = flow.sort_values(["frame", "zone"])

    flow.to_csv(OUTPUT_CSV, index=False)

    print("Inflow/outflow analysis completed.")
    print(f"Output saved to: {OUTPUT_CSV}")
    print()
    print(flow)


if __name__ == "__main__":
    main()