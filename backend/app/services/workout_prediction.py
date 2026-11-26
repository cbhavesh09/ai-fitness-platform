from functools import lru_cache

import joblib
import pandas as pd

from backend.app.db.client import database
from ml.model_data import MODEL_FILE
from ml.progression_features import (
    EXERCISE,
    FEATURE_COLUMNS,
    FEATURE_SCHEMA_VERSION,
    MIN_HISTORY,
    aggregate_sessions,
    build_next_session_features,
    lb_to_kg,
)
from ml.recommendation import adjust_prediction


@lru_cache(maxsize=1)
def load_model():
    model = joblib.load(MODEL_FILE)
    if (getattr(model, "progression_schema_version", None) != FEATURE_SCHEMA_VERSION
            or list(model.feature_names_in_) != FEATURE_COLUMNS):
        raise RuntimeError("Workout model has an incompatible feature schema. Retrain offline.")
    return model


async def load_user_sessions(user_id: str, exercise_name: str) -> pd.DataFrame:
    cursor = database.workouts.find({"user_id": user_id, "exercise": exercise_name})
    workouts = [
        {
            "Date": workout.get("date"),
            EXERCISE: workout.get("exercise"),
            "sets": workout.get("sets"),
            "reps": workout.get("reps"),
            "weight": workout.get("weight"),
        }
        async for workout in cursor
    ]
    sessions = aggregate_sessions(pd.DataFrame(workouts), weight_unit="kg")
    if sessions.empty:
        return sessions
    today = pd.Timestamp.now(tz="UTC").tz_localize(None).normalize()
    return sessions.loc[sessions["Date"] <= today]


async def get_user_exercises(user_id: str) -> list[str]:
    exercises = await database.workouts.distinct("exercise", {"user_id": user_id})
    return sorted(exercise for exercise in exercises if exercise)


def history_sufficiency(session_count: int) -> float:
    scores = (0.60, 0.65, 0.70, 0.75, 0.78, 0.80)
    if session_count < MIN_HISTORY:
        return 0.0
    return scores[min(session_count - MIN_HISTORY, len(scores) - 1)]


async def recommend_workout_weight(user_id: str, exercise_name: str) -> dict:
    sessions = await load_user_sessions(user_id, exercise_name)
    if sessions.empty:
        raise ValueError("No eligible recorded sessions for this exercise.")

    session_count = len(sessions)
    features = build_next_session_features(sessions)
    sufficiency = history_sufficiency(session_count)
    response = {
        "exercise": exercise_name,
        "historical_sessions": session_count,
        "history_sufficiency": sufficiency,
        # Legacy response key for existing clients. This is a history-count heuristic.
        "confidence": sufficiency,
    }
    if features is None:
        current = sessions.sort_values("Date").iloc[-1]["max_weight"]
        return {
            **response,
            "recommended_weight": None,
            "current_weight": round(lb_to_kg(float(current)), 1),
            "previous_weight": None,
            "method": "insufficient_history",
            "message": f"Record at least {MIN_HISTORY} completed sessions for this exercise.",
        }

    model_input = pd.DataFrame([features], columns=FEATURE_COLUMNS)
    prediction = float(load_model().predict(model_input)[0])
    recommendation = adjust_prediction(features, prediction)
    return {
        **response,
        "recommended_weight": recommendation.weight_kg,
        "predicted_weight": round(lb_to_kg(max(0.0, prediction)), 1),
        "current_weight": round(lb_to_kg(float(features["previous_weight"])), 1),
        "previous_weight": round(lb_to_kg(float(features["weight_2_sessions_ago"])), 1),
        "recent_best_weight": round(lb_to_kg(float(features["recent_best_weight_3"])), 1),
        "recent_average_weight": round(lb_to_kg(float(features["rolling_avg_weight_3"])), 1),
        "weight_trend": round(lb_to_kg(float(features["weight_trend"])), 1),
        "method": "random_forest_progression",
        "message": recommendation.message,
        "safety_adjustment": recommendation.adjustment,
    }
