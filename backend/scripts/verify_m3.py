"""M3 端到端验证：重摄入广州塔 → 经 LangGraph 智能体问答。

覆盖：knowledge_qa（含引用）、nearby_recommend（周边技能）、general_chat（寒暄）。
并验证长期记忆：先问一次，再问相关问题时 memory_used 非空。

用法：
  python scripts/verify_m3.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent.run import run_agent
from app.database import SessionLocal
from app.rag.chroma_store import collection_name, get_client
from app.rag.ingest import ingest_document

KB_ID = 1
FOLDER = "data/kb_raw/广州塔"


def reingest():
    client = get_client()
    name = collection_name(KB_ID)
    try:
        client.delete_collection(name)
        print(f"[ingest] 清空旧集合 {name}")
    except Exception:  # noqa: BLE001
        pass
    total = 0
    for fn in sorted(os.listdir(FOLDER)):
        if fn.lower().endswith((".txt", ".md", ".pdf", ".docx")):
            n = ingest_document(KB_ID, os.path.join(FOLDER, fn), source_name=fn)
            total += n
            print(f"[ingest] {fn}: {n} 块")
    print(f"[ingest] 共 {total} 块")


def ask(db, q, session_id=None):
    r = run_agent(kb_id=KB_ID, user_id=1, query=q, db=db, session_id=session_id)
    print(f"\n问题：{q}")
    print(f"  命中技能：{r['skill']}")
    print(f"  长期记忆召回：{r['memory_used']}")
    print(f"  引用数：{len(r['citations'])}")
    print(f"  回答：{r['answer'][:300]}")
    return r


def main():
    print("=== 重摄入知识库 ===")
    reingest()

    db = SessionLocal()
    try:
        print("\n=== 智能体问答 ===")
        ask(db, "广州塔有多高？")                       # knowledge_qa + 引用
        ask(db, "广州塔周边有什么交通和美食推荐？")        # nearby_recommend
        ask(db, "你好")                                  # general_chat
        # 再次提问，验证长期记忆召回（上一轮已写入关注点）
        r = ask(db, "广州塔的门票价格是多少？")
        assert r["memory_used"] is not None
    finally:
        db.close()
    print("\n=== M3 验证完成 ===")


if __name__ == "__main__":
    main()
