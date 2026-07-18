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

class SparkLiteApi:
    def __init__(self, app_id, api_key, api_secret):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.url = "wss://spark-api.xf-yun.com/v1.1/chat"
        self.domain = "general" 

    def create_url(self):
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        signature_origin = "host: spark-api.xf-yun.com\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET /v1.1/chat HTTP/1.1"
        signature_sha = hmac.new(self.api_secret.encode('utf-8'), signature_origin.encode('utf-8'), digestmod=hashlib.sha256).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')
        authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        v = {"authorization": authorization, "date": date, "host": "spark-api.xf-yun.com"}
        url = self.url + '?' + urlencode(v)
        return url

    def ask(self, question):
        answer = ""
        
        def on_message(ws, message):
            nonlocal answer
            data = json.loads(message)
            code = data['header']['code']
            if code != 0:
                print(f"Error: {code}, {data['header']['message']}")
                ws.close()
            else:
                choices = data["payload"]["choices"]
                status = choices["status"]
                content = choices["text"][0]["content"]
                answer += content
                if status == 2:
                    ws.close()

        def on_error(ws, error):
            print(f"WebSocket Error: {error}")

        def on_close(ws, close_status_code, close_msg):
            pass

        def on_open(ws):
            thread.start_new_thread(run, (ws,))

        def run(ws, *args):
            data = json.dumps({
                "header": {"app_id": self.app_id, "uid": "1234"},
                "parameter": {"chat": {"domain": self.domain, "temperature": 0.5, "max_tokens": 2048}},
                "payload": {"message": {"text": [{"role": "user", "content": question}]}}
            })
            ws.send(data)

        ws = websocket.WebSocketApp(
            self.create_url(),
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        return answer
