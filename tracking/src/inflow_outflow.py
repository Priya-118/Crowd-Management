
import pandas as pd

INPUT_CSV = "tracking/outputs/zone_flow.csv"
OUTPUT_CSV = "tracking/outputs/inflow_outflow.csv"

OUTPUT_COLUMNS = [
    "frame",
    "zone",
    "inflow",
    "outflow",
    "net_flow",
]


def main():
    try:
        df = pd.read_csv(INPUT_CSV)
    except pd.errors.EmptyDataError:
        df = pd.DataFrame()

    if df.empty:
        flow = pd.DataFrame(columns=OUTPUT_COLUMNS)
    else:
        required_columns = ["frame", "from_zone", "to_zone"]
        missing = [
            col for col in required_columns
            if col not in df.columns
        ]

        if missing:
            raise ValueError(
                f"Missing required columns in zone flow CSV: {missing}"
            )

        inflow = (
            df.groupby(["frame", "to_zone"])
            .size()
            .reset_index(name="inflow")
            .rename(columns={"to_zone": "zone"})
        )

        outflow = (
            df.groupby(["frame", "from_zone"])
            .size()
            .reset_index(name="outflow")
            .rename(columns={"from_zone": "zone"})
        )

        flow = pd.merge(
            inflow,
            outflow,
            on=["frame", "zone"],
            how="outer",
        )

        flow[["inflow", "outflow"]] = (
            flow[["inflow", "outflow"]]
            .fillna(0)
            .astype(int)
        )

        flow["net_flow"] = flow["inflow"] - flow["outflow"]
        flow = flow[OUTPUT_COLUMNS].sort_values(
            ["frame", "zone"]
        )

    flow.to_csv(OUTPUT_CSV, index=False)

    print("Inflow/outflow analysis completed.")
    print(f"Output saved to: {OUTPUT_CSV}")

    if flow.empty:
        print("No zone transitions detected; output contains headers only.")
    else:
        print(flow.head(10))


if __name__ == "__main__":
    main()
