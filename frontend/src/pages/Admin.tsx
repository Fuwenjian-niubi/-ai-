import { useEffect, useState } from 'react'
import type { KBOut, DocOut } from '../types'
import {
  listKBs,
  createKB,
  deleteKB,
  listDocuments,
  uploadDocument,
} from '../api/kb'
import KBCard from '../components/Admin/KBCard'

export default function Admin() {
  const [kbs, setKbs] = useState<KBOut[]>([])
  const [docsMap, setDocsMap] = useState<Record<number, DocOut[]>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState({ name: '', description: '', spot: '' })

  const refresh = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await Promise.race([
        listKBs(),
        new Promise<never>((_, reject) =>
          setTimeout(() => reject(new Error('请求超时，后端可能正在加载模型，请稍后刷新')), 10000),
        ),
      ])
      setKbs(data)
      const map: Record<number, DocOut[]> = {}
      await Promise.all(
        data.map(async (k) => {
          map[k.id] = await listDocuments(k.id)
        }),
      )
      setDocsMap(map)
    } catch (e: any) {
      if (e?.message?.includes('超时')) {
        setError(e.message)
      } else {
        setError(e?.response?.data?.detail || '加载失败')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  const onCreate = async () => {
    if (!form.name.trim()) {
      setError('请填写知识库名称')
      return
    }
    setCreating(true)
    setError('')
    try {
      await createKB(form.name.trim(), form.description.trim(), form.spot.trim())
      setShowCreate(false)
      setForm({ name: '', description: '', spot: '' })
      await refresh()
    } catch (e: any) {
      setError(e?.response?.data?.detail || '创建失败')
    } finally {
      setCreating(false)
    }
  }

  const onDelete = async (id: number) => {
    if (!window.confirm('确认删除该知识库？其下文档与向量索引将一并清除。')) return
    await deleteKB(id).catch(() => {})
    await refresh()
  }

  const onUpload = async (kbId: number, file: File) => {
    await uploadDocument(kbId, file)
    await refresh()
  }

  return (
    <div className="admin-wrap">
      <h1>知识库管理</h1>
      <p className="sub">
        创建多景点知识库并上传资料（支持 txt / md / pdf / docx），系统将自动分块、向量化并建立检索索引。
      </p>
      {error && <div className="alert alert-error">{error}</div>}

      <div className="toolbar">
        <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
          + 新建知识库
        </button>
        <button className="btn" onClick={refresh}>
          刷新
        </button>
      </div>

      {loading ? (
        <div className="centered-fill">
          <div className="spinner" />
        </div>
      ) : (
        <div className="kb-grid">
          {kbs.length === 0 && (
            <div style={{ color: 'var(--muted)' }}>
              还没有知识库，点击「新建知识库」开始。
            </div>
          )}
          {kbs.map((k) => (
            <KBCard
              key={k.id}
              kb={k}
              docs={docsMap[k.id] || []}
              onDelete={() => onDelete(k.id)}
              onUpload={(f) => onUpload(k.id, f)}
            />
          ))}
        </div>
      )}

      {showCreate && (
        <div className="modal-mask" onClick={() => setShowCreate(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>新建知识库</h3>
            <div className="field">
              <label>名称（必填）</label>
              <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="例如：广州塔"
                autoFocus
              />
            </div>
            <div className="field">
              <label>关联景点</label>
              <input
                value={form.spot}
                onChange={(e) => setForm({ ...form, spot: e.target.value })}
                placeholder="例如：广州塔 / 广州"
              />
            </div>
            <div className="field">
              <label>描述</label>
              <textarea
                value={form.description}
                onChange={(e) =>
                  setForm({ ...form, description: e.target.value })
                }
                placeholder="简要说明该知识库覆盖的内容"
                style={{ minHeight: 70 }}
              />
            </div>
            <div className="actions">
              <button className="btn" onClick={() => setShowCreate(false)}>
                取消
              </button>
              <button
                className="btn btn-primary"
                onClick={onCreate}
                disabled={creating}
              >
                {creating ? '创建中…' : '创建'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
