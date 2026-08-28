from pathlib import Path

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "workout_progression_features.csv"
)

MODEL_DIR = PROJECT_ROOT / "models"

MODEL_FILE = (
    MODEL_DIR
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


def rmse(y_true, y_pred):
    return mean_squared_error(
        y_true,
        y_pred,
    ) ** 0.5


def main():
    print(f"Loading features: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE)

    df["Date"] = pd.to_datetime(df["Date"])

    df = df.sort_values("Date").reset_index(drop=True)

    print(f"Total rows: {len(df)}")

    # ---------------------------------------------------------
    # VERIFY NO LEAKAGE
    # ---------------------------------------------------------

    forbidden_current_features = [
        "sets",
        "total_reps",
        "total_volume",
        "max_weight",
        "avg_weight",
        "best_1rm",
        "best_reps",
    ]

    leaked = [
        column
        for column in forbidden_current_features
        if column in FEATURE_COLUMNS
    ]

    if leaked:
        raise ValueError(
            f"Data leakage detected. "
            f"Current-session columns found in features: {leaked}"
        )

    print()
    print("No current-session target leakage detected.")

    # ---------------------------------------------------------
    # FEATURES / TARGET
    # ---------------------------------------------------------

    X = df[FEATURE_COLUMNS]

    y = df[TARGET_COLUMN]

    # ---------------------------------------------------------
    # CHRONOLOGICAL SPLIT
    # ---------------------------------------------------------

    n = len(df)

    train_end = int(n * 0.70)

    validation_end = int(n * 0.85)

    X_train = X.iloc[:train_end]
    y_train = y.iloc[:train_end]

    X_validation = X.iloc[
        train_end:validation_end
    ]

    y_validation = y.iloc[
        train_end:validation_end
    ]

    X_test = X.iloc[validation_end:]

    y_test = y.iloc[validation_end:]

    print()
    print("========== DATA SPLIT ==========")

    print(f"Training:    {len(X_train)} rows")
    print(f"Validation:  {len(X_validation)} rows")
    print(f"Test:        {len(X_test)} rows")

    print()
    print("Date ranges:")

    print(
        "Train:       "
        f"{df['Date'].iloc[0]} -> "
        f"{df['Date'].iloc[train_end - 1]}"
    )

    print(
        "Validation:  "
        f"{df['Date'].iloc[train_end]} -> "
        f"{df['Date'].iloc[validation_end - 1]}"
    )

    print(
        "Test:        "
        f"{df['Date'].iloc[validation_end]} -> "
        f"{df['Date'].iloc[-1]}"
    )

    # ---------------------------------------------------------
    # PREPROCESSING
    # ---------------------------------------------------------

    categorical_features = [
        "Exercise Name"
    ]

    numerical_features = [
        column
        for column in FEATURE_COLUMNS
        if column not in categorical_features
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "exercise",
                OneHotEncoder(
                    handle_unknown="ignore"
                ),
                categorical_features,
            ),
            (
                "numeric",
                "passthrough",
                numerical_features,
            ),
        ]
    )

    # ---------------------------------------------------------
    # MODEL
    # ---------------------------------------------------------

    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=12,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )

    pipeline = Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor,
            ),
            (
                "model",
                model,
            ),
        ]
    )

    print()
    print("Training Random Forest...")

    pipeline.fit(
        X_train,
        y_train,
    )

    # ---------------------------------------------------------
    # PREDICTIONS
    # ---------------------------------------------------------

    validation_predictions = pipeline.predict(
        X_validation
    )

    test_predictions = pipeline.predict(
        X_test
    )

    # ---------------------------------------------------------
    # MODEL METRICS
    # ---------------------------------------------------------

    validation_mae = mean_absolute_error(
        y_validation,
        validation_predictions,
    )

    validation_rmse = rmse(
        y_validation,
        validation_predictions,
    )

    test_mae = mean_absolute_error(
        y_test,
        test_predictions,
    )

    test_rmse = rmse(
        y_test,
        test_predictions,
    )

    # ---------------------------------------------------------
    # BASELINE
    # ---------------------------------------------------------

    validation_baseline = X_validation[
        "previous_weight"
    ]

    test_baseline = X_test[
        "previous_weight"
    ]

    validation_baseline_mae = mean_absolute_error(
        y_validation,
        validation_baseline,
    )

    test_baseline_mae = mean_absolute_error(
        y_test,
        test_baseline,
    )

    improvement = (
        1
        - test_mae / test_baseline_mae
    ) * 100

    # ---------------------------------------------------------
    # RESULTS
    # ---------------------------------------------------------

    print()
    print("========== MODEL RESULTS ==========")

    print()
    print("Random Forest")

    print(
        f"Validation MAE:  {validation_mae:.2f}"
    )

    print(
        f"Validation RMSE: {validation_rmse:.2f}"
    )

    print(
        f"Test MAE:        {test_mae:.2f}"
    )

    print(
        f"Test RMSE:       {test_rmse:.2f}"
    )

    print()
    print("Baseline: previous weight")

    print(
        f"Validation MAE:  "
        f"{validation_baseline_mae:.2f}"
    )

    print(
        f"Test MAE:        "
        f"{test_baseline_mae:.2f}"
    )

    print()
    print(
        "Model improvement over baseline:"
    )

    print(
        f"{improvement:.2f}%"
    )

    # ---------------------------------------------------------
    # SAVE MODEL
    # ---------------------------------------------------------

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        pipeline,
        MODEL_FILE,
    )

    print()
    print("========== TRAINING COMPLETE ==========")

    print(
        f"Model saved to: {MODEL_FILE}"
    )

    print(
        "========================================"
    )


if __name__ == "__main__":
    main()