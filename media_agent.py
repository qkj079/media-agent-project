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
# 请确保这里填入了正确的值，否则无法连接
APP_ID = "3dd79365"      # 你的 AppID
API_KEY = "cf7b4d3e5fc58a69d2e144ea9875a094"   # 你的 WebAPI Key
API_SECRET = "MTdlYjg5ZTE3YTM2MzI3ZGE2OTFlODZh" # 你的 WebAPI Secret

DOMAIN = "generalv3.5"  # 模型版本：v3.5 (Max)
SPARK_URL = "wss://spark-api.xf-yun.com/v3.5/chat"
# ======================================================

class SparkApi:
    def __init__(self):
        self.APP_ID = APP_ID
        self.API_KEY = API_KEY
        self.API_SECRET = API_SECRET
        self.Domain = DOMAIN
        self.Spark_url = SPARK_URL
        self.answer = ""  # 用于存储最终的回答

    # 生成 URL 鉴权参数
    def create_url(self):
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        signature_origin = "host: spark-api.xf-yun.com\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET /v3.5/chat HTTP/1.1"
        
        signature_sha = hmac.new(self.API_SECRET.encode('utf-8'), signature_origin.encode('utf-8'), digestmod=hashlib.sha256).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')
        
        authorization_origin = f'api_key="{self.API_KEY}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        
        v = {
            "authorization": authorization,
            "date": date,
            "host": "spark-api.xf-yun.com"
        }
        url = self.Spark_url + '?' + urlencode(v)
        return url

    # WebSocket 收到消息时的回调处理
    def on_message(self, ws, message):
        data = json.loads(message)
        code = data['header']['code']
        if code != 0:
            print(f'请求错误: {code}, {data}')
            ws.close()
        else:
            choices = data["payload"]["choices"]
            status = choices["status"]
            content = choices["text"][0]["content"]
            self.answer += content  # 拼接回答
            
            if status == 2:  # 2 代表回答结束
                ws.close()

    # WebSocket 报错处理
    def on_error(self, ws, error):
        print("### error:", error)

    # WebSocket 关闭处理
    def on_close(self, ws, close_status_code, close_msg):
        pass

    # WebSocket 建立连接后发送数据
    def on_open(self, ws):
        thread.start_new_thread(self.run, (ws,))

    def run(self, ws, *args):
        data = json.dumps(self.gen_params())
        ws.send(data)

    # 构造发送给大模型的参数
    def gen_params(self):
        return {
            "header": {
                "app_id": self.APP_ID,
                "uid": "1234"
            },
            "parameter": {
                "chat": {
                    "domain": self.Domain,
                    "temperature": 0.7,
                    "max_tokens": 2048
                }
            },
            "payload": {
                "message": {
                    "text": [
                        {"role": "user", "content": self.question} 
                    ]
                }
            }
        }

    # 核心方法：发起对话
    def chat(self, question):
        self.answer = ""  # 清空上一次回答
        self.question = question  # 设置当前问题
        
        ws_url = self.create_url()
        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(
            ws_url, 
            on_message=self.on_message, 
            on_error=self.on_error, 
            on_close=self.on_close
        )
        ws.on_open = self.on_open
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        
        return self.answer  # 返回 AI 生成的完整内容
