import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import type { JSX } from 'react'
import { AuthProvider, useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import Chat from './pages/Chat'
import Admin from './pages/Admin'
import Settings from './pages/Settings'
import ChangePassword from './pages/ChangePassword'

function FullSpinner({ text }: { text?: string }) {
  return (
    <div className="centered-fill">
      <div className="spinner" />
      <p>{text || '加载中…'}</p>
    </div>
  )
}

function RequireAuth({
  children,
  adminOnly,
}: {
  children: JSX.Element
  adminOnly?: boolean
}) {
  const { user, loading } = useAuth()
  if (loading) return <FullSpinner />
  if (!user) return <Navigate to="/login" replace />
  if (adminOnly && user.role !== 'admin') return <Navigate to="/chat" replace />
  return children
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route element={<Layout />}>
            <Route
              path="/chat"
              element={
                <RequireAuth>
                  <Chat />
                </RequireAuth>
              }
            />
            <Route
              path="/admin"
              element={
                <RequireAuth adminOnly>
                  <Admin />
                </RequireAuth>
              }
            />
            <Route
              path="/settings"
              element={
                <RequireAuth adminOnly>
                  <Settings />
                </RequireAuth>
              }
            />
            <Route
              path="/change-password"
              element={
                <RequireAuth>
                  <ChangePassword />
                </RequireAuth>
              }
            />
            <Route path="/" element={<Navigate to="/chat" replace />} />
          </Route>
          <Route path="*" element={<Navigate to="/chat" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
