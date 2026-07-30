"""语音路由：ASR（语音→文本）与 TTS（文本→语音），均需登录。"""
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response

from ..deps import get_current_user
from ..models import User

router = APIRouter(prefix="/api/voice", tags=["voice"])


@router.post("/asr")
async def asr(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """接收 wav 音频，返回识别文本。前端负责把录音转码为 16kHz 单声道 wav。"""
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="空音频")
    from ..voice.asr import transcribe_wav

    try:
        text = transcribe_wav(data)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"语音识别失败：{e}")
    return {"text": text}


@router.post("/tts")
async def tts(
    payload: dict[str, Any],
    user: User = Depends(get_current_user),
):
    """接收文本，返回 mp3 音频流。可选 voice 指定音色。"""
    text = (payload.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text 不能为空")
    if len(text) > 2000:
        text = text[:2000]  # edge-tts 单次不宜过长，超长截断
    voice = payload.get("voice") or "zh-CN-XiaoxiaoNeural"
    from ..voice.tts import synthesize

    try:
        audio = await synthesize(text, voice)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"语音合成失败：{e}")
    return Response(content=audio, media_type="audio/mpeg")
