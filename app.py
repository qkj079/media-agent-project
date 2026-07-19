import streamlit as st

# ==========================================
# 尝试导入你的 AI 模块
# ==========================================
try:
    # 这里假设你的文件名叫 media_agent.py，类名叫 SparkApi
    from media_agent import SparkApi 
    AGENT_READY = True
except ImportError as e:
    AGENT_READY = False
    ERROR_MSG = str(e)

# ==========================================
# 1. 页面配置
# ==========================================
st.set_page_config(page_title="传媒专业智能助手", page_icon="🎓")

st.title("🎓 传媒专业智能助手")
st.caption("基于讯飞星火大模型 | 智能对话与媒体分析")

# ==========================================
# 2. 初始化会话状态
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []

# ==========================================
# 3. 显示历史消息
# ==========================================
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ==========================================
# 4. 聊天输入框
# ==========================================
if prompt := st.chat_input("请输入你的问题..."):
    
    # --- 显示用户的问题 ---
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- 处理 AI 回复 ---
    with st.chat_message("assistant"):
        if not AGENT_READY:
            # 如果导入失败，直接显示错误原因，方便调试
            st.error(f"⚠️ **系统启动失败**\n\n无法加载 AI 模块，请检查 `media_agent.py` 是否存在。\n\n错误详情: `{ERROR_MSG}`")
        else:
            try:
                # 实例化 AI (确保你的 media_agent.py 里有这个类)
                # 注意：如果你的 SparkApi 初始化需要 key/secret，请在这里传入，或者在 media_agent.py 里写死
                ai_bot = SparkApi() 
                
                with st.spinner("AI 正在思考中..."):
                    # 调用 chat 方法
                    response = ai_bot.chat(prompt)
                    
                    if response:
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    else:
                        st.warning("AI 没有返回内容，可能是网络波动或 Key 配置错误。")
                        
            except Exception as e:
                st.error(f"❌ **运行出错**: {str(e)}")
