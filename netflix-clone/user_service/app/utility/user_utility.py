from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User



# Async version of the create_user function
async def create_user(db: AsyncSession, email: str, hashed_pw: str):
    new_user = User(email=email, password=hashed_pw)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


