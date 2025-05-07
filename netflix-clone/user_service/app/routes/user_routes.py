
from fastapi import Depends, APIRouter, HTTPException, Response
from app.models.user import User
from app.services.auth_service import create_access_token,hash_password  # Auth functions
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_async_db
from app.schemas.user import UserCreate
from sqlalchemy.exc import SQLAlchemyError
from core.logger import logger
from app.services.auth_service import set_auth_cookies
from sqlalchemy import select
from app.services.user_service import *

router = APIRouter()




@router.post("/")
async def register(
    response: Response,
    user: UserCreate,
    db: AsyncSession = Depends(get_async_db)  # Make sure get_async_db returns AsyncSession
):

    # Check if user already exists
    result = await db.execute(select(User).filter(User.email == user.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    try:
        # Hash password (you can also make hash_password async if needed)
        hashed_pw = hash_password(user.password)
        new_user = await create_user(db, user.email, hashed_pw)

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"DB Error during registration: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed. Please try again later.")

    access_token = create_access_token(data={"sub": str(new_user.id)})
    set_auth_cookies(response, access_token)

    return {"message": "Success"}
