"""数据库：pgvector 存储文档块与向量，支持余弦相似度检索"""
from sqlalchemy import create_engine, text

from . import config

engine = create_engine(config.DATABASE_URL)


def init_db():
    """建扩展、建表、建 HNSW 索引（幂等，可重复执行）"""
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    id SERIAL PRIMARY KEY,
                    doc_name TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding vector(1024)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS chunks_embedding_idx
                ON chunks USING hnsw (embedding vector_cosine_ops)
                """
            )
        )


def _vec_str(embedding: list[float]) -> str:
    """把 Python 列表转成 pgvector 认识的字符串，如 [0.1,0.2,...]"""
    return "[" + ",".join(str(x) for x in embedding) + "]"


def insert_chunks(doc_name: str, chunks: list[str], embeddings: list[list[float]]):
    """文档块 + 向量逐条入库"""
    with engine.begin() as conn:
        for content, emb in zip(chunks, embeddings):
            conn.execute(
                text(
                    "INSERT INTO chunks (doc_name, content, embedding) "
                    "VALUES (:d, :c, :e::vector)"
                ),
                {"d": doc_name, "c": content, "e": _vec_str(emb)},
            )


def search_similar(query_embedding: list[float], top_k: int = 4) -> list[tuple]:
    """余弦相似度检索，返回 [(doc_name, content, similarity)]，按相似度降序"""
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT doc_name, content, 1 - (embedding <=> :q::vector) AS similarity
                FROM chunks
                ORDER BY embedding <=> :q::vector
                LIMIT :k
                """
            ),
            {"q": _vec_str(query_embedding), "k": top_k},
        ).fetchall()
    return [(r.doc_name, r.content, float(r.similarity)) for r in rows]
