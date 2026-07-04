import axios, { type AxiosInstance, type InternalAxiosRequestConfig } from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Request interceptor: attach access token ─────────────────────────────────
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('synapse_access_token')
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ── Response interceptor: auto-refresh on 401 ───────────────────────────────
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      const refresh = localStorage.getItem('synapse_refresh_token')
      if (refresh) {
        try {
          const { data } = await axios.post(`${BASE_URL}/api/v1/auth/refresh`, {
            refresh_token: refresh,
          })
          localStorage.setItem('synapse_access_token', data.access_token)
          localStorage.setItem('synapse_refresh_token', data.refresh_token)
          original.headers.Authorization = `Bearer ${data.access_token}`
          return api(original)
        } catch {
          localStorage.removeItem('synapse_access_token')
          localStorage.removeItem('synapse_refresh_token')
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

export default api

// ── Typed API helpers ────────────────────────────────────────────────────────
export const authApi = {
  login:   (body: { username: string; password: string }) =>
    api.post('/api/v1/auth/login', body),
  register: (body: object) => api.post('/api/v1/auth/register', body),
  me:      () => api.get('/api/v1/auth/me'),
  logout:  (refresh_token: string) => api.post('/api/v1/auth/logout', { refresh_token }),
}

export const tutorApi = {
  topics:       () => api.get('/api/v1/tutor/topics'),
  selectTopic:  (topic: string) => api.post('/api/v1/tutor/topics/select', { topic }),
}

export const assessmentApi = {
  start:   (topic: string) => api.get(`/api/v1/assessment/start/${encodeURIComponent(topic)}`),
  submit:  (body: object) => api.post('/api/v1/assessment/submit', body),
  history: () => api.get('/api/v1/assessment/history'),
}

export const memoryApi = {
  profile:     () => api.get('/api/v1/memory/profile'),
  mastery:     () => api.get('/api/v1/memory/mastery'),
  gaps:        (topic: string) => api.get(`/api/v1/memory/gaps/${encodeURIComponent(topic)}`),
  preferences: (body: object) => api.patch('/api/v1/memory/preferences', body),
}

export const graphApi = {
  data:   () => api.get('/api/v1/graph/data'),
  expand: (concept: string, depth = 2) =>
    api.get(`/api/v1/graph/expand?concept=${encodeURIComponent(concept)}&depth=${depth}`),
}

export const notesApi = {
  list:     () => api.get('/api/v1/notes/'),
  get:      (topic: string) => api.get(`/api/v1/notes/${encodeURIComponent(topic)}`),
  generate: (body: { topic: string; level: string }) => api.post('/api/v1/notes/generate', body),
  delete:   (topic: string) => api.delete(`/api/v1/notes/${encodeURIComponent(topic)}`),
}

export const roadmapApi = {
  get:          (topic: string) => api.get(`/api/v1/roadmap/${encodeURIComponent(topic)}`),
  completeStep: (topic: string, step: string) =>
    api.post(`/api/v1/roadmap/${encodeURIComponent(topic)}/step/${encodeURIComponent(step)}/complete`),
}

export const dashboardApi = {
  stats:  () => api.get('/api/v1/dashboard/stats'),
  streak: () => api.get('/api/v1/dashboard/streak'),
}

export const chatApi = {
  history: (topic: string) => api.get(`/api/v1/chat/history/${encodeURIComponent(topic)}`),
  clear:   (topic: string) => api.delete(`/api/v1/chat/history/${encodeURIComponent(topic)}`),
}

export const ragApi = {
  status: () => api.get('/api/v1/rag/status'),
}
