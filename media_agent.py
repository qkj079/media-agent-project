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

class SparkLiteApi:
    # 1. 初始化：接收 appid, key, secret
    def __init__(self, appid, api_key, api_secret):
        self.appid = appid
        self.api_key = api_key
        self.api_secret = api_secret
        self.host = "spark-api.xfyun.cn"
        self.uri = "/v1.1/chat" # 注意：如果是星火2.0或3.0，这里路径可能不同，Lite版通常是这个

    # 2. 生成鉴权URL (这是和讯飞服务器握手的关键)
    def create_url(self):
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        
        signature_origin = "host: " + self.host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.uri + " HTTP/1.1"
        
        signature_sha = hmac.new(self.api_secret.encode('utf-8'), signature_origin.encode('utf-8'), digestmod=hashlib.sha256).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')
        
        authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        
        v = {
            "authorization": authorization,
            "date": date,
            "host": self.host
        }
        url = 'wss://' + self.host + self.uri + '?' + urlencode(v)
        return url

    # 3. 核心对话函数 (这就是报错里说 missing 的那个 chat 函数！)
    def chat(self, question):
        wsUrl = self.create_url()
        self.result = "" 
        
        # 定义收到消息时的处理逻辑
        def on_message(ws, message):
            data = json.loads(message)
            code = data['header']['code']
            if code != 0:
                self.result = f"错误代码: {code}, 原因: {data['header']['message']}"
                ws.close()
            else:
                choices = data["payload"]["choices"]["text"]
                for choice in choices:
                    self.result += choice["content"]

        # 定义建立连接时的处理逻辑
        def on_open(ws):
            param = {
                "header": {"app_id": self.appid},
                "parameter": {"chat": {"domain": "lite", "temperature": 0.5, "max_tokens": 2048}},
                "payload": {"message": {"text": [{"role": "user", "content": question}]}}
            }
            ws.send(json.dumps(param))

        # 定义错误处理
        def on_error(ws, error):
            self.result = f"连接出错: {error}"

        # 开始连接
        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_open=on_open)
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        
        return self.result
