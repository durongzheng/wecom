from pydantic import Field, AnyUrl, RedisDsn, PostgresDsn
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # 应用配置
    ENV: str = Field("development", env="ENV")
    APP_NAME: str = Field("wecom", env="APP_NAME")
    APP_VERSION: str = Field("0.1.0", env="APP_VERSION")
    DEBUG: bool = Field(False, env="DEBUG")
    
    # 服务器配置
    HOST: str = Field("127.0.0.1", env="HOST")
    PORT: int = Field(8000, env="PORT")
    WORKERS: int = Field(4, env="WORKERS")

    # Redis 配置
    REDIS_HOST: str = Field("redis", env="REDIS_HOST")
    REDIS_PORT: int = Field(6379, env="REDIS_PORT")
    REDIS_DB: int = Field(0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(None, env="REDIS_PASSWORD")
    
    # Celery 配置
    CELERY_BROKER_URL: AnyUrl = Field(
        "redis://redis:6379/0", 
        env="CELERY_BROKER_URL"
    )
    CELERY_RESULT_BACKEND: AnyUrl = Field(
        "redis://redis:6379/0", 
        env="CELERY_RESULT_BACKEND"
    )

    # 数据库配置
    POSTGRES_HOST: str = Field("postgres", env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(5432, env="POSTGRES_PORT")
    POSTGRES_DB: str = Field("wecom", env="POSTGRES_DB")
    POSTGRES_USER: str = Field("wecom_prod_user", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field("StrongPassword123!", env="POSTGRES_PASSWORD")
    
    # 数据库连接池配置
    POOL_SIZE: int = Field(10, env="POOL_SIZE")
    MAX_OVERFLOW: int = Field(5, env="MAX_OVERFLOW")
    POOL_RECYCLE: int = Field(1800, env="POOL_RECYCLE")
    POOL_PRE_PING: bool = Field(True, env="POOL_PRE_PING")
    POOL_TIMEOUT: int = Field(30, env="POOL_TIMEOUT")
    ECHO_POOL: bool = Field(False, env="ECHO_POOL")

    # 安全配置
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    SECRET_KEY_EXPIRE_MINUTES: int = Field(1440, env="SECRET_KEY_EXPIRE_MINUTES")

    @property
    def SQLALCHEMY_DATABASE_URL(self) -> PostgresDsn:
        """动态生成数据库连接字符串"""
        return PostgresDsn.build(
            scheme="postgresql",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=f"/{self.POSTGRES_DB}"
        )

    @property
    def REDIS_URL(self) -> RedisDsn:
        """动态生成Redis连接字符串"""
        return RedisDsn.build(
            scheme="redis",
            host=self.REDIS_HOST,
            port=self.REDIS_PORT,
            path=f"/{self.REDIS_DB}"
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False  # 允许小写环境变量

def get_settings():
    return Settings()

# 测试配置
if __name__ == "__main__":
    settings = get_settings()
    print("Database URL:", settings.SQLALCHEMY_DATABASE_URL)
    print("Redis URL:", settings.REDIS_URL)
    print("Pool Config:", {
        "pool_size": settings.POOL_SIZE,
        "max_overflow": settings.MAX_OVERFLOW
    })