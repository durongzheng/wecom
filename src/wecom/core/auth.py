# 基于HMAC的多企业认证
import secrets
import string
from sqlalchemy import create_engine
from requests import Request
from cryptography.fernet import Fernet
from ..config import get_settings

def generate_api_key(length=32):
    """生成安全的随机API Key"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

class SecretManager:
    def __init__(self, master_key=None):
        # 主密钥建议通过环境变量注入
        self.master_key = master_key or Fernet.generate_key()
        self.cipher = Fernet(self.master_key)

    def encrypt_secret(self, plaintext: str) -> bytes:
        return self.cipher.encrypt(plaintext.encode())

    def decrypt_secret(self, ciphertext: bytes) -> str:
        return self.cipher.decrypt(ciphertext).decode()

class EnterpriseAuthenticator:
    def __init__(self):
        self.engine = create_engine(config.DB_URL, pool_size=5, max_overflow=2)
        
    async def verify_request(self, request: Request):
        api_key = request.headers.get("X-API-Key")
        signature = request.headers.get("X-Signature")
        
        # 从连接池获取会话
        with Session(self.engine) as session:
            enterprise = session.query(Enterprise).filter_by(api_key=api_key).first()
            if not enterprise:
                raise HTTPException(status_code=403)
                
            # 验证签名
            payload = await request.body()
            expected_sig = hmac.new(
                enterprise.secret_key.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_sig):
                raise HTTPException(status_code=403)
                
        request.state.enterprise = enterprise