from app.config import settings


def get_client():
    import chromadb

    return chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)


def collection_name(kb_id: int) -> str:
    return f"kb_{kb_id}"
