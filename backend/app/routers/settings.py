"""全局设置接口（管理员专用）。

当前提供「大模型（LLM）配置」的查看 / 测试 / 保存：
- GET  /api/settings/llm   -> 返回当前生效配置（api_key 脱敏）
- POST /api/settings/llm/test -> 用给定配置发一次最小请求验证连通，不落盘
- PUT  /api/settings/llm   -> 验证通过后写入 llm_runtime.json，后续问答即时生效

所有端点要求管理员权限（require_admin）。
"""
import httpx
from fastapi import APIRouter, Depends, HTTPException
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from ..config import settings
from ..deps import require_admin
from ..rag.llm import LLM_RUNTIME_PATH, load_llm_config, save_llm_config

router = APIRouter(prefix="/api/settings", tags=["settings"])


class LLMConfigIn(BaseModel):
    base_url: str
    api_key: str = ""  # 可选：留空表示沿用已保存的 key
    model: str


def _mask_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "****"
    return key[:4] + "****" + key[-4:]


def _resolve(payload: LLMConfigIn) -> tuple[str, str, str]:
    """解析出本次要用的 (base_url, api_key, model)，api_key 留空时回退到已保存值。"""
    cfg = load_llm_config()
    key = payload.api_key or cfg["api_key"]
    if not key:
        raise HTTPException(status_code=400, detail="缺少 API Key，请填写后重试")
    if not payload.base_url.strip():
        raise HTTPException(status_code=400, detail="请填写接口地址 Base URL")
    if not payload.model.strip():
        raise HTTPException(status_code=400, detail="请填写模型名称 Model")
    return payload.base_url.strip(), key, payload.model.strip()


def _test_connection(base_url: str, api_key: str, model: str) -> None:
    """发起一次最小 chat/completions 调用验证配置可用；失败抛 HTTPException。"""
    client = ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=0,
        max_tokens=16,
        timeout=30,
        max_retries=1,
        http_client=httpx.Client(trust_env=False),
        **({"extra_body": {"enable_thinking": False}} if "dashscope" in base_url else {}),
    )
    try:
        out = client.invoke([("human", "请只回复 pong")])
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"连接测试失败：{e}")
    content = getattr(out, "content", "") or ""
    if not content.strip():
        raise HTTPException(status_code=400, detail="连接测试失败：模型返回为空")


@router.get("/llm")
def get_llm_settings(_admin=Depends(require_admin)):
    cfg = load_llm_config()
    return {
        "base_url": cfg["base_url"],
        "model": cfg["model"],
        "api_key": _mask_key(cfg["api_key"]),
        "has_key": bool(cfg["api_key"]),
    }


@router.post("/llm/test")
def test_llm_settings(payload: LLMConfigIn, _admin=Depends(require_admin)):
    base_url, api_key, model = _resolve(payload)
    _test_connection(base_url, api_key, model)
    return {"ok": True, "message": "连接成功"}


@router.put("/llm")
def update_llm_settings(payload: LLMConfigIn, _admin=Depends(require_admin)):
    base_url, api_key, model = _resolve(payload)
    _test_connection(base_url, api_key, model)
    # 落盘：api_key 留空时保留已保存的 key
    save_llm_config(
        {
            "base_url": base_url,
            "api_key": api_key,
            "model": model,
            "max_tokens": settings.LLM_MAX_TOKENS,
        }
    )
    return {"ok": True, "message": "已保存并生效"}
