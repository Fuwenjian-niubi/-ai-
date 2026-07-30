import { useEffect, useState } from 'react'
import type { ChatMessage, KBOut, SessionOut } from '../types'
import { listKBs } from '../api/kb'
import {
  listSessions,
  createSession,
  deleteSession,
  getMessages,
} from '../api/sessions'
import { askStream } from '../api/qa'
import SessionSidebar from '../components/Chat/SessionSidebar'
import MessageView from '../components/Chat/MessageView'
import Composer from '../components/Chat/Composer'

let seq = 0
const nextId = () => `m${++seq}`

export default function Chat() {
  const [kbs, setKbs] = useState<KBOut[]>([])
  const [kbId, setKbId] = useState<number | null>(null)
  const [sessions, setSessions] = useState<SessionOut[]>([])
  const [activeId, setActiveId] = useState<number | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [loadingKb, setLoadingKb] = useState(true)

  useEffect(() => {
    listKBs()
      .then((data) => {
        setKbs(data)
        if (data.length > 0) setKbId(data[0].id)
      })
      .catch(() => setError('知识库加载失败'))
      .finally(() => setLoadingKb(false))
  }, [])

  useEffect(() => {
    listSessions().then(setSessions).catch(() => {})
  }, [])

  const handleNewSession = async () => {
    const s = await createSession('新对话')
    setSessions((prev) => [s, ...prev])
    setActiveId(s.id)
    setMessages([])
    setError('')
    return s.id
  }

  const handleSelect = async (id: number) => {
    setActiveId(id)
    setError('')
    try {
      const msgs = await getMessages(id)
      setMessages(
        msgs.map((m) => ({
          id: nextId(),
          role: m.role as 'user' | 'assistant',
          content: m.content,
          citations: m.citations,
        })),
      )
    } catch {
      setMessages([])
    }
  }

  const handleDelete = async (id: number) => {
    await deleteSession(id).catch(() => {})
    setSessions((prev) => prev.filter((s) => s.id !== id))
    if (activeId === id) {
      setActiveId(null)
      setMessages([])
    }
  }

  const handleSend = async (text: string) => {
    if (!kbId) {
      setError('请先在右上角选择一个知识库')
      return
    }
    setError('')
    let sid = activeId
    if (sid == null) sid = await handleNewSession()

    const userMsg: ChatMessage = { id: nextId(), role: 'user', content: text }
    const pendingMsg: ChatMessage = {
      id: nextId(),
      role: 'assistant',
      content: '',
      pending: true,
    }
    setMessages((prev) => [...prev, userMsg, pendingMsg])
    setBusy(true)

    const patchAssistant = (patch: Partial<ChatMessage>) =>
      setMessages((prev) =>
        prev.map((m) => (m.id === pendingMsg.id ? { ...m, ...patch } : m)),
      )

    try {
      await askStream(
        kbId,
        text,
        sid,
        {
          onToken: (t) =>
            setMessages((prev) =>
              prev.map((m) =>
                m.id === pendingMsg.id ? { ...m, content: m.content + t } : m,
              ),
            ),
          onDone: (done) => {
            patchAssistant({
              pending: false,
              content: done.answer,
              citations: done.citations,
              skill: done.skill,
              memory_used: done.memory_used,
            })
            // 若为新会话，用首问作为标题
            setSessions((prev) =>
              prev.map((s) =>
                s.id === sid && s.title === '新对话'
                  ? { ...s, title: text.slice(0, 20) }
                  : s,
              ),
            )
          },
          onError: (msg) => {
            setMessages((prev) => prev.filter((m) => m.id !== pendingMsg.id))
            setError(msg || '问答请求失败，请稍后重试')
          },
        },
      )
    } catch (err: any) {
      setMessages((prev) => prev.filter((m) => m.id !== pendingMsg.id))
      setError(err?.message || '问答请求失败，请稍后重试')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="chat-layout">
      <SessionSidebar
        sessions={sessions}
        activeId={activeId}
        onSelect={handleSelect}
        onNew={handleNewSession}
        onDelete={handleDelete}
      />
      <div className="chat-pane">
        <div className="chat-head">
          <select
            className="kb-select"
            value={kbId ?? ''}
            onChange={(e) => setKbId(Number(e.target.value))}
            disabled={loadingKb}
          >
            {loadingKb && <option>加载知识库…</option>}
            {kbs.map((k) => (
              <option key={k.id} value={k.id}>
                {k.name}
              </option>
            ))}
          </select>
          <div className="spacer" />
          {kbs.length === 0 && (
            <span style={{ color: 'var(--muted)', fontSize: 13 }}>
              暂无知识库，请联系管理员创建
            </span>
          )}
        </div>

        <MessageView messages={messages} />

        <Composer onSend={handleSend} disabled={busy || !kbId} />
        {error && (
          <div style={{ padding: '0 20px 10px' }}>
            <div className="alert alert-error">{error}</div>
          </div>
        )}
      </div>
    </div>
  )
}
