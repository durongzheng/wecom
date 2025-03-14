from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional

class SubscriberBase(BaseModel):
    company_name: str
    contact_email: EmailStr
    wecom_corp_id: str
    is_active: bool = True
    subscription_tier: str = "basic"  # e.g., basic, premium, enterprise

class SubscriberCreate(SubscriberBase):
    password: str

class SubscriberInDB(SubscriberBase):
    id: int
    created_at: datetime
    updated_at: datetime
    hashed_password: str

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None