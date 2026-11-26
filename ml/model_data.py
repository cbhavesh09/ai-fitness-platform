"""Common paths and date-grouped partitions for training and evaluation."""
from pathlib import Path

import pandas as pd

from ml.progression_features import FEATURE_COLUMNS, TARGET_COLUMN, session_dates

ROOT = Path(__file__).resolve().parents[1]
FEATURE_FILE = ROOT / "data/processed/workout_progression_features.csv"
MODEL_FILE = ROOT / "models/workout_weight_model.joblib"


def load_features():
    frame = pd.read_csv(FEATURE_FILE, parse_dates=["Date"])
    metadata = ["Date"] + (["athlete_id"] if "athlete_id" in frame else [])
    if list(frame.columns) != metadata + FEATURE_COLUMNS + [TARGET_COLUMN]:
        raise ValueError("Feature CSV has an incompatible schema. Regenerate features first.")
    return frame


def chronological_split(frame):
    ordered = frame.assign(Date=session_dates(frame["Date"])).sort_values("Date", kind="stable")
    groups = ordered.groupby("Date").size().cumsum()
    if len(groups) < 3:
        raise ValueError("Training, validation and test require at least three dates.")
    train_end = (groups.iloc[:-2] - len(ordered) * 0.70).abs().idxmin()
    validation_end = (groups.loc[groups.index > train_end].iloc[:-1]
                      - len(ordered) * 0.85).abs().idxmin()
    return (
        ordered.loc[ordered["Date"] <= train_end],
        ordered.loc[ordered["Date"].gt(train_end) & ordered["Date"].le(validation_end)],
        ordered.loc[ordered["Date"] > validation_end],
    )


def print_partitions(partitions):
    for label, frame in zip(("Train", "Validation", "Test"), partitions):
        dates = frame["Date"]
        print(f"{label}: {len(frame)} rows, {dates.min().date()} to {dates.max().date()}")
