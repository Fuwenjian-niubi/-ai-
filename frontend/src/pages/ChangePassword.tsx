import { useState } from 'react'
import type { FormEvent } from 'react'
import { useAuth } from '../context/AuthContext'

export default function ChangePassword() {
  const { changePassword } = useAuth()
  const [oldPassword, setOldPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setOk('')
    if (newPassword.length < 6) {
      setError('新密码至少 6 个字符')
      return
    }
    if (newPassword !== confirm) {
      setError('两次输入的新密码不一致')
      return
    }
    setBusy(true)
    try {
      await changePassword(oldPassword, newPassword)
      setOk('密码已修改，请使用新密码登录')
      setOldPassword('')
      setNewPassword('')
      setConfirm('')
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      setError(detail === '原密码错误' ? '原密码错误' : detail || '修改失败')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-wrap">
      <form className="auth-card" onSubmit={submit}>
        <h1>修改密码</h1>
        <p className="sub">定期更换密码有助于保护账号安全</p>
        {error && <div className="alert alert-error">{error}</div>}
        {ok && <div className="alert alert-ok">{ok}</div>}
        <div className="field">
          <label>原密码</label>
          <input
            type="password"
            value={oldPassword}
            onChange={(e) => setOldPassword(e.target.value)}
            placeholder="请输入当前密码"
            autoFocus
          />
        </div>
        <div className="field">
          <label>新密码</label>
          <input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="至少 6 个字符"
          />
        </div>
        <div className="field">
          <label>确认新密码</label>
          <input
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            placeholder="再次输入新密码"
          />
        </div>
        <button className="btn btn-primary" style={{ width: '100%' }} disabled={busy}>
          {busy ? '提交中…' : '确认修改'}
        </button>
      </form>
    </div>
  )
}
