import os
import threading
from pathlib import Path

# 防止 torch/sentence-transformers 在 Windows 上因 OpenMP 重复库导致加载时段错误（segfault）
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import Base, engine
from .routers import auth, kb, qa, sessions, voice
from .routers import settings as settings_router
from .seed import seed_admin

# 前端生产构建产物目录：backend/app → backend → 项目根 → frontend/dist
_FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


def _preload_models():
    """后台预加载 bge 嵌入 / 重排模型，避免首次提问时再等待数十秒加载。"""
    try:
        from app.rag.embeddings import _encoder
        from app.rag.retrieve import _reranker

        _encoder()
        _reranker()
        print("[startup] bge embedding + reranker models preloaded.")
    except Exception as e:  # noqa: BLE001
        print(f"[startup] bge preload skipped (first query will load): {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_admin()
    # 后台预加载模型，不阻塞启动；若模型尚未下载会尝试从 HF 拉取（受 HF_ENDPOINT 影响）
    threading.Thread(target=_preload_models, daemon=True).start()
    yield


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(sessions.router)
app.include_router(kb.router)
app.include_router(qa.router)
app.include_router(settings_router.router)
app.include_router(voice.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "project": settings.PROJECT_NAME}


# ===== 托管前端生产构建（同一 8000 端口，API 与页面同源，免 CORS）=====
# 仅当 frontend/dist 存在时才托管；开发期用 `npm run dev`(5173) 则不受影响。
if _FRONTEND_DIST.exists():
    _assets_dir = _FRONTEND_DIST / "assets"
    if _assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(_assets_dir)), name="assets")

    @app.get("/")
    async def serve_index():
        return FileResponse(str(_FRONTEND_DIST / "index.html"))

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # 未匹配的 /api 路由保持 404 JSON；FastAPI 自带的 /docs、/openapi.json 由显式路由优先处理
        if full_path.startswith("api"):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        candidate = _FRONTEND_DIST / full_path
        if candidate.is_file():
            return FileResponse(str(candidate))
        # SPA 兜底：任意非资源路径返回 index.html（前端路由自行处理）
        return FileResponse(str(_FRONTEND_DIST / "index.html"))

