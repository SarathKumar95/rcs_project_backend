
from sqlalchemy import Column, Integer, String, Float
from . import Base  # reuse declarative_base()


class SubscriptionPlan(Base):
    __tablename__ = 'subscription_plans'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    max_devices = Column(Integer, nullable=False)
    max_resolution = Column(String, nullable=False)
    monthly_price = Column(Float, nullable=False)
