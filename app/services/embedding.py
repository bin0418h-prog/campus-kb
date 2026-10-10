"""Embedding：把文本转成向量（硅基流动 BAAI/bge-m3，中文效果好）"""
from openai import OpenAI

from .. import config

_client = OpenAI(api_key=config.EMBEDDING_API_KEY, base_url=config.EMBEDDING_BASE_URL)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """批量生成向量，返回与输入等长的向量列表"""
    resp = _client.embeddings.create(model=config.EMBEDDING_MODEL, input=texts)
    return [d.embedding for d in resp.data]
