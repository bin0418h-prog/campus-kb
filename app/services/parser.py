"""文档解析：把 PDF / Word / Markdown 转成纯文本"""
from pathlib import Path

import pymupdf  # PDF 解析
from docx import Document  # Word 解析


def parse_file(path: Path) -> str:
    """按文件后缀分发到对应的解析器"""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _parse_pdf(path)
    if suffix == ".docx":
        return _parse_docx(path)
    if suffix in (".md", ".txt"):
        return path.read_text(encoding="utf-8")
    raise ValueError(f"不支持的文件类型: {suffix}")


def _parse_pdf(path: Path) -> str:
    doc = pymupdf.open(path)
    return "\n".join(page.get_text() for page in doc)


def _parse_docx(path: Path) -> str:
    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
