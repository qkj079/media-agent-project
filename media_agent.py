import _thread as thread
import base64
import datetime
import hashlib
import hmac
import json
import ssl
import time
from urllib.parse import urlparse, urlencode
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import websocket

# ================== ⚠️ 核心配置区 (必填) ==================
APP_ID = "3dd79365"  
API_KEY = "cf7b4d3e5fc58a69d2e144ea9875a094" 
API_SECRET = "MTdlYjg5ZTE3YTM2MzI3ZGE2OTFlODZh" 

DOMAIN = "generalv3.5"
SPARK_URL = "wss://spark-api.xf-yun.com/v3.5/chat"
# =======================================================

class SparkApi:
    def __init__(self):
        self.result = "" # 用于存储返回结果

    # 【关键修复】这里定义了 chat 方法，解决了报错问题
    def chat(self, text):
        self.result = "" # 每次对话前清空旧结果
        wsUrl = self.create_url()
        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(wsUrl, on_message=self.on_message, on_error=self.on_error, on_close=self.on_close, on_open=self.on_open)
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        return self.result # 将结果返回给主程序

    def create_url(self):
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        signature_origin = "host: spark-api.xf-yun.com\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET /v3.5/chat HTTP/1.1"
        signature_sha = hmac.new(API_SECRET.encode('utf-8'), signature_origin.encode('utf-8'), digestmod=hashlib.sha256).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')
        authorization_origin = f'api_key="{API_KEY}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        v = {"authorization": authorization, "date": date, "host": "spark-api.xf-yun.com"}
        url = SPARK_URL + '?' + urlencode(v)
        return url

    def on_message(self, ws, message):
        data = json.loads(message)
        code = data['header']['code']
        if code != 0:
            print(f'请求错误: {code}, {data}')
            ws.close()
        else:
            choices = data["payload"]["choices"]["text"]
            for choice in choices:
                self.result += choice["content"]

    def on_error(self, ws, error):
        print("### error:", error)

    def on_close(self, ws, close_status_code, close_msg):
        pass

    def on_open(self, ws):
        frame = {
            "header": {"app_id": APP_ID, "uid": "1234"},
            "parameter": {"chat": {"domain": DOMAIN, "temperature": 0.5, "max_tokens": 2048}},
            "payload": {"message": {"text": [{"role": "user", "content": "你好"}]}} 
        }
        ws.send(json.dumps(frame))
