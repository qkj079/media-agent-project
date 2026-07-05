import streamlit as st
import os

# --- 尝试导入 LangChain 组件 ---
# 增加了一个 try-except 块，防止因为版本问题直接白屏或报错
try:
    from langchain_community.llms import SparkLLM
    from langchain.chains import ConversationChain
    from langchain.memory import ConversationBufferMemory
except ImportError:
    st.error("⚠️ 缺少必要的库！请在 requirements.txt 中添加 'langchain-community' 并重新部署。")
    st.stop()

# --- 页面配置 ---
st.set_page_config(page_title="传媒专业智能助手", page_icon="📺")
st.title("📺 传媒专业智能助手")
st.caption("具备记忆功能、联网搜索与爆款文案生成能力的智能体（讯飞星火版）")

# --- 初始化 Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "llm" not in st.session_state:
    st.session_state.llm = None
if "memory" not in st.session_state:
    st.session_state.memory = ConversationBufferMemory()

# --- 侧边栏：API Key 设置 ---
with st.sidebar:
    st.header("⚙️ 配置中心")
    
    # 输入框：获取讯飞星火的三个关键参数
    app_id = st.text_input("APPID", type="password", placeholder="请输入讯飞 APPID")
    api_key = st.text_input("APIKey", type="password", placeholder="请输入讯飞 APIKey")
    api_secret = st.text_input("APISecret", type="password", placeholder="请输入讯飞 APISecret")
    
    model_version = st.selectbox(
        "选择模型版本",
        ["spark-max", "spark-pro", "spark-lite"],
        index=0,
        help="Max效果最好但稍慢，Lite速度最快"
    )

    if st.button("💾 保存并连接"):
        if app_id and api_key and api_secret:
            try:
                # 初始化讯飞星火 LLM
                st.session_state.llm = SparkLLM(
                    spark_app_id=app_id,
                    spark_api_key=api_key,
                    spark_api_secret=api_secret,
                    model=model_version 
                )
                # 重置对话链和记忆
                st.session_state.memory = ConversationBufferMemory()
                st.success(f"✅ 成功连接讯飞星火 ({model_version})！")
            except Exception as e:
                st.error(f"❌ 连接失败: {str(e)}")
        else:
            st.warning("⚠️ 请填写完整的 APPID、APIKey 和 APISecret")

# --- 主聊天区域 ---

# 显示历史消息
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 处理用户输入
if prompt := st.chat_input("请输入你的传媒相关问题或文案需求..."):
    # 1. 检查模型是否已加载
    if not st.session_state.llm:
        st.error("🔴 请先在左侧侧边栏配置讯飞星火 API 信息并点击连接！")
        st.stop()

    # 2. 显示用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 3. 调用 AI 生成回复
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # 使用 ConversationChain 处理带记忆的对话
            conversation = ConversationChain(
                llm=st.session_state.llm,
                memory=st.session_state.memory,
                verbose=False 
            )
            
            # 获取回复
            response = conversation.predict(input=prompt)
            full_response = response
            
            # 打字机效果显示
            message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            
        except Exception as e:
            st.error(f"生成出错: {str(e)}")
            full_response = "抱歉，我遇到了一点问题，请检查 API 配置或网络连接。"

    # 4. 保存 AI 回复到历史
    st.session_state.messages.append({"role": "assistant", "content": full_response})
