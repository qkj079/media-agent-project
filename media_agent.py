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

import websocket  # 使用 websocket-client 库

# ================== 1. 配置区域 (必填) ==================
# 这里的 ID 是根据你截图填写的，如果不对请修正
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


class SparkApi:
    def __init__(self):
        # 针对不同模型的 URL 配置
        # Ultra-32K 通常对应 generalv3.5 或 generalv3
        self.domain = "generalv3.5" 
        self.spark_url = "wss://spark-api.xf-yun.com/v3.5/chat"
        
        # 如果上面的 v3.5 报错，可以尝试改成 v3.1 (对应 Pro 版本)
        # self.domain = "generalv3"
        # self.spark_url = "wss://spark-api.xf-yun.com/v3.1/chat"

    def chat(self, question):
        """对外提供的聊天接口"""
        if not APP_ID or not API_KEY or not API_SECRET:
            return "❌ 错误：请在 media_agent.py 顶部填入有效的 APP_ID, API_KEY 和 API_SECRET！"

        wsParam = Ws_Param(APPID=APP_ID, APIKey=API_KEY,
                           APISecret=API_SECRET,
                           Spark_url=self.spark_url)
        
        try:
            websocket.enableTrace(False)
            wsUrl = wsParam.create_url()
            ws = websocket.WebSocketApp(wsUrl, on_message=self.on_message, on_error=self.on_error, on_close=self.on_close, on_open=self.on_open)
            ws.appid = APP_ID
            ws.question = question
            ws.domain = self.domain
            ws.answer = "" # 用于存储回答
            
            ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
            
            if ws.answer:
                return ws.answer
            else:
                return "AI 没有返回内容，请检查 Key 是否正确或网络是否通畅。"
                
        except Exception as e:
            return f"发生异常: {str(e)}"

    # --- 以下是 WebSocket 的回调函数 ---

    # 收到websocket错误的处理
    def on_error(self, ws, error):
        print("### error:", error)

    # 收到websocket关闭的处理
    def on_close(self, ws, one, two):
        pass # print("### closed ###")

    # 收到websocket连接建立的处理
    def on_open(self, ws):
        thread.start_new_thread(self.run, (ws,))

    def run(self, ws, *args):
        data = json.dumps(self.gen_params())
        ws.send(data)

    # 收到websocket消息的处理
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
            # 累积答案
            ws.answer += content
            
            if status == 2:
                ws.close()

    # 生成发送给大模型的参数
    def gen_params(self):
        data = {
            "header": {
                "app_id": APP_ID,
                "uid": "1234"
            },
            "parameter": {
                "chat": {
                    "domain": self.domain,
                    "random_threshold": 0.5,
                    "max_tokens": 2048,
                    "auditing": "default"
                }
            },
            "payload": {
                "message": {
                    "text": [
                        {"role": "user", "content": ws.question} # 这里引用外部的 question
                    ]
                }
            }
        }
        return data
