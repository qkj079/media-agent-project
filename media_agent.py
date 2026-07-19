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
# 根据你提供的截图，APPID 应该是这个，请核对
APP_ID = "3dd79365"
# ⚠️ 下面这两个必须去控制台复制粘贴，不能留空
API_KEY = "cf7b4d3e5fc58a69d2e144ea9875a094"
API_SECRET = "MTdlYjg5ZTE3YTM2MzI3ZGE2OTFlODZh"
# ======================================================

class Ws_Param(object):
    def __init__(self, APPID, APIKey, APISecret, Spark_url):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.Spark_url = Spark_url

    def get_host(self):
        return urlparse(self.Spark_url).netloc

    def get_path(self):
        return urlparse(self.Spark_url).path

    # 生成鉴权 URL
    def create_url(self):
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        signature_origin = "host: " + self.get_host() + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.get_path() + " HTTP/1.1"

        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'), digestmod=hashlib.sha256).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        v = {
            "authorization": authorization,
            "date": date,
            "host": self.get_host()
        }
        url = self.Spark_url + '?' + urlencode(v)
        return url

# 收到 WebSocket 错误的处理
def on_error(ws, error):
    print("### error:", error)

# 收到 WebSocket 关闭的处理
def on_close(ws, one, two):
    pass

# 收到 WebSocket 连接建立的处理
def on_open(ws):
    thread.start_new_thread(run, (ws,))

def run(ws, *args):
    data = json.dumps(gen_params(appid=ws.appid, domain=ws.domain, question=ws.question))
    ws.send(data)

# 收到 WebSocket 消息的处理
def on_message(ws, message):
    data = json.loads(message)
    code = data['header']['code']
    if code != 0:
        ws.content = f"请求错误: {code}, {data['header']['message']}"
        ws.close()
    else:
        choices = data["payload"]["choices"]
        status = choices["status"]
        content = choices["text"][0]["content"]
        ws.content += content
        
        if status == 2:
            ws.close()

def gen_params(appid, domain, question):
    """
    通过 appid 和用户的提问来构造请求参数
    """
    data = {
        "header": {
            "app_id": appid,
            "uid": "1234"
        },
        "parameter": {
            "chat": {
                "domain": domain, 
                "temperature": 0.5,
                "max_tokens": 2048
            }
        },
        "payload": {
            "message": {
                "text": [
                    {"role": "user", "content": question}
                ]
            }
        }
    }
    return data

class SparkApi:
    def __init__(self):
        # ✅ 关键修改：针对 Spark Ultra-32K 的接口地址 (v3.5)
        # 如果 Ultra-32K 对应的是 V4.0，请将下面的 v3.5 改为 v4.0
        self.spark_url = "wss://spark-api.xf-yun.com/v3.5/chat"
        self.domain = "generalv3.5" 
        
        # 备用：如果你的 Ultra-32K 其实是 V4.0 接口，请使用下面这两行：
        # self.spark_url = "wss://spark-api.xf-yun.com/v4.0/chat"
        # self.domain = "4.0Ultra"

    def chat(self, text):
        wsParam = Ws_Param(APP_ID, API_KEY, API_SECRET, self.spark_url)
        websocket.enableTrace(False)
        wsUrl = wsParam.create_url()
        
        ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close, on_open=on_open)
        ws.appid = APP_ID
        ws.question = text
        ws.domain = self.domain
        ws.content = ""
        
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        return ws.content

# 测试代码（可选）
if __name__ == "__main__":
    agent = SparkApi()
    print("正在连接讯飞 Ultra-32K...")
    result = agent.chat("你好，请介绍一下你自己")
    print("回答:", result)
