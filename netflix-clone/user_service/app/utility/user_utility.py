from fastapi import Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_async_db
from app.utility.auth_utility import decode_access_token
from sqlalchemy import select

# Async version of the create_user function
async def create_user(db: AsyncSession, email: str, hashed_pw: str):
    new_user = User(email=email, password=hashed_pw)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

