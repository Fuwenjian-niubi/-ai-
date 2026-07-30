import { useState, type FormEvent, type KeyboardEvent } from 'react'
import { Recorder, blobToWav } from '../../utils/audio'
import { asr } from '../../api/voice'

export default function Composer({
  onSend,
  disabled,
}: {
  onSend: (text: string) => void
  disabled: boolean
}) {
  const [text, setText] = useState('')
  const [recording, setRecording] = useState(false)
  const [busyMic, setBusyMic] = useState(false)
  const [micError, setMicError] = useState('')
  const recorderRef = useState(() => new Recorder())[0]

  const submit = () => {
    const t = text.trim()
    if (!t || disabled) return
    onSend(t)
    setText('')
  }

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    submit()
  }

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  const toggleRecord = async () => {
    setMicError('')
    if (!recording) {
      try {
        await recorderRef.start()
        setRecording(true)
      } catch {
        setMicError('无法访问麦克风（请检查浏览器权限）')
      }
      return
    }
    // 停止录音 → 转码 → 识别 → 填入输入框
    setRecording(false)
    setBusyMic(true)
    try {
      const raw = await recorderRef.stop()
      const wav = await blobToWav(raw)
      const transcript = await asr(wav)
      if (transcript) {
        setText((prev) => (prev ? prev + transcript : transcript))
      } else {
        setMicError('没听清，请再说一遍')
      }
    } catch (err: any) {
      setMicError(err?.message || '语音识别失败')
    } finally {
      setBusyMic(false)
    }
  }

  return (
    <form className="composer" onSubmit={onSubmit}>
      <div className="row">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="输入关于景点的问题，或点麦克风语音提问，Enter 发送，Shift+Enter 换行"
          disabled={disabled || recording}
        />
        <div className="composer-btns">
          <button
            type="button"
            className={`btn btn-mic ${recording ? 'recording' : ''}`}
            onClick={toggleRecord}
            disabled={disabled || busyMic}
            title={recording ? '点击停止并识别' : '点击开始语音输入'}
          >
            {busyMic ? '识别中…' : recording ? '■ 停止' : '🎤 语音'}
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={disabled || !text.trim()}
          >
            发送
          </button>
        </div>
      </div>
      <div className="hint">
        回答由大模型基于知识库生成，仅供参考；引用来源可点击展开核对。
        {micError && <span className="mic-error"> · {micError}</span>}
      </div>
    </form>
  )
}
