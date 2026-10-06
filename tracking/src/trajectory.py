import pandas as pd


INPUT_CSV = "tracking/outputs/tracked_detections.csv"


def build_trajectories():
    # Load tracking results
    df = pd.read_csv(INPUT_CSV)

    # Store trajectory for every tracked person
    trajectories = {}

    for track_id, person_data in df.groupby("track_id"):
        person_data = person_data.sort_values("frame")

        trajectory = []

        for _, row in person_data.iterrows():
            trajectory.append({
                "frame": int(row["frame"]),
                "cx": float(row["cx"]),
                "cy": float(row["cy"])
            })

        trajectories[int(track_id)] = trajectory

    return trajectories


def main():
    trajectories = build_trajectories()

    print("Trajectories created.")
    print()

    for track_id, points in trajectories.items():
        print(f"Person ID {track_id}:")
        print(points)
        print()


if __name__ == "__main__":
    main()