import streamlit as st
import os

# 1. 页面配置必须放在最前面
st.set_page_config(page_title="传媒专业智能助手", page_icon="📺")

# 2. 尝试导入 LangChain
try:
    from langchain_community.llms import SparkLLM
    from langchain.chains import ConversationChain
    from langchain.memory import ConversationBufferMemory
    LIBS_LOADED = True
except ImportError as e:
    LIBS_LOADED = False
    IMPORT_ERROR_MSG = str(e)

# --- 页面标题与配置 ---
st.title("📺 传媒专业智能助手")
st.caption("具备记忆功能、联网搜索与爆款文案生成能力的智能体（讯飞星火版）")

# 检查库是否加载成功
if not LIBS_LOADED:
    st.error("⚠️ 环境配置错误：缺少必要的库！")
    st.code(f"错误详情: {IMPORT_ERROR_MSG}")
    st.info("请在终端运行以下命令安装依赖：\npip install langchain langchain-community streamlit")
    st.stop()

# --- Domain 与 URL 映射表 ---
MODEL_CONFIG = {
    "generalv3.5": {
        "label": "Spark Max（效果最好，稍慢）",
        "url": "wss://spark-api.xf-yun.com/v3.5/chat",
    },
    "generalv3": {
        "label": "Spark Pro（均衡）",
        "url": "wss://spark-api.xf-yun.com/v3.1/chat",
    },
    "general": {
        "label": "Spark Lite（速度最快，免费）",
        "url": "wss://spark-api.xf-yun.com/v1.1/chat",
    },
}

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

    app_id = st.text_input("APPID", type="password", placeholder="请输入讯飞 APPID")
    api_key = st.text_input("APIKey", type="password", placeholder="请输入讯飞 APIKey")
    api_secret = st.text_input("APISecret", type="password", placeholder="请输入讯飞 APISecret")

    # 下拉菜单：显示友好名称，返回 domain 值
    model_domain = st.selectbox(
        "选择模型版本",
        options=list(MODEL_CONFIG.keys()),
        format_func=lambda x: MODEL_CONFIG[x]["label"],
        index=0,
        help="Max效果最好但稍慢，Lite速度最快且免费"
    )

    if st.button("💾 保存并连接"):
        if app_id and api_key and api_secret:
            try:
                # 根据选择的 domain 获取对应的 URL
                api_url = MODEL_CONFIG[model_domain]["url"]

                st.session_state.llm = SparkLLM(
                    spark_app_id=app_id,
                    spark_api_key=api_key,
                    spark_api_secret=api_secret,
                    spark_api_url=api_url,
                    spark_llm_domain=model_domain,
                )
                st.session_state.memory = ConversationBufferMemory()
                st.success(f"✅ 成功连接讯飞星火（{MODEL_CONFIG[model_domain]['label']}）！")
            except Exception as e:
                st.error(f"❌ 连接失败: {str(e)}")
        else:
            st.warning("⚠️ 请填写完整的 APPID、APIKey 和 APISecret")

# --- 主聊天区域 ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("请输入你的传媒相关问题或文案需求..."):
    if not st.session_state.llm:
        st.error("🔴 请先在左侧侧边栏配置讯飞星火 API 信息并点击「保存并连接」！")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            conversation = ConversationChain(
                llm=st.session_state.llm,
                memory=st.session_state.memory,
                verbose=False,
            )

            response = conversation.predict(input=prompt)
            full_response = response

            message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)

        except Exception as e:
            st.error(f"生成出错: {str(e)}")
            full_response = "抱歉，我遇到了一点问题，请检查 API 配置或网络连接。"

    st.session_state.messages.append({"role": "assistant", "content": full_response})
