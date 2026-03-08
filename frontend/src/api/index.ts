import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const authStorage = localStorage.getItem('auth-storage')
    if (authStorage) {
      const { state } = JSON.parse(authStorage)
      if (state?.token) {
        config.headers.Authorization = `Bearer ${state.token}`
      }
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth-storage')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api

// Auth API
export const authApi = {
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }),
  register: (username: string, email: string, password: string) =>
    api.post('/auth/register', { username, email, password }),
  getMe: () => api.get('/auth/me'),
}

// API Keys
export const apiKeysApi = {
  list: () => api.get('/api-keys'),
  create: (data: { name: string; quota_limit?: number; llm_model?: string }) =>
    api.post('/api-keys', data),
  delete: (id: number) => api.delete(`/api-keys/${id}`),
  deactivate: (id: number) => api.post(`/api-keys/${id}/deactivate`),
  resetQuota: (id: number) => api.post(`/api-keys/${id}/reset-quota`),
}

// Datasets
export const datasetsApi = {
  list: (params?: { page?: number; page_size?: number }) =>
    api.get('/datasets', { params }),
  get: (id: number) => api.get(`/datasets/${id}`),
  create: (data: { name: string; description?: string }) => api.post('/datasets', data),
  update: (id: number, data: { name?: string; description?: string }) =>
    api.patch(`/datasets/${id}`, data),
  delete: (id: number) => api.delete(`/datasets/${id}`),
  scan: (id: number) => api.post(`/datasets/${id}/scan`),
}

// Tasks
export const tasksApi = {
  list: (params?: { status?: string; page?: number }) => api.get('/tasks', { params }),
  get: (id: number) => api.get(`/tasks/${id}`),
}
