from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

class User(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr
    password_hash: str
    age: int = Field(gt=0)
    gender: str
    height_cm: float = Field(gt=0)
    weight_kg: float = Field(gt=0)
    activity_level: str
    goal: str
    created_at: datetime