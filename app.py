import streamlit as st
from media_agent import SparkLiteApi  # 这里必须和你另一个文件名完全一致
import time

# --- 页面配置 ---
st.set_page_config(page_title="传媒智囊团 AI", page_icon="🎓", layout="wide")
st.title("🎓 传媒专业智能助手")
st.caption("基于讯飞星火大模型 | 智能对话与媒体分析")

# --- 侧边栏配置 (用于输入密钥) ---
with st.sidebar:
    st.header("⚙️ 配置中心")
    app_id = st.text_input("APP_ID", type="password")
    api_key = st.text_input("API_KEY", type="password")
    api_secret = st.text_input("API_SECRET", type="password")
    
    if st.button("清除对话历史"):
        st.session_state.messages = []
        st.rerun()

# --- 初始化会话状态 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 显示历史消息 ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 处理用户输入 ---
if prompt := st.chat_input("请输入你的问题，例如：帮我写一个关于AI的新闻标题..."):
    # 1. 检查密钥是否填写
    if not app_id or not api_key or not api_secret:
        st.error("⚠️ 请先在左侧侧边栏填写讯飞星火的 APP_ID, API_KEY 和 API_SECRET！")
        st.stop()

    # 2. 显示用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 3. 调用 AI (使用你的 media_agent.py)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # 实例化你的类
            spark_api = SparkLiteApi(app_id, api_key, api_secret)
            
            # 获取回答 (假设你的 SparkLiteApi 有一个叫 chat 的方法，如果没有，请看下面的提示)
            # 注意：如果你之前的代码里方法名不叫 chat，请改成对应的方法名
            response_text = spark_api.chat(prompt) 
            
            # 模拟打字机效果显示
            for chunk in response_text.split(): 
                full_response += chunk + " "
                time.sleep(0.05)
                message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            
        except Exception as e:
            st.error(f"发生错误: {str(e)}")
            full_response = "抱歉，连接大脑时出错了，请检查密钥或网络。"

    # 4. 保存助手回复
    st.session_state.messages.append({"role": "assistant", "content": full_response})
