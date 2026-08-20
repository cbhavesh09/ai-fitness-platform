from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.auth.dependencies import get_current_user
from backend.app.db.client import database
from backend.app.schemas.user import UserResponse


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/me",
    response_model=UserResponse,
)
async def get_current_user_profile(
    user_id: str = Depends(get_current_user),
):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID",
        )

    user = await database.users.find_one(
        {"_id": ObjectId(user_id)}
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse(
        id=str(user["_id"]),
        name=user["name"],
        email=user["email"],
        age=user["age"],
        gender=user["gender"],
        height_cm=user["height_cm"],
        weight_kg=user["weight_kg"],
        activity_level=user["activity_level"],
        goal=user["goal"],
        created_at=user["created_at"],
    )