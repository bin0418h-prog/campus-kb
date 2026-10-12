"""MySQL：对话历史持久化"""
from sqlalchemy import create_engine, text

from . import config

engine = create_engine(config.MYSQL_URL)


def init_db():
    """建对话表（幂等）"""
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    sources TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )


def save_conversation(question: str, answer: str, sources: list[str]):
    """保存一轮问答"""
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO conversations (question, answer, sources) "
                "VALUES (:q, :a, :s)"
            ),
            {"q": question, "a": answer, "s": ",".join(sources)},
        )


def get_history(limit: int = 20) -> list[dict]:
    """最近的 N 轮对话"""
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT question, answer, sources, created_at FROM conversations "
                "ORDER BY id DESC LIMIT :n"
            ),
            {"n": limit},
        ).fetchall()
    return [
        {
            "question": r.question,
            "answer": r.answer,
            "sources": r.sources,
            "created_at": str(r.created_at),
        }
        for r in rows
    ]
