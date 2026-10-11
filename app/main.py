"""FastAPI 入口：健康检查 + 文档上传入库 + 流式问答"""
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from . import config
from .db import init_db, insert_chunks, search_similar
from .services import embedding, llm, parser, splitter

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # 启动时建扩展/建表/建索引
    yield


app = FastAPI(title="CampusKB 校园知识库问答系统", lifespan=lifespan)


class ChatRequest(BaseModel):
    question: str


def sse(obj: dict) -> str:
    """把一个事件包装成 SSE 标准格式：data: {json}\\n\\n"""
    return "data: " + json.dumps(obj, ensure_ascii=False) + "\n\n"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload(file: UploadFile):
    """上传文档 → 解析 → 分块 → 向量化 → 入库，四步一气呵成"""
    path = UPLOAD_DIR / file.filename
    path.write_bytes(await file.read())

    text = parser.parse_file(path)  # 1. PDF/Word/MD → 纯文本
    chunks = splitter.split_text(text)  # 2. 结构感知分块
    vectors = embedding.embed_texts(chunks)  # 3. bge-m3 向量化
    insert_chunks(file.filename, chunks, vectors)  # 4. 写入 pgvector

    return {"doc": file.filename, "chars": len(text), "chunks": len(chunks)}


@app.post("/chat")
def chat(req: ChatRequest):
    """流式问答：问题向量化 → 检索 → 拒答判断 → 大模型生成（SSE）"""
    query_vec = embedding.embed_texts([req.question])[0]
    hits = search_similar(query_vec, top_k=4)  # [(doc_name, content, similarity)]

    async def generate():
        yield sse({"event": "start"})
        if not hits or hits[0][2] < config.REJECT_THRESHOLD:
            # 拒答：最相关的内容相似度也过低，说明知识库里没有答案，不调大模型
            yield sse({"event": "token", "text": "资料中没有相关信息。"})
        else:
            sources = [{"doc": h[0], "similarity": round(h[2], 3)} for h in hits]
            yield sse({"event": "sources", "data": sources})
            for token in llm.stream_answer(req.question, [(h[0], h[1]) for h in hits]):
                yield sse({"event": "token", "text": token})
        yield sse({"event": "done"})

    return StreamingResponse(generate(), media_type="text/event-stream")
