import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '@/types'
import { authApi } from '@/lib/api'
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface AuthState {
  isHydrated: boolean
  user:            User | null
  accessToken:     string | null
  isAuthenticated: boolean
  isLoading:       boolean

  login:   (username: string, password: string) => Promise<void>
  logout:  () => Promise<void>
  setUser: (user: User) => void
  hydrate: () => Promise<void>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, _get) => ({
      user:            null,
      accessToken:     null,
      isAuthenticated: false,
      isLoading:       false,
      isHydrated:      false,

      login: async (username, password) => {
        set({ isLoading: true })
        try {
          const { data: tokens } = await authApi.login({ username, password })
          localStorage.setItem('synapse_access_token', tokens.access_token)
          localStorage.setItem('synapse_refresh_token', tokens.refresh_token)
          const { data: user } = await authApi.me()
          set({ user, accessToken: tokens.access_token, isAuthenticated: true, isLoading: false })
        } catch (err) {
          set({ isLoading: false })
          throw err
        }
      },

      logout: async () => {
        const refresh = localStorage.getItem('synapse_refresh_token') ?? ''
        try { await authApi.logout(refresh) } catch { /* ignore */ }
        localStorage.removeItem('synapse_access_token')
        localStorage.removeItem('synapse_refresh_token')
        set({ user: null, accessToken: null, isAuthenticated: false })
      },

      setUser: (user) => set({ user }),

      hydrate: async () => {
        const token = localStorage.getItem('synapse_access_token')
        const refresh = localStorage.getItem('synapse_refresh_token')
        if (!token) { set({ isAuthenticated: false, isHydrated: true }); return }
        try {
          const { data: user } = await authApi.me()
          set({ user, accessToken: token, isAuthenticated: true, isHydrated: true })
        } catch {
          // Access token expired — try refresh before logging out
          if (refresh) {
            try {
              const { data } = await axios.post(`${BASE_URL}/api/v1/auth/refresh`, { refresh_token: refresh })
              localStorage.setItem('synapse_access_token', data.access_token)
              localStorage.setItem('synapse_refresh_token', data.refresh_token)
              const { data: user } = await authApi.me()
              set({ user, accessToken: data.access_token, isAuthenticated: true, isHydrated: true })
              return
            } catch { /* refresh also failed — session is dead */ }
          }
          localStorage.removeItem('synapse_access_token')
          localStorage.removeItem('synapse_refresh_token')
          set({ user: null, accessToken: null, isAuthenticated: false, isHydrated: true })
        }
      },
    }),
    {
      name:    'synapse-auth',
      partialize: (s) => ({ user: s.user, isAuthenticated: s.isAuthenticated }),
    }
  )
)
