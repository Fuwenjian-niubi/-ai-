import os
import uuid

from app.rag.chroma_store import collection_name, get_client
from app.rag.chunking import chunk_text
from app.rag.embeddings import embed_texts


def parse_file(path: str) -> str:
    """解析支持的文档格式，返回纯文本。"""
    ext = os.path.splitext(path)[1].lower()
    if ext in (".txt", ".md", ".text"):
        with open(path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    if ext == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(path)
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    if ext == ".docx":
        from docx import Document

        document = Document(path)
        return "\n".join(p.text for p in document.paragraphs if p.text)
    raise ValueError(f"不支持的文件格式: {ext}")


def ingest_document(kb_id: int, file_path: str, source_name: str) -> int:
    """解析→分块→嵌入→写入 Chroma，返回分块数。"""
    text = parse_file(file_path)
    chunks = chunk_text(text)
    if not chunks:
        return 0

    embeddings = embed_texts(chunks)
    client = get_client()
    col = client.get_or_create_collection(
        name=collection_name(kb_id), metadata={"kb_id": kb_id}
    )
    ids = [str(uuid.uuid4()) for _ in chunks]
    metadatas = [{"source": source_name, "kb_id": kb_id} for _ in chunks]
    col.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    return len(chunks)
