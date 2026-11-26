"""Evaluate four approaches on the same date-grouped holdout."""
import joblib
import pandas as pd

from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    mean_absolute_error,
    median_absolute_error,
    r2_score,
    root_mean_squared_error,
)

from ml.model_data import MODEL_FILE, chronological_split, load_features, print_partitions
from ml.progression_features import EXERCISE, FEATURE_COLUMNS, TARGET_COLUMN
from ml.train_model import fit_model


def main():
    partitions = chronological_split(load_features())
    print_partitions(partitions)
    train, validation, test = partitions
    forest = joblib.load(MODEL_FILE)
    linear = fit_model(train, LinearRegression())
    validation_mae = mean_absolute_error(
        validation[TARGET_COLUMN], forest.predict(validation[FEATURE_COLUMNS])
    )
    print(f"Random Forest validation MAE: {validation_mae:.4f} lb")
    actual = test[TARGET_COLUMN]
    predictions = {
        "Persistence": test["previous_weight"],
        "Recent three mean": test["rolling_avg_weight_3"],
        "Linear Regression": linear.predict(test[FEATURE_COLUMNS]),
        "Random Forest": forest.predict(test[FEATURE_COLUMNS]),
    }
    baseline_mae = mean_absolute_error(actual, predictions["Persistence"])
    metrics = []
    errors = pd.DataFrame({EXERCISE: test[EXERCISE]})
    for name, predicted in predictions.items():
        mae = mean_absolute_error(actual, predicted)
        metrics.append({
            "Model": name,
            "MAE": mae,
            "RMSE": root_mean_squared_error(actual, predicted),
            "Median AE": median_absolute_error(actual, predicted),
            "R²": r2_score(actual, predicted),
            "MAE improvement (%)": (1 - mae / baseline_mae) * 100 if baseline_mae else float("nan"),
        })
        errors[name] = (actual - predicted).abs()
    print(pd.DataFrame(metrics).to_string(index=False, float_format="{:.4f}".format))
    grouped = errors.groupby(EXERCISE)
    per_exercise = grouped.mean()
    per_exercise.insert(0, "Test n", grouped.size())
    print("\nPer-exercise MAE (lb)")
    print(per_exercise.to_string(float_format="{:.2f}".format))


if __name__ == "__main__":
    main()
