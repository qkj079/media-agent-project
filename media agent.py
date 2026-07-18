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
        
        # 【关键配置】Lite版本接口地址
        self.Host = "spark-api.xf-yun.com"
        self.URI = "/v1.1/chat" 
        self.Url = "wss://spark-api.xf-yun.com/v1.1/chat"
        self.Domain = "general"  # Lite版本对应的Domain是 general

    # 生成鉴权 URL
    def create_url(self):
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        
        signature_origin = "host: " + self.Host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.URI + " HTTP/1.1"
        
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'), digestmod=hashlib.sha256).digest()
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
            print(content, end="")
            
            # 将结果存入实例变量以便外部获取
            self.last_response = content
            
            if status == 2:
                ws.close()

    def on_error(self, ws, error):
        print("### error:", error)

    def on_close(self, ws, close_status_code, close_msg):
        pass

    def on_open(self, ws):
        thread.start_new_thread(self.run, (ws,))

    def run(self, ws, *args):
        data = json.dumps(self.gen_params())
        ws.send(data)

    def gen_params(self):
        data = {
            "header": {
                "app_id": self.APPID,
                "uid": "1234"
            },
            "parameter": {
                "chat": {
                    "domain": self.Domain,
                    "temperature": 0.5,
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
        return data

    def start_chat(self, question):
        self.question = question
        self.last_response = ""
        wsUrl = self.create_url()
        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(wsUrl, on_message=self.on_message, on_error=self.on_error, on_close=self.on_close)
        ws.on_open = self.on_open
        # 【修复点】这里必须导入 ssl 模块才能使用 ssl.CERT_NONE
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        return self.last_response

# 测试代码（可选）
if __name__ == "__main__":
    # 请替换为你真实的 Key
    app_id = "YOUR_APPID"
    api_key = "YOUR_APIKEY"
    api_secret = "YOUR_APISECRET"
    
    spark = SparkLiteApi(app_id, api_key, api_secret)
    print("开始对话...")
    response = spark.start_chat("你好，介绍一下你自己")
    print("\n回答结束:", response)
