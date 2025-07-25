from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from typing import AsyncGenerator


DATABASE_URL = os.environ["DATABASE_URL"]  # assume Docker is setting this

engine =  create_async_engine(DATABASE_URL, echo=True)
# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

Base = declarative_base()


# Asynchronous DB dependency
from sqlalchemy.ext.asyncio import AsyncSession

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
