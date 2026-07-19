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
import websocket  # 确保 requirements.txt 里有 websocket-client

# ================= 配置区域 (必须修改) =================
# 请在讯飞开放平台获取以下信息
APP_ID = "3dd79365"      # 例如: "12345678"
API_KEY = "cf7b4d3e5fc58a69d2e144ea9875a094"    # 例如: "a1b2c3d4..."
API_SECRET = "MTdlYjg5ZTE3YTM2MzI3ZGE2OTFlODZh" # 例如: "x9y8z7..."
# =====================================================

class SparkApi:
    def __init__(self):
        self.response = ""
        self.error_msg = ""

    # 生成鉴权 URL
    def create_url(self):
        url = 'wss://spark-api.xf-yun.com/v3.5/chat' # 默认使用 v3.5 版本，如果是 v2.0 请修改 URL
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        signature_origin = "host: spark-api.xf-yun.com\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET /v3.5/chat HTTP/1.1"

        signature_sha = hmac.new(API_SECRET.encode('utf-8'), signature_origin.encode('utf-8'), digestmod=hashlib.sha256).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = f'api_key="{API_KEY}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        v = {"authorization": authorization, "date": date, "host": "spark-api.xf-yun.com"}
        url = url + '?' + urlencode(v)
        return url

    # WebSocket 收到消息时的回调
    def on_message(self, ws, message):
        data = json.loads(message)
        code = data['header']['code']
        
        if code != 0:
            self.error_msg = f"请求错误: {code}, {data['header']['message']}"
            ws.close()
        else:
            choices = data["payload"]["choices"]
            status = choices["status"]
            content = choices["text"][0]["content"]
            self.response += content
            
            if status == 2: # 结束标志
                ws.close()

    # WebSocket 报错回调
    def on_error(self, ws, error):
        self.error_msg = f"WebSocket 错误: {error}"

    # WebSocket 关闭回调
    def on_close(self, ws, close_status_code, close_msg):
        pass

    # WebSocket 建立连接回调
    def on_open(self, ws):
        thread.start_new_thread(self.run, (ws,))

    def run(self, ws, *args):
        data = json.dumps(self.gen_params())
        ws.send(data)

    # 构造发送给讯飞的参数
    def gen_params(self):
        return {
            "header": {
                "app_id": APP_ID,
                "uid": "1234"
            },
            "parameter": {
                "chat": {
                    "domain": "generalv3.5", # 对应 v3.5 模型
                    "temperature": 0.5,
                    "max_tokens": 2048
                }
            },
            "payload": {
                "message": {
                    "text": [
                        {"role": "user", "content": self.question} # 这里的 question 需要在 chat 方法里赋值
                    ]
                }
            }
        }

    # 对外调用的主方法
    def chat(self, prompt):
        self.response = ""
        self.error_msg = ""
        self.question = prompt
        
        ws_url = self.create_url()
        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(ws_url, 
                                    on_message=self.on_message, 
                                    on_error=self.on_error, 
                                    on_close=self.on_close)
        ws.on_open = self.on_open
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

        if self.error_msg:
            return f"系统内部错误: {self.error_msg}"
        
        return self.response
