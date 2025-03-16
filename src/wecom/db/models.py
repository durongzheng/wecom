from sqlalchemy import Column, Integer, String, Boolean, DateTime, LargeBinary
from sqlalchemy.sql import func
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
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)  # 长度为255,唯一,非空
    is_active = Column(Boolean, server_default='TRUE', nullable=False)  # 默认值+非空
    api_key = Column(String(64), unique=True, nullable=False)  # 唯一+非空
    encrypted_secret = Column(LargeBinary, nullable=False)  # BYTEA对应LargeBinary
    wecom_corp_id = Column(String(64), unique=True, nullable=False)  # 唯一+非空
    wecom_secret = Column(String(64), unique=True, nullable=False)  # 唯一+非空
    db_cluster = Column(String(100))  # 允许为空
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # 自动生成时间戳