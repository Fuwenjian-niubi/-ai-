"""记忆系统（Memory）。

三层记忆：
1. 短期记忆：当前请求内的会话窗口缓冲（在 Agent 内处理，不在此持久化）。
2. 会话级记忆：每个 (用户, 会话) 独立，由 messages 表持久化（load_session_history）。
3. 长期记忆：用户级偏好/关注点，存入独立 Chroma 集合，跨会话召回。

本模块负责「会话级加载」与「长期记忆存取」。
"""
from __future__ import annotations

import uuid

from app.config import settings
from app.rag.chroma_store import get_client
from app.rag.embeddings import embed_query, embed_texts

# 长期记忆独立集合（所有用户共用，按 user_id 元数据隔离）
_USER_MEMORY_COLLECTION = "user_long_term_memory"


def _memory_collection():
    client = get_client()
    return client.get_or_create_collection(name=_USER_MEMORY_COLLECTION)


def add_user_memory(user_id: int, text: str) -> None:
    """写入一条长期记忆（例如用户的关注点 / 偏好）。"""
    text = (text or "").strip()
    if not text:
        return
    col = _memory_collection()
    emb = embed_texts([text])
    col.add(
        embeddings=emb,
        documents=[text],
        ids=[str(uuid.uuid4())],
        metadatas=[{"user_id": user_id}],
    )


def retrieve_user_memory(user_id: int, query: str, k: int = 3) -> list[str]:
    """跨会话召回与当前问题相关的长期记忆。"""
    col = _memory_collection()
    try:
        res = col.query(
            query_embeddings=[embed_query(query)],
            n_results=k,
            where={"user_id": user_id},
            include=["documents"],
        )
    except Exception:  # noqa: BLE001 - 集合为空等情况
        return []
    return (res.get("documents") or [[]])[0]


def load_session_history(db, session_id: int | None, window: int = 10) -> list[dict]:
    """从 messages 表加载某会话最近的 window 轮对话（会话级记忆）。"""
    if not session_id:
        return []
    from app import models

    rows = (
        db.query(models.Message)
        .filter(models.Message.session_id == session_id)
        .order_by(models.Message.id.desc())
        .limit(window * 2)
        .all()
    )
    rows.reverse()
    return [{"role": m.role, "content": m.content} for m in rows]
