import api from './client'

export interface LLMSettings {
  base_url: string
  model: string
  api_key: string // 脱敏后的展示值（如 sk-a****b），空表示未设置
  has_key: boolean
}

// 仅 admin 可用：读取当前生效的 LLM 配置
export const getLLMSettings = () =>
  api.get<LLMSettings>('/settings/llm').then((r) => r.data)

// 用给定配置做一次连通测试（不落盘）
export const testLLMSettings = (payload: {
  base_url: string
  model: string
  api_key?: string
}) => api.post<{ ok: boolean; message?: string }>('/settings/llm/test', payload).then((r) => r.data)

// 验证通过后保存配置（写入后端 llm_runtime.json，即时生效）
export const updateLLMSettings = (payload: {
  base_url: string
  model: string
  api_key?: string
}) => api.put<{ ok: boolean; message?: string }>('/settings/llm', payload).then((r) => r.data)
