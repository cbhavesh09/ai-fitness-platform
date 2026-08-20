from datetime import date

from pydantic import BaseModel


class WeightLogCreate(BaseModel):
    weight: float
    date: date


class WeightLogResponse(BaseModel):
    id: str
    user_id: str
    weight: float
    date: date