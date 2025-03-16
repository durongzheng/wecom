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

# 企业模型示例
class Enterprise(Base):
    __tablename__ = "enterprises"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    api_key = Column(String(64), unique=True)
    secret_key = Column(String(64))
    wecom_corp_id = Column(String(64))
    wecom_secret = Column(String(64))
    db_cluster = Column(String(100))  # 分库配置