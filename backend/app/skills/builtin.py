"""内置技能与路由。

内置技能：
- knowledge_qa    核心 RAG：基于知识库检索回答（带引用）
- nearby_recommend 周边推荐：基于知识库检索周边/交通/美食等
- general_chat    通用对话 / 寒暄兜底
- clarify         澄清：问题过短或模糊时反问

route_query() 为轻量意图路由，决定 Agent 调用哪个技能（无需额外 LLM 调用，
稳定且可解释）。
"""
from __future__ import annotations

from app.rag.retrieve import retrieve
from app.skills.registry import Skill, registry

# 周边/推荐类关键词
_NEARBY_KEYWORDS = ["周边", "附近", "推荐", "美食", "交通", "住宿", "怎么去", "怎么走", "玩", "游玩"]

# 日常对话 / 寒暄 / 自我介绍 / 礼貌用语（命中后不再反问澄清）
_DAILY_GREETINGS = {
    "你好", "您好", "hi", "hello", "在吗", "在么", "在嘛",
    "哈喽", "嗨", "hey", "早上好", "中午好", "下午好", "晚上好",
    "再见", "拜拜", "bye", "goodbye",
    "谢谢", "多谢", "感谢", "辛苦了",
    "你是谁", "你是谁？", "你叫什么", "你叫什么名字", "你能做什么",
    "你会做什么", "介绍一下自己", "自我介绍一下", "你是干什么的",
}
_DAILY_KEYWORDS = ["你好", "您好", "哈喽", "嗨", "谢谢", "再见", "拜拜", "辛苦了"]


def skill_knowledge_qa(kb_id: int, query: str) -> list[dict]:
    """核心技能：按 kb 检索返回相关片段（供 synthesize 生成带引用回答）。"""
    return retrieve(kb_id, query)


def skill_nearby_recommend(kb_id: int, query: str) -> list[dict]:
    """周边推荐技能：以推荐类检索词拉取周边/交通/美食上下文。"""
    return retrieve(kb_id, query + " 周边 交通 美食 住宿 推荐")


def skill_general_chat(query: str) -> str:
    return ""  # 由 Agent 的 synthesize 用通用提示词生成


def skill_daily_chat(query: str) -> str:
    """日常对话技能：寒暄、问候、自我介绍等，不强制关联景点。"""
    return ""  # 由 Agent 的 synthesize 用日常对话提示词生成


def skill_clarify(query: str) -> str:
    return (
        "您的问题有点模糊，可以告诉我您想了解关于这个景点的哪方面吗？"
        "例如：开放时间、门票价格、交通方式、历史背景、游玩路线等。"
    )


def route_query(query: str) -> str:
    """轻量意图路由，返回技能名。

    优先级：日常对话 > 澄清 > 周边推荐 > 知识问答。
    这样用户说“你好”“谢谢”等不会被反问。
    """
    q = (query or "").strip()
    ql = q.lower()

    if ql in _DAILY_GREETINGS or any(k in q for k in _DAILY_KEYWORDS):
        return "daily_chat"

    if len(q) <= 3:
        return "clarify"

    if any(k in q for k in _NEARBY_KEYWORDS):
        return "nearby_recommend"

    return "knowledge_qa"


def register_builtin_skills() -> None:
    registry.register(Skill("knowledge_qa", "基于景点知识库检索并回答（带引用）", skill_knowledge_qa))
    registry.register(Skill("nearby_recommend", "检索景点周边交通/美食/住宿等推荐信息", skill_nearby_recommend))
    registry.register(Skill("general_chat", "通用对话与寒暄兜底", skill_general_chat))
    registry.register(Skill("daily_chat", "日常对话与寒暄", skill_daily_chat))
    registry.register(Skill("clarify", "问题模糊时澄清反问", skill_clarify))


# 应用导入本模块即注册内置技能
register_builtin_skills()
