from datetime import datetime

from pydantic import EmailStr, BaseModel

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    age: int
    gender: str
    height_cm: float
    weight_kg: float
    activity_level: str
    goal: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    age: int
    gender: str
    height_cm: float
    weight_kg: float
    activity_level: str
    goal: str
    created_at: datetime

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    name: str
    age: int
    gender: str
    height_cm: float
    weight_kg: float
    activity_level: str
    goal: str