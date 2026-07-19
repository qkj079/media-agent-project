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
# 根据你的截图，APPID 已预填
APP_ID = "3dd79365"
# ⚠️ 请务必在此处填入你在讯飞控制台获取的 Key 和 Secret
API_KEY = "cf7b4d3e5fc58a69d2e144ea9875a094"
API_SECRET = "MTdlYjg5ZTE3YTM2MzI3ZGE2OTFlODZh"
# ======================================================

class Ws_Param(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret, Spark_url):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.Host = urlparse(Spark_url).netloc
        self.Path = urlparse(Spark_url).path
        self.Spark_url = Spark_url

    # 生成url
    def create_url(self):
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + self.Host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.Path + " HTTP/1.1"

        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()

        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'

        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": self.Host
        }
        # 拼接鉴权参数，生成url地址
        url = self.Spark_url + '?' + urlencode(v)
        return url


# 收到websocket错误的处理
def on_error(ws, error):
    print("### error:", error)

# 收到websocket关闭的处理
def on_close(ws, one, two):
    pass

# 收到websocket连接建立的处理
def on_open(ws):
    thread.start_new_thread(run, (ws,))

def run(ws, *args):
    data = json.dumps(gen_params(appid=ws.appid, domain=ws.domain, question=ws.question))
    ws.send(data)

# 收到websocket消息的处理
def on_message(ws, message):
    data = json.loads(message)
    code = data['header']['code']
    if code != 0:
        ws.content = f"错误代码: {code}, 信息: {data['header']['message']}"
        ws.close()
    else:
        choices = data["payload"]["choices"]
        status = choices["status"]
        content = choices["text"][0]["content"]
        ws.content += content  # 累积内容
        
        if status == 2:
            ws.close()

def gen_params(appid, domain, question):
    """
    通过appid和用户的提问来构造请请求的参数
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
        self.content = ""
        
    def chat(self, text):
        self.content = "" # 清空历史
        
        # ⚠️ 重点修改：这里使用了适配 Ultra-32K 的地址
        # 如果是 V3.5 或 V4.0 Ultra，通常使用这个地址
        Spark_url = "wss://spark-api.xf-yun.com/v4.0/chat" 
        
        wsParam = Ws_Param(APP_ID, API_KEY, API_SECRET, Spark_url)
        websocket.enableTrace(False)
        wsUrl = wsParam.create_url()
        
        ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close, on_open=on_open)
        ws.appid = APP_ID
        
        # ⚠️ 重点修改：Ultra-32K 对应的 domain 参数通常是 generalv3.5 或 generalv4
        # 如果下面这个不行，可以尝试改成 "generalv3.5"
        ws.domain = "generalv4" 
        
        ws.question = text
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        return self.content

# 实例化对象，供外部调用
agent = SparkApi()
