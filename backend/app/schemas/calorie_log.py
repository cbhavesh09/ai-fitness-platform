from datetime import date

from pydantic import BaseModel


class CalorieLogCreate(BaseModel):
    calories: float
    date: date


class CalorieLogResponse(BaseModel):
    id: str
    user_id: str
    calories: float
    date: date