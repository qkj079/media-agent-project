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

# ================== 1. 配置区域 (必填) ==================
APP_ID = "3dd79365"      # 纯数字
API_KEY = "cf7b4d3e5fc58a69d2e144ea9875a094"
API_SECRET = "MTdlYjg5ZTE3YTM2MzI3ZGE2OTFlODZh"
# ======================================================

class Ws_Param(object):
    def __init__(self, APPID, APIKey, APISecret, Spark_url):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.host = urlparse(Spark_url).netloc
        self.path = urlparse(Spark_url).path
        self.Spark_url = Spark_url

    def create_url(self):
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        signature_origin = "host: " + self.host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.path + " HTTP/1.1"
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'), digestmod=hashlib.sha256).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')
        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        v = {"authorization": authorization, "date": date, "host": self.host}
        url = self.Spark_url + '?' + urlencode(v)
        return url

def on_error(ws, error):
    print("### error:", error)

def on_close(ws, one, two):
    pass

def on_open(ws):
    thread.start_new_thread(run, (ws,))

def run(ws, *args):
    data = json.dumps(gen_params(appid=ws.appid, domain=ws.domain, question=ws.question))
    ws.send(data)

def on_message(ws, message):
    data = json.loads(message)
    code = data['header']['code']
    if code != 0:
        ws.error = f"请求错误: {code}, {data['header']['message']}"
        ws.close()
    else:
        choices = data["payload"]["choices"]
        status = choices["status"]
        content = choices["text"][0]["content"]
        ws.answer += content
        if status == 2:
            ws.close()

def gen_params(appid, domain, question):
    return {
        "header": {"app_id": appid, "uid": "1234"},
        "parameter": {"chat": {"domain": domain, "temperature": 0.5, "max_tokens": 2048}},
        "payload": {"message": {"text": [{"role": "user", "content": question}]}}
    }

class SparkApi:
    def __init__(self):
        # ✅ 这里配置的是 Spark Lite 的地址
        self.spark_url = "wss://spark-api.xf-yun.com/v1.1/chat" 
        self.appid = APP_ID
        self.api_key = API_KEY
        self.api_secret = API_SECRET
        self.domain = "general" # Lite 版本对应 general

    def get_answer(self, question):
        wsParam = Ws_Param(self.appid, self.api_key, self.api_secret, self.spark_url)
        websocket.enableTrace(False)
        wsUrl = wsParam.create_url()
        ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
        ws.appid = self.appid
        ws.domain = self.domain
        ws.question = question
        ws.answer = "" 
        ws.error = None 
        
        ws.on_open = on_open
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        
        if ws.error:
            return f"出错啦：{ws.error}"
        return ws.answer
