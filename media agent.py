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

import websocket  # 需安装: pip install websocket-client

class SparkLiteApi:
    def __init__(self, APPID, APIKey, APISecret):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        
        # 【关键修改】这里改为 Lite 版本的地址
        self.Host = "spark-api.xf-yun.com"
        self.URI = "/v1.1/chat" 
        self.Url = "wss://spark-api.xf-yun.com/v1.1/chat"

    # 生成鉴权 URL
    def create_url(self):
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        signature_origin = "host: " + self.Host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.URI + " HTTP/1.1"

        signature_sha = hmac.new(
            self.APISecret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        v = {
            "authorization": authorization,
            "date": date,
            "host": self.Host
        }
        url = self.Url + '?' + urlencode(v)
        return url

    # 发送消息并获取回复
    def run(self, question):
        wsUrl = self.create_url()
        
        # 用于存储接收到的完整回答
        self.answer_content = "" 
        
        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(
            wsUrl, 
            on_message=self.on_message, 
            on_error=self.on_error, 
            on_close=self.on_close
        )
        ws.on_open = self.on_open
        ws.appid = self.APPID
        ws.question = question
        
        # 运行 WebSocket，直到连接关闭
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        
        return self.answer_content

    # WebSocket 建立连接后发送数据
    def on_open(self, ws):
        def run(*args):
            d = {
                "header": {
                    "app_id": ws.appid,
                    "uid": "1234" # 用户ID，可随意填写
                },
                "parameter": {
                    "chat": {
                        # 【关键修改】Lite 版本必须用 "general"
                        "domain": "general", 
                        "temperature": 0.5,
                        "max_tokens": 2048
                    }
                },
                "payload": {
                    "message": {
                        "text": [
                            {"role": "user", "content": ws.question}
                        ]
                    }
                }
            }
            d = json.dumps(d)
            ws.send(d)
            
        thread.start_new_thread(run, ())

    # 收到消息的处理逻辑
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
            
            # 累积回答内容
            self.answer_content += content
            
            # 可以在这里打印流式输出，或者留给 Streamlit 处理
            # print(content, end="") 

            if status == 2:
                ws.close()

    def on_error(self, ws, error):
        print("### WebSocket Error ###:", error)

    def on_close(self, ws, close_status_code, close_msg):
        pass # 连接关闭时不做特殊处理
