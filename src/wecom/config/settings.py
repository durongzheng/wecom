from pydantic import BaseSettings

class Settings(BaseSettings):
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str
    
    debug: bool = False
    log_level: str = "INFO"
    secret_key: str
    access_token_expire_minutes: int = 1440

    class Config:
        env_file = None  # 禁用 .env 文件加载
        case_sensitive = True

def get_settings():
    return Settings()