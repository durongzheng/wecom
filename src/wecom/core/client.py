import requests
from redis import Redis

class WeComClient:
    def __init__(self, corp_id: str, secret: str):
        self.corp_id = corp_id
        self.secret = secret
        self.redis = Redis.from_url("redis://localhost:6379/0")
    
    @property
    def access_token(self):
        cache_key = f"wecom_token:{self.corp_id}"
        token = self.redis.get(cache_key)
        if not token:
            url = f"https://qyapi.weixin.qq.com/cgi-bin/service/get_provider_token?corpid={self.corp_id}&provider_secret={self.secret}"
            resp = requests.get(url).json()
            if resp["errcode"] != 0:
                raise Exception(f"Get token failed: {resp['errmsg']}")
            token = resp["provider_access_token"].encode()
            self.redis.setex(cache_key, 7000, token)  # 实际有效7200秒
        return token.decode()

    def send_message(self, userid: str, content: str):
        url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={self.access_token}"
        payload = {
            "touser": userid,
            "msgtype": "text",
            "agentid": 1000002,
            "text": {"content": content}
        }
        return requests.post(url, json=payload).json()