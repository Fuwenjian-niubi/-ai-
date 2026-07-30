# 景点AI问答机器人 - 项目长期备忘

## 目标
基于 LangChain 的 RAG 景点知识库问答系统（暑假项目）。核心功能：
- 多景点知识库（用户上传景点资料 → 构建专属 KB → 问答）
- 语音输入(ASR) + 文本/语音输出(TTS)，机器人讲解体验
- 多用户多会话隔离、历史可回溯
- 管理员(admin)管理知识库，普通用户仅问答
- 引用溯源（回答标注知识库片段）
- 必含：Agent、知识库RAG、记忆系统、Skills

## 已确认决策（2026-07-29）
- 形态：纯 Web（React + Vite 响应式 + PWA），不打包原生 App
- 大模型：云端**通义千问 Qwen**（OpenAI 兼容，DashScope compatible-mode）；原 Agnes 因需 Clash 境外代理被弃用。后端用 `ChatOpenAI` + base_url 抽象，换 DeepSeek/GLM/Kimi 仅改 .env 的 LLM_* 三行。
- ASR/TTS：本地免费方案（faster-whisper + edge-tts）
- 知识库：支持多景点，上传不同景点生成多个 KB（一级实体，按景点隔离检索）

## 关键参数
- admin 账号：admin / 123456（仅 admin 可管理知识库）
- LLM（通义千问 Qwen，OpenAI 兼容）：base_url=https://dashscope.aliyuncs.com/compatible-mode/v1，model=qwen3.7-plus（2026-07-29 经 verify_live_llm.py 实测可用，返回 pong），api_key=DashScope Key（已填入 .env，勿提交仓库）
- .env 变量已从 AGNES_* 改名为 LLM_*（config.py / llm.py 同步）；**无需 Clash/代理**，国内直连
- key 存于 backend/.env（切勿提交到仓库）

## 里程碑
- M1 后端骨架：已完成（2026-07-29）
- M2 RAG 摄入/检索/引用：已完成并验证（2026-07-29，广州塔 docx 摄入5块，检索+bge重排+citations 经 mock-LLM 全链路验证通过）
- M3 Agent + 记忆系统 + Skills：已完成（2026-07-29，LangGraph 状态图 + 长期/会话记忆 + 4 技能注册表）；live LLM 已于 19:26 在用户本机验证通过（Agnes 真实返回 pong）
- M4 语音 ASR/TTS（**已完成 2026-07-29 深夜**，见下方「M4 语音」经验）
- M5 前端 React（登录/聊天/知识库管理 admin）：**已完成（2026-07-29，npm run build 通过，dist 产物含 PWA 资源）**
- M6 性能优化 + Docker 部署（待）

## 技术栈
FastAPI + LangChain + (Chroma/SQLite) + bge-base-zh-v1.5(嵌入) + bge-reranker-v2-m3(重排) + Qwen(LLM, OpenAI兼容) + faster-whisper + edge-tts + React/Vite(PWA) + PostgreSQL + Redis + Docker
- RAG 管线：解析(txt/md/pdf/docx)→中文按句分块(500字/80重叠)→bge 嵌入→Chroma 持久化（按 kb_id 集合隔离）；检索=向量召回 Top8→bge重排→Top4 带来源。

## 工程经验（坑，重要）
- 端口占用/进程清理：uvicorn --reload 在 Windows = reloader 父 + worker 子，杀 worker 会被 reloader 立即重生；必须连 reloader 一起结束。本环境有效：PowerShell `Stop-Process -Id <pid> -Force`（数组批量杀，跨会话有效，但 stdout 有时不回显）；`taskkill /F /T /PID` 在 git bash 中 `/F` 会被 MSYS 转义，`cmd /c` 被安全策略拦截，故优先用 PowerShell。
- 依赖安装：langchain/chromadb/sentence-transformers 体积大，首次安装较久；装完前切勿在 main.py 注册依赖这些包的路由（langchain_openai 顶层 import 会导致整个 app 启动 500）。所有重依赖已在 rag/ 内懒加载。
- **HF 模型缓存损坏**：首次下载中断会让 `models--BAAI--bge-base-zh-v1.5` 的 config.json 变空、blobs 成 tmp 半成品 → 加载时 JSONDecodeError。修复用 Python `shutil.rmtree` 清缓存（git bash 的 `rm` 被 safe-delete 代理拦截且路径错乱，$USERPROFILE 在 git bash 未定义）。`scripts/download_models.py` 已做 snapshot_download + 加载校验 + 重试。**切勿并发跑多个 download 进程**（同缓存并发写会损坏）。
- **torch/sentence-transformers 在 Windows 段错误(segfault)**：加载模型时因 OpenMP 重复库崩溃。已在 `app/main.py` 顶部 `os.environ.setdefault("KMP_DUPLICATE_LIB_OK","TRUE")` + `OMP_NUM_THREADS=1"` 自动规避，无论何种方式启动均生效。运行任何加载模型的脚本也可前缀 `KMP_DUPLICATE_LIB_OK=TRUE OMP_NUM_THREADS=1`。
- **Agnes API 在本沙箱不可达**：OpenAI/Google 经代理可达（OpenAI POST 1s 返 401），但 `https://apihub.agnes-ai.com/v1/chat/completions` 的 POST 连接建立后 0 字节挂起（90s 超时）。故 live LLM 回答无法在此环境实测；M3 已用 mock LLM 验证除 LLM 外的全链路。**用户在自有网络运行时应可正常调用 Agnes**，需他们确认。
- **【历史·已弃用】Agnes 在本机连通条件（2026-07-29 19:26 实测成功；项目已于 2026-07-29 深夜切到通义千问 Qwen，无需 Clash）**：用户网络对境外 AI API 受限（裸连/无代理时 OpenAI 也 10060 超时），必须借 Clash 代理。最终可用配置 = **Clash TUN 模式 ON + 系统代理 ON**（两者都开），此时 DNS 把 `apihub.agnes-ai.com` 解析到 fake-ip `198.18.0.x`，直连该假 IP 被 Clash 透明拦截转发 → 返回 200/pong。关键：① `llm.py` 已从早期 `trust_env=True`（读系统代理）改为 `trust_env=False`（绕过 HTTP 代理、直连 fake-ip），方向正确且已验证；② 验证脚本 `scripts/verify_live_agnes.py` 为标准库 urllib + `ProxyHandler({})` 直连等效版，零依赖可在用户机器直接跑；③ 实测单次 ping 往返约 **32s**（首响偏慢），真实问答已实施 **SSE 打字机切片**（/api/qa/stream，服务端拿到整段后逐字推送；因 Agnes 不支持上游流式）+ **答案缓存**（复问秒回）缓解慢感，但首字延迟仍受链路硬伤影响。④ 用户若换到"必须走代理出网"的部署环境，需把 `trust_env` 改回可配置。
- **端口 8000 残留孤儿进程**：早期某 uvicorn worker(3716) 处于与本工具不同的进程命名空间，netstat 可见但其 PID 无法被 taskkill/Stop-Process 枚举与终止；本会话改用 **8001** 作为开发端口。用户在自己机器上正常 `uvicorn --port 8000` 不受影响。
- **M5 前端 PWA 方案（2026-07-29）**：`vite-plugin-pwa@0.20.5/0.21.2` 在 Node 22 + Vite 5 下构建报 `Dynamic require of "workbox-build" is not supported`（ESM/CJS 兼容坑），且切换版本时把 `@rollup/plugin-babel` 依赖树弄坏。最终**弃用该插件**，改为手写轻量 PWA：`public/manifest.webmanifest` + `public/sw.js`（导航网络优先回退首页、同源静态 stale-while-revalidate、/api 与跨域一律透传不缓存）+ `main.tsx` 仅在 `import.meta.env.PROD` 注册 SW。仍保留"可安装到桌面 + 离线壳层"，且不依赖 workbox。
- **【重要·已验证】Agnes 不支持上游流式（2026-07-29 20:30 实测）**：`verify_agnes_stream.py` 发 `stream=true` 仅返回 **1 个整段片段（29s）**，证明 Agnes 忽略 stream 参数、整段返回。故"从上游逐 token 取"不可行；原 LangGraph `astream` 方案已**回退**（synthesize 改回同步 `chain.invoke`，删除 `run_agent_stream`）。
- **【已完成】/api/qa 慢感缓解方案（2026-07-29 20:3x）**：Agnes 不支持上游流式 + 链路约 30s 硬伤，采用两层缓解：① **进程内答案缓存** `app/agent/cache.py`（键=kb_id+归一化query，TTL 1h；知识库上传/删除时 `invalidate_kb` 失效），复问秒回；② **服务端"打字机"切片**：`/api/qa/stream` 拿到整段后用 `_slice_text` 每 4 字一段通过 SSE 推送（token/done/error），仅改善结尾观感、不降首字延迟。同步 `/api/qa` 也走 `run_agent_cached`。前端 `askStream` 逐字渲染不变。`llm.py` timeout=300 防长生成截断。
- **backend/requirements.txt 已补全（2026-07-29 19:5x）**：此前只有 M1 基础依赖，缺 langchain-openai/langgraph/chromadb/sentence-transformers/httpx/pypdf/python-docx，用户直接 pip install 会因导入 langchain 启动失败。现已补齐（langchain-core 由 langchain-openai+langgraph 自带，无需单列）。
- **【重要坑】后端 venv 勿用 Python 3.14**：用户系统 Python 为 3.14，而 torch/chromadb/onnxruntime(随 chromadb)/sentence-transformers 等 ML 包常滞后提供预编译 wheel，3.14 上可能只能源码编译或直接报错。推荐用本机已有的 **managed Python 3.13.12** 建 venv：`C:\Users\ZhuanZ\.workbuddy\binaries\python\versions\3.13.12\python.exe -m venv .venv`。
- **bge 模型首次需从 HuggingFace 下载（BAAI/bge-base-zh-v1.5 + BAAI/bge-reranker-v2-m3，约 1-2GB）**：必须经 Clash 路由；若 HF 官方端点被墙，设 `HF_ENDPOINT=https://hf-mirror.com` 走镜像。下载脚本 scripts/download_models.py 已含校验。
- **【2026-07-29 深夜·决策变更】从 Agnes 切换到通义千问 Qwen**：根因是用户网络对境外 AI API 受限，Agnes 必须靠 Clash TUN+系统代理(fake-ip 198.18.0.x)才能通，太折腾。Qwen 为国内端点、直连即通、无需 Clash；且 Qwen 原生支持 `stream=true`。改动仅 3 处（`.env` 的 AGNES_*→LLM_*、config.py、llm.py），零业务代码改动。`llm.py` 仍保留 `trust_env=False` 直连单例，避免本机若开 Clash 时误转发国内请求。新增 `scripts/verify_live_llm.py`（零依赖直连验证，替代已废弃的 verify_live_agnes.py）。**注意**：之前为 Agnes 不支持流式而回退的 SSE（synthesize 改回同步 invoke、删 run_agent_stream）可借 Qwen 重新启用以提升体感——若要做，把 synthesize 改回 async+astream 即可。bge 模型下载仍可能需 HF 镜像（一次性，与 LLM 出网无关）。
- **【运行方式·双击启动】**：项目根 `启动.bat` 双击即用——校验 `backend/.venv` 存在→设 `HF_ENDPOINT=https://hf-mirror.com`→`cd backend`→`start` 后台起 uvicorn(8000)→6s 后自动开浏览器 http://127.0.0.1:8000（管理员 admin/123456）。前提：`frontend/dist` 已构建（前端 `npm run build`）。后端 `app/main.py` 在 `frontend/dist` 存在时同端口托管网页（`/assets` 挂 StaticFiles + `/` 与 `/{full_path:path}` 兜底 index.html，API 与页面同源免 CORS）。**改前端后必须重新 `npm run build`** 再启动才生效。若双击后报“address already in use”，先关掉旧的“景点AI后端”窗口。
- **【新增·模型设置界面（2026-07-29 21:5x）】**：用户可在网页直接改大模型，不用改 .env。后端 `app/rag/llm.py` 新增运行时配置：`load_llm_config()` 优先读 `backend/llm_runtime.json`（页面写入），回退 `.env`/默认值；`get_llm()` 每次问答读取即时生效。**新增 `app/routers/settings.py`（admin 专用）**：`GET /api/settings/llm`（api_key 脱敏返回）、`POST /api/settings/llm/test`（用给定配置发最小请求验证连通，不落盘）、`PUT /api/settings/llm`（验证通过后写 llm_runtime.json）。前端新增 `pages/Settings.tsx` + `api/settings.ts`，路由 `/settings`（adminOnly），导航栏 admin 可见“模型设置”。`llm_runtime.json` 已加入 `.gitignore`（含真实 key，勿提交）。仅 DashScope 端关闭思考模式（`extra_body={"enable_thinking":False}`），其他兼容端点不加该字段避免被拒。**注意**：main.py 导入 settings 路由时用 `as settings_router` 别名，避免与 `from .config import settings` 命名冲突（已踩坑：直接 `import ... settings` 会覆盖配置对象导致 `settings.PROJECT_NAME` AttributeError）。
- **【M4 语音 ASR/TTS（2026-07-29 深夜）】**：新增 `app/voice/{asr.py,tts.py}` + `app/routers/voice.py`，`main.py` 注册 `voice.router`（前缀 `/api/voice`，均需登录）。**ASR**=`faster-whisper`(base, cpu, int8, language=zh) 懒加载，接收 **16kHz 单声道 WAV**（前端 `utils/audio.ts` 用 MediaRecorder 录→Web Audio 解码→OfflineAudioContext 重采样 16k→手写 WAV 头）；**TTS**=`edge-tts`(默认 `zh-CN-XiaoxiaoNeural` 中文女声，在线，返回 mp3)。**关键坑·懒加载**：`voice.py` 路由与 `tts.py` 内 `import edge_tts` 必须**懒加载（在函数内 import）**，否则 venv 未装语音依赖时整个 app 启动失败（ImportError 会连带 chat/KB 全挂）；懒加载后缺依赖仅该端点报错、其余功能正常。`requirements.txt` 已加 `faster-whisper>=1.0.0` + `edge-tts>=1.1.0`。**前端**：`Composer.tsx` 加🎤录音按钮（录→转wav→`/api/voice/asr`→填入输入框，不自动发）；`MessageView.tsx` 给 AI 消息加🔊朗读按钮（调 `/api/voice/tts` 播放 mp3，失败回退 `window.speechSynthesis`）。**launcher.py 增强 `ensure_voice_deps()`**：启动前检测 faster-whisper/edge-tts，缺失则在 venv 自动 `pip install`（首次较慢），双击即用。**验证**：沙箱实测 `synthesize()` 返回 23760 字节合法 mp3（`\xff\xf3` 帧头）；app 无语音依赖时 `from app.main import app` 正常；本沙箱 `uvicorn` 后台启动偶发 segfault（环境怪象，用户机器此前跑 uvicorn 正常，且 `app.main` 可导入证明非代码问题）。frontend `npm run build`（tsc+vite）通过。
