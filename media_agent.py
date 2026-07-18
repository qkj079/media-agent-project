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
    # 🔴 注意：这里必须接收 appid, api_key, api_secret 三个参数，否则就会报你截图里的错
    def __init__(self, appid, api_key, api_secret):
        self.appid = appid
        self.api_key = api_key
        self.api_secret = api_secret
        self.host = "spark-api.xfyun.cn"
        self.uri = "/v1.1/chat" 
        self.domain = "lite" 

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
        v = {"authorization": authorization, "date": date, "host": self.host}
        url = 'wss://' + self.host + self.uri + '?' + urlencode(v)
        return url

    def run(self, text):
        wsUrl = self.create_url()
        result = []
        
        def on_message(ws, message):
            data = json.loads(message)
            code = data['header']['code']
            if code != 0:
                result.append(f"错误代码 {code}: {data['header']['message']}")
                ws.close()
            else:
                choices = data["payload"]["choices"]["text"]
                for choice in choices:
                    result.append(choice["content"])

        def on_error(ws, error):
            result.append(f"连接出错: {str(error)}")

        def on_close(ws, close_status_code, close_msg):
            pass 

        def on_open(ws):
            frame = {
                "header": {"app_id": self.appid, "uid": "1234"},
                "parameter": {"chat": {"domain": self.domain, "temperature": 0.5, "max_tokens": 1024}},
                "payload": {"message": {"text": [{"role": "user", "content": text}]}}
            }
            ws.send(json.dumps(frame))

        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
        ws.on_open = on_open
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        
        return "".join(result)
