"""Shared session aggregation and next-session features in pounds."""

from numbers import Number

import numpy as np
import pandas as pd

MIN_HISTORY = 3
LB_TO_KG = 0.45359237
FEATURE_SCHEMA_VERSION = 2
EXERCISE = "Exercise Name"
TARGET_COLUMN = "target_weight"
SESSION_STATS = ["sets", "total_reps", "total_volume", "max_weight", "best_1rm"]
FEATURE_COLUMNS = [
    EXERCISE,
    "previous_weight", "previous_volume", "previous_reps", "previous_1rm",
    "previous_sets",
    "weight_2_sessions_ago", "volume_2_sessions_ago", "one_rm_2_sessions_ago",
    "weight_3_sessions_ago", "volume_3_sessions_ago", "one_rm_3_sessions_ago",
    "weight_change", "volume_change", "reps_change", "one_rm_change",
    "weight_change_2", "volume_change_2", "one_rm_change_2",
    "days_since_previous", "previous_session_count",
    "rolling_avg_weight_3", "rolling_avg_volume_3", "rolling_avg_1rm_3",
    "rolling_avg_reps_3", "recent_best_weight_3", "recent_best_1rm_3",
    "weight_trend", "volume_trend", "one_rm_trend",
]

EXERCISE_ALIASES = {
    "Incline Bench Press": "Incline Bench Press (Barbell)",
    "Squat": "Squat (Barbell)",
    "Seated Row": "Seated Cable Row (close Grip)",
    "Good Morning": "Good Morning (Barbell)",
    "Bicep Curl (barbell )": "Bicep Curl (Barbell)",
    "Lateral Raise": "Lateral Raise (Dumbbells)",
    "Hammer Curl": "Hammer Curl (Dumbbell )",
    "Leg press": "Leg press (hinge )",
}
EXCLUDED_EXERCISES = {"Chin Up", "Weighted dips"}


def normalize_exercise_name(name):
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Every workout record must have an exercise name.")
    name = " ".join(name.split())
    return EXERCISE_ALIASES.get(name, name)


def kg_to_lb(weight):
    return weight / LB_TO_KG


def lb_to_kg(weight):
    return weight * LB_TO_KG


def session_dates(values):
    if values.map(lambda value: isinstance(value, Number)).any():
        raise ValueError("Numeric workout dates are unsupported.")
    dates = pd.to_datetime(values, format="mixed", utc=True, errors="raise")
    if dates.isna().any():
        raise ValueError("Workout session dates must be present.")
    return dates.dt.tz_convert(None).dt.normalize()


def validate_numeric(frame, columns):
    frame[columns] = frame[columns].apply(pd.to_numeric, errors="raise")
    values = frame[columns].to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Workout statistics must be finite nonnegative numbers.")


def aggregate_sessions(records, *, weight_unit):
    """Aggregate set records by UTC calendar date, exercise and optional athlete_id.

    Pass per-set reps and a sets multiplier (1 for a raw set).
    """
    groups = ["Date", EXERCISE]
    if "athlete_id" in records:
        groups.append("athlete_id")
    if records.empty:
        return pd.DataFrame(columns=groups + SESSION_STATS)
    if weight_unit not in {"lb", "kg"}:
        raise ValueError(f"Unsupported weight unit: {weight_unit}")

    rows = records[groups + ["weight", "reps", "sets"]].copy()
    rows["Date"] = session_dates(rows["Date"])
    rows[EXERCISE] = rows[EXERCISE].map(normalize_exercise_name)
    if rows[groups].isna().any().any():
        raise ValueError("Session identifiers must be present.")
    validate_numeric(rows, ["weight", "reps", "sets"])
    if (rows["sets"] < 1).any() or (rows["sets"] % 1 != 0).any():
        raise ValueError("Set counts must be positive integers.")
    weight = rows["weight"]
    if weight_unit == "kg":
        weight = kg_to_lb(weight)
    rows["max_weight"] = weight
    rows["total_reps"] = rows["sets"] * rows["reps"]
    rows["total_volume"] = weight * rows["total_reps"]
    rows["best_1rm"] = weight * (1 + rows["reps"] / 30)
    sessions = rows.groupby(groups, as_index=False).agg(
        sets=("sets", "sum"),
        total_reps=("total_reps", "sum"),
        total_volume=("total_volume", "sum"),
        max_weight=("max_weight", "max"),
        best_1rm=("best_1rm", "max"),
    )
    validate_numeric(sessions, SESSION_STATS)
    excluded = sessions[EXERCISE].isin(EXCLUDED_EXERCISES)
    squat_outlier = sessions[EXERCISE].eq("Squat (Barbell)") & sessions["max_weight"].gt(1000)
    return sessions.loc[~(excluded | squat_outlier)].reset_index(drop=True)


def build_next_session_features(history):
    """Build features from completed sessions for one athlete and exercise.

    Trends compare the latest session with the fourth latest, or the third
    latest when only three exist. Return None during cold start.
    """
    if len(history) < MIN_HISTORY:
        return None
    if history[EXERCISE].nunique(dropna=False) != 1 or history[EXERCISE].isna().any():
        raise ValueError("Feature history must contain exactly one exercise.")
    if "athlete_id" in history and (
        history["athlete_id"].nunique(dropna=False) != 1 or history["athlete_id"].isna().any()
    ):
        raise ValueError("Feature history must contain exactly one athlete.")

    dates = session_dates(history["Date"])
    if dates.duplicated().any():
        raise ValueError("Aggregate workouts to one session per exercise and date.")
    ordered = history.assign(Date=dates).sort_values("Date")
    validate_numeric(ordered, SESSION_STATS)
    recent = ordered.tail(4)
    latest, previous, third = (recent.iloc[-lag] for lag in (1, 2, 3))
    trend_start = recent.iloc[0]
    window = recent.tail(3)
    features = {
        EXERCISE: latest[EXERCISE],
        "previous_weight": latest["max_weight"],
        "previous_volume": latest["total_volume"],
        "previous_reps": latest["total_reps"],
        "previous_1rm": latest["best_1rm"],
        "previous_sets": latest["sets"],
        "weight_2_sessions_ago": previous["max_weight"],
        "volume_2_sessions_ago": previous["total_volume"],
        "one_rm_2_sessions_ago": previous["best_1rm"],
        "weight_3_sessions_ago": third["max_weight"],
        "volume_3_sessions_ago": third["total_volume"],
        "one_rm_3_sessions_ago": third["best_1rm"],
        "weight_change": latest["max_weight"] - previous["max_weight"],
        "volume_change": latest["total_volume"] - previous["total_volume"],
        "reps_change": latest["total_reps"] - previous["total_reps"],
        "one_rm_change": latest["best_1rm"] - previous["best_1rm"],
        "weight_change_2": latest["max_weight"] - third["max_weight"],
        "volume_change_2": latest["total_volume"] - third["total_volume"],
        "one_rm_change_2": latest["best_1rm"] - third["best_1rm"],
        "days_since_previous": (latest["Date"] - previous["Date"]).days,
        "previous_session_count": len(history),
        "rolling_avg_weight_3": window["max_weight"].mean(),
        "rolling_avg_volume_3": window["total_volume"].mean(),
        "rolling_avg_1rm_3": window["best_1rm"].mean(),
        "rolling_avg_reps_3": window["total_reps"].mean(),
        "recent_best_weight_3": window["max_weight"].max(),
        "recent_best_1rm_3": window["best_1rm"].max(),
        "weight_trend": latest["max_weight"] - trend_start["max_weight"],
        "volume_trend": latest["total_volume"] - trend_start["total_volume"],
        "one_rm_trend": latest["best_1rm"] - trend_start["best_1rm"],
    }
    return pd.Series(features, index=FEATURE_COLUMNS)


def walk_forward(sessions):
    """Yield each target and the strictly earlier sessions for its exercise and athlete."""
    groups = [EXERCISE]
    if "athlete_id" in sessions:
        groups.append("athlete_id")
    ordered = sessions.assign(Date=session_dates(sessions["Date"])).sort_values("Date")
    if ordered[groups].isna().any().any():
        raise ValueError("Session identifiers must be present.")
    if ordered.duplicated(groups + ["Date"]).any():
        raise ValueError("Duplicate exercise session dates.")
    for _, group in ordered.groupby(groups):
        for index in range(len(group)):
            yield group.iloc[index], group.iloc[:index]


def supervised_observations(sessions):
    rows = []
    has_athletes = "athlete_id" in sessions
    for target, history in walk_forward(sessions):
        features = build_next_session_features(history)
        if features is None:
            continue
        row = features.to_dict()
        row["Date"] = target["Date"]
        row[TARGET_COLUMN] = target["max_weight"]
        if has_athletes:
            row["athlete_id"] = target["athlete_id"]
        rows.append(row)
    metadata = ["Date"] + (["athlete_id"] if has_athletes else [])
    result = pd.DataFrame(rows, columns=metadata + FEATURE_COLUMNS + [TARGET_COLUMN])
    validate_numeric(result, [TARGET_COLUMN])
    return result.sort_values(["Date", EXERCISE]).reset_index(drop=True)
