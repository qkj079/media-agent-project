# 📺 传媒智囊团 AI (Media Agent Project)

这是一个基于 Streamlit 和 LangChain 构建的智能媒体助手应用。它具备对话记忆能力，能够模拟联网搜索热点，并辅助生成爆款文案标题，专为传媒专业学生和内容创作者设计。

## ✨ 核心功能

- **智能对话记忆**：基于 LangChain 的 ConversationBufferMemory，能够记住上下文语境，进行多轮流畅对话。
- **模拟热点搜索**：内置 `MediaSearch` 工具，可模拟检索微博、知乎、抖音等平台的实时热点趋势。
- **爆款标题生成**：内置 `TitleGenerator` 工具，利用大模型为特定话题生成震惊体、干货体等多种风格的吸睛标题。
- **交互式界面**：使用 Streamlit 构建，支持侧边栏配置 API Key，聊天窗口实时流式响应。

## 🚀 如何运行

### 1. 环境准备
确保已安装 Python 3.8+，然后克隆本仓库并安装依赖：

```bash
git clone https://github.com/qkj079/media-agent-project.git
cd media-agent-project
pip install -r requirements.txt