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

import websocket  # 注意：需要安装 websocket-client 库

# ================= 配置区域 (请替换为你自己的 Key) =================
APP_ID = "3dd79365"          # 在讯飞控制台获取，纯数字
API_KEY = "cf7b4d3e5fc58a69d2e144ea9875a094"      # 在讯飞控制台获取
API_SECRET = "MTdlYjg5ZTE3YTM2MzI3ZGE2OTFlODZh"  # 在讯飞控制台获取
# ================================================================

class SparkApi:
    def __init__(self):
        self.APP_ID = APP_ID
        self.API_KEY = API_KEY
        self.API_SECRET = API_SECRET
        # ✅ 关键修正：Spark Lite 必须使用 v1.1 接口
        self.host = "spark-api.xf-yun.com"
        self.uri = "/v1.1/chat" 
        self.domain = "general" # ✅ 关键修正：Lite 版本对应的 domain 是 general

    def create_url(self):
        # 生成鉴权 URL
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        signature_origin = "host: " + self.host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.uri + " HTTP/1.1"

        signature_sha = hmac.new(self.API_SECRET.encode('utf-8'), signature_origin.encode('utf-8'), digestmod=hashlib.sha256).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = f'api_key="{self.API_KEY}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        v = {
            "authorization": authorization,
            "date": date,
            "host": self.host
        }
        url = 'wss://' + self.host + self.uri + '?' + urlencode(v)
        return url

    def run(self, text):
        """
        主运行函数，接收用户文本，返回 AI 回答
        """
        wsUrl = self.create_url()
        
        # 初始化结果容器
        self.answer = ""
        self.error = None

        def on_message(ws, message):
            data = json.loads(message)
            code = data['header']['code']
            if code != 0:
                self.error = f"错误码: {code}, 信息: {data['header']['message']}"
                ws.close()
            else:
                choices = data["payload"]["choices"]
                status = choices["status"]
                content = choices["text"][0]["content"]
                self.answer += content
                
                # 如果是最后一条消息，关闭连接
                if status == 2:
                    ws.close()

        def on_error(ws, error):
            self.error = str(error)

        def on_close(ws, close_status_code, close_msg):
            pass

        def on_open(ws):
            thread.start_new_thread(run, (ws,))

        def run(ws, *args):
            data = json.dumps(gen_params(appid=self.APP_ID, domain=self.domain, question=text))
            ws.send(data)

        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close, on_open=on_open)
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

        if self.error:
            return f"系统出错了：{self.error}"
        return self.answer

def gen_params(appid, domain, question):
    """
    通过 appid 和用户的提问来生成请求参数
    """
    data = {
        "header": {
            "app_id": appid,
            "uid": "1234"
        },
        "parameter": {
            "chat": {
                "domain": domain,
                "temperature": 0.7, # 随机度
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

# 测试入口（可选）
if __name__ == "__main__":
    api = SparkApi()
    print("正在连接讯飞星火...")
    result = api.run("你好，请帮我写一段关于四川火锅的美食文案，要诱人一点。")
    print("AI 回复：", result)
