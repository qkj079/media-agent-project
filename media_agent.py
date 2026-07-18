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
import time

# ==========================================
# 🔴 请在下面三行引号内填入你的真实密钥 🔴
# ==========================================
APPID = "3dd79365"          # 例如: "5f9a..."
API_KEY = "cf7b4d3e5fc58a69d2e144ea9875a094"       # 例如: "a1b2c3..."
API_SECRET = "MTdlYjg5ZTE3YTM2MzI3ZGE2OTFlODZh" # 例如: "x9y8z7..."
# ==========================================

class SparkLiteApi:
    def __init__(self):
        self.appid = APPID
        self.api_key = API_KEY
        self.api_secret = API_SECRET
        self.host = "spark-api.xf-yun.com"
        self.domain = "general" 
        self.uri = "/v1.1/chat"
        self.answer = ""

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
        print("连接出错:", error)

    def on_close(self, ws, close_status_code, close_msg):
        pass

    def on_open(self, ws):
        thread.start_new_thread(self.run, (ws,))

    def run(self, ws, *args):
        data = json.dumps(self.gen_params())
        ws.send(data)

    def gen_params(self):
        return {
            "header": {"app_id": self.appid, "uid": "1234"},
            "parameter": {"chat": {"domain": self.domain, "temperature": 0.5, "max_tokens": 2048}},
            "payload": {"message": {"text": [{"role": "user", "content": self.question}]}}
        }

    def get_url(self):
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        signature_origin = f"host: {self.host}\ndate: {date}\nGET {self.uri} HTTP/1.1"
        signature_sha = hmac.new(self.api_secret.encode('utf-8'), signature_origin.encode('utf-8'), digestmod=hashlib.sha256).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')
        authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        v = {"authorization": authorization, "date": date, "host": self.host}
        url = 'wss://' + self.host + self.uri + '?' + urlencode(v)
        return url

    def ask(self, question):
        self.question = question
        self.answer = ""
        ws = websocket.WebSocketApp(
            self.get_url(),
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        return self.answer
