from pathlib import Path

import joblib
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

MODEL_FILE = PROJECT_ROOT / "models" / "workout_weight_model.joblib"

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


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

# Exercises where 5 lb increments are practical.
DEFAULT_INCREMENT = 5.0

# Exercises where smaller increments make more sense.
SMALL_INCREMENT_EXERCISES = {
    "Lateral Raise (Dumbbells)",
    "Hammer Curl (Dumbbell )",
    "Bicep Curl (Barbell)",
    "Face pull",
}

SMALL_INCREMENT = 2.5


# Minimum number of historical sessions required
# before trusting the Random Forest.
HIGH_CONFIDENCE_SESSIONS = 10
MEDIUM_CONFIDENCE_SESSIONS = 5


# ---------------------------------------------------------
# BASIC HELPERS
# ---------------------------------------------------------

def round_weight(
    weight: float,
    exercise_name: str,
) -> float:
    """
    Round a weight to a practical gym increment.
    """

    if weight <= 0:
        return 0.0

    if exercise_name in SMALL_INCREMENT_EXERCISES:
        increment = SMALL_INCREMENT
    else:
        increment = DEFAULT_INCREMENT

    return round(weight / increment) * increment


def load_model():
    if not MODEL_FILE.exists():
        raise FileNotFoundError(
            f"Model not found: {MODEL_FILE}"
        )

    return joblib.load(MODEL_FILE)


def load_features() -> pd.DataFrame:

    if not FEATURE_FILE.exists():
        raise FileNotFoundError(
            f"Feature file not found: {FEATURE_FILE}"
        )

    df = pd.read_csv(FEATURE_FILE)

    df["Date"] = pd.to_datetime(
        df["Date"]
    )

    return (
        df
        .sort_values("Date")
        .reset_index(drop=True)
    )


def get_exercise_history(
    df: pd.DataFrame,
    exercise_name: str,
) -> pd.DataFrame:

    history = df[
        df["Exercise Name"] == exercise_name
    ].copy()

    return history.sort_values(
        "Date"
    ).reset_index(drop=True)


# ---------------------------------------------------------
# RECENT PERFORMANCE
# ---------------------------------------------------------

def analyze_recent_performance(
    history: pd.DataFrame,
) -> dict:
    """
    Analyze the athlete's most recent progression.

    We intentionally use historical sessions only.
    """

    recent = history.tail(3)

    weights = recent["max_weight"]

    previous_weight = float(
        history.iloc[-1]["max_weight"]
    )

    recent_best = float(
        weights.max()
    )

    recent_average = float(
        weights.mean()
    )

    if len(weights) >= 2:
        latest_change = float(
            weights.iloc[-1]
            - weights.iloc[-2]
        )
    else:
        latest_change = 0.0

    if len(weights) >= 3:
        older_average = float(
            weights.iloc[:-1].mean()
        )

        trend = (
            previous_weight
            - older_average
        )
    else:
        trend = latest_change

    return {
        "previous_weight": previous_weight,
        "recent_best": recent_best,
        "recent_average": recent_average,
        "latest_change": latest_change,
        "trend": trend,
    }


# ---------------------------------------------------------
# SANITY CHECK
# ---------------------------------------------------------

def apply_sanity_bounds(
    prediction: float,
    history: pd.DataFrame,
    exercise_name: str,
) -> tuple[float, str]:

    latest_weight = float(
        history.iloc[-1]["max_weight"]
    )

    recent = history.tail(3)

    recent_weights = recent[
        "max_weight"
    ]

    recent_best = float(
        recent_weights.max()
    )

    recent_low = float(
        recent_weights.min()
    )

    # -----------------------------------------------------
    # No meaningful previous weight.
    # -----------------------------------------------------

    if latest_weight <= 0:

        # If recent history contains a positive value,
        # use that as the anchor.
        positive_recent = (
            recent_weights[
                recent_weights > 0
            ]
        )

        if not positive_recent.empty:

            anchor = float(
                positive_recent.iloc[-1]
            )

            # Don't allow a huge jump from the
            # recent usable value.
            lower = max(
                0.0,
                anchor - 20,
            )

            upper = anchor + 20

            bounded = min(
                max(prediction, lower),
                upper,
            )

            return (
                bounded,
                "bounded around recent usable weight",
            )

        return (
            max(0.0, prediction),
            "no positive historical anchor",
        )

    # -----------------------------------------------------
    # Normal case.
    #
    # Don't allow a single prediction to jump
    # unrealistically far away from recent performance.
    # -----------------------------------------------------

    lower = max(
        0.0,
        recent_low - 30,
    )

    upper = recent_best + 30

    bounded = min(
        max(prediction, lower),
        upper,
    )

    if bounded != prediction:
        return (
            bounded,
            "prediction constrained by recent performance",
        )

    return (
        prediction,
        "prediction within historical bounds",
    )


# ---------------------------------------------------------
# RECOMMENDATION LOGIC
# ---------------------------------------------------------

def recommend_weight(
    model,
    df: pd.DataFrame,
    exercise_name: str,
) -> dict:

    history = get_exercise_history(
        df,
        exercise_name,
    )

    # -----------------------------------------------------
    # No history
    # -----------------------------------------------------

    if history.empty:

        return {
            "exercise": exercise_name,
            "recommended_weight": None,
            "method": "insufficient_data",
            "confidence": "low",
            "message": (
                "No historical data found "
                "for this exercise."
            ),
        }

    sample_count = len(history)

    performance = (
        analyze_recent_performance(
            history
        )
    )

    previous_weight = (
        performance["previous_weight"]
    )

    recent_best = (
        performance["recent_best"]
    )

    recent_average = (
        performance["recent_average"]
    )

    trend = performance["trend"]

    # -----------------------------------------------------
    # VERY LIMITED HISTORY
    # -----------------------------------------------------

    if sample_count < MEDIUM_CONFIDENCE_SESSIONS:

        if previous_weight > 0:

            recommended = previous_weight

            method = "previous_weight"
            confidence = "low"

            message = (
                "Very limited history. "
                "Maintain the previous usable "
                "weight until more sessions are recorded."
            )

        else:

            recommended = recent_best

            method = "recent_best"
            confidence = "low"

            message = (
                "Very limited history. "
                "Using the most recent usable "
                "historical weight."
            )

        return {
            "exercise": exercise_name,
            "recommended_weight": round_weight(
                recommended,
                exercise_name,
            ),
            "previous_weight": previous_weight,
            "historical_sessions": sample_count,
            "recent_best": recent_best,
            "recent_average": recent_average,
            "trend": trend,
            "method": method,
            "confidence": confidence,
            "message": message,
        }

    # -----------------------------------------------------
    # MODERATE HISTORY
    # -----------------------------------------------------

    if sample_count < HIGH_CONFIDENCE_SESSIONS:

        recent = history.tail(3)

        recent_median = float(
            recent["max_weight"].median()
        )

        # Blend recent median with previous weight.
        # This reduces sensitivity to a single unusual session.
        if previous_weight > 0:

            recommended = (
                0.6 * previous_weight
                + 0.4 * recent_median
            )

        else:

            recommended = recent_median

        recommended, bound_reason = (
            apply_sanity_bounds(
                recommended,
                history,
                exercise_name,
            )
        )

        return {
            "exercise": exercise_name,
            "recommended_weight": round_weight(
                recommended,
                exercise_name,
            ),
            "predicted_weight": None,
            "previous_weight": previous_weight,
            "historical_sessions": sample_count,
            "recent_best": recent_best,
            "recent_average": recent_average,
            "trend": trend,
            "method": "recent_progression",
            "confidence": "medium",
            "message": (
                "Moderate historical data. "
                "Recommendation is based on recent "
                f"progression ({bound_reason})."
            ),
        }

    # -----------------------------------------------------
    # RANDOM FOREST
    # -----------------------------------------------------

    latest = history.iloc[-1]

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

    raw_prediction = prediction

    # -----------------------------------------------------
    # Constrain prediction using recent history.
    # -----------------------------------------------------

    prediction, bound_reason = (
        apply_sanity_bounds(
            prediction,
            history,
            exercise_name,
        )
    )

    # -----------------------------------------------------
    # Blend ML prediction with recent performance.
    #
    # The ML model gets the majority of the weight,
    # but recent real performance prevents extreme
    # recommendations.
    # -----------------------------------------------------

    if previous_weight > 0:

        blended_prediction = (
            0.70 * prediction
            + 0.30 * recent_average
        )

    else:

        blended_prediction = prediction

    # -----------------------------------------------------
    # Progression sanity check.
    #
    # If the model predicts a very large jump relative
    # to the previous usable weight, cap it.
    # -----------------------------------------------------

    if previous_weight > 0:

        maximum_jump = 20.0

        upper_progression_limit = (
            previous_weight
            + maximum_jump
        )

        lower_progression_limit = max(
            0.0,
            previous_weight
            - maximum_jump,
        )

        blended_prediction = min(
            blended_prediction,
            upper_progression_limit,
        )

        blended_prediction = max(
            blended_prediction,
            lower_progression_limit,
        )

    recommended = round_weight(
        blended_prediction,
        exercise_name,
    )

    # -----------------------------------------------------
    # Confidence
    # -----------------------------------------------------

    if sample_count >= HIGH_CONFIDENCE_SESSIONS:

        confidence = "high"

    else:

        confidence = "medium"

    # -----------------------------------------------------
    # Human-readable message
    # -----------------------------------------------------

    if trend > 10:

        message = (
            "Recent performance is trending upward. "
            "The ML prediction supports progressive loading."
        )

    elif trend < -10:

        message = (
            "Recent performance has declined. "
            "The recommendation is kept conservative "
            "to avoid an excessive jump."
        )

    else:

        message = (
            "Recent performance is relatively stable. "
            "The recommendation combines the ML prediction "
            "with recent training performance."
        )

    return {
        "exercise": exercise_name,
        "recommended_weight": recommended,
        "predicted_weight": raw_prediction,
        "previous_weight": previous_weight,
        "historical_sessions": sample_count,
        "recent_best": recent_best,
        "recent_average": recent_average,
        "trend": trend,
        "method": "random_forest_blended",
        "confidence": confidence,
        "message": message,
        "bound_reason": bound_reason,
    }


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    print("Loading model...")
    model = load_model()

    print("Loading features...")
    df = load_features()

    exercises = [
        "Incline Bench Press (Barbell)",
        "Squat (Barbell)",
        "Leg press (hinge )",
        "Deadlift - Trap Bar",
    ]

    print()
    print(
        "========== RECOMMENDATIONS =========="
    )

    for exercise in exercises:

        result = recommend_weight(
            model,
            df,
            exercise,
        )

        print()
        print(
            f"Exercise:          "
            f"{result['exercise']}"
        )

        print(
            f"Recommended:       "
            f"{result['recommended_weight']}"
        )

        print(
            f"Previous:          "
            f"{result.get('previous_weight')}"
        )

        print(
            f"ML Prediction:     "
            f"{result.get('predicted_weight')}"
        )

        print(
            f"Recent Best:       "
            f"{result.get('recent_best')}"
        )

        print(
            f"Recent Average:    "
            f"{result.get('recent_average')}"
        )

        print(
            f"Trend:             "
            f"{result.get('trend')}"
        )

        print(
            f"History:           "
            f"{result.get('historical_sessions')}"
        )

        print(
            f"Method:            "
            f"{result['method']}"
        )

        print(
            f"Confidence:        "
            f"{result['confidence']}"
        )

        print(
            f"Message:           "
            f"{result['message']}"
        )

        if result.get("bound_reason"):
            print(
                f"Safety adjustment: "
                f"{result['bound_reason']}"
            )

    print()
    print(
        "======================================"
    )


if __name__ == "__main__":
    main()