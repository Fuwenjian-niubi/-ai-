import api from './client'
import type { KBOut, DocOut } from '../types'

// 任意已登录用户可列出知识库（用于选择要问答的景点）
export const listKBs = () => api.get<KBOut[]>('/kb').then((r) => r.data)

// 以下仅 admin 可用
export const createKB = (name: string, description = '', spot = '') =>
  api.post<KBOut>('/kb', { name, description, spot }).then((r) => r.data)

export const deleteKB = (id: number) =>
  api.delete(`/kb/${id}`).then((r) => r.data)

export const listDocuments = (kbId: number) =>
  api.get<DocOut[]>(`/kb/${kbId}/documents`).then((r) => r.data)

export const uploadDocument = (kbId: number, file: File) => {
  const form = new FormData()
  form.append('file', file)
  return api
    .post(`/kb/${kbId}/documents`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    .then((r) => r.data)
}
