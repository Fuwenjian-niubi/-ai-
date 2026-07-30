#!/usr/bin/env python3
r"""Agnes 流式(stream)支持探测 —— 标准库直连（等效 llm.py trust_env=False）。

用法（你本机，无需安装任何第三方包）：
  & "C:\Users\ZhuanZ\AppData\Local\Programs\Python\Python314\python.exe" \
      "c:/Users/ZhuanZ/Desktop/暑假项目ai景点讲解/backend/scripts/verify_agnes_stream.py"

它会用 stream=true 发起请求，统计收到的 SSE 片段数与首 token 延迟：
 - [OK] 收到多个流式片段 => Agnes 支持流式，前端 SSE 改造可用。
 - [WARN] 仅 1 个（整体）   => Agnes 可能不支持流式，需回退同步方案。
"""
import json
import os
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def load_env() -> dict:
    env: dict = {}
    env_path = os.path.join(HERE, "..", ".env")
    try:
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return env


def main() -> None:
    env = load_env()
    base = env.get("AGNES_BASE_URL", "https://apihub.agnes-ai.com/v1").rstrip("/")
    url = base + "/chat/completions"
    model = env.get("AGNES_MODEL", "agnes-2.0-flash")
    key = env.get("AGNES_API_KEY", "")

    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 32,
        "stream": True,
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {key}")

    # 强制直连：清空代理（等效 trust_env=False）。
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    print(f"POST {url}")
    print(f"MODEL: {model}")
    t0 = time.time()
    count = 0
    first_tok_t = None
    try:
        with opener.open(req, timeout=120) as resp:
            for raw in resp:
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                data = line[len("data:"):].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                except Exception:
                    continue
                try:
                    delta = obj["choices"][0]["delta"].get("content")
                except Exception:
                    delta = None
                if delta:
                    count += 1
                    if first_tok_t is None:
                        first_tok_t = time.time() - t0
        el = time.time() - t0
        if count >= 2:
            print(f"[OK] 收到 {count} 个流式片段，首 token 延迟 ~{first_tok_t:.2f}s，总耗时 {el:.2f}s")
            print("=> Agnes 支持流式，前端 SSE 改造可用 ✅")
        else:
            print(f"[WARN] 仅收到 {count} 个流式片段，总耗时 {el:.2f}s")
            print("=> Agnes 可能不支持流式，建议回退同步方案")
    except Exception as e:
        print(f"[FAIL] {type(e).__name__}: {e}")
        print("=> 请先确认 Agnes 直连可达（verify_live_agnes.py）")


if __name__ == "__main__":
    main()
