"""大模型生成：调用 DeepSeek API，流式返回回答"""
from openai import OpenAI

from .. import config

_client = OpenAI(api_key=config.DEEPSEEK_API_KEY, base_url=config.DEEPSEEK_BASE_URL)

# 系统提示词：约束模型只依据资料回答，资料没有就直说，防止幻觉
SYSTEM_PROMPT = (
    "你是校园知识库助手。只依据用户消息中提供的资料回答；"
    "资料中没有答案时，直接回答\"资料中没有相关信息\"，不要编造。"
)


def build_messages(question: str, context_chunks: list[tuple[str, str]]) -> list[dict]:
    """把检索到的资料片段拼进提示词，连同问题一起发给模型。
    context_chunks 每一项是 (文档名, 内容)，文档名用于引用溯源"""
    context = "\n\n".join(
        f"[资料{i + 1} · 来自《{doc}》] {text}" for i, (doc, text) in enumerate(context_chunks)
    )
    user_content = f"参考资料：\n{context}\n\n问题：{question}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def stream_answer(question: str, context_chunks: list[tuple[str, str]]):
    """逐 token 生成回答。返回生成器，供 SSE 接口逐个转发给前端"""
    response = _client.chat.completions.create(
        model=config.DEEPSEEK_MODEL,
        messages=build_messages(question, context_chunks),
        stream=True,
        temperature=0.3,  # 知识问答用低温度，输出更稳定
    )
    for chunk in response:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
