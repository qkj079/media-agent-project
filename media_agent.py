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
import time

# === 配置区域 (请替换为你自己的密钥) ===
APPID = "你的APPID" 
APIKey = "你的APIKey" 
APISecret = "你的APISecret" 
# ======================================

class SparkLiteApi:
    def __init__(self, appid, api_key, api_secret):
        self.appid = appid
        self.api_key = api_key
        self.api_secret = api_secret
        self.result = ""

    # 1. 生成鉴权 URL (这是之前报错缺失的关键部分)
    def get_url(self, host, path):
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        
        signature_origin = "host: {}\ndate: {}\nGET {} HTTP/1.1".format(host, date, path)
        signature_sha = hmac.new(self.api_secret.encode('utf-8'), signature_origin.encode('utf-8'), digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
        
        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            self.api_key, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        
        v = {
            "authorization": authorization,
            "date": date,
            "host": host
        }
        url = 'wss://' + host + path + '?' + urlencode(v)
        return url

    # 2. 处理 WebSocket 消息
    def on_message(self, ws, message):
        data = json.loads(message)
        code = data['header']['code']
        if code != 0:
            print(f'请求错误: {code}, {data}')
            ws.close()
        else:
            choices = data["payload"]["choices"]["text"]
            for choice in choices:
                self.result += choice["content"]

    # 3. 发起对话的主函数
    def chat(self, text):
        self.result = ""
        wsUrl = self.get_url("spark-api.xf-yun.com", "/v1.1/chat") 
        
        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(wsUrl, on_message=self.on_message)
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        
        # 简单的等待机制，实际项目中建议用回调
        timeout = 10 
        while not self.result and timeout > 0:
            time.sleep(0.5)
            timeout -= 0.5
            
        return self.result if self.result else "抱歉，连接超时或无回复。"

# 实例化对象供外部调用
agent = SparkLiteApi(APPID, APIKey, APISecret)
