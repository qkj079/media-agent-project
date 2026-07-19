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
# 请将这里的 Key 换成你自己的，或者使用 Streamlit Secrets
APP_ID = "3dd79365"  
API_KEY = "cf7b4d3e5fc58a69d2e144ea9875a094" 
API_SECRET = "MTdlYjg5ZTE3YTM2MzI3ZGE2OTFlODZh" 

# 模型版本配置 (Ultra-32K 对应 v3.5)
DOMAIN = "generalv3.5"
SPARK_URL = "wss://spark-api.xf-yun.com/v3.5/chat"
# =======================================================

class SparkApi:
    """
    这就是 app.py 正在寻找的类！
    它封装了讯飞的所有连接逻辑。
    """
    def __init__(self):
        self.answer = ""
        self.total_tokens = 0
        
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
            self.answer += content
            
            # 如果对话结束
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
        return {
            "header": {
                "app_id": APP_ID,
                "uid": "1234"
            },
            "parameter": {
                "chat": {
                    "domain": DOMAIN,
                    "temperature": 0.5,
                    "max_tokens": 2048
                }
            },
            "payload": {
                "message": {
                    "text": [
                        {"role": "user", "content": "你好"} 
                    ]
                }
            }
        }

    def get_url(self):
        host = urlparse(SPARK_URL).netloc
        path = urlparse(SPARK_URL).path
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        
        signature_origin = "host: " + host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + path + " HTTP/1.1"
        
        signature_sha = hmac.new(API_SECRET.encode('utf-8'), signature_origin.encode('utf-8'), digestmod=hashlib.sha256).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')
        
        authorization_origin = f'api_key="{API_KEY}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        
        url = SPARK_URL + "?" + urlencode({"authorization": authorization, "date": date, "host": host})
        return url

    def ask(self, question):
        """
        这是主程序调用的入口函数
        """
        self.answer = "" # 清空上次回答
        wsUrl = self.get_url()
        
        # 更新问题到参数中
        # 注意：这里为了简化，每次都是单轮对话。如果需要多轮，需要维护 history 列表
        self.gen_params()['payload']['message']['text'] = [{"role": "user", "content": question}]

        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(
            wsUrl,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        
        return self.answer
