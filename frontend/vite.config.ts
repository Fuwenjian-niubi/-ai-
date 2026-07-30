import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// 前端开发服务器通过代理把 /api 转发到后端（默认 8000）。
// 生产构建如需直连后端，可设置环境变量 VITE_API_BASE 为后端地址（如 http://localhost:8000/api）。
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
