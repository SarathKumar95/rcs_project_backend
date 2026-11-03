import unicodedata
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime


class UserOut(BaseModel):
    id: int
    email: str
    role: Optional[str] = None
    # created_at: Optional[datetime] = None
    subscription_plan_id: Optional[int] = None
    # active_devices_count: Optional[int] = None

    class Config:
        orm_mode = True  # Crucial! Tells Pydantic to work with SQLAlchemy models


class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @validator("password")
    def validate_password(cls, password: str) -> str:
        if len(password) < 12:
            raise ValueError("Password must be at least 12 characters long")
        if not any(character.isupper() for character in password):
            raise ValueError("Password must include at least one uppercase letter")
        if not any(
            unicodedata.category(character)[0] in {"P", "S"}
            for character in password
        ):
            raise ValueError("Password must include at least one symbol")
        return password


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
