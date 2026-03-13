import { Outlet } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import Sidebar from './Sidebar'
import TopBar from './TopBar'
import Toast from '../ui/Toast'
import { useAppStore } from '../../stores/appStore'

export default function AppShell() {
  const collapsed = useAppStore(s => s.sidebarCollapsed)

  return (
    <div className="flex min-h-screen bg-bg">
      <Sidebar />
      <div
        className="flex-1 flex flex-col transition-all duration-300 ease-out-expo"
        style={{ marginLeft: collapsed ? 72 : 260 }}
      >
        <TopBar />
        <main className="flex-1 overflow-auto">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
      <Toast />
    </div>
  )
}
