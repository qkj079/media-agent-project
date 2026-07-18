import base64
import datetime
import hashlib
import hmac
import json
from urllib.parse import urlparse, urlencode
from time import mktime
from wsgiref.handlers import format_date_time
from datetime import datetime

import websocket  # 需安装: pip install websocket-client
import threading  # 【修改点】使用标准 threading 替代 _thread

class SparkLiteApi:
    def __init__(self, APPID, APIKey, APISecret):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        
        # 【确认】这里是 Spark Lite (免费版) 的地址
        self.Host = "spark-api.xf-yun.com"
        self.URI = "/v1.1/chat" 
        self.Url = "wss://spark-api.xf-yun.com/v1.1/chat"

    # 生成鉴权 URL
    def create_url(self):
        # 生成 RFC1123 格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接签名原始串
        signature_origin = "host: " + self.Host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.URI + " HTTP/1.1"

        # 进行 HMAC-SHA256 加密
        signature_sha = hmac.new(
            self.APISecret.encode('utf-8'), 
            signature_origin.encode('utf-8'), 
            digestmod=hashlib.sha256
        ).digest()
        
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

        # 拼接 Authorization 头
        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        # 拼接最终 URL
        v = {
            "authorization": authorization,
            "date": date,
            "host": self.Host
        }
        url = self.Url + '?' + urlencode(v)
        return url

    def run(self, text_list):
        """
        运行 API 调用
        :param text_list: 对话历史列表，例如 [{"role": "user", "content": "你好"}]
        :return: 完整的回答字符串
        """
        wsUrl = self.create_url()
        
        # 用于存储返回结果的容器
        result_container = {"text": "", "error": None}
        
        # 定义 WebSocket 回调函数
        def on_message(ws, message):
            data = json.loads(message)
            code = data.get("header", {}).get("code")
            
            if code != 0:
                # 错误处理
                result_container["error"] = f"Error {code}: {data.get('header', {}).get('message', 'Unknown error')}"
                ws.close()
            else:
                choices = data.get("payload", {}).get("choices", {}).get("text", [])
                for item in choices:
                    result_container["text"] += item.get("content", "")
                
                # 如果是最后一帧，关闭连接
                if data.get("header", {}).get("status") == 2:
                    ws.close()

        def on_error(ws, error):
            result_container["error"] = str(error)

        def on_close(ws, close_status_code, close_msg):
            pass

        def on_open(ws):
            # 构造请求参数
            gen_params = {
                "header": {
                    "app_id": self.APPID,
                    "uid": "1234"
                },
                "parameter": {
                    "chat": {
                        "domain": "general",  # 【确认】Lite 版本必须是 general
                        "temperature": 0.5,
                        "max_tokens": 1024
                    }
                },
                "payload": {
                    "message": {
                        "text": text_list
                    }
                }
            }
            ws.send(json.dumps(gen_params))

        # 建立连接
        try:
            ws = websocket.WebSocketApp(
                wsUrl, 
                on_message=on_message, 
                on_error=on_error, 
                on_close=on_close, 
                on_open=on_open
            )
            # 【修改点】使用 threading 模块启动，避免阻塞主进程
            wst = threading.Thread(target=ws.run_forever, kwargs={"sslopt": {"cert_reqs": ssl.CERT_NONE}})
            wst.start()
            wst.join()  # 等待线程结束
            
            if result_container["error"]:
                return f"出错了：{result_container['error']}"
            return result_container["text"]
            
        except Exception as e:
            return f"连接建立失败：{str(e)}"

# 测试代码（仅在直接运行此文件时执行）
if __name__ == "__main__":
    # 这里填入你的真实 Key 进行测试
    app_id = "YOUR_APP_ID"
    api_key = "YOUR_API_KEY"
    api_secret = "YOUR_API_SECRET"
    
    agent = SparkLiteApi(app_id, api_key, api_secret)
    print("正在连接讯飞星火 Lite...")
    response = agent.run([{"role": "user", "content": "你好"}])
    print(f"回复：{response}")
