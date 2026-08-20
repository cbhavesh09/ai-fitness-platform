from datetime import date

from pydantic import BaseModel, Field


class WeightLogCreate(BaseModel):
    weight: float = Field(..., gt=0)
    date: date


class WeightLogResponse(BaseModel):
    id: str
    user_id: str
    weight: float
    date: date