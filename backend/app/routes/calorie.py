from datetime import datetime, time, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.auth.dependencies import get_current_user
from backend.app.db.client import database
from backend.app.schemas.calorie_log import (
    CalorieLogCreate,
    CalorieLogResponse,
)


router = APIRouter(
    prefix="/calories",
    tags=["Calories"],
)


@router.post(
    "",
    response_model=CalorieLogResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_calorie_log(
    calorie_data: CalorieLogCreate,
    user_id: str = Depends(get_current_user),
):
    calorie_datetime = datetime.combine(
        calorie_data.date,
        time.min,
        tzinfo=timezone.utc,
    )

    document = {
        "user_id": user_id,
        "calories": calorie_data.calories,
        "date": calorie_datetime,
    }

    result = await database.calorie_logs.insert_one(document)

    return CalorieLogResponse(
        id=str(result.inserted_id),
        user_id=user_id,
        calories=calorie_data.calories,
        date=calorie_data.date,
    )

@router.get(
    "",
    response_model=list[CalorieLogResponse],
)
async def get_calorie_logs(
    user_id: str = Depends(get_current_user),
):
    calorie_logs = []

    cursor = database.calorie_logs.find(
        {"user_id": user_id}
    ).sort("date", -1)

    async for calorie_log in cursor:
        calorie_logs.append(
            CalorieLogResponse(
                id=str(calorie_log["_id"]),
                user_id=calorie_log["user_id"],
                calories=calorie_log["calories"],
                date=calorie_log["date"].date(),
            )
        )

    return calorie_logs

@router.delete(
    "/{calorie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_calorie_log(
    calorie_id: str,
    user_id: str = Depends(get_current_user),
):
    if not ObjectId.is_valid(calorie_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calorie log not found",
        )

    result = await database.calorie_logs.delete_one(
        {
            "_id": ObjectId(calorie_id),
            "user_id": user_id,
        }
    )

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calorie log not found",
        )