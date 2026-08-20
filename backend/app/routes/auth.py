from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from backend.app.auth.password import hash_password
from backend.app.db.client import database
from backend.app.models.user import User
from backend.app.schemas.user import UserCreate, UserResponse
from backend.app.auth.jwt import create_access_token
from backend.app.auth.password import hash_password, verify_password
from backend.app.schemas.user import UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(user_data: UserCreate):
    existing_user = await database.users.find_one(
        {"email": user_data.email}
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        age=user_data.age,
        gender=user_data.gender,
        height_cm=user_data.height_cm,
        weight_kg=user_data.weight_kg,
        activity_level=user_data.activity_level,
        goal=user_data.goal,
        created_at=datetime.now(timezone.utc),
    )

    result = await database.users.insert_one(
        user.model_dump()
    )

    return UserResponse(
        id=str(result.inserted_id),
        name=user.name,
        email=user.email,
        age=user.age,
        gender=user.gender,
        height_cm=user.height_cm,
        weight_kg=user.weight_kg,
        activity_level=user.activity_level,
        goal=user.goal,
        created_at=user.created_at,
    )

@router.post("/login")
async def login(user_data: UserLogin):
    user = await database.users.find_one(
        {"email": user_data.email}
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(
        user_data.password,
        user["password_hash"],
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(str(user["_id"]))

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }