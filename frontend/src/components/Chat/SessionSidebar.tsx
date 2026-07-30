import type { SessionOut } from '../../types'

export default function SessionSidebar({
  sessions,
  activeId,
  onSelect,
  onNew,
  onDelete,
}: {
  sessions: SessionOut[]
  activeId: number | null
  onSelect: (id: number) => void
  onNew: () => void
  onDelete: (id: number) => void
}) {
  return (
    <div className="session-pane">
      <div className="pane-head">
        <button className="btn btn-primary btn-sm" style={{ width: '100%' }} onClick={onNew}>
          + 新对话
        </button>
      </div>
      <div className="session-list">
        {sessions.length === 0 && (
          <div style={{ color: 'var(--muted)', fontSize: 13, padding: 10 }}>
            暂无历史对话
          </div>
        )}
        {sessions.map((s) => (
          <div
            key={s.id}
            className={`session-item ${s.id === activeId ? 'active' : ''}`}
            onClick={() => onSelect(s.id)}
          >
            <span className="title">{s.title}</span>
            <button
              className="del"
              title="删除对话"
              onClick={(e) => {
                e.stopPropagation()
                onDelete(s.id)
              }}
            >
              ✕
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
