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
# 🔴 关键修复：强制指定 IP (解决 Name or service not known)
# ==========================================
import socket
original_getaddrinfo = socket.getaddrinfo

def new_getaddrinfo(*args):
    # 如果请求的是讯飞的域名，直接返回我们指定的 IP，跳过 DNS 解析
    if args[0] == 'spark-api.xf-yun.com':
        return [(2, 1, 6, '', ('101.226.179.183', args[1]))] 
    return original_getaddrinfo(*args)

socket.getaddrinfo = new_getaddrinfo
# ==========================================


class SparkLiteApi:
    def __init__(self, appid, api_key, api_secret):
        self.appid = appid
        self.api_key = api_key
        self.api_secret = api_secret
        # Lite 版本对应的 URL
        self.host = "spark-api.xf-yun.com"
        self.domain = "general" 
        self.chat_url = f"wss://{self.host}/v1.1/chat"

    # 生成握手需要的鉴权 URL
    def create_url(self):
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        signature_origin = "host: " + self.host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET /v1.1/chat HTTP/1.1"

        signature_sha = hmac.new(
            self.api_secret.encode("utf-8"),
            signature_origin.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding="utf-8")

        authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode(encoding="utf-8")

        v = {"authorization": authorization, "date": date, "host": self.host}
        url = self.chat_url + "?" + urlencode(v)
        return url

    # 核心对话函数
    def chat(self, question):
        url = self.create_url()
        wsParam = Ws_Param(url, self.appid, question)
        
        # 建立连接
        websocket.enableTrace(False)
        wsResult = websocket.WebSocketApp(
            url,
            on_message=wsParam.on_message,
            on_error=wsParam.on_error,
            on_close=wsParam.on_close,
            on_open=wsParam.on_open,
        )
        wsResult.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        
        return wsResult.answer if hasattr(wsResult, 'answer') else "未收到回复"


# WebSocket 参数处理类
class Ws_Param(object):
    def __init__(self, url, appid, question):
        self.url = url
        self.appid = appid
        self.question = question
        self.answer = "" 

    # 收到消息时的处理
    def on_message(self, ws, message):
        data = json.loads(message)
        code = data["header"]["code"]
        if code != 0:
            print(f"错误代码 {code}: {data['header']['message']}")
            ws.close()
        else:
            choices = data["payload"]["choices"]
            status = choices["status"]
            content = choices["text"][0]["content"]
            self.answer += content 
            
            # 如果回答结束（status=2），关闭连接
            if status == 2:
                ws.close()

    # 发生错误时的处理
    def on_error(self, ws, error):
        print("### error:", error)

    # 连接关闭时的处理
    def on_close(self, ws, close_status_code, close_msg):
        pass

    # 连接建立时的处理（发送问题）
    def on_open(self, ws):
        thread.start_new_thread(self.run, (ws,))

    def run(self, ws, *args):
        data = json.dumps(self.gen_params())
        ws.send(data)

    # 构造发送给讯飞的数据包
    def gen_params(self):
        data = {
            "header": {"app_id": self.appid, "uid": "1234"},
            "parameter": {
                "chat": {
                    "domain": "general", # Lite 版本固定为 general
                    "temperature": 0.5,
                    "max_tokens": 2048,
                }
            },
            "payload": {
                "message": {
                    "text": [{"role": "user", "content": self.question}]
                }
            },
        }
        return data
