import api from './client'
import type { UserOut, TokenResponse } from '../types'

export const register = (username: string, password: string) =>
  api.post<UserOut>('/auth/register', { username, password }).then((r) => r.data)

export const login = (username: string, password: string) =>
  api.post<TokenResponse>('/auth/login', { username, password }).then((r) => r.data)

export const me = () => api.get<UserOut>('/auth/me').then((r) => r.data)

export const changePassword = (old_password: string, new_password: string) =>
  api
    .post('/auth/change-password', { old_password, new_password })
    .then((r) => r.data)
