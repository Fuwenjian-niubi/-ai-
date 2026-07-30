"""后端离线冒烟测试（不联网、不依赖 API Key）。

覆盖：
  - 整个 FastAPI 应用的导入（验证所有路由/服务无导入期错误）
  - LLM 配置加载（llm_runtime.json > .env > 默认值）
  - RAG 中文分块（按句、带重叠、长文本分块）
  - 技能注册表与意图路由（日常对话 / 知识问答 / 周边推荐 / 澄清）
  - Agent 状态图构建（LangGraph，离线）
  - ChatOpenAI 客户端构造（离线，不发起请求）
"""
from __future__ import annotations


def test_app_imports_and_health_route():
    # 导入整个应用，验证所有 router / service 在导入期无错误
    from app.main import app

    assert app is not None
    paths = [getattr(r, "path", "") for r in app.routes]
    assert "/api/health" in paths


def test_llm_config_loads():
    from app.rag.llm import load_llm_config

    cfg = load_llm_config()
    assert {"api_key", "base_url", "model", "max_tokens"} <= set(cfg.keys())
    assert cfg["base_url"]
    assert isinstance(cfg["max_tokens"], int)


def test_get_llm_constructs_offline():
    from langchain_openai import ChatOpenAI

    from app.rag.llm import get_llm

    llm = get_llm()
    assert isinstance(llm, ChatOpenAI)
    # 流式开关不应改变构造本身的成功
    assert get_llm(streaming=True) is not None


def test_chunk_text_empty_and_short():
    from app.rag.chunking import chunk_text

    assert chunk_text("") == []
    assert chunk_text("   ") == []

    short = "广州塔很高。"
    chunks = chunk_text(short)
    assert len(chunks) == 1
    assert chunks[0] == "广州塔很高。"


def test_chunk_text_long_splits_with_overlap():
    from app.rag.chunking import chunk_text

    text = "。".join([f"第{i}句景点介绍内容很长很长很长很长" for i in range(60)]) + "。"
    chunks = chunk_text(text, size=120, overlap=30)

    assert len(chunks) > 1
    # 所有块均非空，且总覆盖应接近原文
    assert all(c.strip() for c in chunks)
    joined = "".join(chunks)
    assert len(joined) >= len(text) - 200  # 重叠会拉长，但应覆盖全文


def test_skill_registry_has_core_skills():
    from app.skills import builtin  # 导入即触发注册
    from app.skills.registry import registry

    names = registry.names()
    for skill in (
        "knowledge_qa",
        "nearby_recommend",
        "daily_chat",
        "clarify",
        "general_chat",
    ):
        assert skill in names, f"缺少内置技能：{skill}"


def test_route_query_intent():
    from app.skills import builtin

    # 日常对话 / 寒暄应路由到 daily_chat（不再反问）
    assert builtin.route_query("你好") == "daily_chat"
    assert builtin.route_query("谢谢") == "daily_chat"
    assert builtin.route_query("你是谁") == "daily_chat"

    # 知识问答
    assert builtin.route_query("广州塔有多高") == "knowledge_qa"

    # 周边推荐
    assert builtin.route_query("周边有什么美食推荐") == "nearby_recommend"

    # 过短 / 模糊 → 澄清
    assert builtin.route_query("?") == "clarify"
    assert builtin.route_query("塔") == "clarify"


def test_build_agent_graph_offline():
    from app.agent.graph import build_graph

    graph = build_graph()
    assert graph is not None
