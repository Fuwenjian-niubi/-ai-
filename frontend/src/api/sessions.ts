import api from './client'
import type { SessionOut } from '../types'

export const listSessions = () =>
  api.get<SessionOut[]>('/sessions').then((r) => r.data)

export const createSession = (title?: string) =>
  api.post<SessionOut>('/sessions', { title }).then((r) => r.data)

export const renameSession = (id: number, title: string) =>
  api.patch<SessionOut>(`/sessions/${id}`, { title }).then((r) => r.data)

export const deleteSession = (id: number) =>
  api.delete(`/sessions/${id}`).then((r) => r.data)

export const getMessages = (sid: number) =>
  api
    .get<Array<{ role: string; content: string; citations?: any[] }>>(
      `/sessions/${sid}/messages`,
    )
    .then((r) => r.data)
