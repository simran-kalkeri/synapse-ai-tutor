import axios, { type AxiosInstance, type InternalAxiosRequestConfig } from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Shared refresh promise mutex — prevents concurrent 401 refresh calls ──
let refreshPromise: Promise<void> | null = null

async function doRefresh(): Promise<void> {
  const refresh = localStorage.getItem('synapse_refresh_token')
  if (!refresh) throw new Error('No refresh token')
  const { data } = await axios.post(`${BASE_URL}/api/v1/auth/refresh`, {
    refresh_token: refresh,
  })
  localStorage.setItem('synapse_access_token', data.access_token)
  localStorage.setItem('synapse_refresh_token', data.refresh_token)
}

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
      if (!refreshPromise) {
        refreshPromise = doRefresh().finally(() => { refreshPromise = null })
      }
      try {
        await refreshPromise
        const token = localStorage.getItem('synapse_access_token')
        original.headers.Authorization = `Bearer ${token}`
        return api(original)
      } catch {
        localStorage.removeItem('synapse_access_token')
        localStorage.removeItem('synapse_refresh_token')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

import type {
  TokenResponse, LoginRequest, User, StudentProfile, MasteryScore,
  AssessmentResult, AssessmentQuestion, GraphData, Note, NoteListItem, Roadmap,
  DashboardData, ChatMessage,
  VisualizeResponse, VisualizeTopicsResponse,
  TTSResponse, STTResponse,
  AnalyticsData, StudyGoal,
  RagUploadResponse,
} from '@/types'

export default api

// ── Typed API helpers ────────────────────────────────────────────────────────
export const authApi = {
  login: (body: LoginRequest) =>
    api.post<TokenResponse>('/api/v1/auth/login', body),
  register: (body: object) => api.post<TokenResponse>('/api/v1/auth/register', body),
  me: () => api.get<User>('/api/v1/auth/me'),
  logout: (refresh_token: string) => api.post('/api/v1/auth/logout', { refresh_token }),
}

export const tutorApi = {
  topics: () => api.get<string[]>('/api/v1/tutor/topics'),
  selectTopic: (topic: string) => api.post('/api/v1/tutor/topics/select', { topic }),
}

export const assessmentApi = {
  start: (topic: string) => api.get<{ questions: AssessmentQuestion[]; session_id: string; topic: string }>(`/api/v1/assessment/start/${encodeURIComponent(topic)}`),
  submit: (body: object) => api.post<AssessmentResult>('/api/v1/assessment/submit', body),
  history: () => api.get<AssessmentResult[]>('/api/v1/assessment/history'),
}

export const memoryApi = {
  profile: () => api.get<StudentProfile>('/api/v1/memory/profile'),
  mastery: () => api.get<{ mastery: MasteryScore[] }>('/api/v1/memory/mastery'),
  gaps: (topic: string) => api.get<string[]>(`/api/v1/memory/gaps/${encodeURIComponent(topic)}`),
  preferences: (body: object) => api.patch('/api/v1/memory/preferences', body),
}

export const graphApi = {
  data: () => api.get<GraphData>('/api/v1/graph/data'),
  expand: (concept: string, depth = 2) =>
    api.get<GraphData>(`/api/v1/graph/expand?concept=${encodeURIComponent(concept)}&depth=${depth}`),
}

export const notesApi = {
  list: () => api.get<NoteListItem[]>('/api/v1/notes/'),
  get: (topic: string) => api.get<Note>(`/api/v1/notes/${encodeURIComponent(topic)}`),
  generate: (body: { topic: string; level: string }) => api.post<Note>('/api/v1/notes/generate', body),
  delete: (topic: string) => api.delete(`/api/v1/notes/${encodeURIComponent(topic)}`),
}

export const roadmapApi = {
  get: (topic: string) => api.get<Roadmap>(`/api/v1/roadmap/${encodeURIComponent(topic)}`),
  completeStep: (topic: string, step: string) =>
    api.post(`/api/v1/roadmap/${encodeURIComponent(topic)}/step/${encodeURIComponent(step)}/complete`),
}

export const studyApi = {
  start: (topic: string) =>
    api.post<{ session_id: string; topic: string; started_at: string; status: string }>('/api/v1/study/start', { topic }),
  end: (body: { session_id: string; topic: string; duration_minutes?: number; questions_answered?: number; concepts_reviewed?: number }) =>
    api.post('/api/v1/study/end', body),
}

export const dashboardApi = {
  stats: () => api.get<DashboardData>('/api/v1/dashboard/stats'),
  streak: () => api.get<number>('/api/v1/dashboard/streak'),
  analytics: () => api.get<AnalyticsData>('/api/v1/dashboard/analytics'),
  goals: {
    list: () => api.get<StudyGoal[]>('/api/v1/dashboard/goals'),
    create: (body: { title: string; description?: string; topic?: string; target_sessions?: number; target_mastery?: number }) =>
      api.post<StudyGoal>('/api/v1/dashboard/goals', body),
    update: (id: string, body: Partial<StudyGoal>) =>
      api.patch<StudyGoal>(`/api/v1/dashboard/goals/${id}`, body),
    delete: (id: string) => api.delete(`/api/v1/dashboard/goals/${id}`),
  },
}

export const chatApi = {
  history: (topic: string) => api.get<ChatMessage[]>(`/api/v1/chat/history/${encodeURIComponent(topic)}`),
  clear: (topic: string) => api.delete(`/api/v1/chat/history/${encodeURIComponent(topic)}`),
}

export const ragApi = {
  status: () => api.get<{ ready: boolean; chunks: number }>('/api/v1/rag/status'),
  upload: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post<RagUploadResponse>('/api/v1/rag/upload', fd, {
      timeout: 120000,
    })
  },
}

export const visualizeApi = {
  generate: (body: { topic: string; level?: string; language?: string; params?: object }) =>
    api.post<VisualizeResponse>('/api/v1/visualize', body),
  topics: () => api.get<VisualizeTopicsResponse>('/api/v1/visualize/topics'),
}

export const voiceApi = {
  tts: (text: string) => api.post<TTSResponse>('/api/v1/voice/tts', { text }),
  stt: (audio: Blob) => {
    const fd = new FormData()
    fd.append('file', audio, 'recording.webm')
    return api.post<STTResponse>('/api/v1/voice/stt', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  voices: () => api.get<{ voices: { voice_id: string; name: string }[] }>('/api/v1/voice/voices'),
  status: () => api.get<Record<string, unknown>>('/api/v1/voice/status'),
}
