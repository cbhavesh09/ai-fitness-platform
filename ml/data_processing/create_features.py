"""Generate supervised observations using only preceding exercise sessions."""
import pandas as pd

from ml.model_data import FEATURE_FILE, ROOT
from ml.progression_features import aggregate_sessions, supervised_observations

INPUT_FILE = ROOT / "data/processed/weightlifting_clean.csv"


def load_sessions():
    sets = pd.read_csv(INPUT_FILE).rename(columns={"Weight": "weight", "Reps": "reps"})
    return aggregate_sessions(sets.assign(sets=1), weight_unit="lb")


def main():
    sessions = load_sessions()
    features = supervised_observations(sessions)
    FEATURE_FILE.parent.mkdir(parents=True, exist_ok=True)
    features.to_csv(FEATURE_FILE, index=False)
    print(f"{len(sessions)} eligible exercise sessions; {len(features)} supervised rows.")
    print(f"Saved to {FEATURE_FILE}")


if __name__ == "__main__":
    main()
