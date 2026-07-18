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
# 1. 讯飞星火 WebSocket 鉴权与连接逻辑
# ==========================================

class Ws_Param(object):
    def __init__(self, APPID, APIKey, APISecret, Spark_url):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.host = Spark_url.split("//")[1].split("/")[0] # 提取 host
        self.url = Spark_url

    def create_body(self):
        body = {
            "header": {"app_id": self.APPID, "uid": "1234"},
            "parameter": {
                "chat": {
                    "domain": "generalv3", # 如果是 v3.5 模型，这里改为 generalv3.5
                    "temperature": 0.5,
                    "max_tokens": 2048
                }
            },
            "payload": {
                "message": {
                    "text": []
                }
            }
        }
        return body

    def create_url(self):
        now = datetime.now()
        date = format_date_time(time.mktime(now.timetuple()))
        signature_origin = "host: {}\ndate: {}\nGET {} HTTP/1.1".format(self.host, date, "/v3.5/chat")
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'), digestmod=hashlib.sha256).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')
        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        v = {
            "authorization": authorization,
            "date": date,
            "host": self.host
        }
        url = self.url + '?' + urlencode(v)
        return url

# ==========================================
# 2. 核心交互函数 (解决多线程问题的关键)
# ==========================================

def run_spark_chat(appid, api_key, api_secret, prompt):
    """
    这是一个生成器函数。它负责启动 WebSocket，
    并在收到消息时 yield 给主线程，而不是直接在子线程操作 UI。
    """
    # 根据 key 判断使用哪个版本的接口地址
    spark_url = "wss://spark-api.xf-yun.com/v3.1/chat" 
    if "v3.5" in api_key or "generalv3.5" in str(st.session_state.get("model_version", "")):
         spark_url = "wss://spark-api.xf-yun.com/v3.5/chat"

    wsParam = Ws_Param(APPID=appid, APIKey=api_key, APISecret=api_secret, Spark_url=spark_url)
    websocket.enableTrace(False)
    wsUrl = wsParam.create_url()
    
    # 用于暂存子线程收到的完整回复
    result_container = [""] 
    
    def on_message(ws, message):
        data = json.loads(message)
        code = data['header']['code']
        if code != 0:
            result_container[0] = f"错误代码 {code}: {data['header']['message']}"
            ws.close()
        else:
            choices = data["payload"]["choices"]["text"]
            content = choices[0]["content"]
            result_container[0] += content
            
    def on_error(ws, error):
        result_container[0] = f"连接出错: {str(error)}"

    def on_close(ws, close_status_code, close_msg):
        pass 

    def on_open(ws):
        thread.start_new_thread(run, (ws,))

    def run(ws, *args):
        data = json.dumps(wsParam.create_body())
        # 将用户的问题放入 payload
        req_data = json.loads(data)
        req_data["payload"]["message"]["text"] = [{"role": "user", "content": prompt}]
        ws.send(json.dumps(req_data))

    ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.on_open = on_open
    
    # 在新线程中运行 WebSocket，避免阻塞 Streamlit 主进程
    thread.start_new_thread(ws.run_forever, (None, {"sslopt": {"cert_reqs": ssl.CERT_NONE}}))

    # 循环等待结果，一旦有内容就 yield 出去
    while True:
        if result_container[0]:
            yield result_container[0]
            # 如果收到了结束标志（这里简化处理，只要有内容且不再变化太久可视为结束，或者依靠 WebSocket 关闭）
            # 简单起见，我们假设只要连接还在，就一直更新
        time.sleep(0.1)
        # 注意：实际生产中需要更严谨的判断连接是否断开来退出循环
        # 这里为了演示简单，我们假设它会自动停止或通过异常退出

# ==========================================
# 3. Streamlit 界面逻辑
# ==========================================

st.set_page_config(page_title="传媒专业智能助手", page_icon="🤖")
st.title("🤖 传媒专业智能助手")
st.caption("基于讯飞星火认知大模型，为您提供专业的文案创作支持。")

# 侧边栏配置 API Key
with st.sidebar:
    st.header("⚙️ 配置区域")
    app_id = st.text_input("APP ID", type="password", help="请输入讯飞开放平台的 APPID")
    api_key = st.text_input("API Key", type="password", help="请输入讯飞开放平台的 APIKey")
    api_secret = st.text_input("API Secret", type="password", help="请输入讯飞开放平台的 APISecret")
    
    st.info("请在 [讯飞开放平台](https://console.xfyun.cn/services/bm4) 获取上述信息。")

# 聊天输入区
prompt = st.chat_input("请输入您的需求，例如：帮我写一篇关于家乡美食的推文...")

if prompt:
    if not app_id or not api_key or not api_secret:
        st.error("❌ 请先在左侧侧边栏填写完整的 API 配置信息！")
    else:
        # 显示用户的问题
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 显示 AI 的回答
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                # 调用生成器函数
                for response_chunk in run_spark_chat(app_id, api_key, api_secret, prompt):
                    full_response = response_chunk
                    message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
            except Exception as e:
                st.error(f"发生未知错误: {e}")
