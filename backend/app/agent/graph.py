"""LangGraph 智能体编排（Agent）。

状态图（四节点）：
  START → load_context → route_skill → synthesize → save_memory → END

- load_context：加载会话级历史 + 跨会话长期记忆（记忆系统接入点）。
- route_skill ：基于轻量意图路由选择技能（知识问答 / 周边推荐 / 通用 / 澄清）。
- synthesize  ：组装提示词（记忆 + 历史 + 知识库上下文），调用 Agnes 生成回答与引用。
- save_memory ：把本次关注点写入长期记忆，供后续会话召回。

Skills 通过 app.skills.builtin 注册；长期/会话记忆通过 app.memory.store 实现。
"""
from __future__ import annotations

from typing import Any, TypedDict

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, START, StateGraph

from app.agent.tools import clarify_reply, general_reply, knowledge_context  # noqa: F401
from app.memory.store import (
    add_user_memory,
    load_session_history,
    retrieve_user_memory,
)
from app.rag.llm import get_llm
from app.rag.qa import _build_context
from app.skills import builtin  # 触发内置技能注册
from app.skills.registry import registry


class AgentState(TypedDict):
    query: str
    kb_id: int
    user_id: int
    session_id: int | None
    db: Any  # SQLAlchemy Session（不持久化，仅本次请求使用）
    history: list[dict]
    memory: list[str]
    retrieved: list[dict]
    skill: str
    answer: str
    citations: list[dict]


# ----------------------------- 节点 -----------------------------
def load_context(state: AgentState) -> dict:
    history = load_session_history(state["db"], state.get("session_id"))
    memory = retrieve_user_memory(state["user_id"], state["query"])
    return {"history": history, "memory": memory}


def route_skill(state: AgentState) -> dict:
    skill_name = builtin.route_query(state["query"])
    retrieved: list[dict] = []
    if skill_name in ("knowledge_qa", "nearby_recommend"):
        skill = registry.get(skill_name)
        retrieved = skill.func(state["kb_id"], state["query"]) if skill else []
    return {"skill": skill_name, "retrieved": retrieved}


def _prompt_for(skill: str, history: list[dict], memory: list[str], context: str) -> ChatPromptTemplate:
    if skill == "nearby_recommend":
        base = (
            "你是专业的景点讲解与导览助手。用户正在询问景点的周边推荐"
            "（交通 / 美食 / 住宿 / 玩法）。请【仅基于】下方知识库内容给出实用建议，"
            "在相关句末用 [n] 标注引用编号（对应引用来源顺序）；资料不足时如实说明。"
        )
    else:
        base = (
            "你是专业的景点讲解助手。请严格【仅基于】下方“知识库内容”回答用户问题。\n"
            "规则：\n1. 若知识库内容不足以回答，请如实说明“根据现有资料无法回答”，禁止编造。"
            "\n2. 回答中请在相关句末用 [n] 标注引用编号，编号必须对应引用来源顺序。"
            "\n3. 语言自然、面向游客，可适当补充细节。"
        )
    parts = [base]
    if memory:
        parts.append("【用户长期偏好 / 关注】\n" + "\n".join(f"- {m}" for m in memory))
    if history:
        turns = "\n".join(
            f"{'游客' if h['role'] == 'user' else '助手'}: {h['content']}" for h in history
        )
        parts.append("【对话历史】\n" + turns)
    parts.append("【知识库内容】\n" + (context or "（无相关内容）"))
    system_full = "\n\n".join(parts)
    return ChatPromptTemplate.from_messages([("system", system_full), ("human", "{question}")])


def synthesize(state: AgentState) -> dict:
    skill = state["skill"]

    if skill == "clarify":
        return {"answer": builtin.skill_clarify(state["query"]), "citations": []}

    if skill == "general_chat":
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是友好的景点讲解助手，可进行简单寒暄，并引导用户就具体景点提问。"),
            ("human", "{question}"),
        ])
        chain = prompt | get_llm() | StrOutputParser()
        answer_text = chain.invoke({"question": state["query"]})
        return {"answer": answer_text, "citations": []}

    if skill == "daily_chat":
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "你是友好、热情的景点 AI 讲解助手。用户正在和你进行日常闲聊或问候，"
                "请自然亲切地回应，不要反问用户，也不需要强行关联景点。"
                "如果对方愿意，可以友好地邀请他继续咨询任何景点问题。",
            ),
            ("human", "{question}"),
        ])
        chain = prompt | get_llm() | StrOutputParser()
        answer_text = chain.invoke({"question": state["query"]})
        return {"answer": answer_text, "citations": []}

    # knowledge_qa / nearby_recommend：基于检索上下文生成带引用回答
    context = _build_context(state["retrieved"])
    prompt = _prompt_for(skill, state["history"], state["memory"], context)
    chain = prompt | get_llm() | StrOutputParser()
    answer_text = chain.invoke({"question": state["query"]})
    citations = [
        {"index": i, "source": r.get("source"), "content": r["content"]}
        for i, r in enumerate(state["retrieved"], 1)
    ]
    return {"answer": answer_text, "citations": citations}


def save_memory(state: AgentState) -> dict:
    # 把本次关注点写入长期记忆，供后续会话召回。
    # 日常寒暄、澄清反问等不必写入记忆，避免记忆被无用问候刷屏。
    if state["skill"] in ("daily_chat", "clarify", "general_chat"):
        return {}
    add_user_memory(state["user_id"], f"用户关注：{state['query']}")
    return {}


# ----------------------------- 图构建 -----------------------------
def build_graph():
    g = StateGraph(AgentState)
    g.add_node("load_context", load_context)
    g.add_node("route_skill", route_skill)
    g.add_node("synthesize", synthesize)
    g.add_node("save_memory", save_memory)
    g.add_edge(START, "load_context")
    g.add_edge("load_context", "route_skill")
    g.add_edge("route_skill", "synthesize")
    g.add_edge("synthesize", "save_memory")
    g.add_edge("save_memory", END)
    return g.compile()
