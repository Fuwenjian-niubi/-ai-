import { useEffect, useState } from 'react'
import {
  getLLMSettings,
  testLLMSettings,
  updateLLMSettings,
  type LLMSettings,
} from '../api/settings'

export default function Settings() {
  const [form, setForm] = useState({ base_url: '', api_key: '', model: '' })
  const [hasKey, setHasKey] = useState(false)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<'test' | 'save' | null>(null)
  const [msg, setMsg] = useState<{ type: 'ok' | 'error'; text: string }>({
    type: 'ok',
    text: '',
  })

  useEffect(() => {
    getLLMSettings()
      .then((d: LLMSettings) => {
        setForm({ base_url: d.base_url, api_key: '', model: d.model })
        setHasKey(d.has_key)
      })
      .catch(
        (e: any) =>
          setMsg({ type: 'error', text: e?.response?.data?.detail || '加载失败' }),
      )
      .finally(() => setLoading(false))
  }, [])

  const onTest = async () => {
    setBusy('test')
    setMsg({ type: 'ok', text: '' })
    try {
      const r = await testLLMSettings(form)
      setMsg({ type: 'ok', text: r.message || '连接成功' })
    } catch (e: any) {
      setMsg({ type: 'error', text: e?.response?.data?.detail || '连接测试失败' })
    } finally {
      setBusy(null)
    }
  }

  const onSave = async () => {
    setBusy('save')
    setMsg({ type: 'ok', text: '' })
    try {
      const r = await updateLLMSettings(form)
      setMsg({ type: 'ok', text: r.message || '已保存' })
      setHasKey(true)
      setForm((f) => ({ ...f, api_key: '' })) // 保存后清空 key 输入框
    } catch (e: any) {
      setMsg({ type: 'error', text: e?.response?.data?.detail || '保存失败' })
    } finally {
      setBusy(null)
    }
  }

  if (loading) {
    return (
      <div className="admin-wrap">
        <div className="centered-fill">
          <div className="spinner" />
        </div>
      </div>
    )
  }

  return (
    <div className="admin-wrap">
      <h1>模型设置</h1>
      <p className="sub">
        配置问答使用的大模型（OpenAI 兼容）。修改后即时生效，无需重启。可选：通义千问
        Qwen、DeepSeek、智谱 GLM、Kimi 等。
      </p>

      {msg.text && (
        <div className={`alert ${msg.type === 'ok' ? 'alert-ok' : 'alert-error'}`}>
          {msg.text}
        </div>
      )}

      <div className="settings-card">
        <div className="field">
          <label>接口地址 (Base URL)</label>
          <input
            value={form.base_url}
            onChange={(e) => setForm({ ...form, base_url: e.target.value })}
            placeholder="https://dashscope.aliyuncs.com/compatible-mode/v1"
          />
        </div>

        <div className="field">
          <label>模型名称 (Model)</label>
          <input
            value={form.model}
            onChange={(e) => setForm({ ...form, model: e.target.value })}
            placeholder="例如：qwen3.7-plus"
          />
        </div>

        <div className="field">
          <label>
            API Key
            {hasKey && (
              <span className="muted-inline">（已保存，留空则不修改）</span>
            )}
          </label>
          <input
            type="password"
            value={form.api_key}
            onChange={(e) => setForm({ ...form, api_key: e.target.value })}
            placeholder={hasKey ? '如需更换请填写新 Key' : '请填写 API Key'}
          />
        </div>

        <div className="toolbar">
          <button
            className="btn"
            onClick={onTest}
            disabled={busy !== null}
          >
            {busy === 'test' ? '测试中…' : '测试连接'}
          </button>
          <button
            className="btn btn-primary"
            onClick={onSave}
            disabled={busy !== null}
          >
            {busy === 'save' ? '保存中…' : '保存设置'}
          </button>
        </div>

        <p className="hint-text">
          提示：保存时会先用填入的配置发一次测试请求，成功后才写入。更换模型后，
          首次问答会重新连接，请稍候几秒。
        </p>
      </div>
    </div>
  )
}
