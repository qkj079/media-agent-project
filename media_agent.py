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
# 请在讯飞开放平台控制台获取以下信息
APP_ID = "3dd79365"      # 纯数字
API_KEY = "cf7b4d3e5fc58a69d2e144ea9875a094"
API_SECRET = "MTdlYjg5ZTE3YTM2MzI3ZGE2OTFlODZh"
# ======================================================

class Ws_Param(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret, Spark_url):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.host = urlparse(Spark_url).netloc
        self.path = urlparse(Spark_url).path
        self.Spark_url = Spark_url

    # 生成url
    def create_url(self):
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + self.host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.path + " HTTP/1.1"

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
            "host": self.host
        }
        # 拼接鉴权参数，生成url地址
        url = self.Spark_url + '?' + urlencode(v)
        return url

# 收到websocket错误的处理
def on_error(ws, error):
    print("### error:", error)

# 收到websocket关闭的处理
def on_close(ws, one, two):
    print(" ")

# 收到websocket连接建立的处理
def on_open(ws):
    thread.start_new_thread(run, (ws,))

def run(ws, *args):
    data = json.dumps(gen_params(appid=ws.appid, domain=ws.domain, question=ws.question))
    ws.send(data)

# 收到websocket消息的处理
def on_message(ws, message):
    # print(message)
    data = json.loads(message)
    code = data['header']['code']
    if code != 0:
        print(f'请求错误: {code}, {data}')
        ws.close()
    else:
        choices = data["payload"]["choices"]
        status = choices["status"]
        content = choices["text"][0]["content"]
        # print(content, end="") # 调试用
        ws.content += content  # 将内容追加到 ws 对象的一个属性中
        
        if status == 2:
            ws.close()

def gen_params(appid, domain, question):
    """
    通过appid和用户的提问来生成请参数
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
                    {
                        "role": "user",
                        "content": question
                    }
                ]
            }
        }
    }
    return data

class SparkApi:
    def __init__(self):
        # ✅ 关键修正：Spark Lite 必须使用 v1.1 接口
        self.url = "wss://spark-api.xf-yun.com/v1.1/chat"
        self.domain = "general" # Lite版本对应 general

    def chat(self, question):
        """
        这是主程序调用的入口函数
        """
        wsParam = Ws_Param(APP_ID, API_KEY, API_SECRET, self.url)
        websocket.enableTrace(False)
        wsUrl = wsParam.create_url()
        
        ws = websocket.WebSocketApp(wsUrl, 
                                    on_message=on_message, 
                                    on_error=on_error, 
                                    on_close=on_close, 
                                    on_open=on_open)
        ws.appid = APP_ID
        ws.question = question
        ws.domain = self.domain
        ws.content = "" # 初始化一个空字符串用来存结果
        
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        
        return ws.content

# 测试代码（本地运行时可以解开注释测试）
# if __name__ == "__main__":
#     api = SparkApi()
#     print(api.chat("你好"))
