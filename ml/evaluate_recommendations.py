from pathlib import Path

import joblib
import pandas as pd

from recommendation import (
    load_features,
    load_model,
    recommend_weight,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main():

    print("Loading model...")
    model = load_model()

    print("Loading features...")
    df = load_features()

    exercises = sorted(
        df["Exercise Name"].unique()
    )

    results = []

    for exercise in exercises:

        result = recommend_weight(
            model,
            df,
            exercise,
        )

        previous = result.get(
            "previous_weight"
        )

        recommended = result.get(
            "recommended_weight"
        )

        if (
            previous is not None
            and recommended is not None
        ):
            change = (
                recommended
                - previous
            )
        else:
            change = None

        results.append(
            {
                "exercise": exercise,
                "history": result.get(
                    "historical_sessions"
                ),
                "previous": previous,
                "recommended": recommended,
                "change": change,
                "ml_prediction": result.get(
                    "predicted_weight"
                ),
                "confidence": result.get(
                    "confidence"
                ),
                "method": result.get(
                    "method"
                ),
            }
        )

    results_df = pd.DataFrame(
        results
    )

    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------

    print()
    print(
        "========== RECOMMENDATION EVALUATION =========="
    )

    print(
        f"Exercises evaluated: "
        f"{len(results_df)}"
    )

    print()

    print(
        "========== BY CONFIDENCE =========="
    )

    print(
        results_df[
            "confidence"
        ].value_counts().to_string()
    )

    print()

    print(
        "========== BY METHOD =========="
    )

    print(
        results_df[
            "method"
        ].value_counts().to_string()
    )

    # --------------------------------------------------
    # LARGEST INCREASES
    # --------------------------------------------------

    print()
    print(
        "========== LARGEST INCREASES =========="
    )

    increases = (
        results_df
        .dropna(subset=["change"])
        .sort_values(
            "change",
            ascending=False,
        )
        .head(15)
    )

    print(
        increases[
            [
                "exercise",
                "history",
                "previous",
                "recommended",
                "change",
                "confidence",
                "method",
            ]
        ].to_string(index=False)
    )

    # --------------------------------------------------
    # LARGEST DECREASES
    # --------------------------------------------------

    print()
    print(
        "========== LARGEST DECREASES =========="
    )

    decreases = (
        results_df
        .dropna(subset=["change"])
        .sort_values(
            "change",
            ascending=True,
        )
        .head(15)
    )

    print(
        decreases[
            [
                "exercise",
                "history",
                "previous",
                "recommended",
                "change",
                "confidence",
                "method",
            ]
        ].to_string(index=False)
    )

    # --------------------------------------------------
    # SUSPICIOUS LARGE CHANGES
    # --------------------------------------------------

    suspicious = (
        results_df[
            results_df["change"].abs() >= 30
        ]
        .sort_values(
            "change"
        )
    )

    print()
    print(
        "========== SUSPICIOUS CHANGES (>= 30 LB) =========="
    )

    if suspicious.empty:

        print(
            "No recommendations changed "
            "by 30 lb or more."
        )

    else:

        print(
            suspicious[
                [
                    "exercise",
                    "history",
                    "previous",
                    "recommended",
                    "change",
                    "confidence",
                    "method",
                ]
            ].to_string(index=False)
        )

    # --------------------------------------------------
    # FINAL TABLE
    # --------------------------------------------------

    output_file = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / "recommendation_evaluation.csv"
    )

    results_df.to_csv(
        output_file,
        index=False,
    )

    print()
    print(
        f"Full results saved to: "
        f"{output_file}"
    )

    print(
        "==============================================="
    )


if __name__ == "__main__":
    main()