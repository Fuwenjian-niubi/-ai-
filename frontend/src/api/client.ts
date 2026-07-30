import axios from 'axios'

// API 基地址：默认相对路径 /api（开发期由 Vite 代理转发到后端 8000）；
// 生产环境可设置 VITE_API_BASE 指向后端，例如 http://localhost:8000/api
const base = import.meta.env.VITE_API_BASE || '/api'

export const api = axios.create({
  baseURL: base,
  headers: { 'Content-Type': 'application/json' },
  timeout: 120000, // 大模型首响较慢，放宽超时
})

// 请求拦截：自动注入 JWT
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截：401 统一跳登录
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
        window.location.assign('/login')
      }
    }
    return Promise.reject(error)
  },
)

export default api
