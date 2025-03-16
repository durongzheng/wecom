# 基于HMAC的多企业认证

import hashlib
import hmac
from fastapi import HTTPException, Request
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet, InvalidToken
from ..db.models import Enterprise
from ..config import get_settings


class SecretManager:
    def __init__(self, master_key=None):
        # 主密钥建议通过环境变量注入
        self.master_key = master_key or Fernet.generate_key()
        self.cipher = Fernet(self.master_key)

    def encrypt_secret(self, plaintext: str) -> bytes:
        return self.cipher.encrypt(plaintext.encode())

    def decrypt_secret(self, encrypted_data: bytes) -> str:
        try:
            return self.cipher.decrypt(encrypted_data).decode()
        except InvalidToken:
            raise ValueError("Invalid decryption key or corrupted data")

class EnterpriseAuthenticator:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.secret_manager = SecretManager()  # 生产环境应从配置加载master_key
        
    async def authenticate_request(self, request: Request) -> dict:
        # 获取请求头
        api_key = request.headers.get("X-API-Key")
        client_signature = request.headers.get("X-Signature")
        
        if not (api_key and client_signature):
            raise HTTPException(401, "Missing authentication headers")
            
        # 查询企业信息
        enterprise = self.db.query(Enterprise).filter(
            Enterprise.api_key == api_key
        ).first()
        
        if not enterprise:
            raise HTTPException(403, "Invalid API key or inactive account")
            
        # 解密加密的密钥（核心修改点）
        try:
            decrypted_secret = self.secret_manager.decrypt_secret(
                enterprise.encrypted_secret
            )
        except ValueError as e:
            raise HTTPException(500, f"Secret decryption failed: {str(e)}")
            
        # 验证请求签名
        request_body = await request.body()
        expected_signature = hmac.new(
            decrypted_secret.encode('utf-8'),
            request_body,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(client_signature, expected_signature):
            raise HTTPException(403, "Invalid request signature")
            
        return {
            "enterprise_id": enterprise.id,
            "wecom_config": {
                "name": enterprise.name,
                "is_active": enterprise.is_active,
                "api_key": api_key,
                "corp_id": enterprise.wecom_corp_id,
                "secret": enterprise.wecom_secret
            }
        }