import streamlit as st
import hashlib
import base64
import hmac
import json
import websocket
import _thread as thread
import time
from datetime import datetime
from wsgiref.handlers import format_date_time
from urllib.parse import urlencode
import ssl

# ==========================================
# 1. 配置区域 (请填入你的真实 Key)
# ==========================================
# 如果你有 .streamlit/secrets.toml，这里会自动读取；如果没有，请手动填入字符串
APP_ID = st.secrets.get("APP_ID", "你的_APP_ID") 
API_KEY = st.secrets.get("API_KEY", "你的_API_KEY")
API_SECRET = st.secrets.get("API_SECRET", "你的_API_SECRET")

# 讯飞星火大模型地址 (根据你使用的版本调整，这里是 v3.5 通用地址)
SPARK_URL = "wss://spark-api.xf-yun.com/v3.5/chat" 

# ==========================================
# 2. 核心工具函数
# ==========================================

def generate_ws_url():
    """生成带鉴权信息的 WebSocket URL"""
    now = datetime.now()
    date = format_date_time(time.mktime(now.timetuple()))
    
    signature_origin = f"host: spark-api.xf-y
