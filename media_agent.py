import _thread as thread
import base64
import datetime
import hashlib
import hmac
import json
import ssl
import time
from datetime import datetime
from time import mktime
from urllib.parse import urlparse, urlencode
from wsgiref.handlers import format_date_time

import websocket

# ================== ⚠️ 核心配置区 (必填) ==================
APP_ID = "3dd79365"
API_KEY = "在此处粘贴你的API_KEY"
API_SECRET = "在此处粘贴你的API_SECRET"
# =======================================================

# 模型版本配置（根据你的讯飞应用选择）
# Ultra-32K 用 generalv3.5，Pro 用 generalv3，Max 用 generalv3.5
DOMAIN = "generalv3.5"
SPARK_URL = "wss://spark-api.xf-yun.com/v3.5/chat"

# 如果上面连不上，注释掉上面两行，改用下面这组（Pro版本）
# DOMAIN = "generalv3"
# SPARK_URL = "wss://spark-api.xf-yun.com/v3.1/chat"


def create_url():
    """生成带鉴权信息的 WebSocket URL"""
    parsed = urlparse(SPARK_URL)
    host = parsed.netloc
    path = parsed.path

    now = datetime.now()
    date = format_date_time(mktime(now.timetuple()))

    signature_origin = "host: " + host + "\n"
    signature_origin += "date: " + date + "\n"
    signature_origin += "GET " + path + " HTTP/1.1"

    signature_sha = hmac.new(
        API_SECRET.encode('utf-8'),
        signature_origin.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()

    signature_sha_base64 = base64.b64encode(signature_sha).decode('utf-8')

    authorization_origin = (
        f'api_key="{API_KEY}", '
        f'algorithm="hmac-sha256", '
        f'headers="host date request-line", '
        f'signature="{signature_sha_base64}"'
    )
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')

    v = {
        "authorization": authorization,
        "date": date,
        "host": host
    }
    url = SPARK_URL + '?' + urlencode(v)
    return url


def chat(question):
    """
    向讯飞星火发送问题并等待完整回答。
    这是 app.py 中调用的唯一接口。
    """
    # 检查 Key 是否填写
    if "在此处粘贴" in API_KEY or "在此处粘贴" in API_SECRET:
        return "❌ **配置错误**：请先在 `media_agent.py` 顶部填入真实的 API_KEY 和 API_SECRET！"

    # 用于存储结果和状态的容器
    result = {"answer": "", "error": None, "done": False}

    def on_message(ws, message):
        """收到讯飞返回的消息"""
        data = json.loads(message)
        code = data['header']['code']

        if code != 0:
            # 讯飞返回了错误
            result["error"] = f"讯飞错误码 {code}：{data['header']['message']}"
            result["done"] = True
            ws.close()
        else:
            # 正常返回，拼接内容
            choices = data["payload"]["choices"]
            status = choices["status"]
            content = choices["text"][0]["content"]
            result["answer"] += content

            if status == 2:
                # status=2 表示回答完毕
                result["done"] = True
                ws.close()

    def on_error(ws, error):
        """WebSocket 连接出错"""
        result["error"] = f"连接错误：{str(error)}"
        result["done"] = True

    def on_close(ws, close_status_code, close_msg):
        """WebSocket 连接关闭"""
        result["done"] = True

    def on_open(ws):
        """连接建立后，发送问题"""
        def run(*args):
            data = {
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
                            {"role": "user", "content": question}
                        ]
                    }
                }
            }
            ws.send(json.dumps(data))
        thread.start_new_thread(run, ())

    # 建立 WebSocket 连接
    ws_url = create_url()
    ws = websocket.WebSocketApp(
        ws_url,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open
    )

    # 在后台线程中运行 WebSocket
    thread.start_new_thread(
        ws.run_forever,
        (),
        {"sslopt": {"cert_reqs": ssl.CERT_NONE}}
    )

    # ⚠️ 关键修复：等待讯飞返回结果（最多等 30 秒）
    timeout = 30  # 最大等待秒数
    waited = 0
    while not result["done"] and waited < timeout:
        time.sleep(0.5)
        waited += 0.5

    # 超时处理
    if not result["done"]:
        ws.close()
        return f"⚠️ **请求超时**（等待了 {timeout} 秒没有收到回复）。请检查网络连接或 Key 是否正确。"

    # 如果有错误，返回错误信息
    if result["error"]:
        return f"❌ **请求失败**\n\n{result['error']}\n\n请检查 `media_agent.py` 中的 Key 和模型版本配置。"

    # 返回正常回答
    return result["answer"]
