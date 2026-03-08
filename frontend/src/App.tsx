import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Spin } from 'antd'
import { useAuthStore } from './stores/auth'
import MainLayout from './layouts/MainLayout'
import Login from './pages/Login'
import Register from './pages/Register'
import FirstTimeSetup from './pages/FirstTimeSetup'
import SetupConfig from './pages/SetupConfig'
import Dashboard from './pages/Dashboard'
import Datasets from './pages/Datasets'
import DatasetVisualizer from './pages/DatasetVisualizer'
import ApiKeys from './pages/ApiKeys'
import AIAssistant from './pages/AIAssistant'
import Settings from './pages/Settings'
import { initApi } from './api'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { token } = useAuthStore()
  return token ? <>{children}</> : <Navigate to="/login" replace />
}

function App() {
  const [checking, setChecking] = useState(true)
  const [initialized, setInitialized] = useState<boolean | null>(null)

  useEffect(() => {
    checkInitStatus()
  }, [])

  const checkInitStatus = async () => {
    try {
      const res = await initApi.getStatus()
      setInitialized(res.data.initialized)
    } catch (error) {
      setInitialized(false)
    } finally {
      setChecking(false)
    }
  }

  if (checking) {
    return (
      <div style={{
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexDirection: 'column',
        gap: 16
      }}>
        <Spin size="large" />
        <span>正在加载...</span>
      </div>
    )
  }

  // 未初始化 - 显示首次设置页面
  if (!initialized) {
    return (
      <BrowserRouter>
        <Routes>
          <Route path="/*" element={<FirstTimeSetup />} />
        </Routes>
      </BrowserRouter>
    )
  }

  // 已初始化 - 显示正常应用
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/setup/config" element={
          <PrivateRoute>
            <SetupConfig />
          </PrivateRoute>
        } />
        <Route
          path="/*"
          element={
            <PrivateRoute>
              <MainLayout />
            </PrivateRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="datasets" element={<Datasets />} />
          <Route path="datasets/:id/visualize" element={<DatasetVisualizer />} />
          <Route path="api-keys" element={<ApiKeys />} />
          <Route path="ai-assistant" element={<AIAssistant />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App