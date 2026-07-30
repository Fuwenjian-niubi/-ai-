"""Agnes 真实调用验证（零第三方依赖，标准库实现）。

用 urllib 强制直连（ProxyHandler({})，等效 llm.py 的 trust_env=False）调用 Agnes。
前置条件：本机 Clash/代理已接管 DNS（域名解析到 198.18.0.x fake-ip），
直连该 fake-ip 会被代理透明转发到真实 Agnes。
无需安装 langchain 即可在本机运行；运行前请开启 Clash『系统代理』或『TUN 模式』。
"""
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_env(path):
    cfg = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip().strip('"').strip("'")
    return cfg


cfg = load_env(os.path.join(BACKEND_ROOT, ".env"))
KEY = cfg.get("AGNES_API_KEY", "")
BASE = cfg.get("AGNES_BASE_URL", "").rstrip("/")
MODEL = cfg.get("AGNES_MODEL", "agnes-2.0-flash")
URL = BASE + "/chat/completions"

print("=" * 56)
print("Agnes LIVE 验证（标准库直连，等效 llm.py trust_env=False）")
print(f"URL: {URL}")
print(f"MODEL: {MODEL}")
print("=" * 56)

if not KEY or not BASE:
    print("[FAIL] .env 缺少 AGNES_API_KEY / AGNES_BASE_URL")
    sys.exit(1)

# ---- DNS 诊断 ----
host = urllib.parse.urlparse(URL).hostname
try:
    ips = sorted({a[4][0] for a in socket.getaddrinfo(host, 443)})
    print(f"DNS 解析 {host} -> {ips}")
    fake = any(ip.startswith("198.18.") for ip in ips)
    if fake:
        print("[OK] 解析到 Clash fake-ip(198.18.0.x)，DNS 已被代理接管 ✅")
    else:
        print("[提示] 解析到的不是 198.18.0.x fake-ip —— Clash 未接管 DNS。")
        print("       请先打开 Clash 并开启『系统代理』或『TUN 模式』，再重跑本脚本。")
except Exception as e:
    print(f"DNS 解析异常: {type(e).__name__}: {e}")

# ---- 直连请求 ----
payload = {
    "model": MODEL,
    "messages": [{"role": "user", "content": "只回复 pong 两个字，不要多余内容"}],
    "max_tokens": 16,
    "stream": False,
}
data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(
    URL, data=data, method="POST",
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {KEY}"},
)
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # 强制直连

t0 = time.time()
try:
    resp = opener.open(req, timeout=40)
    body = resp.read().decode("utf-8", "replace")
    el = time.time() - t0
    try:
        js = json.loads(body)
        content = js.get("choices", [{}])[0].get("message", {}).get("content", "")
        print(f"[OK] HTTP {resp.status} 耗时 {el:.2f}s")
        print(f"     模型回复: {content!r}")
        if content and "pong" in content.lower():
            print("\n[RESULT] Agnes 真实调用成功 ✅（后端 LLM 直连方案可行）")
        else:
            print("\n[RESULT] 收到响应但内容异常，请检查 ⚠️")
    except Exception:
        print(f"[WARN] 非 JSON 响应（耗时 {el:.2f}s）: {body[:200]}")
except urllib.error.HTTPError as e:
    print(f"[FAIL] HTTPError {e.code}（耗时 {time.time()-t0:.2f}s）: {e.read().decode('utf-8','replace')[:200]}")
    sys.exit(1)
except Exception as e:
    print(f"[FAIL] 调用失败（耗时 {time.time()-t0:.2f}s）: {type(e).__name__}: {e}")
    print("\n[RESULT] 仍不可达 ❌ —— 请确认 Clash 已开启并接管 DNS（系统代理/TUN）")
    sys.exit(1)
