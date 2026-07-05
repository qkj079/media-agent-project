# --- 修改开始 ---
import os
from langchain_community.llms import SparkLLM 
# 注意：如果你的 langchain 版本较老，可能需要用 from langchain.llms import SparkLLM

def get_llm():
    """根据环境变量自动选择模型"""
    
    # 1. 尝试获取讯飞星火的三个必要参数
    spark_app_id = os.environ.get("SPARK_APP_ID")
    spark_api_key = os.environ.get("SPARK_API_KEY")
    spark_api_secret = os.environ.get("SPARK_API_SECRET")

    # 2. 如果三个参数都存在，则初始化讯飞星火模型
    if spark_app_id and spark_api_key and spark_api_secret:
        print("✅ 检测到讯飞星火配置，正在初始化 Spark-Max...")
        return SparkLLM(
            spark_app_id=spark_app_id,
            spark_api_key=spark_api_key,
            spark_api_secret=spark_api_secret,
            model_name="generalv3.5" # 推荐使用 v3.5 (对应 Max)，速度快且聪明
        )
    
    # 3. 如果没有讯飞配置，报错提示（防止像之前那样报奇怪的 Pydantic 错误）
    else:
        raise ValueError("❌ 未检测到有效的讯飞星火 API 配置，请检查 Secrets 设置。")

# 调用函数获取模型实例
llm = get_llm()
# --- 修改结束 ---
