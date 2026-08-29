from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.auth.dependencies import get_current_user
from backend.app.config import settings
from backend.app.db.client import client
from backend.app.routes.auth import router as auth_router
from backend.app.routes.calorie import router as calorie_router
from backend.app.routes.dashboard import router as dashboard_router
from backend.app.routes.prediction import router as prediction_router
from backend.app.routes.users import router as users_router
from backend.app.routes.weight import router as weight_router
from backend.app.routes.workouts import router as workout_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await client.admin.command("ping")
    yield
    await client.close()


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(workout_router)
app.include_router(weight_router)
app.include_router(calorie_router)
app.include_router(prediction_router)
app.include_router(users_router)
app.include_router(dashboard_router)


@app.get("/")
def root():
    return {
        "message": "API is running for the FastAPI application."
    }


@app.get("/protected")
async def protected_route(
    user_id: str = Depends(get_current_user),
):
    return {
        "message": "You are authenticated",
        "user_id": user_id,
    }