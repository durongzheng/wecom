from fastapi import FastAPI
from .routers import auth, notify
from .db import database
from .config import get_settings
app = FastAPI()

def validate_config():
    settings = get_settings()
    if not all([settings.postgres_host, settings.postgres_user, settings.postgres_password]):
        raise ValueError("Missing required database configuration")

# 初始化数据库
database.Base.metadata.create_all(bind=database.engine)

# 包含路由
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(notify.router, prefix="/api", tags=["notifications"])