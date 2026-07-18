import streamlit as st
import _thread as thread
import base64
import datetime
import hashlib
import hmac
import json
from urllib.parse import urlparse, urlencode
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import websocket

# --- 页面配置 ---
st.set_page_config(page_title="传媒专业智能助手", page_icon="📺")
st.title("📺 传媒专业智能助手")
st.caption("基于讯飞星火原生 SDK 构建，修复鉴权问题")

# --- 侧边栏配置 ---
with st.sidebar:
    st.header("⚙️ API 配置")
    app_id = st.text_input("APPID", type="password", value=st.session_state.get("app_id", ""))
    api_key = st.text_input("APIKey", type="password", value=st.session_state.get("api_key", ""))
    api_secret = st.text_input("APISecret", type="password", value=st.session_state.get("api_secret", ""))
    
    # 模型选择映射
    model_map = {
        "Spark Lite (免费/快)": {"domain": "general", "url": "wss://spark-api.xf-yun.com/v1.1/chat"},
        "Spark Pro (均衡)": {"domain": "generalv3", "url": "wss://spark-api.xf-yun.com/v3.1/chat"},
        "Spark Max (最强)": {"domain": "generalv3.5", "url": "wss://spark-api.xf-yun.com/v3.5/chat"},
    }
    selected_model_label = st.selectbox("选择模型", list(model_map.keys()))
    selected_model = model_map[selected_model_label]

    if st.button("💾 保存并测试连接"):
        if app_id and api_key and api_secret:
            st.session_state.app_id = app_id
            st.session_state.api_key = api_key
            st.session_state.api_secret = api_secret
            st.session_state.model_config = selected_model
            st.success("✅ 配置已保存！")
        else:
            st.error("❌ 请填写完整信息")

# --- 核心 WebSocket 类 (修复鉴权的关键) ---
class WsParam:
    def __init__(self, app_id, api_key, api_secret, spark_url, domain):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.spark_url = spark_url
        self.domain = domain
        self.host = urlparse(self.spark_url).netloc
        self.path = urlparse(self.spark_url).path

    def create_url(self):
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        signature_origin = "host: " + self.host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.path + " HTTP/1.1"
        signature_sha = hmac.new(self.api_secret.encode('utf-8'), signature_origin.encode('utf-8'), digestmod=hashlib.sha256).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')
        authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        v = {"authorization": authorization, "date": date, "host": self.host}
        url = self.spark_url + '?' + urlencode(v)
        return url

# --- 聊天逻辑 ---
def on_message(ws, message):
    data = json.loads(message)
    code = data['header']['code']
    if code != 0:
        st.session_state.response_error = f"错误代码: {code}, 原因: {data['header']['message']}"
        ws.close()
    else:
        choices = data["payload"]["choices"]
        status = choices[0]["status"]
        content = choices[0]["content"]["text"]
        st.session_state.current_response += content
        
        if status == 2:
            ws.close()

def on_error(ws, error):
    st.session_state.response_error = str(error)

def on_close(ws, close_status_code, close_msg):
    pass

def on_open(ws):
    thread.start_new_thread(run, (ws,))

def run(ws, *args):
    config = st.session_state.get("model_config")
    if not config: return
    
    data = json.dumps({
        "header": {"app_id": st.session_state.app_id, "uid": "1234"},
        "parameter": {"chat": {"domain": config["domain"], "temperature": 0.5, "max_tokens": 2048}},
        "payload": {"message": {"text": [{"role": "user", "content": st.session_state.user_prompt}]}}
    })
    ws.send(data)

if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示历史消息
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 输入框
if prompt := st.chat_input("请输入你的问题..."):
    if not st.session_state.get("app_id"):
        st.error("请先在左侧配置 API 信息！")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        st.session_state.current_response = ""
        st.session_state.response_error = None
        st.session_state.user_prompt = prompt

        try:
            ws_param = WsParam(
                app_id=st.session_state.app_id,
                api_key=st.session_state.api_key,
                api_secret=st.session_state.api_secret,
                spark_url=st.session_state.model_config["url"],
                domain=st.session_state.model_config["domain"]
            )
            websocket.enableTrace(False)
            ws_url = ws_param.create_url()
            ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_error=on_error, on_close=on_close)
            ws.on_open = on_open
            ws.run_forever(sslopt={"cert_reqs": websocket.ssl.CERT_NONE})

            if st.session_state.response_error:
                st.error(f"生成出错: {st.session_state.response_error}")
            else:
                message_placeholder.markdown(st.session_state.current_response)
                st.session_state.messages.append({"role": "assistant", "content": st.session_state.current_response})

        except Exception as e:
            st.error(f"连接异常: {str(e)}")
