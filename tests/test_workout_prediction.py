import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd

from backend.app.routes.prediction import create_workout_weight_prediction
from backend.app.schemas.prediction import WorkoutWeightPredictionRequest
from backend.app.services import workout_prediction as serving
from ml.progression_features import (
    EXERCISE, FEATURE_COLUMNS, aggregate_sessions, lb_to_kg, supervised_observations,
)
from ml.recommendation import adjust_prediction


class WorkoutPredictionTests(unittest.IsolatedAsyncioTestCase):
    async def test_route_matches_offline_features_and_recommendation(self):
        dates = ["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04"]
        source = pd.DataFrame({
            "Date": dates,
            EXERCISE: ["Squat"] * 4,
            "sets": [2, 1, 3, 1],
            "reps": [4, 5, 6, 7],
            "weight": [100.0, 110.0, 105.0, 108.0],
        })

        async def cursor():
            for record in source.iloc[:3].to_dict("records"):
                yield {
                    "date": record["Date"], "exercise": record[EXERCISE],
                    "sets": record["sets"], "reps": record["reps"],
                    "weight": lb_to_kg(record["weight"]),
                }

            yield {
                "date": "2200-01-01", "exercise": "Squat",
                "sets": 1, "reps": 1, "weight": 100,
            }

        sessions = aggregate_sessions(source, weight_unit="lb")
        train_features = supervised_observations(sessions)[FEATURE_COLUMNS].iloc[0]
        model = serving.load_model()
        self.assertIs(model, serving.load_model())
        self.assertEqual(list(model.feature_names_in_), FEATURE_COLUMNS)
        expected_raw = model.predict(pd.DataFrame([train_features], columns=FEATURE_COLUMNS))[0]
        expected = adjust_prediction(train_features, expected_raw)
        workouts = SimpleNamespace(find=lambda _: cursor())

        with patch.object(serving, "database", SimpleNamespace(workouts=workouts)), (
            patch.object(model, "predict", wraps=model.predict)
        ) as predict:
            result = await create_workout_weight_prediction(
                WorkoutWeightPredictionRequest(exercise_name="Squat"), "athlete"
            )
        actual = predict.call_args.args[0].iloc[0]
        self.assertEqual(actual[EXERCISE], train_features[EXERCISE])
        for feature in FEATURE_COLUMNS[1:]:
            self.assertAlmostEqual(actual[feature], train_features[feature], places=10)
        self.assertEqual(result["recommended_weight"], expected.weight_kg)
        self.assertEqual(result["historical_sessions"], 3)
        self.assertEqual(result["confidence"], result["history_sufficiency"])

    async def test_cold_start_does_not_load_model(self):
        sessions = aggregate_sessions(pd.DataFrame([{
            "Date": "2025-01-01", EXERCISE: "Squat", "sets": 2, "reps": 5, "weight": 50,
        }]), weight_unit="kg")
        with patch.object(serving, "load_user_sessions", return_value=sessions), (
            patch.object(serving, "load_model")
        ) as load:
            result = await serving.recommend_workout_weight("athlete", "Squat")
        self.assertIsNone(result["recommended_weight"])
        self.assertEqual(result["history_sufficiency"], 0)
        load.assert_not_called()
