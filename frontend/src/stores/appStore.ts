import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface Notification {
  id: string
  type: 'success' | 'error' | 'warn' | 'info'
  title: string
  message?: string
  duration?: number
}

interface AppState {
  /* theme */
  isDark: boolean
  toggleTheme: () => void
  /* mode */
  mode: 'production' | 'developer'
  toggleMode: () => void
  /* sidebar */
  sidebarCollapsed: boolean
  toggleSidebar: () => void
  /* search */
  searchOpen: boolean
  setSearchOpen: (open: boolean) => void
  searchQuery: string
  setSearchQuery: (q: string) => void
  /* notifications */
  notifications: Notification[]
  addNotification: (n: Omit<Notification, 'id'>) => void
  removeNotification: (id: string) => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      isDark: true,
      toggleTheme: () => {
        const next = !get().isDark
        set({ isDark: next })
        if (next) document.documentElement.classList.add('dark')
        else document.documentElement.classList.remove('dark')
      },
      mode: 'production',
      toggleMode: () => set(s => ({ mode: s.mode === 'production' ? 'developer' : 'production' })),
      sidebarCollapsed: false,
      toggleSidebar: () => set(s => ({ sidebarCollapsed: !s.sidebarCollapsed })),
      searchOpen: false,
      setSearchOpen: (open) => set({ searchOpen: open }),
      searchQuery: '',
      setSearchQuery: (q) => set({ searchQuery: q }),
      notifications: [],
      addNotification: (n) => {
        const id = Math.random().toString(36).slice(2)
        set(s => ({ notifications: [{ ...n, id }, ...s.notifications] }))
        setTimeout(() => get().removeNotification(id), n.duration ?? 4000)
      },
      removeNotification: (id) => set(s => ({ notifications: s.notifications.filter(n => n.id !== id) })),
    }),
    { name: 'astra-app', partialize: s => ({ isDark: s.isDark, mode: s.mode, sidebarCollapsed: s.sidebarCollapsed }) }
  )
)

// Apply theme on load
if (typeof window !== 'undefined') {
  const stored = localStorage.getItem('astra-app')
  if (stored) {
    try {
      const { state } = JSON.parse(stored)
      if (state?.isDark) document.documentElement.classList.add('dark')
      else document.documentElement.classList.remove('dark')
    } catch { /* ignore */ }
  }
}
