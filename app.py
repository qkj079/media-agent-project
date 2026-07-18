import streamlit as st
from media_agent import SparkLiteApi  # 导入刚才创建的类

# --- 1. 页面设置 ---
st.set_page_config(page_title="传媒专业智能助手", page_icon="🎓")
st.title("🎓 传媒专业智能助手")
st.caption("基于讯飞星火 Lite 模型 | 安全密钥已连接")

# --- 2. 初始化 API (从 Secrets 读取密钥) ---
if "spark_api" not in st.session_state:
    try:
        # 这里会自动读取你在网页 Secrets 里填的那三个值
        app_id = st.secrets["SPARK_APP_ID"]
        api_key = st.secrets["SPARK_API_KEY"]
        api_secret = st.secrets["SPARK_API_SECRET"]
        
        # 创建 API 对象
        st.session_state.spark_api = SparkLiteApi(app_id, api_key, api_secret)
        st.success("✅ 系统初始化成功，可以开始提问了！")
    except Exception as e:
        st.error(f"❌ 初始化失败，请检查 Secrets 配置: {e}")
        st.stop()

# --- 3. 聊天界面逻辑 ---
# 初始化聊天记录
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示历史消息
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 处理用户输入
if prompt := st.chat_input("请输入你的问题..."):
    # 显示用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 获取 AI 回复
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # 调用后端 API
        with st.spinner("正在思考中..."):
            response = st.session_state.spark_api.ask(prompt)
            full_response = response
        
        message_placeholder.markdown(full_response)
    
    # 保存 AI 回复到历史
    st.session_state.messages.append({"role": "assistant", "content": full_response})
