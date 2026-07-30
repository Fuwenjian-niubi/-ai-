from functools import lru_cache

from app.config import settings


@lru_cache(maxsize=1)
def get_client():
    """返回复用的 Chroma 持久化客户端单例。

    复用客户端可避免每次检索都重新打开底层存储与建立连接，
    是检索性能优化的一环（配合启动时预热，首次查询几乎无建连开销）。
    """
    import chromadb

    return chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)


def collection_name(kb_id: int) -> str:
    return f"kb_{kb_id}"
