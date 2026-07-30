from functools import lru_cache

from app.config import settings

# bge 系列检索模型要求查询加前缀，文档不加
_QUERY_PREFIX = "为这个句子生成表示以用于检索相关文章："


@lru_cache(maxsize=1)
def _encoder():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.EMBEDDING_MODEL)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """文档块嵌入（无前缀）。"""
    return _encoder().encode(texts, normalize_embeddings=True).tolist()


def embed_query(text: str) -> list[float]:
    """查询嵌入（带 bge 前缀）。"""
    return _encoder().encode(_QUERY_PREFIX + text, normalize_embeddings=True).tolist()
