"""将本地知识文档重新摄入指定知识库（用于模型就绪后重建索引）。

用法：
  python scripts/ingest_kb.py --kb-id 1 --folder data/kb_raw/广州塔
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag.chroma_store import collection_name, get_client
from app.rag.ingest import ingest_document


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kb-id", type=int, required=True)
    ap.add_argument("--folder", required=True)
    args = ap.parse_args()

    # 清空旧集合，避免上次失败/中断留下的脏数据或重复
    client = get_client()
    name = collection_name(args.kb_id)
    try:
        client.delete_collection(name)
        print(f"已清空旧集合 {name}", flush=True)
    except Exception:  # noqa: BLE001
        print(f"集合 {name} 不存在，跳过清空", flush=True)

    total = 0
    for root, _dirs, files in os.walk(args.folder):
        for fn in sorted(files):
            if fn.lower().endswith((".txt", ".md", ".pdf", ".docx")):
                path = os.path.join(root, fn)
                n = ingest_document(args.kb_id, path, source_name=fn)
                total += n
                print(f"摄入 {fn}: {n} 块", flush=True)
    print(f"=== 知识库 {args.kb_id} 共摄入 {total} 块 ===", flush=True)


if __name__ == "__main__":
    main()
