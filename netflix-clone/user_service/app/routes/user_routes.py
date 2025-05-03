

from fastapi import Depends, APIRouter, HTTPException
from app.models.user import User
from app.services.auth_service import create_access_token,hash_password  # Auth functions
from sqlalchemy.orm import Session
from app.db.session import get_db  
from app.schemas.user import UserCreate,Token
from sqlalchemy.exc import SQLAlchemyError
from core.logger import logger





router = APIRouter()


@router.post("/", response_model=Token)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    try:
        hashed_pw = hash_password(user.password)
        new_user = User(email=user.email, hashed_password=hashed_pw)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"DB Error during registration: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed. Please try again later.")

    token = create_access_token(data={"sub": str(new_user.id)})
    return {"access_token": token}
