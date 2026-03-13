import { AnimatePresence, motion } from 'framer-motion'
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from 'lucide-react'
import { useAppStore } from '../../stores/appStore'

const icons: Record<string, React.ReactNode> = {
  success: <CheckCircle2 size={16} className="text-success" />,
  error: <AlertCircle size={16} className="text-danger" />,
  warn: <AlertTriangle size={16} className="text-warn" />,
  warning: <AlertTriangle size={16} className="text-warn" />,
  info: <Info size={16} className="text-info" />,
}

export default function Toast() {
  const { notifications, removeNotification } = useAppStore()

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      <AnimatePresence>
        {notifications.map(n => (
          <motion.div
            key={n.id}
            initial={{ opacity: 0, x: 40, scale: 0.95 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 40, scale: 0.95 }}
            transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
            className="card p-3.5 flex items-start gap-3 shadow-elevated"
          >
            <div className="mt-0.5">{icons[n.type] ?? icons.info}</div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-text-primary">{n.title}</p>
              {n.message && <p className="text-xs text-text-secondary mt-0.5">{n.message}</p>}
            </div>
            <button onClick={() => removeNotification(n.id)} className="text-text-muted hover:text-text-primary">
              <X size={14} />
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}
