import api from './client'
import type { QAResponse, SkillInfo } from '../types'

export const ask = (kbId: number, question: string, sessionId?: number) =>
  api
    .post<QAResponse>('/qa', { kb_id: kbId, question, session_id: sessionId })
    .then((r) => r.data)

export const listSkills = () =>
  api.get<{ skills: SkillInfo[] }>('/qa/skills').then((r) => r.data)

/** SSE 流式问答的处理器。 */
export interface StreamHandlers {
  onToken: (t: string) => void
  onDone: (d: QAResponse) => void
  onError: (msg: string) => void
}

/**
 * 调 /api/qa/stream（text/event-stream）。逐 token 回调 onToken，最终 onDone，
 * 出错 onError。底层用 fetch + ReadableStream 解析 SSE，无需额外依赖。
 */
export async function askStream(
  kbId: number,
  question: string,
  sessionId: number | undefined,
  handlers: StreamHandlers,
): Promise<void> {
  const token = localStorage.getItem('token')
  const resp = await fetch('/api/qa/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ kb_id: kbId, question, session_id: sessionId }),
  })
  if (!resp.ok || !resp.body) {
    handlers.onError(`请求失败 (${resp.status})`)
    return
  }
  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buf = ''
  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buf += decoder.decode(value, { stream: true })
    let idx: number
    while ((idx = buf.indexOf('\n\n')) !== -1) {
      const raw = buf.slice(0, idx)
      buf = buf.slice(idx + 2)
      const dataLine = raw.split('\n').find((l) => l.startsWith('data:'))
      if (!dataLine) continue
      const data = dataLine.slice(5).trim()
      if (data === '[DONE]') return
      try {
        const evt = JSON.parse(data)
        if (evt.type === 'token') handlers.onToken(evt.content)
        else if (evt.type === 'done') handlers.onDone(evt)
        else if (evt.type === 'error') handlers.onError(evt.message)
      } catch {
        // 忽略不完整片段
      }
    }
  }
}
