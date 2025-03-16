import secrets
import string
from sqlalchemy.orm import Session
from auth import SecretManager
from ..db.models import Enterprise

def generate_secure_key(length=32):
    """生成安全的随机API Key"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def register_enterprise(db: Session, name: str, wecom_corp_id: str, wecom_secret: str):
    # 生成API凭证
    api_key = generate_secure_key(32)  # 32位随机字符串
    secret_key = generate_secure_key(64)  # 64位随机字符串
    
    # 加密存储（核心修改）
    secret_manager = SecretManager()
    encrypted_secret = secret_manager.encrypt_secret(secret_key)
    
    # 保存记录
    enterprise = Enterprise(
        name=name,
        api_key=api_key,
        encrypted_secret=encrypted_secret,  # 使用新字段
        wecom_corp_id=wecom_corp_id,
        wecom_secret=wecom_secret
    )
    db.add(enterprise)
    db.commit()
    
    # 返回明文密钥（需在安全通道传输）
    return {
        "api_key": api_key,
        "secret_key": secret_key,  # 最后一次明文展示
        "expires_in": 3600  # 要求客户端立即保存
    }