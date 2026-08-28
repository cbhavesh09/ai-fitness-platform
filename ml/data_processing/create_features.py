from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "weightlifting_clean.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

OUTPUT_FILE = (
    OUTPUT_DIR
    / "workout_progression_features.csv"
)


def main() -> None:
    print(f"Loading dataset: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE)

    df["Date"] = pd.to_datetime(df["Date"])

    df = df.sort_values(
        ["Exercise Name", "Date"]
    ).reset_index(drop=True)

    # ---------------------------------------------------------
    # SESSION / EXERCISE AGGREGATION
    # ---------------------------------------------------------

    session_exercise = (
        df.groupby(
            ["Date", "Session Date", "Exercise Name"],
            as_index=False,
        )
        .agg(
            sets=("Reps", "size"),
            total_reps=("Reps", "sum"),
            total_volume=("Volume", "sum"),
            max_weight=("Weight", "max"),
            avg_weight=("Weight", "mean"),
            best_1rm=("Estimated 1RM", "max"),
            best_reps=("Reps", "max"),
        )
    )

    session_exercise["Date"] = pd.to_datetime(
        session_exercise["Date"]
    )

    session_exercise = session_exercise.sort_values(
        ["Exercise Name", "Date"]
    ).reset_index(drop=True)

    print()
    print(
        f"Session/exercise rows: {len(session_exercise)}"
    )

    # ---------------------------------------------------------
    # ML DATA QUALITY FILTERS
    # ---------------------------------------------------------

    EXCLUDED_ML_EXERCISES = {
        "Chin Up",
        "Weighted dips",
    }

    before_exercise_filter = len(session_exercise)

    session_exercise = session_exercise[
        ~session_exercise["Exercise Name"].isin(
            EXCLUDED_ML_EXERCISES
        )
    ].copy()

    removed_exercises = (
        before_exercise_filter - len(session_exercise)
    )

    # Remove the known extreme squat outlier.
    squat_outlier_mask = (
        (session_exercise["Exercise Name"] == "Squat (Barbell)")
        & (session_exercise["max_weight"] > 1000)
    )

    squat_outliers = int(
        squat_outlier_mask.sum()
    )

    session_exercise = session_exercise[
        ~squat_outlier_mask
    ].copy()

    session_exercise = session_exercise.sort_values(
        ["Exercise Name", "Date"]
    ).reset_index(drop=True)

    print()
    print(
        "========== ML DATA QUALITY FILTER =========="
    )
    print(
        f"Excluded exercise rows: {removed_exercises}"
    )
    print(
        "Excluded exercises:     "
        f"{', '.join(sorted(EXCLUDED_ML_EXERCISES))}"
    )
    print(
        f"Squat outliers removed: {squat_outliers}"
    )
    print(
        f"Remaining rows:         {len(session_exercise)}"
    )
    print(
        "============================================"
    )

    # ---------------------------------------------------------
    # HISTORICAL FEATURES
    # ---------------------------------------------------------

    grouped = session_exercise.groupby(
        "Exercise Name",
        group_keys=False,
    )

    # Previous session
    session_exercise["previous_weight"] = grouped[
        "max_weight"
    ].shift(1)

    session_exercise["previous_volume"] = grouped[
        "total_volume"
    ].shift(1)

    session_exercise["previous_reps"] = grouped[
        "total_reps"
    ].shift(1)

    session_exercise["previous_1rm"] = grouped[
        "best_1rm"
    ].shift(1)

    session_exercise["previous_sets"] = grouped[
        "sets"
    ].shift(1)

    # Two sessions ago
    session_exercise["weight_2_sessions_ago"] = grouped[
        "max_weight"
    ].shift(2)

    session_exercise["volume_2_sessions_ago"] = grouped[
        "total_volume"
    ].shift(2)

    session_exercise["one_rm_2_sessions_ago"] = grouped[
        "best_1rm"
    ].shift(2)

    # Three sessions ago
    session_exercise["weight_3_sessions_ago"] = grouped[
        "max_weight"
    ].shift(3)

    session_exercise["volume_3_sessions_ago"] = grouped[
        "total_volume"
    ].shift(3)

    session_exercise["one_rm_3_sessions_ago"] = grouped[
        "best_1rm"
    ].shift(3)

    # ---------------------------------------------------------
    # CHANGES
    # ---------------------------------------------------------

    session_exercise["weight_change"] = (
        session_exercise["max_weight"]
        - session_exercise["previous_weight"]
    )

    session_exercise["volume_change"] = (
        session_exercise["total_volume"]
        - session_exercise["previous_volume"]
    )

    session_exercise["reps_change"] = (
        session_exercise["total_reps"]
        - session_exercise["previous_reps"]
    )

    session_exercise["one_rm_change"] = (
        session_exercise["best_1rm"]
        - session_exercise["previous_1rm"]
    )

    session_exercise["weight_change_2"] = (
        session_exercise["max_weight"]
        - session_exercise["weight_2_sessions_ago"]
    )

    session_exercise["volume_change_2"] = (
        session_exercise["total_volume"]
        - session_exercise["volume_2_sessions_ago"]
    )

    session_exercise["one_rm_change_2"] = (
        session_exercise["best_1rm"]
        - session_exercise["one_rm_2_sessions_ago"]
    )

    # ---------------------------------------------------------
    # TIME FEATURES
    # ---------------------------------------------------------

    session_exercise["days_since_previous"] = (
        grouped["Date"]
        .diff()
        .dt.total_seconds()
        .div(86400)
    )

    session_exercise["previous_session_count"] = (
        grouped.cumcount()
    )

    # ---------------------------------------------------------
    # ROLLING FEATURES
    # ---------------------------------------------------------

    # Shift first so the current session is NOT included
    # in its own historical rolling statistics.

    shifted_weight = grouped["max_weight"].shift(1)

    shifted_volume = grouped["total_volume"].shift(1)

    shifted_1rm = grouped["best_1rm"].shift(1)

    shifted_reps = grouped["total_reps"].shift(1)

    session_exercise["rolling_avg_weight_3"] = (
        shifted_weight
        .groupby(
            session_exercise["Exercise Name"]
        )
        .transform(
            lambda x: x.rolling(
                3,
                min_periods=1,
            ).mean()
        )
    )

    session_exercise["rolling_avg_volume_3"] = (
        shifted_volume
        .groupby(
            session_exercise["Exercise Name"]
        )
        .transform(
            lambda x: x.rolling(
                3,
                min_periods=1,
            ).mean()
        )
    )

    session_exercise["rolling_avg_1rm_3"] = (
        shifted_1rm
        .groupby(
            session_exercise["Exercise Name"]
        )
        .transform(
            lambda x: x.rolling(
                3,
                min_periods=1,
            ).mean()
        )
    )

    session_exercise["rolling_avg_reps_3"] = (
        shifted_reps
        .groupby(
            session_exercise["Exercise Name"]
        )
        .transform(
            lambda x: x.rolling(
                3,
                min_periods=1,
            ).mean()
        )
    )

    # ---------------------------------------------------------
    # RECENT BEST PERFORMANCE
    # ---------------------------------------------------------

    session_exercise["recent_best_weight_3"] = (
        shifted_weight
        .groupby(
            session_exercise["Exercise Name"]
        )
        .transform(
            lambda x: x.rolling(
                3,
                min_periods=1,
            ).max()
        )
    )

    session_exercise["recent_best_1rm_3"] = (
        shifted_1rm
        .groupby(
            session_exercise["Exercise Name"]
        )
        .transform(
            lambda x: x.rolling(
                3,
                min_periods=1,
            ).max()
        )
    )

    # ---------------------------------------------------------
    # TREND FEATURES
    # ---------------------------------------------------------

    session_exercise["weight_trend"] = (
        session_exercise["previous_weight"]
        - session_exercise["weight_3_sessions_ago"]
    )

    session_exercise["volume_trend"] = (
        session_exercise["previous_volume"]
        - session_exercise["volume_3_sessions_ago"]
    )

    session_exercise["one_rm_trend"] = (
        session_exercise["previous_1rm"]
        - session_exercise["one_rm_3_sessions_ago"]
    )

    # ---------------------------------------------------------
    # TARGET
    # ---------------------------------------------------------

    # Predict the current session's maximum weight
    # using only information available before the session.

    session_exercise["target_weight"] = (
        session_exercise["max_weight"]
    )

    # ---------------------------------------------------------
    # REMOVE FIRST SESSION(S)
    # ---------------------------------------------------------

    ml_df = session_exercise[
        session_exercise["previous_weight"].notna()
    ].copy()

    # ---------------------------------------------------------
    # FILL HISTORICAL FEATURES
    # ---------------------------------------------------------

    historical_columns = [
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

    ml_df[historical_columns] = (
        ml_df[historical_columns].fillna(0)
    )

    # ---------------------------------------------------------
    # FINAL SORT
    # ---------------------------------------------------------

    ml_df = ml_df.sort_values(
        ["Date", "Exercise Name"]
    ).reset_index(drop=True)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    ml_df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # ---------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------

    print()
    print(
        "========== FEATURE ENGINEERING COMPLETE =========="
    )

    print(
        f"Session/exercise rows: {len(session_exercise)}"
    )

    print(
        f"ML feature rows:       {len(ml_df)}"
    )

    print(
        f"Features/columns:      {len(ml_df.columns)}"
    )

    print(
        f"Exercises:             "
        f"{ml_df['Exercise Name'].nunique()}"
    )

    print(
        f"Date range:            "
        f"{ml_df['Date'].min()} to "
        f"{ml_df['Date'].max()}"
    )

    print(
        f"Output:                {OUTPUT_FILE}"
    )

    print(
        "=================================================="
    )


if __name__ == "__main__":
    main()