import pandas as pd


FILE = "data/processed/workout_progression_features.csv"

df = pd.read_csv(FILE)

columns = [
    "Date",
    "previous_weight",
    "previous_reps",
    "previous_1rm",
    "weight_2_sessions_ago",
    "weight_3_sessions_ago",
    "weight_change",
    "weight_change_2",
    "weight_trend",
    "recent_best_weight_3",
    "target_weight",
]

exercises = [
    "Chin Up",
    "Weighted dips",
    "Deadlift - Trap Bar",
]

for exercise in exercises:
    print()
    print("=" * 70)
    print(exercise)
    print("=" * 70)

    history = df[
        df["Exercise Name"] == exercise
    ].tail(15)

    print(
        history[columns].to_string(index=False)
    )