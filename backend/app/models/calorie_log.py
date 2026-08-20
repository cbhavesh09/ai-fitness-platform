from datetime import date

from pydantic import BaseModel, Field


class CalorieLog(BaseModel):
    user_id: str
    calories: float = Field(gt=0)
    date: date