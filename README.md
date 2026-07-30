# 景点 AI 问答机器人

基于 **LangChain + RAG** 的景点知识库智能问答系统（暑假项目）。支持多景点知识库检索、引用溯源、智能体（Agent + 记忆 + 技能）、语音问答（ASR/TTS），并可在网页后台直接配置大模型。纯 Web 形态（React 前端 + FastAPI 后端），支持双击一键启动。

> 在线仓库：`https://github.com/Fuwenjian-niubi/-ai-`

---

## ✨ 功能特性

- **多景点知识库**：按景点隔离构建知识库，上传 `txt / md / pdf / docx` 资料后自动摄入、分块、向量化。
- **RAG 检索增强**：中文按句分块 → `bge-base-zh-v1.5` 向量嵌入 → Chroma 向量库（按 `kb_id` 隔离）→ `bge-reranker-v2-m3` 重排 → 带**引用溯源**的回答。
- **智能体（Agent + 记忆 + Skills）**：
  - 记忆系统：会话级短期记忆 + 跨会话长期记忆（自动召回用户关注点）。
  - 技能注册表：知识问答 `knowledge_qa`、周边推荐 `nearby_recommend`、日常对话 `daily_chat`、澄清 `clarify` 等可插拔技能。
  - 基于 LangGraph 编排：`load_context → route_skill → synthesize → save_memory`。
- **真流式回复**：服务端 SSE 真流式输出，首个字延迟约 1–2 秒（默认关闭 Qwen3 思考模式）。
- **语音问答（M4）**：`faster-whisper` 语音识别（ASR）+ `edge-tts` 语音合成（TTS），前端一键录音提问、一键朗读回答。
- **多用户 / 多会话隔离**：JWT 鉴权，普通用户与管理员权限分离，会话相互独立。
- **网页模型设置（管理员）**：无需改配置、无需命令行，在网页「模型设置」页填写 `base_url / api_key / model` 即可切换大模型（运行时生效，持久化到 `llm_runtime.json`）。
- **一键启动**：双击 `启动.bat` 自动检测端口、启动后端、打开浏览器，并自动安装语音依赖、配置 HuggingFace 镜像。

---

## 🧱 技术架构

```
┌─────────────────────────┐      ┌──────────────────────────────────────────┐
│    前端 (React + Vite)   │      │            后端 (FastAPI + LangChain)      │
│  - 登录 / 聊天 / 知识库   │ HTTP │  - RAG 摄入与检索（Chroma + bge）          │
│  - 模型设置 / 语音问答    │◄────►│  - Agent 状态图（记忆 + 技能）             │
│  - 录音 / 朗读 / 流式渲染 │ SSE  │  - 语音 ASR/TTS（懒加载）                 │
└─────────────────────────┘      │  - JWT 鉴权 / 多用户多会话                 │
                                  └──────────────────────────────────────────┘
                       大模型：通义千问 Qwen（OpenAI 兼容，DashScope 直连）
                       嵌入/重排：BAAI/bge-base-zh-v1.5 · BAAI/bge-reranker-v2-m3
                       存储：SQLite（用户/会话/记忆） + Chroma（向量）
```

| 层 | 选型 |
|---|---|
| 前端 | React 18 + TypeScript + Vite（PWA 化，响应式） |
| 后端 | FastAPI + LangChain + LangGraph |
| 向量库 | Chroma（按 `kb_id` 隔离） |
| 关系/记忆存储 | SQLite（SQLAlchemy） |
| 嵌入模型 | `BAAI/bge-base-zh-v1.5` |
| 重排模型 | `BAAI/bge-reranker-v2-m3` |
| 大模型 | 通义千问 `qwen3.7-plus`（默认，可网页切换） |
| 语音 | `faster-whisper`（ASR） + `edge-tts`（TTS，音色 `zh-CN-XiaoxiaoNeural`） |

---

## 📁 目录结构

```
.
├── 启动.bat              # 一键启动（双击即可，无需命令行）
├── launcher.py           # 启动器：端口检测/起服务/开浏览器/装语音依赖
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── main.py       # 应用入口、路由注册、静态托管前端 dist
│   │   ├── config.py     # 配置（LLM_*）
│   │   ├── rag/          # RAG：llm / chunking / ingest / retrieve
│   │   ├── agent/        # Agent：graph / run / tools / memory
│   │   ├── skills/       # 技能注册表与内置技能
│   │   ├── routers/      # 路由：auth / sessions / kb / qa / settings / voice
│   │   ├── voice/        # ASR / TTS 实现（懒加载）
│   │   └── database.py   # SQLite 与表模型
│   ├── data/             # 知识库原始资料与向量数据
│   ├── tests/            # 离线冒烟测试（test_smoke.py）
│   ├── scripts/          # 门禁辅助、模型下载等脚本
│   ├── requirements.txt
│   └── .env.example      # 环境变量样例（复制为 .env 后填 Key）
├── frontend/             # React + Vite 前端
│   └── src/
│       ├── pages/        # 登录 / 聊天 / 知识库 / 设置
│       ├── components/   # 聊天组件、布局等
│       ├── api/          # 后端接口封装（含 voice / settings）
│       └── utils/        # 录音、音频转换等
└── README.md
```

---

## 🚀 快速开始

### 方式一：双击启动（推荐，无需命令行）

1. 进入项目根目录，**双击 `启动.bat`**。
2. 启动器会自动：
   - 释放/复用后端虚拟环境并安装依赖；
   - 检测并清理 `8000` 端口占用（冲突时自动顺延到 `8001+`）；
   - 启动 FastAPI 服务并打开浏览器 `http://127.0.0.1:8000`；
   - 配置 HuggingFace 镜像（`HF_ENDPOINT=https://hf-mirror.com`）；
   - 自动安装语音依赖（首次需要下载 `faster-whisper` / `edge-tts`）。
3. 用管理员账户登录（见下方「管理员账户」）。

> 首次运行会自动下载嵌入/重排模型（约 1–2 GB），请保持联网。

### 方式二：手动启动

**后端**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows 激活虚拟环境
pip install -r requirements.txt
cp .env.example .env             # 填入 LLM_API_KEY
uvicorn app.main:app --reload --port 8000
```

**前端（开发模式，可选）**

```bash
cd frontend
npm install
npm run dev                      # 启动开发服务器，默认 http://localhost:5173
```

> 生产形态下，前端需 `npm run build` 后由后端统一托管 `frontend/dist`，双击 `启动.bat` 即走此路径。

启动后接口文档见 `http://127.0.0.1:8000/docs`。

---

## ⚙️ 模型配置

默认使用**通义千问 Qwen**（OpenAI 兼容，DashScope 国内直连，无需代理）：

- `base_url`：`https://dashscope.aliyuncs.com/compatible-mode/v1`
- `model`：`qwen3.7-plus`
- `LLM_API_KEY`：在 [阿里云百炼](https://dashscope.console.aliyun.com/) 申请 DashScope API Key

**两种配置方式：**

1. **网页设置（推荐）**：管理员登录后进入「模型设置」页，填写 `base_url / api_key / model`，可先「测试连接」再「保存」，运行时立即生效（持久化到 `backend/llm_runtime.json`）。
2. **环境变量**：复制 `backend/.env.example` 为 `backend/.env`，填入 `LLM_API_KEY / LLM_BASE_URL / LLM_MODEL`。

> 切换为 DeepSeek / GLM / Kimi 等 OpenAI 兼容模型，仅需改上述三项即可，无需改动代码。

---

## 📚 知识库管理（管理员）

1. 在「知识库」页新建景点知识库（得到 `kb_id`）。
2. 上传该景点的资料（`txt / md / pdf / docx`），系统自动分块、向量化并写入对应向量集合。
3. 普通用户在前端选择景点后即可基于该知识库问答，回答附带引用来源。

也可通过本地脚本摄入：

```bash
python backend/scripts/ingest_kb.py --kb-id 1 --folder backend/data/kb_raw/广州塔
```

> 仓库内含示例知识库文档 `广州塔景点知识文档.docx`，可作为摄入样例。

---

## 🎙️ 语音问答（M4）

- **提问**：聊天输入框的 🎤 按钮开始录音（16kHz 单声道 WAV），松手自动 ASR 转文字并发送。
- **回答**：AI 消息下方的 🔊 按钮调用 `edge-tts` 朗读；若浏览器自带语音不可用，自动回退到系统 `speechSynthesis`。
- 语音依赖在首次启动时由 `launcher.py` 自动安装，缺失时仅语音端点报错，不影响其它功能。

---

## 👤 管理员账户

- 用户名：`admin`
- 密码：`123456`

首次启动后可用该账户登录后台；建议登录后在「设置」中修改密码。

---

## 🧪 开发与质量门禁

项目已配置归档门禁（`/存档` 技能），提交前需通过两项通行证：

- **单元测试**：`backend/tests/test_smoke.py`（8 个离线用例，不联网、不依赖 Key）。
- **质量检测**：后端 `ruff`（配置见 `backend/ruff.toml`）+ 前端 `tsc` 类型检查。

```bash
# 后端测试与 lint
cd backend
.venv\Scripts\python.exe -m pytest tests -q
.venv\Scripts\python.exe -m ruff check .

# 前端类型检查
cd frontend
npm run typecheck
```

---

## 🐳 Docker 部署

适合把整套服务（前端 + 后端）打包到服务器 / 云主机运行，宿主机无需安装 Python / Node。

### 构建与启动

```bash
# 在项目根目录，确保 backend/.env 已填好 LLM_API_KEY。
# 注意：Docker 不读取 .env 文件，而是由 docker-compose 的 env_file 将其注入为
# 容器环境变量；镜像本身不含任何密钥。
docker compose up -d --build
```

启动后访问 `http://<服务器IP>:8000`。首次启动会从 HuggingFace 镜像（`HF_ENDPOINT=https://hf-mirror.com`）拉取嵌入 / 重排模型（约 1–2 GB），请保持联网。

### 数据持久化

`docker-compose.yml` 已挂载两个卷，容器重启不丢数据：

- `./backend/data` → 知识库原始资料与向量数据
- `./backend/app.db` → SQLite 用户 / 会话库

网页「模型设置」写入的 `backend/llm_runtime.json` 默认保存在容器内（重启后需重设）；如需持久化，可在 `volumes` 中追加一行：

```yaml
      - ./backend/llm_runtime.json:/app/backend/llm_runtime.json
```

### 健康检查与编排

compose 内置 healthcheck：后端 `/api/health` 返回 `{"status":"ok"}` 即视为就绪（`start_period` 180s，给模型下载留时间），可用于容器编排与负载均衡探活。

### 运行说明

- 默认 **单 worker**（`--workers 1`）：torch / bge / faster-whisper 占用内存较大，多 worker 会各自加载一份；并发由 uvicorn 线程池处理，足够本项目场景。
- 改端口：调整 `docker-compose.yml` 的 `ports` 映射（如 `"9000:8000"`）即可。
- 本地开发 / Windows 体验仍推荐双击 `启动.bat`，无需 Docker。

---

## ❓ 常见问题

- **打开浏览器是空白页 / `{"detail":"Not Found"}`**：通常是旧的后端进程仍占用 `8000` 端口。双击 `启动.bat` 会自动清理；或手动结束占用进程后重试。
- **回复很慢 / 不是流式**：默认已关闭 Qwen3 思考模式并启用真流式，首字约 1–2 秒。若仍慢，检查网络与 `model` 是否填写正确。
- **发「你好」被反问「问题模糊」**：已加入 `daily_chat` 日常对话技能，问候/感谢会被优先路由为友好闲聊，不再反问。
- **模型 Key 等敏感信息**：`backend/.env`、`backend/llm_runtime.json`、`node_modules`、`dist`、`.venv`、模型 `*.bin` 等均已加入 `.gitignore`，不会进入版本库。

---

## 📌 当前进度

- ✅ M1 后端骨架 · M2 RAG 摄入检索引用 · M3 Agent+记忆+Skills · M4 语音 ASR/TTS · M5 前端（登录/聊天/知识库/设置）
- ✅ M6 性能优化（Chroma 客户端单例化 + 启动预热） / Docker 部署（Dockerfile + docker-compose）

---

## 📄 许可证

本项目为个人暑假学习项目，仅供学习交流使用。
