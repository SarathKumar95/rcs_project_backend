from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserOut(BaseModel):
    id: int
    email: str
    role: Optional[str] = None
    created_at: Optional[datetime] = None
    subscription_plan_id: Optional[int] = None
    active_devices_count: Optional[int] = None

    class Config:
        orm_mode = True  # Crucial! Tells Pydantic to work with SQLAlchemy models


class UserCreate(BaseModel):
    email: EmailStr
    password: str