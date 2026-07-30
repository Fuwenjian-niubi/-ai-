import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'
import type { UserOut } from '../types'
import { login as apiLogin, register as apiRegister, me as apiMe, changePassword as apiChangePassword } from '../api/auth'

interface AuthState {
  user: UserOut | null
  token: string | null
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  register: (username: string, password: string) => Promise<void>
  logout: () => void
  refresh: () => Promise<void>
  changePassword: (oldPassword: string, newPassword: string) => Promise<void>
}

const AuthCtx = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null)
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'))
  const [loading, setLoading] = useState(true)

  // 启动时若本地有 token，则拉取用户信息校验有效性
  useEffect(() => {
    const t = localStorage.getItem('token')
    if (!t) {
      setLoading(false)
      return
    }
    apiMe()
      .then((u) => setUser(u))
      .catch(() => {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        setToken(null)
      })
      .finally(() => setLoading(false))
  }, [])

  const login = async (username: string, password: string) => {
    const res = await apiLogin(username, password)
    localStorage.setItem('token', res.access_token)
    const u = await apiMe()
    localStorage.setItem('user', JSON.stringify(u))
    setToken(res.access_token)
    setUser(u)
  }

  const register = async (username: string, password: string) => {
    await apiRegister(username, password)
    await login(username, password)
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setToken(null)
    setUser(null)
  }

  const refresh = async () => {
    const u = await apiMe()
    setUser(u)
    localStorage.setItem('user', JSON.stringify(u))
  }

  const changePassword = async (oldPassword: string, newPassword: string) => {
    await apiChangePassword(oldPassword, newPassword)
  }

  return (
    <AuthCtx.Provider value={{ user, token, loading, login, register, logout, refresh, changePassword }}>
      {children}
    </AuthCtx.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthCtx)
  if (!ctx) throw new Error('useAuth 必须在 AuthProvider 内使用')
  return ctx
}
