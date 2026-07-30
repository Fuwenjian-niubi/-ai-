import json
from pathlib import Path

import httpx
from langchain_openai import ChatOpenAI

from app.config import settings

# 国内大模型（通义千问 Qwen 等）走直连即可，无需 Clash / 代理。
# 强制 trust_env=False：绕过本机系统代理，避免万一开着 Clash 时把国内请求
# 误转发到境外导致超时。直连国内端点才是最快路径。
_NO_PROXY_CLIENT = httpx.Client(trust_env=False)

# 运行时 LLM 配置：设置界面会把用户的选择写入此文件，优先于 .env。
# 路径：backend/app/rag/llm.py -> backend/
LLM_RUNTIME_PATH = Path(__file__).resolve().parent.parent.parent / "llm_runtime.json"


def load_llm_config() -> dict:
    """读取当前生效的 LLM 配置。

    优先使用 llm_runtime.json（页面设置写入）；若不存在或解析失败，
    则回退到 .env / 默认值。每次问答都会读取，故页面保存后即时生效。
    """
    if LLM_RUNTIME_PATH.exists():
        try:
            data = json.loads(LLM_RUNTIME_PATH.read_text(encoding="utf-8"))
            return {
                "api_key": data.get("api_key", settings.LLM_API_KEY),
                "base_url": data.get("base_url", settings.LLM_BASE_URL),
                "model": data.get("model", settings.LLM_MODEL),
                "max_tokens": data.get("max_tokens", settings.LLM_MAX_TOKENS),
            }
        except Exception:
            pass
    return {
        "api_key": settings.LLM_API_KEY,
        "base_url": settings.LLM_BASE_URL,
        "model": settings.LLM_MODEL,
        "max_tokens": settings.LLM_MAX_TOKENS,
    }


def save_llm_config(cfg: dict) -> None:
    """将 LLM 配置落盘到 llm_runtime.json（含 api_key，注意不要提交到仓库）。"""
    LLM_RUNTIME_PATH.write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_llm(streaming: bool = False):
    """OpenAI 兼容聊天模型（通义千问 Qwen，可换 DeepSeek / 智谱 GLM / Kimi）。

    配置来源：运行时 llm_runtime.json > .env/默认值（见 load_llm_config）。

    设置超时与重试：避免远端不可达时 worker 无限挂起（生产健壮性）。
    强制 trust_env=False：绕过系统代理，直连国内大模型端点。
    streaming=True：开启 token 级流式（SSE 逐字输出用，Qwen 原生支持）。

    extra_body["enable_thinking"]=False：仅对 DashScope(Qwen3) 关闭思考模式，
    否则模型先吐约 6~7 秒推理 token（空 content）再出答案，流式体感尽失。
    其他兼容端点不加该字段，避免被严格校验的服务端拒绝。
    """
    cfg = load_llm_config()
    kwargs = dict(
        model=cfg["model"],
        api_key=cfg["api_key"],
        base_url=cfg["base_url"],
        temperature=0.3,
        max_tokens=cfg["max_tokens"],
        timeout=300,
        max_retries=2,
        streaming=streaming,
        http_client=_NO_PROXY_CLIENT,
    )
    if "dashscope" in cfg["base_url"]:
        kwargs["extra_body"] = {"enable_thinking": False}
    return ChatOpenAI(**kwargs)
