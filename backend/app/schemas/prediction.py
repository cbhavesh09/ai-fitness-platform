from datetime import datetime

from pydantic import BaseModel


class PredictionResponse(BaseModel):
    id: str
    user_id: str
    prediction_type: str
    prediction: str
    confidence: float
    created_at: datetime


class WorkoutWeightPredictionRequest(BaseModel):
    exercise_name: str