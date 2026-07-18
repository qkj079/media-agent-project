import _thread as thread
import base64
import datetime
import hashlib
import hmac
import json
from urllib.parse import urlparse
import ssl
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
import websocket

# 配置你的密钥 (建议从环境变量获取，这里为了演示直接写死，或者你自己在代码里填)
# 注意：如果在Streamlit云端部署，最好用 st.secrets，但为了先跑通，你可以先填在这里
APPID = "你的APPID" 
APIKey = "你的APIKey" 
APISecret = "你的APISecret" 

class SparkLiteApi:
    def __init__(self, appid, api_key, api_secret):
        self.appid = appid
        self.api_key = api_key
        self.api_secret = api_secret
        self.answer = ""

    # 1. 这里是报错缺失的 get_url 函数
    def get_url(self):
        host = "spark-api.xf-yun.com"
        url = "wss://{}/v1.1/chat".format(host)
        
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        
        signature_origin = "host: {}\ndate: {}\nGET /v1.1/chat HTTP/1.1".format(host, date)
        signature_sha = hmac.new(self.api_secret.encode('utf-8'), signature_origin.encode('utf-8'), digestmod=hashlib.sha256).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')
        
        authorization_origin = "api_key=\"{}\", algorithm=\"hmac-sha256\", headers=\"host date request-line\", signature=\"{}\"".format(
            self.api_key, signature_sha_base64)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        
        v = {"authorization": authorization, "date": date, "host": host}
        url = url + '?' + urlencode(v)
        return url

    # 2. 这里是核心对话逻辑
    def chat(self, prompt):
        self.answer = ""
        wsUrl = self.get_url()
        
        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(wsUrl, on_message=self.on_message, on_error=self.on_error, on_close=self.on_close)
        ws.on_open = self.on_open
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        return self.answer

    # --- 以下是 WebSocket 的回调函数，不需要改动 ---
    def on_message(self, ws, message):
        data = json.loads(message)
        code = data['header']['code']
        if code != 0:
            print(f'请求错误: {code}, {data}')
            ws.close()
        else:
            choices = data["payload"]["choices"]
            status = choices["status"]
            content = choices["text"][0]["content"]
            self.answer += content
            if status == 2:
                ws.close()

    def on_error(self, ws, error):
        print("### error:", error)

    def on_close(self, ws, close_status_code, close_msg):
        pass

    def on_open(self, ws):
        gen_params = {
            "header": {
                "app_id": self.appid,
                "uid": "1234"
            },
            "parameter": {
                "chat": {
                    "domain": "general", # Lite版本通常用 general
                    "temperature": 0.5,
                    "max_tokens": 1024
                }
            },
            "payload": {
                "message": {
                    "text": [
                        {"role": "user", "content": "你好"} # 这里只是占位，实际应该传入 prompt
                    ]
                }
            }
        }
        # 修正：把传入的 prompt 放进去
        gen_params["payload"]["message"]["text"] = [{"role": "user", "content": self.current_prompt}]
        ws.send(json.dumps(gen_params))
