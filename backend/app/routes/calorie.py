from datetime import datetime, time, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.auth.dependencies import get_current_user
from backend.app.db.client import database
from backend.app.schemas.calorie_log import (
    CalorieLogCreate,
    CalorieLogResponse,
)
from backend.app.schemas.calorie_summary import CalorieSummary


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

@router.get(
    "/summary",
    response_model=CalorieSummary,
)
async def get_calorie_summary(
    user_id: str = Depends(get_current_user),
):
    latest_calorie = await database.calorie_logs.find_one(
        {"user_id": user_id},
        sort=[("date", -1)],
    )

    pipeline = [
        {"$match": {"user_id": user_id}},
        {
            "$group": {
                "_id": None,
                "total_calories": {"$sum": "$calories"},
            }
        },
    ]

    cursor = await database.calorie_logs.aggregate(pipeline)

    total_result = await cursor.to_list(length=1)

    total_calories = (
        total_result[0]["total_calories"]
        if total_result
        else 0
    )

    return CalorieSummary(
        latest_calories=(
            latest_calorie["calories"]
            if latest_calorie
            else None
        ),
        total_calories=total_calories,
    )

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