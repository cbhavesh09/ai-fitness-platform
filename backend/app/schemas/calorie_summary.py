from pydantic import BaseModel


class CalorieSummary(BaseModel):
    latest_calories: float | None
    total_calories: float