import { useLocation } from 'react-router-dom'
import { Sun, Moon, Code2, Eye, Bell } from 'lucide-react'
import { useAppStore } from '../../stores/appStore'
import { motion } from 'framer-motion'

const routeNames: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/optimize': 'Optimization',
  '/ask': 'Ask Question',
  '/compare': 'Model Comparison',
  '/prompt-analyzer': 'Prompt Analyzer',
  '/analytics': 'Analytics',
  '/questions': 'Question Bank',
  '/settings': 'Settings',
  '/costs': 'Cost Tracking',
  '/models': 'Models',
}

export default function TopBar() {
  const { isDark, toggleTheme, mode, toggleMode, notifications } = useAppStore()
  const location = useLocation()

  const pageName = routeNames[location.pathname] ??
    (location.pathname.startsWith('/sessions/') ? 'Session Detail' : 'Astra AI')

  const unread = notifications.length

  return (
    <header className="h-16 border-b border-border bg-surface-1 flex items-center justify-between px-6 sticky top-0 z-30">
      {/* Left: breadcrumb */}
      <div className="flex items-center gap-2">
        <span className="text-text-muted text-sm font-body">Astra AI</span>
        <span className="text-text-muted text-sm">/</span>
        <span className="text-text-primary text-sm font-medium">{pageName}</span>
      </div>

      {/* Right: controls */}
      <div className="flex items-center gap-2">
        {/* Mode toggle */}
        <button
          onClick={toggleMode}
          className="btn-ghost gap-1.5 text-xs"
          title={`Switch to ${mode === 'production' ? 'Developer' : 'Production'} mode`}
        >
          {mode === 'developer' ? <Code2 size={14} /> : <Eye size={14} />}
          <span className="hidden sm:inline">{mode === 'developer' ? 'Dev' : 'Prod'}</span>
        </button>

        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="btn-ghost p-2"
          title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          <motion.div
            key={isDark ? 'dark' : 'light'}
            initial={{ rotate: -90, opacity: 0 }}
            animate={{ rotate: 0, opacity: 1 }}
            transition={{ duration: 0.2 }}
          >
            {isDark ? <Sun size={16} /> : <Moon size={16} />}
          </motion.div>
        </button>

        {/* Notifications */}
        <div className="relative">
          <button className="btn-ghost p-2">
            <Bell size={16} />
          </button>
          {unread > 0 && (
            <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-danger text-white text-[10px] font-bold rounded-full flex items-center justify-center">
              {unread > 9 ? '9+' : unread}
            </span>
          )}
        </div>
      </div>
    </header>
  )
}
