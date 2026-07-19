import streamlit as st

# ==========================================
# 导入 AI 模块
# ==========================================
try:
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
            st.error(f"⚠️ **系统启动失败**\n\n无法加载 AI 模块。\n\n错误详情: `{ERROR_MSG}`")
        else:
            try:
                ai_bot = SparkApi() 
                
                with st.spinner("AI 正在思考中..."):
                    response = ai_bot.chat(prompt)
                    
                    # 判断是否有返回值
                    if response and len(response.strip()) > 0:
                        # 如果返回的是错误提示（包含特定关键词），用 error 显示
                        if "错误" in response or "Exception" in response or "error" in response:
                            st.error(response)
                        else:
                            st.markdown(response)
                            st.session_state.messages.append({"role": "assistant", "content": response})
                    else:
                        st.warning("⚠️ AI 返回了空内容。请检查 `media_agent.py` 中的 Key 是否正确填写。")
                        
            except Exception as e:
                st.error(f"❌ **程序运行出错**: {str(e)}")
