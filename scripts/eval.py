"""评测脚本：检验知识库"应答/拒答"边界判断准确率。

用法：python scripts/eval.py
- 读 eval_questions.json（20 条：10 条库内应回答 + 10 条库外应拒答）
- 对每条问题跑混合检索，按拒答阈值判定，与期望对比
- 输出逐题结果 + 整体准确率 + 召回/拒答正确率
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config
from app.services import embedding, retriever


def main():
    retriever.build_index()  # 构建 BM25 索引

    with open(Path(__file__).resolve().parent.parent / "eval_questions.json", encoding="utf-8") as f:
        questions = json.load(f)

    correct = 0
    answer_total = sum(1 for q in questions if q["expect"] == "answer")
    reject_total = len(questions) - answer_total
    answer_hit = 0  # 库内问题被正确应答
    reject_hit = 0  # 库外问题被正确拒答

    print(f"{'预期':<7} {'判定':<7} {'最高相似度':<10} 问题")
    print("-" * 60)
    for item in questions:
        q = item["question"]
        hits, max_sim = retriever.hybrid_search(q, top_k=4)
        decision = "answer" if hits and max_sim >= config.REJECT_THRESHOLD else "reject"
        ok = decision == item["expect"]
        if ok:
            correct += 1
        if item["expect"] == "answer" and ok:
            answer_hit += 1
        if item["expect"] == "reject" and ok:
            reject_hit += 1
        mark = "OK " if ok else "MISS"
        print(f"{item['expect']:<7} {decision:<7} {max_sim:<10.3f} {mark} {q}")

    n = len(questions)
    print("-" * 60)
    print(f"总题数: {n}")
    print(f"边界判断准确率: {correct}/{n} = {correct / n:.0%}")
    print(f"库内问题应答率(召回): {answer_hit}/{answer_total} = {answer_hit / answer_total:.0%}")
    print(f"库外问题拒答率: {reject_hit}/{reject_total} = {reject_hit / reject_total:.0%}")


if __name__ == "__main__":
    main()
