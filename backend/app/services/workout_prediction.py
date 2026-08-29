from pathlib import Path

import joblib
import pandas as pd

from backend.app.db.client import database


PROJECT_ROOT = Path(__file__).resolve().parents[3]

MODEL_FILE = (
    PROJECT_ROOT
    / "models"
    / "workout_weight_model.joblib"
)

MODEL_FEATURE_COLUMNS = [
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

LB_TO_KG = 0.45359237
KG_TO_LB = 1 / LB_TO_KG

_model = None


def kg_to_lb(weight: float) -> float:
    return weight * KG_TO_LB


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


def calculate_1rm(weight_lb: float, reps: float) -> float:
    return weight_lb * (1 + reps / 30)


async def load_user_sessions(
    user_id: str,
    exercise_name: str,
) -> pd.DataFrame:

    cursor = database.workouts.find(
        {
            "user_id": user_id,
            "exercise": exercise_name,
        }
    ).sort("date", 1)

    workouts = []

    async for workout in cursor:
        workouts.append(
            {
                "Date": workout["date"],
                "Exercise Name": workout["exercise"],
                "sets": workout["sets"],
                "reps": workout["reps"],
                "weight": workout["weight"],
            }
        )

    if not workouts:
        return pd.DataFrame()

    df = pd.DataFrame(workouts)

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce",
    ).dt.normalize()

    df["weight_lb"] = (
        df["weight"]
        .astype(float)
        .apply(kg_to_lb)
    )

    df["reps"] = df["reps"].astype(float)
    df["sets"] = df["sets"].astype(float)

    df["total_reps"] = (
        df["sets"] * df["reps"]
    )

    df["total_volume"] = (
        df["weight_lb"]
        * df["reps"]
        * df["sets"]
    )

    df["max_weight"] = df["weight_lb"]

    df["avg_weight"] = df["weight_lb"]

    df["best_1rm"] = df.apply(
        lambda row: calculate_1rm(
            row["weight_lb"],
            row["reps"],
        ),
        axis=1,
    )

    df["best_reps"] = df["reps"]

    sessions = (
        df.groupby(
            ["Date", "Exercise Name"],
            as_index=False,
        )
        .agg(
            sets=("sets", "sum"),
            total_reps=("total_reps", "sum"),
            total_volume=("total_volume", "sum"),
            max_weight=("max_weight", "max"),
            avg_weight=("avg_weight", "mean"),
            best_1rm=("best_1rm", "max"),
            best_reps=("best_reps", "max"),
        )
    )

    sessions = (
        sessions
        .sort_values("Date")
        .reset_index(drop=True)
    )

    return sessions


def build_next_session_features(
    sessions: pd.DataFrame,
) -> pd.Series:

    latest = sessions.iloc[-1]

    previous = (
        sessions.iloc[-2]
        if len(sessions) >= 2
        else None
    )

    two_ago = (
        sessions.iloc[-3]
        if len(sessions) >= 3
        else None
    )

    three_ago = (
        sessions.iloc[-4]
        if len(sessions) >= 4
        else None
    )

    current_weight = float(
        latest["max_weight"]
    )

    current_volume = float(
        latest["total_volume"]
    )

    current_reps = float(
        latest["total_reps"]
    )

    current_1rm = float(
        latest["best_1rm"]
    )

    current_sets = float(
        latest["sets"]
    )

    previous_weight = (
        float(previous["max_weight"])
        if previous is not None
        else current_weight
    )

    previous_volume = (
        float(previous["total_volume"])
        if previous is not None
        else current_volume
    )

    previous_reps = (
        float(previous["total_reps"])
        if previous is not None
        else current_reps
    )

    previous_1rm = (
        float(previous["best_1rm"])
        if previous is not None
        else current_1rm
    )

    previous_sets = (
        float(previous["sets"])
        if previous is not None
        else current_sets
    )

    weight_2 = (
        float(two_ago["max_weight"])
        if two_ago is not None
        else previous_weight
    )

    volume_2 = (
        float(two_ago["total_volume"])
        if two_ago is not None
        else previous_volume
    )

    one_rm_2 = (
        float(two_ago["best_1rm"])
        if two_ago is not None
        else previous_1rm
    )

    weight_3 = (
        float(three_ago["max_weight"])
        if three_ago is not None
        else weight_2
    )

    volume_3 = (
        float(three_ago["total_volume"])
        if three_ago is not None
        else volume_2
    )

    one_rm_3 = (
        float(three_ago["best_1rm"])
        if three_ago is not None
        else one_rm_2
    )

    days_since_previous = (
        latest["Date"] - previous["Date"]
    ).total_seconds() / 86400 \
        if previous is not None \
        else 0

    recent = sessions.tail(3)

    rolling_avg_weight = (
        recent["max_weight"].mean()
    )

    rolling_avg_volume = (
        recent["total_volume"].mean()
    )

    rolling_avg_1rm = (
        recent["best_1rm"].mean()
    )

    rolling_avg_reps = (
        recent["total_reps"].mean()
    )

    recent_best_weight = (
        recent["max_weight"].max()
    )

    recent_best_1rm = (
        recent["best_1rm"].max()
    )

    return pd.Series(
        {
            "Exercise Name": latest["Exercise Name"],
            "previous_weight": current_weight,
            "previous_volume": current_volume,
            "previous_reps": current_reps,
            "previous_1rm": current_1rm,
            "previous_sets": current_sets,
            "weight_2_sessions_ago": previous_weight,
            "volume_2_sessions_ago": previous_volume,
            "one_rm_2_sessions_ago": previous_1rm,
            "weight_3_sessions_ago": weight_2,
            "volume_3_sessions_ago": volume_2,
            "one_rm_3_sessions_ago": one_rm_2,
            "weight_change": current_weight - previous_weight,
            "volume_change": current_volume - previous_volume,
            "reps_change": current_reps - previous_reps,
            "one_rm_change": current_1rm - previous_1rm,
            "weight_change_2": current_weight - weight_2,
            "volume_change_2": current_volume - volume_2,
            "one_rm_change_2": current_1rm - one_rm_2,
            "days_since_previous": days_since_previous,
            "previous_session_count": len(sessions),
            "rolling_avg_weight_3": rolling_avg_weight,
            "rolling_avg_volume_3": rolling_avg_volume,
            "rolling_avg_1rm_3": rolling_avg_1rm,
            "rolling_avg_reps_3": rolling_avg_reps,
            "recent_best_weight_3": recent_best_weight,
            "recent_best_1rm_3": recent_best_1rm,
            "weight_trend": current_weight - weight_3,
            "volume_trend": current_volume - volume_3,
            "one_rm_trend": current_1rm - one_rm_3,
        }
    )


async def get_user_exercises(
    user_id: str,
) -> list[str]:

    exercises = await database.workouts.distinct(
        "exercise",
        {"user_id": user_id},
    )

    return sorted(
        exercise
        for exercise in exercises
        if exercise
    )


def round_weight(weight_lb: float) -> float:
    return round(weight_lb / 5) * 5


def calculate_confidence(
    session_count: int,
) -> float:

    if session_count < 3:
        return 0.0

    if session_count == 3:
        return 0.60

    if session_count == 4:
        return 0.65

    if session_count == 5:
        return 0.70

    if session_count == 6:
        return 0.75

    if session_count == 7:
        return 0.78

    if session_count >= 8:
        return 0.80

    return 0.60


async def recommend_workout_weight(
    user_id: str,
    exercise_name: str,
) -> dict:

    sessions = await load_user_sessions(
        user_id,
        exercise_name,
    )

    if sessions.empty:
        raise ValueError(
            "You have not recorded this exercise yet."
        )

    session_count = len(sessions)

    latest = sessions.iloc[-1]

    current_weight_lb = float(
        latest["max_weight"]
    )

    if session_count < 3:
        return {
            "exercise": exercise_name,
            "recommended_weight": None,
            "current_weight": round(
                lb_to_kg(current_weight_lb),
                1,
            ),
            "previous_weight": None,
            "historical_sessions": session_count,
            "method": "insufficient_history",
            "confidence": 0.0,
            "message": (
                "Not enough training history for a "
                "recommendation. Record at least "
                "3 sessions for this exercise."
            ),
        }

    features = build_next_session_features(
        sessions
    )

    model = load_model()

    model_input = pd.DataFrame(
        [
            {
                column: features[column]
                for column in MODEL_FEATURE_COLUMNS
            }
        ]
    )

    prediction_lb = float(
        model.predict(model_input)[0]
    )

    prediction_lb = max(
        0.0,
        prediction_lb,
    )

    recent = sessions.tail(3)

    recent_average_lb = float(
        recent["max_weight"].mean()
    )

    recent_best_lb = float(
        recent["max_weight"].max()
    )

    previous_weight_lb = (
        float(sessions.iloc[-2]["max_weight"])
    )

    progression = (
        current_weight_lb
        - previous_weight_lb
    )

    if progression > 0:
        ml_weight = 0.45
        recent_weight = 0.25
        progression_weight = 0.30

        message = (
            "Your recent performance is improving. "
            "The recommendation combines the ML prediction "
            "with your recent progression."
        )

    elif progression < 0:
        ml_weight = 0.35
        recent_weight = 0.45
        progression_weight = 0.20

        message = (
            "Your recent performance has declined. "
            "The recommendation gives more weight to "
            "your recent training performance."
        )

    else:
        ml_weight = 0.45
        recent_weight = 0.45
        progression_weight = 0.10

        message = (
            "Your recent performance is stable. "
            "The recommendation combines the ML prediction "
            "with recent training performance."
        )

    progression_target_lb = (
        current_weight_lb
        + max(0.0, progression)
    )

    blended_lb = (
        prediction_lb * ml_weight
        + recent_average_lb * recent_weight
        + progression_target_lb * progression_weight
    )

    minimum_lb = current_weight_lb

    maximum_progression_lb = (
        current_weight_lb + 10
    )

    if blended_lb < minimum_lb:
        recommended_lb = minimum_lb

        safety_adjustment = (
            "Recommendation kept at the current "
            "working weight because the model predicted "
            "a lower value."
        )

    elif blended_lb > maximum_progression_lb:
        recommended_lb = maximum_progression_lb

        safety_adjustment = (
            "Recommendation capped at a conservative "
            "10 lb progression from the current weight."
        )

    else:
        recommended_lb = blended_lb

        safety_adjustment = (
            "Recommendation is within a conservative "
            "progression range."
        )

    recommended_lb = round_weight(
        recommended_lb
    )

    recommended_kg = round(
        lb_to_kg(recommended_lb) / 2.5
    ) * 2.5

    return {
        "exercise": exercise_name,
        "recommended_weight": recommended_kg,
        "predicted_weight": round(
            lb_to_kg(prediction_lb),
            1,
        ),
        "current_weight": round(
            lb_to_kg(current_weight_lb),
            1,
        ),
        "previous_weight": round(
            lb_to_kg(previous_weight_lb),
            1,
        ),
        "recent_best_weight": round(
            lb_to_kg(recent_best_lb),
            1,
        ),
        "recent_average_weight": round(
            lb_to_kg(recent_average_lb),
            1,
        ),
        "weight_trend": round(
            lb_to_kg(
                float(features["weight_trend"])
            ),
            1,
        ),
        "historical_sessions": session_count,
        "method": "random_forest_progression",
        "confidence": calculate_confidence(
            session_count
        ),
        "message": message,
        "safety_adjustment": safety_adjustment,
    }