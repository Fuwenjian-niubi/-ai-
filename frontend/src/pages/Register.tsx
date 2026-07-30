import { useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    if (username.trim().length < 3) {
      setError('用户名至少 3 个字符')
      return
    }
    if (password.length < 6) {
      setError('密码至少 6 个字符')
      return
    }
    if (password !== confirm) {
      setError('两次输入的密码不一致')
      return
    }
    setBusy(true)
    try {
      await register(username.trim(), password)
      navigate('/chat')
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      setError(detail === '用户名已存在' ? '该用户名已被注册' : detail || '注册失败')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-wrap">
      <form className="auth-card" onSubmit={submit}>
        <h1>注册</h1>
        <p className="sub">创建账号以使用景点知识库问答</p>
        {error && <div className="alert alert-error">{error}</div>}
        <div className="field">
          <label>用户名</label>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="3-64 个字符"
            autoFocus
          />
        </div>
        <div className="field">
          <label>密码</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="至少 6 个字符"
          />
        </div>
        <div className="field">
          <label>确认密码</label>
          <input
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            placeholder="再次输入密码"
          />
        </div>
        <button className="btn btn-primary" style={{ width: '100%' }} disabled={busy}>
          {busy ? '注册中…' : '注册并登录'}
        </button>
        <div className="auth-switch">
          已有账号？<Link to="/login">去登录</Link>
        </div>
      </form>
    </div>
  )
}
