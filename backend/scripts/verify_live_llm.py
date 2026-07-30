r"""
验证「任意 OpenAI 兼容大模型」连通性（通义千问 Qwen / DeepSeek / GLM / Kimi 等）。

用法（在 backend/ 目录下，用系统 Python 即可，无需安装依赖）：
    python scripts/verify_live_llm.py

它会读取 backend/.env 里的 LLM_BASE_URL / LLM_API_KEY / LLM_MODEL，
向 `{LLM_BASE_URL}/chat/completions` 发一个最小请求，并打印耗时与回复。

设计要点：
- 直连（ProxyHandler({}) 绕过系统代理），国内大模型应直连；
  若你本机开着 Clash，直连反而最快、不会被误转发到境外。
- 零第三方依赖，标准库 urllib 实现，避免 venv 未装好时跑不起来。
"""
import json
import os
import time
import urllib.request
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def load_env(path: Path) -> dict:
    """极简 .env 解析（仅支持 KEY=VALUE，忽略注释与空行）。"""
    env = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        env[key.strip()] = val.strip().strip('"').strip("'")
    return env


def main() -> None:
    env = load_env(ENV_PATH)
    base_url = env.get("LLM_BASE_URL", "").rstrip("/")
    api_key = env.get("LLM_API_KEY", "")
    model = env.get("LLM_MODEL", "")

    print(f"[INFO] LLM_BASE_URL = {base_url}")
    print(f"[INFO] LLM_MODEL    = {model}")
    if not base_url or not api_key or not model:
        print("[ERROR] .env 缺少 LLM_BASE_URL / LLM_API_KEY / LLM_MODEL，请先填写。")
        return
    if "REPLACE_WITH" in api_key:
        print("[ERROR] LLM_API_KEY 还是占位符，请填入真实 DashScope Key。")
        return

    url = f"{base_url}/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "ping，只回复 pong 两个字"}],
        "max_tokens": 16,
        "temperature": 0,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    print(f"[INFO] POST {url} （直连，绕过系统代理）")
    t0 = time.time()
    try:
        # ProxyHandler({}) => 不使用任何代理，直连大模型端点
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        elapsed = time.time() - t0
        content = body["choices"][0]["message"]["content"]
        print(f"[OK] 耗时 {elapsed:.2f}s，模型回复：{content!r}")
        print("[OK] 大模型连通正常 ✅")
    except urllib.error.HTTPError as e:
        elapsed = time.time() - t0
        detail = e.read().decode("utf-8", errors="replace")[:300]
        print(f"[FAIL] HTTP {e.code}（{elapsed:.2f}s）：{detail}")
        print("[TIP] 401=Key 错误；404=base_url/model 不对；检查 .env。")
    except Exception as e:  # noqa: BLE001
        elapsed = time.time() - t0
        print(f"[FAIL] {type(e).__name__}（{elapsed:.2f}s）：{e}")
        print("[TIP] 超时多为网络问题：确认端点为国内地址、本机未强制走 Clash 转发。")


if __name__ == "__main__":
    main()
