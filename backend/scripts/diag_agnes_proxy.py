"""Agnes 连通性诊断：区分「走系统代理」与「直连」，并以 OpenAI 作对照。

目的：定位超时是 Agnes 服务端问题，还是本机代理(127.0.0.1:7890)路由问题。
"""
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")


def load_env(path):
    cfg = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip().strip('"').strip("'")
    return cfg


cfg = load_env(ENV_PATH)
API_KEY = cfg.get("AGNES_API_KEY", "")
BASE_URL = cfg.get("AGNES_BASE_URL", "").rstrip("/")
MODEL = cfg.get("AGNES_MODEL", "agnes-2.0-flash")
AGNES_URL = BASE_URL + "/chat/completions"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

print("=" * 64)
print("代理环境变量：")
print(f"  HTTP_PROXY  = {os.environ.get('HTTP_PROXY', '(空)')}")
print(f"  HTTPS_PROXY = {os.environ.get('HTTPS_PROXY', '(空)')}")
print(f"  NO_PROXY    = {os.environ.get('NO_PROXY', '(空)')}")
print("=" * 64)


def post(url, key, model, use_proxy, timeout=25):
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "reply with pong only"}],
        "max_tokens": 8,
        "stream": False,
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    }
    if use_proxy:
        opener = urllib.request.build_opener()  # 默认读环境变量代理
    else:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # 强制直连

    req = urllib.request.Request(url, data=data, method="POST", headers=headers)
    t0 = time.time()
    try:
        resp = opener.open(req, timeout=timeout)
        body = resp.read().decode("utf-8", "replace")
        elapsed = time.time() - t0
        try:
            js = json.loads(body)
            content = js.get("choices", [{}])[0].get("message", {}).get("content", "")
            return (resp.status, f"OK content={content!r}", elapsed)
        except Exception:
            return (resp.status, f"non-JSON: {body[:120]}", elapsed)
    except urllib.error.HTTPError as e:
        return (e.code, f"HTTPError {e.read().decode('utf-8','replace')[:200]}", time.time() - t0)
    except Exception as e:
        return (None, f"{type(e).__name__}: {e}", time.time() - t0)


def dns(host):
    try:
        return socket.getaddrinfo(host, 443)[0][4][0]
    except Exception as e:
        return f"<fail {e}>"


tests = [
    ("Agnes  [走代理]", AGNES_URL, API_KEY, MODEL, True),
    ("Agnes  [直连 ]", AGNES_URL, API_KEY, MODEL, False),
    ("OpenAI [走代理]", OPENAI_URL, "sk-fake-for-control", "gpt-4o-mini", True),
    ("OpenAI [直连 ]", OPENAI_URL, "sk-fake-for-control", "gpt-4o-mini", False),
]

for name, url, key, model, use_proxy in tests:
    host = urllib.parse.urlparse(url).hostname
    ip = dns(host)
    print(f"\n--- {name} ---  ({host} -> {ip})")
    status, msg, el = post(url, key, model, use_proxy)
    print(f"    [{ 'proxy' if use_proxy else 'direct'}] status={status} 耗时={el:.2f}s")
    print(f"    {msg}")

print("\n" + "=" * 64)
print("判读：")
print(" - 若『走代理』超时而『直连』成功 => Agnes 需绕过代理直连")
print(" - 若两者都超时            => 本机网络确实不可达 Agnes（需换网络/确认服务状态）")
print(" - OpenAI 对照用于确认代理本身是否工作")
print("=" * 64)
