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

// Statistics
export const statisticsApi = {
  getOverview: () => api.get('/statistics/overview'),
  getTimeline: (days: number = 30) => api.get('/statistics/timeline', { params: { days } }),
  getDatasetStats: (datasetId: number) => api.get(`/statistics/dataset/${datasetId}`),
}

// Search
export const searchApi = {
  searchFiles: (query: string, dataType?: string, page?: number) =>
    api.get('/search/files', { params: { q: query, data_type: dataType, page } }),
  searchDatasets: (query: string) =>
    api.get('/search/datasets', { params: { q: query } }),
}

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
  create: (data: { name: string; description?: string; storage_path?: string }) => api.post('/datasets', data),
  update: (id: number, data: { name?: string; description?: string }) =>
    api.patch(`/datasets/${id}`, data),
  delete: (id: number) => api.delete(`/datasets/${id}`),
  scan: (id: number) => api.post(`/datasets/${id}/scan`),
  listFiles: (datasetId: number, params?: { page?: number; page_size?: number }) =>
    api.get(`/datasets/${datasetId}/files`, { params }),
  downloadFromHuggingface: (datasetId: number, repoId: string, allowPatterns?: string) =>
    api.post(`/datasets/${datasetId}/download/huggingface`, null, {
      params: { repo_id: repoId, allow_patterns: allowPatterns }
    }),
  downloadFromUrl: (datasetId: number, url: string) =>
    api.post(`/datasets/${datasetId}/download/url`, null, { params: { url } }),
}

// Tasks
export const tasksApi = {
  list: (params?: { status?: string; page?: number }) => api.get('/tasks', { params }),
  get: (id: number) => api.get(`/tasks/${id}`),
}
