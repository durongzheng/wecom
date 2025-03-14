from pydantic import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # 应用配置
    env: str = "development"
    app_name: str = "wecom"
    app_version: str = "0.1.0"
    debug: bool = True
    log_level: str = "INFO"
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    
    # 企业微信配置
    wecom_corp_id: str
    wecom_agent_id: str
    wecom_secret: str
    wecom_token: str
    wecom_aes_key: str
    
    # Redis 配置
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    
    # Celery 配置
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/0"
    
    class Config:
        env_file = str(Path(__file__).parent / ".env")
        env_file_encoding = "utf-8"

def get_settings():
    return Settings()