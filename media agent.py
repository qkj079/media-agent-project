import base64
import hashlib
import hmac
import json
import threading
import time
from datetime import datetime
from urllib.parse import urlencode, urlparse
from wsgiref.handlers import format_date_time

import websocket


class SparkLiteApi:
    def __init__(self, app_id, api_key, api_secret):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.host = "spark-api.xf-yun.com"
        self.uri = "/v1.1/chat"
        self.url = f"wss://{self.host}{self.uri}"

    def create_url(self):
        # 生成鉴权URL
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        signature_origin = f"host: {self.host}\ndate: {date}\nGET {self.uri} HTTP/1.1"
        signature_sha = hmac.new(
            self.api_secret.encode("utf-8"),
            signature_origin.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode("utf-8")
        authorization_origin = (
            f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", '
            f'signature="{signature_sha_base64}"'
        )
        authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode("utf-8")
        v = {"authorization": authorization, "date": date, "host": self.host}
        url = self.url + "?" + urlencode(v)
        return url

    def on_message(self, ws, message):
        data = json.loads(message)
        if data["header"]["code"] != 0:
            print(f"Error: {data['header']['message']}")
            ws.close()
            return
        choices = data["payload"]["choices"]["text"]
        for choice in choices:
            print(choice["content"], end="", flush=True)

    def on_error(self, ws, error):
        print(f"WebSocket Error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("\nConnection closed.")

    def on_open(self, ws):
        question = {
            "header": {"app_id": self.app_id, "uid": "12345"},
            "parameter": {"chat": {"domain": "general", "temperature": 0.5, "max_tokens": 1024}},
            "payload": {"message": {"text": [{"role": "user", "content": "你好"}]}},
        }
        ws.send(json.dumps(question))

    def run(self):
        url = self.create_url()
        ws = websocket.WebSocketApp(
            url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
        )
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})


# 示例用法
if __name__ == "__main__":
    app = SparkLiteApi(
        app_id="你的APPID",
        api_key="你的APIKey",
        api_secret="你的APISecret"
    )
    app.run()
