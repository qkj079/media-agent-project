import streamlit as st
import hashlib
import base64
import hmac
import json
import websocket
import _thread as thread
import time
from datetime import datetime
from wsgiref.handlers import format_date_time
from urllib.parse import urlencode
import ssl

# ==========================================
# 1. 配置区域 (请确保这里填入了正确的 Key)
# ==========================================
# 建议优先从环境变量读取，如果没有则使用默认值（请替换为你自己的）
APP_ID = st.secrets.get("APP_ID", "你的_APP_ID")
API_KEY = st.secrets.get("API_KEY", "你的_API_KEY")
API_SECRET = st.secrets.get("API_SECRET", "你的_API_SECRET")

# 讯飞星火 v3.5 接口地址 (根据你的版本调整，v3.5 是目前较新的)
SPARK_URL = "wss://spark-api.xf-yun.com/v3.5/chat"

# ==========================================
# 2. 核心 WebSocket 类 (原生实现，不依赖 SDK)
# ==========================================
class SparkWebSocket:
    def __init__(self, app_id, api_key, api_secret, url):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.url = url
        self.answer = "" # 用于存储完整的回答

    # 生成鉴权 URL
    def create_url(self):
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        signature_origin = "host: spark-api.xf-yun.com\n"
        signature_origin += f"date: {date}\n"
        signature_origin += "GET /v3.5/chat HTTP/1.1"

        signature_sha = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        v = {
            "authorization": authorization,
            "date": date,
            "host": "spark-api.xf-yun.com"
        }
        url = self.url + '?' + urlencode(v)
        return url

    # 启动连接
    def run(self, prompt, on_message_callback):
        ws_url = self.create_url()

        def on_message(ws, message):
            data = json.loads(message)
            code = data['header']['code']
            if code != 0:
                st.error(f'请求错误: {code}, {data}')
                ws.close()
            else:
                choices = data["payload"]["choices"]
                status = choices["status"]
                content = choices["text"][0]["content"]
                self.answer += content

                # 将内容传回给 Streamlit 进行显示
                on_message_callback(content)

                if status == 2:
                    ws.close()

        def on_error(ws, error):
            st.error(f"WebSocket 错误: {error}")

        def on_close(ws, close_status_code, close_msg):
            pass

        def on_open(ws):
            frame = {
                "header": {
                    "app_id": self.app_id,
                    "uid": "1234"
                },
                "parameter": {
                    "chat": {
                        "domain": "generalv3.5", # 对应 v3.5 版本
                        "temperature": 0.7,
                        "max_tokens": 2048
                    }
                },
                "payload": {
                    "message": {
                        "text": [
                            {"role": "user", "content": prompt}
                        ]
                    }
                }
            }
            ws.send(json.dumps(frame))

        # 创建 WebSocket 连接
        # 关键点：使用 sslopt={"cert_reqs": ssl.CERT_NONE} 有时能绕过某些云端证书问题，
        # 但标准做法是保持默认。如果遇到 SSL 错误，可以尝试开启这个选项。
        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        ws.on_open = on_open

        # 这里的 run_forever 是阻塞的，所以通常需要在 Streamlit 中配合线程或异步使用
        # 为了简化，我们在下方调用时处理
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})


# ==========================================
# 3. Streamlit 界面逻辑
# ==========================================
st.set_page_config(page_title="传媒专业智能助手", page_icon="📺", layout="wide")
st.title("📺 传媒专业智能助手")
st.caption("基于讯飞星火大模型构建，专注传媒领域问答与文案创作")

# 初始化 Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示历史消息
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 输入框
if prompt := st.chat_input("请输入你的问题..."):
    # 1. 显示用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. 准备接收 AI 回复
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        # 定义回调函数：每当收到一个字，就更新界面
        def update_ui(text_chunk):
            nonlocal full_response
            full_response += text_chunk
            message_placeholder.markdown(full_response + "▌")

        try:
            # 3. 调用原生 WebSocket 类
            spark_bot = SparkWebSocket(APP_ID, API_KEY, API_SECRET, SPARK_URL)
            # 注意：run_forever 是阻塞的，Streamlit 会等待它执行完
            # 在这里我们传入 prompt 和 回调函数
            spark_bot.run(prompt, on_message_callback=update_ui)

            # 4. 移除光标并保存历史记录
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"发生异常: {e}")
            st.info("提示：如果是 'module websocket has no attribute ssl'，请检查 requirements.txt 是否已删除 spark-ai-python 并重新部署。")
