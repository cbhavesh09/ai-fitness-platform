from datetime import date

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    current_weight: float | None
    latest_calories: float | None
    total_workouts: int
    latest_prediction: str | None
    prediction_confidence: float | None
    date: date