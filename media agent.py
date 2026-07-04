import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.tools import Tool
from langchain.memory import ConversationBufferMemory
import requests 

# ==========================================
# 1. 设置页面配置 (网页版智能体)
# ==========================================
st.set_page_config(page_title="传媒智囊团 AI", page_icon="📺")
st.title("📺 传媒专业智能助手")
st.caption("具备记忆功能、联网搜索与爆款文案生成能力的智能体")

# ==========================================
# 2. 定义自定义工具 (Custom Tools)
# ==========================================

# 工具1：模拟联网搜索热点
def search_media_trends(query: str) -> str:
    """当用户询问最近的新闻热点、社交媒体趋势或特定事件背景时使用此工具。"""
    # 模拟返回结果，实际可对接 SerpAPI
    return f"根据最新检索，关于'{query}'的热点如下：\n1. 微博热搜榜第3位讨论激烈。\n2. 知乎相关话题下高赞回答倾向于理性分析。\n3. 抖音相关视频播放量已破亿。"

# 工具2：爆款标题生成器
def generate_viral_titles(topic: str) -> str:
    """当用户需要为文章、视频生成吸引人的标题时使用。"""
    llm_temp = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.8) 
    prompt = f"请为传媒专业的学生生成5个关于'{topic}'的爆款标题，风格涵盖震惊体、干货体和情感共鸣体。"
    return llm_temp.predict(prompt)

tools = [
    Tool(
        name="MediaSearch",
        func=search_media_trends,
        description="用于搜索最新的媒体热点和事件背景。"
    ),
    Tool(
        name="TitleGenerator",
        func=generate_viral_titles,
        description="用于生成小红书、抖音或公众号的爆款标题。"
    )
]

# ==========================================
# 3. 初始化智能体与记忆 (Memory & Agent)
# ==========================================

api_key = st.sidebar.text_input("请输入你的 OpenAI API Key", type="password")

if api_key:
    llm = ChatOpenAI(openai_api_key=api_key, model_name="gpt-3.5-turbo", temperature=0.7)
    
    # 初始化记忆
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    # 初始化 Agent
    agent = initialize_agent(
        tools, 
        llm, 
        agent="chat-conversational-react-description", 
        verbose=True,
        memory=memory,
        handle_parsing_errors=True
    )

    # ==========================================
    # 4. 网页交互逻辑
    # ==========================================
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("你想聊点什么？比如：帮我查一下最近AI视频的热点"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("正在思考并调用工具..."):
                try:
                    response = agent.run(input=prompt)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"出错了：{e}")
else:
    st.warning("请在左侧输入 API Key 以启动智能体。")
