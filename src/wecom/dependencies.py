from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError

# 注意这里的相对路径引用
from .config import get_settings  
from .db import crud, database

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

async def get_current_subscriber(
    token: str = Depends(oauth2_scheme),
    db: database.SessionLocal = Depends(database.get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        settings = get_settings()
        payload = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.algorithm]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except (JWTError, ValidationError) as e:
        raise credentials_exception
    
    # 通过数据库获取订阅者
    subscriber = crud.get_subscriber_by_email(db, email=email)
    if subscriber is None:
        raise credentials_exception
    return subscriber