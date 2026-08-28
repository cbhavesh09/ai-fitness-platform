from pathlib import Path

import joblib
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]

MODEL_FILE = (
    PROJECT_ROOT
    / "models"
    / "workout_weight_model.joblib"
)

FEATURE_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "workout_progression_features.csv"
)


FEATURE_COLUMNS = [
    "Exercise Name",
    "sets",
    "total_reps",
    "total_volume",
    "max_weight",
    "avg_weight",
    "best_1rm",
    "best_reps",
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


_model = None
_features = None

LB_TO_KG = 0.45359237


def lb_to_kg(weight: float) -> float:
    return weight * LB_TO_KG


def load_model():
    global _model

    if _model is None:
        if not MODEL_FILE.exists():
            raise FileNotFoundError(
                f"Workout model not found: {MODEL_FILE}"
            )

        _model = joblib.load(MODEL_FILE)

    return _model


def load_features() -> pd.DataFrame:
    global _features

    if _features is None:
        if not FEATURE_FILE.exists():
            raise FileNotFoundError(
                f"Workout feature file not found: {FEATURE_FILE}"
            )

        df = pd.read_csv(FEATURE_FILE)

        df["Date"] = pd.to_datetime(df["Date"])

        _features = (
            df.sort_values("Date")
            .reset_index(drop=True)
        )

    return _features


def get_supported_exercises() -> list[str]:
    df = load_features()

    excluded_exercises = {
        "Chin Up",
        "Weighted dips",
    }

    exercises = (
        df.loc[
            ~df["Exercise Name"].isin(excluded_exercises),
            "Exercise Name",
        ]
        .dropna()
        .drop_duplicates()
        .sort_values()
        .tolist()
    )

    return exercises


def round_weight(weight: float) -> float:
    return round(weight / 5) * 5


def recommend_workout_weight(
    exercise_name: str,
) -> dict:

    df = load_features()
    model = load_model()

    history = df[
        df["Exercise Name"] == exercise_name
    ].copy()

    history = history.sort_values("Date")

    if history.empty:
        raise ValueError(
            f"No historical data found for exercise: "
            f"{exercise_name}"
        )

    latest = history.iloc[-1]

    previous_weight = float(
        latest["max_weight"]
    )

    sample_count = len(history)

    if sample_count < 10:

        if sample_count < 3:

            recommended = previous_weight

            method = "previous_weight"

            confidence = 0.40

            message = (
                "Very limited history. Maintain the "
                "previous usable weight until more "
                "sessions are recorded."
            )

        else:

            recent = history.tail(3)

            recommended = float(
                recent["max_weight"].median()
            )

            method = "recent_progression"

            confidence = 0.60

            message = (
                "Limited historical data. "
                "Recommendation is based on recent "
                "training performance."
            )

        return {
            "exercise": exercise_name,

            "recommended_weight": round(
                lb_to_kg(recommended),
                1,
            ),

            "previous_weight": round(
                lb_to_kg(previous_weight),
                1,
            ),

            "historical_sessions": sample_count,

            "method": method,

            "confidence": confidence,

            "message": message,
        }

    X = latest[
        FEATURE_COLUMNS
    ].to_frame().T

    prediction = float(
        model.predict(X)[0]
    )

    prediction = max(
        0.0,
        prediction,
    )

    recent = history.tail(3)

    recent_best = float(
        recent["max_weight"].max()
    )

    recent_average = float(
        recent["max_weight"].mean()
    )

    trend = float(
        latest.get("weight_trend", 0)
    )

    if trend > 0:

        ml_weight = 0.60
        recent_weight = 0.40

        message = (
            "Recent performance is trending upward. "
            "The ML prediction supports progressive loading."
        )

    elif trend < 0:

        ml_weight = 0.40
        recent_weight = 0.60

        message = (
            "Recent performance is declining. "
            "The recommendation gives more weight to "
            "recent training performance."
        )

    else:

        ml_weight = 0.50
        recent_weight = 0.50

        message = (
            "Recent performance is relatively stable. "
            "The recommendation combines the ML prediction "
            "with recent training performance."
        )

    blended = (
        prediction * ml_weight
        + recent_average * recent_weight
    )

    lower_bound = min(
        recent_best,
        previous_weight,
    )

    upper_bound = max(
        recent_best,
        previous_weight,
    )

    upper_bound += 5

    if blended < lower_bound:

        blended = lower_bound

        safety_adjustment = (
            "recommendation raised to recent historical range"
        )

    elif blended > upper_bound:

        blended = upper_bound

        safety_adjustment = (
            "recommendation capped at a conservative "
            "historical progression limit"
        )

    else:

        safety_adjustment = (
            "prediction within historical bounds"
        )

    recommended = round_weight(blended)

    return {
        "exercise": exercise_name,

        "recommended_weight": round(
            lb_to_kg(recommended),
            1,
        ),

        "predicted_weight": round(
            lb_to_kg(prediction),
            1,
        ),

        "previous_weight": round(
            lb_to_kg(previous_weight),
            1,
        ),

        "recent_best_weight": round(
            lb_to_kg(recent_best),
            1,
        ),

        "recent_average_weight": round(
            lb_to_kg(recent_average),
            1,
        ),

        "weight_trend": round(
            lb_to_kg(trend),
            1,
        ),

        "historical_sessions": sample_count,

        "method": "random_forest_blended",

        "confidence": 0.90,

        "message": message,

        "safety_adjustment": safety_adjustment,
    }