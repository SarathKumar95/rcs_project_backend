import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base


DATABASE_URL = os.environ["DATABASE_URL"]  # assume Docker is setting this

engine =  create_async_engine(DATABASE_URL, echo=True)
# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

Base = declarative_base()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
