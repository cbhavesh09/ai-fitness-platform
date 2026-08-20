from datetime import date

from pydantic import BaseModel


class WorkoutCreate(BaseModel):
    exercise: str
    muscle_group: str
    sets: int
    reps: int
    weight: float
    duration: float
    date: date


class WorkoutResponse(BaseModel):
    id: str
    user_id: str
    exercise: str
    muscle_group: str
    sets: int
    reps: int
    weight: float
    duration: float
    date: date