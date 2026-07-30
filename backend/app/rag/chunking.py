import re

from app.config import settings


def chunk_text(
    text: str, size: int | None = None, overlap: int | None = None
) -> list[str]:
    """中文友好的分块：按句末/换行切分，按字符数装箱，带重叠。"""
    size = size or settings.CHUNK_SIZE
    overlap = overlap or settings.CHUNK_OVERLAP

    text = text.replace("\r\n", "\n").strip()
    if not text:
        return []

    # 在句号/问号/感叹号/换行后切分，保留标点
    pieces = re.split(r"(?<=[。！？\n])", text)
    pieces = [p for p in pieces if p.strip()]

    chunks: list[str] = []
    buf = ""
    for piece in pieces:
        if len(buf) + len(piece) <= size:
            buf += piece
        else:
            if buf:
                chunks.append(buf.strip())
            # 新块带重叠，避免截断语义
            buf = (buf[-overlap:] if overlap else "") + piece
            # 若单句超长，强制按 size 硬切
            while len(buf) > size:
                chunks.append(buf[:size].strip())
                buf = buf[size - overlap :] if overlap else buf[size:]
    if buf.strip():
        chunks.append(buf.strip())
    return [c for c in chunks if c]
