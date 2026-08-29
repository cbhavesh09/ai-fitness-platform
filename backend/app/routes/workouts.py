from fastapi import APIRouter, Depends, HTTPException, status
from datetime import date, datetime, time, timezone
from backend.app.auth.dependencies import get_current_user
from backend.app.db.client import database
from backend.app.models.workout import Workout
from backend.app.schemas.workout import WorkoutCreate, WorkoutResponse
from backend.app.schemas.workout_summary import WorkoutSummary

router = APIRouter(prefix="/workouts", tags=["Workouts"])
def normalize_exercise_name(name: str) -> str:
    normalized = " ".join(name.strip().split())

    alias = EXERCISE_ALIASES.get(
        normalized.lower()
    )

    if alias:
        return alias

    return normalized
EXERCISE_ALIASES = {
    "squat": "Squat (Barbell)",
    "squats": "Squat (Barbell)",
    "bench press": "Bench Press (Barbell)",
    "bench press barbell": "Bench Press (Barbell)",
    "deadlift": "Deadlift (Barbell)",
}

@router.post(
    "",
    response_model=WorkoutResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_workout(
    workout_data: WorkoutCreate,
    user_id: str = Depends(get_current_user),
):
    workout = Workout(
        user_id=user_id,
        exercise=normalize_exercise_name(
    workout_data.exercise
),
        muscle_group=workout_data.muscle_group,
        sets=workout_data.sets,
        reps=workout_data.reps,
        weight=workout_data.weight,
        duration=workout_data.duration,
        date=workout_data.date,
    )

    workout_document = workout.model_dump()
    workout_document["date"] = datetime.combine(
    workout.date,
    datetime.min.time(),
)

    result = await database.workouts.insert_one(
    workout_document

    )

    return WorkoutResponse(
        id=str(result.inserted_id),
        user_id=workout.user_id,
        exercise=workout.exercise,
        muscle_group=workout.muscle_group,
        sets=workout.sets,
        reps=workout.reps,
        weight=workout.weight,
        duration=workout.duration,
        date=workout.date,
    )

@router.get(
    "",
    response_model=list[WorkoutResponse],
)
async def get_workouts(
    user_id: str = Depends(get_current_user),
):
    workouts = []

    cursor = database.workouts.find(
        {"user_id": user_id}
    ).sort("date", -1)

    async for workout in cursor:
        workouts.append(
            WorkoutResponse(
                id=str(workout["_id"]),
                user_id=workout["user_id"],
                exercise=workout["exercise"],
                muscle_group=workout["muscle_group"],
                sets=workout["sets"],
                reps=workout["reps"],
                weight=workout["weight"],
                duration=workout["duration"],
                date=workout["date"].date(),
            )
        )

    return workouts

@router.get(
    "/summary",
    response_model=WorkoutSummary,
)
async def get_workout_summary(
    user_id: str = Depends(get_current_user),
):
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

    return WorkoutSummary(
        total_workouts=total_workouts,
        today_workouts=today_workouts,
    )


from bson import ObjectId

@router.get(
    "/exercise-suggestions",
)
async def get_exercise_suggestions(
    user_id: str = Depends(get_current_user),
):
    exercises = await database.workouts.distinct(
        "exercise"
    )

    seed_exercises = [
        "Bench Press (Barbell)",
        "Incline Bench Press (Barbell)",
        "Squat (Barbell)",
        "Deadlift (Barbell)",
        "Romanian Deadlift (Barbell)",
        "Overhead Press (Barbell)",
        "Lat Pulldown",
        "Seated Cable Row",
        "Bicep Curl (Barbell)",
        "Bicep Curl (Dumbbell)",
        "Hammer Curl (Dumbbell)",
        "Tricep Pushdown",
        "Lateral Raise (Dumbbells)",
        "Leg Press",
        "Leg Extension",
        "Leg Curl",
        "Pull Up",
        "Push Up",
    ]

    all_exercises = set(seed_exercises)
    all_exercises.update(exercises)

    return {
        "exercises": sorted(all_exercises)
    }

@router.delete(
    "/{workout_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_workout(
    workout_id: str,
    user_id: str = Depends(get_current_user),
):
    if not ObjectId.is_valid(workout_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found",
        )

    result = await database.workouts.delete_one(
        {
            "_id": ObjectId(workout_id),
            "user_id": user_id,
        }
    )

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found",
        )