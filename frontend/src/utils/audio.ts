// 录音与音频编码工具：用 MediaRecorder 采集，再转码为 16kHz 单声道 WAV 上传。
// WAV 是更快-whisper 最友好的输入格式，避免浏览器录音格式（webm/ogg）解码依赖问题。

export class Recorder {
  private mr: MediaRecorder | null = null
  private chunks: BlobPart[] = []
  private stream: MediaStream | null = null

  get recording(): boolean {
    return this.mr != null && this.mr.state === 'recording'
  }

  async start(): Promise<void> {
    if (this.recording) return
    this.stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    this.mr = new MediaRecorder(this.stream)
    this.chunks = []
    this.mr.ondataavailable = (e) => {
      if (e.data.size > 0) this.chunks.push(e.data)
    }
    this.mr.start()
  }

  /** 停止录音并返回原始 blob（webm/ogg，具体取决于浏览器）。 */
  stop(): Promise<Blob> {
    return new Promise((resolve, reject) => {
      if (!this.mr) {
        reject(new Error('收音机未启动'))
        return
      }
      this.mr.onstop = async () => {
        const blob = new Blob(this.chunks, { type: this.mr?.mimeType })
        this.stream?.getTracks().forEach((t) => t.stop())
        this.mr = null
        this.stream = null
        resolve(blob)
      }
      this.mr.stop()
    })
  }
}

/** 将任意浏览器录音 blob 转码为 16kHz 单声道 PCM WAV（用于 ASR 上传）。 */
export async function blobToWav(blob: Blob): Promise<Blob> {
  const arr = await blob.arrayBuffer()
  const Ctx =
    window.AudioContext ||
    (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
  const ctx = new Ctx()
  const audioBuf = await ctx.decodeAudioData(arr)

  const targetRate = 16000
  const offline = new OfflineAudioContext(
    1,
    Math.ceil(audioBuf.duration * targetRate),
    targetRate,
  )
  const src = offline.createBufferSource()
  src.buffer = audioBuf
  src.connect(offline.destination)
  src.start()
  const rendered = await offline.startRendering()
  return encodeWav(rendered)
}

function encodeWav(buf: AudioBuffer): Blob {
  const numCh = 1
  const sampleRate = buf.sampleRate
  const samples = buf.getChannelData(0)
  const bytesPerSample = 2
  const blockAlign = numCh * bytesPerSample
  const dataSize = samples.length * bytesPerSample

  const buffer = new ArrayBuffer(44 + dataSize)
  const view = new DataView(buffer)
  let offset = 0
  const writeStr = (s: string) => {
    for (let i = 0; i < s.length; i++) view.setUint8(offset++, s.charCodeAt(i))
  }
  writeStr('RIFF')
  view.setUint32(offset, 36 + dataSize, true)
  offset += 4
  writeStr('WAVE')
  writeStr('fmt ')
  view.setUint32(offset, 16, true)
  offset += 4
  view.setUint16(offset, 1, true) // PCM
  offset += 2
  view.setUint16(offset, numCh, true)
  offset += 2
  view.setUint32(offset, sampleRate, true)
  offset += 4
  view.setUint32(offset, sampleRate * blockAlign, true)
  offset += 4
  view.setUint16(offset, blockAlign, true)
  offset += 2
  view.setUint16(offset, 16, true) // 位深
  offset += 2
  writeStr('data')
  view.setUint32(offset, dataSize, true)
  offset += 4
  for (let i = 0; i < samples.length; i++) {
    let s = Math.max(-1, Math.min(1, samples[i]))
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true)
    offset += 2
  }
  return new Blob([buffer], { type: 'audio/wav' })
}
