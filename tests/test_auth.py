import pytest
from jose import jwt
from wecom.config import get_settings

# 测试注册和登录
async def test_register_and_login(client):
    # 注册新用户
    register_data = {
        "company_name": "测试公司",
        "contact_email": "test@example.com",
        "wecom_corp_id": "test_corp_123",
        "password": "securepassword123",
        "subscription_tier": "basic"
    }
    response = client.post("/auth/register", json=register_data)
    assert response.status_code == 200
    assert response.json()["contact_email"] == "test@example.com"

    # 测试登录
    login_data = {
        "username": "test@example.com",
        "password": "securepassword123"
    }
    response = client.post("/auth/token", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # 验证 JWT 令牌
    settings = get_settings()
    payload = jwt.decode(
        token, 
        settings.secret_key, 
        algorithms=[settings.algorithm]
    )
    assert payload["sub"] == "test@example.com"

# 测试受保护路由
def test_protected_route(client):
    # 先登录获取令牌
    login_data = {"username": "test@example.com", "password": "securepassword123"}
    token = client.post("/auth/token", data=login_data).json()["access_token"]
    
    # 访问受保护路由
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/notifications", headers=headers)
    assert response.status_code == 200
    assert "notifications" in response.json()

# 测试失败场景
def test_invalid_credentials(client):
    # 错误密码
    response = client.post("/auth/token", data={
        "username": "test@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

    # 无效令牌
    headers = {"Authorization": "Bearer invalidtoken"}
    response = client.get("/api/notifications", headers=headers)
    assert response.status_code == 401