"""Shared production adjustment for a next-session prediction."""
from dataclasses import dataclass
from math import ceil, floor, isfinite

from ml.progression_features import lb_to_kg


@dataclass(frozen=True)
class Recommendation:
    weight_kg: float
    lower_kg: float
    upper_kg: float
    message: str
    adjustment: str


def adjust_prediction(features, prediction_lb, *, max_increase_lb=10.0,
                      max_decrease_lb=10.0, increment_kg=2.5):
    if not all(isfinite(value) for value in (
        prediction_lb, max_increase_lb, max_decrease_lb, increment_kg
    )) or min(max_increase_lb, max_decrease_lb) < 0 or increment_kg <= 0:
        raise ValueError("Invalid prediction or recommendation bounds.")

    current = float(features["previous_weight"])
    change = float(features["weight_change"])
    if change > 0:
        model_share, average_share, trend_share = 0.45, 0.25, 0.30
        message = "Your most recent working weight increased."
    elif change < 0:
        model_share, average_share, trend_share = 0.35, 0.45, 0.20
        message = "Your most recent working weight decreased."
    else:
        model_share, average_share, trend_share = 0.45, 0.45, 0.10
        message = "Your most recent working weight held steady."

    blended = (
        model_share * max(0.0, prediction_lb)
        + average_share * float(features["rolling_avg_weight_3"])
        + trend_share * max(0.0, current + change)
    )
    lower = lb_to_kg(max(0.0, current - max_decrease_lb))
    upper = lb_to_kg(current + max_increase_lb)
    bounded = min(max(lb_to_kg(blended), lower), upper)
    first_step = ceil(lower / increment_kg)
    last_step = floor(upper / increment_kg)
    if first_step <= last_step:
        step = min(max(round(bounded / increment_kg), first_step), last_step)
        rounded = step * increment_kg
        if lower <= rounded <= upper:
            return Recommendation(rounded, lower, upper, message,
                                  "Rounded within the configured weight bounds.")
    return Recommendation(bounded, lower, upper, message,
                          "Returned without rounding because no increment fits the bounds.")
