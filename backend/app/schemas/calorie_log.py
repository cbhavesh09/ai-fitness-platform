from datetime import date

from pydantic import BaseModel,Field


class CalorieLogCreate(BaseModel):
    calories: float = Field(..., gt=0)
    date: date


class CalorieLogResponse(BaseModel):
    id: str
    user_id: str
    calories: float
    date: date