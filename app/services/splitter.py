"""文档分块：按段落聚合到目标大小，块间保留重叠，防止语义被切断"""
import re

CHUNK_SIZE = 500  # 每块约 500 字
OVERLAP = 80  # 相邻块重叠 80 字，切分点附近的内容两个块都能看到


def split_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    """结构感知分块：
    1. 按段落切（标题、章节天然是段落边界，结构信息得以保留）
    2. 小段落聚合直到接近 chunk_size，超了就开新块
    3. 新块开头带上上一块结尾的 overlap 字，防止一句话被切在两块中间
    """
    paras = [p.strip() for p in re.split(r"\n+", text) if p.strip()]

    chunks = []
    current = ""
    for para in paras:
        if current and len(current) + len(para) + 1 > chunk_size:
            chunks.append(current)
            current = para
        else:
            current = f"{current}\n{para}" if current else para
    if current:
        chunks.append(current)

    # 块间重叠
    result = []
    for i, chunk in enumerate(chunks):
        if i > 0:
            tail = chunks[i - 1][-overlap:]
            chunk = tail + "\n" + chunk
        result.append(chunk)
    return result
