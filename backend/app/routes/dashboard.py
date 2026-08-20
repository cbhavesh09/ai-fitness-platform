from datetime import date, datetime, time, timezone

from fastapi import APIRouter, Depends

from backend.app.auth.dependencies import get_current_user
from backend.app.db.client import database
from backend.app.schemas.dashboard import DashboardSummary


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "",
    response_model=DashboardSummary,
)
async def get_dashboard(
    user_id: str = Depends(get_current_user),
):
    latest_weight = await database.weight_logs.find_one(
        {"user_id": user_id},
        sort=[("date", -1)],
    )

    latest_calories = await database.calorie_logs.find_one(
        {"user_id": user_id},
        sort=[("date", -1)],
    )

    total_workouts = await database.workouts.count_documents(
        {"user_id": user_id}
    )

    today = date.today()
    start_of_day = datetime.combine(
        today,
        time.min,
        tzinfo=timezone.utc,
    )
    end_of_day = datetime.combine(
    today,
    time.max,
    tzinfo=timezone.utc,
)
    today_workouts = await database.workouts.count_documents(
    {
        "user_id": user_id,
        "date": {
            "$gte": start_of_day,
            "$lte": end_of_day,
        },
    }
)


    latest_prediction = await database.predictions.find_one(
        {"user_id": user_id},
        sort=[("created_at", -1)],
    )

    return DashboardSummary(
        current_weight=(
            latest_weight["weight"]
            if latest_weight
            else None
        ),
        latest_calories=(
            latest_calories["calories"]
            if latest_calories
            else None
        ),
        total_workouts=total_workouts,
        today_workouts=today_workouts,
        latest_prediction=(
            latest_prediction["prediction"]
            if latest_prediction
            else None
        ),
        prediction_confidence=(
            latest_prediction["confidence"]
            if latest_prediction
            else None
        ),
        date=date.today(),
    )