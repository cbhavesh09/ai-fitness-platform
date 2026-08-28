from pathlib import Path

import joblib
import pandas as pd

from sklearn.metrics import mean_absolute_error


PROJECT_ROOT = Path(__file__).resolve().parents[1]

FEATURE_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "workout_progression_features.csv"
)

MODEL_FILE = (
    PROJECT_ROOT
    / "models"
    / "workout_weight_model.joblib"
)


FEATURE_COLUMNS = [
    "Exercise Name",

    "previous_weight",
    "previous_volume",
    "previous_reps",
    "previous_1rm",
    "previous_sets",

    "weight_2_sessions_ago",
    "volume_2_sessions_ago",
    "one_rm_2_sessions_ago",

    "weight_3_sessions_ago",
    "volume_3_sessions_ago",
    "one_rm_3_sessions_ago",

    "weight_change",
    "volume_change",
    "reps_change",
    "one_rm_change",

    "weight_change_2",
    "volume_change_2",
    "one_rm_change_2",

    "days_since_previous",
    "previous_session_count",

    "rolling_avg_weight_3",
    "rolling_avg_volume_3",
    "rolling_avg_1rm_3",
    "rolling_avg_reps_3",

    "recent_best_weight_3",
    "recent_best_1rm_3",

    "weight_trend",
    "volume_trend",
    "one_rm_trend",
]

TARGET_COLUMN = "target_weight"


def main():
    print(f"Loading features: {FEATURE_FILE}")

    df = pd.read_csv(FEATURE_FILE)

    df["Date"] = pd.to_datetime(df["Date"])

    df = df.sort_values("Date").reset_index(drop=True)

    model = joblib.load(MODEL_FILE)

    # Same chronological test split used during training.
    test_start = int(len(df) * 0.85)

    test_df = df.iloc[test_start:].copy()

    X_test = test_df[FEATURE_COLUMNS]

    y_test = test_df[TARGET_COLUMN]

    predictions = model.predict(X_test)

    test_df["Predicted Weight"] = predictions

    test_df["Absolute Error"] = (
        test_df["Predicted Weight"]
        - test_df["target_weight"]
    ).abs()

    # ---------------------------------------------------------
    # OVERALL
    # ---------------------------------------------------------

    mae = mean_absolute_error(
        y_test,
        predictions,
    )

    print()
    print("========== EVALUATION ==========")

    print(f"Test rows: {len(test_df)}")

    print(f"Test MAE:  {mae:.2f} lb")

    # ---------------------------------------------------------
    # BEST PREDICTIONS
    # ---------------------------------------------------------

    print()
    print("========== BEST PREDICTIONS ==========")

    best = (
        test_df
        .sort_values("Absolute Error")
        .head(15)
    )

    print(
        best[
            [
                "Date",
                "Exercise Name",
                "previous_weight",
                "weight_trend",
                "Predicted Weight",
                "target_weight",
                "Absolute Error",
            ]
        ].to_string(index=False)
    )

    # ---------------------------------------------------------
    # WORST PREDICTIONS
    # ---------------------------------------------------------

    print()
    print("========== WORST PREDICTIONS ==========")

    worst = (
        test_df
        .sort_values("Absolute Error", ascending=False)
        .head(20)
    )

    print(
        worst[
            [
                "Date",
                "Exercise Name",
                "previous_weight",
                "weight_trend",
                "Predicted Weight",
                "target_weight",
                "Absolute Error",
            ]
        ].to_string(index=False)
    )

    # ---------------------------------------------------------
    # PERFORMANCE BY EXERCISE
    # ---------------------------------------------------------

    print()
    print("========== PERFORMANCE BY EXERCISE ==========")

    by_exercise = (
        test_df
        .groupby("Exercise Name")
        .agg(
            samples=("Absolute Error", "size"),
            mae=("Absolute Error", "mean"),
        )
        .sort_values("samples", ascending=False)
    )

    print(
        by_exercise.head(30).to_string()
    )

    print()
    print("============================================")


if __name__ == "__main__":
    main()