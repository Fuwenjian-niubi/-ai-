import { useRef, useState } from 'react'
import type { KBOut, DocOut } from '../../types'

export default function KBCard({
  kb,
  docs,
  onDelete,
  onUpload,
}: {
  kb: KBOut
  docs: DocOut[]
  onDelete: () => void
  onUpload: (file: File) => void
}) {
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  const doUpload = async () => {
    if (!file) return
    setBusy(true)
    setMsg('')
    try {
      await onUpload(file)
      setMsg(`已摄入：${file.name}`)
      setFile(null)
    } catch (e: any) {
      setMsg(e?.response?.data?.detail || '摄入失败')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="kb-card">
      <div>
        <h3>{kb.name}</h3>
        {kb.spot && <div className="spot">关联景点：{kb.spot}</div>}
      </div>
      <div className="desc">{kb.description || '（无描述）'}</div>

      <div className="docs">
        <div style={{ fontWeight: 600, marginBottom: 4 }}>
          已摄入文档（{docs.length}）
        </div>
        {docs.length === 0 && (
          <div style={{ color: 'var(--muted)' }}>暂无文档</div>
        )}
        {docs.map((d) => (
          <div className="doc-item" key={d.id}>
            <span>{d.filename}</span>
            <span style={{ color: 'var(--muted)' }}>{d.chunk_count} 块</span>
          </div>
        ))}
      </div>

      <div
        className="upload-zone"
        onClick={() => inputRef.current?.click()}
      >
        点击选择文件上传（txt / md / pdf / docx）
        {file && <div className="file-name">已选择：{file.name}</div>}
      </div>
      <input
        ref={inputRef}
        type="file"
        accept=".txt,.md,.pdf,.docx"
        style={{ display: 'none' }}
        onChange={(e) => setFile(e.target.files?.[0] || null)}
      />

      <div className="actions">
        <button
          className="btn btn-primary btn-sm"
          onClick={doUpload}
          disabled={!file || busy}
        >
          {busy ? '摄入中…' : '上传并摄入'}
        </button>
        <button className="btn btn-danger btn-sm" onClick={onDelete}>
          删除知识库
        </button>
      </div>

      {msg && (
        <div
          style={{
            fontSize: 12,
            color: msg.startsWith('已') ? 'var(--ok)' : 'var(--danger)',
          }}
        >
          {msg}
        </div>
      )}
    </div>
  )
}
