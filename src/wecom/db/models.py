from sqlalchemy import Column, Integer, String, Boolean, DateTime
from .database import Base

class Subscriber(Base):
    __tablename__ = "subscribers"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(100), index=True)
    contact_email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(200))
    wecom_corp_id = Column(String(100), unique=True)
    is_active = Column(Boolean, default=True)
    subscription_tier = Column(String(20), default="basic")
    created_at = Column(DateTime)
    updated_at = Column(DateTime)