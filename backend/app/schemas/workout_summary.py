from pydantic import BaseModel


class WorkoutSummary(BaseModel):
    total_workouts: int
    today_workouts: int