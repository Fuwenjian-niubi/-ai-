"""TTS：edge-tts 在线合成，返回 mp3 字节流。

- 默认音色 zh-CN-XiaoxiaoNeural（中文女声，自然好听）。
- edge-tts 为异步库，路由内直接 await；无需本地模型，但需可直连微软 TTS 服务
  （国内一般可用，失败前端会自动回退到浏览器原生语音）。
"""
import io

DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"


async def synthesize(text: str, voice: str = DEFAULT_VOICE) -> bytes:
    """合成文本为 mp3 字节。edge-tts 在此懒加载，未安装时不拖累整个服务启动。"""
    import edge_tts

    communicate = edge_tts.Communicate(text, voice)
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk.get("type") == "audio":
            buf.write(chunk["data"])
    return buf.getvalue()
