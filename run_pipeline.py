
import argparse
import subprocess
import sys

SCRIPTS = [
    "tracking/src/tracker.py",
    "tracking/src/trajectory.py",
    "tracking/src/movement.py",
    "tracking/src/zones.py",
    "tracking/src/zone_counts.py",
    "tracking/src/zone_flow.py",
    "tracking/src/inflow_outflow.py",
    "tracking/src/crowd_flow_analysis.py",
    "tracking/src/spatiotemporal_dataset.py",
]


def main():
    parser = argparse.ArgumentParser(
        description="Run the crowd tracking and flow pipeline."
    )
    parser.add_argument(
        "--input",
        default="tracking/data/test_detections.csv",
        help="Path to the input detections CSV file."
    )
    args = parser.parse_args()

    for script in SCRIPTS:
        print(f"\n{'=' * 60}")
        print(f"Running: {script}")
        print("=" * 60)

        command = [sys.executable, script]

        if script == "tracking/src/tracker.py":
            command.extend(["--input", args.input])

        result = subprocess.run(command, check=False)

        if result.returncode != 0:
            print(f"\nPipeline stopped: {script} failed.")
            sys.exit(result.returncode)

    print("\nAll pipeline stages completed successfully.")


if __name__ == "__main__":
    main()
