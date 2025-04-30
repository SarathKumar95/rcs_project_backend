from fastapi import Depends, APIRouter, HTTPException
from pydantic import BaseModel
from models.user import User
from services.auth_service import create_access_token, verify_password  # Auth functions
from sqlalchemy.orm import Session
from db.session import get_db  # Your database session dependency
from typing import List
from schemas.user import UserOut  # <-- import the schema

router = APIRouter()


# Pydantic schema for register request
class RegisterRequest(BaseModel):
    email: str
    password: str
    role: str


# Pydantic schema for login request
class LoginRequest(BaseModel):
    email: str
    password: str


router = APIRouter()


@router.get("/users", response_model=List[UserOut])
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()


@router.post("/register", response_model=RegisterRequest)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register new user in the system.
    """
    user = user_model.User(
        email=request.email,
        password=hash_password(request.password),  # Ensure you hash the password
        role=request.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    User login and JWT token generation.
    """
    user = db.query(user_model.User).filter(user_model.User.email == request.email).first()
    if not user or not verify_password(request.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

