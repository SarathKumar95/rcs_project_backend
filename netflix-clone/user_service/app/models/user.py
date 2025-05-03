from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from . import Base
import datetime


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="user")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    subscription_plan_id = Column(Integer, default=1)
    active_devices_count = Column(Integer, default=1)
