from datetime import date

from pydantic import BaseModel, Field


class WeightLog(BaseModel):
    user_id: str
    weight: float = Field(gt=0)
    date: date