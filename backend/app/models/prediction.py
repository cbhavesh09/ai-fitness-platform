from datetime import datetime

from pydantic import BaseModel, Field


class Prediction(BaseModel):
    user_id: str
    prediction_type: str = Field(min_length=1)
    prediction: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    created_at: datetime