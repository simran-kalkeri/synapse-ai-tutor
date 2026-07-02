import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '@/types'
import { authApi } from '@/lib/api'

interface AuthState {
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
    (set, get) => ({
      user:            null,
      accessToken:     null,
      isAuthenticated: false,
      isLoading:       false,

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
        if (!token) { set({ isAuthenticated: false }); return }
        try {
          const { data: user } = await authApi.me()
          set({ user, accessToken: token, isAuthenticated: true })
        } catch {
          localStorage.removeItem('synapse_access_token')
          localStorage.removeItem('synapse_refresh_token')
          set({ user: null, accessToken: null, isAuthenticated: false })
        }
      },
    }),
    {
      name:    'synapse-auth',
      partialize: (s) => ({ user: s.user, isAuthenticated: s.isAuthenticated }),
    }
  )
)
