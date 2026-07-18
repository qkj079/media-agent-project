import base64
import hashlib
import hmac
import json
import time
from datetime import datetime  # 这里只导入 datetime 类
from wsgiref.handlers import format_date_time
from urllib.parse import urlencode
from time import mktime

import websocket
import _thread as thread  # 恢复使用 _thread，这是讯飞官方示例的标准写法，Streamlit 兼容没问题

class SparkLiteApi:
    def __init__(self, APPID, APIKey, APISecret):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        
        # 【确认】这里是 Lite 版本的地址
        self.Host = "spark-api.xf-yun.com"
        self.URI = "/v1.1/chat" 
        self.Url = "wss://spark-api.xf-yun.com/v1.1/chat"

    # 生成鉴权 URL
    def create_url(self):
        # 获取当前时间
        now = datetime.now() 
        date = format_date_time(mktime(now.timetuple()))

        signature_origin = "host: " + self.Host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.URI + " HTTP/1.1"

        # 进行 hmac-sha256 加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'), digestmod=hashlib.sha256).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": self.Host
        }
        # 拼接鉴权参数，生成 url 地址
        url = self.Url + '?' + urlencode(v)
        return url

    # 收到 websocket 错误的处理
    def on_error(self, ws, error):
        print("### error:", error)

    # 收到 websocket 关闭的处理
    def on_close(self, ws, one, two):
        pass 

    # 收到 websocket 建立连接后的处理
    def on_open(self, ws):
        thread.start_new_thread(self.run, (ws,))

    def run(self, ws, *args):
        data = json.dumps(self.gen_params())
        ws.send(data)

    # 收到 websocket 消息的处理
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
            print(content, end="") # 打印生成的文字
            
            # 如果是最后一条消息，关闭连接
            if status == 2:
                ws.close()

    def gen_params(self):
        """
        通过 appid, key, secret 生成鉴权参数并发起请求
        """
        data = {
            "header": {
                "app_id": self.APPID,
                "uid": "1234"
            },
            "parameter": {
                "chat": {
                    # 【确认】Lite 版本对应 domain 为 general
                    "domain": "general", 
                    "temperature": 0.5,
                    "max_tokens": 2048
                }
            },
            "payload": {
                "message": {
                    "text": [
                        # 这里可以预设一个问题，或者由外部传入
                        {"role": "user", "content": "你好"} 
                    ]
                }
            }
        }
        return data

    def start_chat(self, question="你好"):
        wsUrl = self.create_url()
        ws = websocket.WebSocketApp(wsUrl, on_message=self.on_message, on_error=self.on_error, on_close=self.on_close)
        ws.on_open = self.on_open
        
        # 修改 payload 中的问题
        # 注意：实际使用中，你应该把 question 传进去
        # 这里为了演示简单，直接在 run 里面发数据
        
        # 重写 run 方法以支持动态提问（简单起见，这里直接覆盖上面的 run 逻辑）
        def dynamic_run(ws):
            data = json.dumps(self.gen_params())
            # 替换里面的问题
            msg_data = json.loads(data)
            msg_data["payload"]["message"]["text"] = [{"role": "user", "content": question}]
            ws.send(json.dumps(msg_data))
            
        ws.on_open = lambda ws: dynamic_run(ws)
        
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

# 测试代码（可选）
if __name__ == "__main__":
    # 请在这里填入你的真实 Key
    spark = SparkLiteApi("你的APPID", "你的APIKey", "你的APISecret")
    spark.start_chat("你好，介绍一下你自己")
