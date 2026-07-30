from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.rag.llm import get_llm
from app.rag.retrieve import retrieve

SYSTEM_PROMPT = (
    "你是专业的景点讲解助手。请严格【仅基于】下方提供的“知识库内容”回答用户问题。\n"
    "规则：\n"
    "1. 若知识库内容不足以回答，请如实说明“根据现有资料无法回答”，禁止编造。\n"
    "2. 回答中请在相关句末用 [n] 标注引用编号，编号必须对应下方“引用来源”的顺序。\n"
    "3. 语言自然、面向游客，适当补充知识库中的细节。"
)

HUMAN_TEMPLATE = "【知识库内容】\n{context}\n\n【用户问题】\n{question}"


def _build_context(results: list[dict]) -> str:
    lines = []
    for i, r in enumerate(results, 1):
        src = r.get("source") or "未知来源"
        lines.append(f"[{i}] {r['content']}（来源：{src}）")
    return "\n".join(lines)


def answer(kb_id: int, question: str) -> dict:
    results = retrieve(kb_id, question)
    context = _build_context(results)

    prompt = ChatPromptTemplate.from_messages(
        [("system", SYSTEM_PROMPT), ("human", HUMAN_TEMPLATE)]
    )
    chain = prompt | get_llm() | StrOutputParser()
    answer_text = chain.invoke({"context": context, "question": question})

    citations = [
        {"index": i, "source": r.get("source"), "content": r["content"]}
        for i, r in enumerate(results, 1)
    ]
    return {"answer": answer_text, "citations": citations}
