import _thread as thread
import base64
import datetime
import hashlib
import hmac
import json
from urllib.parse import urlparse, urlencode
from time import mktime
from wsgiref.handlers import format_date_time
from datetime import datetime
import ssl  # 【修复点】必须显式导入 ssl

import websocket 

class SparkLiteApi:
    def __init__(self, APPID, APIKey, APISecret):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        
        # Lite 版本配置
        self.Host = "spark-api.xf-yun.com"
        self.URI = "/v1.1/chat"
        self.Url = "wss://spark-api.xf-yun.com/v1.1/chat"
        self.Domain = "general" 

    def create_url(self):
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        
        signature_origin = "host: " + self.Host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.URI + " HTTP/1.1"
        
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'), digestmod=hashlib.sha256).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')
        
        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        
        v = {
            "authorization": authorization,
            "date": date,
            "host": self.Host
        }
        url = self.Url + '?' + urlencode(v)
        return url

    def start_chat(self, question):
        ws_url = self.create_url()
        # 这里的 on_message 和 on_error 需要根据你的业务逻辑补充
        # 为了演示，这里仅展示连接部分
        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(ws_url, on_message=self.on_message, on_error=self.on_error, on_close=self.on_close)
        ws.on_open = self.on_open
        # 【修复点】使用 sslopt 关闭证书验证，防止云端环境证书问题
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE}) 

    # 下面是回调函数占位符，你需要根据你的实际逻辑填充
    def on_message(self, ws, message):
        data = json.loads(message)
        print(data) 

    def on_error(self, ws, error):
        print("### error:", error) 

    def on_close(self, ws, close_status_code, close_msg):
        print("### closed ###") 

    def on_open(self, ws):
        frame = {
            "header": {"app_id": self.APPID, "uid": "1234"},
            "parameter": {"chat": {"domain": self.Domain, "temperature": 0.5, "max_tokens": 1024}},
            "payload": {"message": {"text": [{"role": "user", "content": "你好"}]}}
        }
        ws.send(json.dumps(frame))

# 【重要】去掉了 if __name__ == "__main__": 块，防止在 Streamlit Cloud 上误触发或报错
