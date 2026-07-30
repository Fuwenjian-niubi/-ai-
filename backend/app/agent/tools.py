"""Agent 工具（LangChain Tool 封装）。

把内置技能包装成标准 LangChain Tool，便于后续升级为 ReAct / 函数调用式
智能体；当前图编排已直接调用技能函数，这里同时保留工具定义以满足
“Agent 具备可调用工具”的工程要求。
"""
from __future__ import annotations

from langchain_core.tools import tool

from app.skills import builtin


@tool
def knowledge_context(query: str, kb_id: int = 1) -> str:
    """基于景点知识库检索与问题相关的片段（返回原文，供回答时引用）。"""
    chunks = builtin.skill_knowledge_qa(kb_id, query)
    if not chunks:
        return "（知识库中未检索到相关内容）"
    return "\n".join(f"[{i}] {c['content']}（来源：{c.get('source')}）" for i, c in enumerate(chunks, 1))


@tool
def nearby_recommend(query: str, kb_id: int = 1) -> str:
    """检索景点周边的交通、美食、住宿等推荐信息。"""
    chunks = builtin.skill_nearby_recommend(kb_id, query)
    if not chunks:
        return "（知识库中未检索到周边相关信息）"
    return "\n".join(f"[{i}] {c['content']}（来源：{c.get('source')}）" for i, c in enumerate(chunks, 1))


@tool
def general_reply(query: str) -> str:
    """通用对话 / 寒暄兜底。"""
    return builtin.skill_general_chat(query)


@tool
def daily_reply(query: str) -> str:
    """日常对话 / 问候 / 自我介绍（不反问、不强制关联景点）。"""
    return builtin.skill_daily_chat(query)


@tool
def clarify_reply(query: str) -> str:
    """问题模糊时澄清反问。"""
    return builtin.skill_clarify(query)


AGENT_TOOLS = [knowledge_context, nearby_recommend, general_reply, daily_reply, clarify_reply]
