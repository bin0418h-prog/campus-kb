"""全局配置：从 .env 文件读取密钥与连接信息"""
import os

from dotenv import load_dotenv

load_dotenv()

# DeepSeek 生成模型
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# Embedding 模型（硅基流动）
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", "")
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", "https://api.siliconflow.cn/v1")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")

# PostgreSQL + pgvector
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/campuskb")

# 拒答阈值：检索最高相似度低于它时直接拒答，不调用大模型（防幻觉）
REJECT_THRESHOLD = float(os.getenv("REJECT_THRESHOLD", "0.4"))
