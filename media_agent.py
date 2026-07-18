# media_agent.py
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

class SparkLiteApi:
    def __init__(self, app_id, api_key, api_secret):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.answer = ""

    # ...这里省略掉那些复杂的加密签名函数(get_url, create_header等)，保持你原有的即可...
    # 只要你原来的代码里有 get_url 和 on_message 逻辑就行。

    # 【关键】必须添加或修改这个 chat 方法
    def chat(self, question):
        self.answer = "" # 清空上一次回答
        wsUrl = self.get_url() # 假设你原来有获取URL的方法
        
        # 启动 WebSocket 连接
        thread.start_new_thread(self.run, (wsUrl, question))
        
        # 简单等待一下结果返回（实际生产环境建议用回调，这里为了简单演示）
        import time
        while not self.answer and len(self.answer) == 0:
             time.sleep(0.1)
             # 注意：这里需要配合 on_message 把结果存进 self.answer
        return self.answer 

    def run(self, wsUrl, question):
        # 这里是你原来的 WebSocket 连接逻辑
        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(wsUrl, on_message=self.on_message, on_error=self.on_error, on_close=self.on_close)
        ws.on_open = lambda ws: self.on_open(ws, question)
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

    def on_message(self, ws, message):
        data = json.loads(message)
        code = data['header']['code']
        if code != 0:
            self.answer = f"错误: {code}"
            ws.close()
        else:
            choices = data["payload"]["choices"]["text"]
            for choice in choices:
                self.answer += choice["content"]
            # 如果是最后一段，可以关闭连接
            if data["header"]["status"] == 2:
                ws.close()

    # ... 其他 on_error, on_close, on_open, get_url 等辅助函数保持原样 ...
