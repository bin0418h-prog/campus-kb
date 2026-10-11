"""BM25 关键词检索：jieba 分词 + 倒排统计，与向量检索互补。

向量检索擅长"意思相近"（同义词、改写），BM25 擅长"字面精确"
（专有名词、课程号、条款编号），两路召回再用 RRF 融合。
"""
import math
from collections import defaultdict

import jieba


class BM25:
    """经典 BM25 算法：按词频(TF)与逆文档频率(IDF)给文档打分"""

    def __init__(self, chunks: list[tuple[str, str]]):
        self.chunks = chunks  # [(doc_name, content)]
        self.docs = [jieba.lcut(content) for _, content in chunks]
        self.n_docs = len(chunks)
        self.avg_len = sum(len(d) for d in self.docs) / max(self.n_docs, 1)
        self.df = defaultdict(int)  # 词 -> 出现在多少个文档里
        for doc in self.docs:
            for term in set(doc):
                self.df[term] += 1

    def search(self, query: str, top_k: int = 4) -> list[tuple[str, str, float]]:
        """返回 [(doc_name, content, score)]，按分数降序"""
        query_terms = jieba.lcut(query)
        scores = []
        for i, doc in enumerate(self.docs):
            tf = defaultdict(int)
            for t in doc:
                tf[t] += 1
            score = 0.0
            for term in set(query_terms):
                if term not in self.df:
                    continue
                idf = math.log((self.n_docs - self.df[term] + 0.5) / (self.df[term] + 0.5) + 1)
                k1, b = 1.5, 0.75  # BM25 经典超参
                denom = tf[term] + k1 * (1 - b + b * len(doc) / self.avg_len)
                score += idf * (tf[term] * (k1 + 1)) / denom
            scores.append((i, score))
        scores.sort(key=lambda x: -x[1])
        return [
            (*self.chunks[i], score)
            for i, score in scores[:top_k]
            if score > 0
        ]
