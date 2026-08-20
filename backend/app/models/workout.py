from datetime import date

from pydantic import BaseModel, Field


class Workout(BaseModel):
    user_id: str
    exercise: str = Field(min_length=1)
    muscle_group: str = Field(min_length=1)
    sets: int = Field(gt=0)
    reps: int = Field(gt=0)
    weight: float = Field(ge=0)
    duration: float = Field(ge=0)
    date: date