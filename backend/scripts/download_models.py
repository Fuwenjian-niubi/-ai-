"""下载并校验 M2 RAG 所需的本地模型（嵌入 + 重排）。
用法：python scripts/download_models.py
断点续传由 huggingface_hub 保证；结束后会实际加载一次以确认完整性。
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings


def download_with_retry(repo: str, max_retries: int = 5):
    from huggingface_hub import snapshot_download

    for attempt in range(1, max_retries + 1):
        try:
            print(f"[{repo}] 尝试下载 ({attempt}/{max_retries}) ...", flush=True)
            path = snapshot_download(repo_id=repo, local_files_only=False)
            print(f"[{repo}] 下载完成：{path}", flush=True)
            return path
        except Exception as e:  # noqa: BLE001
            print(f"[{repo}] 下载失败：{e}", flush=True)
            time.sleep(3)
    raise SystemExit(f"[{repo}] 多次重试仍失败")


def verify_load():
    print("=== 校验模型可加载 ===", flush=True)
    from sentence_transformers import CrossEncoder, SentenceTransformer

    enc = SentenceTransformer(settings.EMBEDDING_MODEL)
    print(f"嵌入模型加载OK，维度={enc.get_sentence_embedding_dimension()}", flush=True)
    ce = CrossEncoder(settings.RERANKER_MODEL)
    print(f"重排模型加载OK：{type(ce).__name__}", flush=True)


if __name__ == "__main__":
    for repo in [settings.EMBEDDING_MODEL, settings.RERANKER_MODEL]:
        download_with_retry(repo)
    verify_load()
    print("=== 全部模型就绪 ===", flush=True)
