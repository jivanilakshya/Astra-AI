import { NavLink, useLocation, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  LayoutDashboard, Zap, MessageSquare, GitCompare, Search,
  BarChart3, BookOpen, Settings, DollarSign, Cpu,
  PanelLeftClose, PanelLeft
} from 'lucide-react'
import { useAppStore } from '../../stores/appStore'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/optimize', icon: Zap, label: 'Optimize' },
  { to: '/ask', icon: MessageSquare, label: 'Ask' },
  { to: '/compare', icon: GitCompare, label: 'Compare' },
  { to: '/prompt-analyzer', icon: Search, label: 'Analyzer' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/questions', icon: BookOpen, label: 'Questions' },
  { to: '/models', icon: Cpu, label: 'Models' },
  { to: '/costs', icon: DollarSign, label: 'Costs' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export default function Sidebar() {
  const collapsed = useAppStore(s => s.sidebarCollapsed)
  const toggle = useAppStore(s => s.toggleSidebar)
  const location = useLocation()

  return (
    <motion.aside
      className="fixed top-0 left-0 h-screen bg-surface-1 border-r border-border z-40 flex flex-col"
      animate={{ width: collapsed ? 72 : 260 }}
      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
    >
      {/* Logo */}
      <Link to="/" className="h-16 flex items-center px-5 border-b border-border hover:bg-surface-2 transition-colors">
        <div className="flex items-center gap-3 overflow-hidden">
          <svg className="w-8 h-8 flex-shrink-0" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="64" height="64" rx="16" fill="var(--color-accent)" />
            <ellipse cx="32" cy="32" rx="22" ry="10" fill="none" stroke="var(--color-accent-contrast)" strokeWidth="0.8" opacity="0.2" transform="rotate(-25 32 32)" />
            <path d="M32 14L20 50h5.5l2.8-8h11.4l2.8 8H48L32 14z" fill="var(--color-accent-contrast)" />
            <path d="M29.6 38L32 29l2.4 9h-4.8z" fill="var(--color-accent)" />
            <circle cx="32" cy="11" r="1.5" fill="var(--color-accent-contrast)" />
          </svg>
          {!collapsed && (
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="font-display text-xl text-text-primary whitespace-nowrap"
            >
              Astra AI
            </motion.span>
          )}
        </div>
      </Link>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map(({ to, icon: Icon, label }) => {
          const isActive = location.pathname === to || location.pathname.startsWith(to + '/')
          return (
            <NavLink
              key={to}
              to={to}
              className="relative block"
              title={collapsed ? label : undefined}
            >
              <div className={`nav-item ${isActive ? 'active' : ''}`}>
                {isActive && (
                  <motion.div
                    layoutId="nav-active"
                    className="absolute inset-0 bg-accent-muted rounded-button"
                    transition={{ type: 'spring', stiffness: 350, damping: 30 }}
                  />
                )}
                <Icon size={18} className="relative z-10 flex-shrink-0" />
                {!collapsed && (
                  <span className="relative z-10 whitespace-nowrap">{label}</span>
                )}
              </div>
            </NavLink>
          )
        })}
      </nav>

      {/* Collapse toggle */}
      <div className="p-3 border-t border-border">
        <button
          onClick={toggle}
          className="w-full flex items-center justify-center gap-2 py-2 rounded-button text-text-muted hover:text-text-primary hover:bg-surface-2 transition-colors"
        >
          {collapsed ? <PanelLeft size={18} /> : <PanelLeftClose size={18} />}
          {!collapsed && <span className="text-sm">Collapse</span>}
        </button>
      </div>
    </motion.aside>
  )
}
