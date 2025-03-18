import pytest
from pydantic import ValidationError
from wecom.config import get_settings, Settings

@pytest.fixture
def mock_env(monkeypatch):
    """模拟基础环境变量（覆盖所有必要变量）"""
    # 安全配置
    monkeypatch.setenv("SECRET_KEY", "test_secret")
    # 数据库配置
    monkeypatch.setenv("POSTGRES_USER", "test_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "test_pass")
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_PORT", "5433")
    # Redis配置
    monkeypatch.setenv("REDIS_HOST", "redis.test")
    monkeypatch.setenv("REDIS_PORT", "6380")

def test_default_config():
    settings = get_settings()
    assert settings.ENV == "development"
    assert settings.DEBUG is True
    assert settings.PORT == 8000

def test_database_url(mock_env):
    settings = get_settings()
    expected = "postgresql://test_user:test_pass@localhost:5433/test_wecom"
    assert str(settings.SQLALCHEMY_DATABASE_URL) == expected

def test_redis_url(mock_env):
    settings = get_settings()
    expected = "redis://redis.test:6380/0"
    assert str(settings.REDIS_URL) == expected

def test_secret_key_validation(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)

def test_env_override(mock_env):
    settings = get_settings()
    assert settings.POSTGRES_HOST == "localhost"
    assert settings.REDIS_PORT == 6380

def test_pool_config():
    settings = get_settings()
    assert settings.POOL_SIZE == 10
    assert settings.MAX_OVERFLOW == 5
    assert settings.POOL_TIMEOUT == 30