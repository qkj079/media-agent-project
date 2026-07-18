import streamlit as st
from media_agent import SparkLiteApi  # 导入你之前写好的工具类

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

# --- 3. 聊天界面逻辑 ---
# 显示历史消息
for message in st.session_state.get("messages", []):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 处理用户输入
if prompt := st.chat_input("请输入你想问的问题..."):
    # 显示用户消息
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 调用 AI 回答
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # 获取回答 (假设你的 media_agent.py 里有 get_response 方法)
        # 如果之前的代码里方法名不一样，请在这里修改
        try:
            response = st.session_state.spark_api.get_response(prompt)
            full_response = str(response) # 确保是字符串
            
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"出错了: {e}")
