"""进程内答案缓存。

Agnes 单次调用约 30s 且不支持上游流式，因此对“相同问题重复问”这类高频场景，
命中缓存可做到秒回，是缓解慢感最有效的手段。

- 键：kb_id + 归一化后的 query（忽略大小写与首尾空白）。
- TTL：默认 1 小时，过期自动失效。
- 失效：知识库内容变更（上传/删除文档）时由 kb 路由调用 invalidate_kb()。

单进程（uvicorn 单 worker）下足够；多 worker / 重启会清空，属可接受权衡。
"""
from __future__ import annotations

import time

_TTL_SECONDS = 3600

_CACHE: dict[str, tuple[float, dict]] = {}


def _key(kb_id: int, query: str) -> str:
    return f"{kb_id}::{(query or '').strip().lower()}"


def get_cached(kb_id: int, query: str):
    item = _CACHE.get(_key(kb_id, query))
    if item is None:
        return None
    ts, res = item
    if time.time() - ts > _TTL_SECONDS:
        _CACHE.pop(_key(kb_id, query), None)
        return None
    return res


def set_cached(kb_id: int, query: str, res: dict) -> None:
    _CACHE[_key(kb_id, query)] = (time.time(), res)


def invalidate_kb(kb_id: int) -> None:
    """知识库内容变更后调用，清掉该库相关的所有缓存条目。"""
    prefix = f"{kb_id}::"
    for k in list(_CACHE.keys()):
        if k.startswith(prefix):
            _CACHE.pop(k, None)
