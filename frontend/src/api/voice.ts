// 语音接口：ASR（录音→文本）与 TTS（文本→音频 URL）

const token = () => localStorage.getItem('token') || ''

/** 上传 wav 音频，返回识别文本。 */
export async function asr(blob: Blob): Promise<string> {
  const form = new FormData()
  form.append('file', blob, 'audio.wav')
  const resp = await fetch('/api/voice/asr', {
    method: 'POST',
    headers: token() ? { Authorization: `Bearer ${token()}` } : {},
    body: form,
  })
  if (!resp.ok) {
    let msg = `语音识别失败 (${resp.status})`
    try {
      const d = await resp.json()
      if (d.detail) msg = d.detail
    } catch {
      /* ignore */
    }
    throw new Error(msg)
  }
  const data = await resp.json()
  return (data.text as string) || ''
}

/** 合成文本为音频，返回可播放的 object URL（mp3）。 */
export async function tts(text: string, voice?: string): Promise<string> {
  const resp = await fetch('/api/voice/tts', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token() ? { Authorization: `Bearer ${token()}` } : {}),
    },
    body: JSON.stringify({ text, voice }),
  })
  if (!resp.ok) {
    let msg = `语音合成失败 (${resp.status})`
    try {
      const d = await resp.json()
      if (d.detail) msg = d.detail
    } catch {
      /* ignore */
    }
    throw new Error(msg)
  }
  const blob = await resp.blob()
  return URL.createObjectURL(blob)
}
