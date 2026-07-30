"""ASR：本地 faster-whisper 将语音转为中文文本。

设计要点：
- 模型懒加载（首次调用时下载/加载 base 模型，约 140MB），并用 lru_cache 单例复用。
- CPU + int8 推理，Windows 无 GPU 也能跑；中文固定 language="zh"。
- 入参为 wav 字节（前端已转码为 16kHz 单声道 PCM），faster-whisper 原生支持读取。
"""
import os
import tempfile
from functools import lru_cache

# 模型尺寸：base（快、够用）可经环境变量切到 small（更准、更慢）。
_WHISPER_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "base")


@lru_cache(maxsize=1)
def _whisper_model():
    from faster_whisper import WhisperModel

    # device="cpu" + compute_type="int8" 兼容绝大多数机器，无需 CUDA。
    return WhisperModel(_WHISPER_SIZE, device="cpu", compute_type="int8")


def transcribe_wav(data: bytes) -> str:
    """接收 wav 字节流，返回识别文本（中文）。"""
    model = _whisper_model()
    fd, path = tempfile.mkstemp(suffix=".wav")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        segments, _info = model.transcribe(path, language="zh", beam_size=5)
        return "".join(s.text for s in segments).strip()
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
