import streamlit as st
from media_agent import SparkApi # 确保这里导入的是你刚才修改过的文件名

# ==========================================
# 1. 页面基础配置
# ==========================================
st.set_page_config(page_title="传媒专业智能助手", page_icon="🎓", layout="wide")

# 自定义 CSS 样式（让界面更好看）
st.markdown("""
    <style>
    .main { padding: 2rem; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; }
    .chat-container { background-color: #f9f9f9; padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0; min-height: 300px;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 初始化 Session State (记忆功能)
# ==========================================
if 'history' not in st.session_state:
    st.session_state.history = [] # 存放聊天记录
if 'agent' not in st.session_state:
    # 初始化 AI 助手实例 (只初始化一次，避免重复连接)
    try:
        st.session_state.agent = SparkApi() 
    except Exception as e:
        st.error(f"初始化 AI 失败，请检查 media_agent.py 配置: {e}")

# ==========================================
# 3. 侧边栏与标题
# ==========================================
with st.sidebar:
    st.title("🛠️ 功能控制台")
    st.info("当前模型：**Spark Lite**\n状态：🟢 在线")
    
    # 清空历史按钮
    if st.button("🗑️ 清空对话记录"):
        st.session_state.history = []
        st.rerun()

st.title("🎓 传媒专业智能助手")
st.caption("基于讯飞星火大模型 | 智能对话与媒体分析")

# ==========================================
# 4. 聊天显示区域 (核心修改部分)
# ==========================================
# 创建一个容器来显示聊天记录
chat_container = st.container()

with chat_container:
    # 遍历历史记录并显示
    for message in st.session_state.history:
        role = message["role"]
        content = message["content"]
        
        with st.chat_message(role):
            st.markdown(content)

# ==========================================
# 5. 输入与交互区域
# ==========================================
# 使用 columns 布局让按钮更整齐
col1, col2 = st.columns([3, 1])

with col1:
    user_input = st.chat_input("请输入你的问题，例如：帮我写一个关于AI的新闻标题...")

# 处理发送逻辑
if user_input:
    # 1. 先把用户的话显示出来
    st.session_state.history.append({"role": "user", "content": user_input})
    
    # 2. 显示 AI 正在思考的占位符
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("🤖 **AI 正在思考中...**")
        
        try:
            # 3. 调用 AI (调用我们在 media_agent.py 写的 chat 函数)
            agent = st.session_state.agent
            response = agent.chat(user_input)
            
            # 4. 更新占位符为真实结果
            if response:
                placeholder.markdown(response)
                # 存入历史记录
                st.session_state.history.append({"role": "assistant", "content": response})
            else:
                placeholder.markdown("⚠️ **未收到回复** (可能是网络波动或 API 限制，请重试)")
                
        except Exception as e:
            placeholder.error(f"❌ **出错了**: {str(e)}")
    
    # 强制刷新页面以显示最新记录
    st.rerun()
