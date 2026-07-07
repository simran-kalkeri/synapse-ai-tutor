import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface UIState {
  sidebarCollapsed: boolean
  currentTopic:     string
  selectedLevel:    string

  setSidebarCollapsed: (v: boolean) => void
  toggleSidebar:       () => void
  setCurrentTopic:     (t: string) => void
  setSelectedLevel:    (l: string) => void
}

export const useUIStore = create<UIState>()(
  persist(
    (set, _get) => ({
      sidebarCollapsed: false,
      currentTopic:     '',
      selectedLevel:    'Intermediate',

      setSidebarCollapsed: (v) => set({ sidebarCollapsed: v }),
      toggleSidebar:       () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
      setCurrentTopic:     (t) => set({ currentTopic: t }),
      setSelectedLevel:    (l) => set({ selectedLevel: l }),
    }),
    { name: 'synapse-ui' }
  )
)
