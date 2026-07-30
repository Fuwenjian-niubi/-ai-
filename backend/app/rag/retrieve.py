from functools import lru_cache

from app.config import settings
from app.rag.chroma_store import collection_name, get_client
from app.rag.embeddings import embed_query


@lru_cache(maxsize=1)
def _reranker():
    from sentence_transformers import CrossEncoder

    return CrossEncoder(settings.RERANKER_MODEL)


def _rerank(query: str, results: list[dict]) -> list[dict]:
    if not results:
        return results
    ce = _reranker()
    pairs = [(query, r["content"]) for r in results]
    scores = ce.predict(pairs)
    for r, s in zip(results, scores):
        r["rerank_score"] = float(s)
    results.sort(key=lambda x: x["rerank_score"], reverse=True)
    return results


def retrieve(kb_id: int, query: str, top_k: int | None = None) -> list[dict]:
    """按 kb 隔离检索：向量召回 → bge 重排 → 返回带来源的结果。"""
    top_k = top_k or settings.RETRIEVE_TOP_K
    client = get_client()
    col = client.get_or_create_collection(name=collection_name(kb_id))
    q_emb = embed_query(query)
    res = col.query(
        query_embeddings=[q_emb],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]

    results = [
        {
            "content": d,
            "source": (m or {}).get("source"),
            "score": float(dist),
        }
        for d, m, dist in zip(docs, metas, dists)
    ]
    return _rerank(query, results)[: settings.RERANK_TOP_K]
