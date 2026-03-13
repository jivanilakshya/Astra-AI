import { motion } from 'framer-motion'

interface ToggleProps {
  checked: boolean
  onChange: (v: boolean) => void
  label?: string
  size?: 'sm' | 'md'
}

export default function Toggle({ checked, onChange, label, size = 'md' }: ToggleProps) {
  const w = size === 'sm' ? 36 : 44
  const h = size === 'sm' ? 20 : 24
  const dot = size === 'sm' ? 14 : 18

  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className="flex items-center gap-2.5 cursor-pointer"
    >
      <div
        className={`relative rounded-full transition-colors duration-200 ${
          checked ? 'bg-accent' : 'bg-surface-4'
        }`}
        style={{ width: w, height: h }}
      >
        <motion.div
          className="absolute top-1/2 rounded-full"
          style={{ width: dot, height: dot, y: '-50%' }}
          animate={{
            x: checked ? w - dot - 3 : 3,
            backgroundColor: checked ? 'var(--color-accent-contrast)' : 'var(--color-text-muted)',
          }}
          transition={{ type: 'spring', stiffness: 500, damping: 30 }}
        />
      </div>
      {label && <span className="text-sm text-text-secondary">{label}</span>}
    </button>
  )
}
