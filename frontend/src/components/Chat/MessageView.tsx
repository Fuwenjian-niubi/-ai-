import { useEffect, useRef, useState } from 'react'
import type { ChatMessage } from '../../types'
import { tts } from '../../api/voice'

const SKILL_LABELS: Record<string, string> = {
  knowledge_qa: '景点问答',
  nearby_recommend: '周边推荐',
  general_chat: '通用对话',
  daily_chat: '日常对话',
  clarify: '澄清反问',
}

function MessageRow({ m }: { m: ChatMessage }) {
  const isUser = m.role === 'user'
  const skillLabel = m.skill ? SKILL_LABELS[m.skill] || m.skill : ''
  // 日常寒暄不显示“记忆”标签，避免把历史问候记忆刷屏
  const memoryList = m.skill !== 'daily_chat' ? m.memory_used || [] : []
  const [speaking, setSpeaking] = useState(false)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  const toggleSpeak = async () => {
    const text = m.content?.trim()
    if (!text) return
    // 已在播放 → 停止
    if (speaking) {
      audioRef.current?.pause()
      audioRef.current = null
      if (typeof window.speechSynthesis !== 'undefined') window.speechSynthesis.cancel()
      setSpeaking(false)
      return
    }
    setSpeaking(true)
    try {
      const url = await tts(text)
      const audio = new Audio(url)
      audioRef.current = audio
      audio.onended = () => {
        setSpeaking(false)
        audioRef.current = null
      }
      await audio.play()
    } catch {
      // 后端 TTS 不可用（如网络受限）→ 回退浏览器原生语音
      try {
        const u = new SpeechSynthesisUtterance(text)
        u.lang = 'zh-CN'
        u.onend = () => setSpeaking(false)
        window.speechSynthesis.cancel()
        window.speechSynthesis.speak(u)
      } catch {
        setSpeaking(false)
      }
    }
  }

  return (
    <div className={`msg ${m.role}`}>
      <div className="avatar">{isUser ? '我' : 'AI'}</div>
      <div className="bubble">
        {m.pending ? (m.content ? m.content : '思考中…') : m.content || '(无内容)'}

        {!isUser && !m.pending && m.content && (
          <button
            type="button"
            className={`btn-speak ${speaking ? 'speaking' : ''}`}
            onClick={toggleSpeak}
            title={speaking ? '停止朗读' : '朗读此回答'}
          >
            {speaking ? '🔇 停止' : '🔊 朗读'}
          </button>
        )}


        {!isUser && skillLabel && (
          <div className="meta-row">
            <span className="chip skill">技能：{skillLabel}</span>
          </div>
        )}

        {!isUser && memoryList.length > 0 && (
          <div className="meta-row">
            {memoryList.map((x, i) => (
              <span key={i} className="chip">
                记忆：{x}
              </span>
            ))}
          </div>
        )}

        {!isUser && m.citations && m.citations.length > 0 && (
          <details className="citations">
            <summary>引用来源（{m.citations.length}）</summary>
            {m.citations.map((c) => (
              <div className="citation-item" key={c.index}>
                <div className="src">
                  [{c.index}] {c.source || '知识库片段'}
                </div>
                <div>{c.content}</div>
              </div>
            ))}
          </details>
        )}
      </div>
    </div>
  )
}

export default function MessageView({ messages }: { messages: ChatMessage[] }) {
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (messages.length === 0) {
    return (
      <div className="chat-body">
        <div className="empty-state">
          <img src="/icon.svg" width={64} height={64} alt="" />
          <h2>开始你的景点问答</h2>
          <p>在下方输入问题，AI 将基于所选知识库作答，并标注引用来源。</p>
        </div>
      </div>
    )
  }

  return (
    <div className="chat-body">
      {messages.map((m) => (
        <MessageRow key={m.id} m={m} />
      ))}
      <div ref={endRef} />
    </div>
  )
}
