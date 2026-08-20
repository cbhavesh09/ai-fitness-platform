from pydantic import BaseModel


class WeightSummary(BaseModel):
    current_weight: float | None
    starting_weight: float | None
    weight_change: float | None