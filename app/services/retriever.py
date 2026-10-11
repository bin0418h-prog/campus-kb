"""混合检索：向量 + BM25 两路召回，RRF 倒数排名融合"""
from collections import defaultdict

from .. import db
from ..services import bm25, embedding

bm25_index: bm25.BM25 | None = None


def build_index():
    """启动时把库里全部文档块加载进内存，构建 BM25 索引"""
    global bm25_index
    chunks = db.get_all_chunks()  # [(doc_name, content)]
    bm25_index = bm25.BM25(chunks) if chunks else None


def rrf_merge(ranked_lists: list[list[tuple]], k: int = 60) -> list[tuple]:
    """RRF（倒数排名融合）：按名次计分求和，不依赖两路分数尺度。
    RRF 分数 = Σ 1/(k + rank + 1)，rank 从 0 开始"""
    scores = defaultdict(float)
    docs = {}
    for lst in ranked_lists:
        for rank, item in enumerate(lst):
            key = (item[0], item[1])  # (doc_name, content) 作唯一键
            docs[key] = item
            scores[key] += 1.0 / (k + rank + 1)
    merged = sorted(scores.items(), key=lambda x: -x[1])
    return [docs[key] for key, _ in merged]


def hybrid_search(query: str, top_k: int = 4) -> tuple[list[tuple], float]:
    """两路召回 → RRF 融合。返回 (融合结果, 向量路最高相似度)
    向量路最高相似度用于拒答阈值判断"""
    query_vec = embedding.embed_texts([query])[0]
    vec_hits = db.search_similar(query_vec, top_k=top_k)  # [(doc, content, sim)]
    max_sim = vec_hits[0][2] if vec_hits else 0.0

    bm_hits = bm25_index.search(query, top_k=top_k) if bm25_index else []

    merged = rrf_merge([vec_hits, bm_hits])
    return merged[:top_k], max_sim
