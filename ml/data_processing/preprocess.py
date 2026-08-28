from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = PROJECT_ROOT / "data" / "weightlifting_721_workouts.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "weightlifting_clean.csv"


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


def normalize_exercise_name(name: str) -> str:
    name = str(name).strip()
    name = " ".join(name.split())

    return EXERCISE_ALIASES.get(name, name)


def main() -> None:
    print(f"Loading dataset: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE)

    original_rows = len(df)

    print(f"Original rows: {original_rows}")

    # ---------------------------------------------------------
    # 1. Normalize exercise names FIRST
    # ---------------------------------------------------------

    df["Exercise Name"] = df["Exercise Name"].apply(
        normalize_exercise_name
    )

    # ---------------------------------------------------------
    # 2. Remove duplicates AFTER normalization
    # ---------------------------------------------------------

    duplicate_count = df.duplicated().sum()

    print(
        f"Exact duplicate rows after normalization: "
        f"{duplicate_count}"
    )

    df = df.drop_duplicates().copy()

    print(
        f"Rows after duplicate removal: {len(df)}"
    )

    # ---------------------------------------------------------
    # 3. Validate dates
    # ---------------------------------------------------------

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce",
    )

    invalid_dates = df["Date"].isna().sum()

    if invalid_dates:
        raise ValueError(
            f"Found {invalid_dates} invalid dates."
        )

    # ---------------------------------------------------------
    # 4. Handle text columns
    # ---------------------------------------------------------

    df["Notes"] = df["Notes"].fillna("")
    df["Workout Notes"] = df["Workout Notes"].fillna("")

    # ---------------------------------------------------------
    # 5. Convert numeric columns
    # ---------------------------------------------------------

    numeric_columns = [
        "Set Order",
        "Weight",
        "Reps",
        "Distance",
        "Seconds",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    numeric_missing = df[numeric_columns].isna().sum()

    if numeric_missing.any():
        print("Warning: missing numeric values:")
        print(
            numeric_missing[numeric_missing > 0]
        )

    # ---------------------------------------------------------
    # 6. Create date features
    # ---------------------------------------------------------

    df["Session Date"] = df["Date"].dt.date

    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["Day"] = df["Date"].dt.day

    # ---------------------------------------------------------
    # 7. Create training-related features
    # ---------------------------------------------------------

    df["Volume"] = (
        df["Weight"] * df["Reps"]
    )

    df["Estimated 1RM"] = (
        df["Weight"]
        * (1 + df["Reps"] / 30)
    )

    # ---------------------------------------------------------
    # 8. Sort the dataset
    # ---------------------------------------------------------

    df = df.sort_values(
        [
            "Date",
            "Exercise Name",
            "Set Order",
        ]
    ).reset_index(drop=True)

    # ---------------------------------------------------------
    # 9. Save processed dataset
    # ---------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # ---------------------------------------------------------
    # 10. Final validation
    # ---------------------------------------------------------

    remaining_duplicates = df.duplicated().sum()

    print()
    print(
        "========== PREPROCESSING COMPLETE =========="
    )
    print(
        f"Original rows:       {original_rows}"
    )
    print(
        f"Clean rows:          {len(df)}"
    )
    print(
        f"Duplicates remaining: {remaining_duplicates}"
    )
    print(
        f"Columns:             {len(df.columns)}"
    )
    print(
        f"Unique exercises:    "
        f"{df['Exercise Name'].nunique()}"
    )
    print(
        f"Unique sessions:     "
        f"{df['Date'].nunique()}"
    )
    print(
        f"Calendar dates:      "
        f"{df['Session Date'].nunique()}"
    )
    print(
        f"Output:              {OUTPUT_FILE}"
    )
    print(
        "============================================"
    )


if __name__ == "__main__":
    main()
