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
# 1. 配置区域 (请填入你的真实 Key)
# ==========================================
# 如果你有 .streamlit/secrets.toml，这里会自动读取；如果没有，请手动填入字符串
APP_ID = st.secrets.get("APP_ID", "你的_APP_ID") 
API_KEY = st.secrets.get("API_KEY", "你的_API_KEY")
API_SECRET = st.secrets.get("API_SECRET", "你的_API_SECRET")

# 讯飞星火大模型地址 (根据你使用的版本调整，这里是 v3.5 通用地址)
SPARK_URL = "wss://spark-api.xf-yun.com/v3.5/chat" 

# ==========================================
# 2. 核心工具函数
# ==========================================

def generate_ws_url():
    """生成带鉴权信息的 WebSocket URL"""
    now = datetime.now()
    date = format_date_time(time.mktime(now.timetuple()))
    
    signature_origin = f"host: spark-api.xf-yun.com\ndate: {date}\nGET /v3.5/chat HTTP/1.1"
    signature_sha = hmac.new(API_SECRET.encode('utf-8'), signature_origin.encode('utf-8'), digestmod=hashlib.sha256).digest()
    signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')
    
    authorization_origin = f'api_key="{API_KEY}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
    
    v = {"authorization": authorization, "date": date, "host": "spark-api.xf-yun.com"}
    url = SPARK_URL + "?" + urlencode(v)
    return url

def on_message(ws, message):
    """WebSocket 收到消息时的处理逻辑"""
    data = json.loads(message)
    code = data['header']['code']
    
    if code != 0:
        # 如果出错，把错误信息存入 session_state
        st.session_state.error_msg = f'请求错误: {code}, {data}'
        ws.close()
    else:
        choices = data["payload"]["choices"]
        status = choices["status"]
        content = choices["text"][0]["content"]
        
        # 将内容追加到 session_state 的列表中
        st.session_state.response_buffer.append(content)
        
        # 如果是最后一段，关闭连接
        if status == 2:
            ws.close()

def on_error(ws, error):
    st.session_state.error_msg = f"连接错误: {error}"

def on_close(ws, close_status_code, close_msg):
    pass # 连接关闭

def on_open(ws):
    """建立连接后发送数据"""
    thread.start_new_thread(run, (ws,))

def run(ws, *args):
    """发送具体的 Prompt 数据"""
    data = json.dumps(gen_params(appid=APP_ID, question=st.session_state.current_question))
    ws.send(data)

def gen_params(appid, question):
    """构造发送给讯飞的 JSON 数据包"""
    data = {
        "header": {
            "app_id": appid,
            "uid": "1234"
        },
        "parameter": {
            "chat": {
                "domain": "generalv3.5", # 对应 v3.5 模型
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
    return data

# ==========================================
# 3. 封装调用函数 (解决 nonlocal 报错的关键)
# ==========================================
def get_spark_response(question):
    """
    这是一个生成器函数。
    它启动 WebSocket，然后不断 yield 出新的文本片段给 Streamlit 显示。
    """
    # 初始化 Session State 中的临时变量
    st.session_state.response_buffer = []
    st.session_state.error_msg = None
    st.session_state.current_question = question
    
    ws_url = generate_ws_url()
    websocket.enableTrace(False)
    
    # 创建 WebSocket 连接
    ws = websocket.WebSocketApp(
        ws_url,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.on_open = on_open
    
    # 在后台线程启动连接
    thread.start_new_thread(ws.run_forever, ({"sslopt": {"cert_reqs": ssl.CERT_NONE}},))
    
    # 循环等待数据返回
    while True:
        # 检查是否有新内容产生
        current_len = len(st.session_state.response_buffer)
        
        # 如果有新内容，yield 出去
        if current_len > 0:
            # 取出最新的内容片段
            new_content = st.session_state.response_buffer.pop(0)
            yield new_content
            
        # 检查是否结束或出错
        if st.session_state.error_msg:
            yield f"\n\n[系统错误]: {st.session_state.error_msg}"
            break
            
        # 简单的超时或结束判断 (实际项目中可根据 status 标志位优化)
        # 这里简单判断：如果 buffer 空了且没有报错，稍微等待一下
        time.sleep(0.1) 
        
        # 注意：由于 WebSocket 是异步的，这里需要一个更严谨的退出机制。
        # 为了简化代码适应 Streamlit，我们假设只要连接断了或者有明显结束标志就停。
        # 在实际运行中，当 status=2 时 ws 会 close，我们需要检测这一点。
        # 但由于我们在另一个线程 run_forever，主线程很难直接知道 ws 状态。
        # **改进方案**：利用一个标记位。
        if not ws.keep_running and len(st.session_state.response_buffer) == 0:
             break


# ==========================================
# 4. Streamlit 界面逻辑
# ==========================================
st.set_page_config(page_title="传媒专业智能助手", page_icon="📺")
st.title("📺 传媒专业智能助手")
st.caption("基于讯飞星火大模型，专注传媒领域问答与创意生成")

# 初始化聊天历史
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

    # 2. 调用 AI 并显示回复
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # 使用生成器获取流式回复
        for chunk in get_spark_response(prompt):
            full_response += chunk
            message_placeholder.markdown(full_response + "▌")
        
        message_placeholder.markdown(full_response)
        
    # 3. 保存 AI 回复到历史
    st.session_state.messages.append({"role": "assistant", "content": full_response})
