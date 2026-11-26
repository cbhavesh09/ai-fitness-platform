import unittest

import pandas as pd
from pandas.testing import assert_series_equal

from ml.model_data import chronological_split
from ml.progression_features import (
    EXERCISE, FEATURE_COLUMNS, MIN_HISTORY, aggregate_sessions,
    build_next_session_features, kg_to_lb, lb_to_kg, supervised_observations,
)
from ml.recommendation import adjust_prediction


def example_sets():
    return pd.DataFrame({
        "Date": pd.date_range("2025-01-01", periods=6, freq="2D"),
        EXERCISE: ["Squat"] * 6,
        "sets": [1, 2, 3, 4, 1, 1],
        "reps": [2, 3, 4, 5, 6, 7],
        "weight": [10, 20, 30, 40, 50, 60],
    })


class ProgressionFeatureTests(unittest.TestCase):
    def setUp(self):
        self.sessions = aggregate_sessions(example_sets(), weight_unit="lb")

    def test_target_independence(self):
        original = supervised_observations(self.sessions).iloc[0]
        changed = self.sessions.copy()
        changed.loc[3, ["max_weight", "total_reps", "total_volume", "best_1rm", "sets"]] += 100
        observation = supervised_observations(changed).iloc[0]
        self.assertEqual(observation.target_weight, original.target_weight + 100)
        assert_series_equal(observation.drop(labels="target_weight"),
                            original.drop(labels="target_weight"))

    def test_future_independence(self):
        original = supervised_observations(self.sessions.iloc[:4]).iloc[0]
        changed = self.sessions.copy()
        changed.loc[4:, ["max_weight", "total_reps", "total_volume", "best_1rm"]] += 100
        assert_series_equal(original, supervised_observations(changed).iloc[0])

    def test_historical_calculations(self):
        features = build_next_session_features(self.sessions.iloc[:4])
        expected = {
            "previous_weight": 40, "previous_volume": 800, "previous_reps": 20,
            "previous_1rm": 40 * (1 + 5 / 30), "previous_sets": 4,
            "weight_2_sessions_ago": 30, "volume_2_sessions_ago": 360,
            "one_rm_2_sessions_ago": 34,
            "weight_3_sessions_ago": 20, "volume_3_sessions_ago": 120,
            "one_rm_3_sessions_ago": 22,
            "weight_change": 10, "volume_change": 440, "reps_change": 8,
            "one_rm_change": 40 * (1 + 5 / 30) - 34,
            "weight_change_2": 20, "volume_change_2": 680,
            "one_rm_change_2": 40 * (1 + 5 / 30) - 22,
            "days_since_previous": 2, "previous_session_count": 4,
            "rolling_avg_weight_3": 30, "rolling_avg_volume_3": 1280 / 3,
            "rolling_avg_1rm_3": (22 + 34 + 40 * (1 + 5 / 30)) / 3,
            "rolling_avg_reps_3": 38 / 3, "recent_best_weight_3": 40,
            "recent_best_1rm_3": 40 * (1 + 5 / 30),
            "weight_trend": 30, "volume_trend": 780,
            "one_rm_trend": 40 * (1 + 5 / 30) - 10 * (1 + 2 / 30),
        }
        self.assertEqual(set(expected), set(FEATURE_COLUMNS[1:]))
        for name, value in expected.items():
            with self.subTest(feature=name):
                self.assertAlmostEqual(features[name], value)
        fallback = build_next_session_features(self.sessions.iloc[:3])
        self.assertAlmostEqual(fallback["weight_trend"], 20)
        self.assertAlmostEqual(fallback["volume_trend"], 340)
        self.assertAlmostEqual(fallback["one_rm_trend"], 34 - 10 * (1 + 2 / 30))

    def test_cold_start(self):
        for count in range(MIN_HISTORY):
            self.assertIsNone(build_next_session_features(self.sessions.iloc[:count]))
        self.assertIsNotNone(build_next_session_features(self.sessions.iloc[:MIN_HISTORY]))

    def test_exercise_and_athlete_isolation(self):
        athlete = self.sessions.assign(athlete_id="A")
        other_athlete = athlete.assign(athlete_id="B", max_weight=999)
        other_exercise = athlete.assign(**{EXERCISE: "Row", "max_weight": 100})
        mixed = pd.concat([athlete, other_athlete, other_exercise], ignore_index=True)
        observations = supervised_observations(mixed)
        same_exercise = observations[observations[EXERCISE] == "Squat (Barbell)"]
        pd.testing.assert_frame_equal(
            same_exercise[same_exercise.athlete_id == "A"].reset_index(drop=True),
            supervised_observations(athlete),
        )
        with self.assertRaises(ValueError):
            build_next_session_features(mixed)

    def test_partition_dates_are_disjoint(self):
        sessions = pd.concat([self.sessions, self.sessions], ignore_index=True)
        train, validation, test = chronological_split(sessions)
        self.assertLess(train.Date.max(), validation.Date.min())
        self.assertLess(validation.Date.max(), test.Date.min())
        self.assertEqual(len(train) + len(validation) + len(test), len(sessions))

    def test_unit_conversion_and_same_day_aggregation(self):
        self.assertAlmostEqual(lb_to_kg(100), 45.359237)
        self.assertAlmostEqual(kg_to_lb(45.359237), 100)
        rows = example_sets().iloc[:2].copy()
        rows["Date"] = ["2025-01-01 09:00:00", "2025-01-01 19:00:00"]
        lbs = aggregate_sessions(rows, weight_unit="lb")
        kg = aggregate_sessions(rows.assign(weight=lb_to_kg(rows.weight)), weight_unit="kg")
        pd.testing.assert_frame_equal(lbs, kg, check_dtype=False)
        session = lbs.iloc[0]
        self.assertEqual((session.sets, session.total_reps, session.total_volume,
                          session.max_weight, session.best_1rm), (3, 8, 140, 20, 22))

    def test_invalid_records_fail_explicitly(self):
        for field, value in (("Date", "invalid"), ("Date", 1234), ("weight", float("nan")), ("sets", 0)):
            with self.subTest(field=field), self.assertRaises(ValueError):
                aggregate_sessions(example_sets().assign(**{field: value}), weight_unit="lb")

    def test_recommendation_decreases_and_rounding_respects_bounds(self):
        features = {"previous_weight": 113, "weight_change": -10,
                    "rolling_avg_weight_3": 120}
        lower = adjust_prediction(features, 0)
        upper = adjust_prediction(features, 1000)
        for result in (lower, upper):
            self.assertLessEqual(result.lower_kg, result.weight_kg)
            self.assertLessEqual(result.weight_kg, result.upper_kg)
        self.assertLess(lower.weight_kg, lb_to_kg(113))
        fallback = adjust_prediction(features, 0, max_increase_lb=0, max_decrease_lb=0)
        self.assertEqual(fallback.weight_kg, lb_to_kg(113))
