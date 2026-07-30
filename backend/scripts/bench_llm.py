"""Benchmark Qwen latency (non-stream total vs stream time-to-first-token).

Reads LLM_* from backend/.env (simple parse, no langchain needed).
"""
import json
import os
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = os.path.join(ROOT, ".env")

cfg = {"LLM_API_KEY": "", "LLM_BASE_URL": "", "LLM_MODEL": "qwen-plus"}
with open(ENV, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k in cfg:
            cfg[k] = v

KEY = cfg["LLM_API_KEY"]
BASE = cfg["LLM_BASE_URL"].rstrip("/")
MODEL = cfg["LLM_MODEL"]
URL = f"{BASE}/chat/completions"

if not KEY or "REPLACE" in KEY:
    print("[ERROR] LLM_API_KEY not set in .env")
    raise SystemExit(1)

messages = [
    {
        "role": "system",
        "content": "你是专业的景点讲解助手。请严格仅基于知识库内容回答。"
        "【知识库内容】广州塔又称小蛮腰，塔高600米，是中国第一高塔、世界第二高塔，"
        "位于广州市海珠区赤岗塔附近。塔身由钢结构网格构成，夜晚有彩色灯光秀。",
    },
    {"role": "user", "content": "广州塔有多高？有什么特色？"},
]


_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def post(payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {KEY}",
        },
        method="POST",
    )
    return _opener.open(req, timeout=60)


print(f"Model={MODEL}  Endpoint={BASE}")

# 1) Non-stream total time
t0 = time.time()
with post({"model": MODEL, "messages": messages, "max_tokens": 400}) as resp:
    body = json.loads(resp.read().decode("utf-8"))
total = time.time() - t0
ans = body["choices"][0]["message"]["content"]
print(f"[non-stream] total={total:.2f}s  answer_len={len(ans)}  answer={ans[:40]!r}")

# 2) Stream time-to-first-token + total
t0 = time.time()
first = None
buf = b""
full = ""
try:
    with post({"model": MODEL, "messages": messages, "max_tokens": 400, "stream": True}) as resp:
        while True:
            chunk = resp.read(1)
            if not chunk:
                break
            buf += chunk
            if b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                line = line.strip()
                if not line or not line.startswith(b"data:"):
                    continue
                data = line[5:].strip()
                if data == b"[DONE]":
                    break
                try:
                    obj = json.loads(data)
                except Exception:
                    continue
                parts = obj.get("choices", [{}])
                if not parts:
                    continue
                delta = parts[0].get("delta", {}).get("content")
                if delta:
                    if first is None:
                        first = time.time() - t0
                    full += delta
except Exception as e:
    print(f"[stream] error: {e}")
total2 = time.time() - t0
print(f"[stream] time_to_first_token={first:.2f}s  total={total2:.2f}s  answer_len={len(full)}")

print("\nConclusion:")
print(f"  - Without streaming you wait {total:.1f}s seeing nothing.")
print(f"  - With streaming the first character appears in {first:.1f}s." if first else "  - stream failed")
