import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const onLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <img src="/icon.svg" alt="logo" className="brand-logo" />
          <span>景点AI问答机器人</span>
        </div>
        <nav className="topnav">
          <NavLink to="/chat">对话</NavLink>
          {user?.role === 'admin' && <NavLink to="/admin">知识库管理</NavLink>}
          {user?.role === 'admin' && <NavLink to="/settings">模型设置</NavLink>}
          <NavLink to="/change-password">修改密码</NavLink>
        </nav>
        <div className="userbox">
          <span className="uname">{user?.username}</span>
          <span className={`role-tag ${user?.role === 'admin' ? 'admin' : 'user'}`}>
            {user?.role === 'admin' ? '管理员' : '用户'}
          </span>
          <button className="btn-ghost" onClick={onLogout}>
            退出
          </button>
        </div>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}
