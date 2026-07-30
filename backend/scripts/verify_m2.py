"""
M2 端到端验证脚本（临时）。
步骤：创建/复用"广州塔"知识库 -> 摄入 docx -> 提问验证引用溯源。
运行：cd backend && python scripts/verify_m2.py
"""
import os
import sys

# 将 backend 目录加入 path，便于直接 import app
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from app import models
from app.database import SessionLocal
from app.rag import ingest
from app.rag import qa as rag_qa

DOC_PATH = os.path.join(BACKEND_DIR, "data", "kb_raw", "广州塔", "广州塔景点知识文档.docx")
SPOT = "广州塔"


def main():
    db = SessionLocal()
    try:
        # 1) 创建或复用知识库
        kb = db.query(models.KnowledgeBase).filter_by(spot=SPOT).first()
        if not kb:
            kb = models.KnowledgeBase(
                name="广州塔", description="广州塔景点知识库", spot=SPOT
            )
            db.add(kb)
            db.commit()
            db.refresh(kb)
            print(f"[1] 创建知识库 KB id={kb.id} name={kb.name}")
        else:
            print(f"[1] 复用知识库 KB id={kb.id} name={kb.name}")

        # 2) 摄入文档（已摄入则跳过）
        existing = db.query(models.Document).filter_by(kb_id=kb.id).first()
        if not existing:
            print(f"[2] 正在摄入文档：{os.path.basename(DOC_PATH)}（首次会下载 bge 模型，稍慢）")
            n = ingest.ingest_document(kb.id, DOC_PATH, os.path.basename(DOC_PATH))
            doc = models.Document(
                kb_id=kb.id, filename=os.path.basename(DOC_PATH), chunk_count=n
            )
            db.add(doc)
            db.commit()
            print(f"[2] 摄入完成，分块数={n}")
        else:
            print(f"[2] 已摄入，分块数={existing.chunk_count}，跳过")

        # 3) 提问验证（含引用溯源）
        questions = [
            "广州塔有多高？",
            "广州塔的开放时间是什么时候？",
            "广州塔有哪些特色观光项目？",
        ]
        for q in questions:
            print("\n" + "=" * 50)
            print(f"Q: {q}")
            res = rag_qa.answer(kb.id, q)
            print(f"A: {res['answer']}")
            print(f"引用片段数: {len(res['citations'])}")
            for c in res["citations"]:
                snippet = c["content"][:90].replace("\n", " ")
                print(f"  [{c['index']}] ({c['source']}) {snippet}...")
    finally:
        db.close()


if __name__ == "__main__":
    main()
