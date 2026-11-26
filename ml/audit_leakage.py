"""Audit exported features against historical prefixes and perturb the source sessions."""
import pandas as pd

from ml.data_processing.create_features import load_sessions
from ml.model_data import load_features
from ml.progression_features import EXERCISE, FEATURE_COLUMNS, TARGET_COLUMN, supervised_observations


def main():
    sessions = load_sessions()
    exported = load_features()
    rebuilt = supervised_observations(sessions)
    pd.testing.assert_frame_equal(exported, rebuilt, check_exact=False, check_dtype=False)

    # Perturb one target for each exercise with an eligible observation.
    # Compare that target and every earlier observation for the same exercise.
    changed = sessions.copy()
    cutoffs = {}
    for exercise, group in rebuilt.groupby(EXERCISE):
        date = group.iloc[len(group) // 2]["Date"]
        cutoffs[exercise] = date
        mask = changed[EXERCISE].eq(exercise) & changed["Date"].ge(date)
        changed.loc[mask, ["max_weight", "total_reps", "total_volume", "best_1rm"]] += 100
    perturbed = supervised_observations(changed)
    cutoff_dates = rebuilt[EXERCISE].map(cutoffs)
    before = rebuilt["Date"].lt(cutoff_dates)
    at_target = rebuilt["Date"].eq(cutoff_dates)
    pd.testing.assert_frame_equal(rebuilt.loc[before], perturbed.loc[before])
    pd.testing.assert_frame_equal(
        rebuilt.loc[at_target, FEATURE_COLUMNS], perturbed.loc[at_target, FEATURE_COLUMNS]
    )
    assert (perturbed.loc[at_target, TARGET_COLUMN] > rebuilt.loc[at_target, TARGET_COLUMN]).all()
    print(f"All {len(rebuilt)} exported observations match reconstructed prefixes.")
    print(f"Perturbation checks passed for {before.sum()} earlier and {at_target.sum()} target observations.")


if __name__ == "__main__":
    main()
