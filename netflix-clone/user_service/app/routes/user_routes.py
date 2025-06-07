
from fastapi import Depends, APIRouter, HTTPException, Response, Request
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_async_db
from app.schemas.user import UserCreate, UserOut
from sqlalchemy.exc import SQLAlchemyError
from core.logger import logger
from app.utility.auth_utility import set_auth_cookies , create_access_token,hash_password 
from sqlalchemy import select
from app.utility.user_utility import *


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

    access_token = create_access_token(new_user)
    set_auth_cookies(response, access_token)

    return {"message": "Success"}



@router.get("/",response_model=UserOut)
async def get_current_user(request: Request, db: AsyncSession = Depends(get_async_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=403, detail="No Token found")

    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserOut(
        id=user.id,
        email=user.email,
        role=user.role_name
    )