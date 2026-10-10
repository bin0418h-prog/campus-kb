"""FastAPI 入口：健康检查 + 流式问答接口"""
import json

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .services import llm

app = FastAPI(title="CampusKB 校园知识库问答系统")


class ChatRequest(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def chat(req: ChatRequest):
    """流式问答：SSE 格式返回。检索功能后续接入，目前 context 为空"""

    async def generate():
        yield "data: " + json.dumps({"event": "start"}, ensure_ascii=False) + "\n\n"
        for token in llm.stream_answer(req.question, []):
            yield "data: " + json.dumps({"event": "token", "text": token}, ensure_ascii=False) + "\n\n"
        yield "data: " + json.dumps({"event": "done"}, ensure_ascii=False) + "\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
