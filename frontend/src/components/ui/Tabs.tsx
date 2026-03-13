import { motion } from 'framer-motion'

interface TabsProps {
  tabs: Array<{ key: string; label: string; icon?: React.ReactNode }>
  active: string
  onChange: (key: string) => void
  className?: string
}

export default function Tabs({ tabs, active, onChange, className = '' }: TabsProps) {
  return (
    <div className={`flex gap-1 p-1 bg-surface-2 rounded-button border border-border ${className}`}>
      {tabs.map(tab => (
        <button
          key={tab.key}
          onClick={() => onChange(tab.key)}
          className={`relative flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-[7px] transition-colors ${
            active === tab.key ? 'text-text-primary' : 'text-text-muted hover:text-text-secondary'
          }`}
        >
          {active === tab.key && (
            <motion.div
              layoutId="tab-bg"
              className="absolute inset-0 bg-surface-1 rounded-[7px] shadow-sm border border-border"
              transition={{ type: 'spring', stiffness: 400, damping: 30 }}
            />
          )}
          {tab.icon && <span className="relative z-10">{tab.icon}</span>}
          <span className="relative z-10">{tab.label}</span>
        </button>
      ))}
    </div>
  )
}
