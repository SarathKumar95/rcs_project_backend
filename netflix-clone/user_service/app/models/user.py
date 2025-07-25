from sqlalchemy import Column, Integer, String, DateTime
from . import Base
import datetime
from enum import IntEnum

class Role(IntEnum):
    USER = 0
    ADMIN = 1

    

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(Integer, default=Role.USER)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    subscription_plan_id = Column(Integer, default=1)
    active_devices_count = Column(Integer, default=1)


    @property
    def role_name(self):
        return Role(self.role).name.lower()
