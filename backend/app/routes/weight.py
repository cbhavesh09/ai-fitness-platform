from datetime import datetime, time, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId

from backend.app.auth.dependencies import get_current_user
from backend.app.db.client import database
from backend.app.schemas.weight_log import WeightLogCreate, WeightLogResponse
from backend.app.schemas.weight_summary import WeightSummary


router = APIRouter(
    prefix="/weight",
    tags=["Weight"],
)


@router.post(
    "",
    response_model=WeightLogResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_weight_log(
    weight_data: WeightLogCreate,
    user_id: str = Depends(get_current_user),
):
    weight_datetime = datetime.combine(
        weight_data.date,
        time.min,
        tzinfo=timezone.utc,
    )

    document = {
        "user_id": user_id,
        "weight": weight_data.weight,
        "date": weight_datetime,
    }

    result = await database.weight_logs.insert_one(document)

    return WeightLogResponse(
        id=str(result.inserted_id),
        user_id=user_id,
        weight=weight_data.weight,
        date=weight_data.date,
    )

@router.get(
    "",
    response_model=list[WeightLogResponse],
)
async def get_weight_logs(
    user_id: str = Depends(get_current_user),
):
    weight_logs = []

    cursor = database.weight_logs.find(
        {"user_id": user_id}
    ).sort("date", -1)

    async for weight_log in cursor:
        weight_logs.append(
            WeightLogResponse(
                id=str(weight_log["_id"]),
                user_id=weight_log["user_id"],
                weight=weight_log["weight"],
                date=weight_log["date"].date(),
            )
        )

    return weight_logs
@router.get(
    "/summary",
    response_model=WeightSummary,
)

async def get_weight_summary(
    user_id: str = Depends(get_current_user),
):
    latest_weight = await database.weight_logs.find_one(
        {"user_id": user_id},
        sort=[("date", -1)],
    )

    earliest_weight = await database.weight_logs.find_one(
        {"user_id": user_id},
        sort=[("date", 1)],
    )

    if latest_weight is None or earliest_weight is None:
        return WeightSummary(
            current_weight=None,
            starting_weight=None,
            weight_change=None,
        )

    current_weight = latest_weight["weight"]
    starting_weight = earliest_weight["weight"]

    return WeightSummary(
        current_weight=current_weight,
        starting_weight=starting_weight,
        weight_change=current_weight - starting_weight,
    )

@router.delete(
    "/{weight_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_weight_log(
    weight_id: str,
    user_id: str = Depends(get_current_user),
):
    if not ObjectId.is_valid(weight_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Weight log not found",
        )

    result = await database.weight_logs.delete_one(
        {
            "_id": ObjectId(weight_id),
            "user_id": user_id,
        }
    )

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Weight log not found",
        )