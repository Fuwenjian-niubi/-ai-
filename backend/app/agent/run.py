"""Agent 编排入口。

对外提供 run_agent() / run_agent_cached()（同步，供非流式路由）与
run_agent_stream()（async 生成器，真·逐 token 流式，供 SSE 路由）。

Qwen 原生支持 stream=true，因此 run_agent_stream 直接调用上游流式，
首字延迟从“等整段生成”降到 1~2s 出字（体感大幅改善）。缓存命中时则直接
返回 done 事件，实现复问秒回。
"""
from __future__ import annotations

from functools import lru_cache

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.agent.cache import get_cached, set_cached
from app.agent.graph import (
    AgentState,
    _build_context,
    _prompt_for,
    build_graph,
    load_context,
    route_skill,
    save_memory,
)
from app.rag.llm import get_llm
from app.skills import builtin


@lru_cache(maxsize=1)
def _graph():
    return build_graph()


def run_agent(
    kb_id: int,
    user_id: int,
    query: str,
    db,
    session_id: int | None = None,
) -> dict:
    state0: AgentState = {
        "query": query,
        "kb_id": kb_id,
        "user_id": user_id,
        "session_id": session_id,
        "db": db,
        "history": [],
        "memory": [],
        "retrieved": [],
        "skill": "",
        "answer": "",
        "citations": [],
    }
    result = _graph().invoke(state0)
    return {
        "answer": result["answer"],
        "citations": result["citations"],
        "skill": result["skill"],
        "memory_used": result["memory"],
    }


def run_agent_cached(kb_id: int, user_id: int, query: str, db, session_id: int | None = None) -> dict:
    """带进程内答案缓存的问答：相同 (kb_id, query) 命中即秒回，缓解重复慢感。"""
    hit = get_cached(kb_id, query)
    if hit is not None:
        return hit
    res = run_agent(kb_id, user_id, query, db, session_id)
    set_cached(kb_id, query, res)
    return res


async def run_agent_stream(kb_id: int, user_id: int, query: str, db, session_id: int | None = None):
    """真·流式问答生成器：逐个 yield {"type": "token"/"done"/"error"} 事件。

    - 命中答案缓存：直接 yield done（秒回，无需等上游）。
    - 未命中：复用 LangGraph 的 load_context / route_skill 取得检索上下文，
      再用 get_llm(streaming=True).astream 逐 token 推送；结束后写长期记忆、入缓存。
    """
    hit = get_cached(kb_id, query)
    if hit is not None:
        yield {
            "type": "done",
            "answer": hit["answer"],
            "citations": hit["citations"],
            "skill": hit["skill"],
            "memory_used": hit["memory_used"],
        }
        return

    state: AgentState = {
        "query": query,
        "kb_id": kb_id,
        "user_id": user_id,
        "session_id": session_id,
        "db": db,
        "history": [],
        "memory": [],
        "retrieved": [],
        "skill": "",
        "answer": "",
        "citations": [],
    }
    state.update(load_context(state))
    state.update(route_skill(state))
    skill = state["skill"]

    if skill == "clarify":
        ans = builtin.skill_clarify(query)
        yield {"type": "token", "content": ans}
        yield {
            "type": "done",
            "answer": ans,
            "citations": [],
            "skill": skill,
            "memory_used": state["memory"],
        }
        return

    if skill == "general_chat":
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是友好的景点讲解助手，可进行简单寒暄，并引导用户就具体景点提问。"),
            ("human", "{question}"),
        ])
    elif skill == "daily_chat":
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "你是友好、热情的景点 AI 讲解助手。用户正在和你进行日常闲聊或问候，"
                "请自然亲切地回应，不要反问用户，也不需要强行关联景点。"
                "如果对方愿意，可以友好地邀请他继续咨询任何景点问题。",
            ),
            ("human", "{question}"),
        ])
    else:
        context = _build_context(state["retrieved"])
        prompt = _prompt_for(skill, state["history"], state["memory"], context)

    chain = prompt | get_llm(streaming=True) | StrOutputParser()
    answer = ""
    try:
        async for piece in chain.astream({"question": query}):
            if piece:
                answer += piece
                yield {"type": "token", "content": piece}
    except Exception as e:  # noqa: BLE001
        yield {"type": "error", "message": str(e)}
        return

    citations = [
        {"index": i, "source": r.get("source"), "content": r["content"]}
        for i, r in enumerate(state["retrieved"], 1)
    ]
    save_memory(state)
    result = {
        "answer": answer,
        "citations": citations,
        "skill": skill,
        "memory_used": state["memory"],
    }
    set_cached(kb_id, query, result)
    yield {
        "type": "done",
        "answer": answer,
        "citations": citations,
        "skill": skill,
        "memory_used": state["memory"],
    }

