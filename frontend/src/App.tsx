import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/auth'
import MainLayout from './layouts/MainLayout'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Datasets from './pages/Datasets'
import DatasetVisualizer from './pages/DatasetVisualizer'
import ApiKeys from './pages/ApiKeys'
import AIAssistant from './pages/AIAssistant'
import Settings from './pages/Settings'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { token } = useAuthStore()
  return token ? <>{children}</> : <Navigate to="/login" replace />
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
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
