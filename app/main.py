"""FastAPI 入口：健康检查 + 文档上传入库 + 流式问答"""
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from . import config
from .db import init_db, insert_chunks
from .services import embedding, llm, parser, retriever, splitter

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # 启动时建扩展/建表/建索引
    retriever.build_index()  # 把库里全部文档块加载进内存，构建 BM25 索引
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
    """流式问答：混合检索 → 拒答判断 → 大模型生成（SSE）"""
    hits, max_sim = retriever.hybrid_search(req.question, top_k=4)

    async def generate():
        yield sse({"event": "start"})
        if not hits or max_sim < config.REJECT_THRESHOLD:
            # 拒答：向量路最高相似度也低于阈值，说明知识库里没有答案，不调大模型
            yield sse({"event": "token", "text": "资料中没有相关信息。"})
        else:
            docs = sorted({h[0] for h in hits})  # 引用溯源：答案来自哪些文档
            yield sse({"event": "sources", "data": [{"doc": d} for d in docs]})
            for token in llm.stream_answer(req.question, [(h[0], h[1]) for h in hits]):
                yield sse({"event": "token", "text": token})
        yield sse({"event": "done"})

    return StreamingResponse(generate(), media_type="text/event-stream")
