"""本机 Agnes API 连通性测试（标准库实现，无第三方依赖）。

分阶段验证：
  1. DNS 解析 + TCP 443 握手（网络层）
  2. HTTPS POST /v1/chat/completions（API 层，带超时）
"""
import json
import os
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# ---- 读取 .env ----
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

if not API_KEY or not BASE_URL:
    print("[FAIL] .env 缺少 AGNES_API_KEY 或 AGNES_BASE_URL")
    sys.exit(1)

URL = BASE_URL + "/chat/completions"
print("=" * 60)
print(f"目标 URL : {URL}")
print(f"模型     : {MODEL}")
print(f"Key 前缀 : {API_KEY[:8]}...{API_KEY[-4:]}")
print("=" * 60)

# ---- 阶段 1：DNS + TCP ----
host = urllib.parse.urlparse(BASE_URL).hostname
print(f"\n[1/2] 网络层：解析 {host} 并 TCP 握手 443 ...")
t0 = time.time()
try:
    addrs = socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
    ip = addrs[0][4][0]
    print(f"      DNS 解析成功 -> {ip}（共 {len(addrs)} 条记录）")
    sock = socket.create_connection((host, 443), timeout=10)
    sock.close()
    print(f"      TCP 443 握手成功（耗时 {time.time()-t0:.2f}s）")
except Exception as e:
    print(f"      [FAIL] 网络层不可达：{type(e).__name__}: {e}")
    sys.exit(1)

# ---- 阶段 2：HTTPS POST ----
print(f"\n[2/2] API 层：POST {URL}（timeout=30s）...")
payload = {
    "model": MODEL,
    "messages": [{"role": "user", "content": "ping，只回复 pong 两个字"}],
    "temperature": 0.1,
    "max_tokens": 16,
    "stream": False,
}
data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(
    URL, data=data, method="POST",
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json",
    },
)
t1 = time.time()
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8", "replace")
        status = resp.status
        elapsed = time.time() - t1
    print(f"      HTTP 状态 : {status}（耗时 {elapsed:.2f}s）")
    try:
        js = json.loads(body)
        content = js.get("choices", [{}])[0].get("message", {}).get("content", "")
        print(f"      模型回复 : {content!r}")
        print(f"      usage    : {js.get('usage')}")
        print("\n[RESULT] Agnes 连通性 OK ✅")
    except json.JSONDecodeError:
        print(f"      [WARN] 响应非 JSON：{body[:300]}")
        print("\n[RESULT] 网络可达但响应异常 ⚠️")
except urllib.error.HTTPError as e:
    detail = e.read().decode("utf-8", "replace")[:500]
    print(f"      [HTTPError] 状态码 {e.code}")
    print(f"      响应体   : {detail}")
    print("\n[RESULT] 已连通但鉴权/参数有误 ❌（检查 key/model）")
except urllib.error.URLError as e:
    print(f"      [FAIL] 连接失败：{type(e.reason).__name__}: {e.reason}")
    print(f"      耗时     : {time.time()-t1:.2f}s")
    print("\n[RESULT] 网络层可达但 API 握手失败 ❌")
except Exception as e:
    print(f"      [FAIL] 未知错误：{type(e).__name__}: {e}")
    print("\n[RESULT] 连通性测试失败 ❌")
