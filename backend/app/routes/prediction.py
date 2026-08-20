from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.auth.dependencies import get_current_user
from backend.app.db.client import database
from backend.app.models.prediction import Prediction
from backend.app.models.user import User
from backend.app.schemas.prediction import PredictionResponse
from backend.app.services.prediction import calculate_calorie_burn


router = APIRouter(
    prefix="/predictions",
    tags=["Predictions"],
)


@router.post(
    "/calorie-burn",
    response_model=PredictionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_calorie_burn_prediction(
    user_id: str = Depends(get_current_user),
):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID",
        )

    user_document = await database.users.find_one(
        {"_id": ObjectId(user_id)}
    )

    if user_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user = User(
        name=user_document["name"],
        email=user_document["email"],
        password_hash=user_document["password_hash"],
        age=user_document["age"],
        gender=user_document["gender"],
        height_cm=user_document["height_cm"],
        weight_kg=user_document["weight_kg"],
        activity_level=user_document["activity_level"],
        goal=user_document["goal"],
        created_at=user_document["created_at"],
    )

    calorie_burn, confidence = calculate_calorie_burn(user)

    prediction = Prediction(
        user_id=user_id,
        prediction_type="calorie_burn",
        prediction=f"{calorie_burn} kcal",
        confidence=confidence,
        created_at=datetime.now(timezone.utc),
    )

    result = await database.predictions.insert_one(
        prediction.model_dump()
    )

    return PredictionResponse(
        id=str(result.inserted_id),
        user_id=prediction.user_id,
        prediction_type=prediction.prediction_type,
        prediction=prediction.prediction,
        confidence=prediction.confidence,
        created_at=prediction.created_at,
    )

@router.get(
    "",
    response_model=list[PredictionResponse],
)
async def get_predictions(
    user_id: str = Depends(get_current_user),
):
    predictions = []

    cursor = database.predictions.find(
        {"user_id": user_id}
    ).sort("created_at", -1)

    async for prediction in cursor:
        predictions.append(
            PredictionResponse(
                id=str(prediction["_id"]),
                user_id=prediction["user_id"],
                prediction_type=prediction["prediction_type"],
                prediction=prediction["prediction"],
                confidence=prediction["confidence"],
                created_at=prediction["created_at"],
            )
        )

    return predictions

@router.delete(
    "/{prediction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_prediction(
    prediction_id: str,
    user_id: str = Depends(get_current_user),
):
    if not ObjectId.is_valid(prediction_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found",
        )

    result = await database.predictions.delete_one(
        {
            "_id": ObjectId(prediction_id),
            "user_id": user_id,
        }
    )

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found",
        )