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

import websocket  # 确保已安装 websocket-client

# ==========================================
# ⚠️ 请在这里填入你的讯飞星火 Key 信息
# ==========================================
APP_ID = "3dd79365"      # 控制台获取
API_SECRET = "MTdlYjg5ZTE3YTM2MzI3ZGE2OTFlODZh" # 控制台获取
API_KEY = "cf7b4d3e5fc58a69d2e144ea9875a094"     # 控制台获取
# ==========================================

class SparkApi:
    def __init__(self):
        self.response = "" # 用于存储最终的回复

    # 生成 URL
    def create_url(self):
        url = 'wss://spark-api.xf-yun.com/v3.5/chat' # v3.5 是星火 Max 版本，如需其他版本请修改
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        signature_origin = "host: spark-api.xf-yun.com\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET /v3.5/chat HTTP/1.1"

        signature_sha = hmac.new(API_SECRET.encode('utf-8'), signature_origin.encode('utf-8'), digestmod=hashlib.sha256).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = f'api_key="{API_KEY}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        v = {
            "authorization": authorization,
            "date": date,
            "host": "spark-api.xf-yun.com"
        }
        url = url + '?' + urlencode(v)
        return url

    # WebSocket 收到消息的处理逻辑
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
            self.response += content # 拼接回答
            
            if status == 2: # 结束标志
                ws.close()

    # WebSocket 发生错误的处理
    def on_error(self, ws, error):
        print("### error:", error)

    # WebSocket 关闭的处理
    def on_close(self, ws, close_status_code, close_msg):
        pass 

    # WebSocket 建立连接后的处理
    def on_open(self, ws):
        thread.start_new_thread(self.run, (ws,))

    def run(self, ws, *args):
        data = json.dumps(self.gen_params())
        ws.send(data)

    # 构造请求参数
    def gen_params(self):
        data = {
            "header": {
                "app_id": APP_ID,
                "uid": "1234"
            },
            "parameter": {
                "chat": {
                    "domain": "generalv3.5", # 对应 v3.5 接口
                    "temperature": 0.5,
                    "max_tokens": 2048
                }
            },
            "payload": {
                "message": {
                    "text": [
                        {"role": "user", "content": self.question} # 使用实例变量 self.question
                    ]
                }
            }
        }
        return data

    # 对外暴露的调用方法
    def chat(self, question):
        self.response = "" # 清空上一次回答
        self.question = question # 保存当前问题
        
        wsUrl = self.create_url()
        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(wsUrl, 
                                    on_message=self.on_message, 
                                    on_error=self.on_error, 
                                    on_close=self.on_close, 
                                    on_open=self.on_open)
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        
        return self.response
