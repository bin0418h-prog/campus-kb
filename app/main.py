"""FastAPI 入口：健康检查 + 文档上传入库 + 流式问答"""
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Header, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import text

from .db import engine as pg_engine

from . import config
from .db import init_db, insert_chunks
from .db_mysql import get_history, init_db as init_mysql, save_conversation
from .services import embedding, llm, parser, retriever, splitter

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # pgvector：建扩展/建表/建索引
    init_mysql()  # MySQL：建对话历史表
    retriever.build_index()  # 把库里全部文档块加载进内存，构建 BM25 索引
    yield


app = FastAPI(title="CampusKB 校园知识库问答系统", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def index():
    """前端页面"""
    return FileResponse("static/index.html")


class ChatRequest(BaseModel):
    question: str


def sse(obj: dict) -> str:
    """把一个事件包装成 SSE 标准格式：data: {json}\\n\\n"""
    return "data: " + json.dumps(obj, ensure_ascii=False) + "\n\n"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload(file: UploadFile, x_admin_password: str = Header("")):
    """上传文档（管理员鉴权）→ 解析 → 分块 → 向量化 → 入库。
    请求头 X-Admin-Password 需与配置一致，防止匿名上传污染知识库"""
    if x_admin_password != config.ADMIN_PASSWORD:
        return JSONResponse(status_code=401, content={"detail": "管理员密码错误"})

    path = UPLOAD_DIR / file.filename
    path.write_bytes(await file.read())

    text = parser.parse_file(path)  # 1. PDF/Word/MD → 纯文本
    chunks = splitter.split_text(text)  # 2. 结构感知分块
    vectors = embedding.embed_texts(chunks)  # 3. bge-m3 向量化
    insert_chunks(file.filename, chunks, vectors)  # 4. 写入 pgvector

    return {"doc": file.filename, "chars": len(text), "chunks": len(chunks)}


@app.post("/chat")
def chat(req: ChatRequest):
    """流式问答：混合检索 → 拒答判断 → 大模型生成（SSE），结束后存对话历史"""
    hits, max_sim = retriever.hybrid_search(req.question, top_k=4)

    async def generate():
        answer_parts = []
        docs = sorted({h[0] for h in hits}) if hits else []
        yield sse({"event": "start"})
        if not hits or max_sim < config.REJECT_THRESHOLD:
            # 拒答：向量路最高相似度也低于阈值，说明知识库里没有答案，不调大模型
            answer_parts.append("资料中没有相关信息。")
            yield sse({"event": "token", "text": answer_parts[0]})
        else:
            yield sse({"event": "sources", "data": [{"doc": d} for d in docs]})
            for token in llm.stream_answer(req.question, [(h[0], h[1]) for h in hits]):
                answer_parts.append(token)
                yield sse({"event": "token", "text": token})
        save_conversation(req.question, "".join(answer_parts), docs)  # 落库：系统有记忆
        yield sse({"event": "done"})

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/history")
def history(limit: int = 20):
    """最近的对话记录"""
    return {"items": get_history(limit)}


@app.get("/documents")
def documents():
    """知识库文档清单（用于前端展示档案数量）"""
    with pg_engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT doc_name, COUNT(*) AS chunks FROM chunks "
                "GROUP BY doc_name ORDER BY doc_name"
            )
        ).fetchall()
    return {"items": [{"doc": r.doc_name, "chunks": r.chunks} for r in rows]}
