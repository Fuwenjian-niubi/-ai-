# 景点 AI 问答机器人 —— 后端

基于 FastAPI + LangChain 的 RAG 景点知识库问答系统（暑假项目）。

## 当前进度：M1 / M2 完成，M3（Agent+记忆+Skills）已落地
- M1 后端骨架：FastAPI + SQLAlchemy + JWT 鉴权 + 会话/用户 CRUD。
- M2 RAG：文档摄入（txt/md/pdf/docx）→ 中文分块 → bge 嵌入 → Chroma（按 kb_id 隔离）→ 向量召回+bge重排 → 带引用溯源问答（通义千问 Qwen 生成）。
- M3 智能体：
  - **记忆系统** `app/memory/store.py`：会话级（messages 表）、长期记忆（独立 Chroma 集合，跨会话召回用户关注点）。
  - **技能注册表** `app/skills/`：可插拔技能（knowledge_qa / nearby_recommend / general_chat / clarify），并封装为 LangChain Tool。
  - **LangGraph 智能体** `app/agent/graph.py`：状态图 `load_context → route_skill → synthesize → save_memory`，编排记忆+技能+RAG。

## 本地运行

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # 填入 LLM_API_KEY 等（通义千问 DashScope Key）
uvicorn app.main:app --reload --port 8000
```

启动后访问 http://127.0.0.1:8000/docs 查看接口文档。

## 接口一览
- `GET  /api/health`
- `POST /api/auth/register` · `POST /api/auth/login` · `GET /api/auth/me` · `POST /api/auth/change-password`
- `POST /api/sessions`  ·  `GET /api/sessions`  ·  `GET /api/sessions/{id}`  ·  `PATCH /api/sessions/{id}`  ·  `DELETE /api/sessions/{id}`
- `POST /api/kb`（admin：建库） · `GET /api/kb` · `DELETE /api/kb/{id}`
- `POST /api/kb/{id}/documents`（admin：上传摄入）
- `POST /api/qa`（问答+引用+技能+记忆） · `GET /api/qa/skills`（列出技能）

## 知识库摄入（管理员）
文档放入 `data/kb_raw/<景点名>/`，通过 `POST /api/kb/{id}/documents` 上传摄入；
或本地脚本：`python scripts/ingest_kb.py --kb-id 1 --folder data/kb_raw/广州塔`。

## 模型说明
首次运行需下载本地模型（自动）：`BAAI/bge-base-zh-v1.5`（嵌入）、`BAAI/bge-reranker-v2-m3`（重排）。
如缓存损坏可手动重下：`python scripts/download_models.py`。
