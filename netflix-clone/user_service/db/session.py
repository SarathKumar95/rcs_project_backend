from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.orm import Session
import os

DATABASE_URL = os.environ["DATABASE_URL"]  # assume Docker is setting this

engine = create_engine(DATABASE_URL, echo=True)  # `echo=True` logs SQL queries
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Dependency
def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
