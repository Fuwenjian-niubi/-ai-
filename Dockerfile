# syntax=docker/dockerfile:1

# ============================================================
# 阶段 1：构建前端（React + Vite）
# ============================================================
FROM node:22-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ============================================================
# 阶段 2：后端运行环境
# ============================================================
FROM python:3.13-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    KMP_DUPLICATE_LIB_OK=TRUE \
    OMP_NUM_THREADS=1 \
    HF_ENDPOINT=https://hf-mirror.com \
    PIP_NO_CACHE_DIR=1

# 系统依赖：ffmpeg 供 faster-whisper 使用；build-essential 用于部分包编译
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安装 Python 依赖到独立虚拟环境（镜像内路径 /opt/venv）
COPY backend/requirements.txt ./backend/requirements.txt
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r backend/requirements.txt

# 复制后端源码与前端构建产物
COPY backend/ ./backend/
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8000

# 单 worker：模型（torch / bge / faster-whisper）占用内存较大，
# 多 worker 会各自加载一份；并发靠 uvicorn 线程池处理，足够本项目场景。
CMD ["sh", "-c", "cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1"]
