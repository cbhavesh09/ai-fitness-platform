from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.app.db.client import client
from fastapi import Depends
from backend.app.auth.dependencies import get_current_user
from backend.app.routes.auth import router as auth_router
from backend.app.auth.jwt import create_access_token
from backend.app.auth.password import hash_password, verify_password
from backend.app.schemas.user import UserCreate, UserLogin, UserResponse
from backend.app.routes.workouts import router as workout_router
from backend.app.routes.weight import router as weight_router
from backend.app.routes.calorie import router as calorie_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await client.admin.command("ping")
    yield
    await client.close()


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(workout_router)
app.include_router(weight_router)
app.include_router(calorie_router)

@app.get("/")
def root():
    return {"message":"API is running for the FastAPI application."}

@app.get("/protected")
async def protected_route(
    user_id: str = Depends(get_current_user),
):
    return {
        "message": "You are authenticated",
        "user_id": user_id,
    }
