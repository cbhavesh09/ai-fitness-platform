"""Walk forward over held-out sessions using the production recommendation policy."""
import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import mean_absolute_error, root_mean_squared_error

from ml.data_processing.create_features import load_sessions
from ml.model_data import MODEL_FILE, ROOT, chronological_split, load_features
from ml.progression_features import (
    EXERCISE, FEATURE_COLUMNS, build_next_session_features, kg_to_lb, walk_forward,
)
from ml.recommendation import adjust_prediction


def main():
    _, _, test = chronological_split(load_features())
    expected = test.set_index(["Date", EXERCISE])
    first_date, last_date = test["Date"].min(), test["Date"].max()
    model = joblib.load(MODEL_FILE)
    eligible = []
    cold_start = 0
    for target, history in walk_forward(load_sessions()):
        date = target["Date"]
        if not first_date <= date <= last_date:
            continue
        features = build_next_session_features(history)
        if features is None:
            cold_start += 1
            continue
        key = (date, target[EXERCISE])
        stored = expected.loc[key, FEATURE_COLUMNS[1:]].to_numpy(dtype=float)
        np.testing.assert_allclose(features.iloc[1:].to_numpy(dtype=float), stored)
        model_input = pd.DataFrame([features], columns=FEATURE_COLUMNS)
        raw = float(model.predict(model_input)[0])
        recommendation = adjust_prediction(features, raw)
        hybrid = kg_to_lb(recommendation.weight_kg)
        previous = float(features["previous_weight"])
        eligible.append({
            "Date": date,
            EXERCISE: target[EXERCISE],
            "target_lb": float(target["max_weight"]),
            "persistence_lb": previous,
            "raw_lb": raw,
            "hybrid_lb": hybrid,
            "change_lb": hybrid - previous,
            "constraint_violation": not recommendation.lower_kg <= recommendation.weight_kg <= recommendation.upper_kg,
        })
    results = pd.DataFrame(eligible).sort_values(["Date", EXERCISE])
    pd.testing.assert_index_equal(results.set_index(["Date", EXERCISE]).index, expected.index)
    np.testing.assert_allclose(results["target_lb"], expected["target_weight"])
    total = len(results) + cold_start
    print(f"Coverage: {len(results)}/{total} ({len(results)/total:.2%}); cold starts: {cold_start}")
    for label in ("persistence", "raw", "hybrid"):
        actual, predicted = results["target_lb"], results[f"{label}_lb"]
        print(f"{label}: MAE {mean_absolute_error(actual, predicted):.4f} lb; "
              f"RMSE {root_mean_squared_error(actual, predicted):.4f} lb")
    change = results["change_lb"]
    flat = np.isclose(change, 0, atol=1e-9)
    print(f"Changes: {(change[~flat] < 0).sum()} decreases, {flat.sum()} unchanged, "
          f"{(change[~flat] > 0).sum()} increases")
    print(f"Changes (lb): min {change.min():.4f}; median {change.median():.4f}; "
          f"max {change.max():.4f}")
    print(f"Constraint violations: {results['constraint_violation'].sum()}")
    results.to_csv(ROOT / "data/processed/recommendation_evaluation.csv", index=False)


if __name__ == "__main__":
    main()
